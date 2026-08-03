from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_db
from app.models import PlaidItem, Subscription, Transaction, User
from app.services import plaid_client
from app.services.rate_limit import rate_limit
from app.services.tenancy import plaid_item_ids_for_user

router = APIRouter(prefix="/plaid", tags=["plaid"])


@router.post("/sandbox-link", dependencies=[Depends(rate_limit(10, 60))])
async def sandbox_link(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    plaid_item = await plaid_client.create_sandbox_item(db, user.id)
    return {"item_id": plaid_item.item_id}


@router.post("/sync", dependencies=[Depends(rate_limit(20, 60))])
async def sync(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    result = await db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user.id).order_by(PlaidItem.id.desc()).limit(1)
    )
    plaid_item = result.scalar_one_or_none()
    if plaid_item is None:
        raise HTTPException(status_code=400, detail="No Plaid item linked yet. Call /plaid/sandbox-link first.")

    ingested = await plaid_client.sync_transactions(db, plaid_item)
    return {"ingested": ingested}


@router.get("/status")
async def status(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    result = await db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user.id).order_by(PlaidItem.id.desc()).limit(1)
    )
    plaid_item = result.scalar_one_or_none()
    if plaid_item is None:
        return {"connected": False, "linked_at": None}
    return {"connected": True, "linked_at": plaid_item.created_at.isoformat()}


@router.delete("/item", dependencies=[Depends(rate_limit(10, 60))])
async def disconnect(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    plaid_item_ids = await plaid_item_ids_for_user(db, user.id)
    if not plaid_item_ids:
        raise HTTPException(status_code=400, detail="No Plaid item linked.")

    await db.execute(delete(Transaction).where(Transaction.plaid_item_id.in_(plaid_item_ids)))
    await db.execute(delete(Subscription).where(Subscription.plaid_item_id.in_(plaid_item_ids)))
    await db.execute(delete(PlaidItem).where(PlaidItem.id.in_(plaid_item_ids)))
    await db.commit()
    return {"disconnected": True}
