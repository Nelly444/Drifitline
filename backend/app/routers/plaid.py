from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_db
from app.models import PlaidItem, User
from app.services import plaid_client

router = APIRouter(prefix="/plaid", tags=["plaid"])


@router.post("/sandbox-link")
async def sandbox_link(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    plaid_item = await plaid_client.create_sandbox_item(db, user.id)
    return {"item_id": plaid_item.item_id}


@router.post("/sync")
async def sync(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    result = await db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user.id).order_by(PlaidItem.id.desc()).limit(1)
    )
    plaid_item = result.scalar_one_or_none()
    if plaid_item is None:
        raise HTTPException(status_code=400, detail="No Plaid item linked yet. Call /plaid/sandbox-link first.")

    ingested = await plaid_client.sync_transactions(db, plaid_item)
    return {"ingested": ingested}
