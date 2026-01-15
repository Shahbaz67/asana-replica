import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_workspaces(client: AsyncClient, auth_headers, test_workspace):
    """Test getting workspaces."""
    response = await client.get("/api/1.0/workspaces", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_get_workspace_by_gid(client: AsyncClient, auth_headers, test_workspace):
    """Test getting a workspace by GID."""
    response = await client.get(
        f"/api/1.0/workspaces/{test_workspace.gid}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["gid"] == test_workspace.gid
    assert data["name"] == test_workspace.name


@pytest.mark.asyncio
async def test_update_workspace(client: AsyncClient, auth_headers, test_workspace):
    """Test updating a workspace."""
    new_name = "Updated Workspace Name"
    response = await client.put(
        f"/api/1.0/workspaces/{test_workspace.gid}",
        headers=auth_headers,
        json={"data": {"name": new_name}},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == new_name


@pytest.mark.asyncio
async def test_get_workspace_users(client: AsyncClient, auth_headers, test_workspace):
    """Test getting users in a workspace."""
    response = await client.get(
        f"/api/1.0/workspaces/{test_workspace.gid}/users",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) > 0

