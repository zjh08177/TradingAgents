"""
Ultra-fast Reddit implementation for unit testing
Optimized version with shorter timeouts and better error handling
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def get_reddit_fast(
    ticker: str, 
    subreddits: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Fast Reddit data fetching with aggressive timeouts for testing
    
    Args:
        ticker: Stock ticker symbol
        subreddits: List of subreddits (defaults to top 3 for speed)
        limit: Posts per subreddit (max 10 for speed)
    
    Returns:
        Reddit sentiment data
    """
    # Use only top 3 subreddits for speed
    if not subreddits:
        subreddits = ["wallstreetbets", "stocks", "investing"]
    else:
        subreddits = subreddits[:3]  # Limit to 3 max
    
    all_posts = []
    subreddit_breakdown = {}
    
    # Set very aggressive timeout
    timeout = aiohttp.ClientTimeout(total=3)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            headers = {"User-Agent": "StockAnalyzer/1.0"}
            
            # Process just the first subreddit for speed
            subreddit = subreddits[0]
            posts = await fetch_subreddit_fast(session, subreddit, ticker, limit, headers)
            
            if posts:
                all_posts.extend(posts)
                subreddit_breakdown[subreddit] = len(posts)
            else:
                subreddit_breakdown[subreddit] = 0
                
    except asyncio.TimeoutError:
        logger.warning(f"Reddit timeout for {ticker}")
        return create_fallback_result(ticker, subreddit_breakdown)
    except Exception as e:
        logger.error(f"Reddit error: {str(e)}")
        return create_fallback_result(ticker, subreddit_breakdown)
    
    if not all_posts:
        return create_fallback_result(ticker, subreddit_breakdown)
    
    # Process sentiment
    return process_reddit_sentiment(ticker, all_posts, subreddit_breakdown)


async def fetch_subreddit_fast(
    session: aiohttp.ClientSession,
    subreddit: str, 
    ticker: str,
    limit: int,
    headers: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Fast single subreddit fetch with 2s timeout"""
    
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": ticker,
        "sort": "hot", 
        "limit": min(limit, 10),
        "t": "week",
        "restrict_sr": "true"
    }
    
    try:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                posts = []
                
                for child in data.get("data", {}).get("children", []):
                    post_data = child.get("data", {})
                    post = {
                        "title": post_data.get("title", ""),
                        "score": post_data.get("score", 0),
                        "upvote_ratio": post_data.get("upvote_ratio", 0.5),
                        "num_comments": post_data.get("num_comments", 0),
                        "subreddit": subreddit
                    }
                    posts.append(post)
                
                return posts
                
    except Exception as e:
        logger.warning(f"Error fetching r/{subreddit}: {str(e)}")
    
    return []


def process_reddit_sentiment(
    ticker: str,
    posts: List[Dict[str, Any]], 
    subreddit_breakdown: Dict[str, int]
) -> Dict[str, Any]:
    """Process sentiment from Reddit posts"""
    
    if not posts:
        return create_fallback_result(ticker, subreddit_breakdown)
    
    # Calculate basic metrics
    avg_score = sum(p.get("score", 0) for p in posts) / len(posts)
    avg_comments = sum(p.get("num_comments", 0) for p in posts) / len(posts)
    avg_ratio = sum(p.get("upvote_ratio", 0.5) for p in posts) / len(posts)
    
    # Simple sentiment based on upvote ratio
    sentiment_score = avg_ratio  # 0.5 = neutral, >0.5 = bullish
    
    # Confidence based on post count
    confidence = "high" if len(posts) >= 8 else "medium" if len(posts) >= 4 else "low"
    
    return {
        "ticker": ticker,
        "sentiment_score": round(sentiment_score, 3),
        "post_count": len(posts),
        "avg_score": round(avg_score, 2),
        "avg_comments": round(avg_comments, 2),
        "subreddit_breakdown": subreddit_breakdown,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }


def create_fallback_result(ticker: str, subreddit_breakdown: Dict[str, int]) -> Dict[str, Any]:
    """Create fallback result when no posts found"""
    return {
        "ticker": ticker,
        "sentiment_score": 0.5,
        "post_count": 0,
        "avg_score": 0,
        "avg_comments": 0,
        "subreddit_breakdown": subreddit_breakdown,
        "confidence": "low",
        "error": "No posts found or timeout",
        "timestamp": datetime.now().isoformat()
    }


# Sync wrapper for testing
def get_reddit_sync(ticker: str) -> Dict[str, Any]:
    """Synchronous wrapper for testing"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_reddit_fast(ticker))
    finally:
        loop.close()