from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Merchant, PlaidItem
from app.services import clustering, plaid_client, scoring
from app.services.serializers import serialize_transaction


async def run_pipeline(db: AsyncSession) -> dict:
    result = await db.execute(select(PlaidItem).order_by(PlaidItem.id.desc()).limit(1))
    plaid_item = result.scalar_one_or_none()
    if plaid_item is None:
        return {"ingested": 0, "clustering": None, "scoring": None, "alerts": []}

    ingested = await plaid_client.sync_transactions(db, plaid_item)
    # TODO(Step 6): this still only ever resolves "the single most recent
    # PlaidItem in the whole table" above, not per-tenant fan-out - that's the
    # next step. Scoping the clustering/scoring calls here now so the app
    # keeps working in the meantime.
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
