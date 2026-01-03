from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.schemas.api_key import APIKeyCreate
from app.services.api_key_service import create_api_key

# Use NullPool to avoid connection issues in tests
# Use separate test database to avoid affecting development data
engine = create_async_engine(
    settings.test_database_url,
    echo=False,
    poolclass=NullPool,
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create tables, yield session, then drop tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Get test HTTP client with DB override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_api_key(db: AsyncSession) -> str:
    """Create a test API key and return the raw key."""
    api_key_data = APIKeyCreate(name="Test API Key", rate_limit_per_minute=100)
    _, raw_key = await create_api_key(db, api_key_data)
    return raw_key


@pytest.fixture
def api_key_headers(test_api_key: str) -> dict:
    """Get headers with API key for authenticated requests."""
    return {"X-API-Key": test_api_key}
