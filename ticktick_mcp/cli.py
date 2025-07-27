#!/usr/bin/env python3
"""
Command-line interface for TickTick MCP server.
"""

import logging
import sys

import click
from rich.console import Console
from rich.panel import Panel

from .authenticate import main as auth_main
from .config import ConfigManager
from .logging_config import LoggerManager
from .server_oop import create_server


def check_auth_setup() -> bool:
    """Check if authentication is set up properly."""
    config_manager = ConfigManager()
    return config_manager.is_authenticated()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """TickTick MCP Server - Task management integration for Claude."""
    if ctx.invoked_subcommand is None:
        # Default to run command if no subcommand is provided
        ctx.invoke(run)


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio"]),
    help="Transport type (currently only stdio is supported)",
)
def run(debug: bool, transport: str) -> None:
    """Run the TickTick MCP server."""
    # Note: transport parameter is reserved for future use
    _ = transport  # Currently only stdio is supported

    # Check if auth is set up
    if not check_auth_setup():
        console = Console()

        auth_panel = Panel(
            "[yellow]Authentication setup required![/yellow]\n\n"
            "You need to set up authentication before running the server.",
            title="[bold red]🔒 TickTick / Dida365 MCP Server - Authentication[/bold red]",
            border_style="red",
        )
        console.print(auth_panel)

        if click.confirm("Would you like to set up authentication now?"):
            # Run the auth flow
            auth_result = auth_main()
            if auth_result != 0:
                # Auth failed, exit
                sys.exit(auth_result)
        else:
            console = Console()
            console.print(
                "\n[yellow]Authentication is required to use the MCP server.[/yellow]"
            )
            console.print(
                "Run [bold]'ticktick-mcp auth'[/bold] to set up authentication later."
            )
            sys.exit(1)

    # Configure logging based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO
    logger_manager = LoggerManager()
    logger_manager.setup_logging(level=log_level)

    # Create and start the server
    try:
        server = create_server()
        if not server.initialize():
            console = Console()
            console.print(
                "[bold red]❌ Failed to initialize TickTick MCP server[/bold red]",
                file=sys.stderr,
            )
            sys.exit(1)
        server.run()
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]⚠️ Server stopped by user[/yellow]", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(
            f"[bold red]❌ Error starting server:[/bold red] {e}", file=sys.stderr
        )
        sys.exit(1)


@cli.command()
def auth() -> None:
    """Authenticate with TickTick."""
    sys.exit(auth_main())


@cli.command()
def status() -> None:
    """Check authentication status."""
    console = Console()
    config_manager = ConfigManager()

    if config_manager.is_authenticated():
        status_panel = Panel(
            "[green]✅ Authentication configured[/green]\n\n"
            "You can run the server with: [bold]ticktick-mcp run[/bold]",
            title="[bold green]🔓 Authentication Status[/bold green]",
            border_style="green",
        )
        console.print(status_panel)
    else:
        status_panel = Panel(
            "[red]❌ Authentication not configured[/red]\n\n"
            "Run authentication with: [bold]ticktick-mcp auth[/bold]",
            title="[bold red]🔒 Authentication Status[/bold red]",
            border_style="red",
        )
        console.print(status_panel)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
