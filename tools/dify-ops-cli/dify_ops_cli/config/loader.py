"""Configuration loader for YAML files."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from .schema import DifyOpsConfig
from ..client.exceptions import DifyValidationError


class ConfigLoader:
    """Loader for configuration files with environment variable substitution."""

    @staticmethod
    def load(config_path: str | Path) -> DifyOpsConfig:
        """Load and validate configuration from a YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Validated configuration object

        Raises:
            DifyValidationError: If the configuration is invalid
            FileNotFoundError: If the configuration file does not exist
        """
        # Load environment variables from .env file if it exists
        load_dotenv()

        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Read YAML file
        with open(config_path, encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        # Substitute environment variables
        raw_config = ConfigLoader._substitute_env_vars(raw_config)

        # Validate configuration
        try:
            config = DifyOpsConfig(**raw_config)
        except ValidationError as e:
            raise DifyValidationError(f"Invalid configuration: {e}") from e

        return config

    @staticmethod
    def _substitute_env_vars(data):
        """Recursively substitute environment variables in configuration.

        Args:
            data: Configuration data (dict, list, or str)

        Returns:
            Data with environment variables substituted
        """
        if isinstance(data, dict):
            return {key: ConfigLoader._substitute_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [ConfigLoader._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Replace ${VAR_NAME} with environment variable value
            if data.startswith("${") and data.endswith("}"):
                env_var = data[2:-1]
                value = os.getenv(env_var)
                if value is None:
                    raise DifyValidationError(f"Environment variable not found: {env_var}")
                return value
            return data
        else:
            return data

    @staticmethod
    def validate(config_path: str | Path) -> tuple[bool, str]:
        """Validate a configuration file without loading it.

        Args:
            config_path: Path to the configuration file

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            ConfigLoader.load(config_path)
            return True, "Configuration is valid"
        except Exception as e:
            return False, str(e)
