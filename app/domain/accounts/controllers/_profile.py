"""User profile controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, Request, delete, get, patch, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
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

    @post(path="/profile/avatar/", name="profile.avatar.upload", status_code=303)
    async def upload_avatar(
        self,
        request: Request,
        current_user: UserModel,
        users_service: UserService,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    ) -> InertiaRedirect:
        """Upload user avatar.

        Accepts multipart form with file upload.

        Returns:
            Redirect to profile page.
        """
        content = await data.read()
        await users_service.upload_avatar(
            user=current_user,
            content=content,
            content_type=data.content_type or "application/octet-stream",
            original_filename=data.filename or "avatar",
        )
        flash(request, "Avatar updated successfully.", category="success")
        return InertiaRedirect(request, request.url_for("profile.show"))

    @delete(path="/profile/avatar/", name="profile.avatar.delete", status_code=303)
    async def delete_avatar(
        self,
        request: Request,
        current_user: UserModel,
        users_service: UserService,
    ) -> InertiaRedirect:
        """Delete user avatar and revert to Gravatar.

        Returns:
            Redirect to profile page.
        """
        await users_service.delete_avatar(current_user)
        flash(request, "Avatar removed. Using Gravatar.", category="success")
        return InertiaRedirect(request, request.url_for("profile.show"))
