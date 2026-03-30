"""User profile controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, Request, delete, get, patch, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ValidationException
from litestar.params import Body
from litestar_vite.inertia import InertiaRedirect, flash
from sqlalchemy.orm import undefer_group

from app.domain.accounts.dependencies import provide_user_session_service, provide_users_service
from app.domain.accounts.guards import requires_active_user, requires_token_ability
from app.domain.accounts.schemas import BrowserSessionInfo, BrowserSessionsLogoutOthers, PasswordUpdate, ProfilePage, ProfileUpdate, User
from app.domain.accounts.services import UserService, UserSessionService
from app.lib import crypt
from app.lib.settings import get_settings
from app.lib.schema import Message

if TYPE_CHECKING:
    from app.db.models import User as UserModel

__all__ = ("ProfileController",)


class ProfileController(Controller):
    """User profile management."""

    include_in_schema = False
    dependencies = {
        "users_service": Provide(provide_users_service),
        "user_session_service": Provide(provide_user_session_service),
    }
    signature_namespace = {
        "UserService": UserService,
        "User": User,
        "ProfileUpdate": ProfileUpdate,
        "PasswordUpdate": PasswordUpdate,
        "ProfilePage": ProfilePage,
        "UserSessionService": UserSessionService,
    }
    guards = [requires_active_user]

    @get(component="profile/edit", guards=[requires_token_ability("profile:read")], name="profile.show", path="/profile/")
    async def profile(
        self,
        request: Request,
        current_user: UserModel,
        user_session_service: UserSessionService,
    ) -> ProfilePage:
        """Display the user profile page.

        Returns:
            Current session management props.
        """
        current_session_id = request.cookies.get(get_settings().app.SESSION_COOKIE_NAME) or request.get_session_id()
        sessions = await user_session_service.list_active_for_user(user_id=current_user.id)
        return ProfilePage(
            browser_sessions=[
                BrowserSessionInfo(
                    id=session.id,
                    session_id=session.session_id,
                    ip_address=session.ip_address,
                    browser=session.browser or "Unknown Browser",
                    os=session.os or "Unknown OS",
                    device_type=session.device_type or "desktop",
                    last_activity=session.last_activity,
                    is_current=session.session_id == current_session_id,
                )
                for session in sessions
            ],
        )

    @patch(component="profile/edit", guards=[requires_token_ability("profile:write")], name="profile.update", path="/profile/")
    async def update_profile(self, current_user: UserModel, data: ProfileUpdate, users_service: UserService) -> User:
        """Update the current user's profile information.

        Returns:
            Updated user data.
        """
        db_obj = await users_service.update(data, item_id=current_user.id)
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(
        component="profile/edit",
        guards=[requires_token_ability("profile:write")],
        name="password.update",
        path="/profile/password-update/",
    )
    async def update_password(
        self, current_user: UserModel, data: PasswordUpdate, users_service: UserService,
    ) -> Message:
        """Update the current user's password.

        Returns:
            Success message confirming password update.
        """
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return Message(message="Your password was successfully modified.")

    @delete(guards=[requires_token_ability("profile:write")], name="account.remove", path="/profile/", status_code=303)
    async def remove_account(
        self, request: Request, current_user: UserModel, users_service: UserService,
    ) -> InertiaRedirect:
        """Remove the current user's account from the system.

        Returns:
            Redirect to landing page after account deletion.
        """
        request.clear_session()
        await users_service.delete(current_user.id)
        flash(request, "Your account has been removed from the system.", category="info")
        return InertiaRedirect(request, request.url_for("landing"))

    @post(
        guards=[requires_token_ability("profile:write")], path="/profile/avatar/", name="profile.avatar.upload", status_code=303,
    )
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

    @delete(
        guards=[requires_token_ability("profile:write")], path="/profile/avatar/", name="profile.avatar.delete", status_code=303,
    )
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

    @post(
        guards=[requires_token_ability("profile:write")],
        path="/profile/browser-sessions/logout-others/",
        name="browser-sessions.logout-others",
        status_code=303,
    )
    async def logout_other_browser_sessions(
        self,
        request: Request,
        current_user: UserModel,
        users_service: UserService,
        user_session_service: UserSessionService,
        data: BrowserSessionsLogoutOthers,
    ) -> InertiaRedirect:
        """Log out every browser session except the current one after password confirmation."""
        current_session_id = request.cookies.get(get_settings().app.SESSION_COOKIE_NAME) or request.get_session_id()
        if not current_session_id:
            raise ValidationException("Current session could not be determined.")

        user = await users_service.get_one_or_none(id=current_user.id, load=[undefer_group("security_sensitive")])
        if user is None or user.hashed_password is None:
            raise ValidationException("A password is required to log out other browser sessions.")
        if not await crypt.verify_password(data.password, user.hashed_password):
            raise ValidationException("The provided password is incorrect.")

        destroyed = await user_session_service.destroy_other_sessions(
            user_id=current_user.id,
            current_session_id=current_session_id,
        )
        request.logger.info("Destroyed %s browser sessions for user %s", destroyed, current_user.email)
        flash(request, "Other browser sessions were logged out.", category="success")
        return InertiaRedirect(request, request.url_for("profile.show"))
