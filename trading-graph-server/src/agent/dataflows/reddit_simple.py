"""
Ultrafast Reddit Data Fetching - No Authentication Required
Following KISS principle: Simple, fast, reliable
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def get_reddit_fast(
    ticker: str,
    subreddits: Optional[List[str]] = None,
    limit: int = 25,
    time_filter: str = "week"
) -> Dict[str, Any]:
    """
    Ultrafast Reddit data fetching using public JSON API
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "TSLA", "BTC", "ETH")
        subreddits: List of subreddits to search (default: financial subreddits)
        limit: Number of posts per subreddit (max 100, default 25)
        time_filter: Time range - "hour", "day", "week", "month", "year", "all"
    
    Returns:
        Dict containing:
        - ticker: The ticker symbol
        - sentiment_score: Calculated sentiment (0-1 scale)
        - post_count: Total number of posts found
        - avg_score: Average Reddit score (upvotes)
        - avg_comments: Average number of comments
        - top_posts: List of top 5 posts by score
        - subreddit_breakdown: Posts per subreddit
        - error: Error message if any
    
    Response time: <500ms for single subreddit, <2s for comprehensive search
    """
    # Default to popular financial subreddits if none provided
    if not subreddits:
        # Fallback to main trading subreddits
        subreddits = ["wallstreetbets", "stocks", "investing", "StockMarket", "CryptoCurrency"]
    
    all_posts = []
    subreddit_breakdown = {}
    
    async with aiohttp.ClientSession() as session:
        # Set user agent to avoid being blocked
        headers = {"User-Agent": "StockAnalyzer/1.0 (Trading Agent)"}
        
        # Limit concurrent requests to avoid rate limiting
        # Process subreddits in batches of 5 for optimal performance
        batch_size = 5
        all_results = []
        
        for i in range(0, len(subreddits), batch_size):
            batch = subreddits[i:i + batch_size]
            tasks = []
            for subreddit in batch:
                task = fetch_subreddit_data(session, subreddit, ticker, limit, time_filter, headers)
                tasks.append(task)
            
            # Gather results for this batch with error handling
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend(batch_results)
            
            # Small delay between batches to avoid rate limiting
            if i + batch_size < len(subreddits):
                await asyncio.sleep(0.2)
        
        results = all_results
        
        # Process results
        for subreddit, result in zip(subreddits, results):
            if isinstance(result, Exception):
                logger.warning(f"Error fetching r/{subreddit}: {result}")
                subreddit_breakdown[subreddit] = 0
            elif isinstance(result, list):
                all_posts.extend(result)
                subreddit_breakdown[subreddit] = len(result)
            else:
                subreddit_breakdown[subreddit] = 0
    
    # Process and return sentiment analysis
    return process_reddit_sentiment(ticker, all_posts, subreddit_breakdown)


async def fetch_subreddit_data(
    session: aiohttp.ClientSession,
    subreddit: str,
    ticker: str,
    limit: int,
    time_filter: str,
    headers: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Fetch posts from a single subreddit
    
    Returns list of post dictionaries
    """
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": ticker,
        "sort": "hot",
        "limit": min(limit, 100),  # Reddit max is 100
        "t": time_filter,
        "restrict_sr": "true"  # Search only in this subreddit
    }
    
    try:
        async with session.get(url, params=params, headers=headers, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                posts = []
                
                # Extract post data
                for child in data.get("data", {}).get("children", []):
                    post_data = child.get("data", {})
                    
                    # Extract relevant fields
                    post = {
                        "title": post_data.get("title", ""),
                        "selftext": post_data.get("selftext", ""),
                        "score": post_data.get("score", 0),
                        "upvote_ratio": post_data.get("upvote_ratio", 0.5),
                        "num_comments": post_data.get("num_comments", 0),
                        "created_utc": post_data.get("created_utc", 0),
                        "subreddit": post_data.get("subreddit", subreddit),
                        "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                        "author": post_data.get("author", "unknown")
                    }
                    posts.append(post)
                
                return posts
            else:
                logger.warning(f"Reddit API returned status {response.status} for r/{subreddit}")
                return []
                
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching r/{subreddit}")
        return []
    except Exception as e:
        logger.error(f"Error fetching r/{subreddit}: {e}")
        return []


def process_reddit_sentiment(
    ticker: str,
    posts: List[Dict[str, Any]],
    subreddit_breakdown: Dict[str, int]
) -> Dict[str, Any]:
    """
    Process posts and calculate sentiment metrics
    
    Simple sentiment calculation based on:
    - Post scores (upvotes)
    - Upvote ratios
    - Comment engagement
    - Recent vs old posts
    """
    if not posts:
        from .empty_response_handler import create_empty_reddit_response
        return create_empty_reddit_response(
            ticker=ticker,
            reason="No Reddit posts found for ticker"
        )
    
    # Calculate metrics
    total_score = sum(p.get("score", 0) for p in posts)
    total_comments = sum(p.get("num_comments", 0) for p in posts)
    avg_score = total_score / len(posts) if posts else 0
    avg_comments = total_comments / len(posts) if posts else 0
    
    # Calculate weighted sentiment
    # Higher scores and upvote ratios = more bullish
    sentiment_components = []
    
    for post in posts:
        score = post.get("score", 0)
        upvote_ratio = post.get("upvote_ratio", 0.5)
        comments = post.get("num_comments", 0)
        
        # Weight by engagement (score + comments)
        engagement = score + (comments * 2)  # Comments weighted more
        
        # Base sentiment from upvote ratio (0.5 = neutral, >0.5 = positive)
        post_sentiment = upvote_ratio
        
        # Boost for high engagement
        if engagement > 100:
            post_sentiment = min(post_sentiment * 1.2, 1.0)
        elif engagement < 10:
            post_sentiment = post_sentiment * 0.9
        
        sentiment_components.append((post_sentiment, engagement))
    
    # Calculate weighted average sentiment
    if sentiment_components:
        total_weight = sum(weight for _, weight in sentiment_components)
        if total_weight > 0:
            weighted_sentiment = sum(
                sentiment * weight for sentiment, weight in sentiment_components
            ) / total_weight
        else:
            weighted_sentiment = 0.5
    else:
        weighted_sentiment = 0.5
    
    # Determine confidence based on data volume
    if len(posts) >= 20:
        confidence = "high"
    elif len(posts) >= 10:
        confidence = "medium"
    else:
        confidence = "low"
    
    # Get top posts
    top_posts = sorted(posts, key=lambda x: x.get("score", 0), reverse=True)[:5]
    
    # Format top posts for output
    formatted_top_posts = []
    for post in top_posts:
        formatted_top_posts.append({
            "title": post.get("title", "")[:100],  # Truncate long titles
            "score": post.get("score", 0),
            "comments": post.get("num_comments", 0),
            "subreddit": post.get("subreddit", ""),
            "url": post.get("permalink", "")
        })
    
    return {
        "ticker": ticker,
        "sentiment_score": round(weighted_sentiment, 3),
        "post_count": len(posts),
        "avg_score": round(avg_score, 2),
        "avg_comments": round(avg_comments, 2),
        "top_posts": formatted_top_posts,
        "subreddit_breakdown": subreddit_breakdown,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }


# Synchronous wrapper for backwards compatibility
def get_reddit_sentiment_sync(ticker: str, **kwargs) -> Dict[str, Any]:
    """
    Synchronous wrapper for get_reddit_fast
    For use in non-async contexts
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_reddit_fast(ticker, **kwargs))
    finally:
        loop.close()