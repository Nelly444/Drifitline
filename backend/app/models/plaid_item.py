import uuid
from datetime import datetime

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PlaidItem(Base):
    __tablename__ = "plaid_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable in Step 1 so existing rows/writers keep working; tightened to
    # NOT NULL in Step 5 once every writer populates it.
    user_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    item_id: Mapped[str] = mapped_column(unique=True)
    access_token: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
