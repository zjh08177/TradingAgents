"""
Aggregated Social Sentiment from Multiple Sources
Combines data from multiple free APIs for reliability
"""

import asyncio
import aiohttp
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import statistics

logger = logging.getLogger(__name__)


async def get_fmp_social_sentiment(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get social sentiment from Financial Modeling Prep
    Free tier: 250 calls/day
    Covers Reddit, StockTwits, Twitter, Yahoo
    """
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        logger.debug("FMP API key not configured")
        return None
    
    url = f"https://financialmodelingprep.com/api/v4/social-sentiments"
    params = {
        "symbol": ticker.upper(),
        "apikey": api_key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=3) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        latest = data[0]  # Get most recent sentiment
                        
                        # Calculate normalized sentiment (0-1 scale)
                        sentiment = latest.get('sentimentScore', 0)
                        normalized_sentiment = (sentiment + 1) / 2  # Convert -1,1 to 0,1
                        
                        return {
                            "ticker": ticker.upper(),
                            "sentiment_score": round(normalized_sentiment, 3),
                            "mention_count": latest.get('mentions', 0),
                            "positive_mentions": latest.get('positiveMentions', 0),
                            "negative_mentions": latest.get('negativeMentions', 0),
                            "confidence": "high" if latest.get('mentions', 0) > 50 else "medium",
                            "source": "fmp_social",
                            "data_sources": ["reddit", "stocktwits", "twitter", "yahoo"],
                            "fallback_mode": False,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                return None
                
    except Exception as e:
        logger.debug(f"FMP API error: {str(e)}")
        return None


async def get_alpha_vantage_news_sentiment(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get news sentiment from Alpha Vantage
    Free tier: 25 calls/day (use sparingly)
    """
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        logger.debug("Alpha Vantage API key not configured")
        return None
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker.upper(),
        "apikey": api_key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "feed" in data:
                        articles = data["feed"]
                        
                        if articles:
                            # Calculate aggregate sentiment from articles
                            sentiments = []
                            for article in articles[:10]:  # Use top 10 articles
                                ticker_sentiment = article.get("ticker_sentiment", [])
                                for ts in ticker_sentiment:
                                    if ts.get("ticker") == ticker.upper():
                                        score = float(ts.get("ticker_sentiment_score", 0))
                                        # Convert to 0-1 scale
                                        normalized = (score + 1) / 2
                                        sentiments.append(normalized)
                            
                            if sentiments:
                                avg_sentiment = statistics.mean(sentiments)
                                
                                return {
                                    "ticker": ticker.upper(),
                                    "sentiment_score": round(avg_sentiment, 3),
                                    "article_count": len(sentiments),
                                    "confidence": "high" if len(sentiments) >= 5 else "medium",
                                    "source": "alpha_vantage_news",
                                    "data_sources": ["news_articles"],
                                    "fallback_mode": False,
                                    "timestamp": datetime.now().isoformat()
                                }
                    
                return None
                
    except Exception as e:
        logger.debug(f"Alpha Vantage API error: {str(e)}")
        return None


async def get_aggregated_social_sentiment(ticker: str) -> Dict[str, Any]:
    """
    Aggregate sentiment from multiple reliable sources
    Provides fallback and redundancy
    
    Priority order:
    1. Finnhub (Reddit + Twitter historical)
    2. StockTwits (existing implementation) 
    3. Reddit (existing implementation)
    4. FMP (if API key available)
    5. Alpha Vantage News (if API key available)
    6. Intelligent fallback simulation
    """
    
    # Import existing implementations
    from .finnhub_social import get_finnhub_social_sentiment
    from .stocktwits_simple import get_stocktwits_fast
    from .reddit_simple import get_reddit_fast
    
    # Create tasks for parallel execution with timeout
    tasks = []
    source_names = []
    
    # Always try these sources
    tasks.append(asyncio.create_task(get_finnhub_social_sentiment(ticker)))
    source_names.append("finnhub")
    
    tasks.append(asyncio.create_task(get_stocktwits_fast(ticker)))
    source_names.append("stocktwits")
    
    tasks.append(asyncio.create_task(get_reddit_fast(ticker)))
    source_names.append("reddit")
    
    # Try additional sources if API keys are configured
    if os.getenv('FMP_API_KEY'):
        tasks.append(asyncio.create_task(get_fmp_social_sentiment(ticker)))
        source_names.append("fmp")
    
    if os.getenv('ALPHA_VANTAGE_API_KEY'):
        tasks.append(asyncio.create_task(get_alpha_vantage_news_sentiment(ticker)))
        source_names.append("alpha_vantage")
    
    # Wait for all tasks with timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=8.0
        )
    except asyncio.TimeoutError:
        logger.warning(f"Timeout getting social sentiment for {ticker}")
        results = []
    
    # Process results
    valid_results = []
    sources_used = []
    
    for i, result in enumerate(results):
        if result and not isinstance(result, Exception) and isinstance(result, dict):
            if result.get('sentiment_score') is not None:
                valid_results.append(result)
                sources_used.append(source_names[i])
                logger.info(f"✅ Got sentiment from {source_names[i]}: {result.get('sentiment_score'):.3f}")
        else:
            logger.debug(f"❌ Failed to get sentiment from {source_names[i]}")
    
    if not valid_results:
        # All sources failed - use intelligent fallback
        logger.warning(f"All social sentiment sources failed for {ticker}, using fallback")
        return {
            "ticker": ticker.upper(),
            "sentiment_score": 0.5,  # Neutral
            "mention_count": 0,
            "confidence": "low",
            "source": "fallback",
            "sources_attempted": source_names,
            "sources_succeeded": [],
            "fallback_mode": True,
            "error": "All data sources unavailable",
            "timestamp": datetime.now().isoformat()
        }
    
    # Aggregate valid results
    sentiment_scores = []
    total_mentions = 0
    all_sources = []
    
    for result in valid_results:
        # Weight by confidence/mention count
        score = result.get('sentiment_score', 0.5)
        mentions = result.get('mention_count', 1) or result.get('tweet_count', 1) or result.get('post_count', 1) or result.get('article_count', 1) or 1
        
        # Add weighted sentiment
        for _ in range(min(mentions, 10)):  # Cap weight at 10 to prevent single source dominance
            sentiment_scores.append(score)
        
        total_mentions += mentions
        
        # Collect data sources
        if 'data_sources' in result:
            all_sources.extend(result['data_sources'])
    
    # Calculate aggregated sentiment
    if sentiment_scores:
        aggregated_sentiment = statistics.mean(sentiment_scores)
        sentiment_std = statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0
    else:
        aggregated_sentiment = 0.5
        sentiment_std = 0
    
    # Determine confidence based on source agreement and volume
    if len(valid_results) >= 3 and sentiment_std < 0.2:
        confidence = "high"
    elif len(valid_results) >= 2:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        "ticker": ticker.upper(),
        "sentiment_score": round(aggregated_sentiment, 3),
        "sentiment_std": round(sentiment_std, 3),
        "total_mentions": total_mentions,
        "confidence": confidence,
        "source": "aggregated",
        "sources_used": sources_used,
        "source_count": len(valid_results),
        "data_sources": list(set(all_sources)),  # Unique data sources
        "fallback_mode": False,
        "timestamp": datetime.now().isoformat()
    }


# Synchronous wrapper for testing
def get_aggregated_sync(ticker: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for testing
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_aggregated_social_sentiment(ticker))
    finally:
        loop.close()


if __name__ == "__main__":
    # Test the aggregated API
    import json
    
    test_ticker = "NVDA"
    print(f"Testing aggregated social sentiment for {test_ticker}...")
    print("=" * 60)
    
    result = get_aggregated_sync(test_ticker)
    print(json.dumps(result, indent=2))