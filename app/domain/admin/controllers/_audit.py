"""Admin audit log controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_dependencies
from litestar import Controller, get
from litestar.params import Dependency

from app.domain.accounts.guards import requires_superuser
from app.domain.admin.schemas import AuditLogItem, AuditLogPage
from app.domain.admin.services import AuditLogService

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes

__all__ = ("AdminAuditController",)


class AdminAuditController(Controller):
    """Audit log viewer."""

    tags = ["Admin - Audit"]
    path = "/admin/audit"
    guards = [requires_superuser]
    dependencies = create_service_dependencies(
        AuditLogService,
        key="audit_service",
        filters={
            "id_filter": UUID,
            "search": "actor_email,action,target_label",
            "pagination_type": "limit_offset",
            "pagination_size": 50,
            "created_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    )

    @get(component="admin/audit/list", name="admin.audit.list", operation_id="AdminListAuditLogs", path="/")
    async def list_audit_logs(
        self, audit_service: AuditLogService, filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> AuditLogPage:
        """List audit log entries.

        Returns:
            Paginated list of audit log entries.
        """
        results, total = await audit_service.list_and_count(*filters)

        return AuditLogPage(
            logs=[
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
                for log in results
            ],
            total=total,
        )
