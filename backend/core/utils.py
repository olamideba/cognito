import asyncio
import random
import logging
from functools import wraps
from typing import Callable, TypeVar, Any
from typing_extensions import ParamSpec

logger = logging.getLogger(__name__)

T = TypeVar("T")
P = ParamSpec("P")

def retry_with_backoff(
    retries: int = 3,
    backoff_in_seconds: float = 1.0,
    max_delay: float = 10.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """
    Decorator to retry an async function with exponential backoff and randomized jitter.
    
    Args:
        retries: Maximum number of retry attempts.
        backoff_in_seconds: Initial backoff delay in seconds.
        max_delay: Maximum delay in seconds between retries.
        exceptions: A tuple of exception classes that trigger a retry.
    """
    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            attempt = 0
            delay = backoff_in_seconds
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    attempt += 1
                    if attempt > retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after {attempt} attempts. Final exception: {exc}"
                        )
                        raise
                    
                    # Calculate exponential backoff with jitter
                    # Adding randomized jitter helps prevent "thundering herd" scenarios.
                    jitter = random.uniform(0, 0.5 * delay)
                    sleep_time = min(delay + jitter, max_delay)
                    
                    logger.warning(
                        f"Attempt {attempt} for '{func.__name__}' failed with {exc.__class__.__name__}: {exc}. "
                        f"Retrying in {sleep_time:.2f} seconds..."
                    )
                    await asyncio.sleep(sleep_time)
                    delay *= 2
        return wrapper
    return decorator
