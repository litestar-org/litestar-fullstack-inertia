"""Add personal access tokens and user sessions

Revision ID: b7e4f2c9d1a0
Revises: 1f2d9a6c1b3e
Create Date: 2026-03-30 00:00:00.000000+00:00

"""

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import GUID, DateTimeUTC
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC

revision = "b7e4f2c9d1a0"
down_revision = "1f2d9a6c1b3e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()
            data_upgrades()


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            data_downgrades()
            schema_downgrades()


def schema_upgrades() -> None:
    """Schema upgrade migrations go here."""
    op.create_table(
        "personal_access_token",
        sa.Column("id", sa.GUID(length=16), nullable=False),
        sa.Column("user_id", sa.GUID(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("abilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("last_used_at", sa.DateTimeUTC(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTimeUTC(timezone=True), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTimeUTC(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTimeUTC(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_account.id"],
            name=op.f("fk_personal_access_token_user_id_user_account"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_personal_access_token")),
    )
    with op.batch_alter_table("personal_access_token", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_personal_access_token_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_personal_access_token_token_hash"), ["token_hash"], unique=True)
        batch_op.create_index(batch_op.f("ix_personal_access_token_expires_at"), ["expires_at"], unique=False)

    op.create_table(
        "user_session",
        sa.Column("id", sa.GUID(length=16), nullable=False),
        sa.Column("user_id", sa.GUID(length=16), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("last_activity", sa.DateTimeUTC(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTimeUTC(timezone=True), nullable=True),
        sa.Column("browser", sa.String(length=100), nullable=True),
        sa.Column("browser_version", sa.String(length=50), nullable=True),
        sa.Column("os", sa.String(length=100), nullable=True),
        sa.Column("os_version", sa.String(length=50), nullable=True),
        sa.Column("device_type", sa.String(length=20), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTimeUTC(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTimeUTC(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user_account.id"], name=op.f("fk_user_session_user_id_user_account"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_session")),
    )
    with op.batch_alter_table("user_session", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_session_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_user_session_session_id"), ["session_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_user_session_expires_at"), ["expires_at"], unique=False)


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    with op.batch_alter_table("user_session", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_session_expires_at"))
        batch_op.drop_index(batch_op.f("ix_user_session_session_id"))
        batch_op.drop_index(batch_op.f("ix_user_session_user_id"))
    op.drop_table("user_session")

    with op.batch_alter_table("personal_access_token", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_personal_access_token_expires_at"))
        batch_op.drop_index(batch_op.f("ix_personal_access_token_token_hash"))
        batch_op.drop_index(batch_op.f("ix_personal_access_token_user_id"))
    op.drop_table("personal_access_token")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here."""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here."""
