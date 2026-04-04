from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy import delete, or_, select

from app.db.models import SessionStore, UserSession
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models import User


class UserSessionService(SQLAlchemyAsyncRepositoryService[UserSession]):
    """Track and manage browser-session metadata."""

    class Repo(SQLAlchemyAsyncRepository[UserSession]):
        model_type = UserSession

    repository_type = Repo

    @staticmethod
    def _extract_version(user_agent: str, pattern: str) -> str | None:
        match = re.search(pattern, user_agent, flags=re.IGNORECASE)
        return match.group(1) if match else None

    @classmethod
    def parse_user_agent(cls, user_agent: str | None) -> dict[str, str]:
        raw = user_agent or ""
        lowered = raw.lower()

        browser = "Unknown Browser"
        browser_version = ""
        if "edg/" in lowered:
            browser = "Edge"
            browser_version = cls._extract_version(raw, r"Edg/([\d.]+)") or ""
        elif "chrome/" in lowered and "chromium/" not in lowered:
            browser = "Chrome"
            browser_version = cls._extract_version(raw, r"Chrome/([\d.]+)") or ""
        elif "firefox/" in lowered:
            browser = "Firefox"
            browser_version = cls._extract_version(raw, r"Firefox/([\d.]+)") or ""
        elif "safari/" in lowered and "chrome/" not in lowered:
            browser = "Safari"
            browser_version = cls._extract_version(raw, r"Version/([\d.]+)") or ""
        elif "python-httpx/" in lowered:
            browser = "HTTPX"
            browser_version = cls._extract_version(raw, r"python-httpx/([\d.]+)") or ""

        os_name = "Unknown OS"
        os_version = ""
        if "windows nt 10.0" in lowered:
            os_name = "Windows"
            os_version = "10"
        elif "windows nt 6.3" in lowered:
            os_name = "Windows"
            os_version = "8.1"
        elif "windows nt 6.2" in lowered:
            os_name = "Windows"
            os_version = "8"
        elif "windows nt 6.1" in lowered:
            os_name = "Windows"
            os_version = "7"
        elif "iphone os" in lowered:
            os_name = "iOS"
            os_version = (cls._extract_version(raw, r"iPhone OS ([\d_]+)") or "").replace("_", ".")
        elif "ipad; cpu os" in lowered:
            os_name = "iPadOS"
            os_version = (cls._extract_version(raw, r"CPU OS ([\d_]+)") or "").replace("_", ".")
        elif "android" in lowered:
            os_name = "Android"
            os_version = cls._extract_version(raw, r"Android ([\d.]+)") or ""
        elif "mac os x" in lowered:
            os_name = "macOS"
            os_version = (cls._extract_version(raw, r"Mac OS X ([\d_]+)") or "").replace("_", ".")
        elif "linux" in lowered:
            os_name = "Linux"

        device_type = "desktop"
        if "ipad" in lowered or "tablet" in lowered:
            device_type = "tablet"
        elif "mobi" in lowered or "iphone" in lowered or "android" in lowered:
            device_type = "mobile"

        browser_label = browser if not browser_version else f"{browser} {browser_version}"
        os_label = os_name if not os_version else f"{os_name} {os_version}"
        return {
            "browser": browser_label,
            "browser_version": browser_version,
            "os": os_label,
            "os_version": os_version,
            "device_type": device_type,
        }

    @staticmethod
    def _session_expiry() -> datetime:
        settings = get_settings()
        return datetime.now(UTC) + timedelta(seconds=settings.app.SESSION_MAX_AGE)

    async def track_session(
        self,
        *,
        user: User,
        session_id: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UserSession:
        parsed = self.parse_user_agent(user_agent)
        payload = {
            "user_id": user.id,
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "last_activity": datetime.now(UTC),
            "expires_at": self._session_expiry(),
            "browser": parsed["browser"],
            "browser_version": parsed["browser_version"],
            "os": parsed["os"],
            "os_version": parsed["os_version"],
            "device_type": parsed["device_type"],
        }

        db_obj = await self.get_one_or_none(session_id=session_id)
        if db_obj is None:
            return await self.create(payload, auto_commit=True)

        db_obj = await self.update(item_id=db_obj.id, data=payload, auto_commit=True)
        return db_obj

    async def list_active_for_user(self, user_id: UUID) -> list[UserSession]:
        rows = await self.list(user_id=user_id)
        if not rows:
            return []

        active_store_rows = await self.repository.session.scalars(
            select(SessionStore).where(
                SessionStore.namespace == get_settings().app.slug,
                SessionStore.key.in_([row.session_id for row in rows]),
                or_(SessionStore.expires_at.is_(None), SessionStore.expires_at > datetime.now(UTC)),
            ),
        )
        active_keys = {row.key for row in active_store_rows}
        stale_rows = [row for row in rows if row.session_id not in active_keys]
        if stale_rows:
            await self.repository.session.execute(delete(UserSession).where(UserSession.id.in_([row.id for row in stale_rows])))
            await self.repository.session.commit()

        active_rows = [row for row in rows if row.session_id in active_keys]
        return sorted(active_rows, key=lambda row: row.last_activity, reverse=True)

    async def destroy_other_sessions(self, *, user_id: UUID, current_session_id: str) -> int:
        rows = await self.list_active_for_user(user_id)
        session_ids = [row.session_id for row in rows if row.session_id != current_session_id]
        if not session_ids:
            return 0

        await self.repository.session.execute(
            delete(SessionStore).where(
                SessionStore.namespace == get_settings().app.slug,
                SessionStore.key.in_(session_ids),
            ),
        )
        await self.repository.session.execute(delete(UserSession).where(UserSession.session_id.in_(session_ids)))
        await self.repository.session.commit()
        return len(session_ids)

    async def destroy_session(self, session_id: str) -> None:
        await self.repository.session.execute(
            delete(SessionStore).where(
                SessionStore.namespace == get_settings().app.slug,
                SessionStore.key == session_id,
            ),
        )
        await self.repository.session.execute(delete(UserSession).where(UserSession.session_id == session_id))
        await self.repository.session.commit()
