from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_db
from app.models import User
from app.services import scoring
from app.services.tenancy import plaid_item_ids_for_user

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


@router.post("/run")
async def run(db: AsyncSession = Depends(get_db), user: User = Depends(current_active_user)):
    plaid_item_ids = await plaid_item_ids_for_user(db, user.id)
    result = await scoring.run_scoring(db, plaid_item_ids)
    return {
        "transactions_scored": result["transactions_scored"],
        "flagged_as_drift": result["flagged_as_drift"],
        "newly_flagged_count": len(result["newly_flagged"]),
    }
