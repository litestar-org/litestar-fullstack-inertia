from __future__ import annotations

from advanced_alchemy.extensions.litestar.store import StoreModelMixin


class SessionStore(StoreModelMixin):
    """Server-side session storage model."""

    __tablename__ = "session_store"
