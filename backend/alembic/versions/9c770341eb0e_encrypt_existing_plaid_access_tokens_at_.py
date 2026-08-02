"""encrypt existing plaid access tokens at rest

Revision ID: 9c770341eb0e
Revises: 4d7ca3325cb8
Create Date: 2026-08-02 13:49:19.498003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.services.crypto import decrypt, encrypt


# revision identifiers, used by Alembic.
revision: str = '9c770341eb0e'
down_revision: Union[str, Sequence[str], None] = '4d7ca3325cb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Encrypt any plaintext access tokens left over from before ENCRYPTION_KEY existed."""
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, access_token FROM plaid_items")).fetchall()
    for row in rows:
        conn.execute(
            sa.text("UPDATE plaid_items SET access_token = :token WHERE id = :id"),
            {"token": encrypt(row.access_token), "id": row.id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, access_token FROM plaid_items")).fetchall()
    for row in rows:
        conn.execute(
            sa.text("UPDATE plaid_items SET access_token = :token WHERE id = :id"),
            {"token": decrypt(row.access_token), "id": row.id},
        )
