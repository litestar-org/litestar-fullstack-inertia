"""User profile controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, Request, delete, get, patch
from litestar.di import Provide
from litestar_vite.inertia import InertiaRedirect, flash

from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.schemas import PasswordUpdate, ProfileUpdate, User
from app.domain.accounts.services import UserService
from app.lib.schema import Message

if TYPE_CHECKING:
    from app.db.models import User as UserModel

__all__ = ("ProfileController",)


class ProfileController(Controller):
    """User profile management."""

    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {
        "UserService": UserService,
        "User": User,
        "ProfileUpdate": ProfileUpdate,
        "PasswordUpdate": PasswordUpdate,
    }
    guards = [requires_active_user]

    @get(component="profile/edit", name="profile.show", path="/profile/")
    async def profile(self, current_user: UserModel, users_service: UserService) -> User:
        """Display the user profile page.

        Returns:
            Current user data for profile display.
        """
        return users_service.to_schema(current_user, schema_type=User)

    @patch(component="profile/edit", name="profile.update", path="/profile/")
    async def update_profile(self, current_user: UserModel, data: ProfileUpdate, users_service: UserService) -> User:
        """Update the current user's profile information.

        Returns:
            Updated user data.
        """
        db_obj = await users_service.update(data, item_id=current_user.id)
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(component="profile/edit", name="password.update", path="/profile/password-update/")
    async def update_password(
        self, current_user: UserModel, data: PasswordUpdate, users_service: UserService,
    ) -> Message:
        """Update the current user's password.

        Returns:
            Success message confirming password update.
        """
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return Message(message="Your password was successfully modified.")

    @delete(name="account.remove", path="/profile/", status_code=303)
    async def remove_account(
        self, request: Request, current_user: UserModel, users_service: UserService,
    ) -> InertiaRedirect:
        """Remove the current user's account from the system.

        Returns:
            Redirect to landing page after account deletion.
        """
        request.session.clear()
        _ = await users_service.delete(current_user.id)
        flash(request, "Your account has been removed from the system.", category="info")
        return InertiaRedirect(request, request.url_for("landing"))
