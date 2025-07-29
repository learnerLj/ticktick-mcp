# TickTick MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

**✨ Supports both TickTick (International) and Dida365 滴答清单 (China) with automatic configuration!**

**⚠️ Note: TickTick/Dida365 official APIs have reliability issues and may return HTTP 500 errors frequently. This MCP server includes robust error handling and retry logic to work around these limitations.**

## Features

- **Task Management**: Create, update, complete, and delete tasks across all projects
- **Advanced Search**: Filter tasks by status, priority, project, and content
- **Task Migration**: Move tasks between projects with full data preservation
- **Batch Operations**: Complete or delete multiple tasks at once
- **Project Management**: Create, update, and manage TickTick projects

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- TickTick account with API access
- TickTick API credentials (Client ID, Client Secret, Access Token)

## Installation & Setup

1. **Clone this repository**:
   ```bash
   git clone https://github.com/jacepark12/ticktick-mcp.git
   cd ticktick-mcp
   ```

2. **Install as global tool**:
   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install as global tool from local source
   uv tool install --editable .
   ```

3. **Register your application** at [TickTick Developer Center](https://developer.ticktick.com/) or [Dida365 Developer Center](https://developer.dida365.com/)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

4. **Authenticate**:
   ```bash
   ticktick-mcp auth
   ```
   Follow the prompts and authorize in your browser.

5. **Verify setup**:
   ```bash
   ticktick-mcp status
   ```

## Configuration with Claude Desktop

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "/absolute/path/to/ticktick-mcp",
      "args": ["run"],
      "env": {}
    }
  }
}
```

Use `which ticktick-mcp` to find the absolute path.

## Available MCP Tools

The TickTick MCP server provides **15 comprehensive tools** for managing your tasks and projects:

### Project Management (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_projects` | List all your TickTick projects | None |
| `get_project` | Get details about a specific project | `project_id` |
| `create_project` | Create a new project | `name`, `color` (optional), `view_mode` (optional) |
| `update_project` | Update project properties | `project_id`, `name` (optional), `color` (optional), `view_mode` (optional), `kind` (optional) |
| `delete_project` | Delete a project | `project_id` |

### Core Task Management (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_all_tasks` | Get all tasks across projects with advanced filtering | `status`, `limit`, `query`, `priority`, `project_id` (all optional) |
| `get_task_by_id` | Get task by ID directly (no project needed) | `task_id` |
| `create_task` | Create a new task with full property support | `title`, `project_id`, `content`, `start_date`, `due_date`, `priority` (all optional except title) |
| `update_task` | Update existing task properties | `task_id`, `title`, `content`, `start_date`, `due_date`, `priority`, `project_id` (all optional except task_id) |
| `batch_complete_tasks` | Complete multiple tasks with error handling | `task_ids` (comma-separated) |
| `batch_delete_tasks` | Delete multiple tasks (active tasks only) | `task_ids` (comma-separated) |

### Advanced Operations (4 tools)

| Tool | Description | Key Features |
|------|-------------|--------------|
| `batch_migrate_tasks` | Migrate tasks between projects | • Atomic create+delete operations<br/>• Full data preservation<br/>• Intelligent batching (1-3 tasks)<br/>• Retry logic with exponential backoff<br/>• API limitation workarounds |

### Legacy Compatibility (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_project_tasks` | List tasks in specific project (legacy) | `project_id` |
| `get_task` | Get task details (legacy method) | `project_id`, `task_id` |


