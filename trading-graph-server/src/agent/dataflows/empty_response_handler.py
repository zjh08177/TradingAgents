"""
Empty Response Handler - Safe Fallback System
Provides standardized empty responses when real data cannot be fetched.
Eliminates dangerous mock data by returning empty but valid structures.
"""

from datetime import datetime
from typing import Dict, Any


def create_empty_twitter_response(ticker: str, reason: str = "No real data available") -> Dict[str, Any]:
    """
    Create empty Twitter response when no real data can be fetched
    
    Args:
        ticker: Stock ticker symbol
        reason: Reason why data couldn't be fetched
        
    Returns:
        Empty but valid Twitter response structure
    """
    return {
        "ticker": ticker.upper(),
        "sentiment_score": None,  # Explicitly None instead of mock value
        "tweet_count": 0,
        "top_tweets": [],
        "sentiment": None,
        "confidence": "none",
        "source": "empty_response",
        "fallback_mode": False,  # Not fallback - genuinely empty
        "mock_data": False,  # Not mock - genuinely empty
        "empty_response": True,  # Flag indicating empty response
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "data_available": False
    }


def create_empty_reddit_response(ticker: str, reason: str = "No real data available") -> Dict[str, Any]:
    """
    Create empty Reddit response when no real data can be fetched
    
    Args:
        ticker: Stock ticker symbol  
        reason: Reason why data couldn't be fetched
        
    Returns:
        Empty but valid Reddit response structure
    """
    return {
        "ticker": ticker.upper(),
        "posts": 0,
        "sentiment": None,
        "sentiment_score": None,
        "avg_score": 0,
        "avg_comments": 0,
        "top_posts": [],
        "subreddit_breakdown": {},
        "confidence": "none",
        "message": f"No Reddit data available for {ticker}",
        "timestamp": datetime.now().isoformat(),
        "empty_response": True,
        "reason": reason,
        "data_available": False
    }


def create_empty_stocktwits_response(ticker: str, reason: str = "No real data available") -> Dict[str, Any]:
    """
    Create empty StockTwits response when no real data can be fetched
    
    Args:
        ticker: Stock ticker symbol
        reason: Reason why data couldn't be fetched
        
    Returns:
        Empty but valid StockTwits response structure
    """
    return {
        "ticker": ticker.upper(),
        "sentiment": None,
        "score": None,
        "mentions": 0,
        "bullish_percent": 0,
        "bearish_percent": 0,
        "confidence": "none", 
        "message": f"No StockTwits data available for {ticker}",
        "timestamp": datetime.now().isoformat(),
        "empty_response": True,
        "reason": reason,
        "data_available": False
    }


def is_empty_response(response: Dict[str, Any]) -> bool:
    """
    Check if a response is an empty response
    
    Args:
        response: Response dictionary to check
        
    Returns:
        True if response is empty, False otherwise
    """
    return response.get("empty_response", False) or response.get("data_available", True) is False


def has_real_data(response: Dict[str, Any]) -> bool:
    """
    Check if a response contains real data
    
    Args:
        response: Response dictionary to check
        
    Returns:
        True if response has real data, False otherwise
    """
    if is_empty_response(response):
        return False
    
    # Check for mock data flags
    if response.get("mock_data", False):
        return False
        
    # Check for actual data presence
    if response.get("tweet_count", 0) == 0 and response.get("posts", 0) == 0 and response.get("mentions", 0) == 0:
        return False
        
    return True


def create_empty_market_data_response(ticker: str, reason: str = "Market data unavailable") -> str:
    """
    Create empty market data response when real data cannot be fetched
    
    Args:
        ticker: Stock ticker symbol
        reason: Reason why data couldn't be fetched
        
    Returns:
        Empty market data report string
    """
    return f"""❌ MARKET DATA UNAVAILABLE - {ticker.upper()}

Failed to retrieve market data for {ticker.upper()}: {reason}

No price data, technical indicators, or market statistics are available.
All requested technical indicators and price data are currently unavailable.

Recommendation: HOLD - Cannot make informed trading decisions without market data.

Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: Data collection failed - no mock data provided
"""


def create_empty_technical_indicators_response(ticker: str, indicator: str, reason: str = "Indicator calculation failed") -> str:
    """
    Create empty response for technical indicators when calculation fails
    
    Args:
        ticker: Stock ticker symbol
        indicator: Technical indicator name
        reason: Reason why indicator couldn't be calculated
        
    Returns:
        Empty indicator report string
    """
    return f"""❌ TECHNICAL INDICATOR UNAVAILABLE - {ticker.upper()}

## {indicator} values - DATA UNAVAILABLE

Failed to calculate {indicator} for {ticker.upper()}: {reason}

No technical indicator data is available for the requested time period.

Status: Indicator calculation failed - no fallback data provided
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""


def aggregate_empty_responses(twitter_resp: Dict[str, Any], reddit_resp: Dict[str, Any], 
                             stocktwits_resp: Dict[str, Any], ticker: str) -> Dict[str, Any]:
    """
    Aggregate multiple empty responses into a single empty social media response
    
    Args:
        twitter_resp: Twitter response (possibly empty)
        reddit_resp: Reddit response (possibly empty)
        stocktwits_resp: StockTwits response (possibly empty)
        ticker: Stock ticker symbol
        
    Returns:
        Aggregated empty response
    """
    # Count how many sources have real data
    real_data_sources = []
    
    if has_real_data(twitter_resp):
        real_data_sources.append("twitter")
    if has_real_data(reddit_resp):
        real_data_sources.append("reddit") 
    if has_real_data(stocktwits_resp):
        real_data_sources.append("stocktwits")
    
    if len(real_data_sources) == 0:
        # All sources are empty - return empty aggregate
        return {
            "ticker": ticker.upper(),
            "sentiment_score": None,
            "sources_used": [],
            "sources_available": 0,
            "total_mentions": 0,
            "confidence": "none",
            "source": "empty_aggregate",
            "empty_response": True,
            "reason": "No real data available from any social media source",
            "timestamp": datetime.now().isoformat(),
            "data_available": False,
            "twitter": twitter_resp,
            "reddit": reddit_resp,
            "stocktwits": stocktwits_resp
        }
    else:
        # Some sources have real data - this should use normal aggregation
        # This function only handles the all-empty case
        raise ValueError("aggregate_empty_responses should only be called when all sources are empty")


# Export key functions
__all__ = [
    'create_empty_twitter_response',
    'create_empty_reddit_response', 
    'create_empty_stocktwits_response',
    'create_empty_market_data_response',
    'create_empty_technical_indicators_response',
    'is_empty_response',
    'has_real_data',
    'aggregate_empty_responses'
]