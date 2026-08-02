from collections import defaultdict

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Merchant, Subscription, Transaction
from app.services.merchant_matching import normalize_merchants

# eps/min_samples chosen empirically in backend/scripts/derisk_dbscan.py
EPS = 1.0
MIN_SAMPLES = 3
MIN_GROUP_SIZE = 3


def build_group_features(sorted_txns: list[Transaction]) -> np.ndarray:
    """sorted_txns must already be sorted by posted_date ascending."""
    dates = [t.posted_date for t in sorted_txns]
    amounts = [float(t.amount) for t in sorted_txns]

    intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
    # First transaction in a group has no prior charge to diff against; imputing the
    # group's own median interval avoids both dropping it and biasing toward zero.
    median_interval = float(np.median(intervals)) if intervals else 0.0
    day_intervals = [median_interval] + intervals

    return np.array(list(zip(amounts, day_intervals)))


def resolve_group_links(sorted_txns: list, existing_subscription_id: int | None) -> tuple:
    """
    If a Subscription already exists for this merchant, reuse it for every
    not-yet-linked transaction instead of re-running DBSCAN. Once a subscription
    is established, a price change is drift to be scored, not noise to be
    discarded - and re-running DBSCAN from scratch on a scheduler would both
    re-litigate cluster membership unstably and create a duplicate Subscription
    every run. Returns (None, []) if there's no existing subscription yet,
    telling the caller to fall back to DBSCAN discovery as usual.
    """
    if existing_subscription_id is None:
        return None, []
    unlinked = [t for t in sorted_txns if t.subscription_id is None]
    return existing_subscription_id, unlinked


async def run_clustering(db: AsyncSession, plaid_item_ids: list[int]) -> dict:
    txn_result = await db.execute(select(Transaction).where(Transaction.plaid_item_id.in_(plaid_item_ids)))
    all_txns = list(txn_result.scalars().all())

    # Merchant is a shared, global name-vocabulary table (not tenant data) -
    # deliberately unfiltered.
    merchant_result = await db.execute(select(Merchant))
    merchants = list(merchant_result.scalars().all())
    merchants_by_id = {m.id: m for m in merchants}

    mapping = normalize_merchants([m.raw_name for m in merchants])
    for merchant in merchants:
        merchant.normalized_name = mapping[merchant.raw_name]
    await db.flush()

    raw_name_to_merchant = {m.raw_name: m for m in merchants}

    # Scoped to this tenant's own Subscriptions only - reusing another tenant's
    # Subscription for a same-named merchant (e.g. both have "Netflix") would
    # silently merge their transaction histories into one shared subscription.
    sub_result = await db.execute(select(Subscription).where(Subscription.plaid_item_id.in_(plaid_item_ids)))
    subscription_id_by_merchant_id = {s.merchant_id: s.id for s in sub_result.scalars().all()}

    groups: dict[str, list[Transaction]] = defaultdict(list)
    for txn in all_txns:
        normalized_name = merchants_by_id[txn.merchant_id].normalized_name
        groups[normalized_name].append(txn)

    eligible_groups = {
        name: sorted(txns, key=lambda t: t.posted_date)
        for name, txns in groups.items()
        if len(txns) >= MIN_GROUP_SIZE
    }

    subscriptions_created = 0
    transactions_linked = 0
    discovery_groups: dict[str, list[Transaction]] = {}

    for name, sorted_txns in eligible_groups.items():
        canonical_merchant = raw_name_to_merchant[name]
        existing_subscription_id = subscription_id_by_merchant_id.get(canonical_merchant.id)
        resolved_id, unlinked_txns = resolve_group_links(sorted_txns, existing_subscription_id)

        if resolved_id is not None:
            for txn in unlinked_txns:
                txn.subscription_id = resolved_id
                transactions_linked += 1
        else:
            discovery_groups[name] = sorted_txns

    group_features = {name: build_group_features(txns) for name, txns in discovery_groups.items()}

    if group_features:
        scaler = StandardScaler()
        scaler.fit(np.vstack(list(group_features.values())))

        for name, sorted_txns in discovery_groups.items():
            scaled = scaler.transform(group_features[name])
            labels = DBSCAN(eps=EPS, min_samples=MIN_SAMPLES).fit_predict(scaled)

            for cluster_label in sorted(set(labels)):
                if cluster_label == -1:
                    continue
                member_txns = [t for t, label in zip(sorted_txns, labels) if label == cluster_label]

                canonical_merchant = raw_name_to_merchant[name]
                item_id = member_txns[0].plaid_item_id

                # A concurrent clustering run for this tenant (scheduler tick
                # overlapping a manual /clustering/run) can both decide "no
                # existing subscription yet" and try to create one; the
                # savepoint confines the resulting IntegrityError so we fall
                # back to reusing the row the other run just created instead
                # of splitting this merchant's history across two duplicates.
                try:
                    async with db.begin_nested():
                        subscription = Subscription(merchant_id=canonical_merchant.id, plaid_item_id=item_id)
                        db.add(subscription)
                        await db.flush()
                    subscriptions_created += 1
                except IntegrityError:
                    result = await db.execute(
                        select(Subscription).where(
                            Subscription.merchant_id == canonical_merchant.id,
                            Subscription.plaid_item_id == item_id,
                        )
                    )
                    subscription = result.scalar_one()

                for txn in member_txns:
                    txn.subscription_id = subscription.id
                    transactions_linked += 1

    await db.commit()
    return {
        "subscriptions_created": subscriptions_created,
        "transactions_linked": transactions_linked,
        "merchant_groups_considered": len(eligible_groups),
    }
