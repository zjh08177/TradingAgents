"""Connection retry logic for handling OpenAI API connection failures."""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar, Union

import httpx
import httpcore

logger = logging.getLogger(__name__)

T = TypeVar('T')


def connection_retry(
    max_retries: int = 3, 
    backoff_seconds: float = 1.0,
    backoff_multiplier: float = 2.0
) -> Callable:
    """
    Decorator for retrying async functions that may fail due to connection errors.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_seconds: Initial backoff time in seconds (default: 1.0)
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Log attempt
                    if attempt > 0:
                        logger.warning(
                            f"⚠️ Connection retry {attempt}/{max_retries} for {func.__name__}"
                        )
                    
                    # Try to execute the function
                    result = await func(*args, **kwargs)
                    
                    # Success - log if it was a retry
                    if attempt > 0:
                        logger.info(
                            f"✅ Connection successful after {attempt} retries for {func.__name__}"
                        )
                    
                    return result
                    
                except (
                    httpx.RemoteProtocolError,
                    httpcore.RemoteProtocolError,
                    httpx.ReadTimeout,
                    httpx.ConnectTimeout,
                    httpx.NetworkError,
                    ConnectionError,
                    asyncio.TimeoutError
                ) as e:
                    last_exception = e
                    
                    # If this was the last attempt, raise the exception
                    if attempt == max_retries:
                        logger.error(
                            f"❌ Connection failed after {max_retries} retries for {func.__name__}: {e}"
                        )
                        raise
                    
                    # Calculate backoff time with exponential increase
                    wait_time = backoff_seconds * (backoff_multiplier ** attempt)
                    
                    logger.warning(
                        f"⚠️ Connection error in {func.__name__} (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        f"\n   Retrying in {wait_time:.1f}s..."
                    )
                    
                    # Wait before retrying
                    await asyncio.sleep(wait_time)
                    
                except Exception as e:
                    # For non-connection errors, don't retry
                    logger.error(
                        f"❌ Non-connection error in {func.__name__}: {type(e).__name__}: {e}"
                    )
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected error in retry logic for {func.__name__}")
            
        return wrapper
    return decorator


async def safe_llm_invoke(chain: Any, messages: list, **kwargs: Any) -> Any:
    """
    Safely invoke an LLM chain with connection retry logic.
    
    This is a convenience function that wraps the chain.ainvoke call
    with the connection retry decorator.
    
    Args:
        chain: The LLM chain to invoke
        messages: List of messages to send
        **kwargs: Additional keyword arguments for the chain
    
    Returns:
        The result from the LLM chain
    """
    @connection_retry(max_retries=3, backoff_seconds=1.0)
    async def _invoke():
        return await chain.ainvoke(messages, **kwargs)
    
    return await _invoke()


# Export commonly used functions
__all__ = ['connection_retry', 'safe_llm_invoke']