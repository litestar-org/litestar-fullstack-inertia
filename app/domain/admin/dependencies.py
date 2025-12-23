"""Admin domain dependencies."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from sqlalchemy.orm import joinedload

from app.db.models import AuditLog
from app.domain.admin.services import AuditLogService

provide_audit_service = create_service_provider(
    AuditLogService,
    load=[joinedload(AuditLog.actor)],
)
