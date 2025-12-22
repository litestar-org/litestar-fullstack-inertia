from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import (
    ModelDictT,
    SQLAlchemyAsyncRepositoryService,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)

from app.db.models import EmailToken, TokenType

if TYPE_CHECKING:
    from uuid import UUID


class EmailTokenService(SQLAlchemyAsyncRepositoryService[EmailToken]):
    """Service for managing email tokens.

    Handles creation, validation, and consumption of secure tokens
    for email verification, password reset, and similar flows.

    Tokens are hashed (SHA-256) before storage - plain tokens are
    only returned once during creation.
    """

    class Repo(SQLAlchemyAsyncRepository[EmailToken]):
        """Email Token SQLAlchemy Repository."""

        model_type = EmailToken

    repository_type = Repo

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token using SHA-256.

        Args:
            token: Plain text token to hash.

        Returns:
            SHA-256 hex digest of the token.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _generate_token() -> str:
        """Generate a secure random token.

        Returns:
            URL-safe base64 encoded random token.
        """
        return secrets.token_urlsafe(32)

    async def to_model_on_create(self, data: ModelDictT[EmailToken]) -> ModelDictT[EmailToken]:
        """Auto-hash token if plain token is provided.

        Returns:
            Token data with hashed token.
        """
        data = schema_dump(data)
        if is_dict_with_field(data, "token") and is_dict_without_field(data, "token_hash"):
            data["token_hash"] = self._hash_token(data.pop("token"))
        return data

    async def create_token(
        self,
        email: str,
        token_type: TokenType,
        expires_delta: timedelta,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> tuple[EmailToken, str]:
        """Create a new email token.

        Returns:
            Tuple of (database record, plain token). Plain token should be sent to user via email.
        """
        token = self._generate_token()
        return await self.create(
            {
                "email": email,
                "token_type": token_type,
                "token": token,  # to_model_on_create hashes this
                "expires_at": datetime.now(UTC) + expires_delta,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "metadata_": metadata or {},
            },
            auto_commit=True,
        ), token

    async def validate_token(
        self,
        plain_token: str,
        token_type: TokenType,
        email: str | None = None,
    ) -> EmailToken | None:
        """Validate a token without consuming it.

        Returns:
            EmailToken record if valid, None otherwise.
        """
        token = await self.get_one_or_none(token_hash=self._hash_token(plain_token), token_type=token_type)
        if token is None or not token.is_valid or (email and token.email != email):
            return None
        return token

    async def consume_token(
        self,
        plain_token: str,
        token_type: TokenType,
        email: str | None = None,
    ) -> EmailToken | None:
        """Validate and consume a token. Token cannot be used again after consumption.

        Returns:
            EmailToken record if valid and consumed, None otherwise.
        """
        if (token := await self.validate_token(plain_token, token_type, email)) is None:
            return None
        token.mark_used()
        await self.update(token, auto_commit=True)
        return token

    async def invalidate_existing_tokens(self, email: str, token_type: TokenType) -> int:
        """Invalidate all existing valid tokens of a type for an email.

        Returns:
            Number of tokens invalidated.
        """
        tokens = [t for t in await self.list(email=email, token_type=token_type, used_at=None) if t.is_valid]
        for token in tokens:
            token.mark_used()
            await self.update(token, auto_commit=False)
        if tokens:
            await self.repository.session.commit()
        return len(tokens)
