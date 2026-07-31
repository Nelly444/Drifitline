from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Merchant, Subscription, Transaction

router = APIRouter(tags=["dashboard"])


@router.get("/subscriptions")
async def list_subscriptions(db: AsyncSession = Depends(get_db)):
    sub_result = await db.execute(select(Subscription))
    subscriptions = list(sub_result.scalars().all())

    merchant_result = await db.execute(select(Merchant))
    merchants_by_id = {m.id: m for m in merchant_result.scalars().all()}

    out = []
    for sub in subscriptions:
        txn_result = await db.execute(
            select(Transaction)
            .where(Transaction.subscription_id == sub.id)
            .order_by(Transaction.posted_date.desc())
            .limit(1)
        )
        latest = txn_result.scalar_one_or_none()
        merchant = merchants_by_id.get(sub.merchant_id)

        out.append({
            "id": sub.id,
            "merchant_name": merchant.normalized_name if merchant else None,
            "forecast_amount": float(sub.forecast_amount) if sub.forecast_amount is not None else None,
            "forecast_date": sub.forecast_date.isoformat() if sub.forecast_date else None,
            "latest_transaction": {
                "amount": float(latest.amount),
                "posted_date": latest.posted_date.isoformat(),
                "deviation_pct": latest.deviation_pct,
                "is_drift": latest.is_drift,
            } if latest else None,
        })

    return out


@router.get("/transactions")
async def list_transactions(flagged_only: bool = False, db: AsyncSession = Depends(get_db)):
    query = select(Transaction).order_by(Transaction.posted_date.desc())
    if flagged_only:
        query = query.where(Transaction.is_drift.is_(True))

    txn_result = await db.execute(query)
    transactions = list(txn_result.scalars().all())

    merchant_result = await db.execute(select(Merchant))
    merchants_by_id = {m.id: m for m in merchant_result.scalars().all()}

    return [
        {
            "id": t.id,
            "merchant_name": merchants_by_id[t.merchant_id].normalized_name,
            "amount": float(t.amount),
            "posted_date": t.posted_date.isoformat(),
            "expected_amount": float(t.expected_amount) if t.expected_amount is not None else None,
            "deviation_pct": t.deviation_pct,
            "is_drift": t.is_drift,
        }
        for t in transactions
    ]


@router.get("/stats/summary")
async def stats_summary(db: AsyncSession = Depends(get_db)):
    sub_result = await db.execute(select(Subscription))
    subscriptions = list(sub_result.scalars().all())

    # Plaid's sandbox sign convention is inconsistent in our data (e.g. Sweetgreen
    # forecasts at -810.00), so summing raw signed amounts would be misleading -
    # abs() gives a sane "total recurring spend" figure regardless of sign.
    total_monthly_spend = sum(abs(float(s.forecast_amount)) for s in subscriptions if s.forecast_amount is not None)
    active_subscriptions_count = len(subscriptions)

    thirty_days_ago = date.today() - timedelta(days=30)
    flagged_result = await db.execute(
        select(Transaction).where(Transaction.is_drift.is_(True), Transaction.posted_date >= thirty_days_ago)
    )
    flagged_this_month_count = len(list(flagged_result.scalars().all()))

    ninety_days_ago = date.today() - timedelta(days=90)
    recent_result = await db.execute(
        select(Transaction).where(Transaction.posted_date >= ninety_days_ago).order_by(Transaction.posted_date)
    )
    recent_txns = list(recent_result.scalars().all())

    daily_totals: dict[date, float] = {}
    for t in recent_txns:
        daily_totals[t.posted_date] = daily_totals.get(t.posted_date, 0.0) + abs(float(t.amount))

    sparkline = [{"date": d.isoformat(), "amount": round(amount, 2)} for d, amount in sorted(daily_totals.items())]

    return {
        "total_monthly_spend": round(total_monthly_spend, 2),
        "active_subscriptions_count": active_subscriptions_count,
        "flagged_this_month_count": flagged_this_month_count,
        "sparkline": sparkline,
    }
