from __future__ import annotations

from dataclasses import dataclass

import pytest
from litestar import Litestar
from litestar.testing import RequestFactory

from app.db.models import User
from app.domain.accounts.deps import provide_user

pytestmark = pytest.mark.anyio


@dataclass
class MessageTest:
    test_attr: str


def test_provide_user_dependency() -> None:
    user = User()
    request = RequestFactory(app=Litestar(route_handlers=[])).get("/", user=user)
    assert provide_user(request) is user
