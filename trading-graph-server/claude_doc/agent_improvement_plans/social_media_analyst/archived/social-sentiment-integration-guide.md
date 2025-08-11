# Social Sentiment Integration Guide

## Quick Start Implementation

### Step 1: Environment Setup

Add to `.env`:
```bash
# StockTwits (no API key needed for basic access)
STOCKTWITS_ENABLED=true

# Reddit API (register app at https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_client_id
REDDIT_SECRET=your_client_secret

# Optional: Twitter API v2
TWITTER_BEARER_TOKEN=your_bearer_token  # Only if budget allows
```

### Step 2: Install Dependencies

```bash
pip install aiohttp textblob praw asyncio-throttle
```

### Step 3: Replace Placeholder Implementation

Replace `/trading-graph-server/src/agent/dataflows/interface_new_tools.py`:

```python
# Import the new implementation
from claude_doc.social_sentiment_implementation import (
    get_stocktwits_sentiment,
    get_reddit_sentiment,
    get_aggregated_social_sentiment
)

# The tools are now real implementations instead of placeholders
```

### Step 4: Update Toolkit Factory

Update `/trading-graph-server/src/agent/factories/toolkit_factory.py`:

```python
@staticmethod
def create_social_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
    """Create social media analyst toolkit with real sentiment tools"""
    allowed_tools = [
        # Enhanced social sentiment tools
        "get_aggregated_social_sentiment",  # NEW: Primary aggregated tool
        "get_stocktwits_sentiment",         # FIXED: Real StockTwits data
        "get_reddit_sentiment",              # FIXED: With error handling
        
        # Existing tools
        "get_stock_news_openai",
        "get_google_news",
    ]
    return BaseAnalystToolkit(base_toolkit, allowed_tools)
```

### Step 5: Update Social Media Analyst

Update `/trading-graph-server/src/agent/analysts/social_media_analyst.py`:

```python
def create_social_media_analyst(llm, toolkit):
    @debug_node("Social_Media_Analyst")
    async def social_media_analyst_node(state):
        # ... existing code ...
        
        if toolkit.config["online_tools"]:
            tools = [
                # Primary tool for aggregated sentiment
                toolkit.get_aggregated_social_sentiment,
                
                # Individual source tools
                toolkit.get_stocktwits_sentiment,
                toolkit.get_reddit_sentiment,
                toolkit.get_stock_news_openai,
            ]
        
        # Enhanced system message
        system_message = """
        Expert social media analyst specializing in real-time sentiment analysis.
        
        WORKFLOW:
        1. Use get_aggregated_social_sentiment for comprehensive analysis
        2. Drill down with individual tools for specific insights
        3. Analyze sentiment scores, trends, and trading signals
        4. Generate actionable recommendations
        
        REQUIRED OUTPUT:
        - Overall Sentiment Score: -1 (bearish) to +1 (bullish)
        - Confidence Level: Based on data volume and consistency
        - Trend Direction: Rising/Falling/Stable momentum
        - Key Insights: Notable posts, influencer mentions, viral content
        - Trading Signal: BUY/SELL/HOLD with risk assessment
        """
```

## Testing the Implementation

### Test Script

```python
import asyncio
from trading_graph_server.claude_doc.social_sentiment_implementation import (
    StockTwitsClient,
    RedditSentimentClient,
    SentimentAggregator
)

async def test_sentiment():
    # Test individual sources
    stocktwits = StockTwitsClient()
    result = await stocktwits.get_sentiment("AAPL")
    print(f"StockTwits: {result}")
    
    # Test aggregation
    reddit = RedditSentimentClient("id", "secret")
    aggregator = SentimentAggregator(stocktwits, reddit)
    
    aggregated = await aggregator.get_aggregated_sentiment("AAPL")
    print(f"Aggregated: {aggregated}")
    
    await stocktwits.close()

# Run test
asyncio.run(test_sentiment())
```

## Expected Output Format

```json
{
  "ticker": "AAPL",
  "timestamp": "2024-01-15T10:30:00Z",
  "aggregated_sentiment": {
    "score": 0.65,
    "confidence": 0.85,
    "volume": 1250,
    "trend": "bullish"
  },
  "sources": {
    "stocktwits": {
      "sentiment": {"score": 0.7, "bullish": 70, "bearish": 30},
      "volume": 500,
      "trending": true
    },
    "reddit": {
      "sentiment": {"score": 0.6, "confidence": 0.8},
      "metrics": {"total_score": 5000, "total_comments": 300}
    }
  },
  "signals": {
    "sentiment_signal": "buy",
    "volume_signal": "elevated",
    "risk_level": "medium",
    "confidence": 0.75
  },
  "recommendation": "BUY - Positive sentiment with elevated social activity. Risk: medium"
}
```

## Monitoring & Optimization

### Key Metrics to Track

1. **API Usage**
   - StockTwits: Monitor 200 req/hour limit
   - Reddit: Track rate limiting responses
   - Cache hit rates (target >60%)

2. **Performance**
   - Tool execution time (<5s target)
   - Aggregation latency (<500ms)
   - LLM processing time

3. **Data Quality**
   - Sentiment accuracy vs actual price movement
   - Volume correlation with volatility
   - False signal rate

### Optimization Tips

1. **Caching Strategy**
   - High volatility stocks: 1-2 minute TTL
   - Normal stocks: 5-10 minute TTL
   - After hours: 15-30 minute TTL

2. **Rate Limit Management**
   - Implement exponential backoff
   - Use circuit breakers for failing APIs
   - Prioritize high-volume stocks

3. **Cost Optimization**
   - Start with free tiers (StockTwits, Reddit)
   - Add premium sources only for high-value analysis
   - Monitor cost per analysis

## Troubleshooting

### Common Issues

1. **Reddit Division by Zero**
   - Fixed: Check `post.score > 0` before processing
   - Fallback: Return neutral sentiment if no valid posts

2. **StockTwits Rate Limiting**
   - Solution: Implement token bucket rate limiter
   - Cache aggressively for popular tickers

3. **API Timeouts**
   - Set reasonable timeouts (30s max)
   - Use asyncio.gather with return_exceptions=True
   - Provide partial results if some sources fail

## Production Checklist

- [ ] API keys configured in `.env`
- [ ] Dependencies installed
- [ ] Rate limiters configured
- [ ] Caching enabled with appropriate TTLs
- [ ] Error handling tested
- [ ] Monitoring/logging in place
- [ ] Fallback mechanisms working
- [ ] Performance benchmarks met
- [ ] Cost tracking enabled
- [ ] Documentation updated