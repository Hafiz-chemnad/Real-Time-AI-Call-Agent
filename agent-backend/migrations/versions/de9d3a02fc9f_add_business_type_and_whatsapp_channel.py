"""add business_type and whatsapp channel

Revision ID: de9d3a02fc9f
Revises: 54186b2fed3f
Create Date: 2026-08-10 11:03:09.643144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de9d3a02fc9f'
down_revision: Union[str, Sequence[str], None] = '54186b2fed3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    ALTER TABLE businesses
        ADD COLUMN business_type VARCHAR(20) NOT NULL DEFAULT 'general'
            CHECK (business_type IN ('delivery', 'appointment', 'general'));

    ALTER TABLE call_logs
        DROP CONSTRAINT IF EXISTS call_logs_channel_check;

    ALTER TABLE call_logs
        ADD CONSTRAINT call_logs_channel_check
            CHECK (channel IN ('phone', 'chat', 'voice_web', 'whatsapp'));
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    ALTER TABLE call_logs
        DROP CONSTRAINT IF EXISTS call_logs_channel_check;

    ALTER TABLE call_logs
        ADD CONSTRAINT call_logs_channel_check
            CHECK (channel IN ('phone', 'chat', 'voice_web'));

    ALTER TABLE businesses
        DROP COLUMN IF EXISTS business_type;
    """)