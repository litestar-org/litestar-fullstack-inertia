"""Admin dashboard controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, get
from litestar.di import Provide

from app.domain.accounts.guards import requires_superuser
from app.domain.admin.dependencies import provide_audit_service
from app.domain.admin.schemas import AdminDashboardPage, AdminStats, AuditLogItem

if TYPE_CHECKING:
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
        stats = await audit_service.get_dashboard_stats()
        # Get recent audit logs
        recent_logs_result, _ = await audit_service.list_and_count(LimitOffset(limit=10, offset=0))

        return AdminDashboardPage(
            stats=AdminStats(
                total_users=stats["total_users"],
                active_users=stats["active_users"],
                verified_users=stats["verified_users"],
                total_teams=stats["total_teams"],
                recent_signups=stats["recent_signups"],
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
