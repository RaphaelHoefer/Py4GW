"""
Retry and safe execution utilities for Py4GW.

Provides decorators and functions for handling transient failures gracefully.
"""

import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, Union

import Py4GW

T = TypeVar('T')


def retry_on_failure(
    max_retries: int = 3,
    delay_ms: int = 100,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Decorator that retries a function on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay_ms: Initial delay between retries in milliseconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback called on each retry with (exception, attempt_number)

    Usage:
        @retry_on_failure(max_retries=3, delay_ms=100)
        def flaky_operation():
            # This will be retried up to 3 times on failure
            return some_unreliable_call()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay_ms

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        if on_retry:
                            on_retry(e, attempt + 1)

                        time.sleep(current_delay / 1000.0)
                        current_delay = int(current_delay * backoff_factor)

            # All retries exhausted, raise the last exception
            raise last_exception

        return wrapper
    return decorator


def safe_execute(
    func: Callable[..., T],
    *args,
    fallback: T = None,
    log_error: bool = True,
    module_name: str = "SafeExecute",
    **kwargs
) -> T:
    """
    Execute a function safely, returning a fallback value on failure.

    Args:
        func: The function to execute
        *args: Arguments to pass to the function
        fallback: Value to return if the function fails
        log_error: Whether to log errors to the console
        module_name: Module name for logging
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The function result, or fallback on failure

    Usage:
        result = safe_execute(risky_function, arg1, arg2, fallback=default_value)
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            Py4GW.Console.Log(
                module_name,
                f"Error executing {func.__name__}: {str(e)}",
                Py4GW.Console.MessageType.Error
            )
        return fallback


def safe_execute_with_retry(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    delay_ms: int = 100,
    fallback: T = None,
    log_error: bool = True,
    module_name: str = "SafeExecute",
    **kwargs
) -> T:
    """
    Execute a function with retries, returning fallback on complete failure.

    Combines retry logic with safe execution - will retry on failure but
    ultimately return a fallback value if all retries are exhausted.

    Args:
        func: The function to execute
        *args: Arguments to pass to the function
        max_retries: Maximum number of retry attempts
        delay_ms: Delay between retries in milliseconds
        fallback: Value to return if all retries fail
        log_error: Whether to log errors to the console
        module_name: Module name for logging
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The function result, or fallback on complete failure
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(delay_ms / 1000.0)

    if log_error and last_error:
        Py4GW.Console.Log(
            module_name,
            f"All {max_retries + 1} attempts failed for {func.__name__}: {str(last_error)}",
            Py4GW.Console.MessageType.Error
        )

    return fallback


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures.

    The circuit breaker tracks failures and "opens" (stops allowing calls)
    after a threshold is reached. After a timeout, it allows a test call
    through to see if the underlying issue is resolved.

    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

        @breaker
        def external_api_call():
            return api.fetch_data()

        # Or use directly:
        if breaker.is_closed:
            try:
                result = external_api_call()
                breaker.record_success()
            except Exception as e:
                breaker.record_failure()
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None
    ):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Seconds to wait before attempting recovery
            on_open: Callback when circuit opens
            on_close: Callback when circuit closes
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.on_open = on_open
        self.on_close = on_close

        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "closed"  # closed, open, half-open

    @property
    def is_closed(self) -> bool:
        """Check if the circuit is closed (allowing calls)."""
        if self._state == "closed":
            return True

        if self._state == "open":
            # Check if recovery timeout has passed
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = "half-open"
                return True

        return self._state == "half-open"

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == "half-open":
            self._state = "closed"
            self._failure_count = 0
            if self.on_close:
                self.on_close()

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            if self.on_open:
                self.on_open()

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._failure_count = 0
        self._state = "closed"

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Use as a decorator."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            if not self.is_closed:
                raise RuntimeError(f"Circuit breaker is open for {func.__name__}")

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise

        return wrapper
