from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services import scoring

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


@router.post("/run")
async def run(db: AsyncSession = Depends(get_db)):
    result = await scoring.run_scoring(db)
    return {
        "transactions_scored": result["transactions_scored"],
        "flagged_as_drift": result["flagged_as_drift"],
        "newly_flagged_count": len(result["newly_flagged"]),
    }
