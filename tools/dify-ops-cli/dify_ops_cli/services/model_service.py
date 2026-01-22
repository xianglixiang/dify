"""Model provider and model management service."""

import logging

from ..client.base import DifyClient
from ..client.exceptions import DifyAPIError, DifyNotFoundError
from ..config.schema import DefaultModelConfig, ModelConfig, ModelProviderConfig

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing model providers and models."""

    def __init__(self, client: DifyClient):
        """Initialize the model service.

        Args:
            client: Dify API client
        """
        self.client = client

    def configure_provider(self, provider_config: ModelProviderConfig) -> dict:
        """Configure a model provider with credentials and enable models.

        Args:
            provider_config: Provider configuration

        Returns:
            Provider configuration result

        Raises:
            DifyAPIError: If the configuration fails
        """
        provider = provider_config.provider
        logger.info(f"Configuring model provider: {provider}")

        # Set provider credentials
        result = self.set_provider_credentials(provider, provider_config.credentials)

        # Enable models if provided
        if provider_config.models:
            for model_config in provider_config.models:
                if model_config.enabled:
                    self.enable_model(provider, model_config)

        logger.info(f"Provider {provider} configured successfully")
        return result

    def set_provider_credentials(self, provider: str, credentials: dict[str, str]) -> dict:
        """Set credentials for a model provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            credentials: Provider credentials as key-value pairs

        Returns:
            API response data

        Raises:
            DifyAPIError: If the request fails
        """
        logger.info(f"Setting credentials for provider: {provider}")

        try:
            response = self.client.post(
                f"/workspaces/current/model-providers/{provider}/credentials",
                json={"credentials": credentials},
            )

            data = response.json()
            logger.info(f"Credentials set for provider: {provider}")
            return data

        except Exception as e:
            raise DifyAPIError(f"Failed to set provider credentials: {e}") from e

    def enable_model(self, provider: str, model_config: ModelConfig) -> dict:
        """Enable a specific model for a provider.

        Args:
            provider: Provider name
            model_config: Model configuration

        Returns:
            API response data

        Raises:
            DifyAPIError: If the request fails
        """
        logger.info(f"Enabling model: {provider}/{model_config.model} ({model_config.model_type})")

        try:
            response = self.client.patch(
                f"/workspaces/current/model-providers/{provider}/models/enable",
                json={
                    "model": model_config.model,
                    "model_type": model_config.model_type,
                },
            )

            data = response.json()
            logger.info(f"Model enabled: {provider}/{model_config.model}")
            return data

        except Exception as e:
            raise DifyAPIError(f"Failed to enable model: {e}") from e

    def disable_model(self, provider: str, model: str, model_type: str) -> dict:
        """Disable a specific model for a provider.

        Args:
            provider: Provider name
            model: Model name
            model_type: Model type

        Returns:
            API response data

        Raises:
            DifyAPIError: If the request fails
        """
        logger.info(f"Disabling model: {provider}/{model} ({model_type})")

        try:
            response = self.client.patch(
                f"/workspaces/current/model-providers/{provider}/models/disable",
                json={
                    "model": model,
                    "model_type": model_type,
                },
            )

            data = response.json()
            logger.info(f"Model disabled: {provider}/{model}")
            return data

        except Exception as e:
            raise DifyAPIError(f"Failed to disable model: {e}") from e

    def set_default_model(self, default_model_config: DefaultModelConfig) -> dict:
        """Set the default model for the workspace.

        Args:
            default_model_config: Default model configuration

        Returns:
            API response data

        Raises:
            DifyAPIError: If the request fails
        """
        logger.info(
            f"Setting default model: {default_model_config.provider}/"
            f"{default_model_config.model} ({default_model_config.model_type})"
        )

        try:
            response = self.client.post(
                "/workspaces/current/default-model",
                json={
                    "model_provider": default_model_config.provider,
                    "model": default_model_config.model,
                    "model_type": default_model_config.model_type,
                },
            )

            data = response.json()
            logger.info(
                f"Default model set: {default_model_config.provider}/{default_model_config.model}"
            )
            return data

        except Exception as e:
            raise DifyAPIError(f"Failed to set default model: {e}") from e

    def list_providers(self) -> list[dict]:
        """List all model providers.

        Returns:
            List of provider data

        Raises:
            DifyAPIError: If the request fails
        """
        try:
            response = self.client.get("/workspaces/current/model-providers")
            return response.json()

        except Exception as e:
            raise DifyAPIError(f"Failed to list providers: {e}") from e

    def get_provider(self, provider: str) -> dict:
        """Get details of a specific provider.

        Args:
            provider: Provider name

        Returns:
            Provider details

        Raises:
            DifyAPIError: If the request fails
            DifyNotFoundError: If the provider is not found
        """
        providers = self.list_providers()

        for p in providers:
            if p.get("provider") == provider:
                return p

        raise DifyNotFoundError(f"Provider not found: {provider}")

    def get_provider_models(self, provider: str) -> list[dict]:
        """Get available models for a provider.

        Args:
            provider: Provider name

        Returns:
            List of model information

        Raises:
            DifyAPIError: If the request fails
            DifyNotFoundError: If the provider is not found
        """
        provider_data = self.get_provider(provider)
        return provider_data.get("models", [])

    def get_default_model(self) -> dict | None:
        """Get the current default model configuration.

        Returns:
            Default model configuration or None if not set

        Raises:
            DifyAPIError: If the request fails
        """
        try:
            response = self.client.get("/workspaces/current/default-model")
            return response.json()

        except Exception as e:
            logger.warning(f"Failed to get default model: {e}")
            return None

    def configure_multiple_providers(
        self, provider_configs: list[ModelProviderConfig]
    ) -> list[dict]:
        """Configure multiple model providers.

        Args:
            provider_configs: List of provider configurations

        Returns:
            List of configuration results

        Raises:
            DifyAPIError: If any configuration fails
        """
        results = []

        for provider_config in provider_configs:
            result = self.configure_provider(provider_config)
            results.append(
                {
                    "provider": provider_config.provider,
                    "status": "success",
                    "result": result,
                }
            )

        return results
