"""Base HTTP client for Dify API."""

import httpx
from typing import Any


class DifyClient:
    """HTTP client for interacting with Dify API."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 300,
        verify_ssl: bool = True,
        ca_bundle_path: str | None = None,
    ):
        """Initialize the Dify API client.

        Args:
            api_url: Base URL of the Dify API
            api_key: API key for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            ca_bundle_path: Path to custom CA certificate bundle file.
                If provided, this will be used for SSL verification instead of verify_ssl.
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

        # Determine SSL verification setting
        # Priority: ca_bundle_path > verify_ssl boolean
        verify: bool | str = verify_ssl
        if ca_bundle_path:
            verify = ca_bundle_path

        self._client = httpx.Client(
            timeout=timeout,
            verify=verify,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def post(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """Send a POST request to the API.

        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = f"{self.api_url}{endpoint}"
        response = self._client.post(url, **kwargs)
        response.raise_for_status()
        return response

    def get(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """Send a GET request to the API.

        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = f"{self.api_url}{endpoint}"
        response = self._client.get(url, **kwargs)
        response.raise_for_status()
        return response

    def patch(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """Send a PATCH request to the API.

        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = f"{self.api_url}{endpoint}"
        response = self._client.patch(url, **kwargs)
        response.raise_for_status()
        return response

    def delete(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """Send a DELETE request to the API.

        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = f"{self.api_url}{endpoint}"
        response = self._client.delete(url, **kwargs)
        response.raise_for_status()
        return response
