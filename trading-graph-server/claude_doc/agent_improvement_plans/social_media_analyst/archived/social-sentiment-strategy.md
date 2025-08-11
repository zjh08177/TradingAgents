# Optimal Social Sentiment Gathering Strategy for Stock Analysis

## Executive Summary

After analyzing the current implementation, I propose a **multi-source aggregation strategy** that prioritizes cost-effectiveness, reliability, and actionable insights. The system should use StockTwits as the primary source (free tier available, finance-focused), complemented by Reddit and news sentiment, with Twitter/X as an optional premium addition.

## Current State Assessment

### Existing Implementation
- **Placeholder Tools**: `get_twitter_mentions` and `get_stocktwits_sentiment` return mock data
- **Reddit Integration**: Disabled due to division by zero error
- **Fallback**: Using `get_stock_news_openai` for general sentiment
- **Architecture**: LangChain tool-based with single API call per tool principle

### Key Issues
1. No actual social media data collection
2. Missing sentiment scoring framework
3. No caching or rate limiting strategy
4. Limited error handling and fallback mechanisms

## Recommended Architecture

### 1. Multi-Source Aggregation Pattern

```python
# Priority-based data sources
SENTIMENT_SOURCES = {
    "tier1": ["stocktwits"],      # Free, finance-focused
    "tier2": ["reddit"],           # Free with proper handling
    "tier3": ["news_sentiment"],   # Existing Serper integration
    "premium": ["twitter"]         # If budget allows
}
```

### 2. Efficient Tool Implementation

```python
from typing import Dict, Any
import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
import aiohttp

class SocialSentimentTools:
    
    @tool
    async def get_stocktwits_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch StockTwits sentiment data with caching
        Single API call principle maintained
        """
        # Check cache first
        cached = await self.cache.get(f"stocktwits:{ticker}")
        if cached and cached['expires'] > datetime.now():
            return cached['data']
        
        # Single API call
        async with aiohttp.ClientSession() as session:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
            async with session.get(url) as response:
                data = await response.json()
                
        # Process sentiment
        result = self._process_stocktwits_data(data)
        
        # Cache with TTL
        await self.cache.set(
            f"stocktwits:{ticker}", 
            result,
            ttl=300  # 5 minutes for active stocks
        )
        
        return result
    
    @tool
    async def get_reddit_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Reddit sentiment with proper error handling
        """
        try:
            # Use PRAW with rate limiting
            posts = await self._fetch_reddit_posts(ticker, limit=100)
            sentiment = self._analyze_reddit_sentiment(posts)
            return sentiment
        except Exception as e:
            logger.error(f"Reddit fetch failed: {e}")
            return self._empty_sentiment_response(ticker, "reddit")
    
    @tool
    async def get_aggregated_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Aggregate sentiment from multiple sources in parallel
        """
        # Parallel fetch from all available sources
        tasks = [
            self.get_stocktwits_sentiment(ticker),
            self.get_reddit_sentiment(ticker),
            self.get_news_sentiment(ticker)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate and weight results
        return self._aggregate_sentiment_scores(results)
```

### 3. Sentiment Scoring Framework

```python
class SentimentScore:
    """Standardized sentiment data structure"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.timestamp = datetime.now().isoformat()
        self.sentiment = {
            "score": 0.0,        # -1 to 1 scale
            "confidence": 0.0,   # 0 to 1
            "volume": 0,         # mention count
            "trend": "stable",   # rising/falling/stable
            "momentum": 0.0      # rate of change
        }
        self.sources = {}
        self.signals = {
            "buy_signal": 0.0,
            "sell_signal": 0.0,
            "hold_signal": 0.0,
            "risk_level": "medium"
        }
        self.metadata = {
            "unusual_activity": False,
            "influencer_mentions": [],
            "viral_posts": [],
            "key_topics": []
        }
```

### 4. API Integration Specifications

#### StockTwits Integration
```python
# Free tier: 200 requests/hour
STOCKTWITS_CONFIG = {
    "base_url": "https://api.stocktwits.com/api/2",
    "rate_limit": 200,
    "window": 3600,  # 1 hour
    "endpoints": {
        "symbol_stream": "/streams/symbol/{ticker}.json",
        "trending": "/trending/symbols.json",
        "sentiment": "/symbol/{ticker}/sentiment.json"
    }
}

async def fetch_stocktwits_data(ticker: str) -> Dict:
    """
    Returns:
    {
        "messages": [...],
        "sentiment": {"bullish": 65, "bearish": 35},
        "volume": {"today": 150, "average": 100}
    }
    """
```

#### Reddit Integration (Fixed)
```python
# Using PRAW with proper error handling
import praw
from prawcore.exceptions import PrawcoreException

REDDIT_CONFIG = {
    "subreddits": ["wallstreetbets", "stocks", "investing", "StockMarket"],
    "post_limit": 100,
    "comment_depth": 2,
    "cache_ttl": 600  # 10 minutes
}

async def fetch_reddit_data(ticker: str) -> Dict:
    """
    Fetch with error handling for division by zero
    """
    try:
        reddit = praw.Reddit(
            client_id=config.reddit_client_id,
            client_secret=config.reddit_secret,
            user_agent="StockSentimentBot/1.0"
        )
        
        posts = []
        for subreddit_name in REDDIT_CONFIG["subreddits"]:
            subreddit = reddit.subreddit(subreddit_name)
            for post in subreddit.search(ticker, limit=25):
                if post.score > 0:  # Avoid division by zero
                    posts.append({
                        "title": post.title,
                        "score": post.score,
                        "comments": post.num_comments,
                        "sentiment": analyze_text_sentiment(post.title + post.selftext)
                    })
        
        return {"posts": posts, "total_mentions": len(posts)}
        
    except PrawcoreException as e:
        logger.error(f"Reddit API error: {e}")
        return {"posts": [], "error": str(e)}
```

#### Twitter/X Integration (Optional Premium)
```python
# Twitter API v2 - Only if budget allows
TWITTER_CONFIG = {
    "bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
    "endpoints": {
        "search": "https://api.twitter.com/2/tweets/search/recent",
        "counts": "https://api.twitter.com/2/tweets/counts/recent"
    },
    "rate_limits": {
        "basic": 10000,     # $100/month
        "pro": 1000000,     # $5000/month
    }
}

async def fetch_twitter_data(ticker: str) -> Dict:
    """
    Premium feature - only activated with valid token
    """
    if not TWITTER_CONFIG["bearer_token"]:
        return {"error": "Twitter API not configured"}
    
    # Implementation for Twitter API v2
    ...
```

### 5. Caching & Optimization Strategy

```python
class SentimentCache:
    """Intelligent caching with volatility-based TTL"""
    
    def __init__(self):
        self.cache = {}
        self.ttl_config = {
            "high_volatility": 60,      # 1 minute
            "medium_volatility": 300,   # 5 minutes
            "low_volatility": 900,      # 15 minutes
        }
    
    async def get_ttl(self, ticker: str) -> int:
        """Dynamic TTL based on stock volatility"""
        volatility = await self.get_volatility_score(ticker)
        if volatility > 0.7:
            return self.ttl_config["high_volatility"]
        elif volatility > 0.3:
            return self.ttl_config["medium_volatility"]
        else:
            return self.ttl_config["low_volatility"]
```

### 6. Rate Limiting & Circuit Breaker

```python
from asyncio import Semaphore
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter with circuit breaker"""
    
    def __init__(self, rate: int, window: int):
        self.rate = rate
        self.window = window
        self.semaphore = Semaphore(rate)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=aiohttp.ClientError
        )
    
    async def acquire(self):
        async with self.circuit_breaker:
            async with self.semaphore:
                yield
                await asyncio.sleep(self.window / self.rate)
```

### 7. Implementation Roadmap

#### Phase 1: StockTwits Integration (Week 1)
- [ ] Implement StockTwits API client
- [ ] Add sentiment processing logic
- [ ] Set up basic caching
- [ ] Create tool wrapper for LangChain

#### Phase 2: Reddit Fix & Integration (Week 2)
- [ ] Fix division by zero error
- [ ] Implement PRAW client with error handling
- [ ] Add Reddit sentiment analyzer
- [ ] Integrate with caching layer

#### Phase 3: Aggregation Layer (Week 3)
- [ ] Build sentiment aggregation engine
- [ ] Implement weighting algorithm
- [ ] Create unified sentiment score
- [ ] Add trend detection

#### Phase 4: Optimization (Week 4)
- [ ] Implement intelligent caching
- [ ] Add rate limiting
- [ ] Set up circuit breakers
- [ ] Performance testing

#### Phase 5: Premium Features (Optional)
- [ ] Twitter/X API integration
- [ ] Advanced sentiment analysis
- [ ] Real-time streaming
- [ ] Machine learning models

## Cost Analysis

| Source | Monthly Cost | Requests/Month | Cost per 1K requests |
|--------|-------------|----------------|---------------------|
| StockTwits | $0 (free tier) | 144,000 | $0 |
| Reddit | $0 | Unlimited* | $0 |
| News (Serper) | $50 | 25,000 | $2 |
| Twitter Basic | $100 | 10,000 | $10 |
| Twitter Pro | $5,000 | 1,000,000 | $5 |

*Reddit has rate limits but no hard monthly cap

## Recommended Configuration

```python
# config.py additions
class SocialSentimentConfig:
    # StockTwits (Primary)
    stocktwits_enabled: bool = True
    stocktwits_rate_limit: int = 200
    
    # Reddit (Secondary)
    reddit_enabled: bool = True
    reddit_client_id: str = Field(default="", env="REDDIT_CLIENT_ID")
    reddit_secret: str = Field(default="", env="REDDIT_SECRET")
    
    # Twitter (Optional Premium)
    twitter_enabled: bool = False
    twitter_bearer_token: str = Field(default="", env="TWITTER_BEARER_TOKEN")
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_default: int = 300
    
    # Aggregation weights
    sentiment_weights: Dict = {
        "stocktwits": 0.4,
        "reddit": 0.3,
        "news": 0.2,
        "twitter": 0.1
    }
```

## Example Usage in Social Media Analyst

```python
async def social_media_analyst_node(state):
    """Enhanced social media analyst with real data"""
    
    ticker = state["company_of_interest"]
    
    # Tools now return real data
    tools = [
        toolkit.get_aggregated_sentiment,  # New aggregated tool
        toolkit.get_stocktwits_sentiment,  # Real StockTwits data
        toolkit.get_reddit_sentiment,      # Fixed Reddit integration
        toolkit.get_news_sentiment         # Existing news tool
    ]
    
    # Agent uses tools to get real sentiment
    prompt = """
    Analyze social sentiment for {ticker} using available tools.
    
    Required Analysis:
    1. Overall sentiment score (-1 to 1)
    2. Sentiment trend (rising/falling/stable)
    3. Volume of mentions
    4. Key topics and concerns
    5. Trading signals based on sentiment
    
    Use get_aggregated_sentiment for comprehensive view.
    """
    
    # ... rest of implementation
```

## Success Metrics

1. **Data Quality**
   - Sentiment accuracy > 70%
   - Source availability > 95%
   - Cache hit rate > 60%

2. **Performance**
   - API response time < 2s
   - Aggregation time < 500ms
   - Tool execution < 5s

3. **Cost Efficiency**
   - Cost per analysis < $0.01
   - API usage within limits
   - Minimal failed requests

## Conclusion

This strategy provides a robust, scalable, and cost-effective approach to gathering social sentiment for stock analysis. By prioritizing free and low-cost sources while maintaining the flexibility to add premium services, the system can deliver valuable insights without breaking the budget.

The implementation follows the existing pattern of single tool = single API call, while adding intelligent caching, error handling, and aggregation to maximize the value of each API interaction.