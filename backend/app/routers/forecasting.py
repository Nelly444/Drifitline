from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services import scoring

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


@router.post("/run")
async def run(db: AsyncSession = Depends(get_db)):
    return await scoring.run_scoring(db)
