"""
Timeout decorator for enforcing execution time limits
Task C3: Implement Hard Timeout Wrapper
"""
import signal
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def timeout_decorator(seconds: int):
    """
    Decorator to enforce timeout on function execution
    
    Args:
        seconds: Maximum execution time in seconds
        
    Returns:
        Decorated function that will raise TimeoutError if execution exceeds limit
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            def timeout_handler(signum, frame):
                raise TimeoutError(f"⏰ Execution exceeded {seconds}s limit - TIMEOUT!")
            
            # Set up signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                logger.warning(f"⏱️ Starting execution with {seconds}s timeout for {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"✅ {func.__name__} completed within timeout")
                return result
            except TimeoutError as e:
                logger.error(f"🚨 TIMEOUT: {func.__name__} exceeded {seconds}s limit")
                raise
            finally:
                # Reset alarm
                signal.alarm(0)
                # Restore original handler
                signal.signal(signal.SIGALRM, old_handler)
                
        return wrapper
    return decorator

# Convenience decorators for common timeouts
def timeout_120s(func):
    """Hard timeout at 120 seconds for full execution"""
    return timeout_decorator(120)(func)

def timeout_30s(func):
    """30 second timeout for individual components"""
    return timeout_decorator(30)(func)

def timeout_20s(func):
    """20 second timeout for consolidation tasks"""
    return timeout_decorator(20)(func)

# Context manager version for more flexibility
class TimeoutContext:
    """Context manager for timeout enforcement"""
    
    def __init__(self, seconds: int, message: str = "Operation timed out"):
        self.seconds = seconds
        self.message = message
        self.old_handler = None
        
    def __enter__(self):
        def timeout_handler(signum, frame):
            raise TimeoutError(f"⏰ {self.message} - exceeded {self.seconds}s limit")
        
        self.old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.seconds)
        logger.warning(f"⏱️ Timeout context started: {self.seconds}s")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if self.old_handler:
            signal.signal(signal.SIGALRM, self.old_handler)
        
        if exc_type is TimeoutError:
            logger.error(f"🚨 TIMEOUT CONTEXT: {self.message}")
        return False  # Don't suppress exceptions