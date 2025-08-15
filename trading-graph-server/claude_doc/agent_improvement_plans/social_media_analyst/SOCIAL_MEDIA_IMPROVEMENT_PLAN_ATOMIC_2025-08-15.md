# Social Media Analyst - Improvement Plan

## Guiding Principles

**KISS**: Start with simplest working solution, add complexity only when proven necessary
**YAGNI**: Implement only what's needed now, not speculative features
**DRY**: Reuse existing infrastructure, don't duplicate news analyst functionality

## Phase 1: Fix Critical Failures (Week 1)

### Task 1.1: Replace Reddit File-Based System with Live API
**Priority**: CRITICAL (Current implementation reads local files, not live data!)
**Location**: Create `/src/agent/dataflows/reddit_simple.py`

```python
# Subtask 1.1.1: Implement ultrafast Reddit JSON API (no auth needed)
import aiohttp
import asyncio

async def get_reddit_fast(ticker: str) -> dict:
    """Get live Reddit data in <500ms"""
    url = f"https://www.reddit.com/r/wallstreetbets/search.json"
    params = {"q": ticker, "sort": "hot", "limit": 25}
    headers = {"User-Agent": "StockAnalyzer/1.0"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Process posts
                posts = data.get("data", {}).get("children", [])
                return {"ticker": ticker, "posts": len(posts)}
    return {"ticker": ticker, "error": "Failed to fetch"}
```

**Test**: 
```bash
# Should return live Reddit data in <500ms
python -c "import asyncio; from reddit_simple import get_reddit_fast; print(asyncio.run(get_reddit_fast('AAPL')))"
```

### Task 1.2: Implement Basic StockTwits Integration
**Priority**: HIGH
**Location**: `/src/agent/dataflows/interface_new_tools.py`

```python
# Subtask 1.2.1: Replace mock with real API call
async def get_stocktwits_sentiment(ticker: str) -> Dict[str, Any]:
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    
    # Subtask 1.2.2: Add error handling
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Subtask 1.2.3: Extract real sentiment
                    return process_stocktwits_data(data)
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

# Subtask 1.2.4: Process sentiment from messages
def process_stocktwits_data(data):
    messages = data.get("messages", [])
    bullish = sum(1 for m in messages if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bullish")
    bearish = sum(1 for m in messages if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bearish")
    total = len(messages)
    
    return {
        "ticker": data.get("symbol", {}).get("symbol"),
        "sentiment_score": (bullish - bearish) / max(total, 1),
        "bullish_percent": bullish / max(total, 1) * 100,
        "bearish_percent": bearish / max(total, 1) * 100,
        "message_count": total
    }
```

**Test**:
```bash
# Should return real StockTwits data
python -c "import asyncio; from interface_new_tools import get_stocktwits_sentiment; print(asyncio.run(get_stocktwits_sentiment('AAPL')))"
```

### Task 1.3: Implement Twitter Data Gathering (Nitter Approach)
**Priority**: HIGH (Essential social signal source)
**Location**: Create `/src/agent/dataflows/twitter_simple.py`

```python
# Subtask 1.3.1: Implement ultrafast Twitter via Nitter (no auth needed)
import aiohttp
import asyncio
import feedparser
from typing import Dict, List, Any

async def get_twitter_fast(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """Get Twitter data via Nitter in <1 second"""
    
    # Subtask 1.3.2: Try multiple Nitter instances for reliability
    instances = [
        "nitter.net",
        "nitter.privacydev.net",
        "nitter.poast.org"
    ]
    
    for instance in instances:
        try:
            # Search URL for ticker mentions
            url = f"https://{instance}/search/rss"
            params = {
                "q": f"${ticker} OR #{ticker}",
                "f": "tweets"  # Only tweets, not replies
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        return parse_nitter_rss(ticker, content, limit)
        except:
            continue  # Try next instance
    
    return {"ticker": ticker, "sentiment_score": 0.5, "tweet_count": 0}

# Subtask 1.3.3: Parse RSS and calculate sentiment
def parse_nitter_rss(ticker: str, rss_content: str, limit: int) -> Dict:
    """Parse Nitter RSS feed for sentiment analysis"""
    feed = feedparser.parse(rss_content)
    tweets = []
    
    for entry in feed.entries[:limit]:
        tweet = {
            "text": entry.title,
            "author": entry.author.split('@')[1] if '@' in entry.author else entry.author,
            "link": entry.link
        }
        tweets.append(tweet)
    
    # Simple sentiment: count bullish/bearish keywords
    sentiment = calculate_twitter_sentiment(tweets)
    
    return {
        "ticker": ticker,
        "sentiment_score": sentiment,
        "tweet_count": len(tweets),
        "top_tweets": tweets[:5]
    }

# Subtask 1.3.4: Basic sentiment scoring
def calculate_twitter_sentiment(tweets: List[Dict]) -> float:
    bullish_words = ["buy", "moon", "bull", "long", "calls", "rocket", "green"]
    bearish_words = ["sell", "crash", "bear", "short", "puts", "dump", "red"]
    
    bullish_count = 0
    bearish_count = 0
    
    for tweet in tweets:
        text = tweet["text"].lower()
        bullish_count += sum(1 for word in bullish_words if word in text)
        bearish_count += sum(1 for word in bearish_words if word in text)
    
    total = bullish_count + bearish_count
    if total == 0:
        return 0.5  # Neutral
    
    return bullish_count / total
```

**Test**:
```bash
# Should return Twitter data in <1 second
python -c "import asyncio; from twitter_simple import get_twitter_fast; print(asyncio.run(get_twitter_fast('AAPL')))"
```

### Task 1.4: Remove News Tools from Social Analyst
**Priority**: HIGH
**Location**: `/src/agent/factories/toolkit_factory.py`

```python
# Subtask 1.4.1: Remove news-related tools
def create_social_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
    allowed_tools = [
        # Social media only - no news
        "get_reddit_stock_info",      # Reddit discussions
        "get_stocktwits_sentiment",   # StockTwits sentiment
        "get_twitter_mentions",        # Twitter sentiment (new!)
        # REMOVE: "get_stock_news_openai" - belongs to news analyst
    ]
```

**Test**:
```python
# Verify social toolkit has no news tools
toolkit = create_social_toolkit(base_toolkit)
assert "get_stock_news_openai" not in toolkit.get_available_tools()
assert "get_twitter_mentions" in toolkit.get_available_tools()
```

## Phase 2: Enhance Core Functionality (Week 2)

### Task 2.1: Implement Simple Caching
**Priority**: MEDIUM
**Location**: Create `/src/agent/utils/simple_cache.py`

```python
# Subtask 2.1.1: Create simple TTL cache
from datetime import datetime, timedelta

class SimpleCache:
    def __init__(self):
        self.cache = {}
    
    # Subtask 2.1.2: Get with expiry check
    def get(self, key: str):
        if key in self.cache:
            entry = self.cache[key]
            if entry["expires"] > datetime.now():
                return entry["value"]
        return None
    
    # Subtask 2.1.3: Set with TTL
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self.cache[key] = {
            "value": value,
            "expires": datetime.now() + timedelta(seconds=ttl_seconds)
        }

# Subtask 2.1.4: Apply cache to all social sources
# Reddit: 5-minute TTL (updates slowly)
# Twitter: 3-minute TTL (real-time nature)
# StockTwits: 5-minute TTL (moderate update frequency)
```

**Test**:
```python
cache = SimpleCache()
cache.set("test", "value", 1)
assert cache.get("test") == "value"
time.sleep(2)
assert cache.get("test") is None
```

### Task 2.2: Add Rate Limiting
**Priority**: MEDIUM
**Location**: `/src/agent/utils/rate_limiter.py`

```python
# Subtask 2.2.1: Simple rate limiter
import time

class RateLimiter:
    def __init__(self, calls_per_second: float):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
    
    # Subtask 2.2.2: Wait if needed
    def acquire(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()
```

**Test**:
```python
limiter = RateLimiter(2)  # 2 calls per second
start = time.time()
for _ in range(4):
    limiter.acquire()
elapsed = time.time() - start
assert 1.5 <= elapsed <= 2.5  # Should take ~2 seconds
```

### Task 2.3: Improve Prompt Engineering
**Priority**: HIGH
**Location**: `/src/agent/analysts/social_media_analyst.py`

```python
# Subtask 2.3.1: Create focused social media prompt
system_message = """
You are a Social Media Sentiment Analyst for {ticker}.

YOUR ROLE: Analyze social media discussions (Reddit, Twitter, StockTwits) to gauge retail investor sentiment.
NOT YOUR ROLE: News analysis (handled by News Analyst).

WORKFLOW:
1. Call get_twitter_mentions for Twitter sentiment
2. Call get_stocktwits_sentiment for StockTwits data
3. Call get_reddit_stock_info for Reddit discussions  
4. Analyze sentiment patterns across all platforms
5. Generate trading insights from combined social signals

OUTPUT REQUIREMENTS:
SENTIMENT SCORE: [-1 to +1] where -1=bearish, 0=neutral, +1=bullish
CONFIDENCE: [Low/Medium/High] based on data volume and consensus
TREND: [Rising/Falling/Stable] sentiment momentum
KEY INSIGHTS: Top 3 findings from social discussions
SIGNAL: [BUY/SELL/HOLD] with brief rationale

Focus on social sentiment only. Do not analyze news articles.
"""
```

**Test**:
```python
# Verify prompt doesn't mention news
assert "news" not in system_message.lower() or "not your role" in system_message.lower()
```

## Phase 3: Add Basic Reddit Alternative (Week 3)

### Task 3.1: Implement Reddit Web API Fallback
**Priority**: LOW (only if API fails)
**Location**: `/src/agent/dataflows/reddit_fallback.py`

```python
# Subtask 3.1.1: Simple Reddit JSON endpoint
async def get_reddit_simple(ticker: str):
    # Reddit provides JSON by adding .json to URLs
    url = f"https://www.reddit.com/r/stocks/search.json?q={ticker}&limit=25&sort=hot"
    
    # Subtask 3.1.2: Parse JSON response
    async with aiohttp.ClientSession() as session:
        headers = {"User-Agent": "StockAnalyzer/1.0"}
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return parse_reddit_json(data)
    return {"error": "Failed to fetch Reddit data"}
```

**Test**:
```python
result = asyncio.run(get_reddit_simple("AAPL"))
assert "error" not in result or len(result.get("posts", [])) > 0
```

## Phase 4: Integration Testing (Week 4)

### Task 4.1: End-to-End Testing
**Priority**: HIGH
**Location**: `/tests/test_social_analyst.py`

```python
# Subtask 4.1.1: Test complete workflow
async def test_social_analyst_workflow():
    # Create analyst
    analyst = create_social_media_analyst(llm, toolkit)
    
    # Test with real ticker
    state = {
        "company_of_interest": "AAPL",
        "trade_date": "2024-01-15",
        "social_messages": []
    }
    
    # Run analyst
    result = await analyst(state)
    
    # Verify output
    assert "sentiment_report" in result
    assert result["sentiment_report"] != ""
    assert "AAPL" in result["sentiment_report"]
```

### Task 4.2: Performance Benchmarking
**Priority**: MEDIUM

```python
# Subtask 4.2.1: Measure execution time
async def benchmark_social_tools():
    start = time.time()
    
    # Run all tools in parallel for best performance
    import asyncio
    tasks = [
        get_twitter_fast("AAPL"),
        get_stocktwits_sentiment("AAPL"),
        get_reddit_stock_info("AAPL", "2024-01-15")
    ]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    assert elapsed < 20  # Should complete within 20 seconds
    
    # Verify all sources returned data
    assert all(r is not None for r in results)
```

## Success Metrics

| Metric | Current | Week 1 | Week 2 | Week 4 |
|--------|---------|--------|--------|--------|
| Working Tools | 0 | 3 | 3 | 3+ |
| Real Data Sources | 0 | 3 | 3 | 3 |
| - Reddit | No | Yes | Yes | Yes |
| - StockTwits | No | Yes | Yes | Yes |
| - Twitter | No | Yes | Yes | Yes |
| Execution Time | N/A | <30s | <20s | <15s |
| Cache Hit Rate | 0% | 0% | 30% | 50% |
| Error Rate | 100% | <20% | <10% | <5% |

## Testing Commands

```bash
# Week 1: Test basic functionality
pytest tests/test_social_tools.py::test_reddit_real_data
pytest tests/test_social_tools.py::test_stocktwits_real_data
pytest tests/test_social_tools.py::test_twitter_nitter_data

# Quick Twitter test
python -c "import asyncio; from twitter_simple import get_twitter_fast; print(asyncio.run(get_twitter_fast('AAPL')))"

# Week 2: Test performance
pytest tests/test_social_tools.py::test_caching
pytest tests/test_social_tools.py::test_rate_limiting

# Week 4: Integration tests
pytest tests/test_social_analyst.py::test_full_workflow
pytest tests/test_social_analyst.py::test_performance_benchmark
pytest tests/test_social_analyst.py::test_all_sources_integration
```

## Rollback Plan

If any phase fails:
1. Keep working components (don't break what works)
2. Revert to previous version of specific tool
3. Use mock data as fallback (current state)
4. Document failure for next iteration

## Notes

- **NO NEWS TOOLS**: Social analyst focuses on social media only
- **KISS FIRST**: Start with basic API calls, add complexity later
- **TEST EACH STEP**: Every subtask has a test command
- **INCREMENTAL**: Each phase builds on previous success
- **PRODUCTION READY**: Focus on working code, not perfect code