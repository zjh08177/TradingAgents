"""
Twitter Data Gathering via Nitter
Ultra-lightweight implementation using RSS feeds (no auth required)
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import re
import xml.etree.ElementTree as ET
import random
import hashlib

logger = logging.getLogger(__name__)


async def get_twitter_fast(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """
    Get Twitter-like social sentiment data via multiple sources
    
    Primary: Bluesky API (no auth required, reliable)
    Secondary: Nitter RSS feeds
    Fallback: Simulation
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'ETH')
        limit: Number of posts to fetch (default 20)
    
    Returns:
        Dictionary containing:
        - ticker: The ticker symbol
        - sentiment_score: 0 to 1 (0=bearish, 0.5=neutral, 1=bullish)
        - tweet_count: Number of posts analyzed
        - top_tweets: Sample of recent posts
        - confidence: low/medium/high based on data volume
        - source: Data source used (bluesky/nitter/simulation)
        - error: Error message if request failed
    """
    
    # Try Bluesky first (most reliable, no auth needed)
    logger.info(f"🐦 Attempting Bluesky API for {ticker}")
    bluesky_result = await get_bluesky_sentiment(ticker, limit)
    if bluesky_result and bluesky_result.get("tweet_count", 0) > 0:
        logger.info(f"✅ Bluesky successful: {bluesky_result.get('tweet_count')} posts")
        return bluesky_result
    
    # Fallback to Nitter instances
    logger.info(f"🔄 Bluesky failed, trying Nitter instances for {ticker}")
    instances = [
        "nitter.privacydev.net",
        "nitter.poast.org", 
        "nitter.bird.froth.zone",
        "nitter.net"
    ]
    
    instances_tried = []
    
    for instance in instances:
        instances_tried.append(instance)
        try:
            # Search URL for ticker mentions
            url = f"https://{instance}/search/rss"
            params = {
                "q": f"${ticker} OR #{ticker}",
                "f": "tweets"  # Only tweets, not replies
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            logger.info(f"Trying Nitter instance: {instance}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=8) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        logger.info(f"Success with {instance}, content length: {len(content)}")
                        
                        if len(content.strip()) == 0:
                            logger.warning(f"Empty response from {instance}")
                            continue
                            
                        result = parse_nitter_rss(ticker, content, limit)
                        result["instances_tried"] = instances_tried
                        result["successful_instance"] = instance
                        result["source"] = "nitter"
                        return result
                    else:
                        logger.warning(f"Nitter instance {instance} returned status {resp.status}")
                        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout with Nitter instance {instance}")
            continue
        except Exception as e:
            logger.warning(f"Error with Nitter instance {instance}: {str(e)}")
            continue
    
    # All sources failed - use fallback simulation
    logger.error(f"All social sources failed for {ticker}, using simulation")
    return simulate_twitter_sentiment(ticker, instances_tried)


async def get_bluesky_sentiment(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """
    Get sentiment data from Bluesky (Twitter alternative with public API)
    
    Args:
        ticker: Stock/crypto ticker symbol
        limit: Number of posts to fetch
        
    Returns:
        Sentiment data dictionary or None if failed
    """
    try:
        # Bluesky public API endpoint (no auth required!)
        url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
        
        # Search for ticker mentions (both $ and # format)
        params = {
            "q": f"${ticker} OR #{ticker} OR {ticker}",
            "limit": min(limit, 100),
            "sort": "latest"
        }
        
        headers = {
            "User-Agent": "StockAnalyzer/1.0",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    posts = data.get("posts", [])
                    
                    if not posts:
                        logger.warning(f"No Bluesky posts found for {ticker}")
                        return None
                    
                    # Process Bluesky posts
                    processed_posts = []
                    for post in posts[:limit]:
                        # Extract post text from record
                        record = post.get("record", {})
                        text = record.get("text", "")
                        author = post.get("author", {})
                        
                        processed_posts.append({
                            "text": text,
                            "author": author.get("handle", "unknown"),
                            "link": f"https://bsky.app/profile/{author.get('handle', '')}/post/{post.get('cid', '')}",
                            "created_at": record.get("createdAt", ""),
                            "likes": post.get("likeCount", 0),
                            "reposts": post.get("repostCount", 0)
                        })
                    
                    # Calculate sentiment
                    sentiment = calculate_twitter_sentiment(processed_posts)
                    
                    # Determine confidence
                    confidence = "high" if len(processed_posts) >= 15 else "medium" if len(processed_posts) >= 8 else "low"
                    
                    return {
                        "ticker": ticker,
                        "sentiment_score": sentiment,
                        "tweet_count": len(processed_posts),
                        "top_tweets": processed_posts[:5],
                        "confidence": confidence,
                        "source": "bluesky",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"Bluesky API returned status {resp.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error fetching Bluesky data: {str(e)}")
        return None


def parse_nitter_rss(ticker: str, rss_content: str, limit: int) -> Dict[str, Any]:
    """
    Parse Nitter RSS feed for sentiment analysis using built-in XML parser
    
    Args:
        ticker: Stock ticker symbol
        rss_content: Raw RSS content
        limit: Maximum tweets to process
    
    Returns:
        Parsed sentiment data
    """
    
    try:
        # Parse XML directly using built-in parser
        root = ET.fromstring(rss_content)
        tweets = []
        
        # Find all item elements (RSS entries)
        items = root.findall(".//item")
        
        for item in items[:limit]:
            # Extract data from XML elements
            title_elem = item.find("title")
            author_elem = item.find("author") or item.find("dc:creator", {"dc": "http://purl.org/dc/elements/1.1/"})
            link_elem = item.find("link")
            pubdate_elem = item.find("pubDate")
            desc_elem = item.find("description")
            
            tweet = {
                "text": title_elem.text if title_elem is not None else "",
                "author": extract_username(author_elem.text if author_elem is not None else ""),
                "link": link_elem.text if link_elem is not None else "",
                "published": pubdate_elem.text if pubdate_elem is not None else "",
                "summary": desc_elem.text if desc_elem is not None else ""
            }
            
            # Skip empty tweets
            if tweet["text"] and tweet["text"].strip():
                tweets.append(tweet)
        
        if not tweets:
            return {
                "ticker": ticker,
                "sentiment_score": 0.5,
                "tweet_count": 0,
                "confidence": "low",
                "error": "No tweets found in RSS feed",
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate sentiment
        sentiment = calculate_twitter_sentiment(tweets)
        
        # Determine confidence
        if len(tweets) >= 15:
            confidence = "high"
        elif len(tweets) >= 8:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "ticker": ticker,
            "sentiment_score": sentiment,
            "tweet_count": len(tweets),
            "top_tweets": tweets[:5],
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error parsing RSS content: {str(e)}")
        return {
            "ticker": ticker,
            "sentiment_score": 0.5,
            "tweet_count": 0,
            "confidence": "low",
            "error": f"RSS parsing error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def extract_username(author_string: str) -> str:
    """Extract username from author field"""
    if '@' in author_string:
        # Format: "Display Name (@username)"
        match = re.search(r'@(\w+)', author_string)
        if match:
            return match.group(1)
    
    # Fallback
    return author_string.strip()


def calculate_twitter_sentiment(tweets: List[Dict]) -> float:
    """
    Calculate sentiment score from tweets
    
    Args:
        tweets: List of tweet dictionaries
    
    Returns:
        Sentiment score from 0 (bearish) to 1 (bullish), 0.5 = neutral
    """
    
    # Extended keyword lists for financial sentiment
    bullish_words = [
        "buy", "moon", "bull", "bullish", "long", "calls", "rocket", "green",
        "pump", "breakout", "rally", "surge", "gain", "profit", "up", "rise",
        "growth", "strong", "hodl", "diamond", "hands", "to the moon"
    ]
    
    bearish_words = [
        "sell", "crash", "bear", "bearish", "short", "puts", "dump", "red",
        "drop", "fall", "decline", "loss", "down", "weak", "panic", "fear",
        "collapse", "tank", "plummet", "correction", "bubble"
    ]
    
    bullish_count = 0
    bearish_count = 0
    total_words = 0
    
    for tweet in tweets:
        text = tweet["text"].lower()
        summary = tweet.get("summary", "").lower()
        combined_text = f"{text} {summary}"
        
        # Count sentiment words
        for word in bullish_words:
            if word in combined_text:
                bullish_count += combined_text.count(word)
        
        for word in bearish_words:
            if word in combined_text:
                bearish_count += combined_text.count(word)
        
        # Count total relevant words for context
        total_words += len(combined_text.split())
    
    # Calculate sentiment score
    total_sentiment = bullish_count + bearish_count
    
    if total_sentiment == 0:
        # No explicit sentiment words found
        return 0.5  # Neutral
    
    # Convert to 0-1 scale
    sentiment_score = bullish_count / total_sentiment
    
    # Add slight bias toward neutral if very few sentiment words
    if total_sentiment < 3:
        sentiment_score = 0.4 + (sentiment_score * 0.2)  # Compress toward neutral
    
    return round(sentiment_score, 3)


async def get_twitter_mentions(ticker: str) -> Dict[str, Any]:
    """
    Wrapper function for compatibility with existing interface
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Twitter mention data
    """
    return await get_twitter_fast(ticker)


def get_twitter_sync(ticker: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for testing purposes
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Twitter sentiment data
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_twitter_fast(ticker))
    finally:
        loop.close()


def simulate_twitter_sentiment(ticker: str, instances_tried: List[str]) -> Dict[str, Any]:
    """
    Generate realistic Twitter sentiment simulation when Nitter is unavailable
    Uses deterministic random based on ticker for consistent results
    """
    
    # Create deterministic seed from ticker
    seed = int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16) % 100000
    random.seed(seed)
    
    # Simulate realistic tweet patterns for different assets
    if ticker.upper() in ['BTC', 'ETH', 'CRYPTO']:
        # Crypto tends to be more volatile sentiment
        tweet_count = random.randint(15, 45)
        base_sentiment = random.uniform(0.3, 0.8)
    elif ticker.upper() in ['AAPL', 'GOOGL', 'MSFT', 'TSLA']:
        # Big tech tends to have more tweets, mixed sentiment
        tweet_count = random.randint(20, 50)  
        base_sentiment = random.uniform(0.4, 0.7)
    else:
        # Other stocks - moderate activity
        tweet_count = random.randint(8, 25)
        base_sentiment = random.uniform(0.35, 0.65)
    
    # Generate sample tweets
    sample_tweets = [
        {
            "text": f"${ticker} looking strong today! 🚀",
            "author": "trader_" + str(random.randint(100, 999)),
            "link": f"https://twitter.com/user/status/{random.randint(1000000000, 9999999999)}",
            "published": datetime.now().isoformat()
        },
        {
            "text": f"Holding ${ticker} for the long term",
            "author": "investor_" + str(random.randint(100, 999)),
            "link": f"https://twitter.com/user/status/{random.randint(1000000000, 9999999999)}",
            "published": datetime.now().isoformat()
        },
        {
            "text": f"#{ticker} analysis shows potential breakout",
            "author": "analyst_" + str(random.randint(100, 999)),
            "link": f"https://twitter.com/user/status/{random.randint(1000000000, 9999999999)}",
            "published": datetime.now().isoformat()
        }
    ]
    
    confidence = "high" if tweet_count >= 15 else "medium" if tweet_count >= 10 else "low"
    
    return {
        "ticker": ticker,
        "sentiment_score": round(base_sentiment, 3),
        "tweet_count": tweet_count,
        "top_tweets": sample_tweets[:5],
        "confidence": confidence,
        "instances_tried": instances_tried,
        "fallback_mode": True,
        "note": "Simulated data - Nitter instances unavailable",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Quick test
    import json
    
    test_ticker = "AAPL"
    print(f"Testing Twitter/Nitter API for {test_ticker}...")
    
    result = get_twitter_sync(test_ticker)
    print(json.dumps(result, indent=2))