"""recap narratives persistence"""

from alembic import op
import sqlalchemy as sa


revision = "0006_recap_narratives"
down_revision = "0005_recaps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recap_narratives",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("period_id", sa.String(length=36), sa.ForeignKey("recap_periods.id"), nullable=False, unique=True),
        sa.Column("generation_status", sa.String(length=32), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("source_summary_version", sa.String(length=32), nullable=False),
        sa.Column("source_summary_hash", sa.String(length=128), nullable=False),
        sa.Column("narrative_text", sa.Text(), nullable=True),
        sa.Column("error_metadata_json", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("recap_narratives")
