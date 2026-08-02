from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription, Transaction
from app.services.forecasting import expected_next_date, forecast_amount, score

# Need at least 2 prior points to compute a std-dev, so the first 2 transactions in a
# subscription's history are left unscored (same spirit as clustering's first-point
# interval imputation, but here there's no sane value to impute for a forecast).
MIN_HISTORY = 2


def score_subscription_history(sorted_txns: list) -> tuple[float, date]:
    """
    sorted_txns must already be sorted by posted_date ascending, and expose mutable
    .amount/.posted_date/.expected_amount/.deviation_pct/.is_drift attributes. Mutates
    each scoreable transaction in place. Returns the subscription-level forward forecast
    (amount, next_date) computed from the full history.
    """
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
    """
    Transactions that are drift-flagged now but weren't (or didn't exist) before
    this scoring pass - i.e. what actually changed in this run, not the full set
    of currently-flagged transactions. Used to avoid re-broadcasting the same
    alert on every poll cycle.
    """
    return [t for t in txns if t.is_drift and not before_by_id.get(t.id, False)]


async def run_scoring(db: AsyncSession) -> dict:
    sub_result = await db.execute(select(Subscription))
    subscriptions = list(sub_result.scalars().all())

    transactions_scored = 0
    flagged_as_drift = 0
    newly_flagged: list = []

    for subscription in subscriptions:
        txn_result = await db.execute(
            select(Transaction)
            .where(Transaction.subscription_id == subscription.id)
            .order_by(Transaction.posted_date)
        )
        txns = list(txn_result.scalars().all())
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
