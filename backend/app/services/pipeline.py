from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Merchant, PlaidItem
from app.services import clustering, plaid_client, scoring
from app.services.serializers import serialize_transaction


async def run_pipeline(db: AsyncSession, plaid_item: PlaidItem) -> dict:
    ingested = await plaid_client.sync_transactions(db, plaid_item)
    clustering_result = await clustering.run_clustering(db, [plaid_item.id])
    scoring_result = await scoring.run_scoring(db, [plaid_item.id])

    merchant_result = await db.execute(select(Merchant))
    merchants_by_id = {m.id: m for m in merchant_result.scalars().all()}

    alerts = [
        serialize_transaction(txn, merchants_by_id[txn.merchant_id].normalized_name)
        for txn in scoring_result["newly_flagged"]
    ]

    return {
        "ingested": ingested,
        "clustering": clustering_result,
        "scoring": {
            "transactions_scored": scoring_result["transactions_scored"],
            "flagged_as_drift": scoring_result["flagged_as_drift"],
        },
        "alerts": alerts,
    }
