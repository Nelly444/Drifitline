from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services import clustering

router = APIRouter(prefix="/clustering", tags=["clustering"])


@router.post("/run")
async def run(db: AsyncSession = Depends(get_db)):
    return await clustering.run_clustering(db)
