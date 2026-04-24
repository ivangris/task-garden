"""recap engine persistence"""

from alembic import op
import sqlalchemy as sa


revision = "0005_recaps"
down_revision = "0004_garden_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recap_periods",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("period_type", sa.String(length=16), nullable=False),
        sa.Column("period_label", sa.String(length=128), nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("window_end", sa.DateTime(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "recap_metric_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("period_id", sa.String(length=36), sa.ForeignKey("recap_periods.id"), nullable=False),
        sa.Column("metric_key", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("numeric_value", sa.Float(), nullable=True),
        sa.Column("text_value", sa.Text(), nullable=True),
        sa.Column("json_value_json", sa.Text(), nullable=True),
    )

    op.create_table(
        "highlight_cards",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("period_id", sa.String(length=36), sa.ForeignKey("recap_periods.id"), nullable=False),
        sa.Column("card_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("subtitle", sa.String(length=255), nullable=True),
        sa.Column("primary_value", sa.String(length=255), nullable=True),
        sa.Column("secondary_value", sa.String(length=255), nullable=True),
        sa.Column("supporting_text", sa.Text(), nullable=True),
        sa.Column("visual_hint", sa.String(length=64), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "milestones",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("period_id", sa.String(length=36), sa.ForeignKey("recap_periods.id"), nullable=False),
        sa.Column("milestone_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Integer(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "streak_summaries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("period_id", sa.String(length=36), sa.ForeignKey("recap_periods.id"), nullable=False, unique=True),
        sa.Column("current_streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_best_streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak_start", sa.DateTime(), nullable=True),
        sa.Column("streak_end", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "project_summaries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("period_id", sa.String(length=36), sa.ForeignKey("recap_periods.id"), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("completed_task_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp_gained", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_share", sa.Float(), nullable=False, server_default="0"),
        sa.Column("effort_small_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("effort_medium_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("effort_large_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latest_completion_at", sa.DateTime(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("project_summaries")
    op.drop_table("streak_summaries")
    op.drop_table("milestones")
    op.drop_table("highlight_cards")
    op.drop_table("recap_metric_snapshots")
    op.drop_table("recap_periods")
