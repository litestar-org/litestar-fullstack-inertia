"""Admin dashboard controller."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy import Integer, func, select

from app.db.models import Team
from app.db.models import User as UserModel
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.dependencies import provide_audit_service
from app.domain.admin.schemas import AdminDashboardPage, AdminStats, AuditLogItem
from app.domain.admin.services import AuditLogService

__all__ = ("AdminDashboardController",)


class AdminDashboardController(Controller):
    """Admin dashboard."""

    tags = ["Admin"]
    path = "/admin"
    guards = [requires_superuser]
    dependencies = {"audit_service": Provide(provide_audit_service)}

    @get(component="admin/dashboard", name="admin.dashboard", operation_id="AdminDashboard", path="/")
    async def dashboard(self, audit_service: AuditLogService) -> AdminDashboardPage:
        """Admin dashboard with overview statistics.

        Returns:
            Dashboard page with stats and recent activity.
        """
        session = audit_service.repository.session

        # Get user statistics
        user_stats = await session.execute(
            select(
                func.count(UserModel.id).label("total"),
                func.sum(func.cast(UserModel.is_active, Integer)).label("active"),
                func.sum(func.cast(UserModel.is_verified, Integer)).label("verified"),
            )
        )
        user_row = user_stats.one()

        # Get team count
        team_count_result = await session.execute(select(func.count(Team.id)))
        team_count = team_count_result.scalar() or 0

        # Get recent signups (last 7 days)
        week_ago = datetime.now(UTC) - timedelta(days=7)
        recent_signups_result = await session.execute(
            select(func.count(UserModel.id)).where(UserModel.created_at >= week_ago)
        )
        recent_signups = recent_signups_result.scalar() or 0

        # Get recent audit logs
        recent_logs_result, _ = await audit_service.list_and_count(LimitOffset(limit=10, offset=0))

        return AdminDashboardPage(
            stats=AdminStats(
                total_users=user_row.total or 0,
                active_users=int(user_row.active or 0),
                verified_users=int(user_row.verified or 0),
                total_teams=team_count,
                recent_signups=recent_signups,
            ),
            recent_logs=[
                AuditLogItem(
                    id=log.id,
                    actor_email=log.actor_email,
                    action=log.action,
                    target_type=log.target_type,
                    target_id=log.target_id,
                    target_label=log.target_label,
                    details=log.details,
                    ip_address=log.ip_address,
                    created_at=log.created_at,
                )
                for log in recent_logs_result
            ],
        )
