"""
Phase 5 verification helper: inject a fake new transaction into the linked Plaid
sandbox item via /sandbox/transactions/create, so the scheduled pipeline has real
new data to pick up and (ideally) flag as drift on its next poll. This endpoint
only works against the user_transactions_dynamic sandbox test user (which
create_sandbox_item() already hardcodes) and simulates a transactions/refresh
call, so the injected transaction shows up as `added` on the next transactions_sync.

Usage:
  python scripts/inject_sandbox_drift.py                       # auto-picks a
    subscribed merchant with a real forecast and injects at 1.5x that forecast
  python scripts/inject_sandbox_drift.py "Netflix" 45.00        # explicit merchant + amount
"""

import asyncio
import sys
from datetime import date

from plaid.model.custom_sandbox_transaction import CustomSandboxTransaction
from plaid.model.sandbox_transactions_create_request import SandboxTransactionsCreateRequest
from sqlalchemy import select

from app.db import async_session
from app.models import Merchant, PlaidItem, Subscription
from app.services.plaid_client import _get_client


async def pick_target(db) -> tuple[str, float]:
    result = await db.execute(
        select(Subscription, Merchant)
        .join(Merchant, Subscription.merchant_id == Merchant.id)
        .where(Subscription.forecast_amount.is_not(None))
        .order_by(Subscription.id)
    )
    row = result.first()
    if row is None:
        print("No subscription with a real forecast yet - run /clustering/run and /forecasting/run first.")
        sys.exit(1)
    subscription, merchant = row
    forecast = abs(float(subscription.forecast_amount))
    return merchant.raw_name, round(forecast * 1.5, 2)


async def main():
    async with async_session() as db:
        result = await db.execute(select(PlaidItem).order_by(PlaidItem.id.desc()).limit(1))
        plaid_item = result.scalar_one_or_none()
        if plaid_item is None:
            print("No Plaid item linked yet. Call POST /plaid/sandbox-link first.")
            sys.exit(1)
        access_token = plaid_item.access_token

        if len(sys.argv) == 3:
            description, amount = sys.argv[1], float(sys.argv[2])
        else:
            description, amount = await pick_target(db)

    client = _get_client()
    today = date.today()
    client.sandbox_transactions_create(
        SandboxTransactionsCreateRequest(
            access_token=access_token,
            transactions=[
                CustomSandboxTransaction(
                    date_transacted=today,
                    date_posted=today,
                    amount=amount,
                    description=description,
                )
            ],
        )
    )
    print(f"Injected: {description!r} for ${amount:.2f} on {today.isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
