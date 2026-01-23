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
from .services.model_service import ModelService
from .services.orchestrator import ConfigurationOrchestrator
from .services.plugin_service import PluginService
from .services.tenant_service import TenantService
from .utils.progress import TaskProgressTracker

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


# Apply command
@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Preview changes without applying them")
@click.option("--fail-fast", is_flag=True, help="Stop on first error")
@click.pass_context
def apply(ctx, config_file, dry_run, fail_fast):
    """Apply configuration from a YAML file.

    This command orchestrates the complete setup of Dify tenants, including:
    - Creating tenants/workspaces
    - Configuring model providers
    - Installing plugins
    - Setting default models

    Example:
        dify-ops apply config.yaml
        dify-ops apply config.yaml --dry-run
        dify-ops apply config.yaml --fail-fast
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        # Load configuration
        console.print(f"[blue]Loading configuration:[/blue] {config_file}")
        config = ConfigLoader.load(config_file)

        # Override options with CLI flags if provided
        if dry_run:
            config.options.dry_run = True
        if fail_fast:
            config.options.fail_fast = True

        console.print(f"[green]✓[/green] Configuration loaded successfully")
        console.print(f"  Tenants to configure: {len(config.tenants)}")
        console.print(f"  Idempotent mode: {config.options.idempotent}")
        console.print(f"  Dry run: {config.options.dry_run}")
        console.print(f"  Fail fast: {config.options.fail_fast}")

        # Create client and orchestrator
        with DifyClient(
            config.connection.api_url,
            config.connection.api_key,
            timeout=config.connection.timeout,
            verify_ssl=config.connection.verify_ssl,
            ca_bundle_path=config.connection.ca_bundle_path,
        ) as client:
            orchestrator = ConfigurationOrchestrator(client, config)

            # Execute configuration
            results = orchestrator.execute()

            # Check for errors
            if results.get("errors"):
                console.print(f"\n[yellow]⚠ Configuration completed with errors[/yellow]")
                sys.exit(1)

    except DifyClientError as e:
        console.print(f"\n[red]✗[/red] Configuration failed: {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Unexpected error: {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


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


# Plugin commands
@cli.group()
def plugin():
    """Plugin management."""
    pass


@plugin.command()
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("plugin_file", type=click.Path(exists=True))
@click.option("--no-install", is_flag=True, help="Upload only, do not install")
@click.option("--no-wait", is_flag=True, help="Do not wait for installation to complete")
def upload(api_url, api_key, plugin_file, no_install, no_wait):
    """Upload a plugin package file."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = PluginService(client)

            console.print(f"[blue]Uploading plugin:[/blue] {plugin_file}")
            plugin_id = service.upload_plugin(plugin_file)

            console.print(f"[green]✓[/green] Plugin uploaded successfully")
            console.print(f"  Plugin ID: {plugin_id}")

            if not no_install:
                console.print(f"\n[blue]Installing plugin:[/blue] {plugin_id}")
                task_id = service.install_plugin(plugin_id)
                console.print(f"  Task ID: {task_id}")

                if not no_wait:
                    with TaskProgressTracker() as tracker:
                        task = tracker.add_task(f"Installing {plugin_id}...")

                        # Wait for completion with progress updates
                        final_status = service.wait_for_task(task_id)

                        tracker.update(task, advance=100, description=f"Installed {plugin_id}")

                    console.print(f"[green]✓[/green] Plugin installed successfully")
                else:
                    console.print(f"[yellow]Installation started in background[/yellow]")
                    console.print(f"  Check status with: dify-ops plugin task-status {task_id}")

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to upload plugin: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@plugin.command()
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("plugin_id")
@click.option("--no-wait", is_flag=True, help="Do not wait for installation to complete")
def install(api_url, api_key, plugin_id, no_wait):
    """Install a plugin by its unique identifier."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = PluginService(client)

            console.print(f"[blue]Installing plugin:[/blue] {plugin_id}")
            task_id = service.install_plugin(plugin_id)
            console.print(f"  Task ID: {task_id}")

            if not no_wait:
                with TaskProgressTracker() as tracker:
                    task = tracker.add_task(f"Installing {plugin_id}...")
                    service.wait_for_task(task_id)
                    tracker.update(task, advance=100, description=f"Installed {plugin_id}")

                console.print(f"[green]✓[/green] Plugin installed successfully")
            else:
                console.print(f"[yellow]Installation started in background[/yellow]")
                console.print(f"  Check status with: dify-ops plugin task-status {task_id}")

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to install plugin: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@plugin.command("batch-install")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("plugin_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--no-wait", is_flag=True, help="Do not wait for installation to complete")
def batch_install(api_url, api_key, plugin_files, no_wait):
    """Upload and install multiple plugin files in batch."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = PluginService(client)
            plugin_ids = []

            # Upload all plugins first
            console.print(f"[blue]Uploading {len(plugin_files)} plugins...[/blue]")

            with TaskProgressTracker() as tracker:
                upload_task = tracker.add_task("Uploading plugins...", total=len(plugin_files))

                for plugin_file in plugin_files:
                    tracker.update(upload_task, description=f"Uploading {plugin_file}...")
                    plugin_id = service.upload_plugin(plugin_file)
                    plugin_ids.append(plugin_id)
                    tracker.update(upload_task, advance=100 / len(plugin_files))

                tracker.complete(upload_task, f"Uploaded {len(plugin_ids)} plugins")

            console.print(f"[green]✓[/green] All plugins uploaded successfully")
            console.print(f"  Plugin IDs: {', '.join(plugin_ids)}")

            # Batch install all plugins
            console.print(f"\n[blue]Installing {len(plugin_ids)} plugins in batch...[/blue]")
            task_id = service.install_plugins_batch(plugin_ids)
            console.print(f"  Task ID: {task_id}")

            if not no_wait:
                with TaskProgressTracker() as tracker:
                    install_task = tracker.add_task(f"Installing {len(plugin_ids)} plugins...")
                    service.wait_for_task(task_id, timeout=600)  # Longer timeout for batch
                    tracker.update(install_task, advance=100, description=f"Installed {len(plugin_ids)} plugins")

                console.print(f"[green]✓[/green] All plugins installed successfully")
            else:
                console.print(f"[yellow]Installation started in background[/yellow]")
                console.print(f"  Check status with: dify-ops plugin task-status {task_id}")

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to batch install plugins: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@plugin.command("task-status")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("task_id")
def task_status(api_url, api_key, task_id):
    """Check the status of a plugin installation task."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = PluginService(client)

            console.print(f"[blue]Checking task status:[/blue] {task_id}")
            status = service.get_task_status(task_id)

            # Create a table for status
            table = Table(title=f"Task {task_id}")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Status", status.get("status", "unknown"))
            table.add_row("Created", status.get("created_at", ""))
            table.add_row("Updated", status.get("updated_at", ""))

            if status.get("error"):
                table.add_row("Error", status.get("error"))

            console.print(table)

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to get task status: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@plugin.command()
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
def list(api_url, api_key, page, page_size):
    """List installed plugins."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = PluginService(client)

            console.print("[blue]Fetching installed plugins...[/blue]")
            data = service.list_plugins(page=page, page_size=page_size)

            plugins = data.get("data", [])
            total = data.get("total", 0)

            if not plugins:
                console.print("[yellow]No plugins found[/yellow]")
                return

            # Create a table
            table = Table(title=f"Installed Plugins (Page {page}, Total: {total})")
            table.add_column("Plugin ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("Version", style="yellow")
            table.add_column("Status", style="blue")

            for plugin in plugins:
                table.add_row(
                    plugin.get("plugin_unique_identifier", "")[:40],  # Truncate long IDs
                    plugin.get("name", ""),
                    plugin.get("version", ""),
                    plugin.get("status", ""),
                )

            console.print(table)

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to list plugins: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


# Model commands
@cli.group()
def model():
    """Model provider and model management."""
    pass


@model.command("add-provider")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("provider")
@click.option("--credentials", "-c", multiple=True, help="Credentials as key=value pairs")
def add_provider(api_url, api_key, provider, credentials):
    """Add or update a model provider with credentials.

    Example:
        dify-ops model add-provider openai -c openai_api_key=sk-xxx
        dify-ops model add-provider anthropic -c anthropic_api_key=sk-ant-xxx
    """
    try:
        # Parse credentials
        creds_dict = {}
        for cred in credentials:
            if "=" not in cred:
                console.print(f"[red]✗[/red] Invalid credential format: {cred}")
                console.print("  Use format: key=value")
                sys.exit(1)
            key, value = cred.split("=", 1)
            creds_dict[key] = value

        if not creds_dict:
            console.print("[red]✗[/red] No credentials provided")
            console.print("  Use -c key=value to provide credentials")
            sys.exit(1)

        with DifyClient(api_url, api_key) as client:
            service = ModelService(client)

            console.print(f"[blue]Adding provider:[/blue] {provider}")
            result = service.set_provider_credentials(provider, creds_dict)

            console.print(f"[green]✓[/green] Provider added successfully")
            console.print(f"  Provider: {provider}")
            console.print(f"  Credentials: {', '.join(creds_dict.keys())}")

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to add provider: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@model.command("enable")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("provider")
@click.argument("model_name")
@click.option(
    "--model-type",
    type=click.Choice(["llm", "text-embedding", "rerank", "speech2text", "tts"]),
    default="llm",
    help="Model type",
)
def enable_model(api_url, api_key, provider, model_name, model_type):
    """Enable a model for a provider.

    Example:
        dify-ops model enable openai gpt-4o --model-type llm
        dify-ops model enable openai text-embedding-3-large --model-type text-embedding
    """
    try:
        with DifyClient(api_url, api_key) as client:
            service = ModelService(client)

            # Import ModelConfig to create config object
            from .config.schema import ModelConfig

            model_config = ModelConfig(
                model=model_name,
                model_type=model_type,
                enabled=True,
            )

            console.print(f"[blue]Enabling model:[/blue] {provider}/{model_name} ({model_type})")
            service.enable_model(provider, model_config)

            console.print(f"[green]✓[/green] Model enabled successfully")
            console.print(f"  Provider: {provider}")
            console.print(f"  Model: {model_name}")
            console.print(f"  Type: {model_type}")

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to enable model: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@model.command("disable")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("provider")
@click.argument("model_name")
@click.option(
    "--model-type",
    type=click.Choice(["llm", "text-embedding", "rerank", "speech2text", "tts"]),
    default="llm",
    help="Model type",
)
def disable_model(api_url, api_key, provider, model_name, model_type):
    """Disable a model for a provider.

    Example:
        dify-ops model disable openai gpt-3.5-turbo
    """
    try:
        with DifyClient(api_url, api_key) as client:
            service = ModelService(client)

            console.print(f"[blue]Disabling model:[/blue] {provider}/{model_name} ({model_type})")
            service.disable_model(provider, model_name, model_type)

            console.print(f"[green]✓[/green] Model disabled successfully")
            console.print(f"  Provider: {provider}")
            console.print(f"  Model: {model_name}")
            console.print(f"  Type: {model_type}")

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to disable model: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@model.command("set-default")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("provider")
@click.argument("model_name")
@click.option(
    "--model-type",
    type=click.Choice(["llm", "text-embedding", "rerank", "speech2text", "tts"]),
    default="llm",
    help="Model type",
)
def set_default_model(api_url, api_key, provider, model_name, model_type):
    """Set the default model for the workspace.

    Example:
        dify-ops model set-default openai gpt-4o --model-type llm
    """
    try:
        with DifyClient(api_url, api_key) as client:
            service = ModelService(client)

            # Import DefaultModelConfig
            from .config.schema import DefaultModelConfig

            config = DefaultModelConfig(
                provider=provider,
                model=model_name,
                model_type=model_type,
            )

            console.print(f"[blue]Setting default model:[/blue] {provider}/{model_name} ({model_type})")
            service.set_default_model(config)

            console.print(f"[green]✓[/green] Default model set successfully")
            console.print(f"  Provider: {provider}")
            console.print(f"  Model: {model_name}")
            console.print(f"  Type: {model_type}")

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to set default model: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@model.command("list-providers")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
def list_providers(api_url, api_key):
    """List all model providers."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = ModelService(client)

            console.print("[blue]Fetching model providers...[/blue]")
            providers = service.list_providers()

            if not providers:
                console.print("[yellow]No providers found[/yellow]")
                return

            # Create a table
            table = Table(title="Model Providers")
            table.add_column("Provider", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Models Count", style="yellow")

            for provider in providers:
                provider_name = provider.get("provider", "")
                status = "Configured" if provider.get("is_valid") else "Not Configured"
                models_count = str(len(provider.get("models", [])))

                table.add_row(provider_name, status, models_count)

            console.print(table)

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to list providers: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@model.command("list-models")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
@click.argument("provider")
def list_models(api_url, api_key, provider):
    """List available models for a provider.

    Example:
        dify-ops model list-models openai
    """
    try:
        with DifyClient(api_url, api_key) as client:
            service = ModelService(client)

            console.print(f"[blue]Fetching models for provider:[/blue] {provider}")
            models = service.get_provider_models(provider)

            if not models:
                console.print(f"[yellow]No models found for provider: {provider}[/yellow]")
                return

            # Create a table
            table = Table(title=f"Models for {provider}")
            table.add_column("Model", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Status", style="yellow")

            for model in models:
                model_name = model.get("model", "")
                model_type = model.get("model_type", "")
                status = "Enabled" if model.get("enabled") else "Disabled"

                table.add_row(model_name, model_type, status)

            console.print(table)

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to list models: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@model.command("get-default")
@click.option("--api-url", envvar="DIFY_API_URL", required=True, help="Dify API URL")
@click.option("--api-key", envvar="DIFY_API_KEY", required=True, help="Dify API key")
def get_default_model(api_url, api_key):
    """Get the current default model."""
    try:
        with DifyClient(api_url, api_key) as client:
            service = ModelService(client)

            console.print("[blue]Fetching default model...[/blue]")
            default_model = service.get_default_model()

            if not default_model:
                console.print("[yellow]No default model configured[/yellow]")
                return

            # Create a table
            table = Table(title="Default Model")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Provider", default_model.get("model_provider", ""))
            table.add_row("Model", default_model.get("model", ""))
            table.add_row("Type", default_model.get("model_type", ""))

            console.print(table)

    except DifyClientError as e:
        console.print(f"[red]✗[/red] Failed to get default model: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
