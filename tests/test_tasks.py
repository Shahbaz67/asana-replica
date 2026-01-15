import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers, test_workspace):
    """Test creating a task."""
    # First create a project
    project_response = await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={
            "data": {
                "name": "Task Test Project",
                "workspace": test_workspace.gid,
            }
        },
    )
    project_gid = project_response.json()["data"]["gid"]
    
    # Create task
    response = await client.post(
        "/api/1.0/tasks",
        headers=auth_headers,
        json={
            "data": {
                "name": "Test Task",
                "notes": "Test task notes",
                "projects": [project_gid],
            }
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Test Task"
    assert data["resource_type"] == "task"


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, auth_headers, test_workspace):
    """Test getting a task."""
    # Create project and task
    project_response = await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={"data": {"name": "Project", "workspace": test_workspace.gid}},
    )
    project_gid = project_response.json()["data"]["gid"]
    
    task_response = await client.post(
        "/api/1.0/tasks",
        headers=auth_headers,
        json={"data": {"name": "Task", "projects": [project_gid]}},
    )
    task_gid = task_response.json()["data"]["gid"]
    
    # Get task
    response = await client.get(
        f"/api/1.0/tasks/{task_gid}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["gid"] == task_gid


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_headers, test_workspace):
    """Test updating a task."""
    # Create project and task
    project_response = await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={"data": {"name": "Project", "workspace": test_workspace.gid}},
    )
    project_gid = project_response.json()["data"]["gid"]
    
    task_response = await client.post(
        "/api/1.0/tasks",
        headers=auth_headers,
        json={"data": {"name": "Original Task", "projects": [project_gid]}},
    )
    task_gid = task_response.json()["data"]["gid"]
    
    # Update task
    response = await client.put(
        f"/api/1.0/tasks/{task_gid}",
        headers=auth_headers,
        json={"data": {"name": "Updated Task", "completed": True}},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Updated Task"
    assert data["completed"] == True


@pytest.mark.asyncio
async def test_create_subtask(client: AsyncClient, auth_headers, test_workspace):
    """Test creating a subtask."""
    # Create project and parent task
    project_response = await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={"data": {"name": "Project", "workspace": test_workspace.gid}},
    )
    project_gid = project_response.json()["data"]["gid"]
    
    parent_response = await client.post(
        "/api/1.0/tasks",
        headers=auth_headers,
        json={"data": {"name": "Parent Task", "projects": [project_gid]}},
    )
    parent_gid = parent_response.json()["data"]["gid"]
    
    # Create subtask
    response = await client.post(
        f"/api/1.0/tasks/{parent_gid}/subtasks",
        headers=auth_headers,
        json={"data": {"name": "Subtask"}},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Subtask"
    assert data["parent"]["gid"] == parent_gid


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers, test_workspace):
    """Test deleting a task."""
    # Create project and task
    project_response = await client.post(
        "/api/1.0/projects",
        headers=auth_headers,
        json={"data": {"name": "Project", "workspace": test_workspace.gid}},
    )
    project_gid = project_response.json()["data"]["gid"]
    
    task_response = await client.post(
        "/api/1.0/tasks",
        headers=auth_headers,
        json={"data": {"name": "To Delete", "projects": [project_gid]}},
    )
    task_gid = task_response.json()["data"]["gid"]
    
    # Delete task
    response = await client.delete(
        f"/api/1.0/tasks/{task_gid}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    
    # Verify deletion
    get_response = await client.get(
        f"/api/1.0/tasks/{task_gid}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404

