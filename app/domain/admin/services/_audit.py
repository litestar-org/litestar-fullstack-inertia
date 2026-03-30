from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy import Integer, func, select

from app.db.models import AuditAction, AuditLog, Team
from app.db.models import User as UserModel

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models import User


class AuditLogService(SQLAlchemyAsyncRepositoryService[AuditLog]):
    """Service for managing audit log entries."""

    class Repo(SQLAlchemyAsyncRepository[AuditLog]):
        """Audit log repository."""

        model_type = AuditLog

    repository_type = Repo

    async def get_dashboard_stats(self) -> dict[str, int]:
        """Return aggregate statistics for the admin dashboard."""
        session = self.repository.session

        user_stats = await session.execute(
            select(
                func.count(UserModel.id).label("total"),
                func.sum(func.cast(UserModel.is_active, Integer)).label("active"),
                func.sum(func.cast(UserModel.is_verified, Integer)).label("verified"),
            ),
        )
        user_row = user_stats.one()

        team_count_result = await session.execute(select(func.count(Team.id)))
        recent_signups_result = await session.execute(
            select(func.count(UserModel.id)).where(UserModel.created_at >= (datetime.now(UTC) - timedelta(days=7))),
        )

        return {
            "total_users": int(user_row.total or 0),
            "active_users": int(user_row.active or 0),
            "verified_users": int(user_row.verified or 0),
            "total_teams": int(team_count_result.scalar() or 0),
            "recent_signups": int(recent_signups_result.scalar() or 0),
        }

    async def log_action(
        self,
        *,
        actor: User,
        action: AuditAction,
        target_type: str,
        target_id: UUID,
        target_label: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log an administrative action.

        Args:
            actor: The user performing the action.
            action: The type of action being performed.
            target_type: The type of entity being acted upon (e.g., "user", "team").
            target_id: The ID of the target entity.
            target_label: Optional human-readable label for the target.
            details: Optional additional context about the action.
            ip_address: Optional IP address of the actor.
            user_agent: Optional user agent string.

        Returns:
            The created audit log entry.
        """
        return await self.create({
            "actor_id": actor.id,
            "actor_email": actor.email,
            "action": action.value,
            "target_type": target_type,
            "target_id": target_id,
            "target_label": target_label,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
        })
