"""Configuration schema definitions using Pydantic."""

from typing import Literal

from pydantic import BaseModel, Field


class ConnectionConfig(BaseModel):
    """API connection configuration."""

    api_url: str = Field(..., description="Base URL of the Dify API")
    api_key: str = Field(..., description="API key for authentication")
    timeout: int = Field(default=300, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Whether to verify SSL certificates")


class ModelConfig(BaseModel):
    """Model configuration."""

    model: str = Field(..., description="Model name")
    model_type: Literal["llm", "text-embedding", "rerank", "speech2text", "tts"] = Field(
        ..., description="Model type"
    )
    enabled: bool = Field(default=True, description="Whether the model is enabled")


class ModelProviderConfig(BaseModel):
    """Model provider configuration."""

    provider: str = Field(..., description="Provider name (e.g., openai, anthropic)")
    credentials: dict[str, str] = Field(..., description="Provider credentials")
    models: list[ModelConfig] = Field(default_factory=list, description="List of models to configure")


class PluginConfig(BaseModel):
    """Plugin configuration."""

    source: Literal["local", "marketplace"] = Field(default="local", description="Plugin source")
    path: str | None = Field(default=None, description="Local file path for the plugin")
    install: bool = Field(default=True, description="Whether to install the plugin after upload")


class DefaultModelConfig(BaseModel):
    """Default model configuration."""

    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model name")
    model_type: Literal["llm", "text-embedding", "rerank", "speech2text", "tts"] = Field(
        ..., description="Model type"
    )


class TenantConfig(BaseModel):
    """Tenant configuration."""

    name: str = Field(..., description="Tenant/workspace name")
    email: str = Field(..., description="Owner email address")
    language: str = Field(default="en-US", description="Default language")
    model_providers: list[ModelProviderConfig] = Field(
        default_factory=list, description="List of model providers to configure"
    )
    plugins: list[PluginConfig] = Field(default_factory=list, description="List of plugins to install")
    default_model: DefaultModelConfig | None = Field(default=None, description="Default model configuration")


class OptionsConfig(BaseModel):
    """Execution options."""

    idempotent: bool = Field(default=True, description="Whether operations should be idempotent")
    fail_fast: bool = Field(default=False, description="Whether to stop on first error")
    max_retries: int = Field(default=3, description="Maximum number of retries for failed operations")
    retry_delay: int = Field(default=5, description="Delay between retries in seconds")
    dry_run: bool = Field(default=False, description="Whether to perform a dry run")


class MetadataConfig(BaseModel):
    """Configuration metadata."""

    name: str | None = Field(default=None, description="Configuration name")
    description: str | None = Field(default=None, description="Configuration description")


class DifyOpsConfig(BaseModel):
    """Root configuration model."""

    version: str = Field(pattern=r"^1\.0$", description="Configuration version")
    metadata: MetadataConfig | None = Field(default=None, description="Configuration metadata")
    connection: ConnectionConfig = Field(..., description="API connection settings")
    tenants: list[TenantConfig] = Field(..., description="List of tenants to configure")
    options: OptionsConfig = Field(default_factory=OptionsConfig, description="Execution options")
