# TickTick MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

**✨ Supports both TickTick (International) and Dida365 滴答清单 (China) with automatic configuration!**

## Features

- 📋 **Comprehensive Task Management**: View, create, update, and delete tasks across all projects
- 🎯 **Advanced Filtering**: Search tasks by status, priority, project, and content
- 🔄 **Intelligent Task Migration**: Move tasks between projects with full data preservation
- ✅ **Batch Operations**: Complete or delete multiple tasks simultaneously with smart error handling
- 📁 **Project Management**: Full CRUD operations for TickTick projects
- 🔍 **Global Task Access**: Get tasks by ID without needing project information
- 🚀 **Object-Oriented Architecture**: Modern, maintainable codebase with service layer design
- 🛡️ **Robust Error Handling**: Intelligent retry logic and graceful failure recovery
- 🔄 **Automatic Token Refresh**: Seamless OAuth2 authentication with background token management
- 🔌 **Native MCP Integration**: Purpose-built for Claude Desktop and other MCP clients

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- TickTick account with API access
- TickTick API credentials (Client ID, Client Secret, Access Token)

## Installation

### Option 1: Install from Package (Recommended)

1. **Install via uv (recommended)**:
   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install as a global tool
   uv tool install ticktick-mcp
   ```

2. **Or install via pip**:
   ```bash
   pip install ticktick-mcp
   ```

3. **Authenticate with TickTick**:
   ```bash
   # Run the authentication flow
   ticktick-mcp auth
   ```

   This will:
   - Ask for your TickTick Client ID and Client Secret
   - Open a browser window for you to log in to TickTick
   - Automatically save your access tokens to `~/.config/ticktick-mcp/.env`

4. **Check status**:
   ```bash
   ticktick-mcp status
   ```

### Option 2: Development Installation

For development, you have two approaches:

#### Approach A: Editable Global Install (Recommended for Development)

1. **Clone this repository**:
   ```bash
   git clone https://github.com/jacepark12/ticktick-mcp.git
   cd ticktick-mcp
   ```

2. **Install in editable mode as a global tool**:
   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies and the package in editable mode
   uv sync
   uv tool install --editable .
   ```

   Now you can use `ticktick-mcp` commands globally, and any code changes will be reflected immediately without reinstalling.

3. **Authenticate with TickTick**:
   ```bash
   ticktick-mcp auth
   ```

4. **Test your configuration**:
   ```bash
   uv run test_server.py
   ```

#### Approach B: Local Development with uv run

1. **Clone this repository**:
   ```bash
   git clone https://github.com/jacepark12/ticktick-mcp.git
   cd ticktick-mcp
   ```

2. **Install dependencies**:
   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync
   ```

3. **Use uv run for all commands**:
   ```bash
   # Authenticate with TickTick
   uv run ticktick-mcp auth

   # Check status
   uv run ticktick-mcp status

   # Run the server
   uv run ticktick-mcp run

   # Test configuration
   uv run test_server.py
   ```

#### Which Development Approach to Choose?

| Feature | Approach A (Editable Install) | Approach B (uv run) |
|---------|-------------------------------|----------------------|
| **Command Usage** | `ticktick-mcp auth` | `uv run ticktick-mcp auth` |
| **Global Access** | ✅ Available anywhere | ❌ Only in project directory |
| **Code Changes** | ✅ Instant reflection | ✅ Instant reflection |
| **Claude Desktop Config** | Simple: `"command": "ticktick-mcp"` | Complex: needs full uv path |
| **Isolation** | Less isolated (global tool) | ✅ Fully isolated to project |
| **Convenience** | ✅ Very convenient | Moderate (longer commands) |

**Recommendation**: Use **Approach A (Editable Install)** for active development as it provides the best developer experience while maintaining the ability to test code changes instantly.

## Authentication with TickTick

This server uses OAuth2 to authenticate with TickTick. The setup process is straightforward:

1. Register your application at the [TickTick Developer Center](https://developer.ticktick.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Run the authentication command:
   ```bash
   ticktick-mcp auth
   ```

3. Follow the prompts to enter your Client ID and Client Secret

4. A browser window will open for you to authorize the application with your TickTick account

5. After authorizing, you'll be redirected back to the application, and your access tokens will be automatically saved to `~/.config/ticktick-mcp/.env`

The server handles token refresh automatically, so you won't need to reauthenticate unless you revoke access or delete your configuration.

## Authentication with Dida365 (滴答清单)

[滴答清单 - Dida365](https://dida365.com/home) is the China version of TickTick. The setup is just as simple:

1. **Register your application** at the [Dida365 Developer Center](https://developer.dida365.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. **Run the authentication command**:
   ```bash
   ticktick-mcp auth
   ```
   
   When prompted, select option `2` for Dida365. The system will automatically configure all the necessary API endpoints for you.

**That's it!** No manual environment variable setup needed. The authentication tool will automatically detect you're using Dida365 and configure everything appropriately.

## Configuration with Claude Desktop

### Step 1: Install Claude Desktop
1. Download and install [Claude Desktop](https://claude.ai/download)
2. Complete the initial setup and sign in to your Claude account

### Step 2: Locate Configuration File
Find your Claude Desktop configuration file location:

**macOS**:
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows**:
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux**:
```bash
~/.config/Claude/claude_desktop_config.json
```

### Step 3: Configure MCP Server

Edit the configuration file with your preferred text editor:

**macOS**:
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows**:
```bash
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**Linux**:
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

### Step 4: Add TickTick MCP Server Configuration

Choose the appropriate configuration based on your installation method:

#### Option A: Global Installation (Recommended)
If you installed via `uv tool install ticktick-mcp` or `pip install ticktick-mcp`:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "ticktick-mcp",
      "args": ["run"],
      "env": {}
    }
  }
}
```

#### Option B: Development Setup with Editable Install
If you used `uv tool install --editable .`:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "ticktick-mcp",
      "args": ["run"],
      "env": {}
    }
  }
}
```

#### Option C: Local Development with uv run
If you're running directly from the cloned repository:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/ticktick-mcp", "ticktick-mcp", "run"],
      "env": {}
    }
  }
}
```

**Important**: Replace `/absolute/path/to/ticktick-mcp` with the actual full path to your cloned repository.

### Step 5: Advanced Configuration (Optional)

You can add additional configuration options:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "ticktick-mcp",
      "args": ["run", "--debug"],
      "env": {
        "TICKTICK_CONFIG_DIR": "/custom/config/path"
      }
    }
  }
}
```

Available options:
- `--debug`: Enable debug logging
- `TICKTICK_CONFIG_DIR`: Custom configuration directory (default: `~/.config/ticktick-mcp`)

### Step 6: Verify Configuration

1. **Save the configuration file**
2. **Restart Claude Desktop completely** (close and reopen the application)
3. **Check connection status**:
   - Look for the 🔨 (tools) icon in the Claude interface
   - Try asking: "What TickTick tools are available?"
   - You should see a list of available TickTick MCP tools

### Troubleshooting Configuration

If the MCP server doesn't appear in Claude Desktop:

1. **Check the JSON syntax** - Use a JSON validator to ensure your configuration is valid

2. **Fix "Command not found" error**:
   
   If you see `spawn ticktick-mcp ENOENT` in Claude Desktop logs, the command is not in Claude's PATH. Use the full path instead:
   
   ```bash
   # Find the full path
   which ticktick-mcp
   ```
   
   Then update your configuration to use the full path:
   ```json
   {
     "mcpServers": {
       "ticktick": {
         "command": "/Users/your-username/.local/bin/ticktick-mcp",
         "args": ["run"],
         "env": {}
       }
     }
   }
   ```

3. **Verify the command path**:
   ```bash
   # For global installation
   which ticktick-mcp
   
   # For development setup
   which uv
   ```

4. **Check authentication**:
   ```bash
   ticktick-mcp status
   ```

5. **Test the server manually**:
   ```bash
   ticktick-mcp run
   ```

6. **Check Claude Desktop logs**:
   
   **macOS**: `~/Library/Logs/Claude/mcp-server-ticktick.log`
   
   **Windows**: `%APPDATA%\Claude\logs\mcp-server-ticktick.log`
   
   **Linux**: `~/.local/share/Claude/logs/mcp-server-ticktick.log`

7. **Common PATH issues**:
   
   Claude Desktop runs with a limited PATH. If `ticktick-mcp` is installed in a non-standard location (like `~/.local/bin`), you may need to:
   - Use the full path in the configuration (recommended)
   - Or create a symlink in `/usr/local/bin`

### Multiple MCP Servers

You can configure multiple MCP servers alongside TickTick:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "ticktick-mcp",
      "args": ["run"]
    },
    "other-server": {
      "command": "other-mcp-server",
      "args": ["run"]
    }
  }
}
```

Once properly configured, you'll see the TickTick MCP server tools available in Claude, indicated by the 🔨 (tools) icon. You can now interact with your TickTick account using natural language!

## Available MCP Tools

The TickTick MCP server provides **15 comprehensive tools** for managing your tasks and projects:

### 📁 Project Management (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_projects` | List all your TickTick projects | None |
| `get_project` | Get details about a specific project | `project_id` |
| `create_project` | Create a new project | `name`, `color` (optional), `view_mode` (optional) |
| `update_project` | Update project properties | `project_id`, `name` (optional), `color` (optional), `view_mode` (optional), `kind` (optional) |
| `delete_project` | Delete a project | `project_id` |

### 📋 Core Task Management (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_all_tasks` | **Get all tasks across projects** with advanced filtering | `status`, `limit`, `query`, `priority`, `project_id` (all optional) |
| `get_task_by_id` | **Get task by ID directly** (no project needed) | `task_id` |
| `create_task` | **Create a new task** with full property support | `title`, `project_id`, `content`, `start_date`, `due_date`, `priority` (all optional except title) |
| `update_task` | **Update existing task** properties | `task_id`, `title`, `content`, `start_date`, `due_date`, `priority`, `project_id` (all optional except task_id) |
| `batch_complete_tasks` | **Complete multiple tasks** with error handling | `task_ids` (comma-separated) |
| `batch_delete_tasks` | **Delete multiple tasks** (active tasks only) | `task_ids` (comma-separated) |

### 🚀 Advanced Operations (4 tools)

| Tool | Description | Key Features |
|------|-------------|--------------|
| `batch_migrate_tasks` | **Migrate tasks between projects** | • Atomic create+delete operations<br/>• Full data preservation<br/>• Intelligent batching (1-3 tasks)<br/>• Retry logic with exponential backoff<br/>• API limitation workarounds |

### 🔄 Legacy Compatibility (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_project_tasks` | List tasks in specific project (legacy) | `project_id` |
| `get_task` | Get task details (legacy method) | `project_id`, `task_id` |

## 🎯 Tool Highlights

### **Task Migration System**
The `batch_migrate_tasks` tool is particularly sophisticated:

- **Atomic Operations**: Creates new task first, deletes original only if creation succeeds
- **Complete Data Preservation**: Maintains all properties (content, priority, dates, subtasks, tags)
- **API Limitation Handling**: Works around Dida365's inability to directly move tasks between projects
- **Intelligent Batching**: Adjusts batch size (1-3 tasks) based on success rates
- **Advanced Error Recovery**: Exponential backoff, specific error type handling
- **Detailed Reporting**: Comprehensive success/failure feedback with specific error messages

### **Advanced Filtering**
The `get_all_tasks` tool supports comprehensive filtering:

- **Status**: `active`, `completed`, or all tasks
- **Priority**: Filter by priority level (0-5)
- **Project**: Specific project or special collections (e.g., `inbox`)
- **Search Query**: Text search in task titles and content
- **Limit**: Control number of results returned

### **Batch Operations**
Both `batch_complete_tasks` and `batch_delete_tasks` include:

- **Rate Limiting**: 1.0s delays between API calls
- **Error Tolerance**: Continues processing even if individual tasks fail
- **Detailed Logging**: Progress tracking for multiple-task operations
- **Smart Skipping**: Automatically handles completed tasks that can't be deleted

### Parameter Details

- **Priority levels**: `0` (None), `1` (Low), `3` (Medium), `5` (High)
- **Date format**: ISO format `YYYY-MM-DDThh:mm:ss+0000`
- **Status options**: `active`, `completed`, or leave empty for all
- **View modes**: `list`, `kanban`, `timeline`
- **Colors**: Hex color codes (e.g., `#FF0000` for red)
- **Limit**: Optional number to limit results (no limit by default - returns all tasks)

## Example Prompts for Claude

Here are some example prompts to use with Claude after connecting the TickTick MCP server:

### Basic Operations
- "Show me all my TickTick projects"
- "List all my active tasks"
- "What tasks do I have today?"
- "Show me all completed tasks"

### Project Management
- "Create a new project called 'Vacation Planning' with a blue color"
- "Delete the project 'Old Project'"
- "Show me details about my work project"

### Task Creation
- "Create a new task called 'Finish MCP server documentation' in my work project with high priority"
- "Add a task 'Buy groceries' with due date tomorrow at 6 PM"
- "Create a high-priority task 'Prepare presentation' with content 'Include Q3 results and future roadmap'"

### Task Management
- "Update the task 'Meeting prep' to have medium priority and due date next Friday"
- "Mark the task 'Buy groceries' as complete"
- "Delete the task 'Old reminder'"
- "Complete all tasks related to 'project launch'"

### Search and Filtering
- "Show me all high-priority tasks"
- "Find tasks containing 'meeting'"
- "List all tasks in my personal project"
- "What are my overdue tasks?"
- "Show me tasks from my inbox"
- "Get all active tasks with medium priority"

### Advanced Operations
- "Move these 3 tasks from my personal project to work project"
- "Migrate all tasks containing 'meeting' to my calendar project"
- "Transfer the high-priority tasks from old project to new project"

### Batch Operations
- "Complete tasks with IDs: task1, task2, task3"
- "Delete multiple completed tasks"
- "Mark all grocery-related tasks as complete"

### Analysis and Planning
- "When is my next deadline in TickTick?"
- "What's my workload like this week?"
- "Show me tasks I haven't completed yet"
- "Help me prioritize my tasks for today"

### Natural Language Queries
- "What do I need to do before the weekend?"
- "Create a daily standup checklist in my work project"
- "Set up my grocery shopping list as tasks"
- "Help me organize my tasks by priority"

The MCP server understands natural language, so feel free to ask in your own style!

## Development

### Project Structure

```
ticktick-mcp/
├── README.md                    # Project documentation  
├── CLAUDE.md                    # Claude Code guidance
├── pyproject.toml              # Modern Python project configuration
├── uv.lock                     # Dependency lock file
├── test_server.py              # Server configuration test
└── ticktick_mcp/               # Main package
    ├── __init__.py             # Package initialization
    ├── cli.py                  # Command-line interface
    ├── server_oop.py           # Object-oriented MCP server
    ├── client.py               # Modern API client with services
    ├── auth.py                 # OAuth2 authentication
    ├── config.py               # Configuration management
    ├── models.py               # Data models and enums
    ├── tools.py                # MCP tool implementations
    ├── exceptions.py           # Custom exception classes
    └── logging_config.py       # Logging configuration
```

### Authentication Flow

The project implements a complete OAuth 2.0 flow for TickTick:

1. **Initial Setup**: User provides their TickTick API Client ID and Secret
2. **Browser Authorization**: User is redirected to TickTick to grant access
3. **Token Reception**: A local server receives the OAuth callback with the authorization code
4. **Token Exchange**: The code is exchanged for access and refresh tokens
5. **Token Storage**: Tokens are securely stored in the local `.env` file
6. **Token Refresh**: The client automatically refreshes the access token when it expires

This simplifies the user experience by handling the entire OAuth flow programmatically.

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
