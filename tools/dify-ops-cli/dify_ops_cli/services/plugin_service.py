"""Plugin management service."""

import logging
import time
from pathlib import Path

from ..client.base import DifyClient
from ..client.exceptions import DifyAPIError, DifyNotFoundError
from ..config.schema import PluginConfig

logger = logging.getLogger(__name__)


class PluginService:
    """Service for managing plugins."""

    def __init__(self, client: DifyClient):
        """Initialize the plugin service.

        Args:
            client: Dify API client
        """
        self.client = client

    def upload_plugin(self, plugin_path: str | Path) -> str:
        """Upload a plugin package file.

        Args:
            plugin_path: Path to the plugin package (.difypkg file)

        Returns:
            Plugin unique identifier

        Raises:
            DifyAPIError: If the upload fails
            FileNotFoundError: If the plugin file does not exist
        """
        plugin_path = Path(plugin_path)
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")

        if not plugin_path.name.endswith(".difypkg"):
            logger.warning(f"Plugin file does not have .difypkg extension: {plugin_path}")

        logger.info(f"Uploading plugin: {plugin_path.name}")

        try:
            with open(plugin_path, "rb") as f:
                files = {"file": (plugin_path.name, f, "application/octet-stream")}
                # Note: when uploading files, we need to remove Content-Type: application/json header
                response = self.client._client.post(
                    f"{self.client.api_url}/workspaces/current/plugin/upload/pkg",
                    files=files,
                    headers={"Authorization": f"Bearer {self.client.api_key}"},
                )
                response.raise_for_status()

            data = response.json()
            plugin_id = data.get("plugin_unique_identifier")

            if not plugin_id:
                raise DifyAPIError("Failed to get plugin ID from upload response")

            logger.info(f"Uploaded plugin: {plugin_id}")
            return plugin_id

        except Exception as e:
            raise DifyAPIError(f"Failed to upload plugin: {e}") from e

    def install_plugin(self, plugin_id: str) -> str:
        """Install a plugin by its unique identifier.

        Args:
            plugin_id: Plugin unique identifier

        Returns:
            Task ID for the installation

        Raises:
            DifyAPIError: If the installation fails
        """
        logger.info(f"Installing plugin: {plugin_id}")

        try:
            response = self.client.post(
                "/workspaces/current/plugin/install/pkg",
                json={"plugin_unique_identifiers": [plugin_id]},
            )

            data = response.json()
            task_id = data.get("task_id")

            if not task_id:
                raise DifyAPIError("Failed to get task ID from install response")

            logger.info(f"Installation started, task ID: {task_id}")
            return task_id

        except Exception as e:
            raise DifyAPIError(f"Failed to install plugin: {e}") from e

    def install_plugins_batch(self, plugin_ids: list[str]) -> str:
        """Install multiple plugins in a single batch operation.

        Args:
            plugin_ids: List of plugin unique identifiers

        Returns:
            Task ID for the batch installation

        Raises:
            DifyAPIError: If the installation fails
        """
        logger.info(f"Installing {len(plugin_ids)} plugins in batch")

        try:
            response = self.client.post(
                "/workspaces/current/plugin/install/pkg",
                json={"plugin_unique_identifiers": plugin_ids},
            )

            data = response.json()
            task_id = data.get("task_id")

            if not task_id:
                raise DifyAPIError("Failed to get task ID from batch install response")

            logger.info(f"Batch installation started, task ID: {task_id}")
            return task_id

        except Exception as e:
            raise DifyAPIError(f"Failed to install plugins in batch: {e}") from e

    def get_task_status(self, task_id: str) -> dict:
        """Get the status of a plugin installation task.

        Args:
            task_id: Task ID

        Returns:
            Task status information

        Raises:
            DifyAPIError: If the request fails
        """
        try:
            response = self.client.get(f"/workspaces/current/plugin/tasks/{task_id}")
            return response.json()
        except Exception as e:
            raise DifyAPIError(f"Failed to get task status: {e}") from e

    def wait_for_task(self, task_id: str, timeout: int = 300, poll_interval: int = 5) -> dict:
        """Wait for a plugin installation task to complete.

        Args:
            task_id: Task ID
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            Final task status

        Raises:
            DifyAPIError: If the task fails or times out
        """
        logger.info(f"Waiting for task {task_id} to complete (timeout: {timeout}s)")

        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            current_status = status.get("status")

            # Log status changes
            if current_status != last_status:
                logger.info(f"Task {task_id} status: {current_status}")
                last_status = current_status

            if current_status == "completed":
                logger.info(f"Task {task_id} completed successfully")
                return status
            elif current_status == "failed":
                error_msg = status.get("error", "Unknown error")
                raise DifyAPIError(f"Task {task_id} failed: {error_msg}")
            elif current_status == "stopped":
                raise DifyAPIError(f"Task {task_id} was stopped")

            time.sleep(poll_interval)

        raise DifyAPIError(f"Task {task_id} timed out after {timeout} seconds")

    def upload_and_install(
        self, plugin_config: PluginConfig, wait: bool = True, timeout: int = 300
    ) -> tuple[str, str | None]:
        """Upload and optionally install a plugin.

        Args:
            plugin_config: Plugin configuration
            wait: Whether to wait for installation to complete
            timeout: Maximum time to wait for installation

        Returns:
            Tuple of (plugin_id, task_id or None)

        Raises:
            DifyAPIError: If the operation fails
        """
        if not plugin_config.path:
            raise DifyAPIError("Plugin path is required for local plugins")

        # Upload the plugin
        plugin_id = self.upload_plugin(plugin_config.path)

        # Install if requested
        if plugin_config.install:
            task_id = self.install_plugin(plugin_id)

            # Wait for completion if requested
            if wait:
                self.wait_for_task(task_id, timeout=timeout)

            return plugin_id, task_id

        return plugin_id, None

    def list_plugins(self, page: int = 1, page_size: int = 100) -> dict:
        """List installed plugins.

        Args:
            page: Page number
            page_size: Number of items per page

        Returns:
            Plugin list data

        Raises:
            DifyAPIError: If the request fails
        """
        try:
            response = self.client.get(
                "/workspaces/current/plugin/list",
                params={"page": page, "page_size": page_size},
            )
            return response.json()
        except Exception as e:
            raise DifyAPIError(f"Failed to list plugins: {e}") from e

    def get_plugin(self, plugin_id: str) -> dict:
        """Get details of a specific plugin.

        Args:
            plugin_id: Plugin unique identifier

        Returns:
            Plugin details

        Raises:
            DifyAPIError: If the request fails
            DifyNotFoundError: If the plugin is not found
        """
        plugins_data = self.list_plugins()
        plugins = plugins_data.get("data", [])

        for plugin in plugins:
            if plugin.get("plugin_unique_identifier") == plugin_id:
                return plugin

        raise DifyNotFoundError(f"Plugin not found: {plugin_id}")
