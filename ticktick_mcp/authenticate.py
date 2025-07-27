#!/usr/bin/env python3
"""
TickTick OAuth authentication command-line utility.

This script guides users through the process of authenticating with TickTick
and obtaining the necessary access tokens for the TickTick MCP server.
"""

import logging
import sys
from dataclasses import dataclass
from typing import Optional

import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import print

from .config import ConfigManager
from .src.auth import TickTickAuth


@dataclass
class TestResult:
    """Result of credential testing."""
    success: bool
    error: Optional[str] = None


def test_existing_credentials(config_manager: ConfigManager) -> TestResult:
    """Test existing credentials by making a simple API call."""
    try:
        config = config_manager.load_config()
        
        if not config.access_token:
            return TestResult(success=False, error="No access token found")
        
        # Test with a simple API call (get user info or projects)
        headers = {
            "Authorization": f"Bearer {config.access_token}",
            "Content-Type": "application/json"
        }
        
        # Try to get user projects - this is a lightweight test
        response = requests.get(
            f"{config.base_url}/project",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return TestResult(success=True)
        elif response.status_code == 401:
            return TestResult(success=False, error="Access token expired or invalid")
        elif response.status_code == 403:
            return TestResult(success=False, error="Access denied - check permissions")
        else:
            return TestResult(success=False, error=f"API error: {response.status_code}")
            
    except requests.exceptions.Timeout:
        return TestResult(success=False, error="Connection timeout")
    except requests.exceptions.ConnectionError:
        return TestResult(success=False, error="Network connection failed")
    except Exception as e:
        return TestResult(success=False, error=f"Unexpected error: {str(e)}")


def main() -> int:
    """Run the authentication flow."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    console = Console()
    
    # Create a beautiful banner with Rich
    title_text = Text("TickTick / Dida365 MCP Server Authentication", style="bold cyan")
    
    # Create services table
    services_table = Table(show_header=False, box=None, padding=(0, 1))
    services_table.add_row("🌍", "[bold blue]TickTick[/bold blue] (International)", "[dim]https://developer.ticktick.com[/dim]")
    services_table.add_row("🇨🇳", "[bold red]Dida365[/bold red] (滴答清单 - China)", "[dim]https://developer.dida365.com[/dim]")
    
    # Create requirements table
    req_table = Table(show_header=False, box=None, padding=(0, 1))
    req_table.add_row("1.", "An account with your chosen service")
    req_table.add_row("2.", "A registered API application at the developer center")
    req_table.add_row("3.", "Your Client ID and Client Secret")
    
    # Create the main panel content
    content = Text()
    content.append("This utility will help you authenticate with TickTick or Dida365.\n\n")
    content.append("Supported services:\n", style="bold")
    
    # Display the banner
    console.print(Panel.fit(
        title_text,
        style="bright_blue",
        padding=(1, 2)
    ))
    
    console.print("\n[dim]This utility will help you authenticate with TickTick or Dida365.[/dim]\n")
    
    console.print(Panel(
        services_table,
        title="[bold]🌐 Supported Services[/bold]",
        border_style="blue"
    ))
    
    console.print(Panel(
        req_table,
        title="[bold]📋 Before you begin, you will need[/bold]",
        border_style="green"
    ))
    
    console.print("\n[dim]💡 Advanced users: You can also set [bold]USE_DIDA365=true[/bold] environment variable to automatically configure Dida365 endpoints.[/dim]\n")

    config_manager = ConfigManager()
    
    # First, let user choose the service
    console.print("\n[bold]Which service would you like to use?[/bold]")
    
    # Create choice table
    choice_table = Table(show_header=False, box=None, padding=(0, 1))
    choice_table.add_row("[bold blue]1.[/bold blue]", "🌍 [bold blue]TickTick[/bold blue] (International)")
    choice_table.add_row("[bold red]2.[/bold red]", "🇨🇳 [bold red]Dida365[/bold red] (滴答清单 - China)")
    console.print(choice_table)
    
    service_choice = Prompt.ask("\nEnter choice", choices=["1", "2"], default="1")
    
    if service_choice == "2":
        desired_service = "dida365"
        service_name = "Dida365 (滴答清单)"
        service_emoji = "🇨🇳"
        developer_url = "https://developer.dida365.com/manage"
        use_dida365 = True
    else:
        desired_service = "ticktick"
        service_name = "TickTick"
        service_emoji = "🌍"
        developer_url = "https://developer.ticktick.com/manage"
        use_dida365 = False
    
    console.print(f"\n[bold green]✅ You selected {service_emoji} {service_name}[/bold green]")
    
    # Check if there are existing credentials for the selected service
    existing_config = None
    has_matching_credentials = False
    
    try:
        existing_config = config_manager.load_config()
        # Check if existing config matches the desired service
        if (existing_config.client_id and existing_config.client_secret and
            existing_config.use_dida365 == use_dida365):
            has_matching_credentials = True
    except Exception:
        # Configuration doesn't exist or is invalid
        pass
    
    client_id: str | None = None
    client_secret: str | None = None
    
    if has_matching_credentials:
        console.print(f"\n[bold green]✅ Found existing {service_name} credentials in configuration.[/bold green]")
        
        # Test existing credentials
        with console.status(f"[bold blue]Testing {service_name} API connection...[/bold blue]"):
            test_result = test_existing_credentials(config_manager)
        
        if test_result.success:
            console.print("[bold green]✅ Credentials verified successfully![/bold green]")
            console.print("[dim]You can now run the server with:[/dim] [bold]ticktick-mcp run[/bold]")
            return 0
        else:
            console.print(f"[bold red]❌ Credential test failed:[/bold red] {test_result.error}")
            console.print("[yellow]Proceeding with re-authentication...[/yellow]")
    else:
        # No matching credentials found
        if existing_config and existing_config.client_id:
            other_service = "TickTick" if use_dida365 else "Dida365 (滴答清单)"
            console.print(f"\n[blue]ℹ️ Found existing {other_service} credentials, but you selected {service_name}.[/blue]")
            console.print("[yellow]Setting up new credentials for your selected service...[/yellow]")
        else:
            console.print("\n[blue]ℹ️ No existing credentials found.[/blue]")
        
        # Configure the service endpoint
        if use_dida365:
            console.print("[bold green]✅ Dida365 endpoints will be configured automatically[/bold green]")
            _save_dida365_flag(config_manager)
        else:
            # Remove Dida365 flag if switching from Dida365 to TickTick
            _remove_dida365_flag(config_manager)
    
    # Get credentials (either for re-authentication or new setup)
    setup_panel = Panel(
        f"[bold]1.[/bold] Register your application at:\n   [link]{developer_url}[/link]\n\n"
        f"[bold]2.[/bold] Set the redirect URI to:\n   [cyan]http://localhost:8000/callback[/cyan]\n\n"
        f"[bold]3.[/bold] Get your Client ID and Client Secret",
        title=f"[bold]🔧 Setup Instructions for {service_emoji} {service_name}[/bold]",
        border_style="yellow"
    )
    console.print(setup_panel)
    
    client_id = Prompt.ask("\n[bold]Enter your Client ID[/bold]")
    client_secret = Prompt.ask("[bold]Enter your Client Secret[/bold]", password=True)

    # Reset config cache to ensure new settings are loaded
    config_manager.reset_config()
    
    # Initialize the auth manager with the config manager
    auth = TickTickAuth(
        client_id=client_id, 
        client_secret=client_secret,
        config_manager=config_manager
    )

    console.print("\n[bold blue]🚀 Starting the OAuth authentication flow...[/bold blue]")
    console.print("[dim]A browser window will open for you to authorize the application.[/dim]")
    console.print("[dim]After authorization, you will be redirected back to this application.[/dim]\n")

    # Start the OAuth flow
    result = auth.start_auth_flow()

    console.print(f"\n{result}")

    if "successful" in result.lower():
        # Success panel
        success_steps = Table(show_header=False, box=None, padding=(0, 1))
        success_steps.add_row("[bold]1.[/bold]", "Make sure you have configured Claude for Desktop")
        success_steps.add_row("[bold]2.[/bold]", "Restart Claude for Desktop")
        success_steps.add_row("[bold]3.[/bold]", "You should now see the task management tools available in Claude")
        
        console.print(Panel(
            success_steps,
            title="[bold green]🎉 Authentication Complete![/bold green]",
            subtitle="[dim]Enjoy using your task management system through Claude![/dim]",
            border_style="green"
        ))
        return 0
    else:
        # Error panel
        common_issues = Table(show_header=False, box=None, padding=(0, 1))
        common_issues.add_row("•", "Incorrect Client ID or Client Secret")
        common_issues.add_row("•", "Network connectivity problems")
        common_issues.add_row("•", "Permission issues with the .env file")
        
        console.print(Panel(
            common_issues,
            title="[bold red]❌ Authentication Failed[/bold red]",
            subtitle="[dim]Please try again or check the error message above.[/dim]",
            border_style="red"
        ))
        return 1


def get_user_input(prompt: str) -> str:
    """Get user input with validation."""
    console = Console()
    while True:
        value = Prompt.ask(prompt)
        if value and value.strip():
            return value.strip()
        console.print("[red]This field cannot be empty. Please try again.[/red]")



def _remove_dida365_flag(config_manager: ConfigManager) -> None:
    """Remove USE_DIDA365 flag from configuration file."""
    if not config_manager.env_file.exists():
        return
        
    # Load existing config content
    config_content = {}
    with open(config_manager.env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key != "USE_DIDA365":  # Skip the USE_DIDA365 line
                    config_content[key] = value

    # Write back to config file without USE_DIDA365
    with open(config_manager.env_file, "w") as f:
        for key, value in config_content.items():
            f.write(f"{key}={value}\n")

    Console().print("[bold green]✅ Switched to TickTick mode[/bold green]")


def _save_dida365_flag(config_manager: ConfigManager) -> None:
    """Save USE_DIDA365=true flag to configuration file."""
    # Load existing config content to preserve other settings
    config_content = {}
    if config_manager.env_file.exists():
        with open(config_manager.env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config_content[key] = value

    # Add USE_DIDA365 flag
    config_content["USE_DIDA365"] = "true"

    # Write back to config file
    with open(config_manager.env_file, "w") as f:
        for key, value in config_content.items():
            f.write(f"{key}={value}\n")

    Console().print("[bold green]✅ Dida365 mode enabled in configuration[/bold green]")


if __name__ == "__main__":
    sys.exit(main())
