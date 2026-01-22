"""Retry utilities for handling transient failures."""

import logging
import time
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_exception(
    max_retries: int = 3,
    delay: int = 5,
    backoff: float = 1.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator to retry a function on exception.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry (exponential backoff)
        exceptions: Tuple of exceptions to catch and retry on

    Returns:
        Decorated function

    Example:
        @retry_on_exception(max_retries=3, delay=5)
        def unstable_api_call():
            return api.get_data()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries} retry attempts failed for {func.__name__}: {e}"
                        )

            # If we get here, all retries failed
            raise last_exception

        return wrapper

    return decorator


class RetryContext:
    """Context manager for retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        delay: int = 5,
        backoff: float = 1.0,
        exceptions: tuple = (Exception,),
    ):
        """Initialize retry context.

        Args:
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries in seconds
            backoff: Multiplier for delay after each retry
            exceptions: Tuple of exceptions to catch and retry on
        """
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions
        self.attempt = 0
        self.current_delay = delay

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if exc_type is None:
            return True

        if not isinstance(exc_val, self.exceptions):
            return False

        self.attempt += 1

        if self.attempt <= self.max_retries:
            logger.warning(
                f"Attempt {self.attempt}/{self.max_retries} failed: {exc_val}. "
                f"Retrying in {self.current_delay}s..."
            )
            time.sleep(self.current_delay)
            self.current_delay *= self.backoff
            return True  # Suppress exception, will retry

        return False  # Re-raise exception after all retries


def exponential_backoff(attempt: int, base_delay: int = 1, max_delay: int = 60) -> int:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds for this attempt
    """
    delay = min(base_delay * (2**attempt), max_delay)
    return delay
