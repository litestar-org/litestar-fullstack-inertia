"""Admin controllers."""

from app.domain.admin.controllers._audit import AdminAuditController
from app.domain.admin.controllers._dashboard import AdminDashboardController
from app.domain.admin.controllers._teams import AdminTeamController
from app.domain.admin.controllers._users import AdminUserController

__all__ = (
    "AdminAuditController",
    "AdminDashboardController",
    "AdminTeamController",
    "AdminUserController",
)
