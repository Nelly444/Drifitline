"""add unique constraints on merchant raw_name and subscription tenant merchant

Revision ID: 4d7ca3325cb8
Revises: 63998741dce1
Create Date: 2026-08-02 13:35:02.424428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d7ca3325cb8'
down_revision: Union[str, Sequence[str], None] = '63998741dce1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_merchants_raw_name', 'merchants', ['raw_name'])
    op.create_unique_constraint('uq_subscriptions_plaid_item_merchant', 'subscriptions', ['plaid_item_id', 'merchant_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_subscriptions_plaid_item_merchant', 'subscriptions', type_='unique')
    op.drop_constraint('uq_merchants_raw_name', 'merchants', type_='unique')
