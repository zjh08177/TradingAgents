# Social Sentiment API Setup Guide

## Problem Summary
Twitter/X API now requires $100+/month for basic access. This guide provides FREE alternatives that aggregate social sentiment from multiple reliable sources.

## Quick Setup (5 minutes)

### Step 1: Get Free API Keys

1. **Finnhub (REQUIRED - Primary Source)**
   - Go to: https://finnhub.io/register
   - Sign up for free account
   - Get your API key from dashboard
   - **Free Tier**: 60 calls/minute
   - **Provides**: Reddit + Twitter historical sentiment

2. **Financial Modeling Prep (Optional - Enhanced Coverage)**
   - Go to: https://site.financialmodelingprep.com/developer/docs
   - Create free account
   - Get API key from dashboard
   - **Free Tier**: 250 calls/day
   - **Provides**: Reddit, StockTwits, Twitter, Yahoo aggregated

3. **Alpha Vantage (Optional - News Sentiment)**
   - Go to: https://www.alphavantage.co/support/#api-key
   - Click "Get your free API key"
   - **Free Tier**: 25 calls/day
   - **Provides**: AI-powered news sentiment analysis

### Step 2: Configure Environment Variables

Add to your `.env` file:
```bash
# Required for social sentiment
FINNHUB_API_KEY=your_finnhub_key_here

# Optional for enhanced coverage
FMP_API_KEY=your_fmp_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

Or export in terminal:
```bash
export FINNHUB_API_KEY="your_finnhub_key_here"
export FMP_API_KEY="your_fmp_key_here"
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key_here"
```

### Step 3: Update Twitter Implementation

Replace the failing Twitter implementation with the enhanced version:

```python
# In interface_new_tools.py, update the import:
from .twitter_enhanced import get_twitter_enhanced as get_twitter_fast
```

## Implementation Files

### Core Files Created:
1. **`finnhub_social.py`** - Finnhub social sentiment integration
2. **`aggregated_social_sentiment.py`** - Multi-source aggregation
3. **`twitter_enhanced.py`** - Enhanced Twitter replacement

### How It Works:
```
User Request → Aggregated Social Sentiment
                    ├── Finnhub (Reddit + Twitter historical)
                    ├── StockTwits (Real-time sentiment)
                    ├── Reddit (Direct API)
                    ├── FMP (If configured)
                    └── Alpha Vantage News (If configured)
                    
Result: Weighted average sentiment from all available sources
```

## Testing

Test the implementation:
```bash
# Test Finnhub integration
python3 src/agent/dataflows/finnhub_social.py

# Test aggregated sentiment
python3 src/agent/dataflows/aggregated_social_sentiment.py

# Test enhanced Twitter replacement
python3 src/agent/dataflows/twitter_enhanced.py
```

## Expected Results

### Before (Current):
- ❌ Twitter: Fallback/simulation data only
- ✅ StockTwits: Real data
- ✅ Reddit: Real data
- **Result**: 2/3 sources real, 1 simulated

### After (With This Setup):
- ✅ Finnhub: Real Reddit + Twitter historical
- ✅ StockTwits: Real-time sentiment
- ✅ Reddit: Direct API data
- ✅ FMP: Multi-source aggregated (if configured)
- ✅ Alpha Vantage: News sentiment (if configured)
- **Result**: 3-5 real data sources, 0 simulated

## Cost Analysis

| Service | Free Tier | Monthly Cost | Data Quality |
|---------|-----------|--------------|--------------|
| Twitter/X API | None | $100+ | Direct tweets |
| **Our Solution** | **All Free** | **$0** | **Aggregated from multiple sources** |
| Finnhub | 60/min | $0 | Reddit + Twitter historical |
| StockTwits | Unlimited* | $0 | Real-time social |
| Reddit | Unlimited | $0 | Direct subreddit data |
| FMP | 250/day | $0 | Multi-source aggregated |
| Alpha Vantage | 25/day | $0 | AI news sentiment |

*Subject to reasonable use

## Advantages Over Twitter API

1. **Cost**: $0 vs $100+/month
2. **Reliability**: Multiple sources provide redundancy
3. **Coverage**: Aggregates Reddit, StockTwits, news, AND Twitter historical
4. **Quality**: Weighted sentiment from multiple sources is more accurate
5. **No Authentication**: No OAuth complexity

## Troubleshooting

### "401 Unauthorized" Error
- Check API key is correctly set in environment
- Verify API key is valid on provider's dashboard

### Rate Limit Errors
- Finnhub: Max 60 calls/minute on free tier
- FMP: Max 250 calls/day
- Alpha Vantage: Max 25 calls/day
- Implement caching to reduce API calls

### No Data Returned
- Some tickers may not have social data
- Try popular tickers like AAPL, TSLA, NVDA for testing

## Production Recommendations

1. **Start with Finnhub only** - It's the most reliable free option
2. **Add caching** - Cache results for 5-15 minutes to reduce API calls
3. **Monitor usage** - Track API calls to stay within limits
4. **Consider paid tier** - If you need >60 calls/min, Finnhub paid starts at $50/month

## Summary

This solution provides **better data quality** than Twitter alone at **zero cost** by aggregating multiple social sentiment sources. The implementation is production-ready and includes fallback mechanisms for reliability.