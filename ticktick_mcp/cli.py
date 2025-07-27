#!/usr/bin/env python3
"""
Command-line interface for TickTick MCP server.
"""

import logging
import sys

import click

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
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug logging"
)
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
        click.echo()
        click.echo("╔════════════════════════════════════════════════╗")
        click.echo("║      TickTick MCP Server - Authentication      ║")
        click.echo("╚════════════════════════════════════════════════╝")
        click.echo()
        click.echo("Authentication setup required!")
        click.echo("You need to set up TickTick authentication before running the server.")
        click.echo()
        
        if click.confirm("Would you like to set up authentication now?"):
            # Run the auth flow
            auth_result = auth_main()
            if auth_result != 0:
                # Auth failed, exit
                sys.exit(auth_result)
        else:
            click.echo()
            click.echo("Authentication is required to use the TickTick MCP server.")
            click.echo("Run 'uv run -m ticktick_mcp.cli auth' to set up authentication later.")
            sys.exit(1)

    # Configure logging based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO
    logger_manager = LoggerManager()
    logger_manager.setup_logging(level=log_level)

    # Create and start the server
    try:
        server = create_server()
        if not server.initialize():
            click.echo("Failed to initialize TickTick MCP server", err=True)
            sys.exit(1)
        server.run()
    except KeyboardInterrupt:
        click.echo("\nServer stopped by user", err=True)
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error starting server: {e}", err=True)
        sys.exit(1)


@cli.command()
def auth() -> None:
    """Authenticate with TickTick."""
    sys.exit(auth_main())


@cli.command()
def status() -> None:
    """Check authentication status."""
    config_manager = ConfigManager()
    if config_manager.is_authenticated():
        click.echo("✓ Authentication configured")
        click.echo("You can run the server with: uv run -m ticktick_mcp.cli run")
    else:
        click.echo("✗ Authentication not configured")
        click.echo("Run authentication with: uv run -m ticktick_mcp.cli auth")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
