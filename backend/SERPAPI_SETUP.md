# SerpAPI Setup Guide

## Overview

The Trading Agents system now supports SerpAPI for significantly faster news retrieval. This replaces the slow web scraping approach with a fast, reliable API service.

## Performance Comparison

- **Web Scraping**: ~130 seconds for 300 articles
- **SerpAPI**: ~2-5 seconds for 300 articles
- **Speed Improvement**: 25-60x faster

## Setup Instructions

### 1. Get SerpAPI Key

1. Visit [SerpAPI](https://serpapi.com/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes 100 searches per month

### 2. Set Environment Variable

Add your SerpAPI key to your environment:

```bash
# Option 1: Export in terminal
export SERPAPI_API_KEY="your_serpapi_key_here"

# Option 2: Add to .env file
echo "SERPAPI_API_KEY=your_serpapi_key_here" >> .env

# Option 3: Add to shell profile (permanent)
echo 'export SERPAPI_API_KEY="your_serpapi_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Verify Setup

Run the test to verify SerpAPI is working:

```bash
python test_serpapi_news.py
```

You should see output like:
```
✅ SerpAPI Key Found: 1234567890...
🚀 Testing SerpAPI for query: AAPL
✅ SerpAPI Results: 100 articles in 2.34s
⚡ Speed Improvement: 56.7x faster with SerpAPI
```

## How It Works

The system automatically detects if a SerpAPI key is available:

1. **With SerpAPI key**: Uses fast SerpAPI service
2. **Without SerpAPI key**: Falls back to web scraping (slow but free)

## Integration

The SerpAPI integration is automatically used in:

- `get_google_news()` function
- News Analyst agent
- All news-related tools

No code changes needed - just set the environment variable!

## API Usage

The system uses the Google News search engine through SerpAPI:

```python
# Automatic usage in get_google_news()
news_data = get_google_news("AAPL", "2025-07-05", 7)

# Direct usage (if needed)
from tradingagents.dataflows.serpapi_utils import getNewsDataSerpAPI
results = getNewsDataSerpAPI("AAPL", "2025-07-01", "2025-07-05")
```

## Error Handling

The system includes robust error handling:

- **Invalid API key**: Falls back to web scraping
- **Rate limiting**: Respects API limits with delays
- **Network errors**: Graceful fallback to alternative methods

## Cost Considerations

- **Free tier**: 100 searches/month
- **Paid plans**: Start at $50/month for 5,000 searches
- **Usage**: Each news query = 1 search
- **Recommendation**: Monitor usage in SerpAPI dashboard

## Troubleshooting

### Common Issues

1. **"SerpAPI key not found"**
   - Check environment variable is set
   - Restart terminal/IDE after setting variable

2. **"SerpAPI Error: Invalid API key"**
   - Verify key is correct
   - Check key hasn't expired

3. **Still slow performance**
   - Verify SerpAPI key is being used (check logs)
   - Test with `test_serpapi_news.py`

### Debug Commands

```bash
# Check if environment variable is set
echo $SERPAPI_API_KEY

# Test SerpAPI directly
python test_serpapi_news.py

# Test integrated news function
python test_news_integration.py
```

## Benefits

✅ **Speed**: 25-60x faster news retrieval  
✅ **Reliability**: Professional API service  
✅ **Fallback**: Automatic fallback to web scraping  
✅ **Easy Setup**: Just set environment variable  
✅ **Cost Effective**: Free tier for testing  
✅ **No Code Changes**: Drop-in replacement  

## Next Steps

1. Sign up for SerpAPI account
2. Set environment variable
3. Test with provided scripts
4. Enjoy faster news analysis! 