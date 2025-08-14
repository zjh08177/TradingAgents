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


async def get_twitter_alternative_search(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """
    Alternative Twitter search using web scraping techniques
    More reliable than Nitter instances
    """
    try:
        # Use Google search to find recent Twitter mentions
        search_terms = [
            f'site:twitter.com "{ticker}" (buy OR sell OR bullish OR bearish)',
            f'site:twitter.com "${ticker}" sentiment',
            f'"${ticker}" twitter mentions'
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Try to get recent Twitter sentiment via indirect methods
        async with aiohttp.ClientSession() as session:
            # Search for recent mentions
            for term in search_terms:
                try:
                    # Use DuckDuckGo as it doesn't block as aggressively
                    url = "https://duckduckgo.com/html/"
                    params = {"q": term, "ia": "web"}
                    
                    async with session.get(url, params=params, headers=headers, timeout=8) as resp:
                        if resp.status == 200:
                            content = await resp.text()
                            
                            # Look for Twitter links and sentiment indicators
                            import re
                            twitter_links = re.findall(r'twitter\.com/\w+/status/\d+', content)
                            
                            if twitter_links:
                                # Found Twitter mentions - analyze sentiment from search context
                                sentiment = analyze_search_sentiment(content, ticker)
                                
                                return {
                                    "ticker": ticker,
                                    "sentiment_score": sentiment,
                                    "tweet_count": len(twitter_links),
                                    "top_tweets": [{"text": f"Twitter mention found for ${ticker}", "author": "search_result", "link": f"https://{link}", "published": datetime.now().isoformat()} for link in twitter_links[:5]],
                                    "confidence": "medium" if len(twitter_links) >= 5 else "low",
                                    "source": "twitter_search",
                                    "timestamp": datetime.now().isoformat()
                                }
                except Exception as e:
                    logger.debug(f"Search attempt failed: {e}")
                    continue
        
        return None
        
    except Exception as e:
        logger.error(f"Twitter alternative search failed: {e}")
        return None


async def get_mastodon_sentiment(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """
    Get sentiment from Mastodon instances (decentralized Twitter alternative)
    """
    try:
        # Popular Mastodon instances with finance communities
        instances = [
            "mastodon.social",
            "mstdn.social", 
            "mas.to",
            "fosstodon.org"
        ]
        
        headers = {
            "User-Agent": "StockAnalyzer/1.0",
            "Accept": "application/json"
        }
        
        for instance in instances:
            try:
                # Search for ticker mentions on this instance
                url = f"https://{instance}/api/v2/search"
                params = {
                    "q": f"${ticker} OR #{ticker}",
                    "type": "statuses",
                    "limit": min(limit, 40)
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers, timeout=6) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            statuses = data.get("statuses", [])
                            
                            if statuses:
                                # Process Mastodon posts
                                processed_posts = []
                                for status in statuses[:limit]:
                                    processed_posts.append({
                                        "text": status.get("content", "")[:200],
                                        "author": status.get("account", {}).get("username", "unknown"),
                                        "link": status.get("url", ""),
                                        "created_at": status.get("created_at", ""),
                                        "favourites": status.get("favourites_count", 0),
                                        "reblogs": status.get("reblogs_count", 0)
                                    })
                                
                                # Calculate sentiment
                                sentiment = calculate_twitter_sentiment(processed_posts)
                                confidence = "high" if len(processed_posts) >= 10 else "medium" if len(processed_posts) >= 5 else "low"
                                
                                return {
                                    "ticker": ticker,
                                    "sentiment_score": sentiment,
                                    "tweet_count": len(processed_posts),
                                    "top_tweets": processed_posts[:5],
                                    "confidence": confidence,
                                    "source": f"mastodon_{instance}",
                                    "timestamp": datetime.now().isoformat()
                                }
                        
            except Exception as e:
                logger.debug(f"Mastodon instance {instance} failed: {e}")
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Mastodon search failed: {e}")
        return None


def analyze_search_sentiment(content: str, ticker: str) -> float:
    """
    Analyze sentiment from search results content
    """
    content_lower = content.lower()
    
    # Look for sentiment indicators around the ticker
    ticker_contexts = []
    
    # Find sentences mentioning the ticker
    import re
    sentences = re.split(r'[.!?]', content_lower)
    
    for sentence in sentences:
        if ticker.lower() in sentence or f"${ticker.lower()}" in sentence:
            ticker_contexts.append(sentence)
    
    if not ticker_contexts:
        return 0.5  # Neutral if no context found
    
    # Simple sentiment analysis on ticker contexts
    bullish_words = ["buy", "bull", "bullish", "up", "rise", "gain", "strong", "positive", "growth"]
    bearish_words = ["sell", "bear", "bearish", "down", "fall", "loss", "weak", "negative", "decline"]
    
    bullish_count = 0
    bearish_count = 0
    
    combined_context = " ".join(ticker_contexts)
    
    for word in bullish_words:
        bullish_count += combined_context.count(word)
    
    for word in bearish_words:
        bearish_count += combined_context.count(word)
    
    total_sentiment = bullish_count + bearish_count
    
    if total_sentiment == 0:
        return 0.5  # Neutral
    
    return bullish_count / total_sentiment


async def get_twitter_fast(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """
    Get Twitter-like social sentiment data via multiple sources with aggressive timeouts
    
    Primary: Quick Bluesky API (2s timeout)
    Secondary: Fast Mastodon search (2s timeout)  
    Fallback: Intelligent simulation based on market data
    
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
        - source: Data source used (twitter/bluesky/mastodon/simulation)
        - error: Error message if request failed
    """
    
    # Set maximum total time for all attempts to 5 seconds
    import time
    start_time = time.time()
    max_total_time = 5.0
    
    # Try Bluesky first with aggressive 2s timeout
    if time.time() - start_time < max_total_time:
        logger.info(f"🐦 Quick Bluesky attempt for {ticker}")
        try:
            bluesky_result = await asyncio.wait_for(get_bluesky_sentiment(ticker, limit), timeout=2.0)
            if bluesky_result and bluesky_result.get("tweet_count", 0) > 0:
                logger.info(f"✅ Bluesky quick success: {bluesky_result.get('tweet_count')} posts")
                return bluesky_result
        except asyncio.TimeoutError:
            logger.debug(f"⏰ Bluesky timeout for {ticker}")
        except Exception as e:
            logger.debug(f"❌ Bluesky error for {ticker}: {e}")
    
    # Try Mastodon with aggressive 2s timeout
    if time.time() - start_time < max_total_time:
        logger.info(f"🔄 Quick Mastodon attempt for {ticker}")
        try:
            mastodon_result = await asyncio.wait_for(get_mastodon_sentiment(ticker, limit), timeout=2.0)
            if mastodon_result and mastodon_result.get("tweet_count", 0) > 0:
                logger.info(f"✅ Mastodon quick success: {mastodon_result.get('tweet_count')} posts")
                return mastodon_result
        except asyncio.TimeoutError:
            logger.debug(f"⏰ Mastodon timeout for {ticker}")
        except Exception as e:
            logger.debug(f"❌ Mastodon error for {ticker}: {e}")
    
    # All fast sources failed - return empty response instead of simulation
    elapsed = time.time() - start_time
    logger.warning(f"🚨 All quick Twitter sources failed for {ticker} after {elapsed:.1f}s, returning empty response")
    from .empty_response_handler import create_empty_twitter_response
    return create_empty_twitter_response(
        ticker=ticker,
        reason=f"All Twitter alternative sources failed after {elapsed:.1f}s"
    )


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
    Generate intelligent Twitter sentiment simulation when all real sources fail
    Uses deterministic random based on ticker for consistent results
    This is a FALLBACK and should be clearly marked as such
    """
    
    # Create deterministic seed from ticker
    seed = int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16) % 100000
    random.seed(seed)
    
    # Simulate realistic tweet patterns for different assets
    if ticker.upper() in ['BTC', 'ETH', 'CRYPTO', 'DOGE', 'ADA', 'SOL']:
        # Crypto tends to be more volatile sentiment
        tweet_count = random.randint(15, 45)
        base_sentiment = random.uniform(0.3, 0.8)
        confidence = "low"  # Mark as low confidence since it's simulated
    elif ticker.upper() in ['AAPL', 'GOOGL', 'GOOG', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN']:
        # Big tech tends to have more tweets, mixed sentiment
        tweet_count = random.randint(20, 50)  
        base_sentiment = random.uniform(0.4, 0.7)
        confidence = "low"  # Mark as low confidence since it's simulated
    else:
        # Other stocks - moderate activity
        tweet_count = random.randint(8, 25)
        base_sentiment = random.uniform(0.35, 0.65)
        confidence = "low"  # Mark as low confidence since it's simulated
    
    # Generate sample tweets with clear ERROR/MOCK indication
    sample_tweets = [
        {
            "text": f"❌ ERROR: MOCK DATA - ${ticker} sentiment is simulated",
            "author": "MOCK_DATA",
            "link": "https://twitter.com/simulation",
            "published": datetime.now().isoformat(),
            "note": "ERROR: This is MOCK data - Twitter API not available"
        },
        {
            "text": f"❌ ERROR: MOCK DATA - No real Twitter data for ${ticker}",
            "author": "MOCK_DATA", 
            "link": "https://twitter.com/simulation",
            "published": datetime.now().isoformat(),
            "note": "ERROR: This is MOCK data - Twitter API not available"
        }
    ]
    
    logger.error(f"❌ ERROR: Twitter tool using MOCK DATA for {ticker} - marked as FAILURE")
    
    return {
        "ticker": ticker,
        "sentiment_score": round(base_sentiment, 3),
        "tweet_count": tweet_count,
        "top_tweets": sample_tweets,
        "confidence": "low",
        "instances_tried": instances_tried,
        "fallback_mode": True,
        "mock_data": True,  # Explicitly mark as mock
        "error": "FAILURE: Using MOCK data - Twitter API not available",
        "source": "MOCK_SIMULATION",
        "note": "❌ ERROR: MOCK DATA - All Twitter sources failed",
        "warning": "ERROR: This is MOCK data and marked as FAILURE per requirements",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Quick test
    import json
    
    test_ticker = "AAPL"
    print(f"Testing Twitter/Nitter API for {test_ticker}...")
    
    result = get_twitter_sync(test_ticker)
    print(json.dumps(result, indent=2))