"""Circuit breaker pattern for preventing cascading failures."""

import asyncio
import time
import logging
from enum import Enum
from typing import Any, Callable, TypeVar, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Failing, reject all calls
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 60,
        success_threshold: int = 1,
        name: Optional[str] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            success_threshold: Successes needed in half-open to close circuit
            name: Optional name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.name = name or "CircuitBreaker"
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change = time.time()
        
    def _log_state_change(self, old_state: CircuitState, new_state: CircuitState):
        """Log state transitions."""
        if old_state != new_state:
            logger.warning(
                f"🔌 {self.name}: Circuit breaker state changed: "
                f"{old_state.value} → {new_state.value}"
            )
            self.last_state_change = time.time()
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset from OPEN to HALF_OPEN."""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _record_success(self):
        """Record a successful call."""
        old_state = self.state
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"✅ {self.name}: Circuit recovered and closed")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success in closed state
            self.failure_count = 0
            
        self._log_state_change(old_state, self.state)
    
    def _record_failure(self):
        """Record a failed call."""
        old_state = self.state
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"❌ {self.name}: Circuit opened after {self.failure_count} failures"
                )
        elif self.state == CircuitState.HALF_OPEN:
            # Single failure in half-open returns to open
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning(f"⚠️ {self.name}: Circuit reopened after half-open failure")
            
        self._log_state_change(old_state, self.state)
    
    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Async function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            Exception: If circuit is open or func fails
        """
        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                old_state = self.state
                self.state = CircuitState.HALF_OPEN
                self._log_state_change(old_state, self.state)
                logger.info(f"🔄 {self.name}: Testing circuit in half-open state")
            else:
                time_left = self.recovery_timeout - (time.time() - self.last_failure_time)
                raise Exception(
                    f"Circuit breaker is OPEN. Retry in {time_left:.1f}s"
                )
        
        # Try to execute the function
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def get_state(self) -> dict:
        """Get current circuit breaker state info."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": (
                datetime.fromtimestamp(self.last_failure_time).isoformat()
                if self.last_failure_time else None
            ),
            "uptime": time.time() - self.last_state_change
        }
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        logger.info(f"🔧 {self.name}: Manual circuit reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


# Global circuit breakers for different services
_circuit_breakers = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 3,
    recovery_timeout: int = 60
) -> CircuitBreaker:
    """
    Get or create a named circuit breaker.
    
    Args:
        name: Circuit breaker name (e.g., "openai_api", "market_data")
        failure_threshold: Failures before opening
        recovery_timeout: Recovery timeout in seconds
        
    Returns:
        Circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            name=name
        )
    return _circuit_breakers[name]


async def with_circuit_breaker(
    func: Callable[..., T],
    breaker_name: str,
    *args: Any,
    **kwargs: Any
) -> T:
    """
    Execute function with circuit breaker protection.
    
    Args:
        func: Async function to protect
        breaker_name: Name of circuit breaker to use
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    breaker = get_circuit_breaker(breaker_name)
    return await breaker.call(func, *args, **kwargs)


# Export commonly used functions
__all__ = [
    'CircuitBreaker',
    'CircuitState',
    'get_circuit_breaker',
    'with_circuit_breaker'
]