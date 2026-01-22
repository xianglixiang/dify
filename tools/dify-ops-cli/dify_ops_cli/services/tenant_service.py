"""Tenant management service."""

import logging

from ..client.base import DifyClient
from ..client.exceptions import DifyAPIError
from ..config.schema import TenantConfig

logger = logging.getLogger(__name__)


class TenantService:
    """Service for managing tenants and workspaces."""

    def __init__(self, client: DifyClient):
        """Initialize the tenant service.

        Args:
            client: Dify API client
        """
        self.client = client

    def create_tenant(self, config: TenantConfig, idempotent: bool = True) -> dict:
        """Create a tenant/workspace.

        Args:
            config: Tenant configuration
            idempotent: Whether to check if the tenant already exists

        Returns:
            Created or existing tenant data

        Raises:
            DifyAPIError: If the API request fails
        """
        if idempotent:
            existing = self._find_by_email(config.email)
            if existing:
                logger.info(f"Tenant already exists for email: {config.email}")
                return existing

        logger.info(f"Creating tenant: {config.name}")
        payload = {"name": config.name, "owner_email": config.email}

        try:
            response = self.client.post("/api/enterprise/workspace", json=payload)
            data = response.json()
            logger.info(f"Created tenant: {data.get('id')}")
            return data
        except Exception as e:
            raise DifyAPIError(f"Failed to create tenant: {e}") from e

    def _find_by_email(self, email: str) -> dict | None:
        """Find an existing tenant by owner email.

        Args:
            email: Owner email address

        Returns:
            Tenant data if found, None otherwise
        """
        try:
            response = self.client.get("/api/workspaces")
            workspaces = response.json()

            # Search for workspace with matching owner email
            for workspace in workspaces:
                if workspace.get("owner_email") == email:
                    return workspace

            return None
        except Exception as e:
            logger.warning(f"Failed to query existing tenants: {e}")
            return None

    def list_tenants(self) -> list[dict]:
        """List all tenants/workspaces.

        Returns:
            List of tenant data

        Raises:
            DifyAPIError: If the API request fails
        """
        try:
            response = self.client.get("/api/workspaces")
            return response.json()
        except Exception as e:
            raise DifyAPIError(f"Failed to list tenants: {e}") from e

    def get_tenant(self, tenant_id: str) -> dict:
        """Get details of a specific tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant data

        Raises:
            DifyAPIError: If the API request fails
        """
        try:
            response = self.client.get(f"/api/workspaces/{tenant_id}")
            return response.json()
        except Exception as e:
            raise DifyAPIError(f"Failed to get tenant: {e}") from e
