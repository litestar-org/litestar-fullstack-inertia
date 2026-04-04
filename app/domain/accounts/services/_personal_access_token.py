from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from litestar.exceptions import NotFoundException, ValidationException

from app.db.models import PersonalAccessToken
from app.domain.accounts.abilities import DEFAULT_TOKEN_ABILITIES, TOKEN_ABILITY_DEFINITIONS, TOKEN_ABILITY_KEYS

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models import User


class PersonalAccessTokenService(SQLAlchemyAsyncRepositoryService[PersonalAccessToken]):
    """Manage personal access tokens for bearer-token authentication."""

    class Repo(SQLAlchemyAsyncRepository[PersonalAccessToken]):
        model_type = PersonalAccessToken

    repository_type = Repo

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _generate_plaintext_token() -> str:
        return f"lst_{secrets.token_urlsafe(32)}"

    @staticmethod
    def normalize_abilities(abilities: list[str] | None = None) -> list[str]:
        values = list(abilities or DEFAULT_TOKEN_ABILITIES)
        invalid = sorted(set(values) - TOKEN_ABILITY_KEYS)
        if invalid:
            msg = f"Unknown token abilities: {', '.join(invalid)}"
            raise ValidationException(msg)

        order = {definition.key: index for index, definition in enumerate(TOKEN_ABILITY_DEFINITIONS)}
        return sorted(set(values), key=lambda value: order[value])

    async def create_token(
        self,
        *,
        user: User,
        name: str,
        abilities: list[str] | None = None,
    ) -> tuple[PersonalAccessToken, str]:
        token_name = name.strip()
        if not token_name:
            msg = "Token name is required."
            raise ValidationException(msg)

        plain_text_token = self._generate_plaintext_token()
        db_obj = await self.create(
            {
                "user_id": user.id,
                "name": token_name,
                "token_hash": self._hash_token(plain_text_token),
                "abilities": self.normalize_abilities(abilities),
            },
            auto_commit=True,
        )
        return db_obj, plain_text_token

    async def verify_token(self, plain_text_token: str) -> PersonalAccessToken | None:
        db_obj = await self.get_one_or_none(token_hash=self._hash_token(plain_text_token))
        if db_obj is None:
            return None

        last_used_at = datetime.now(UTC)
        db_obj = await self.update(
            item_id=db_obj.id,
            data={"last_used_at": last_used_at},
            auto_commit=True,
        )
        return db_obj

    async def list_for_user(self, user_id: UUID) -> list[PersonalAccessToken]:
        items = await self.list(user_id=user_id)
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    async def revoke_token(self, *, token_id: UUID, user_id: UUID) -> None:
        db_obj = await self.get_one_or_none(id=token_id, user_id=user_id)
        if db_obj is None:
            msg = "API token not found."
            raise NotFoundException(msg)
        await self.delete(db_obj.id, auto_commit=True)

    @staticmethod
    def has_ability(token: PersonalAccessToken, required_ability: str) -> bool:
        return "*" in token.abilities or required_ability in token.abilities
