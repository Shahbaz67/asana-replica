import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers, test_workspace):
    """Test creating a project."""
    response = await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={
            "data": {
                "name": "Test Project",
                "workspace": test_workspace.gid,
                "notes": "This is a test project",
            }
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Test Project"
    assert data["resource_type"] == "project"
    return data["gid"]


@pytest.mark.asyncio
async def test_get_projects(client: AsyncClient, auth_headers, test_workspace):
    """Test getting projects."""
    # First create a project
    await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={
            "data": {
                "name": "Test Project",
                "workspace": test_workspace.gid,
            }
        },
    )
    
    response = await client.get(
        f"/api/1.0/projects?workspace={test_workspace.gid}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, auth_headers, test_workspace):
    """Test updating a project."""
    # Create project
    create_response = await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={
            "data": {
                "name": "Original Name",
                "workspace": test_workspace.gid,
            }
        },
    )
    project_gid = create_response.json()["data"]["gid"]
    
    # Update project
    response = await client.put(
        f"/api/1.0/projects/{project_gid}",
        headers=auth_headers,
        json={"data": {"name": "Updated Name"}},
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, auth_headers, test_workspace):
    """Test deleting a project."""
    # Create project
    create_response = await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={
            "data": {
                "name": "To Delete",
                "workspace": test_workspace.gid,
            }
        },
    )
    project_gid = create_response.json()["data"]["gid"]
    
    # Delete project
    response = await client.delete(
        f"/api/1.0/projects/{project_gid}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    
    # Verify deletion
    get_response = await client.get(
        f"/api/1.0/projects/{project_gid}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


