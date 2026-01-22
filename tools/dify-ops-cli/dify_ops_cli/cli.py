"""CLI entry point for Dify Operations."""

import logging
import sys

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .client.base import DifyClient
from .client.exceptions import DifyClientError
from .config.loader import ConfigLoader
from .services.tenant_service import TenantService

console = Console()


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """Dify Operations CLI - Automate Dify platform operations."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


# Config commands
@cli.group()
def config():
    """Configuration file operations."""
    pass


@config.command()
@click.argument("config_file", type=click.Path(exists=True))
def validate(config_file):
    """Validate a configuration file."""
    console.print(f"[blue]Validating configuration:[/blue] {config_file}")

    is_valid, message = ConfigLoader.validate(config_file)

    if is_valid:
        console.print(f"[green]✓[/green] {message}")
        sys.exit(0)
    else:
        console.print(f"[red]✗[/red] Validation failed:")
        console.print(f"  {message}")
        sys.exit(1)


@config.command()
@click.argument("config_file", type=click.Path(exists=True))
def show(config_file):
    """Show parsed configuration."""
    try:
        cfg = ConfigLoader.load(config_file)
        console.print("[green]✓[/green] Configuration loaded successfully")
        console.print("\n[blue]Configuration:[/blue]")
        console.print(cfg.model_dump_json(indent=2))
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load configuration: {e}")
        sys.exit(1)


# Tenant commands
@cli.group()
def tenant():
    """Tenant and workspace management."""
    pass


@tenant.command()
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.option("--email", prompt=True, help="Owner email address")
@click.option("--name", prompt=True, help="Tenant/workspace name")
@click.option("--language", default="en-US", help="Default language")
def create(api_url, api_key, email, name, language):
    """Create a new tenant/workspace."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = TenantService(client)

            # Import TenantConfig here to avoid circular imports
            from .config.schema import TenantConfig

            config = TenantConfig(name=name, email=email, language=language)

            console.print(f"[blue]Creating tenant:[/blue] {name}")
            result = service.create_tenant(config)

            console.print(f"[green]✓[/green] Tenant created successfully")
            console.print(f"  ID: {result.get('id')}")
            console.print(f"  Name: {result.get('name')}")
            console.print(f"  Email: {result.get('owner_email')}")

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to create tenant: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@tenant.command()
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
def list(api_url, api_key):
    """List all tenants/workspaces."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = TenantService(client)

            console.print("[blue]Fetching tenants...[/blue]")
            tenants = service.list_tenants()

            if not tenants:
                console.print("[yellow]No tenants found[/yellow]")
                return

            # Create a table
            table = Table(title="Tenants")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Email", style="yellow")

            for tenant in tenants:
                table.add_row(
                    tenant.get("id", ""),
                    tenant.get("name", ""),
                    tenant.get("owner_email", ""),
                )

            console.print(table)

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to list tenants: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
