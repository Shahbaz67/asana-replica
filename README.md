# Asana Backend Replica

A complete backend service replicating Asana's REST API, built with Python FastAPI and PostgreSQL.

## Features

This implementation covers the full Asana API including:

### Core Resources
- **Users** - User management
- **Workspaces** - Workspace creation and management
- **Teams** - Team management within organizations
- **Projects** - Full CRUD with duplication, memberships, statuses
- **Sections** - Project sections for task organization
- **Tasks** - Complete task management with subtasks, dependencies, search
- **Stories** - Comments and activity feed
- **Attachments** - File upload support
- **Tags** - Task labeling

### Advanced Features
- **Custom Fields** - Custom field definitions with enum options
- **Portfolios** - Portfolio management with project grouping
- **Goals** - Goal tracking with metrics and relationships
- **Webhooks** - Real-time event notifications
- **Events API** - Polling-based change detection
- **Batch API** - Multiple requests in one call

### Enterprise Features
- **Audit Logs** - Activity tracking
- **Organization Exports** - Data export functionality
- **Time Periods** - Goal time period management
- **Time Tracking** - Task time entries

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Containerization**: Docker + Docker Compose

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/Shahbaz67/asana-replica.git
cd asana-replica
```

2. Start the services:
```bash
docker-compose up --build
```

3. The API will be available at:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL and create a `.env` file:

   **Option A: Using Docker (Easiest)**
   
   Start PostgreSQL using Docker Compose (only the database service):
   ```bash
   docker-compose up db -d
   ```
   
   This will start PostgreSQL with:
   - User: `asana`
   - Password: `asana`
   - Database: `asana`
   - Port: `5432`
   
   **Option B: Install PostgreSQL Locally**
   
   - **macOS**: `brew install postgresql@15` then `brew services start postgresql@15`
   
   Create the database and user:
   ```bash
   # Connect to PostgreSQL
   psql postgres
   
   # Create database and user
   CREATE DATABASE asana;
   CREATE USER asana WITH PASSWORD 'asana';
   GRANT ALL PRIVILEGES ON DATABASE asana TO asana;
   \q
   ```
   
   **Create `.env` file:**
   
   Create a `.env` file in the project root with the following content:
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql+asyncpg://asana:asana@localhost:5432/asana
   
   # Application
   DEBUG=true
   ```
   
   **Note**: If you used different credentials, update `DATABASE_URL` accordingly:
   ```
   DATABASE_URL=postgresql+asyncpg://your_user:your_password@localhost:5432/your_database
   ```
   
4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

### Example API Calls

Create a project:
```bash
curl -X POST http://localhost:8000/api/1.0/projects \
  -H "Content-Type: application/json" \
  -d '{"data": {"name": "My Project", "workspace": "<workspace_gid>"}}'
```

Create a task:
```bash
curl -X POST http://localhost:8000/api/1.0/tasks \
  -H "Content-Type: application/json" \
  -d '{"data": {"name": "My Task", "projects": ["<project_gid>"]}}'
```

Search tasks:
```bash
curl "http://localhost:8000/api/1.0/tasks/search?workspace=<workspace_gid>&text=search_term"
```

### Response Format

All responses follow the Asana API format:

```json
{
  "data": {
    "gid": "12345",
    "resource_type": "task",
    "name": "My Task",
    ...
  }
}
```

List responses include pagination:
```json
{
  "data": [...],
  "next_page": {
    "offset": "20",
    "path": "/tasks?offset=20",
    "uri": "/tasks?offset=20"
  }
}
```

### Error Responses

```json
{
  "errors": [
    {
      "message": "Error message",
      "help": "Help text",
      "phrase": "error_code"
    }
  ]
}
```

## API Endpoints

### Users
- `GET /users` - List users
- `GET /users/me` - Get current user
- `GET /users/{gid}` - Get user by GID
- `GET /users/{gid}/favorites` - Get user favorites
- `GET /users/{gid}/user_task_list` - Get user's task list

### Workspaces
- `GET /workspaces` - List workspaces
- `GET /workspaces/{gid}` - Get workspace
- `PUT /workspaces/{gid}` - Update workspace
- `POST /workspaces/{gid}/addUser` - Add user to workspace
- `POST /workspaces/{gid}/removeUser` - Remove user from workspace

### Projects
- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/{gid}` - Get project
- `PUT /projects/{gid}` - Update project
- `DELETE /projects/{gid}` - Delete project
- `POST /projects/{gid}/duplicate` - Duplicate project
- `GET /projects/{gid}/tasks` - Get project tasks
- `GET /projects/{gid}/sections` - Get project sections

### Tasks
- `GET /tasks` - List tasks
- `POST /tasks` - Create task
- `GET /tasks/{gid}` - Get task
- `PUT /tasks/{gid}` - Update task
- `DELETE /tasks/{gid}` - Delete task
- `POST /tasks/{gid}/duplicate` - Duplicate task
- `GET /tasks/{gid}/subtasks` - Get subtasks
- `POST /tasks/{gid}/subtasks` - Create subtask
- `POST /tasks/{gid}/setParent` - Set parent task
- `GET /tasks/{gid}/dependencies` - Get dependencies
- `POST /tasks/{gid}/addDependencies` - Add dependencies
- `POST /tasks/{gid}/addProject` - Add to project
- `POST /tasks/{gid}/addTag` - Add tag
- `GET /tasks/search` - Search tasks

### And many more...

See the full API documentation at `/docs` when running the server.

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx aiosqlite

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

## Project Structure

```
scaler-assignment/
├── app/
│   ├── api/
│   │   ├── v1/              # API endpoints
│   │   └── deps.py          # Dependencies
│   ├── core/
│   │   ├── security.py      # Security utilities (GID generation, webhook secrets)
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── events.py        # Event system
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── utils/               # Utilities
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   └── main.py              # Application entry
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the project root with the following variables:

#### Required Variables

- **`DATABASE_URL`** - PostgreSQL connection string
  - Format: `postgresql+asyncpg://user:password@host:port/database`
  - Example: `postgresql+asyncpg://asana:asana@localhost:5432/asana`

#### Optional Variables (with defaults)

- **`DEBUG`** - Enable debug mode (default: `false`)
  - Set to `true` for development (shows detailed error messages)
  - **⚠️ Never set to `true` in production**

## License

MIT License

