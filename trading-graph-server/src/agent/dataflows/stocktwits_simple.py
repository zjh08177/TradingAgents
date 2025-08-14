"""
StockTwits Sentiment Analysis Tool
Ultra-lightweight implementation using public API (no auth required)
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def get_stocktwits_fast(
    ticker: str, 
    limit: int = 30
) -> Dict[str, Any]:
    """
    Get StockTwits sentiment data using public API (no auth required)
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        limit: Number of messages to fetch (max 30 for public API)
    
    Returns:
        Dictionary containing:
        - ticker: The ticker symbol
        - sentiment_score: -1 to 1 (-1=bearish, 0=neutral, 1=bullish)
        - bullish_percent: Percentage of bullish messages
        - bearish_percent: Percentage of bearish messages
        - message_count: Total messages analyzed
        - message_volume: Recent message activity level
        - top_messages: Sample of recent messages
        - confidence: low/medium/high based on data volume
        - error: Error message if request failed
    """
    
    # StockTwits public API endpoint (no auth required)
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Add timeout and user agent
            headers = {
                "User-Agent": "StockAnalyzer/1.0"
            }
            
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data is None:
                        return {
                            "ticker": ticker,
                            "sentiment_score": 0.0,
                            "message_count": 0,
                            "error": "Empty response from API",
                            "confidence": "low"
                        }
                    return process_stocktwits_data(ticker, data)
                elif response.status == 404:
                    logger.warning(f"Ticker {ticker} not found on StockTwits")
                    return {
                        "ticker": ticker,
                        "sentiment_score": 0.0,
                        "message_count": 0,
                        "error": f"Ticker {ticker} not found",
                        "confidence": "low"
                    }
                elif response.status == 429:
                    logger.warning("StockTwits rate limit exceeded")
                    return {
                        "ticker": ticker,
                        "sentiment_score": 0.0,
                        "message_count": 0,
                        "error": "Rate limit exceeded",
                        "confidence": "low"
                    }
                else:
                    logger.error(f"StockTwits API error: {response.status}")
                    return {
                        "ticker": ticker,
                        "sentiment_score": 0.0,
                        "message_count": 0,
                        "error": f"API error: {response.status}",
                        "confidence": "low"
                    }
                    
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching StockTwits data for {ticker}")
        from .empty_response_handler import create_empty_stocktwits_response
        return create_empty_stocktwits_response(
            ticker=ticker,
            reason="StockTwits API request timeout"
        )
    except Exception as e:
        logger.error(f"Error fetching StockTwits data: {str(e)}")
        from .empty_response_handler import create_empty_stocktwits_response
        return create_empty_stocktwits_response(
            ticker=ticker,
            reason=f"StockTwits API error: {str(e)}"
        )


def process_stocktwits_data(ticker: str, data: Dict) -> Dict[str, Any]:
    """
    Process raw StockTwits API response
    
    Args:
        ticker: Stock ticker symbol
        data: Raw API response
    
    Returns:
        Processed sentiment data
    """
    
    if data is None:
        from .empty_response_handler import create_empty_stocktwits_response
        return create_empty_stocktwits_response(
            ticker=ticker,
            reason="No data received from StockTwits API"
        )
    
    messages = data.get("messages", [])
    
    if not messages:
        from .empty_response_handler import create_empty_stocktwits_response
        return create_empty_stocktwits_response(
            ticker=ticker,
            reason="No messages found on StockTwits"
        )
    
    # Count sentiment
    bullish = 0
    bearish = 0
    neutral = 0
    total = len(messages)
    
    # Extract top messages
    top_messages = []
    
    for msg in messages:
        # Get sentiment if available
        entities = msg.get("entities", {})
        sentiment = entities.get("sentiment")
        
        # Handle None sentiment or dict sentiment
        if sentiment is None:
            basic_sentiment = None
        elif isinstance(sentiment, dict):
            basic_sentiment = sentiment.get("basic")
        else:
            basic_sentiment = None
        
        if basic_sentiment == "Bullish":
            bullish += 1
        elif basic_sentiment == "Bearish":
            bearish += 1
        else:
            neutral += 1
        
        # Add to top messages (first 5)
        if len(top_messages) < 5:
            top_messages.append({
                "body": msg.get("body", "")[:200],  # Truncate long messages
                "sentiment": basic_sentiment or "Neutral",
                "username": msg.get("user", {}).get("username", "unknown"),
                "created_at": msg.get("created_at", ""),
                "likes": msg.get("likes", {}).get("total", 0)
            })
    
    # Calculate sentiment score
    # Range: -1 (all bearish) to +1 (all bullish)
    if total > 0:
        # Weight sentiment by explicit labels
        sentiment_labeled = bullish + bearish
        if sentiment_labeled > 0:
            sentiment_score = (bullish - bearish) / sentiment_labeled
        else:
            # If no explicit sentiment, use neutral score
            sentiment_score = 0.0
        
        bullish_percent = (bullish / total) * 100
        bearish_percent = (bearish / total) * 100
    else:
        sentiment_score = 0.0
        bullish_percent = 0.0
        bearish_percent = 0.0
    
    # Determine confidence based on message count and sentiment labels
    labeled_count = bullish + bearish
    if labeled_count >= 10:
        confidence = "high"
    elif labeled_count >= 5:
        confidence = "medium"
    else:
        confidence = "low"
    
    # Get symbol data if available
    symbol_data = data.get("symbol", {})
    
    return {
        "ticker": ticker,
        "sentiment_score": round(sentiment_score, 3),
        "bullish_percent": round(bullish_percent, 1),
        "bearish_percent": round(bearish_percent, 1),
        "neutral_percent": round((neutral / total * 100) if total > 0 else 0, 1),
        "message_count": total,
        "sentiment_labeled_count": labeled_count,
        "top_messages": top_messages,
        "confidence": confidence,
        "symbol_title": symbol_data.get("title", ticker),
        "timestamp": datetime.now().isoformat()
    }


async def get_stocktwits_sentiment(ticker: str) -> Dict[str, Any]:
    """
    Wrapper function for compatibility with existing interface
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        StockTwits sentiment data
    """
    return await get_stocktwits_fast(ticker)


# Synchronous wrapper for testing
def get_stocktwits_sync(ticker: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for testing purposes
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        StockTwits sentiment data
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_stocktwits_fast(ticker))
    finally:
        loop.close()


if __name__ == "__main__":
    # Quick test
    import json
    
    test_ticker = "AAPL"
    print(f"Testing StockTwits API for {test_ticker}...")
    
    result = get_stocktwits_sync(test_ticker)
    print(json.dumps(result, indent=2))