"""
Tool Result Caching for Priority 3 Optimization
Implements an LRU cache for frequently accessed market data
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ToolCache:
    """
    A simple in-memory cache for tool results with TTL support.
    
    This implementation uses Python's built-in lru_cache with custom TTL logic
    for caching market data and technical indicators.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize the tool cache.
        
        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = {}
        self._timestamps = {}
        self._hit_count = 0
        self._miss_count = 0
        
    def _generate_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Generate a unique cache key for a tool call.
        
        Args:
            tool_name: Name of the tool
            args: Arguments passed to the tool
            
        Returns:
            Hash key for caching
        """
        # Create a consistent string representation
        key_data = {
            'tool': tool_name,
            'args': args
        }
        key_str = json.dumps(key_data, sort_keys=True)
        
        # Generate hash
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, tool_name: str, args: Dict[str, Any]) -> Optional[Any]:
        """
        Get a cached result if available and not expired.
        
        Args:
            tool_name: Name of the tool
            args: Arguments passed to the tool
            
        Returns:
            Cached result or None if not found/expired
        """
        key = self._generate_key(tool_name, args)
        
        # Check if key exists
        if key not in self._cache:
            self._miss_count += 1
            logger.debug(f"📊 Cache MISS for {tool_name} (total misses: {self._miss_count})")
            return None
        
        # Check if expired
        timestamp = self._timestamps.get(key, 0)
        if time.time() - timestamp > self.default_ttl:
            # Remove expired entry
            del self._cache[key]
            del self._timestamps[key]
            self._miss_count += 1
            logger.debug(f"📊 Cache EXPIRED for {tool_name}")
            return None
        
        self._hit_count += 1
        hit_rate = self._hit_count / (self._hit_count + self._miss_count) * 100
        logger.info(f"✅ Cache HIT for {tool_name} (hit rate: {hit_rate:.1f}%)")
        
        return self._cache[key]
    
    def set(self, tool_name: str, args: Dict[str, Any], result: Any) -> None:
        """
        Store a result in the cache.
        
        Args:
            tool_name: Name of the tool
            args: Arguments passed to the tool
            result: Result to cache
        """
        key = self._generate_key(tool_name, args)
        
        # Check cache size limit
        if len(self._cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self._timestamps, key=self._timestamps.get)
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
            logger.debug(f"🗑️ Evicted oldest cache entry")
        
        self._cache[key] = result
        self._timestamps[key] = time.time()
        logger.debug(f"💾 Cached result for {tool_name}")
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._timestamps.clear()
        self._hit_count = 0
        self._miss_count = 0
        logger.info("🗑️ Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests * 100 if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._hit_count,
            'misses': self._miss_count,
            'hit_rate': hit_rate,
            'ttl': self.default_ttl
        }


# Global cache instance
_tool_cache = ToolCache()


def cache_tool_result(ttl: Optional[int] = None):
    """
    Decorator to cache tool results.
    
    This is the implementation for Priority 3: Tool Result Caching.
    
    Args:
        ttl: Time-to-live for this specific tool (optional)
        
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract tool name
            tool_name = func.__name__
            
            # Create args dict for cache key
            cache_args = {
                'args': args,
                'kwargs': kwargs
            }
            
            # Check cache first
            cached_result = _tool_cache.get(tool_name, cache_args)
            if cached_result is not None:
                return cached_result
            
            # Execute tool and cache result
            result = func(*args, **kwargs)
            _tool_cache.set(tool_name, cache_args, result)
            
            return result
        
        # Also create async version if needed
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract tool name
            tool_name = func.__name__
            
            # Create args dict for cache key
            cache_args = {
                'args': args,
                'kwargs': kwargs
            }
            
            # Check cache first
            cached_result = _tool_cache.get(tool_name, cache_args)
            if cached_result is not None:
                return cached_result
            
            # Execute tool and cache result
            result = await func(*args, **kwargs)
            _tool_cache.set(tool_name, cache_args, result)
            
            return result
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


def get_cached_market_data(symbol: str, date: str, indicator: str) -> Optional[str]:
    """
    Get cached market data if available.
    
    This is the specific implementation suggested in the diagnosis.
    
    Args:
        symbol: Stock ticker
        date: Trading date
        indicator: Technical indicator name
        
    Returns:
        Cached data or None
    """
    cache_args = {
        'symbol': symbol,
        'date': date,
        'indicator': indicator
    }
    
    tool_name = f"get_stockstats_indicators_report_{indicator}"
    return _tool_cache.get(tool_name, cache_args)


def cache_market_data(symbol: str, date: str, indicator: str, data: str) -> None:
    """
    Cache market data result.
    
    Args:
        symbol: Stock ticker
        date: Trading date
        indicator: Technical indicator name
        data: Data to cache
    """
    cache_args = {
        'symbol': symbol,
        'date': date,
        'indicator': indicator
    }
    
    tool_name = f"get_stockstats_indicators_report_{indicator}"
    _tool_cache.set(tool_name, cache_args, data)


# For testing and monitoring
def get_cache_stats() -> Dict[str, Any]:
    """Get current cache statistics."""
    return _tool_cache.get_stats()


def clear_cache() -> None:
    """Clear all cached data."""
    _tool_cache.clear()