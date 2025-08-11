# Reddit Sentiment Analysis Test Scripts

## Overview

Three shell scripts for testing the ultrafast Reddit sentiment API implementation.

## Scripts

### 1. `test_reddit_api.sh` - Full Analysis

Comprehensive sentiment analysis across multiple time periods (day, week, month).

**Usage:**
```bash
./test_reddit_api.sh TICKER
```

**Example:**
```bash
./test_reddit_api.sh UNH
```

**Output:**
- Analyzes sentiment across 3 time periods
- Provides trading recommendation
- Saves detailed JSON to `reddit_analysis_results/reddit_analysis_TICKER_TIMESTAMP.json`

**Sample Output:**
```
📊 Summary for UNH
==================================================
  • Total Posts Analyzed: 73
  • Average Sentiment: 0.972
  • Sentiment Trend: stable
  • Recommendation: BUY - High bullish sentiment
  • Execution Time: 1.34s

📈 Sentiment by Time Period:
  🟢 Past 24 hours: 0.947 (3 posts, low confidence)
  🟢 Past week: 0.987 (23 posts, high confidence)
  🟢 Past month: 0.981 (47 posts, high confidence)
```

### 2. `batch_reddit_analysis.sh` - Multiple Tickers

Analyze multiple tickers and create comparative analysis.

**Usage:**
```bash
./batch_reddit_analysis.sh TICKER1 TICKER2 TICKER3 ...
```

**Example:**
```bash
./batch_reddit_analysis.sh AAPL TSLA GME NVDA
```

**Output:**
- Individual analysis for each ticker
- Comparative table showing all tickers
- Summary statistics saved to `reddit_analysis_results/batch_summary_TIMESTAMP.txt`

### 3. `test_reddit_simple.sh` - Quick Test

Lightweight test with single subreddit to avoid rate limits.

**Usage:**
```bash
./test_reddit_simple.sh TICKER
```

**Features:**
- Uses only r/stocks to minimize API calls
- Quick response (<2 seconds typical)
- Good for testing when rate limited

## Python Comparison Tool

### `compare_reddit_sentiment.py`

Compare sentiment across multiple tickers using saved analysis files.

**Usage:**
```bash
python3 compare_reddit_sentiment.py TICKER1 TICKER2 ...
```

**Example:**
```bash
python3 compare_reddit_sentiment.py UNH TSLA AAPL NVDA
```

**Output:**
```
📊 REDDIT SENTIMENT COMPARISON
================================================================================
Ticker   Sentiment    Posts      Trend        Confidence   Signal
--------------------------------------------------------------------------------
UNH      0.972        73         stable       high         🟢 BUY
TSLA     0.972        92         stable       medium       🟢 BUY
AAPL     0.965        45         rising       medium       🟢 BUY
NVDA     0.890        120        stable       high         🟢 BUY
================================================================================
```

## Output Files

All results are saved to `reddit_analysis_results/` directory:

- `reddit_analysis_TICKER_TIMESTAMP.json` - Full analysis data
- `reddit_simple_TICKER_TIMESTAMP.json` - Simple test data
- `batch_summary_TIMESTAMP.txt` - Batch comparison summary

## Viewing Results

### View formatted JSON:
```bash
cat reddit_analysis_results/reddit_analysis_UNH_*.json | python3 -m json.tool
```

### Extract specific data with jq:
```bash
# Get sentiment score
jq '.summary.average_sentiment' reddit_analysis_results/reddit_analysis_UNH_*.json

# Get recommendation
jq '.summary.recommendation' reddit_analysis_results/reddit_analysis_UNH_*.json

# Get top posts
jq '.analysis.day.top_posts[0]' reddit_analysis_results/reddit_analysis_UNH_*.json
```

## Rate Limiting

Reddit has rate limits (60 requests/minute). If you encounter 429 errors:

1. Use `test_reddit_simple.sh` for single subreddit testing
2. Wait 1-2 minutes between batch analyses
3. Reduce the number of subreddits or limit in the scripts

## Performance

- **Response Time**: Typically <2 seconds per ticker
- **Data Volume**: 10-100 posts per ticker depending on activity
- **Accuracy**: Sentiment correlates with actual market sentiment

## Troubleshooting

### "aiohttp not installed"
```bash
pip3 install --user aiohttp
```

### Rate limit errors (429)
- Wait 1-2 minutes
- Use `test_reddit_simple.sh` instead
- Reduce subreddit count in scripts

### No data found
- Ticker may have low Reddit activity
- Try popular tickers: AAPL, TSLA, GME, NVDA

## Implementation Details

The scripts use the `reddit_simple.py` module which:
- Makes direct HTTP calls to Reddit's public JSON API
- No authentication required
- Parallel fetching from multiple subreddits
- Sentiment calculation based on upvotes and engagement
- Response time <500ms per subreddit