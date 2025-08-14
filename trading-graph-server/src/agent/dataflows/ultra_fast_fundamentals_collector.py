"""
Ultra-Fast Fundamentals Collector
High-performance financial data fetcher with HTTP/2 connection pooling and batch optimization.

Phase 1 Implementation: Core Infrastructure
- HTTP/2 client setup with connection pooling
- Redis connection pool for caching
- Circuit breaker pattern for fault tolerance
- Rate limiting semaphore for API throttling
"""

import asyncio
import json
import time
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Optional imports for testing compatibility
try:
    import aioredis
    HAS_AIOREDIS = True
except Exception as e:
    # Catch all exceptions including TypeError from Python 3.11+ compatibility issues
    # aioredis has known issues with Python 3.11+ where asyncio.TimeoutError 
    # and builtins.TimeoutError are the same class, causing duplicate base class error
    HAS_AIOREDIS = False
    aioredis = None
    # Note: logger might not be initialized yet, so we'll log later if needed

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None

logger = logging.getLogger(__name__)


@dataclass
class CollectorConfig:
    """Configuration for the Ultra-Fast Fundamentals Collector."""
    max_connections: int = 20
    max_keepalive_connections: int = 10
    timeout_connect: float = 2.0
    timeout_total: float = 10.0
    max_concurrent_api_calls: int = 10
    circuit_breaker_failure_threshold: int = 5
    redis_min_connections: int = 5
    redis_max_connections: int = 10
    cache_ttl_days: int = 90


class UltraFastFundamentalsCollector:
    """
    Ultra-fast fundamentals collector with HTTP/2 connection pooling and batch support.
    
    Phase 1 Features:
    - HTTP/2 client with connection pooling
    - Redis connection pool for caching
    - Circuit breaker pattern for fault tolerance  
    - Rate limiting semaphore for API throttling
    - Parallel endpoint fetching (15 endpoints per ticker)
    - Batch processing with Redis pipelines
    """
    
    def __init__(self, finnhub_key: str, redis_url: str = "redis://localhost", config: CollectorConfig = None):
        self.api_key = finnhub_key
        self.base_url = "https://finnhub.io/api/v1"
        self.redis_url = redis_url
        self.config = config or CollectorConfig()
        
        # Connection pools - initialized in setup()
        self.redis = None
        self.client = None
        
        # Circuit breaker state
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_open_time = None
        
        # Rate limiting
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_api_calls)
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'api_errors': 0,
            'circuit_breaker_opens': 0
        }
        
        logger.info(f"🚀 UltraFastFundamentalsCollector initialized with config: {asdict(self.config)}")

    async def setup(self) -> None:
        """Initialize HTTP/2 client and Redis connection pools."""
        start_time = time.time()
        
        # Check dependencies
        if not HAS_HTTPX:
            logger.warning("⚠️ httpx not available - HTTP client will not be initialized")
            self.client = None
            return
            
        # Task 1.1: HTTP/2 Client Setup with connection pooling
        # Try to use HTTP/2 if h2 is available, fallback to HTTP/1.1
        try:
            self.client = httpx.AsyncClient(
                http2=True,  # Enable HTTP/2 multiplexing for connection reuse
                limits=httpx.Limits(
                    max_connections=self.config.max_connections,
                    max_keepalive_connections=self.config.max_keepalive_connections
                ),
                timeout=httpx.Timeout(
                    connect=self.config.timeout_connect,
                    timeout=self.config.timeout_total
                ),
                headers={
                    'User-Agent': 'TradingAgents-UltraFast-Collector/1.0'
                }
            )
            logger.info("✅ HTTP/2 client initialized")
        except Exception as e:  # Catch all exceptions, not just ImportError
            logger.warning(f"⚠️ HTTP/2 not available ({e}), falling back to HTTP/1.1")
            self.client = httpx.AsyncClient(
                http2=False,  # Use HTTP/1.1
                limits=httpx.Limits(
                    max_connections=self.config.max_connections,
                    max_keepalive_connections=self.config.max_keepalive_connections
                ),
                timeout=httpx.Timeout(
                    connect=self.config.timeout_connect,
                    timeout=self.config.timeout_total
                ),
                headers={
                    'User-Agent': 'TradingAgents-UltraFast-Collector/1.0'
                }
            )
        
        # Task 1.2: Redis Connection Pool
        if not HAS_AIOREDIS:
            logger.warning("⚠️ aioredis not available - Redis caching will be disabled")
            self.redis = None
        else:
            try:
                self.redis = await aioredis.create_redis_pool(
                self.redis_url,
                minsize=self.config.redis_min_connections,
                maxsize=self.config.redis_max_connections,
                encoding='utf-8'
                )
                logger.info("✅ Redis connection pool established")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                # Continue without Redis - will fetch directly from API
                self.redis = None
        
        setup_time = time.time() - start_time
        logger.info(f"⚡ UltraFastFundamentalsCollector setup completed in {setup_time:.3f}s")
        
    async def close(self) -> None:
        """Cleanup connections and resources."""
        logger.info("🔄 Closing UltraFastFundamentalsCollector connections...")
        
        if self.client:
            await self.client.aclose()
            logger.info("✅ HTTP client closed")
            
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("✅ Redis connection pool closed")
            
        # Log final statistics
        logger.info(f"📊 Final stats: {self.stats}")

    def _is_circuit_breaker_open(self) -> bool:
        """Task 1.3: Circuit breaker pattern implementation."""
        if not self.circuit_open:
            return False
            
        # Auto-recovery after 60 seconds
        if self.circuit_open_time and (time.time() - self.circuit_open_time) > 60:
            self.circuit_open = False
            self.failure_count = 0
            logger.info("✅ Circuit breaker auto-recovered")
            return False
            
        return True

    def _record_failure(self) -> None:
        """Record API failure and potentially open circuit breaker."""
        self.failure_count += 1
        self.stats['api_errors'] += 1
        
        if self.failure_count >= self.config.circuit_breaker_failure_threshold:
            self.circuit_open = True
            self.circuit_open_time = time.time()
            self.stats['circuit_breaker_opens'] += 1
            logger.warning(f"🚨 Circuit breaker opened after {self.failure_count} failures")

    def _record_success(self) -> None:
        """Record successful API call and reset circuit breaker."""
        self.failure_count = 0
        if self.circuit_open:
            self.circuit_open = False
            logger.info("✅ Circuit breaker reset after successful call")

    async def get(self, ticker: str) -> Dict[str, Any]:
        """
        Get single ticker data with connection pooling and caching.
        
        Returns structured fundamental data for the specified ticker.
        """
        self.stats['total_requests'] += 1
        start_time = time.time()
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            logger.warning(f"⚠️ Circuit breaker open - rejecting request for {ticker}")
            return {
                "error": "Circuit breaker open - service temporarily unavailable",
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
        
        # Check cache first if Redis is available
        cache_key = f"fund:{ticker}:{date.today()}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    self.stats['cache_hits'] += 1
                    data = json.loads(cached)
                    logger.debug(f"💾 Cache hit for {ticker} ({time.time() - start_time:.3f}s)")
                    return data
            except Exception as e:
                logger.warning(f"⚠️ Cache read error for {ticker}: {e}")
        
        # Cache miss - fetch from API
        self.stats['cache_misses'] += 1
        data = await self._fetch_ticker(ticker)
        
        # Cache successful results
        if self.redis and "error" not in data:
            try:
                cache_ttl = self.config.cache_ttl_days * 86400  # Convert days to seconds
                await self.redis.setex(cache_key, cache_ttl, json.dumps(data))
                logger.debug(f"💾 Cached data for {ticker} (TTL: {self.config.cache_ttl_days} days)")
            except Exception as e:
                logger.warning(f"⚠️ Cache write error for {ticker}: {e}")
        
        fetch_time = time.time() - start_time
        logger.info(f"📈 Fetched {ticker} in {fetch_time:.3f}s (cached: {'no' if self.stats['cache_misses'] > 0 else 'yes'})")
        
        return data

    async def get_batch(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Ultra-fast batch processing for multiple tickers with Redis pipelines.
        
        Optimizations:
        - Pipeline Redis operations for batch cache checks
        - Parallel API fetching for cache misses
        - Pipeline cache writes for new data
        """
        if not tickers:
            return {}
            
        self.stats['total_requests'] += len(tickers)
        start_time = time.time()
        
        logger.info(f"🔄 Processing batch of {len(tickers)} tickers...")
        
        # Phase 1: Batch cache check using Redis pipeline
        results = {}
        to_fetch = []
        
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                cache_keys = [f"fund:{ticker}:{date.today()}" for ticker in tickers]
                
                for key in cache_keys:
                    pipe.get(key)
                    
                cached_results = await pipe.execute()
                
                for ticker, cached in zip(tickers, cached_results):
                    if cached:
                        results[ticker] = json.loads(cached)
                        self.stats['cache_hits'] += 1
                    else:
                        to_fetch.append(ticker)
                        self.stats['cache_misses'] += 1
                        
                logger.info(f"💾 Cache: {len(results)} hits, {len(to_fetch)} misses")
                
            except Exception as e:
                logger.warning(f"⚠️ Batch cache read error: {e}")
                to_fetch = tickers  # Fallback to fetch all
        else:
            to_fetch = tickers  # No Redis - fetch all from API
        
        # Phase 2: Parallel fetch for cache misses
        if to_fetch:
            logger.info(f"🚀 Fetching {len(to_fetch)} tickers from API...")
            
            fetch_tasks = [self._fetch_ticker(ticker) for ticker in to_fetch]
            fresh_data = await asyncio.gather(*fetch_tasks, return_exceptions=True)
            
            # Phase 3: Process results and batch cache writes
            cache_writes = []
            if self.redis:
                pipe = self.redis.pipeline()
                cache_ttl = self.config.cache_ttl_days * 86400
                
            for ticker, data in zip(to_fetch, fresh_data):
                if not isinstance(data, Exception) and "error" not in data:
                    results[ticker] = data
                    
                    # Queue cache write
                    if self.redis:
                        cache_key = f"fund:{ticker}:{date.today()}"
                        pipe.setex(cache_key, cache_ttl, json.dumps(data))
                else:
                    # Handle API errors
                    if isinstance(data, Exception):
                        error_msg = str(data)
                    elif data is None:
                        error_msg = "No data returned from API"
                    elif isinstance(data, dict):
                        error_msg = data.get("error", "Unknown error")
                    else:
                        error_msg = f"Unexpected data type: {type(data)}"
                        
                    error_data = {
                        "error": error_msg,
                        "ticker": ticker,
                        "timestamp": datetime.now().isoformat()
                    }
                    results[ticker] = error_data
                    
            # Execute batch cache writes
            if self.redis and cache_writes:
                try:
                    await pipe.execute()
                    logger.debug(f"💾 Batch cached {len([r for r in results.values() if 'error' not in r])} successful results")
                except Exception as e:
                    logger.warning(f"⚠️ Batch cache write error: {e}")
        
        batch_time = time.time() - start_time
        successful_count = len([r for r in results.values() if "error" not in r])
        logger.info(f"✅ Batch completed: {successful_count}/{len(tickers)} successful in {batch_time:.3f}s")
        
        return results

    async def _fetch_ticker(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch single ticker with rate limiting and parallel endpoint calls.
        
        Task 1.4: Rate limiting semaphore ensures max concurrent API calls.
        """
        # Ensure client is initialized
        if self.client is None:
            logger.info("🔧 Client not initialized, calling setup()...")
            await self.setup()
            
        # Check if setup failed
        if self.client is None:
            raise Exception("HTTP client failed to initialize - check httpx installation")
        
        # Task 1.4: Rate limiting - acquire semaphore
        async with self.semaphore:
            try:
                logger.debug(f"🔍 Fetching {ticker} from API...")
                
                # Build all 15 endpoint URLs
                endpoints = self._build_endpoints(ticker)
                
                # Parallel fetch all endpoints with HTTP/2 multiplexing
                fetch_start = time.time()
                responses = await asyncio.gather(
                    *[self.client.get(url) for url in endpoints],
                    return_exceptions=True
                )
                fetch_time = time.time() - fetch_start
                
                # Process responses into structured data
                data = await self._process_responses(responses, ticker)
                data['fetch_time'] = fetch_time
                data['timestamp'] = datetime.now().isoformat()
                
                self._record_success()
                logger.debug(f"✅ API fetch for {ticker} completed in {fetch_time:.3f}s")
                
                return data
                
            except Exception as e:
                import traceback
                logger.error(f"❌ API fetch failed for {ticker}: {e}")
                logger.error(f"📍 Full traceback: {traceback.format_exc()}")
                self._record_failure()
                return {
                    "error": str(e),
                    "ticker": ticker,
                    "timestamp": datetime.now().isoformat(),
                    "traceback": traceback.format_exc()
                }

    def _build_endpoints(self, ticker: str) -> List[str]:
        """
        Build all 15 Finnhub endpoint URLs for comprehensive fundamental data.
        
        Covers all fundamental data categories:
        - Core financials (5 endpoints)
        - Earnings data (3 endpoints) 
        - Analyst data (2 endpoints)
        - Ownership data (2 endpoints)
        - Corporate actions (3 endpoints)
        """
        return [
            # Core financials (5 endpoints)
            f"{self.base_url}/stock/profile2?symbol={ticker}&token={self.api_key}",
            f"{self.base_url}/stock/metric?symbol={ticker}&metric=all&token={self.api_key}",
            f"{self.base_url}/stock/financials?symbol={ticker}&statement=bs&freq=quarterly&token={self.api_key}",
            f"{self.base_url}/stock/financials?symbol={ticker}&statement=ic&freq=quarterly&token={self.api_key}",
            f"{self.base_url}/stock/financials?symbol={ticker}&statement=cf&freq=quarterly&token={self.api_key}",
            
            # Earnings data (3 endpoints)
            f"{self.base_url}/stock/earnings?symbol={ticker}&limit=20&token={self.api_key}",
            f"{self.base_url}/stock/earnings-calendar?symbol={ticker}&token={self.api_key}",
            f"{self.base_url}/stock/revenue-estimate?symbol={ticker}&token={self.api_key}",
            
            # Analyst data (2 endpoints)
            f"{self.base_url}/stock/recommendation?symbol={ticker}&token={self.api_key}",
            f"{self.base_url}/stock/price-target?symbol={ticker}&token={self.api_key}",
            
            # Ownership data (2 endpoints)
            f"{self.base_url}/stock/insider-transactions?symbol={ticker}&token={self.api_key}",
            f"{self.base_url}/stock/ownership?symbol={ticker}&limit=20&token={self.api_key}",
            
            # Corporate actions (3 endpoints)
            f"{self.base_url}/stock/dividend?symbol={ticker}&token={self.api_key}",
            f"{self.base_url}/stock/split?symbol={ticker}&token={self.api_key}",
            f"{self.base_url}/stock/peers?symbol={ticker}&token={self.api_key}",
        ]

    async def _process_responses(self, responses: List, ticker: str) -> Dict[str, Any]:
        """
        Process API responses into structured fundamental data.
        
        Handles partial failures gracefully - returns empty dict for failed endpoints.
        """
        def safe_json(response):
            """Safely extract JSON from response, return empty dict on error."""
            try:
                if isinstance(response, Exception):
                    return {}
                return response.json()
            except Exception:
                return {}
        
        # Map responses to structured data categories
        processed_data = {
            "ticker": ticker,
            "profile": safe_json(responses[0]),
            "metrics": safe_json(responses[1]),
            "balance_sheet": safe_json(responses[2]),
            "income_statement": safe_json(responses[3]),
            "cash_flow": safe_json(responses[4]),
            "earnings_history": safe_json(responses[5]),
            "earnings_calendar": safe_json(responses[6]),
            "revenue_estimates": safe_json(responses[7]),
            "recommendations": safe_json(responses[8]),
            "price_targets": safe_json(responses[9]),
            "insider_transactions": safe_json(responses[10]),
            "institutional_ownership": safe_json(responses[11]),
            "dividends": safe_json(responses[12]),
            "splits": safe_json(responses[13]),
            "peers": safe_json(responses[14]),
        }
        
        # 🔍 ENHANCED LOGGING: Debug price targets response structure
        price_targets_raw = processed_data["price_targets"]
        logger.info(f"🎯 PRICE_TARGETS RAW RESPONSE for {ticker}:")
        logger.info(f"📊 Type: {type(price_targets_raw)}")
        logger.info(f"📊 Content: {price_targets_raw}")
        if isinstance(price_targets_raw, list) and len(price_targets_raw) > 0:
            logger.info(f"📊 First item: {price_targets_raw[0]}")
            logger.info(f"📊 First item keys: {price_targets_raw[0].keys() if isinstance(price_targets_raw[0], dict) else 'Not a dict'}")
        elif isinstance(price_targets_raw, dict):
            logger.info(f"📊 Dictionary keys: {list(price_targets_raw.keys())}")
        
        # 🔍 ENHANCED LOGGING: Debug recommendations response structure  
        recommendations_raw = processed_data["recommendations"]
        logger.info(f"🏆 RECOMMENDATIONS RAW RESPONSE for {ticker}:")
        logger.info(f"📊 Type: {type(recommendations_raw)}")
        if isinstance(recommendations_raw, list) and len(recommendations_raw) > 0:
            logger.info(f"📊 First recommendation: {recommendations_raw[0]}")
            logger.info(f"📊 First rec keys: {recommendations_raw[0].keys() if isinstance(recommendations_raw[0], dict) else 'Not a dict'}")
        elif isinstance(recommendations_raw, dict):
            logger.info(f"📊 Rec dictionary keys: {list(recommendations_raw.keys())}")
        
        # 🎯 ENHANCED PRICE TARGETS: Apply multi-source fallback if Finnhub returns empty data
        if (isinstance(price_targets_raw, dict) and 
            price_targets_raw.get("numberOfAnalysts", 0) == 0 and 
            price_targets_raw.get("targetMean", 0) == 0):
            
            logger.warning(f"🚨 Finnhub price targets empty for {ticker} - applying enhanced fallback")
            # Fixed: Now both methods are async
            processed_data = await self._apply_enhanced_price_targets(processed_data, ticker)
        
        # Count successful vs failed endpoints
        successful_endpoints = sum(1 for v in processed_data.values() 
                                 if isinstance(v, dict) and v and v != {} and "ticker" not in str(v))
        processed_data["endpoints_fetched"] = successful_endpoints
        processed_data["endpoints_total"] = 15
        
        return processed_data

    async def _apply_enhanced_price_targets(self, processed_data: Dict[str, Any], ticker: str) -> Dict[str, Any]:
        """Apply enhanced price target logic when Finnhub returns empty data"""
        try:
            from .enhanced_price_target_collector import EnhancedPriceTargetCollector
            
            # Initialize enhanced collector
            enhanced_collector = EnhancedPriceTargetCollector(self.api_key)
            await enhanced_collector.setup()
            
            # Get enhanced price targets
            enhanced_targets = await enhanced_collector.get_price_targets(ticker)
            
            # Update processed_data with enhanced targets
            processed_data["price_targets"] = {
                "lastPrice": enhanced_targets.current_price,
                "targetMean": enhanced_targets.target_mean,
                "targetHigh": enhanced_targets.target_high,
                "targetLow": enhanced_targets.target_low,
                "numberOfAnalysts": enhanced_targets.analyst_count,
                "confidence": enhanced_targets.confidence_level,
                "source": enhanced_targets.data_source,
                "lastUpdated": enhanced_targets.last_updated
            }
            
            logger.info(f"✅ ENHANCED PRICE TARGETS applied for {ticker}: "
                       f"Mean=${enhanced_targets.target_mean:.2f}, "
                       f"Analysts={enhanced_targets.analyst_count}, "
                       f"Source={enhanced_targets.data_source}, "
                       f"Confidence={enhanced_targets.confidence_level}")
            
            # Clean up
            await enhanced_collector.client.aclose()
            
        except Exception as e:
            logger.error(f"❌ Enhanced price targets failed for {ticker}: {e}")
            # Keep original empty data but add source indication
            if "price_targets" in processed_data:
                processed_data["price_targets"]["source"] = "Finnhub Free Tier (Limited)"
                processed_data["price_targets"]["confidence"] = "LIMITED"
        
        return processed_data

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring and debugging."""
        cache_hit_rate = (self.stats['cache_hits'] / max(self.stats['total_requests'], 1)) * 100
        
        return {
            **self.stats,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'circuit_breaker_open': self.circuit_open,
            'failure_count': self.failure_count,
            'config': asdict(self.config)
        }


# Graph node integration function
async def create_ultra_fast_fundamentals_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimized graph node integration for ultra-fast fundamentals collection.
    
    Uses singleton pattern with connection pooling for maximum performance.
    """
    ticker = state.get("company_of_interest")
    if not ticker:
        return {"fundamentals_data": {"error": "No ticker specified"}}
    
    # Initialize collector if needed (singleton pattern)
    if not hasattr(state, "_fundamentals_collector"):
        finnhub_key = state.get("finnhub_key") or "your_api_key_here"
        collector = UltraFastFundamentalsCollector(finnhub_key=finnhub_key)
        await collector.setup()
        state["_fundamentals_collector"] = collector
        
    # Fetch data using optimized collector
    try:
        data = await state["_fundamentals_collector"].get(ticker)
        return {"fundamentals_data": data}
    except Exception as e:
        logger.error(f"❌ Fundamentals collection failed for {ticker}: {e}")
        return {
            "fundamentals_data": {
                "error": str(e),
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
        }


# Cleanup function for graceful shutdown
async def cleanup_fundamentals_collector(state: Dict[str, Any]) -> None:
    """Cleanup function for graceful shutdown of collector resources."""
    if hasattr(state, "_fundamentals_collector"):
        await state["_fundamentals_collector"].close()
        delattr(state, "_fundamentals_collector")
        logger.info("✅ UltraFastFundamentalsCollector cleaned up")