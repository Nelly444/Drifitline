from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import PlaidItem
from app.services import plaid_client

router = APIRouter(prefix="/plaid", tags=["plaid"])


@router.post("/sandbox-link")
async def sandbox_link(db: AsyncSession = Depends(get_db)):
    plaid_item = await plaid_client.create_sandbox_item(db)
    return {"item_id": plaid_item.item_id}


@router.post("/sync")
async def sync(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlaidItem).order_by(PlaidItem.id.desc()).limit(1))
    plaid_item = result.scalar_one_or_none()
    if plaid_item is None:
        raise HTTPException(status_code=400, detail="No Plaid item linked yet. Call /plaid/sandbox-link first.")

    ingested = await plaid_client.sync_transactions(db, plaid_item)
    return {"ingested": ingested}
