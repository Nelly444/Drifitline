from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription, Transaction
from app.services.forecasting import expected_next_date, forecast_amount, score

MIN_HISTORY = 2


def score_subscription_history(sorted_txns: list) -> tuple[float, date]:
    for i in range(MIN_HISTORY, len(sorted_txns)):
        history = [float(t.amount) for t in sorted_txns[:i]]
        expected, std_used = forecast_amount(history)
        deviation_pct, is_drift = score(float(sorted_txns[i].amount), expected, std_used)

        sorted_txns[i].expected_amount = round(expected, 2)
        sorted_txns[i].deviation_pct = deviation_pct
        sorted_txns[i].is_drift = is_drift

    full_history = [float(t.amount) for t in sorted_txns]
    full_dates = [t.posted_date for t in sorted_txns]
    forecast_next_amount, _ = forecast_amount(full_history)
    return round(forecast_next_amount, 2), expected_next_date(full_dates)


def newly_flagged_since(before_by_id: dict[int, bool], txns: list) -> list:
    return [t for t in txns if t.is_drift and not before_by_id.get(t.id, False)]


async def run_scoring(db: AsyncSession, plaid_item_ids: list[int]) -> dict:
    sub_result = await db.execute(select(Subscription).where(Subscription.plaid_item_id.in_(plaid_item_ids)))
    subscriptions = list(sub_result.scalars().all())

    transactions_scored = 0
    flagged_as_drift = 0
    newly_flagged: list = []

    sub_ids = [s.id for s in subscriptions]
    txns_by_sub_id: dict[int, list] = defaultdict(list)
    if sub_ids:
        txn_result = await db.execute(
            select(Transaction).where(Transaction.subscription_id.in_(sub_ids)).order_by(Transaction.posted_date)
        )
        for txn in txn_result.scalars().all():
            txns_by_sub_id[txn.subscription_id].append(txn)

    for subscription in subscriptions:
        txns = txns_by_sub_id.get(subscription.id, [])
        if len(txns) < MIN_HISTORY + 1:
            continue

        before_by_id = {t.id: t.is_drift for t in txns}

        forecast_next_amount, forecast_date = score_subscription_history(txns)
        subscription.forecast_amount = forecast_next_amount
        subscription.forecast_date = forecast_date

        newly_flagged.extend(newly_flagged_since(before_by_id, txns))

        for txn in txns[MIN_HISTORY:]:
            transactions_scored += 1
            if txn.is_drift:
                flagged_as_drift += 1

    await db.commit()
    return {
        "transactions_scored": transactions_scored,
        "flagged_as_drift": flagged_as_drift,
        "newly_flagged": newly_flagged,
    }
