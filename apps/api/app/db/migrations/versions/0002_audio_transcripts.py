"""audio transcript support"""

from alembic import op
import sqlalchemy as sa


revision = "0002_audio_transcripts"
down_revision = "0001_phase0_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("raw_entries", sa.Column("transcript_provider_name", sa.String(length=64), nullable=True))
    op.add_column("raw_entries", sa.Column("transcript_model_name", sa.String(length=128), nullable=True))
    op.add_column("raw_entries", sa.Column("transcript_metadata_json", sa.Text(), nullable=True))

    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("raw_entry_id", sa.String(length=36), sa.ForeignKey("raw_entries.id"), nullable=False),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=True),
        sa.Column("end_ms", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("speaker_label", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("transcript_segments")
    op.drop_column("raw_entries", "transcript_metadata_json")
    op.drop_column("raw_entries", "transcript_model_name")
    op.drop_column("raw_entries", "transcript_provider_name")
