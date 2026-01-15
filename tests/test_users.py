import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers):
    """Test getting the current user."""
    response = await client.get("/api/1.0/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "gid" in data
    assert "name" in data
    assert data["resource_type"] == "user"


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test getting current user without authentication."""
    response = await client.get("/api/1.0/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_by_gid(client: AsyncClient, auth_headers, test_user):
    """Test getting a user by GID."""
    response = await client.get(
        f"/api/1.0/users/{test_user.gid}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["gid"] == test_user.gid
    assert data["name"] == test_user.name


@pytest.mark.asyncio
async def test_get_nonexistent_user(client: AsyncClient, auth_headers):
    """Test getting a non-existent user."""
    response = await client.get(
        "/api/1.0/users/nonexistent123",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_users_in_workspace(client: AsyncClient, auth_headers, test_workspace):
    """Test getting users in a workspace."""
    response = await client.get(
        f"/api/1.0/users?workspace={test_workspace.gid}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) > 0

