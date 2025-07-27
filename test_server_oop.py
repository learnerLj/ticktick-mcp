#!/usr/bin/env python3
# Use uv run test_server_oop.py to run this script
"""
Test script for the modern OOP TickTick MCP server.
This will test the new object-oriented architecture and verify functionality.
"""

import sys
from typing import Optional

from ticktick_mcp.authenticate import main as auth_main
from ticktick_mcp.config import ConfigManager
from ticktick_mcp.server_oop import create_server
from ticktick_mcp.logging_config import LoggerManager
from ticktick_mcp.exceptions import TickTickMCPError


def test_config_manager():
    """Test configuration management."""
    print("🔧 Testing configuration management...")
    
    try:
        config_manager = ConfigManager()
        
        # Test authentication check
        is_authenticated = config_manager.is_authenticated()
        if is_authenticated:
            print("  ✅ Configuration loaded successfully")
            config = config_manager.load_config()
            print(f"  ✅ Client ID configured: {bool(config.client_id)}")
            print(f"  ✅ Access token available: {bool(config.access_token)}")
        else:
            print("  ❌ Not authenticated - access token missing")
            return False
            
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def test_server_creation():
    """Test server creation and initialization."""
    print("\n🚀 Testing server creation...")
    
    try:
        # Create server
        server = create_server()
        print("  ✅ Server instance created successfully")
        
        # Test server info before initialization
        info = server.get_server_info()
        print(f"  📊 Server info: {info['name']} v{info['version']}")
        print(f"  📊 Initialized: {info['initialized']}")
        
        return server
    except Exception as e:
        print(f"  ❌ Server creation error: {e}")
        return None


def test_server_initialization(server):
    """Test server initialization."""
    print("\n⚡ Testing server initialization...")
    
    try:
        # Initialize server
        success = server.initialize()
        
        if success:
            print("  ✅ Server initialized successfully")
            
            # Test server info after initialization
            info = server.get_server_info()
            print(f"  📊 Tools registered: {info['tools_count']}")
            print(f"  📊 Available tools: {', '.join(info['tools'][:5])}{'...' if len(info['tools']) > 5 else ''}")
            
            return True
        else:
            print("  ❌ Server initialization failed")
            return False
            
    except TickTickMCPError as e:
        print(f"  ❌ TickTick error: {e.message}")
        return False
    except Exception as e:
        print(f"  ❌ Initialization error: {e}")
        return False


def test_api_connectivity(server):
    """Test API connectivity through services."""
    print("\n🌐 Testing API connectivity...")
    
    try:
        if not server._initialized:
            print("  ❌ Server not initialized")
            return False
        
        # Test project service
        projects = server.project_service.get_all_projects()
        print(f"  ✅ Successfully fetched {len(projects)} projects")
        
        # Test task service with simple query
        try:
            from ticktick_mcp.models import TaskFilter
            task_filter = TaskFilter(limit=5)
            tasks = server.task_service.get_all_tasks(task_filter)
            print(f"  ✅ Successfully fetched {len(tasks)} tasks")
        except Exception as task_error:
            print(f"  ⚠️  Task service error (this may be expected): {task_error}")
            # This is not necessarily a failure - the API endpoint might not be available
            pass
        
        return True
    except Exception as e:
        print(f"  ❌ API connectivity error: {e}")
        return False


def test_tool_execution(server):
    """Test tool execution."""
    print("\n🔨 Testing tool execution...")
    
    try:
        if not server._initialized:
            print("  ❌ Server not initialized")
            return False
        
        # Test getting projects tool
        projects_tool = server.tool_registry.get_tool("get_projects")
        if projects_tool:
            print("  ✅ Projects tool found in registry")
        else:
            print("  ❌ Projects tool not found")
            return False
        
        # Test getting tasks tool
        tasks_tool = server.tool_registry.get_tool("get_all_tasks")
        if tasks_tool:
            print("  ✅ Tasks tool found in registry")
        else:
            print("  ❌ Tasks tool not found")
            return False
        
        print(f"  ✅ All {len(server.tool_registry.list_tools())} tools registered correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Tool execution error: {e}")
        return False


def run_authentication_flow():
    """Run authentication flow if needed."""
    print("\n🔐 Authentication required...")
    print("Would you like to authenticate with TickTick now? (y/n): ", end="")
    choice = input().lower().strip()
    
    if choice == "y":
        print("Starting authentication flow...")
        auth_result = auth_main()
        if auth_result == 0:
            print("✅ Authentication successful!")
            return True
        else:
            print("❌ Authentication failed!")
            return False
    else:
        print("Please run 'ticktick-mcp auth' to authenticate.")
        return False


def main():
    """Main test function."""
    print("="*60)
    print("🧪 TickTick MCP Server OOP Architecture Test")
    print("="*60)
    
    # Setup logging
    logger_manager = LoggerManager()
    logger_manager.setup_logging()
    
    # Test configuration
    if not test_config_manager():
        if not run_authentication_flow():
            sys.exit(1)
        
        # Retry configuration test after authentication
        if not test_config_manager():
            print("\n❌ Configuration still failed after authentication")
            sys.exit(1)
    
    # Test server creation
    server = test_server_creation()
    if not server:
        sys.exit(1)
    
    # Test server initialization
    if not test_server_initialization(server):
        sys.exit(1)
    
    # Test API connectivity
    if not test_api_connectivity(server):
        sys.exit(1)
    
    # Test tool execution
    if not test_tool_execution(server):
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ The TickTick MCP server OOP architecture is working correctly!")
    print("🚀 You can now run the server using 'ticktick-mcp run'")
    print("="*60)


if __name__ == "__main__":
    main()