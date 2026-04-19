"""phase0 foundation"""

from alembic import op
import sqlalchemy as sa


revision = "0001_phase0_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_entries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("audio_file_ref", sa.String(length=255), nullable=True),
        sa.Column("entry_status", sa.String(length=32), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "extraction_batches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("raw_entry_id", sa.String(length=36), sa.ForeignKey("raw_entries.id"), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("open_questions_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "extracted_task_candidates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("extraction_batch_id", sa.String(length=36), sa.ForeignKey("extraction_batches.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("project_or_group", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("effort", sa.String(length=16), nullable=False),
        sa.Column("energy", sa.String(length=16), nullable=False),
        sa.Column("labels_json", sa.Text(), nullable=True),
        sa.Column("due_date", sa.String(length=32), nullable=True),
        sa.Column("parent_task_title", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_excerpt", sa.Text(), nullable=True),
        sa.Column("candidate_status", sa.String(length=32), nullable=False, server_default="pending_review"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color_token", sa.String(length=64), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("effort", sa.String(length=16), nullable=False),
        sa.Column("energy", sa.String(length=16), nullable=False),
        sa.Column("source_raw_entry_id", sa.String(length=36), sa.ForeignKey("raw_entries.id"), nullable=True),
        sa.Column("source_extraction_batch_id", sa.String(length=36), sa.ForeignKey("extraction_batches.id"), nullable=True),
        sa.Column("parent_task_id", sa.String(length=36), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("sync_status", sa.String(length=32), nullable=False, server_default="local_only"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "activity_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("activity_events")
    op.drop_table("tasks")
    op.drop_table("projects")
    op.drop_table("extracted_task_candidates")
    op.drop_table("extraction_batches")
    op.drop_table("raw_entries")

