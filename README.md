# TickTick MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

**✨ Supports both TickTick (International) and Dida365 滴答清单 (China) with automatic configuration!**

## Features

- 📋 View all your TickTick projects and tasks
- ✏️ Create new projects and tasks through natural language
- 🔄 Update existing task details (title, content, dates, priority)
- ✅ Mark tasks as complete
- 🗑️ Delete tasks and projects
- 🔄 Full integration with TickTick's open API
- 🔌 Seamless integration with Claude and other MCP clients

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

## Usage with Claude for Desktop

1. Install [Claude for Desktop](https://claude.ai/download)
2. Edit your Claude for Desktop configuration file:

   **macOS**:
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   **Windows**:
   ```bash
   notepad %APPDATA%\Claude\claude_desktop_config.json
   ```

3. Add the TickTick MCP server configuration:

   **If installed globally:**
   ```json
   {
      "mcpServers": {
         "ticktick": {
            "command": "ticktick-mcp",
            "args": ["run"]
         }
      }
   }
   ```

   **If using development setup:**
   ```json
   {
      "mcpServers": {
         "ticktick": {
            "command": "uv",
            "args": ["run", "--directory", "/absolute/path/to/ticktick-mcp", "ticktick-mcp", "run"]
         }
      }
   }
   ```

4. Restart Claude for Desktop

Once connected, you'll see the TickTick MCP server tools available in Claude, indicated by the 🔨 (tools) icon.

## Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_projects` | List all your TickTick projects | None |
| `get_project` | Get details about a specific project | `project_id` |
| `get_project_tasks` | List all tasks in a project | `project_id` |
| `get_task` | Get details about a specific task | `project_id`, `task_id` |
| `create_task` | Create a new task | `title`, `project_id`, `content` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional) |
| `update_task` | Update an existing task | `task_id`, `project_id`, `title` (optional), `content` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional) |
| `complete_task` | Mark a task as complete | `project_id`, `task_id` |
| `delete_task` | Delete a task | `project_id`, `task_id` |
| `create_project` | Create a new project | `name`, `color` (optional), `view_mode` (optional) |
| `delete_project` | Delete a project | `project_id` |

## Example Prompts for Claude

Here are some example prompts to use with Claude after connecting the TickTick MCP server:

- "Show me all my TickTick projects"
- "Create a new task called 'Finish MCP server documentation' in my work project with high priority"
- "List all tasks in my personal project"
- "Mark the task 'Buy groceries' as complete"
- "Create a new project called 'Vacation Planning' with a blue color"
- "When is my next deadline in TickTick?"

## Development

### Project Structure

```
ticktick-mcp/
├── .env.template          # Template for environment variables
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── setup.py               # Package setup file
├── test_server.py         # Test script for server configuration
└── ticktick_mcp/          # Main package
    ├── __init__.py        # Package initialization
    ├── authenticate.py    # OAuth authentication utility
    ├── cli.py             # Command-line interface
    └── src/               # Source code
        ├── __init__.py    # Module initialization
        ├── auth.py        # OAuth authentication implementation
        ├── server.py      # MCP server implementation
        └── ticktick_client.py  # TickTick API client
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
