from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID  # noqa: TC003

from advanced_alchemy.service import (
    ModelDictT,
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)
from litestar.exceptions import PermissionDeniedException

from app.db.models import Role, User, UserOauthAccount, UserRole
from app.domain.accounts.repositories import (
    RoleRepository,
    UserOauthAccountRepository,
    UserRepository,
    UserRoleRepository,
)
from app.lib import crypt


class UserService(SQLAlchemyAsyncRepositoryService[User]):
    """Handles database operations for users."""

    repository_type = UserRepository
    default_role = "Application Access"

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: UserRepository = self.repository_type(**repo_kwargs)  # pyright: ignore[reportAttributeAccessIssue]
        self.model_type = self.repository.model_type

    async def to_model_on_create(self, data: ModelDictT[User]) -> ModelDictT[User]:
        """Transform data before creating a user."""
        data = schema_dump(data)
        data = await self._populate_with_hashed_password(data)
        return await self._populate_with_role(data)

    async def to_model_on_update(self, data: ModelDictT[User]) -> ModelDictT[User]:
        """Transform data before updating a user."""
        data = schema_dump(data)
        data = await self._populate_with_hashed_password(data)
        return await self._populate_with_role(data)

    async def _populate_with_hashed_password(self, data: ModelDictT[User]) -> ModelDictT[User]:
        """Hash password if provided."""
        if is_dict(data) and (password := data.pop("password", None)) is not None:
            data["hashed_password"] = await crypt.get_password_hash(password)
        return data

    async def _populate_with_role(self, data: ModelDictT[User]) -> ModelDictT[User]:
        """Assign role if role_id provided."""
        if is_dict(data) and (role_id := data.pop("role_id", None)) is not None:
            data = await super().to_model(data)
            data.roles.append(UserRole(role_id=role_id, assigned_at=datetime.now(UTC)))
        return data

    async def authenticate(self, username: str, password: bytes | str) -> User:
        """Authenticate a user.

        Args:
            username: The user's email address.
            password: The user's password.

        Raises:
            PermissionDeniedException: Raised when the user doesn't exist, isn't verified, or is not active.

        Returns:
            User: The user object
        """
        db_obj = await self.get_one_or_none(email=username)
        if db_obj is None:
            msg = "User not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        if db_obj.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not await crypt.verify_password(password, db_obj.hashed_password):
            msg = "User not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        if not db_obj.is_active:
            msg = "User account is inactive"
            raise PermissionDeniedException(detail=msg)
        return db_obj

    async def update_password(self, data: dict[str, Any], db_obj: User) -> None:
        """Update stored user password.

        This is only used when not used IAP authentication.

        Args:
            data (UserPasswordUpdate): _description_
            db_obj (User): _description_

        Raises:
            PermissionDeniedException: _description_
        """
        if db_obj.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not await crypt.verify_password(data["current_password"], db_obj.hashed_password):
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not db_obj.is_active:
            msg = "User account is not active"
            raise PermissionDeniedException(detail=msg)
        db_obj.hashed_password = await crypt.get_password_hash(data["new_password"])
        await self.repository.update(db_obj)

    @staticmethod
    async def has_role_id(db_obj: User, role_id: UUID) -> bool:
        """Return true if user has specified role ID"""
        return any(assigned_role.role_id for assigned_role in db_obj.roles if assigned_role.role_id == role_id)

    @staticmethod
    async def has_role(db_obj: User, role_name: str) -> bool:
        """Return true if user has specified role ID"""
        return any(assigned_role.role_id for assigned_role in db_obj.roles if assigned_role.role_name == role_name)

    @staticmethod
    def is_superuser(user: User) -> bool:
        return bool(
            user.is_superuser
            or any(assigned_role.role.name for assigned_role in user.roles if assigned_role.role.name in {"Superuser"}),
        )


class RoleService(SQLAlchemyAsyncRepositoryService[Role]):
    """Handles database operations for roles."""

    repository_type = RoleRepository
    match_fields = ["name"]

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: RoleRepository = self.repository_type(**repo_kwargs)  # pyright: ignore[reportAttributeAccessIssue]
        self.model_type = self.repository.model_type

    async def to_model_on_create(self, data: ModelDictT[Role]) -> ModelDictT[Role]:
        """Auto-generate slug on create if not provided."""
        data = schema_dump(data)
        if is_dict_without_field(data, "slug"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def to_model_on_update(self, data: ModelDictT[Role]) -> ModelDictT[Role]:
        """Auto-generate slug on update if name changed but no slug provided."""
        data = schema_dump(data)
        if is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data


class UserRoleService(SQLAlchemyAsyncRepositoryService[UserRole]):
    """Handles database operations for user roles."""

    repository_type = UserRoleRepository


class UserOAuthAccountService(SQLAlchemyAsyncRepositoryService[UserOauthAccount]):
    """Handles database operations for user roles."""

    repository_type = UserOauthAccountRepository
