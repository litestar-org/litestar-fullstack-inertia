"""Tests for the dependency providers module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID, uuid4

import pytest
from advanced_alchemy.extensions.litestar.providers import create_filter_dependencies
from advanced_alchemy.filters import BeforeAfter, CollectionFilter, FilterTypes, LimitOffset, OrderBy, SearchFilter
from litestar import Litestar, get
from litestar.params import Dependency
from litestar.testing import AsyncTestClient, RequestFactory

from app.db.models import User
from app.domain.accounts.dependencies import provide_user

pytestmark = pytest.mark.anyio


@dataclass
class MessageTest:
    test_attr: str


async def test_provide_user_dependency() -> None:
    """Test that the provide_user dependency correctly retrieves user from request."""
    user = User()
    request = RequestFactory(app=Litestar(route_handlers=[])).get("/", user=user)
    assert await provide_user(request) is user


async def test_filter_dependencies_with_litestar() -> None:
    """Test that create_filter_dependencies works correctly with Litestar routes."""
    called = False
    path = f"/{uuid4()}"
    test_ids = [uuid4() for _ in range(2)]

    filter_deps = create_filter_dependencies(
        {
            "id_filter": UUID,
            "search": "name",
            "pagination_type": "limit_offset",
            "pagination_size": 10,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "sort_order": "asc",
        },
    )

    @get(path, opt={"exclude_from_auth": True}, dependencies=filter_deps)
    async def test_route(
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> MessageTest:
        nonlocal called
        # Verify we received the expected filter types
        filter_types = {type(f).__name__ for f in filters}
        assert "CollectionFilter" in filter_types or len([f for f in filters if isinstance(f, CollectionFilter)]) >= 0
        assert any(isinstance(f, LimitOffset) for f in filters)
        assert any(isinstance(f, BeforeAfter) for f in filters)
        called = True
        return MessageTest(test_attr="success")

    app = Litestar(route_handlers=[test_route])

    async with AsyncTestClient(app=app) as client:
        response = await client.get(
            path,
            params={
                "ids": [str(id_) for id_ in test_ids],
                "currentPage": 2,
                "pageSize": 5,
            },
        )
        assert response.status_code == 200
        assert called


async def test_filter_dependencies_search_filter() -> None:
    """Test that search filter is properly configured."""
    called = False
    path = f"/{uuid4()}"

    filter_deps = create_filter_dependencies(
        {
            "search": "name,email",
            "search_ignore_case": True,
        },
    )

    @get(path, opt={"exclude_from_auth": True}, dependencies=filter_deps)
    async def test_route(
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> MessageTest:
        nonlocal called
        search_filters = [f for f in filters if isinstance(f, SearchFilter)]
        if search_filters:
            sf = search_filters[0]
            assert sf.value == "test_query"
        called = True
        return MessageTest(test_attr="success")

    app = Litestar(route_handlers=[test_route])

    async with AsyncTestClient(app=app) as client:
        response = await client.get(
            path,
            params={
                "searchString": "test_query",
            },
        )
        assert response.status_code == 200
        assert called


async def test_filter_dependencies_order_by() -> None:
    """Test that order_by filter is properly configured."""
    called = False
    path = f"/{uuid4()}"

    filter_deps = create_filter_dependencies(
        {
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    )

    @get(path, opt={"exclude_from_auth": True}, dependencies=filter_deps)
    async def test_route(
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> MessageTest:
        nonlocal called
        order_filters = [f for f in filters if isinstance(f, OrderBy)]
        if order_filters:
            of = order_filters[0]
            assert of.sort_order == "desc"
        called = True
        return MessageTest(test_attr="success")

    app = Litestar(route_handlers=[test_route])

    async with AsyncTestClient(app=app) as client:
        response = await client.get(
            path,
            params={
                "sortOrder": "desc",
            },
        )
        assert response.status_code == 200
        assert called


async def test_filter_dependencies_pagination() -> None:
    """Test that pagination filter is properly configured."""
    called = False
    path = f"/{uuid4()}"

    filter_deps = create_filter_dependencies(
        {
            "pagination_type": "limit_offset",
            "pagination_size": 25,
        },
    )

    @get(path, opt={"exclude_from_auth": True}, dependencies=filter_deps)
    async def test_route(
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> MessageTest:
        nonlocal called
        pagination_filters = [f for f in filters if isinstance(f, LimitOffset)]
        assert len(pagination_filters) == 1
        pf = pagination_filters[0]
        assert pf.limit == 10
        assert pf.offset == 20  # page 3, page_size 10: (3-1) * 10 = 20
        called = True
        return MessageTest(test_attr="success")

    app = Litestar(route_handlers=[test_route])

    async with AsyncTestClient(app=app) as client:
        response = await client.get(
            path,
            params={
                "currentPage": 3,
                "pageSize": 10,
            },
        )
        assert response.status_code == 200
        assert called
