"""sync readiness persistence"""

from alembic import op
import sqlalchemy as sa


revision = "0007_sync_readiness"
down_revision = "0006_recap_narratives"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("device_name", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=128), nullable=False),
        sa.Column("app_version", sa.String(length=64), nullable=True),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "change_events",
        sa.Column("sequence", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("change_type", sa.String(length=64), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("device_id", sa.String(length=64), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
    )
    op.create_table(
        "sync_cursors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("device_id", sa.String(length=64), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("stream_key", sa.String(length=64), nullable=False),
        sa.Column("cursor_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("sync_cursors")
    op.drop_table("change_events")
    op.drop_table("devices")
