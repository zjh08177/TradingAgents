# News Analyst Pure Data Collection - Integration Guide

## Overview
The news analyst has been transformed from an analysis component to a pure data collection service. This guide explains how downstream agents can consume the new data format.

## Data Format

### Report Structure
The news analyst now provides data in two formats:

1. **Human-readable markdown** with raw article listings
2. **Structured JSON** for programmatic consumption

### JSON Schema

```json
{
  "company": "string",      // Stock ticker (e.g., "AAPL", "NVDA")
  "date": "string",         // Trade date (YYYY-MM-DD)
  "total": number,          // Total article count
  "articles": [
    {
      "index": number,      // Article number (1-based)
      "api_source": "string", // "serper" or "finnhub"
      "title": "string",    // Article headline
      "source": "string",   // News source (e.g., "Reuters")
      "date": "string",     // Publication date/time
      "url": "string",      // Article URL
      "full_content": "string", // Complete article text/snippet
      "metadata": {
        // Source-specific metadata
        "position": number,   // For Serper: search position
        "image_url": "string", // For Serper: image URL
        "category": "string", // For Finnhub: news category
        "id": "string"        // For Finnhub: article ID
      }
    }
  ]
}
```

## Consuming the Data

### For LLM Agents

```python
import json
import re

def extract_news_data(news_report):
    """Extract structured data from news report"""
    
    # Extract JSON block from report
    json_match = re.search(r'```json\n(.*?)\n```', news_report, re.DOTALL)
    if not json_match:
        return None
    
    # Parse JSON
    data = json.loads(json_match.group(1))
    
    # Now you have structured data
    return data

def process_for_llm(news_data):
    """Process news data for LLM consumption"""
    
    # Example: Create a summary prompt
    articles = news_data['articles']
    
    prompt = f"""
    Analyze these {len(articles)} news articles for {news_data['company']}:
    
    Articles:
    """
    
    for article in articles[:10]:  # First 10 for context window
        prompt += f"""
        Title: {article['title']}
        Source: {article['source']} ({article['date']})
        Content: {article['full_content'][:500]}
        ---
        """
    
    return prompt
```

### For Data Analysis

```python
def analyze_news_data(news_report):
    """Analyze news data for patterns"""
    
    data = extract_news_data(news_report)
    
    # Source distribution
    source_counts = {}
    for article in data['articles']:
        source = article['source']
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Time distribution
    date_counts = {}
    for article in data['articles']:
        date = article['date']
        date_counts[date] = date_counts.get(date, 0) + 1
    
    # Keyword analysis
    keywords = {}
    for article in data['articles']:
        text = (article['title'] + ' ' + article['full_content']).lower()
        # Extract keywords...
    
    return {
        'total_articles': data['total'],
        'sources': source_counts,
        'dates': date_counts,
        'keywords': keywords
    }
```

### For Sentiment Analysis

```python
def prepare_for_sentiment(news_data):
    """Prepare news for sentiment analysis"""
    
    articles_for_analysis = []
    
    for article in news_data['articles']:
        articles_for_analysis.append({
            'text': article['title'] + ' ' + article['full_content'],
            'source': article['source'],
            'date': article['date'],
            'source_tier': classify_source_tier(article['source'])
        })
    
    return articles_for_analysis

def classify_source_tier(source):
    """Classify news source by authority tier"""
    source_lower = source.lower()
    
    tier_map = {
        "tier1": ["reuters", "bloomberg", "wsj", "wall street journal", "financial times"],
        "tier2": ["cnbc", "marketwatch", "forbes", "yahoo finance", "barron"],
        "tier3": ["seeking alpha", "motley fool", "investorplace"],
    }
    
    for tier, sources in tier_map.items():
        if any(s in source_lower for s in sources):
            return tier
    
    return "tier4"
```

## Integration Examples

### Example 1: Aggregator Agent

```python
class NewsAggregatorAgent:
    """Agent that aggregates news from multiple sources"""
    
    def process_news_report(self, news_report):
        """Process news analyst report"""
        
        # Extract structured data
        data = extract_news_data(news_report)
        
        # Group by source tier
        tier_articles = {
            'tier1': [],
            'tier2': [],
            'tier3': [],
            'tier4': []
        }
        
        for article in data['articles']:
            tier = classify_source_tier(article['source'])
            tier_articles[tier].append(article)
        
        # Create weighted summary
        summary = self.create_weighted_summary(tier_articles)
        
        return summary
    
    def create_weighted_summary(self, tier_articles):
        """Create summary with source weighting"""
        # Tier 1 sources get highest weight
        # Implementation...
        pass
```

### Example 2: Research Agent

```python
class ResearchAgent:
    """Agent that performs deep research"""
    
    async def analyze_news(self, news_report):
        """Analyze news for investment insights"""
        
        data = extract_news_data(news_report)
        
        # Separate by content type
        earnings_articles = []
        product_articles = []
        market_articles = []
        
        for article in data['articles']:
            content = article['title'] + ' ' + article['full_content']
            
            if 'earnings' in content.lower() or 'revenue' in content.lower():
                earnings_articles.append(article)
            elif 'product' in content.lower() or 'launch' in content.lower():
                product_articles.append(article)
            else:
                market_articles.append(article)
        
        # Deep analysis on each category
        insights = {
            'earnings': await self.analyze_earnings(earnings_articles),
            'products': await self.analyze_products(product_articles),
            'market': await self.analyze_market(market_articles)
        }
        
        return insights
```

## Best Practices

### 1. Handle Large Data Volumes
- The report can contain 50+ articles (100KB+ of data)
- Consider pagination or chunking for LLM processing
- Use streaming for very large reports

### 2. Source Quality Filtering
- Use the `classify_source_tier()` function
- Weight tier 1 sources higher than tier 3/4
- Consider recency alongside source quality

### 3. Error Handling
```python
def safe_extract_news_data(news_report):
    """Safely extract news data with error handling"""
    try:
        if not news_report:
            return {'articles': [], 'total': 0}
        
        data = extract_news_data(news_report)
        
        if not data:
            # Fallback to parsing raw text
            return parse_raw_news_report(news_report)
        
        return data
        
    except Exception as e:
        logger.error(f"Failed to extract news data: {e}")
        return {'articles': [], 'total': 0, 'error': str(e)}
```

### 4. Caching Considerations
- News data is time-sensitive
- Cache for max 1 hour for same ticker
- Include timestamp in cache key

## Migration from Old Format

If you have code expecting the old analysis format:

```python
def migrate_old_code(news_report):
    """Adapter for old code expecting analysis"""
    
    # Extract new format data
    data = extract_news_data(news_report)
    
    # Create compatibility layer
    old_format = {
        'sentiment': 'NEUTRAL',  # No longer provided
        'key_headlines': [a['title'] for a in data['articles'][:5]],
        'total_articles': data['total'],
        'recommendation': 'See downstream analysis'  # Removed
    }
    
    return old_format
```

## Performance Considerations

### Data Volume
- Typical report: 50-60 articles
- Report size: 100-150KB
- JSON parsing: <100ms
- Full processing: <1s

### Optimization Tips
1. Parse JSON once and cache result
2. Use generators for large article lists
3. Implement parallel processing for analysis
4. Consider using structured indices for repeated queries

## Troubleshooting

### Common Issues

1. **No JSON block found**
   - Check if report generation completed
   - Verify news APIs returned data
   - Fall back to raw text parsing

2. **Large report size**
   - Implement streaming parser
   - Process in chunks
   - Filter by date/relevance first

3. **Missing fields**
   - Use `.get()` with defaults
   - Validate against schema
   - Log missing fields for debugging

## Conclusion

The new pure data collection format provides:
- **Complete data**: All articles with full content
- **No bias**: No hardcoded analysis or sentiment
- **Flexibility**: Downstream agents control analysis
- **Consistency**: Structured JSON for reliable parsing

This enables more sophisticated and customized analysis by specialized agents while maintaining data integrity and completeness.