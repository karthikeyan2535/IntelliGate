"""
Pytest configuration and global fixtures for IntelliGate test suite.
Overrides database dependency with an asynchronous mock/in-memory session to run without external Postgres.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.database.base import get_db
from app.main import app


class MockAsyncResult:
    def __init__(self, item=None, items=None):
        self._item = item
        self._items = items or []

    def scalar_one_or_none(self):
        return self._item

    def scalars(self):
        m = MagicMock()
        m.all.return_value = self._items
        return m

    def first(self):
        return self._item


class MockAsyncSession:
    def __init__(self):
        self.add = MagicMock()
        self.commit = AsyncMock()
        self.refresh = AsyncMock()
        self.delete = AsyncMock()

    async def execute(self, statement, *args, **kwargs):
        return MockAsyncResult(item=None, items=[])

    async def close(self):
        pass


async def override_get_db():
    session = MockAsyncSession()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(autouse=True)
def apply_db_override():
    from app.providers.registry import provider_registry
    from tests.mocks import MockLLMProvider

    mock_p = MockLLMProvider()
    provider_registry.register("openai", mock_p)
    provider_registry.register("anthropic", mock_p)
    provider_registry.register("gemini", mock_p)

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
