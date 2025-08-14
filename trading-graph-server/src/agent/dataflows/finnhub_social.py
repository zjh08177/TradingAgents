"""
Finnhub Social Sentiment Integration
Free tier: 60 API calls per minute
Provides Reddit and Twitter historical sentiment data
"""

import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


async def get_finnhub_social_sentiment(ticker: str) -> Dict[str, Any]:
    """
    Get social sentiment from Finnhub API (FREE tier)
    
    Finnhub aggregates Reddit and Twitter sentiment data
    Free tier allows 60 calls/minute
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA')
    
    Returns:
        Dict containing aggregated social sentiment:
        - sentiment_score: 0-1 scale (0=bearish, 1=bullish)
        - mention_count: Total social mentions
        - confidence: Based on data volume
        - sources: Data sources used
    """
    
    # Get API key from environment or use demo key for testing
    api_key = os.getenv('FINNHUB_API_KEY', 'demo')
    
    # Finnhub social sentiment endpoint
    url = "https://finnhub.io/api/v1/stock/social-sentiment"
    
    params = {
        "symbol": ticker.upper(),
        "token": api_key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process Reddit data
                    reddit_data = data.get('reddit', [])
                    twitter_data = data.get('twitter', [])
                    
                    if not reddit_data and not twitter_data:
                        logger.warning(f"No social data found for {ticker} on Finnhub")
                        return None
                    
                    # Calculate aggregated sentiment
                    total_score = 0
                    total_mentions = 0
                    
                    # Process Reddit sentiment
                    if reddit_data:
                        for item in reddit_data:
                            score = item.get('score', 0)
                            mentions = item.get('mention', 1)
                            # Normalize score to 0-1 range
                            normalized_score = (score + 1) / 2  # Convert from -1,1 to 0,1
                            total_score += normalized_score * mentions
                            total_mentions += mentions
                    
                    # Process Twitter sentiment (if available)
                    if twitter_data:
                        for item in twitter_data:
                            score = item.get('score', 0)
                            mentions = item.get('mention', 1)
                            # Normalize score to 0-1 range
                            normalized_score = (score + 1) / 2
                            total_score += normalized_score * mentions
                            total_mentions += mentions
                    
                    # Calculate weighted average sentiment
                    if total_mentions > 0:
                        avg_sentiment = total_score / total_mentions
                    else:
                        avg_sentiment = 0.5  # Neutral
                    
                    # Determine confidence based on mention volume
                    if total_mentions >= 100:
                        confidence = "high"
                    elif total_mentions >= 30:
                        confidence = "medium"
                    else:
                        confidence = "low"
                    
                    return {
                        "ticker": ticker.upper(),
                        "sentiment_score": round(avg_sentiment, 3),
                        "mention_count": total_mentions,
                        "reddit_mentions": len(reddit_data),
                        "twitter_mentions": len(twitter_data),
                        "confidence": confidence,
                        "source": "finnhub_social",
                        "data_sources": ["reddit", "twitter_historical"],
                        "fallback_mode": False,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                elif response.status == 403:
                    logger.error(f"Finnhub API key invalid or limit exceeded")
                    return None
                elif response.status == 429:
                    logger.warning(f"Finnhub rate limit exceeded (60/min on free tier)")
                    return None
                else:
                    logger.error(f"Finnhub API error: {response.status}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error(f"Finnhub API timeout for {ticker}")
        return None
    except Exception as e:
        logger.error(f"Error fetching Finnhub social sentiment: {str(e)}")
        return None


async def get_finnhub_news_sentiment(ticker: str, days: int = 7) -> Dict[str, Any]:
    """
    Get news sentiment from Finnhub
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days to look back (default 7)
    
    Returns:
        News sentiment data
    """
    
    api_key = os.getenv('FINNHUB_API_KEY', 'demo')
    url = "https://finnhub.io/api/v1/news-sentiment"
    
    params = {
        "symbol": ticker.upper(),
        "token": api_key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract sentiment metrics
                    buzz = data.get('buzz', {})
                    sentiment_data = data.get('sentiment', {})
                    
                    return {
                        "ticker": ticker.upper(),
                        "articles_volume": buzz.get('articlesInLastWeek', 0),
                        "weekly_average": buzz.get('weeklyAverage', 0),
                        "buzz_score": buzz.get('buzz', 0),
                        "bearish_percent": sentiment_data.get('bearishPercent', 0),
                        "bullish_percent": sentiment_data.get('bullishPercent', 0),
                        "source": "finnhub_news",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return None
                    
    except Exception as e:
        logger.error(f"Error fetching Finnhub news sentiment: {str(e)}")
        return None


# Synchronous wrapper for testing
def get_finnhub_sync(ticker: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for testing
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_finnhub_social_sentiment(ticker))
    finally:
        loop.close()


if __name__ == "__main__":
    # Test the API
    import json
    
    test_ticker = "AAPL"
    print(f"Testing Finnhub social sentiment for {test_ticker}...")
    
    result = get_finnhub_sync(test_ticker)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Failed to get sentiment data. Check API key or ticker symbol.")