"""
Task 1.2: Pagination Implementation for News Analyst
Following SOLID principles and detailed atomic tasks from day1_detailed_plan.md
"""

import asyncio
import anyio
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Callable, Optional, Tuple, Set
from .news_interfaces import NewsArticle, SerperResponse, NewsGatheringError

logger = logging.getLogger(__name__)


# Task 1.2.1: Create Pagination Configuration (10 min)
class PaginationConfig:
    """Single Responsibility: Manage pagination settings"""
    DEFAULT_PAGES = 5
    MAX_PAGES = 10
    RESULTS_PER_PAGE = 10
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.pages = self._determine_pages()
    
    def _determine_pages(self) -> int:
        """Determine pages based on ticker volatility"""
        HIGH_VOLUME_TICKERS = ['AAPL', 'TSLA', 'NVDA', 'AMC', 'GME', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META']
        if self.ticker in HIGH_VOLUME_TICKERS:
            return 7  # More pages for high-news stocks
        return self.DEFAULT_PAGES
    
    def get_offset(self, page: int) -> int:
        """Calculate offset for pagination"""
        return page * self.RESULTS_PER_PAGE
    
    def is_valid_page(self, page: int) -> bool:
        """Check if page number is valid"""
        return 0 <= page < min(self.pages, self.MAX_PAGES)
    
    def __str__(self) -> str:
        """String representation for logging"""
        return f"PaginationConfig(ticker={self.ticker}, pages={self.pages})"


# Task 1.2.4: Implement Early Termination Logic (10 min)
class PaginationController:
    """Single Responsibility: Control pagination flow"""
    
    def __init__(self, min_articles: int = 20, max_duplicates: int = 5):
        self.min_articles = min_articles
        self.max_duplicates = max_duplicates
        self.seen_urls: Set[str] = set()
        self.duplicate_count = 0
        self.total_articles_processed = 0
    
    def should_continue(self, current_articles: List[NewsArticle], page: int) -> bool:
        """Decide if pagination should continue"""
        # Safety check: don't exceed maximum pages
        if page >= PaginationConfig.MAX_PAGES:
            logger.info(f"Reached maximum pages limit: {PaginationConfig.MAX_PAGES}")
            return False
        
        # Check if we have enough articles (double the minimum)
        if len(current_articles) >= self.min_articles * 2:
            logger.info(f"Collected {len(current_articles)} articles, exceeding target of {self.min_articles * 2}")
            return False
            
        # Too many duplicates indicates source exhaustion
        if self.duplicate_count >= self.max_duplicates:
            logger.info(f"Too many duplicates ({self.duplicate_count}), stopping pagination")
            return False
            
        return True
    
    def process_article(self, article: NewsArticle) -> bool:
        """Track duplicates, return True if unique"""
        self.total_articles_processed += 1
        
        if article.url in self.seen_urls:
            self.duplicate_count += 1
            logger.debug(f"Duplicate article found: {article.title[:50]}...")
            return False
        
        self.seen_urls.add(article.url)
        return True
    
    def get_statistics(self) -> dict:
        """Get pagination statistics"""
        return {
            'total_processed': self.total_articles_processed,
            'unique_articles': len(self.seen_urls),
            'duplicates': self.duplicate_count,
            'duplicate_rate': self.duplicate_count / max(self.total_articles_processed, 1)
        }


# Task 1.2.2 & 1.2.3: Implement Pagination Loop with Single Page Fetch (25 min)
async def fetch_with_pagination(
    query: str, 
    date_range: Tuple[str, str],
    config: PaginationConfig,
    api_key: str,
    fetch_single_page_func: Callable
) -> SerperResponse:
    """Single Responsibility: Handle paginated API calls"""
    
    logger.info(f"Starting pagination fetch: {config}")
    logger.info(f"Query: '{query}', Date range: {date_range[0]} to {date_range[1]}")
    
    all_articles = []
    controller = PaginationController()
    pages_fetched = 0
    
    for page in range(config.pages):
        if not controller.should_continue(all_articles, page):
            logger.info(f"Early termination at page {page}")
            break
            
        try:
            logger.info(f"Fetching page {page + 1}/{config.pages}...")
            
            # Task 1.2.3: Single Page Fetch (integrated)
            response = await fetch_single_page(
                func=fetch_single_page_func,
                query=query,
                date_range=date_range,
                offset=config.get_offset(page),
                api_key=api_key,
                page=page
            )
            
            if not response or not response.get('news'):
                pages_fetched += 1  # Count the empty page as fetched
                logger.warning(f"Page {page + 1} returned no results, stopping pagination")
                break
                
            # Process articles through controller
            page_articles = []
            for item in response.get('news', []):
                try:
                    article = NewsArticle(
                        title=item.get('title', ''),
                        source=item.get('source', ''),
                        snippet=item.get('snippet', ''),
                        url=item.get('link', ''),
                        date=_safe_parse_date(item.get('date', '')),
                        authority_tier=_classify_source_authority(item.get('source', ''))
                    )
                    
                    # Only add if unique and valid
                    if article.validate() and controller.process_article(article):
                        page_articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Error processing article on page {page + 1}: {e}")
                    continue
            
            all_articles.extend(page_articles)
            pages_fetched += 1  # Only increment after successful page processing
            logger.info(f"Page {page + 1}: collected {len(page_articles)} unique articles (total: {len(all_articles)})")
            
            # Rate limit protection
            if page < config.pages - 1:
                await anyio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Page {page + 1} fetch failed: {e}")
            if page == 0:
                # First page failure is critical
                raise NewsGatheringError(
                    error_type=NewsGatheringError.API_ERROR,
                    message=f"First page fetch failed: {e}",
                    fallback_attempted=False,
                    partial_results=None
                )
            else:
                # Partial results are acceptable
                logger.warning(f"Continuing with partial results after page {page} failure")
                break
    
    # Log final statistics
    stats = controller.get_statistics()
    logger.info(f"Pagination complete: {stats}")
    
    return SerperResponse.from_api_response(
        {'news': [_article_to_dict(a) for a in all_articles], 'searchParameters': {'q': query}},
        pages=pages_fetched
    )


async def fetch_single_page(
    func: Callable,
    query: str,
    date_range: Tuple[str, str],
    offset: int,
    api_key: str,
    page: int
) -> dict:
    """
    Task 1.2.3: Single Page Fetch implementation
    Single Responsibility: Fetch a single page of results
    """
    
    start_time = datetime.now()
    
    try:
        # Call the actual fetch function with pagination parameters
        result = await func(
            query=query,
            start_date=date_range[0],
            end_date=date_range[1],
            offset=offset,
            api_key=api_key
        )
        
        fetch_time = (datetime.now() - start_time).total_seconds()
        logger.debug(f"Page {page + 1} fetched in {fetch_time:.2f}s")
        
        return result
        
    except Exception as e:
        logger.error(f"Single page fetch failed for page {page + 1}: {e}")
        raise


# Helper functions for pagination
def _safe_parse_date(date_str: str) -> datetime:
    """Safe date parsing with fallback"""
    try:
        from dateutil import parser
        if not date_str:
            return datetime.now()
        return parser.parse(date_str)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date: {date_str}, using current time")
        return datetime.now()


def _classify_source_authority(source: str) -> int:
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
        'business insider', 'barrons', 'the economist', 'fortune'
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


def _article_to_dict(article: NewsArticle) -> dict:
    """Convert NewsArticle back to dict format for API compatibility"""
    return {
        'title': article.title,
        'source': article.source,
        'snippet': article.snippet,
        'link': article.url,
        'date': article.date.isoformat() + 'Z'
    }


# Configuration validation
def validate_pagination_config(config: PaginationConfig) -> List[str]:
    """Validate pagination configuration"""
    issues = []
    
    if config.pages <= 0:
        issues.append("Pages must be positive")
    
    if config.pages > PaginationConfig.MAX_PAGES:
        issues.append(f"Pages ({config.pages}) exceeds maximum ({PaginationConfig.MAX_PAGES})")
    
    if not config.ticker:
        issues.append("Ticker cannot be empty")
    
    return issues