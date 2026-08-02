from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_db
from app.models import User
from app.services import clustering
from app.services.tenancy import plaid_item_ids_for_user

router = APIRouter(prefix="/clustering", tags=["clustering"])


@router.post("/run")
async def run(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    plaid_item_ids = await plaid_item_ids_for_user(db, user.id)
    return await clustering.run_clustering(db, plaid_item_ids)
