import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PlaidItem


async def plaid_item_ids_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[int]:
    result = await db.execute(select(PlaidItem.id).where(PlaidItem.user_id == user_id))
    return list(result.scalars().all())
