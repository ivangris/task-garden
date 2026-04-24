"""garden domain persistence"""

from alembic import op
import sqlalchemy as sa


revision = "0004_garden_domain"
down_revision = "0003_recommendation_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "garden_state",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("baseline_key", sa.String(length=64), nullable=False),
        sa.Column("stage_key", sa.String(length=64), nullable=False),
        sa.Column("total_xp", sa.Integer(), nullable=False),
        sa.Column("current_level", sa.Integer(), nullable=False),
        sa.Column("total_growth_units", sa.Integer(), nullable=False),
        sa.Column("total_decay_points", sa.Integer(), nullable=False),
        sa.Column("active_task_count", sa.Integer(), nullable=False),
        sa.Column("overdue_task_count", sa.Integer(), nullable=False),
        sa.Column("restored_tile_count", sa.Integer(), nullable=False),
        sa.Column("healthy_tile_count", sa.Integer(), nullable=False),
        sa.Column("lush_tile_count", sa.Integer(), nullable=False),
        sa.Column("health_score", sa.Integer(), nullable=False),
        sa.Column("last_recomputed_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "garden_zones",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("zone_key", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("tile_count", sa.Integer(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "garden_tiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("zone_id", sa.String(length=36), sa.ForeignKey("garden_zones.id"), nullable=False),
        sa.Column("tile_index", sa.Integer(), nullable=False),
        sa.Column("coord_x", sa.Integer(), nullable=False),
        sa.Column("coord_y", sa.Integer(), nullable=False),
        sa.Column("tile_state", sa.String(length=32), nullable=False),
        sa.Column("growth_units", sa.Integer(), nullable=False),
        sa.Column("decay_points", sa.Integer(), nullable=False),
        sa.Column("last_changed_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "plant_instances",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("garden_tile_id", sa.String(length=36), sa.ForeignKey("garden_tiles.id"), nullable=False),
        sa.Column("plant_key", sa.String(length=64), nullable=False),
        sa.Column("growth_stage", sa.String(length=32), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "decoration_instances",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("garden_tile_id", sa.String(length=36), sa.ForeignKey("garden_tiles.id"), nullable=False),
        sa.Column("decoration_key", sa.String(length=64), nullable=False),
        sa.Column("variant_key", sa.String(length=64), nullable=True),
        sa.Column("unlocked_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "xp_ledger",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("xp_amount", sa.Integer(), nullable=False),
        sa.Column("effort_value", sa.Integer(), nullable=False),
        sa.Column("priority_bonus", sa.Integer(), nullable=False),
        sa.Column("streak_multiplier", sa.Float(), nullable=False),
        sa.Column("awarded_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "unlock_ledger",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("unlock_key", sa.String(length=64), nullable=False),
        sa.Column("unlock_type", sa.String(length=32), nullable=False),
        sa.Column("threshold_value", sa.Integer(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "decay_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("task_title", sa.String(length=255), nullable=False),
        sa.Column("days_overdue", sa.Integer(), nullable=False),
        sa.Column("decay_points", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "recovery_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("task_title", sa.String(length=255), nullable=False),
        sa.Column("recovery_points", sa.Integer(), nullable=False),
        sa.Column("xp_amount", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("recovery_events")
    op.drop_table("decay_events")
    op.drop_table("unlock_ledger")
    op.drop_table("xp_ledger")
    op.drop_table("decoration_instances")
    op.drop_table("plant_instances")
    op.drop_table("garden_tiles")
    op.drop_table("garden_zones")
    op.drop_table("garden_state")
