"""
Connection Pooling for Priority 3 Optimization
Implements HTTP connection pooling for improved performance
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Manages a pool of HTTP connections for efficient API calls.
    
    This is the implementation for Priority 3: Add Connection Pooling.
    Uses aiohttp's TCPConnector for connection pooling.
    """
    
    _instance: Optional['ConnectionPool'] = None
    _session: Optional[aiohttp.ClientSession] = None
    _connector: Optional[aiohttp.TCPConnector] = None
    
    def __new__(cls):
        """Singleton pattern to ensure one pool instance."""
        if cls._instance is None:
            cls._instance = super(ConnectionPool, cls).__new__(cls)
        return cls._instance
    
    async def initialize(
        self,
        limit: int = 100,
        limit_per_host: int = 30,
        ttl_dns_cache: int = 300,
        force_close: bool = False
    ):
        """
        Initialize the connection pool.
        
        Args:
            limit: Total connection pool limit
            limit_per_host: Limit per host
            ttl_dns_cache: DNS cache TTL in seconds
            force_close: Force close existing connections
        """
        if self._session and not force_close:
            logger.info("🔌 Connection pool already initialized")
            return
        
        # Close existing session if needed
        if self._session:
            await self.close()
        
        # Create new connector with pooling
        self._connector = aiohttp.TCPConnector(
            limit=limit,
            limit_per_host=limit_per_host,
            ttl_dns_cache=ttl_dns_cache,
            force_close=True,
            enable_cleanup_closed=True
        )
        
        # Create session with connector
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers={
                'User-Agent': 'TradingGraphServer/1.0'
            }
        )
        
        logger.info(
            f"🔌 Connection pool initialized: "
            f"limit={limit}, limit_per_host={limit_per_host}"
        )
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the current session."""
        if not self._session:
            raise RuntimeError("Connection pool not initialized. Call initialize() first.")
        return self._session
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Perform GET request using the connection pool.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for aiohttp
            
        Returns:
            Response object
        """
        async with self.session.get(url, **kwargs) as response:
            return response
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Perform POST request using the connection pool.
        
        Args:
            url: URL to post to
            **kwargs: Additional arguments for aiohttp
            
        Returns:
            Response object
        """
        async with self.session.post(url, **kwargs) as response:
            return response
    
    async def close(self):
        """Close the connection pool and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
            self._connector = None
            logger.info("🔌 Connection pool closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        if not self._connector:
            return {'status': 'not_initialized'}
        
        return {
            'status': 'active',
            'limit': self._connector.limit,
            'limit_per_host': self._connector.limit_per_host,
            'connections': len(self._connector._conns),
        }


# Global connection pool instance
_connection_pool = ConnectionPool()


async def get_connection_pool() -> ConnectionPool:
    """
    Get the global connection pool instance.
    
    Initializes the pool if not already done.
    """
    if not _connection_pool._session:
        await _connection_pool.initialize()
    return _connection_pool


@asynccontextmanager
async def pooled_request(method: str, url: str, **kwargs):
    """
    Context manager for making pooled HTTP requests.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        **kwargs: Additional arguments for the request
        
    Yields:
        Response object
    """
    pool = await get_connection_pool()
    
    async with pool.session.request(method, url, **kwargs) as response:
        yield response


class ToolkitWithPool:
    """
    Example toolkit implementation with connection pooling.
    
    This matches the interface suggested in the diagnosis document.
    """
    
    def __init__(self):
        """Initialize toolkit with connection pool."""
        self._pool_initialized = False
    
    async def _ensure_pool(self):
        """Ensure connection pool is initialized."""
        if not self._pool_initialized:
            pool = await get_connection_pool()
            self._pool_initialized = True
    
    async def fetch_data(self, url: str) -> str:
        """
        Fetch data using the connection pool.
        
        Args:
            url: URL to fetch
            
        Returns:
            Response text
        """
        await self._ensure_pool()
        
        async with pooled_request('GET', url) as response:
            return await response.text()
    
    async def post_data(self, url: str, data: Dict[str, Any]) -> str:
        """
        Post data using the connection pool.
        
        Args:
            url: URL to post to
            data: Data to post
            
        Returns:
            Response text
        """
        await self._ensure_pool()
        
        async with pooled_request('POST', url, json=data) as response:
            return await response.text()


# Cleanup function for graceful shutdown
async def cleanup_connection_pool():
    """Clean up the global connection pool."""
    await _connection_pool.close()


# Statistics function for monitoring
def get_pool_stats() -> Dict[str, Any]:
    """Get connection pool statistics."""
    return _connection_pool.get_stats()