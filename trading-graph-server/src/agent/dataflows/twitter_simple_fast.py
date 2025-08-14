"""
Ultra-fast Twitter implementation for unit testing
Optimized version with immediate fallback to simulation
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime
import logging
import hashlib
import random

logger = logging.getLogger(__name__)


async def get_twitter_fast(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """
    Fast Twitter sentiment with immediate fallback to simulation
    Designed for unit testing with consistent results
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of tweets (for simulation)
    
    Returns:
        Twitter sentiment data
    """
    # Skip all real API calls and go straight to simulation
    # This ensures tests run quickly and consistently
    return simulate_twitter_sentiment(ticker, limit)


def simulate_twitter_sentiment(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """
    Generate deterministic Twitter sentiment simulation
    Uses ticker-based seed for consistent test results
    """
    
    # Create deterministic seed from ticker
    seed = int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16) % 100000
    random.seed(seed)
    
    # Generate realistic patterns based on ticker
    if ticker.upper() in ['BTC', 'ETH', 'CRYPTO']:
        # Crypto tends to be more volatile
        tweet_count = random.randint(8, 20)
        base_sentiment = random.uniform(0.3, 0.8)
    elif ticker.upper() in ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']:
        # Big tech - moderate activity
        tweet_count = random.randint(10, 25)
        base_sentiment = random.uniform(0.4, 0.7) 
    else:
        # Other stocks
        tweet_count = random.randint(5, 15)
        base_sentiment = random.uniform(0.35, 0.65)
    
    # Generate sample tweets
    sample_tweets = []
    tweet_templates = [
        f"${ticker} looking strong today! 🚀",
        f"Holding ${ticker} for the long term",
        f"#{ticker} analysis shows potential",
        f"Just bought more ${ticker}",
        f"${ticker} to the moon!"
    ]
    
    for i in range(min(5, tweet_count)):
        sample_tweets.append({
            "text": random.choice(tweet_templates),
            "author": f"trader_{random.randint(100, 999)}",
            "link": f"https://twitter.com/user/status/{random.randint(1000000000, 9999999999)}",
            "published": datetime.now().isoformat()
        })
    
    # Confidence based on tweet count
    confidence = "high" if tweet_count >= 15 else "medium" if tweet_count >= 8 else "low"
    
    return {
        "ticker": ticker,
        "sentiment_score": round(base_sentiment, 3),
        "tweet_count": tweet_count,
        "top_tweets": sample_tweets,
        "confidence": confidence,
        "source": "simulation",
        "fallback_mode": True,
        "note": "Simulated data for testing",
        "timestamp": datetime.now().isoformat()
    }


# Compatibility wrapper
async def get_twitter_mentions(ticker: str) -> Dict[str, Any]:
    """Wrapper for interface compatibility"""
    return await get_twitter_fast(ticker)


# Sync wrapper for testing  
def get_twitter_sync(ticker: str) -> Dict[str, Any]:
    """Synchronous wrapper for testing"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_twitter_fast(ticker))
    finally:
        loop.close()