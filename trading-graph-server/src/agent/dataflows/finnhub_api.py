"""
Task 1.3: Finnhub API Integration with Resilience Patterns
Following SOLID principles and detailed atomic tasks from day1_detailed_plan.md
"""

import anyio
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Callable, Any, Dict, Tuple
from enum import Enum
import finnhub
import os
import json
from .news_interfaces import NewsArticle, SerperResponse, NewsGatheringError

logger = logging.getLogger(__name__)


# Task 1.3.1: Implement Retry Logic (15 min)
class RetryHandler:
    """Single Responsibility: Handle API retries with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = logging.getLogger(f"{__name__}.RetryHandler")
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Attempt {attempt + 1}/{self.max_retries}")
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s"
                    )
                    await anyio.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed")
        
        raise NewsGatheringError(
            error_type=NewsGatheringError.API_ERROR,
            message=f"Failed after {self.max_retries} retries: {last_error}",
            fallback_attempted=False,
            partial_results=None
        )


# Task 1.3.3: Implement Circuit Breaker (15 min)
class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"    # Normal operation
    OPEN = "open"        # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Single Responsibility: Prevent cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info("Circuit breaker entering half-open state")
            else:
                raise NewsGatheringError(
                    error_type=NewsGatheringError.API_ERROR,
                    message="Circuit breaker is open - service unavailable",
                    fallback_attempted=False,
                    partial_results=None
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.reset_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.logger.info("Circuit breaker closing after successful test")
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        """Increment failure count and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


# Task 1.3.2: Implement Finnhub Fallback (15 min)
class FallbackHandler:
    """Single Responsibility: Handle fallback to cached data"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or "./data/finnhub_cache"
        self.logger = logging.getLogger(f"{__name__}.FallbackHandler")
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Callable,
        cache_key: str,
        *args, **kwargs
    ) -> Tuple[Any, str]:
        """Execute primary with fallback on failure"""
        try:
            result = await primary_func(*args, **kwargs)
            
            # Cache successful result
            await self._cache_result(cache_key, result)
            
            if self._is_sufficient(result):
                return result, "primary"
            else:
                self.logger.warning("Primary returned insufficient results, trying fallback")
                fallback_result = await fallback_func(cache_key)
                return self._merge_results(result, fallback_result), "partial_fallback"
                
        except Exception as e:
            self.logger.error(f"Primary failed: {e}, attempting fallback")
            try:
                fallback_result = await fallback_func(cache_key)
                return fallback_result, "complete_fallback"
            except Exception as fallback_error:
                self.logger.error(f"Fallback also failed: {fallback_error}")
                raise NewsGatheringError(
                    error_type=NewsGatheringError.API_ERROR,
                    message=f"Both primary and fallback failed: {e}",
                    fallback_attempted=True,
                    partial_results=None
                )
    
    def _is_sufficient(self, result: Any) -> bool:
        """Check if result has sufficient data"""
        if isinstance(result, list):
            return len(result) >= 5  # Minimum 5 articles
        return bool(result)
    
    def _merge_results(self, primary: Any, fallback: Any) -> Any:
        """Merge primary and fallback results"""
        if isinstance(primary, list) and isinstance(fallback, list):
            # If items are NewsArticle objects, deduplicate by URL
            if primary and hasattr(primary[0], 'url'):
                # Combine and deduplicate by URL
                seen_urls = set()
                merged = []
                for article in primary + fallback:
                    if hasattr(article, 'url') and article.url not in seen_urls:
                        seen_urls.add(article.url)
                        merged.append(article)
                return merged
            else:
                # For non-article lists, simple concatenation
                return primary + fallback
        return primary or fallback
    
    async def _cache_result(self, cache_key: str, result: Any):
        """Cache successful result to disk"""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            # Convert to serializable format
            if isinstance(result, list) and all(isinstance(item, NewsArticle) for item in result):
                serializable = [
                    {
                        'title': article.title,
                        'source': article.source,
                        'snippet': article.snippet,
                        'url': article.url,
                        'date': article.date.isoformat(),
                        'authority_tier': article.authority_tier
                    }
                    for article in result
                ]
            else:
                serializable = result
            
            with open(cache_path, 'w') as f:
                json.dump({
                    'data': serializable,
                    'cached_at': datetime.now().isoformat()
                }, f)
            self.logger.debug(f"Cached result to {cache_path}")
        except Exception as e:
            self.logger.warning(f"Failed to cache result: {e}")
    
    async def load_from_cache(self, cache_key: str) -> List[NewsArticle]:
        """Load cached data"""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_path):
            raise FileNotFoundError(f"No cache found for {cache_key}")
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check cache age (24 hours max)
            cached_time = datetime.fromisoformat(cache_data['cached_at'])
            if datetime.now() - cached_time > timedelta(hours=24):
                self.logger.warning(f"Cache for {cache_key} is older than 24 hours")
            
            # Convert back to NewsArticle objects
            articles = []
            for item in cache_data['data']:
                articles.append(NewsArticle(
                    title=item['title'],
                    source=item['source'],
                    snippet=item['snippet'],
                    url=item['url'],
                    date=datetime.fromisoformat(item['date']),
                    authority_tier=item['authority_tier']
                ))
            
            self.logger.info(f"Loaded {len(articles)} articles from cache")
            return articles
            
        except Exception as e:
            self.logger.error(f"Failed to load cache: {e}")
            raise


# Main Finnhub API Client
class FinnhubAPIClient:
    """Single Responsibility: Interface with Finnhub API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("Finnhub API key is required")
        
        self.client = finnhub.Client(api_key=self.api_key)
        self.logger = logging.getLogger(f"{__name__}.FinnhubAPIClient")
        
        # Initialize resilience components
        self.retry_handler = RetryHandler(max_retries=3, base_delay=1.0)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60)
        self.fallback_handler = FallbackHandler()
    
    async def fetch_company_news(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> List[NewsArticle]:
        """
        Fetch company news from Finnhub API with resilience patterns
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'ETH')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            List of NewsArticle objects
        """
        cache_key = f"{ticker}_{start_date}_{end_date}_news"
        
        async def fetch_from_api():
            """Inner function to fetch from API"""
            return await self._make_api_call(ticker, start_date, end_date)
        
        async def fetch_from_cache():
            """Inner function to fetch from cache"""
            return await self.fallback_handler.load_from_cache(cache_key)
        
        # Execute with all resilience patterns
        try:
            # Try with circuit breaker
            async def fetch_with_retry():
                return await self.retry_handler.execute_with_retry(
                    fetch_from_api
                )
            
            result, source = await self.fallback_handler.execute_with_fallback(
                lambda: self.circuit_breaker.call(fetch_with_retry),
                lambda key: fetch_from_cache(),
                cache_key
            )
            
            self.logger.info(
                f"Fetched {len(result)} articles for {ticker} from {source}"
            )
            return result
            
        except NewsGatheringError:
            raise
        except Exception as e:
            raise NewsGatheringError(
                error_type=NewsGatheringError.API_ERROR,
                message=f"Failed to fetch news for {ticker}: {e}",
                fallback_attempted=True,
                partial_results=None
            )
    
    async def _make_api_call(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> List[NewsArticle]:
        """Make actual API call to Finnhub"""
        try:
            # Run synchronous API call in executor using anyio for cross-platform support
            # For crypto tickers, use crypto news endpoint
            if ticker in ['BTC', 'ETH', 'DOGE', 'ADA', 'SOL']:
                # Finnhub crypto news endpoint
                news_data = await anyio.to_thread.run_sync(
                    self.client.general_news,
                    'crypto',  # category
                    None  # min_id
                )
                # Filter by ticker mention
                news_data = [
                    item for item in news_data
                    if ticker.lower() in item.get('headline', '').lower() or
                       ticker.lower() in item.get('summary', '').lower()
                ]
            else:
                # Regular company news endpoint
                news_data = await anyio.to_thread.run_sync(
                    self.client.company_news,
                    ticker,
                    start_date,
                    end_date
                )
            
            # Convert to NewsArticle objects
            articles = []
            for item in news_data:
                try:
                    article = NewsArticle(
                        title=item.get('headline', ''),
                        source=item.get('source', 'Finnhub'),
                        snippet=item.get('summary', ''),
                        url=item.get('url', ''),
                        date=datetime.fromtimestamp(item.get('datetime', time.time())),
                        authority_tier=self._classify_source_authority(item.get('source', ''))
                    )
                    
                    if article.validate():
                        articles.append(article)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse article: {e}")
                    continue
            
            self.logger.info(f"API returned {len(articles)} valid articles")
            return articles
            
        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            raise
    
    def _classify_source_authority(self, source: str) -> int:
        """Classify news source by authority tier"""
        if not source:
            return 3
        
        source_lower = source.lower()
        
        # Tier 1: Most authoritative sources
        tier1_sources = [
            'reuters', 'bloomberg', 'wall street journal', 'wsj',
            'financial times', 'ft.com', 'associated press', 'ap news'
        ]
        
        # Tier 2: Reputable financial sources
        tier2_sources = [
            'cnbc', 'marketwatch', 'yahoo finance', 'forbes',
            'business insider', 'barrons', 'the economist', 'fortune',
            'seeking alpha', 'benzinga'
        ]
        
        # Check tier 1
        for t1_source in tier1_sources:
            if t1_source in source_lower:
                return 1
        
        # Check tier 2
        for t2_source in tier2_sources:
            if t2_source in source_lower:
                return 2
        
        # Default to tier 3
        return 3


# Convenience function for backwards compatibility
async def fetch_finnhub_news(
    ticker: str,
    start_date: str,
    end_date: str,
    api_key: Optional[str] = None
) -> SerperResponse:
    """
    Fetch news from Finnhub API with resilience patterns
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: Optional Finnhub API key (defaults to env var)
    
    Returns:
        SerperResponse containing news articles
    """
    client = FinnhubAPIClient(api_key=api_key)
    articles = await client.fetch_company_news(ticker, start_date, end_date)
    
    # Convert to SerperResponse format
    return SerperResponse(
        articles=articles,
        total_results=len(articles),
        query=f"{ticker} news",
        pages_fetched=1
    )


# Configuration validation
def validate_finnhub_config(api_key: Optional[str] = None) -> List[str]:
    """Validate Finnhub API configuration"""
    issues = []
    
    if not api_key and not os.getenv('FINNHUB_API_KEY'):
        issues.append("Finnhub API key not found in environment or config")
    
    # Test API connectivity if key is available
    if api_key or os.getenv('FINNHUB_API_KEY'):
        try:
            test_client = finnhub.Client(api_key=api_key or os.getenv('FINNHUB_API_KEY'))
            # Try a simple API call
            test_client.exchange()
            logger.info("Finnhub API connection successful")
        except Exception as e:
            issues.append(f"Failed to connect to Finnhub API: {e}")
    
    return issues