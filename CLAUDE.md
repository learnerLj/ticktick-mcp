# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development and Testing
- Install dependencies: `uv sync`
- Test server configuration: `uv run test_server.py`
- Set up authentication: `uv run ticktick-mcp auth`
- Run MCP server: `uv run ticktick-mcp run`
- Run with debug logging: `uv run ticktick-mcp run --debug`
- Format code: `uv run black .`
- Lint code: `uv run ruff check .`
- Type check: `uv run mypy ticktick_mcp/`
- Run tests: `uv run pytest`

### Global Installation Commands
- Install globally: `uv tool install ticktick-mcp`
- Set up authentication: `ticktick-mcp auth`
- Check status: `ticktick-mcp status`
- Run MCP server: `ticktick-mcp run`
- Run with debug logging: `ticktick-mcp run --debug`

### Authentication
The project requires TickTick OAuth2 authentication before use. If credentials are missing, the server will prompt for authentication setup.

## Architecture

This is a Model Context Protocol (MCP) server that provides TickTick task management integration for Claude and other MCP clients.

### Core Components

**MCP Server (`ticktick_mcp/src/server.py`)**
- FastMCP-based server with 8 tools for task/project management
- Handles initialization and API connectivity validation
- Formats TickTick objects for human-readable display

**TickTick API Client (`ticktick_mcp/src/ticktick_client.py`)**
- OAuth2 authentication with automatic token refresh
- Full CRUD operations for projects and tasks
- Error handling and API response validation

**CLI Interface (`ticktick_mcp/cli.py`)**
- `auth` command for OAuth2 setup flow
- `run` command for starting the MCP server
- Automatic authentication check before server startup

**Authentication Module (`ticktick_mcp/src/auth.py`)**
- OAuth2 flow implementation with local callback server
- Token exchange and storage in `.env` file
- Support for both TickTick and Dida365 (Chinese version)

### Environment Configuration
- `.env` file stores OAuth2 tokens and API endpoints
- Base URLs configurable for TickTick vs Dida365
- Client credentials required from developer portal

### MCP Tools Available

**Project Management (4 tools):**
- `get_projects` - List all projects
- `get_project` - Get specific project details
- `create_project` - Create new project
- `delete_project` - Delete project

**Task Management (6 tools):**
- `get_project_tasks` - Get tasks in specific project (legacy)
- `get_task` - Get specific task by project_id + task_id (legacy)
- `create_task` - Create new task
- `update_task` - Update existing task
- `complete_task` - Mark task as complete
- `delete_task` - Delete task

**Global Task Operations (2 tools):**
- `get_all_tasks` - Get all tasks across projects (with optional query, priority, project filters)
- `get_task_by_id` - Get task directly by ID (no project_id required)

**Batch Operations (2 tools):**
- `batch_complete_tasks` - Complete multiple tasks at once
- `batch_delete_tasks` - Delete multiple tasks at once

**Total: 14 MCP tools** (reduced from 31)

### Date Format
All date inputs use ISO format: `YYYY-MM-DDThh:mm:ss+0000`

### Priority Levels
- 0: None
- 1: Low
- 3: Medium  
- 5: High