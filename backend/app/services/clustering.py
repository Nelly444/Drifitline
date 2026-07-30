from collections import defaultdict

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
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


async def run_clustering(db: AsyncSession) -> dict:
    txn_result = await db.execute(select(Transaction))
    all_txns = list(txn_result.scalars().all())

    merchant_result = await db.execute(select(Merchant))
    merchants = list(merchant_result.scalars().all())
    merchants_by_id = {m.id: m for m in merchants}

    mapping = normalize_merchants([m.raw_name for m in merchants])
    for merchant in merchants:
        merchant.normalized_name = mapping[merchant.raw_name]
    await db.flush()

    raw_name_to_merchant = {m.raw_name: m for m in merchants}

    groups: dict[str, list[Transaction]] = defaultdict(list)
    for txn in all_txns:
        normalized_name = merchants_by_id[txn.merchant_id].normalized_name
        groups[normalized_name].append(txn)

    eligible_groups = {
        name: sorted(txns, key=lambda t: t.posted_date)
        for name, txns in groups.items()
        if len(txns) >= MIN_GROUP_SIZE
    }
    group_features = {name: build_group_features(txns) for name, txns in eligible_groups.items()}

    subscriptions_created = 0
    transactions_linked = 0

    if group_features:
        scaler = StandardScaler()
        scaler.fit(np.vstack(list(group_features.values())))

        for name, sorted_txns in eligible_groups.items():
            scaled = scaler.transform(group_features[name])
            labels = DBSCAN(eps=EPS, min_samples=MIN_SAMPLES).fit_predict(scaled)

            for cluster_label in sorted(set(labels)):
                if cluster_label == -1:
                    continue
                member_txns = [t for t, label in zip(sorted_txns, labels) if label == cluster_label]

                canonical_merchant = raw_name_to_merchant[name]
                subscription = Subscription(merchant_id=canonical_merchant.id)
                db.add(subscription)
                await db.flush()
                subscriptions_created += 1

                for txn in member_txns:
                    txn.subscription_id = subscription.id
                    transactions_linked += 1

    await db.commit()
    return {
        "subscriptions_created": subscriptions_created,
        "transactions_linked": transactions_linked,
        "merchant_groups_considered": len(eligible_groups),
    }
