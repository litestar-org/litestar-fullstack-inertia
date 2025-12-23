from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db.models import AuditAction, AuditLog

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models import User


class AuditLogService(SQLAlchemyAsyncRepositoryService[AuditLog]):
    """Service for managing audit log entries."""

    class Repo(SQLAlchemyAsyncRepository[AuditLog]):
        """Audit log repository."""

        model_type = AuditLog

    repository_type = Repo

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
