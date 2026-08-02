from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_db
from app.models import Merchant, Subscription, Transaction, User
from app.services.serializers import serialize_transaction
from app.services.tenancy import plaid_item_ids_for_user

router = APIRouter(tags=["dashboard"])


def _empty_sparkline() -> list[dict]:
    today = date.today()
    ninety_days_ago = today - timedelta(days=90)
    sparkline = []
    day = ninety_days_ago
    while day <= today:
        sparkline.append({"date": day.isoformat(), "amount": 0.0})
        day += timedelta(days=1)
    return sparkline


@router.get("/subscriptions")
async def list_subscriptions(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    plaid_item_ids = await plaid_item_ids_for_user(db, user.id)
    if not plaid_item_ids:
        return []

    sub_result = await db.execute(select(Subscription).where(Subscription.plaid_item_id.in_(plaid_item_ids)))
    subscriptions = list(sub_result.scalars().all())

    merchant_ids = {sub.merchant_id for sub in subscriptions}
    merchant_result = await db.execute(select(Merchant).where(Merchant.id.in_(merchant_ids)))
    merchants_by_id = {m.id: m for m in merchant_result.scalars().all()}

    # One query for every subscription's transactions instead of one query per
    # subscription - the first transaction seen per subscription_id is the latest,
    # since the query is already ordered by posted_date desc.
    sub_ids = [sub.id for sub in subscriptions]
    latest_by_sub_id: dict[int, Transaction] = {}
    if sub_ids:
        txn_result = await db.execute(
            select(Transaction)
            .where(Transaction.subscription_id.in_(sub_ids))
            .order_by(Transaction.posted_date.desc())
        )
        for txn in txn_result.scalars().all():
            latest_by_sub_id.setdefault(txn.subscription_id, txn)

    out = []
    for sub in subscriptions:
        latest = latest_by_sub_id.get(sub.id)
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
async def list_transactions(
    flagged_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    plaid_item_ids = await plaid_item_ids_for_user(db, user.id)
    if not plaid_item_ids:
        return []

    query = (
        select(Transaction)
        .where(Transaction.plaid_item_id.in_(plaid_item_ids))
        .order_by(Transaction.posted_date.desc())
    )
    if flagged_only:
        query = query.where(Transaction.is_drift.is_(True))

    txn_result = await db.execute(query)
    transactions = list(txn_result.scalars().all())

    merchant_ids = {t.merchant_id for t in transactions}
    merchant_result = await db.execute(select(Merchant).where(Merchant.id.in_(merchant_ids)))
    merchants_by_id = {m.id: m for m in merchant_result.scalars().all()}

    return [
        serialize_transaction(t, merchants_by_id[t.merchant_id].normalized_name)
        for t in transactions
    ]


@router.get("/stats/summary")
async def stats_summary(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    plaid_item_ids = await plaid_item_ids_for_user(db, user.id)
    if not plaid_item_ids:
        return {
            "total_monthly_spend": 0.0,
            "active_subscriptions_count": 0,
            "flagged_this_month_count": 0,
            "sparkline": _empty_sparkline(),
        }

    sub_result = await db.execute(select(Subscription).where(Subscription.plaid_item_id.in_(plaid_item_ids)))
    subscriptions = list(sub_result.scalars().all())

    # Plaid's sandbox sign convention is inconsistent in our data (e.g. Sweetgreen
    # forecasts at -810.00), so summing raw signed amounts would be misleading -
    # abs() gives a sane "total recurring spend" figure regardless of sign.
    total_monthly_spend = sum(abs(float(s.forecast_amount)) for s in subscriptions if s.forecast_amount is not None)
    active_subscriptions_count = len(subscriptions)

    thirty_days_ago = date.today() - timedelta(days=30)
    flagged_result = await db.execute(
        select(Transaction).where(
            Transaction.plaid_item_id.in_(plaid_item_ids),
            Transaction.is_drift.is_(True),
            Transaction.posted_date >= thirty_days_ago,
        )
    )
    flagged_this_month_count = len(list(flagged_result.scalars().all()))

    ninety_days_ago = date.today() - timedelta(days=90)
    recent_result = await db.execute(
        select(Transaction)
        .where(Transaction.plaid_item_id.in_(plaid_item_ids), Transaction.posted_date >= ninety_days_ago)
        .order_by(Transaction.posted_date)
    )
    recent_txns = list(recent_result.scalars().all())

    daily_totals: dict[date, float] = {}
    for t in recent_txns:
        daily_totals[t.posted_date] = daily_totals.get(t.posted_date, 0.0) + abs(float(t.amount))

    # Zero-fill every day in the window (not just days with transactions) so the
    # sparkline is time-proportional - a category axis over sparse dates otherwise
    # compresses multi-week gaps into the same visual width as single-day gaps.
    today = date.today()
    sparkline = []
    day = ninety_days_ago
    while day <= today:
        sparkline.append({"date": day.isoformat(), "amount": round(daily_totals.get(day, 0.0), 2)})
        day += timedelta(days=1)

    return {
        "total_monthly_spend": round(total_monthly_spend, 2),
        "active_subscriptions_count": active_subscriptions_count,
        "flagged_this_month_count": flagged_this_month_count,
        "sparkline": sparkline,
    }


@router.get("/stats/breakdown")
async def stats_breakdown(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    plaid_item_ids = await plaid_item_ids_for_user(db, user.id)
    if not plaid_item_ids:
        return []

    txn_result = await db.execute(select(Transaction).where(Transaction.plaid_item_id.in_(plaid_item_ids)))
    transactions = list(txn_result.scalars().all())

    merchant_ids = {t.merchant_id for t in transactions}
    merchant_result = await db.execute(select(Merchant).where(Merchant.id.in_(merchant_ids)))
    merchants_by_id = {m.id: m for m in merchant_result.scalars().all()}

    totals: dict[str, float] = {}
    for t in transactions:
        merchant = merchants_by_id[t.merchant_id]
        name = merchant.normalized_name
        totals[name] = totals.get(name, 0.0) + abs(float(t.amount))

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    top = ranked[:6]
    other_total = sum(amount for _, amount in ranked[6:])

    breakdown = [{"merchant_name": name, "amount": round(amount, 2)} for name, amount in top]
    if other_total > 0:
        breakdown.append({"merchant_name": "Other", "amount": round(other_total, 2)})

    return breakdown
