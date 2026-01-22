"""Exception classes for Dify API client."""


class DifyClientError(Exception):
    """Base exception for Dify client errors."""

    pass


class DifyAPIError(DifyClientError):
    """Exception raised when the API returns an error."""

    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        """Initialize the API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Response data from the API
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class DifyAuthenticationError(DifyAPIError):
    """Exception raised when authentication fails."""

    pass


class DifyNotFoundError(DifyAPIError):
    """Exception raised when a resource is not found."""

    pass


class DifyValidationError(DifyClientError):
    """Exception raised when validation fails."""

    pass
