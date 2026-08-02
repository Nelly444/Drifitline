from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    # Nullable in Step 1 so existing rows/writers keep working; tightened to
    # NOT NULL in Step 5 once every writer populates it.
    plaid_item_id: Mapped[int | None] = mapped_column(ForeignKey("plaid_items.id"))
    forecast_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    forecast_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
