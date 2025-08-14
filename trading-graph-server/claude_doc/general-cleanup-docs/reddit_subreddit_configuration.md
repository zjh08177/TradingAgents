# Reddit Subreddit Configuration for Trading Agent

## Overview
The Reddit sentiment tool now uses comprehensive, curated subreddit lists for maximum coverage of trading discussions. The system automatically detects crypto vs stock tickers and queries the appropriate communities.

## Crypto Subreddits (11 communities)

When a crypto ticker is detected (BTC, ETH, etc.), the system queries:

1. **r/CryptoCurrency** - Main crypto subreddit (2.6M members)
2. **r/Bitcoin** - Bitcoin specific discussions (5.8M members)
3. **r/ethereum** - Ethereum ecosystem (2.2M members)
4. **r/BitcoinMarkets** - Bitcoin trading analysis
5. **r/CryptoMarkets** - Crypto trading focused
6. **r/CryptoMoonShots** - High risk crypto plays
7. **r/SatoshiStreetBets** - Crypto version of WSB
8. **r/altcoin** - Alternative cryptocurrencies
9. **r/defi** - DeFi focused discussions
10. **r/ethfinance** - Ethereum finance
11. **r/binance** - Binance exchange users

## Stock Trading Subreddits (10 communities)

When a stock ticker is detected (AAPL, TSLA, etc.), the system queries:

1. **r/stocks** - General stocks discussion (3.1M members)
2. **r/StockMarket** - Market discussion (3.0M members)
3. **r/investing** - Investment strategies (2.2M members)
4. **r/wallstreetbets** - Main WSB community (15.8M members)
5. **r/pennystocks** - Penny stock trading
6. **r/ValueInvesting** - Value investing focus
7. **r/SecurityAnalysis** - Fundamental analysis
8. **r/Daytrading** - Day trading strategies
9. **r/smallstreetbets** - Smaller bets community
10. **r/options** - Options trading

## Ticker Detection

The system maintains a list of known crypto tickers and automatically selects the appropriate subreddit set:

### Currently Detected Crypto Tickers:
```python
crypto_tickers = {
    'BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'DOGE', 'SOL', 'DOT', 'MATIC', 
    'SHIB', 'TRX', 'AVAX', 'UNI', 'ATOM', 'LINK', 'XLM', 'ALGO', 'VET',
    'MANA', 'SAND', 'AXS', 'GALA', 'ENJ', 'CHZ', 'FTM', 'NEAR', 'FLOW',
    'LTC', 'BCH', 'XMR', 'DASH', 'ZEC', 'ETC', 'THETA', 'EGLD', 'XTZ'
}
```

Any ticker not in this list is treated as a stock ticker.

## Performance Optimization

### Batch Processing
- Subreddits are queried in batches of 5 to avoid rate limiting
- 200ms delay between batches for API politeness
- Parallel processing within each batch for speed

### Rate Limits
- Reddit public API: 100 requests/minute without authentication
- Each subreddit search counts as 1 request
- With 11 crypto or 10 stock subreddits, uses ~11% of rate limit per ticker

### Response Times
- Single subreddit: <500ms
- Full crypto scan (11 subreddits): ~2.5 seconds
- Full stock scan (10 subreddits): ~2.2 seconds

## Data Quality Improvements

### Coverage Metrics
- **Crypto tickers**: Up to 275 posts (25 per subreddit × 11 subreddits)
- **Stock tickers**: Up to 250 posts (25 per subreddit × 10 subreddits)
- **Previous coverage**: ~25-50 posts from 3-4 subreddits

### Sentiment Accuracy
The broader coverage provides:
- More representative sentiment sampling
- Detection of trends across different investor communities
- Better signal-to-noise ratio through aggregation
- Community-specific insights (e.g., r/ValueInvesting vs r/wallstreetbets)

## Implementation Files

### Core Files Modified:
1. `/src/agent/dataflows/interface_new_tools.py` - Ticker detection and subreddit selection
2. `/src/agent/dataflows/reddit_simple.py` - Batch processing optimization

### Key Functions:
- `get_reddit_stock_info()` - Main entry point with ticker detection
- `get_reddit_fast()` - Async Reddit fetching with batch processing
- `fetch_subreddit_data()` - Individual subreddit data fetching

## Testing

### Test Commands:
```bash
# Test crypto ticker with 11 subreddits
python -c "import asyncio; from interface_new_tools import get_reddit_stock_info; print(asyncio.run(get_reddit_stock_info('ETH')))"

# Test stock ticker with 10 subreddits
python -c "import asyncio; from interface_new_tools import get_reddit_stock_info; print(asyncio.run(get_reddit_stock_info('AAPL')))"
```

### Expected Results:
- Crypto tickers should show data from crypto-specific subreddits
- Stock tickers should show data from stock trading subreddits
- `subreddit_breakdown` field shows post count per subreddit
- `is_crypto` flag indicates which subreddit set was used

## Future Enhancements

### Planned Improvements:
1. Dynamic ticker detection using exchange APIs
2. Subreddit weighting based on quality/relevance
3. Time-based filtering (hot for day trading, top for long-term)
4. Caching layer for frequently queried tickers
5. Sentiment normalization across different communities

### Potential Additional Subreddits:
- **Crypto**: r/CryptoTechnology, r/CryptoCurrencyTrading, r/ethtrader
- **Stocks**: r/thetagang, r/dividends, r/SPACs, r/CanadianInvestor

## Configuration

The subreddit lists are currently hardcoded but can be easily modified in the `interface_new_tools.py` file. Future versions may externalize this configuration to a JSON file for easier maintenance.

---

*Last Updated: January 11, 2025*
*Reddit API Version: Public JSON API (no authentication required)*