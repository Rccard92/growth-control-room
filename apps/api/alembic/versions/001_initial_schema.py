"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-10

"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEFAULT_WORKSPACE_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name=op.f("fk_workspaces_owner_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workspaces")),
    )
    op.create_index(op.f("ix_workspaces_slug"), "workspaces", ["slug"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_projects_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_index(op.f("ix_projects_workspace_id"), "projects", ["workspace_id"], unique=False)

    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="disconnected", nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_integrations_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_integrations")),
        sa.UniqueConstraint("project_id", "type", name="uq_integrations_project_id_type"),
    )
    op.create_index(op.f("ix_integrations_project_id"), "integrations", ["project_id"], unique=False)

    op.create_table(
        "integration_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("encrypted_payload", sa.Text(), server_default="{}", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], name=op.f("fk_integration_credentials_integration_id_integrations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_integration_credentials")),
        sa.UniqueConstraint("integration_id", name=op.f("uq_integration_credentials_integration_id")),
    )

    op.create_table(
        "shopify_stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop_domain", sa.String(length=255), nullable=False),
        sa.Column("shop_name", sa.String(length=255), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="EUR", nullable=False),
        sa.Column("timezone", sa.String(length=100), server_default="Europe/Rome", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], name=op.f("fk_shopify_stores_integration_id_integrations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_stores")),
        sa.UniqueConstraint("integration_id", name=op.f("uq_shopify_stores_integration_id")),
    )

    op.create_table(
        "shopify_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_product_id", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("product_type", sa.String(length=255), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["shopify_stores.id"], name=op.f("fk_shopify_products_store_id_shopify_stores"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_products")),
        sa.UniqueConstraint("store_id", "shopify_product_id", name="uq_shopify_products_store_id_shopify_product_id"),
    )
    op.create_index(op.f("ix_shopify_products_store_id"), "shopify_products", ["store_id"], unique=False)

    op.create_table(
        "shopify_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_order_id", sa.String(length=50), nullable=False),
        sa.Column("order_number", sa.String(length=50), nullable=False),
        sa.Column("total_price", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="EUR", nullable=False),
        sa.Column("financial_status", sa.String(length=50), nullable=True),
        sa.Column("fulfillment_status", sa.String(length=50), nullable=True),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["shopify_stores.id"], name=op.f("fk_shopify_orders_store_id_shopify_stores"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_orders")),
        sa.UniqueConstraint("store_id", "shopify_order_id", name="uq_shopify_orders_store_id_shopify_order_id"),
    )
    op.create_index(op.f("ix_shopify_orders_store_id"), "shopify_orders", ["store_id"], unique=False)

    op.create_table(
        "shopify_daily_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("orders_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("revenue", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("sessions", sa.Integer(), nullable=True),
        sa.Column("conversion_rate", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["shopify_stores.id"], name=op.f("fk_shopify_daily_metrics_store_id_shopify_stores"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_daily_metrics")),
        sa.UniqueConstraint("store_id", "date", name="uq_shopify_daily_metrics_store_id_date"),
    )
    op.create_index(op.f("ix_shopify_daily_metrics_store_id"), "shopify_daily_metrics", ["store_id"], unique=False)

    op.create_table(
        "content_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_content_plans_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_plans")),
    )
    op.create_index(op.f("ix_content_plans_project_id"), "content_plans", ["project_id"], unique=False)

    op.create_table(
        "blog_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["content_plan_id"], ["content_plans.id"], name=op.f("fk_blog_drafts_content_plan_id_content_plans"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_blog_drafts")),
    )
    op.create_index(op.f("ix_blog_drafts_content_plan_id"), "blog_drafts", ["content_plan_id"], unique=False)

    op.create_table(
        "ai_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_ai_runs_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_runs")),
    )
    op.create_index(op.f("ix_ai_runs_project_id"), "ai_runs", ["project_id"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="info", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=100), server_default="system", nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_alerts_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
    )
    op.create_index(op.f("ix_alerts_project_id"), "alerts", ["project_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO users (id, email, name, password_hash)
            VALUES (:user_id, 'dev@gcr.local', 'Dev User', NULL)
            """
        ).bindparams(user_id=DEFAULT_USER_ID)
    )
    op.execute(
        sa.text(
            """
            INSERT INTO workspaces (id, name, slug, owner_id)
            VALUES (:workspace_id, 'Default', 'default', :user_id)
            """
        ).bindparams(workspace_id=DEFAULT_WORKSPACE_ID, user_id=DEFAULT_USER_ID)
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_alerts_project_id"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_ai_runs_project_id"), table_name="ai_runs")
    op.drop_table("ai_runs")
    op.drop_index(op.f("ix_blog_drafts_content_plan_id"), table_name="blog_drafts")
    op.drop_table("blog_drafts")
    op.drop_index(op.f("ix_content_plans_project_id"), table_name="content_plans")
    op.drop_table("content_plans")
    op.drop_index(op.f("ix_shopify_daily_metrics_store_id"), table_name="shopify_daily_metrics")
    op.drop_table("shopify_daily_metrics")
    op.drop_index(op.f("ix_shopify_orders_store_id"), table_name="shopify_orders")
    op.drop_table("shopify_orders")
    op.drop_index(op.f("ix_shopify_products_store_id"), table_name="shopify_products")
    op.drop_table("shopify_products")
    op.drop_table("shopify_stores")
    op.drop_table("integration_credentials")
    op.drop_index(op.f("ix_integrations_project_id"), table_name="integrations")
    op.drop_table("integrations")
    op.drop_index(op.f("ix_projects_workspace_id"), table_name="projects")
    op.drop_table("projects")
    op.drop_index(op.f("ix_workspaces_slug"), table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
