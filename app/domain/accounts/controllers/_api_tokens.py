"""Personal access token controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.params import Parameter

from app.domain.accounts.abilities import TOKEN_ABILITY_DEFINITIONS
from app.domain.accounts.dependencies import provide_personal_access_token_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.schemas import (
    ApiTokenAbility,
    ApiTokenPage,
    PersonalAccessTokenCreate,
    PersonalAccessTokenCreated,
    PersonalAccessTokenItem,
)
from app.domain.accounts.services import DEFAULT_TOKEN_ABILITIES, PersonalAccessTokenService
from app.lib.schema import Message

if TYPE_CHECKING:
    from app.db.models import User as UserModel

__all__ = ("ApiTokenController",)


class ApiTokenController(Controller):
    """Manage personal access tokens for the current user."""

    include_in_schema = False
    guards = [requires_active_user]
    dependencies = {"personal_access_token_service": Provide(provide_personal_access_token_service)}
    signature_namespace = {
        "ApiTokenPage": ApiTokenPage,
        "PersonalAccessTokenCreate": PersonalAccessTokenCreate,
        "PersonalAccessTokenCreated": PersonalAccessTokenCreated,
        "PersonalAccessTokenService": PersonalAccessTokenService,
    }

    @get(component="profile/api-tokens", name="api-tokens.show", path="/api-tokens/")
    async def show_tokens(
        self,
        current_user: UserModel,
        personal_access_token_service: PersonalAccessTokenService,
    ) -> ApiTokenPage:
        """Render the API token management page."""
        tokens = await personal_access_token_service.list_for_user(current_user.id)
        return ApiTokenPage(
            tokens=[
                PersonalAccessTokenItem(
                    id=token.id,
                    name=token.name,
                    abilities=token.abilities,
                    created_at=token.created_at,
                    last_used_at=token.last_used_at,
                    expires_at=token.expires_at,
                )
                for token in tokens
            ],
            available_abilities=[
                ApiTokenAbility(value=definition.key, label=definition.label, description=definition.description)
                for definition in TOKEN_ABILITY_DEFINITIONS
            ],
            default_abilities=list(DEFAULT_TOKEN_ABILITIES),
        )

    @post(name="api-tokens.create", path="/api-tokens/")
    async def create_token(
        self,
        current_user: UserModel,
        personal_access_token_service: PersonalAccessTokenService,
        data: PersonalAccessTokenCreate,
    ) -> PersonalAccessTokenCreated:
        """Create a new personal access token."""
        token, plain_token = await personal_access_token_service.create_token(
            user=current_user,
            name=data.name,
            abilities=data.abilities,
        )
        return PersonalAccessTokenCreated(
            token=plain_token,
            item=PersonalAccessTokenItem(
                id=token.id,
                name=token.name,
                abilities=token.abilities,
                created_at=token.created_at,
                last_used_at=token.last_used_at,
                expires_at=token.expires_at,
            ),
        )

    @delete(name="api-tokens.delete", path="/api-tokens/{token_id:uuid}/")
    async def revoke_token(
        self,
        current_user: UserModel,
        personal_access_token_service: PersonalAccessTokenService,
        token_id: Annotated[UUID, Parameter(title="Token ID", description="The token to revoke.")],
    ) -> Message:
        """Revoke one of the current user's personal access tokens."""
        await personal_access_token_service.revoke_token(token_id=token_id, user_id=current_user.id)
        return Message(message="API token revoked.")
