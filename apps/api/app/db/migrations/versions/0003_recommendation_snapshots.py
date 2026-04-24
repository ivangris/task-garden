"""recommendation snapshots"""

from alembic import op
import sqlalchemy as sa


revision = "0003_recommendation_snapshots"
down_revision = "0002_audio_transcripts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendation_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("snapshot_kind", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=True),
        sa.Column("window_end", sa.DateTime(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("recommendation_snapshots")
