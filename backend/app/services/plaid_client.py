import uuid

import plaid
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.sandbox_public_token_create_request_options import SandboxPublicTokenCreateRequestOptions
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Merchant, PlaidItem, Transaction
from app.services.crypto import decrypt, encrypt
from app.services.noise import inject_noise

_ENV_HOSTS = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production,
}


def _get_client() -> plaid_api.PlaidApi:
    settings = get_settings()
    configuration = plaid.Configuration(
        host=_ENV_HOSTS[settings.PLAID_ENV],
        api_key={
            "clientId": settings.PLAID_CLIENT_ID,
            "secret": settings.PLAID_SECRET,
        },
    )
    return plaid_api.PlaidApi(plaid.ApiClient(configuration))


async def create_sandbox_item(db: AsyncSession, user_id: uuid.UUID) -> PlaidItem:
    client = _get_client()

    public_token_response = client.sandbox_public_token_create(
        SandboxPublicTokenCreateRequest(
            institution_id="ins_109508",
            initial_products=[Products("transactions")],
            options=SandboxPublicTokenCreateRequestOptions(override_username="user_transactions_dynamic"),
        )
    )
    exchange_response = client.item_public_token_exchange(
        ItemPublicTokenExchangeRequest(public_token=public_token_response.public_token)
    )

    plaid_item = PlaidItem(
        user_id=user_id,
        item_id=exchange_response.item_id,
        access_token=encrypt(exchange_response.access_token),
    )
    db.add(plaid_item)
    await db.commit()
    await db.refresh(plaid_item)
    return plaid_item


async def sync_transactions(db: AsyncSession, plaid_item: PlaidItem) -> int:
    client = _get_client()
    access_token = decrypt(plaid_item.access_token)
    cursor = None
    added = []

    while True:
        kwargs = {"access_token": access_token}
        if cursor is not None:
            kwargs["cursor"] = cursor
        response = client.transactions_sync(TransactionsSyncRequest(**kwargs))
        added.extend(response.added)
        cursor = response.next_cursor
        if not response.has_more:
            break

    if not added:
        return 0

    transaction_ids = [txn.transaction_id for txn in added]
    existing_result = await db.execute(
        select(Transaction.plaid_transaction_id).where(Transaction.plaid_transaction_id.in_(transaction_ids))
    )
    existing_ids = set(existing_result.scalars().all())
    new_txns = [txn for txn in added if txn.transaction_id not in existing_ids]
    if not new_txns:
        return 0

    noisy_name_by_txn_id = {txn.transaction_id: inject_noise(txn.merchant_name or txn.name) for txn in new_txns}
    unique_names = set(noisy_name_by_txn_id.values())

    merchant_result = await db.execute(select(Merchant).where(Merchant.raw_name.in_(unique_names)))
    merchant_by_name = {m.raw_name: m for m in merchant_result.scalars().all()}

    missing_names = unique_names - merchant_by_name.keys()
    if missing_names:
        await db.execute(
            pg_insert(Merchant)
            .values([{"raw_name": name} for name in missing_names])
            .on_conflict_do_nothing(index_elements=["raw_name"])
        )
        merchant_result = await db.execute(select(Merchant).where(Merchant.raw_name.in_(unique_names)))
        merchant_by_name = {m.raw_name: m for m in merchant_result.scalars().all()}

    insert_stmt = (
        pg_insert(Transaction)
        .values(
            [
                {
                    "plaid_transaction_id": txn.transaction_id,
                    "merchant_id": merchant_by_name[noisy_name_by_txn_id[txn.transaction_id]].id,
                    "plaid_item_id": plaid_item.id,
                    "amount": txn.amount,
                    "posted_date": txn.date,
                }
                for txn in new_txns
            ]
        )
        .on_conflict_do_nothing(index_elements=["plaid_transaction_id"])
        .returning(Transaction.id)
    )
    inserted_ids = (await db.execute(insert_stmt)).scalars().all()
    await db.commit()
    return len(inserted_ids)
