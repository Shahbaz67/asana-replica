import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.core.security import get_password_hash, generate_gid
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership

# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with the test database session."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        gid=generate_gid(),
        name="Test User",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_workspace(db_session: AsyncSession, test_user: User) -> Workspace:
    """Create a test workspace."""
    workspace = Workspace(
        gid=generate_gid(),
        name="Test Workspace",
        is_organization=False,
    )
    db_session.add(workspace)
    await db_session.flush()
    
    # Add user as admin
    membership = WorkspaceMembership(
        gid=generate_gid(),
        user_gid=test_user.gid,
        workspace_gid=workspace.gid,
        is_admin=True,
        is_active=True,
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(workspace)
    return workspace


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test requests."""
    response = await client.post(
        "/api/1.0/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

