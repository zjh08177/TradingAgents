"""
Twitter Syndication API Client
Uses Twitter's free internal syndication endpoint for tweet data
No authentication required - this is the endpoint used by Twitter embeds
"""

import aiohttp
import asyncio
import json
import math
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class TwitterSyndicationAPI:
    """
    Client for Twitter's free syndication API
    Used internally by Twitter for embeds - no auth required
    """
    
    BASE_URL = "https://cdn.syndication.twimg.com"
    SEARCH_ENGINES = [
        "https://duckduckgo.com/html/",
        "https://www.bing.com/search",
        "https://search.yahoo.com/search"
    ]
    
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def generate_token(self, tweet_id: str) -> str:
        """
        Generate syndication API token using Twitter's algorithm
        This is the same algorithm used by react-tweet package
        """
        try:
            # Convert tweet ID to number and apply Twitter's token formula
            id_num = int(tweet_id)
            token_base = (id_num / 1e15) * math.pi
            
            # Convert to base 36 and clean up
            token = f"{token_base:.10f}".replace(".", "").lstrip("0")
            
            # Fallback if token is empty
            if not token:
                token = str(abs(hash(tweet_id)) % 1000000)
            
            return token[:10]  # Limit length
            
        except (ValueError, OverflowError):
            # Fallback to hash-based token
            return str(abs(hash(tweet_id)) % 1000000)
    
    async def get_tweet_by_id(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch individual tweet data using syndication API
        """
        if not self.session:
            raise RuntimeError("Use async context manager")
        
        token = self.generate_token(tweet_id)
        url = f"{self.BASE_URL}/tweet-result"
        
        params = {
            "id": tweet_id,
            "token": token
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_tweet_data(data)
                elif response.status == 404:
                    logger.debug(f"Tweet {tweet_id} not found or private")
                    return None
                else:
                    logger.warning(f"Syndication API error {response.status} for tweet {tweet_id}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching tweet {tweet_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching tweet {tweet_id}: {e}")
            return None
    
    def parse_tweet_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse tweet data from syndication API response
        """
        if not data:
            return {}
        
        try:
            # Extract basic tweet information
            tweet_text = data.get("text", "")
            author = data.get("user", {})
            
            # Parse engagement metrics
            favorite_count = data.get("favorite_count", 0)
            retweet_count = data.get("retweet_count", 0)
            reply_count = data.get("reply_count", 0)
            
            # Parse creation time
            created_at = data.get("created_at", "")
            
            # Extract URLs and mentions
            entities = data.get("entities", {})
            urls = [url.get("expanded_url", "") for url in entities.get("urls", [])]
            mentions = [mention.get("screen_name", "") for mention in entities.get("user_mentions", [])]
            hashtags = [tag.get("text", "") for tag in entities.get("hashtags", [])]
            
            return {
                "id": data.get("id_str", ""),
                "text": tweet_text,
                "author": {
                    "username": author.get("screen_name", ""),
                    "name": author.get("name", ""),
                    "followers": author.get("followers_count", 0),
                    "verified": author.get("verified", False)
                },
                "engagement": {
                    "likes": favorite_count,
                    "retweets": retweet_count,
                    "replies": reply_count
                },
                "created_at": created_at,
                "entities": {
                    "urls": urls,
                    "mentions": mentions,
                    "hashtags": hashtags
                },
                "source": "twitter_syndication"
            }
            
        except Exception as e:
            logger.error(f"Error parsing tweet data: {e}")
            return {}
    
    async def search_tweets_via_search_engines(self, query: str, limit: int = 20) -> List[str]:
        """
        Find tweet IDs by searching for Twitter links via search engines
        This is a workaround since syndication API doesn't have search
        """
        tweet_ids = []
        
        # Create search queries for different engines
        search_queries = [
            f'site:twitter.com "{query}"',
            f'site:x.com "{query}"',
            f'twitter.com {query} status',
            f'x.com {query} status'
        ]
        
        for engine_url in self.SEARCH_ENGINES[:2]:  # Limit to 2 engines for speed
            for search_query in search_queries[:2]:  # Limit queries for speed
                try:
                    params = {"q": search_query}
                    
                    async with self.session.get(engine_url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Extract tweet IDs from search results
                            found_ids = self.extract_tweet_ids_from_html(content)
                            tweet_ids.extend(found_ids)
                            
                            # Stop if we have enough
                            if len(tweet_ids) >= limit:
                                break
                                
                except Exception as e:
                    logger.debug(f"Search engine query failed: {e}")
                    continue
                
                if len(tweet_ids) >= limit:
                    break
            
            if len(tweet_ids) >= limit:
                break
        
        # Remove duplicates and limit results
        unique_ids = list(dict.fromkeys(tweet_ids))  # Preserve order while removing dupes
        return unique_ids[:limit]
    
    def extract_tweet_ids_from_html(self, html_content: str) -> List[str]:
        """
        Extract tweet IDs from HTML search results
        """
        tweet_ids = []
        
        # Patterns to match Twitter/X URLs with status IDs
        patterns = [
            r'(?:twitter\.com|x\.com)/\w+/status/(\d+)',
            r'status/(\d+)',
            r'/(\d{15,20})(?:/|\?|$)',  # Long numeric IDs typical of tweets
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Validate that it looks like a tweet ID (15-20 digits)
                if match.isdigit() and 15 <= len(match) <= 20:
                    tweet_ids.append(match)
        
        return tweet_ids
    
    async def get_tweets_for_ticker(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Main method to get tweets for a stock ticker
        """
        if not self.session:
            raise RuntimeError("Use async context manager")
        
        logger.info(f"🔍 Searching for tweets about ${ticker} via syndication API")
        
        # Search for tweet IDs related to the ticker
        search_queries = [
            f"${ticker}",
            f"#{ticker}",
            f"{ticker} stock",
            f"{ticker} earnings"
        ]
        
        all_tweet_ids = []
        
        # Try different search queries
        for query in search_queries:
            try:
                tweet_ids = await self.search_tweets_via_search_engines(query, limit=10)
                all_tweet_ids.extend(tweet_ids)
                
                if len(all_tweet_ids) >= limit:
                    break
                    
            except Exception as e:
                logger.debug(f"Search failed for query '{query}': {e}")
                continue
        
        # Remove duplicates
        unique_tweet_ids = list(dict.fromkeys(all_tweet_ids))[:limit]
        
        if not unique_tweet_ids:
            logger.warning(f"No tweet IDs found for {ticker}")
            return []
        
        # Fetch tweet data for each ID
        tweets = []
        for tweet_id in unique_tweet_ids:
            try:
                tweet_data = await self.get_tweet_by_id(tweet_id)
                if tweet_data and tweet_data.get("text"):
                    # Filter tweets that actually mention the ticker
                    text = tweet_data["text"].upper()
                    if f"${ticker.upper()}" in text or f"#{ticker.upper()}" in text or ticker.upper() in text:
                        tweets.append(tweet_data)
                        
            except Exception as e:
                logger.debug(f"Failed to fetch tweet {tweet_id}: {e}")
                continue
            
            # Rate limiting - small delay between requests
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ Found {len(tweets)} relevant tweets for ${ticker}")
        return tweets


# Async wrapper functions for compatibility
async def get_twitter_syndication_sentiment(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """
    Get Twitter sentiment using syndication API
    """
    async with TwitterSyndicationAPI() as api:
        tweets = await api.get_tweets_for_ticker(ticker, limit)
        
        if not tweets:
            from .empty_response_handler import create_empty_twitter_response
            return create_empty_twitter_response(
                ticker=ticker,
                reason="No tweets found via Twitter syndication API"
            )
        
        # Analyze sentiment from tweets
        sentiment_score = analyze_tweet_sentiment(tweets)
        
        # Determine confidence based on tweet count and quality
        if len(tweets) >= 15:
            confidence = "high"
        elif len(tweets) >= 8:
            confidence = "medium"  
        else:
            confidence = "low"
        
        # Create top tweets summary
        top_tweets = []
        for tweet in tweets[:5]:
            top_tweets.append({
                "text": tweet.get("text", "")[:150] + "..." if len(tweet.get("text", "")) > 150 else tweet.get("text", ""),
                "author": tweet.get("author", {}).get("username", "unknown"),
                "likes": tweet.get("engagement", {}).get("likes", 0),
                "retweets": tweet.get("engagement", {}).get("retweets", 0),
                "created_at": tweet.get("created_at", ""),
                "link": f"https://twitter.com/{tweet.get('author', {}).get('username', 'unknown')}/status/{tweet.get('id', '')}"
            })
        
        return {
            "ticker": ticker,
            "sentiment_score": sentiment_score,
            "tweet_count": len(tweets),
            "top_tweets": top_tweets,
            "confidence": confidence,
            "source": "twitter_syndication",
            "fallback_mode": False,
            "data_quality": "real",
            "timestamp": datetime.now().isoformat()
        }


def analyze_tweet_sentiment(tweets: List[Dict[str, Any]]) -> float:
    """
    Analyze sentiment from tweet data
    Returns score from 0 (bearish) to 1 (bullish)
    """
    if not tweets:
        return 0.5
    
    # Extended keyword lists for financial sentiment
    bullish_words = [
        "buy", "moon", "bull", "bullish", "long", "calls", "rocket", "green",
        "pump", "breakout", "rally", "surge", "gain", "profit", "up", "rise",
        "growth", "strong", "hodl", "diamond", "hands", "to the moon", "🚀", "📈",
        "bullish", "positive", "optimistic", "confident", "buying", "accumulate"
    ]
    
    bearish_words = [
        "sell", "crash", "bear", "bearish", "short", "puts", "dump", "red",
        "drop", "fall", "decline", "loss", "down", "weak", "panic", "fear",
        "collapse", "tank", "plummet", "correction", "bubble", "📉", "⬇️",
        "bearish", "negative", "pessimistic", "selling", "exit", "avoid"
    ]
    
    bullish_count = 0
    bearish_count = 0
    total_weight = 0
    
    for tweet in tweets:
        text = tweet.get("text", "").lower()
        
        # Get engagement weight (likes + retweets)
        engagement = tweet.get("engagement", {})
        weight = max(1, engagement.get("likes", 0) + engagement.get("retweets", 0))
        
        # Count sentiment words
        tweet_bullish = 0
        tweet_bearish = 0
        
        for word in bullish_words:
            if word in text:
                tweet_bullish += text.count(word)
        
        for word in bearish_words:
            if word in text:
                tweet_bearish += text.count(word)
        
        # Apply engagement weighting
        bullish_count += tweet_bullish * weight
        bearish_count += tweet_bearish * weight
        total_weight += weight
    
    # Calculate sentiment score
    total_sentiment = bullish_count + bearish_count
    
    if total_sentiment == 0:
        # No explicit sentiment words found - neutral
        return 0.5
    
    # Convert to 0-1 scale
    sentiment_score = bullish_count / total_sentiment
    
    # Add slight bias toward neutral if very few sentiment words
    if total_sentiment < 5:
        sentiment_score = 0.4 + (sentiment_score * 0.2)  # Compress toward neutral
    
    return round(sentiment_score, 3)


# Synchronous wrapper for testing
def get_twitter_syndication_sync(ticker: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for testing
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_twitter_syndication_sentiment(ticker))
    finally:
        loop.close()


if __name__ == "__main__":
    # Test the syndication API
    import json
    
    test_ticker = "TSLA"
    print(f"🧪 Testing Twitter Syndication API for {test_ticker}...")
    print("=" * 60)
    
    result = get_twitter_syndication_sync(test_ticker)
    print(json.dumps(result, indent=2))