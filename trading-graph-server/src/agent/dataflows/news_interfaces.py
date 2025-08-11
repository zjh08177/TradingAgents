"""
News Analyst API Interfaces - Task 1.1 Implementation
Following SOLID principles and clean architecture
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from dateutil import parser
import logging

logger = logging.getLogger(__name__)


# Task 1.1.1: Define News Article Interface
@dataclass
class NewsArticle:
    """
    Single Responsibility: Represent one news article
    Following DRY and KISS principles
    """
    title: str
    source: str
    snippet: str
    url: str
    date: datetime
    authority_tier: int  # 1=Reuters/Bloomberg, 2=CNBC, 3=Other
    
    def validate(self) -> bool:
        """
        Validate required fields exist
        Following fail-fast principle
        """
        # Check required fields are not empty
        required_fields = [self.title, self.source, self.url]
        if not all(required_fields):
            logger.warning(f"Invalid article: missing required fields - title:{bool(self.title)}, source:{bool(self.source)}, url:{bool(self.url)}")
            return False
        
        # Check authority tier is valid
        if self.authority_tier not in [1, 2, 3]:
            logger.warning(f"Invalid authority tier: {self.authority_tier}")
            return False
            
        return True
    
    def __str__(self) -> str:
        """Human-readable representation"""
        return f"[{self.source} - Tier {self.authority_tier}] {self.title[:50]}..."


# Task 1.1.2: Define Serper Response Interface
@dataclass
class SerperResponse:
    """
    Single Responsibility: Parse and represent Serper API response
    Open/Closed Principle: Open for extension via factory method
    """
    articles: List[NewsArticle]
    total_results: int
    query: str
    pages_fetched: int
    
    @classmethod
    def from_api_response(cls, data: dict, pages: int) -> 'SerperResponse':
        """
        Factory method to create from API response
        Dependency Inversion: Depend on abstract parse_date and classify_source
        """
        articles = []
        
        for item in data.get('news', []):
            try:
                article = NewsArticle(
                    title=item.get('title', ''),
                    source=item.get('source', ''),
                    snippet=item.get('snippet', ''),
                    url=item.get('link', ''),
                    date=parse_date(item.get('date', '')),
                    authority_tier=classify_source(item.get('source', ''))
                )
                
                # Only add valid articles
                if article.validate():
                    articles.append(article)
                else:
                    logger.debug(f"Skipping invalid article: {item.get('title', 'Unknown')}")
                    
            except Exception as e:
                logger.error(f"Error parsing article: {e}, data: {item}")
                continue
        
        return cls(
            articles=articles,
            total_results=len(articles),
            query=data.get('searchParameters', {}).get('q', ''),
            pages_fetched=pages
        )
    
    def get_articles_by_tier(self, tier: int) -> List[NewsArticle]:
        """Get articles filtered by authority tier"""
        return [a for a in self.articles if a.authority_tier == tier]
    
    def has_sufficient_coverage(self, min_articles: int = 10) -> bool:
        """Check if response has sufficient news coverage"""
        return self.total_results >= min_articles


# Task 1.1.3: Define Error Response Interface
@dataclass
class NewsGatheringError(Exception):
    """
    Single Responsibility: Represent news gathering failures
    Interface Segregation: Specific error handling methods
    """
    error_type: str  # 'api_error', 'rate_limit', 'no_results', 'timeout'
    message: str
    fallback_attempted: bool
    partial_results: Optional[List[NewsArticle]]
    
    # Valid error types
    API_ERROR = 'api_error'
    RATE_LIMIT = 'rate_limit'
    NO_RESULTS = 'no_results'
    TIMEOUT = 'timeout'
    
    def should_retry(self) -> bool:
        """
        Determine if operation should be retried
        Following KISS principle - simple retry logic
        """
        retryable_errors = [self.TIMEOUT, self.RATE_LIMIT]
        return self.error_type in retryable_errors
    
    def has_partial_results(self) -> bool:
        """Check if we have any partial results to work with"""
        return self.partial_results is not None and len(self.partial_results) > 0
    
    def get_user_message(self) -> str:
        """Get user-friendly error message"""
        messages = {
            self.API_ERROR: "News service is temporarily unavailable",
            self.RATE_LIMIT: "Too many requests, please try again later",
            self.NO_RESULTS: "No news found for this query",
            self.TIMEOUT: "Request took too long, please try again"
        }
        return messages.get(self.error_type, self.message)
    
    def __str__(self) -> str:
        """String representation for logging"""
        fallback_str = "with fallback" if self.fallback_attempted else "no fallback"
        partial_str = f", {len(self.partial_results)} partial results" if self.partial_results else ""
        return f"NewsGatheringError({self.error_type}): {self.message} ({fallback_str}{partial_str})"


# Helper functions following DRY principle
def parse_date(date_str: str) -> datetime:
    """
    Parse date string to datetime object
    Handles various date formats from news sources
    """
    if not date_str:
        return datetime.now()
    
    try:
        # Try parsing with dateutil (handles many formats)
        return parser.parse(date_str)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date: {date_str}, using current time")
        return datetime.now()


def classify_source(source: str) -> int:
    """
    Classify news source by authority tier
    Single Responsibility: Only classifies sources
    """
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


def validate_error_type(error_type: str) -> bool:
    """Validate that error type is one of the allowed types"""
    valid_types = [
        NewsGatheringError.API_ERROR,
        NewsGatheringError.RATE_LIMIT,
        NewsGatheringError.NO_RESULTS,
        NewsGatheringError.TIMEOUT
    ]
    return error_type in valid_types