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

This is a Model Context Protocol (MCP) server that provides TickTick/Dida365 task management integration for Claude and other MCP clients.

### Core Components

**MCP Server (`ticktick_mcp/server_oop.py`)**
- Object-oriented FastMCP-based server with 15 tools for comprehensive task/project management
- Handles initialization, API connectivity validation, and tool registration
- Formats TickTick objects for human-readable display
- Uses dependency injection pattern for services

**TickTick API Client (`ticktick_mcp/client.py`)**
- Modern object-oriented design with service layer architecture
- OAuth2 authentication with automatic token refresh
- Full CRUD operations for projects and tasks
- Robust error handling and API response validation
- Support for both TickTick and Dida365 APIs

**CLI Interface (`ticktick_mcp/cli.py`)**
- `auth` command for OAuth2 setup flow
- `run` command for starting the MCP server
- `status` command for checking authentication state
- Automatic authentication check before server startup

**Authentication Module (`ticktick_mcp/auth.py`)**
- OAuth2 flow implementation with local callback server
- Token exchange and storage in `.env` file
- Support for both TickTick and Dida365 (Chinese version)

**Configuration Management (`ticktick_mcp/config.py`)**
- Centralized configuration handling
- Environment variable management
- Token persistence and loading

**Models (`ticktick_mcp/models.py`)**
- Comprehensive data models for Task, Project, and related entities
- Type-safe enums for Priority, ViewMode, TaskStatus
- Serialization/deserialization methods

**Tools (`ticktick_mcp/tools.py`)**
- Object-oriented tool implementations with abstract base class
- Comprehensive error handling and validation
- Intelligent batch processing with retry logic

### Environment Configuration
- `.env` file stores OAuth2 tokens and API endpoints
- Base URLs configurable for TickTick vs Dida365
- Client credentials required from developer portal

### MCP Tools Available

**Project Management (5 tools):**
- `get_projects` - List all projects
- `get_project` - Get specific project details
- `create_project` - Create new project
- `update_project` - Update existing project properties
- `delete_project` - Delete project

**Task Management (6 tools):**
- `create_task` - Create new task with full property support
- `update_task` - Update existing task properties
- `get_all_tasks` - Get all tasks across projects with advanced filtering (status, priority, project, query)
- `get_task_by_id` - Get task directly by ID (no project_id required)
- `batch_complete_tasks` - Complete multiple tasks with intelligent error handling
- `batch_delete_tasks` - Delete multiple tasks (active tasks only)

**Advanced Operations (4 tools):**
- `batch_migrate_tasks` - Migrate tasks between projects using atomic create+delete approach
  - Handles API limitations with intelligent batching
  - Preserves all task data (content, priority, dates, subtasks)
  - Includes retry logic and error recovery
  - Works around Dida365 API constraints

**Total: 15 MCP tools**

### Task Migration Features
The `batch_migrate_tasks` tool implements a sophisticated migration system:
- **Atomic Operations**: Creates new task first, then deletes original only if creation succeeds
- **Data Preservation**: Maintains all task properties including subtasks, dates, and priority
- **Intelligent Batching**: Adjusts batch size based on success rates (1-3 tasks per batch)
- **API Limitation Handling**: Works around Dida365's inability to directly move tasks between projects
- **Retry Logic**: Exponential backoff for transient failures
- **Detailed Reporting**: Comprehensive success/failure reporting with specific error types

### Date Format
All date inputs use ISO format: `YYYY-MM-DDThh:mm:ss+0000`

### Priority Levels
- 0: None
- 1: Low
- 3: Medium  
- 5: High

### Testing and Debugging
- Multiple test scripts available for validating functionality
- Debug scripts for step-by-step migration testing
- Comprehensive logging with configurable levels
- Error simulation and recovery testing

### API Compatibility
- Primary support for Dida365 (Chinese TickTick) API
- Automatic handling of API response variations
- Fallback mechanisms for API limitations
- Rate limiting compliance with configurable delays