"""
Social Sentiment Implementation Templates
Ready-to-use code for implementing social sentiment gathering tools
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import json
import os
from langchain.tools import tool
from typing_extensions import Annotated

logger = logging.getLogger(__name__)


# ============================================================================
# STOCKTWITS IMPLEMENTATION
# ============================================================================

class StockTwitsClient:
    """StockTwits API client with rate limiting and caching"""
    
    BASE_URL = "https://api.stocktwits.com/api/2"
    
    def __init__(self):
        self.session = None
        self.rate_limiter = RateLimiter(rate=200, window=3600)  # 200 req/hour
        self.cache = SimpleCache()
    
    async def get_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch StockTwits sentiment for a ticker
        
        Returns:
            {
                "ticker": "AAPL",
                "sentiment": {
                    "score": 0.65,  # -1 to 1
                    "bullish": 65,
                    "bearish": 35
                },
                "volume": 250,
                "trending": true,
                "messages": [...]
            }
        """
        # Check cache
        cache_key = f"stocktwits:{ticker}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for StockTwits {ticker}")
            return cached
        
        async with self.rate_limiter:
            try:
                if not self.session:
                    self.session = aiohttp.ClientSession()
                
                url = f"{self.BASE_URL}/streams/symbol/{ticker}.json"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = self._process_stocktwits_data(ticker, data)
                        
                        # Cache for 5 minutes
                        await self.cache.set(cache_key, result, ttl=300)
                        return result
                    else:
                        logger.error(f"StockTwits API error: {response.status}")
                        return self._empty_response(ticker)
                        
            except Exception as e:
                logger.error(f"StockTwits fetch error: {e}")
                return self._empty_response(ticker)
    
    def _process_stocktwits_data(self, ticker: str, data: Dict) -> Dict[str, Any]:
        """Process raw StockTwits API response"""
        messages = data.get("messages", [])
        
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        
        for msg in messages:
            sentiment = msg.get("entities", {}).get("sentiment", {})
            if sentiment:
                basic = sentiment.get("basic", "").lower()
                if basic == "bullish":
                    bullish_count += 1
                elif basic == "bearish":
                    bearish_count += 1
                else:
                    neutral_count += 1
        
        total = bullish_count + bearish_count + neutral_count
        
        if total > 0:
            bullish_pct = (bullish_count / total) * 100
            bearish_pct = (bearish_count / total) * 100
            # Convert to -1 to 1 scale
            sentiment_score = (bullish_pct - bearish_pct) / 100
        else:
            bullish_pct = bearish_pct = 50
            sentiment_score = 0
        
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "sentiment": {
                "score": round(sentiment_score, 2),
                "bullish": round(bullish_pct, 1),
                "bearish": round(bearish_pct, 1),
                "confidence": min(total / 10, 1.0)  # Confidence based on volume
            },
            "volume": total,
            "trending": data.get("symbol", {}).get("trending", False),
            "messages": [
                {
                    "id": msg.get("id"),
                    "body": msg.get("body"),
                    "created_at": msg.get("created_at"),
                    "sentiment": msg.get("entities", {}).get("sentiment", {}).get("basic")
                }
                for msg in messages[:10]  # Top 10 messages
            ]
        }
    
    def _empty_response(self, ticker: str) -> Dict[str, Any]:
        """Return empty response structure"""
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "sentiment": {
                "score": 0,
                "bullish": 50,
                "bearish": 50,
                "confidence": 0
            },
            "volume": 0,
            "trending": False,
            "messages": [],
            "error": "No data available"
        }
    
    async def close(self):
        """Clean up session"""
        if self.session:
            await self.session.close()


# ============================================================================
# REDDIT IMPLEMENTATION (FIXED)
# ============================================================================

class RedditSentimentClient:
    """Reddit sentiment analyzer with proper error handling"""
    
    SUBREDDITS = ["wallstreetbets", "stocks", "investing", "StockMarket", "options"]
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.cache = SimpleCache()
        self.rate_limiter = RateLimiter(rate=60, window=60)  # 60 req/min
    
    async def get_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch Reddit sentiment for a ticker
        
        Returns structured sentiment data
        """
        # Check cache
        cache_key = f"reddit:{ticker}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for Reddit {ticker}")
            return cached
        
        async with self.rate_limiter:
            try:
                # Use pushshift.io or Reddit API
                posts = await self._fetch_reddit_posts(ticker)
                result = self._analyze_reddit_sentiment(ticker, posts)
                
                # Cache for 10 minutes
                await self.cache.set(cache_key, result, ttl=600)
                return result
                
            except Exception as e:
                logger.error(f"Reddit fetch error: {e}")
                return self._empty_response(ticker)
    
    async def _fetch_reddit_posts(self, ticker: str) -> List[Dict]:
        """Fetch posts mentioning ticker from Reddit"""
        posts = []
        
        # Using pushshift.io as alternative (no auth required)
        async with aiohttp.ClientSession() as session:
            for subreddit in self.SUBREDDITS[:3]:  # Limit to avoid rate limits
                url = f"https://api.pushshift.io/reddit/search/submission"
                params = {
                    "q": ticker,
                    "subreddit": subreddit,
                    "size": 25,
                    "sort": "desc",
                    "sort_type": "score"
                }
                
                try:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            posts.extend(data.get("data", []))
                        await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    logger.warning(f"Failed to fetch from r/{subreddit}: {e}")
        
        return posts
    
    def _analyze_reddit_sentiment(self, ticker: str, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from Reddit posts"""
        from textblob import TextBlob
        
        sentiments = []
        total_score = 0
        total_comments = 0
        
        for post in posts:
            # Avoid division by zero
            if post.get("score", 0) > 0:
                text = f"{post.get('title', '')} {post.get('selftext', '')}"
                
                # Simple sentiment analysis
                blob = TextBlob(text)
                sentiment = blob.sentiment.polarity  # -1 to 1
                
                # Weight by post score
                weight = min(post["score"] / 100, 1.0)
                sentiments.append(sentiment * weight)
                
                total_score += post["score"]
                total_comments += post.get("num_comments", 0)
        
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
        else:
            avg_sentiment = 0
        
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "sentiment": {
                "score": round(avg_sentiment, 2),
                "confidence": min(len(posts) / 50, 1.0),
                "volume": len(posts)
            },
            "metrics": {
                "total_score": total_score,
                "total_comments": total_comments,
                "avg_score": total_score / max(len(posts), 1)
            },
            "top_posts": [
                {
                    "title": p.get("title"),
                    "score": p.get("score"),
                    "comments": p.get("num_comments"),
                    "url": f"https://reddit.com{p.get('permalink', '')}"
                }
                for p in sorted(posts, key=lambda x: x.get("score", 0), reverse=True)[:5]
            ]
        }
    
    def _empty_response(self, ticker: str) -> Dict[str, Any]:
        """Return empty response structure"""
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "sentiment": {
                "score": 0,
                "confidence": 0,
                "volume": 0
            },
            "metrics": {
                "total_score": 0,
                "total_comments": 0,
                "avg_score": 0
            },
            "top_posts": [],
            "error": "No data available"
        }


# ============================================================================
# AGGREGATED SENTIMENT
# ============================================================================

class SentimentAggregator:
    """Aggregate sentiment from multiple sources"""
    
    def __init__(self, stocktwits_client, reddit_client, news_client=None):
        self.stocktwits = stocktwits_client
        self.reddit = reddit_client
        self.news = news_client
        self.weights = {
            "stocktwits": 0.4,
            "reddit": 0.3,
            "news": 0.3
        }
    
    async def get_aggregated_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch and aggregate sentiment from all sources
        
        Returns comprehensive sentiment analysis
        """
        # Parallel fetch from all sources
        tasks = []
        sources = []
        
        if self.stocktwits:
            tasks.append(self.stocktwits.get_sentiment(ticker))
            sources.append("stocktwits")
        
        if self.reddit:
            tasks.append(self.reddit.get_sentiment(ticker))
            sources.append("reddit")
        
        if self.news:
            tasks.append(self.news.get_sentiment(ticker))
            sources.append("news")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        source_data = {}
        weighted_sentiment = 0
        total_weight = 0
        total_volume = 0
        
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {source}: {result}")
                source_data[source] = {"error": str(result)}
            else:
                source_data[source] = result
                
                # Calculate weighted sentiment
                sentiment_score = result.get("sentiment", {}).get("score", 0)
                confidence = result.get("sentiment", {}).get("confidence", 0)
                weight = self.weights.get(source, 0.33) * confidence
                
                weighted_sentiment += sentiment_score * weight
                total_weight += weight
                total_volume += result.get("volume", 0)
        
        # Calculate final sentiment
        if total_weight > 0:
            final_sentiment = weighted_sentiment / total_weight
        else:
            final_sentiment = 0
        
        # Determine trend
        trend = self._calculate_trend(source_data)
        
        # Generate trading signals
        signals = self._generate_signals(final_sentiment, total_volume, trend)
        
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "aggregated_sentiment": {
                "score": round(final_sentiment, 3),
                "confidence": round(total_weight, 2),
                "volume": total_volume,
                "trend": trend
            },
            "sources": source_data,
            "signals": signals,
            "recommendation": self._get_recommendation(signals)
        }
    
    def _calculate_trend(self, source_data: Dict) -> str:
        """Calculate sentiment trend from source data"""
        # Simple trend calculation - can be enhanced
        scores = []
        for source, data in source_data.items():
            if not isinstance(data, dict) or "error" in data:
                continue
            score = data.get("sentiment", {}).get("score", 0)
            scores.append(score)
        
        if not scores:
            return "stable"
        
        avg_score = sum(scores) / len(scores)
        if avg_score > 0.3:
            return "bullish"
        elif avg_score < -0.3:
            return "bearish"
        else:
            return "neutral"
    
    def _generate_signals(self, sentiment: float, volume: int, trend: str) -> Dict[str, Any]:
        """Generate trading signals based on sentiment"""
        signals = {
            "sentiment_signal": "neutral",
            "volume_signal": "normal",
            "risk_level": "medium",
            "confidence": 0
        }
        
        # Sentiment-based signal
        if sentiment > 0.5:
            signals["sentiment_signal"] = "strong_buy"
        elif sentiment > 0.2:
            signals["sentiment_signal"] = "buy"
        elif sentiment < -0.5:
            signals["sentiment_signal"] = "strong_sell"
        elif sentiment < -0.2:
            signals["sentiment_signal"] = "sell"
        else:
            signals["sentiment_signal"] = "hold"
        
        # Volume-based signal
        if volume > 1000:
            signals["volume_signal"] = "high"
        elif volume > 500:
            signals["volume_signal"] = "elevated"
        elif volume < 100:
            signals["volume_signal"] = "low"
        
        # Risk assessment
        if abs(sentiment) > 0.7 and volume > 500:
            signals["risk_level"] = "high"
        elif abs(sentiment) < 0.2 or volume < 50:
            signals["risk_level"] = "low"
        
        # Confidence score
        signals["confidence"] = min(volume / 1000, 1.0) * (1 - abs(sentiment - 0))
        
        return signals
    
    def _get_recommendation(self, signals: Dict) -> str:
        """Generate human-readable recommendation"""
        sentiment_signal = signals.get("sentiment_signal", "neutral")
        volume_signal = signals.get("volume_signal", "normal")
        risk_level = signals.get("risk_level", "medium")
        
        if sentiment_signal in ["strong_buy", "buy"] and volume_signal in ["high", "elevated"]:
            return f"BUY - Positive sentiment with {volume_signal} social activity. Risk: {risk_level}"
        elif sentiment_signal in ["strong_sell", "sell"] and volume_signal in ["high", "elevated"]:
            return f"SELL - Negative sentiment with {volume_signal} social activity. Risk: {risk_level}"
        elif volume_signal == "low":
            return f"HOLD - Low social activity, insufficient data for strong signal. Risk: {risk_level}"
        else:
            return f"HOLD - Mixed signals, monitor for clearer trend. Risk: {risk_level}"


# ============================================================================
# HELPER CLASSES
# ============================================================================

class RateLimiter:
    """Async rate limiter using token bucket algorithm"""
    
    def __init__(self, rate: int, window: int):
        self.rate = rate
        self.window = window
        self.tokens = rate
        self.last_update = datetime.now()
        self.lock = asyncio.Lock()
    
    async def __aenter__(self):
        async with self.lock:
            now = datetime.now()
            elapsed = (now - self.last_update).total_seconds()
            
            # Refill tokens
            self.tokens = min(self.rate, self.tokens + (elapsed * self.rate / self.window))
            self.last_update = now
            
            # Wait if no tokens available
            while self.tokens < 1:
                await asyncio.sleep(self.window / self.rate)
                now = datetime.now()
                elapsed = (now - self.last_update).total_seconds()
                self.tokens = min(self.rate, self.tokens + (elapsed * self.rate / self.window))
                self.last_update = now
            
            self.tokens -= 1
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self):
        self.cache = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if entry["expires"] > datetime.now():
                return entry["value"]
            else:
                del self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL in seconds"""
        self.cache[key] = {
            "value": value,
            "expires": datetime.now() + timedelta(seconds=ttl)
        }
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()


# ============================================================================
# LANGCHAIN TOOL WRAPPERS
# ============================================================================

@tool
async def get_stocktwits_sentiment(
    ticker: Annotated[str, "Stock ticker symbol"]
) -> str:
    """
    Get StockTwits sentiment data for a stock
    
    Returns sentiment score, volume, and trending status
    """
    client = StockTwitsClient()
    try:
        result = await client.get_sentiment(ticker)
        return json.dumps(result, indent=2)
    finally:
        await client.close()


@tool  
async def get_reddit_sentiment(
    ticker: Annotated[str, "Stock ticker symbol"]
) -> str:
    """
    Get Reddit sentiment analysis for a stock
    
    Returns sentiment from multiple investing subreddits
    """
    # Get credentials from environment
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_SECRET", "")
    
    if not client_id or not client_secret:
        return json.dumps({
            "error": "Reddit API credentials not configured",
            "ticker": ticker
        })
    
    client = RedditSentimentClient(client_id, client_secret)
    result = await client.get_sentiment(ticker)
    return json.dumps(result, indent=2)


@tool
async def get_aggregated_social_sentiment(
    ticker: Annotated[str, "Stock ticker symbol"]
) -> str:
    """
    Get aggregated sentiment from multiple social sources
    
    Combines StockTwits, Reddit, and news sentiment
    """
    # Initialize clients
    stocktwits = StockTwitsClient()
    
    reddit = None
    if os.getenv("REDDIT_CLIENT_ID"):
        reddit = RedditSentimentClient(
            os.getenv("REDDIT_CLIENT_ID"),
            os.getenv("REDDIT_SECRET")
        )
    
    # Create aggregator
    aggregator = SentimentAggregator(stocktwits, reddit)
    
    try:
        result = await aggregator.get_aggregated_sentiment(ticker)
        return json.dumps(result, indent=2)
    finally:
        await stocktwits.close()


# ============================================================================
# INTEGRATION WITH EXISTING TOOLKIT
# ============================================================================

def integrate_social_tools(toolkit):
    """
    Add social sentiment tools to existing toolkit
    
    Usage:
        from social_sentiment_implementation import integrate_social_tools
        integrate_social_tools(toolkit)
    """
    # Add new tools to toolkit
    toolkit.get_stocktwits_sentiment = get_stocktwits_sentiment
    toolkit.get_reddit_sentiment = get_reddit_sentiment  
    toolkit.get_aggregated_social_sentiment = get_aggregated_social_sentiment
    
    logger.info("Social sentiment tools integrated successfully")
    return toolkit