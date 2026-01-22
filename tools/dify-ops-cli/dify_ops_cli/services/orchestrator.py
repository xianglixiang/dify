"""Configuration orchestration service."""

import logging
from typing import Any

from rich.console import Console

from ..client.base import DifyClient
from ..config.schema import DifyOpsConfig, TenantConfig
from .model_service import ModelService
from .plugin_service import PluginService
from .tenant_service import TenantService

logger = logging.getLogger(__name__)
console = Console()


class ConfigurationOrchestrator:
    """Orchestrates the application of complete Dify configuration."""

    def __init__(self, client: DifyClient, config: DifyOpsConfig):
        """Initialize the orchestrator.

        Args:
            client: Dify API client
            config: Complete configuration to apply
        """
        self.client = client
        self.config = config
        self.tenant_service = TenantService(client)
        self.plugin_service = PluginService(client)
        self.model_service = ModelService(client)

        # Extract options
        self.options = config.options
        self.idempotent = self.options.idempotent
        self.fail_fast = self.options.fail_fast
        self.max_retries = self.options.max_retries
        self.retry_delay = self.options.retry_delay
        self.dry_run = self.options.dry_run

    def execute(self) -> dict[str, Any]:
        """Execute the complete configuration.

        Returns:
            Execution results with status and details

        Raises:
            Exception: If execution fails and fail_fast is True
        """
        if self.dry_run:
            return self._dry_run()

        logger.info("Starting configuration orchestration")
        console.print("\n[bold blue]🚀 Starting Dify Configuration[/bold blue]\n")

        results = {
            "tenants": [],
            "errors": [],
            "summary": {},
        }

        # Process each tenant configuration
        for idx, tenant_config in enumerate(self.config.tenants, 1):
            console.print(f"[bold cyan]Processing tenant {idx}/{len(self.config.tenants)}:[/bold cyan] {tenant_config.name}")

            try:
                tenant_result = self._configure_tenant(tenant_config)
                results["tenants"].append(tenant_result)

            except Exception as e:
                error_info = {
                    "tenant": tenant_config.name,
                    "error": str(e),
                }
                results["errors"].append(error_info)

                logger.error(f"Failed to configure tenant {tenant_config.name}: {e}")
                console.print(f"[red]✗[/red] Failed to configure tenant: {e}\n")

                if self.fail_fast:
                    raise

        # Generate summary
        results["summary"] = self._generate_summary(results)

        console.print("\n[bold green]✓ Configuration completed[/bold green]\n")
        self._print_summary(results["summary"])

        return results

    def _configure_tenant(self, tenant_config: TenantConfig) -> dict[str, Any]:
        """Configure a single tenant with all its components.

        Args:
            tenant_config: Tenant configuration

        Returns:
            Configuration result
        """
        result = {
            "tenant": None,
            "model_providers": [],
            "plugins": [],
            "default_model": None,
        }

        # Step 1: Create tenant
        console.print("  [blue]1/4[/blue] Creating tenant...")
        tenant = self.tenant_service.create_tenant(tenant_config, idempotent=self.idempotent)
        result["tenant"] = tenant
        console.print(f"  [green]✓[/green] Tenant: {tenant.get('name', tenant_config.name)}")

        # Step 2: Configure model providers
        if tenant_config.model_providers:
            console.print(f"\n  [blue]2/4[/blue] Configuring {len(tenant_config.model_providers)} model provider(s)...")

            for provider_config in tenant_config.model_providers:
                try:
                    provider_result = self.model_service.configure_provider(provider_config)
                    result["model_providers"].append({
                        "provider": provider_config.provider,
                        "status": "success",
                        "models_enabled": len([m for m in provider_config.models if m.enabled]),
                    })
                    console.print(f"  [green]✓[/green] Provider: {provider_config.provider}")

                except Exception as e:
                    logger.error(f"Failed to configure provider {provider_config.provider}: {e}")
                    result["model_providers"].append({
                        "provider": provider_config.provider,
                        "status": "failed",
                        "error": str(e),
                    })
                    console.print(f"  [red]✗[/red] Provider {provider_config.provider} failed: {e}")

                    if self.fail_fast:
                        raise
        else:
            console.print("\n  [blue]2/4[/blue] No model providers to configure")

        # Step 3: Install plugins
        if tenant_config.plugins:
            console.print(f"\n  [blue]3/4[/blue] Installing {len(tenant_config.plugins)} plugin(s)...")

            for plugin_config in tenant_config.plugins:
                try:
                    plugin_id, task_id = self.plugin_service.upload_and_install(
                        plugin_config,
                        wait=True,
                        timeout=300,
                    )
                    result["plugins"].append({
                        "plugin_id": plugin_id,
                        "status": "success",
                        "installed": plugin_config.install,
                    })
                    console.print(f"  [green]✓[/green] Plugin: {plugin_id[:40]}...")

                except Exception as e:
                    logger.error(f"Failed to install plugin {plugin_config.path}: {e}")
                    result["plugins"].append({
                        "path": plugin_config.path,
                        "status": "failed",
                        "error": str(e),
                    })
                    console.print(f"  [red]✗[/red] Plugin {plugin_config.path} failed: {e}")

                    if self.fail_fast:
                        raise
        else:
            console.print("\n  [blue]3/4[/blue] No plugins to install")

        # Step 4: Set default model
        if tenant_config.default_model:
            console.print("\n  [blue]4/4[/blue] Setting default model...")

            try:
                default_result = self.model_service.set_default_model(tenant_config.default_model)
                result["default_model"] = {
                    "provider": tenant_config.default_model.provider,
                    "model": tenant_config.default_model.model,
                    "status": "success",
                }
                console.print(
                    f"  [green]✓[/green] Default model: "
                    f"{tenant_config.default_model.provider}/{tenant_config.default_model.model}"
                )

            except Exception as e:
                logger.error(f"Failed to set default model: {e}")
                result["default_model"] = {
                    "status": "failed",
                    "error": str(e),
                }
                console.print(f"  [red]✗[/red] Default model failed: {e}")

                if self.fail_fast:
                    raise
        else:
            console.print("\n  [blue]4/4[/blue] No default model to set")

        console.print("")  # Empty line for spacing
        return result

    def _dry_run(self) -> dict[str, Any]:
        """Perform a dry run (preview without execution).

        Returns:
            Preview of what would be executed
        """
        console.print("\n[bold yellow]🔍 DRY RUN MODE - No changes will be made[/bold yellow]\n")

        preview = {
            "mode": "dry_run",
            "tenants": [],
        }

        for idx, tenant_config in enumerate(self.config.tenants, 1):
            console.print(f"[bold cyan]Tenant {idx}:[/bold cyan] {tenant_config.name}")
            console.print(f"  Email: {tenant_config.email}")
            console.print(f"  Language: {tenant_config.language}")

            tenant_preview = {
                "name": tenant_config.name,
                "email": tenant_config.email,
                "model_providers": [],
                "plugins": [],
                "default_model": None,
            }

            if tenant_config.model_providers:
                console.print(f"\n  Model Providers ({len(tenant_config.model_providers)}):")
                for provider_config in tenant_config.model_providers:
                    console.print(f"    • {provider_config.provider}")
                    enabled_models = [m for m in provider_config.models if m.enabled]
                    if enabled_models:
                        console.print(f"      Models to enable: {len(enabled_models)}")
                        for model in enabled_models[:3]:  # Show first 3
                            console.print(f"        - {model.model} ({model.model_type})")
                        if len(enabled_models) > 3:
                            console.print(f"        ... and {len(enabled_models) - 3} more")

                    tenant_preview["model_providers"].append({
                        "provider": provider_config.provider,
                        "models_count": len(enabled_models),
                    })

            if tenant_config.plugins:
                console.print(f"\n  Plugins ({len(tenant_config.plugins)}):")
                for plugin_config in tenant_config.plugins:
                    action = "Upload & Install" if plugin_config.install else "Upload only"
                    console.print(f"    • {plugin_config.path} ({action})")
                    tenant_preview["plugins"].append({
                        "path": plugin_config.path,
                        "install": plugin_config.install,
                    })

            if tenant_config.default_model:
                console.print(f"\n  Default Model:")
                console.print(
                    f"    • {tenant_config.default_model.provider}/"
                    f"{tenant_config.default_model.model} ({tenant_config.default_model.model_type})"
                )
                tenant_preview["default_model"] = {
                    "provider": tenant_config.default_model.provider,
                    "model": tenant_config.default_model.model,
                }

            console.print("")  # Empty line
            preview["tenants"].append(tenant_preview)

        console.print("[bold yellow]✓ Dry run completed - No changes were made[/bold yellow]\n")
        return preview

    def _generate_summary(self, results: dict) -> dict[str, Any]:
        """Generate execution summary.

        Args:
            results: Execution results

        Returns:
            Summary statistics
        """
        summary = {
            "total_tenants": len(self.config.tenants),
            "successful_tenants": len(results["tenants"]),
            "failed_tenants": len(results["errors"]),
            "total_providers": 0,
            "successful_providers": 0,
            "total_plugins": 0,
            "successful_plugins": 0,
            "default_models_set": 0,
        }

        for tenant_result in results["tenants"]:
            # Count providers
            providers = tenant_result.get("model_providers", [])
            summary["total_providers"] += len(providers)
            summary["successful_providers"] += sum(
                1 for p in providers if p.get("status") == "success"
            )

            # Count plugins
            plugins = tenant_result.get("plugins", [])
            summary["total_plugins"] += len(plugins)
            summary["successful_plugins"] += sum(
                1 for p in plugins if p.get("status") == "success"
            )

            # Count default models
            if tenant_result.get("default_model", {}).get("status") == "success":
                summary["default_models_set"] += 1

        return summary

    def _print_summary(self, summary: dict[str, Any]):
        """Print execution summary.

        Args:
            summary: Summary statistics
        """
        console.print("[bold]Configuration Summary:[/bold]")
        console.print(f"  Tenants: {summary['successful_tenants']}/{summary['total_tenants']} successful")

        if summary["total_providers"] > 0:
            console.print(
                f"  Model Providers: {summary['successful_providers']}/{summary['total_providers']} configured"
            )

        if summary["total_plugins"] > 0:
            console.print(
                f"  Plugins: {summary['successful_plugins']}/{summary['total_plugins']} installed"
            )

        if summary["default_models_set"] > 0:
            console.print(f"  Default Models: {summary['default_models_set']} set")

        if summary["failed_tenants"] > 0:
            console.print(f"\n  [red]⚠ {summary['failed_tenants']} tenant(s) failed[/red]")
