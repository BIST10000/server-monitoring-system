"""init schema

Revision ID: 001_init
Revises: 
Create Date: 2026-03-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "servers",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False, server_default="prod"),
        sa.Column("labels", sa.dialects.postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_servers_name", "servers", ["name"], unique=True)
    op.create_index("ix_servers_environment", "servers", ["environment"], unique=False)

    op.create_table(
        "heartbeats",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("server_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_version", sa.String(length=50), nullable=True),
        sa.Column("payload", sa.dialects.postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_heartbeats_server_id", "heartbeats", ["server_id"], unique=False)
    op.create_index("ix_heartbeats_created_at", "heartbeats", ["created_at"], unique=False)

    op.create_table(
        "metric_points",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("server_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("tags", sa.dialects.postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_metric_points_server_id", "metric_points", ["server_id"], unique=False)
    op.create_index("ix_metric_points_name", "metric_points", ["name"], unique=False)
    op.create_index("ix_metric_points_ts", "metric_points", ["ts"], unique=False)
    op.create_index("ix_metric_points_server_name_ts", "metric_points", ["server_id", "name", "ts"], unique=False)

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("metric_name", sa.String(length=200), nullable=False),
        sa.Column("comparator", sa.String(length=10), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("window_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("labels", sa.dialects.postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_alert_rules_name", "alert_rules", ["name"], unique=True)
    op.create_index("ix_alert_rules_metric_name", "alert_rules", ["metric_name"], unique=False)
    op.create_index("ix_alert_rules_enabled", "alert_rules", ["enabled"], unique=False)

    op.create_table(
        "alert_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("rule_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("server_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="firing"),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("details", sa.dialects.postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_alert_events_rule_id", "alert_events", ["rule_id"], unique=False)
    op.create_index("ix_alert_events_server_id", "alert_events", ["server_id"], unique=False)
    op.create_index("ix_alert_events_status", "alert_events", ["status"], unique=False)
    op.create_index("ix_alert_events_created_at", "alert_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_alert_events_created_at", table_name="alert_events")
    op.drop_index("ix_alert_events_status", table_name="alert_events")
    op.drop_index("ix_alert_events_server_id", table_name="alert_events")
    op.drop_index("ix_alert_events_rule_id", table_name="alert_events")
    op.drop_table("alert_events")

    op.drop_index("ix_alert_rules_enabled", table_name="alert_rules")
    op.drop_index("ix_alert_rules_metric_name", table_name="alert_rules")
    op.drop_index("ix_alert_rules_name", table_name="alert_rules")
    op.drop_table("alert_rules")

    op.drop_index("ix_metric_points_server_name_ts", table_name="metric_points")
    op.drop_index("ix_metric_points_ts", table_name="metric_points")
    op.drop_index("ix_metric_points_name", table_name="metric_points")
    op.drop_index("ix_metric_points_server_id", table_name="metric_points")
    op.drop_table("metric_points")

    op.drop_index("ix_heartbeats_created_at", table_name="heartbeats")
    op.drop_index("ix_heartbeats_server_id", table_name="heartbeats")
    op.drop_table("heartbeats")

    op.drop_index("ix_servers_environment", table_name="servers")
    op.drop_index("ix_servers_name", table_name="servers")
    op.drop_table("servers")

