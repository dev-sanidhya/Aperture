"""campaign sequence fields"""

from alembic import op
import sqlalchemy as sa


revision = "20260329_03"
down_revision = "20260329_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("campaign_members", sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("campaign_members", sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("campaign_members", sa.Column("last_reply_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("draft_messages", sa.Column("sequence_step", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("draft_messages", "sequence_step", server_default=None)


def downgrade() -> None:
    op.drop_column("draft_messages", "sequence_step")
    op.drop_column("campaign_members", "last_reply_at")
    op.drop_column("campaign_members", "last_sent_at")
    op.drop_column("campaign_members", "next_due_at")

