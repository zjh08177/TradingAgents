# Revised Approach: Agent-Based Summarization

## Core Principle

**News Analyst Role**: Collect and preserve raw data completely  
**Research/Aggregator Agent Role**: Intelligent summarization and analysis

## Why This Approach is Better

### Current Problem with Hardcoded TLDR
```python
# ❌ WRONG: Hardcoded logic, poor quality
def generate_article_tldr(article, company):
    sentences = text.split('.')
    tldr = sentences[0]  # Just takes first sentence!
    return tldr[:200] + "..."  # Arbitrary truncation
```

### Issues with Hardcoded Approach
1. **No Intelligence**: Simple string manipulation, not real understanding
2. **Lost Context**: May cut off mid-sentence or miss key points
3. **No Adaptation**: Same logic for all article types
4. **Quality Issues**: Often produces meaningless summaries
5. **Maintenance Burden**: Complex rules for edge cases

## Recommended Architecture

### Layer 1: News Analyst (Data Collection)
```python
def generate_news_report(company: str, news_data: Dict[str, Any], current_date: str) -> str:
    """Generate data-complete news report WITHOUT summarization"""
    
    # Focus on complete data preservation
    report_lines = [
        f"# 📰 NEWS DATA COLLECTION - {company}",
        f"Generated: {timestamp}",
        f"Total Articles: {total_articles}",
        "",
        "## 📊 RAW NEWS DATA",
        ""
    ]
    
    # Present COMPLETE articles without summarization
    for idx, article in enumerate(all_articles, 1):
        report_lines.extend([
            f"### Article {idx}",
            f"**Title**: {article.get('title', 'No title')}",
            f"**Source**: {article.get('source', 'Unknown')}",
            f"**Date**: {article.get('date', 'N/A')}",
            f"**URL**: {article.get('url', 'N/A')}",
            f"**Full Content**: {article.get('snippet', '')}",  # COMPLETE, no truncation
            f"**Metadata**: {json.dumps(article.get('metadata', {}))}",
            ""
        ])
    
    # Add structured data for agents
    report_lines.extend([
        "## 📋 STRUCTURED DATA FOR AGENTS",
        "```json",
        json.dumps({
            "company": company,
            "article_count": total_articles,
            "articles": all_articles  # Complete data
        }, indent=2),
        "```"
    ])
    
    return "\n".join(report_lines)
```

### Layer 2: Research/Aggregator Agent (Intelligent Summarization)
```python
# This happens in the aggregator or research agent
async def process_news_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Intelligent processing of raw news data"""
    
    news_report = state.get("news_report", "")
    
    # Extract structured data
    raw_data = extract_json_data(news_report)
    articles = raw_data.get("articles", [])
    
    # Use LLM for intelligent summarization
    summarized_articles = []
    for article in articles:
        # LLM-based summarization with context
        summary = await llm.summarize({
            "title": article["title"],
            "content": article["snippet"],
            "context": f"Analyzing {company} for trading decision",
            "requirements": [
                "Extract key financial implications",
                "Identify sentiment indicators",
                "Note any forward-looking statements",
                "Highlight risk factors"
            ]
        })
        
        summarized_articles.append({
            **article,
            "intelligent_summary": summary,
            "sentiment": await llm.analyze_sentiment(article),
            "relevance": await llm.assess_relevance(article, company),
            "trading_impact": await llm.evaluate_impact(article)
        })
    
    return {
        "processed_news": summarized_articles,
        "overall_analysis": await llm.synthesize(summarized_articles)
    }
```

## Implementation Changes

### 1. Simplify News Analyst (`news_analyst_ultra_fast.py`)

**Remove these functions:**
- ❌ `generate_article_tldr()` 
- ❌ `analyze_single_article_sentiment()`
- ❌ `calculate_article_impact()`
- ❌ `extract_article_keywords()`

**Keep these functions (data-focused):**
- ✅ `gather_news_data()` - Pure data collection
- ✅ `classify_source_authority()` - Factual classification
- ✅ `parse_finnhub_result()` - Data parsing

**Simplified report generation:**
```python
def generate_news_report(company: str, news_data: Dict[str, Any], current_date: str) -> str:
    """Generate data-complete report for agent processing"""
    
    all_articles = []
    
    # Collect Serper articles with metadata
    for article in news_data.get("serper_articles", []):
        all_articles.append({
            "source_api": "serper",
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "date": article.get("date", ""),
            "url": article.get("link", ""),
            "content": article.get("snippet", ""),  # FULL content
            "position": article.get("position", 0),
            "source_authority": classify_source_authority(article.get("source", ""))
        })
    
    # Collect Finnhub articles with metadata
    for article in news_data.get("finnhub_news", []):
        all_articles.append({
            "source_api": "finnhub",
            "title": article.get("headline", ""),
            "source": article.get("source", "Finnhub"),
            "date": format_timestamp(article.get("datetime", 0)),
            "url": article.get("url", ""),
            "content": article.get("summary", ""),  # FULL content
            "category": article.get("category", ""),
            "source_authority": "financial"
        })
    
    # Build simple, data-focused report
    report = f"""# 📰 NEWS DATA COLLECTION - {company}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Trade Date: {current_date}

## 📊 COLLECTION SUMMARY
- Total Articles: {len(all_articles)}
- Serper Articles: {len([a for a in all_articles if a['source_api'] == 'serper'])}
- Finnhub Articles: {len([a for a in all_articles if a['source_api'] == 'finnhub'])}
- Collection Time: {news_data.get('data_fetch_time', 0):.3f}s

## 📝 COMPLETE ARTICLE DATA

"""
    
    # Add all articles without summarization
    for idx, article in enumerate(all_articles, 1):
        report += f"""### Article {idx}
**Title**: {article['title']}
**Source**: {article['source']} (Authority: {article['source_authority']})
**Date**: {article['date']}
**URL**: {article['url']}
**Content**: {article['content']}

"""
    
    # Add structured data for agents
    report += f"""## 🤖 STRUCTURED DATA FOR AGENT PROCESSING

```json
{json.dumps({
    "company": company,
    "collection_date": current_date,
    "total_articles": len(all_articles),
    "articles": all_articles
}, indent=2, default=str)}
```

---
*Raw news data collected. Summarization and analysis to be performed by research agents.*
"""
    
    return report
```

### 2. Enhanced Aggregator Agent

The aggregator or research agent should handle intelligent processing:

```python
# In aggregator or research agent
def process_news_for_final_report(news_data: str, llm) -> str:
    """Intelligent processing of raw news data"""
    
    # Parse structured data
    json_match = re.search(r'```json\n(.*?)\n```', news_data, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group(1))
        articles = data['articles']
        
        # Use LLM for intelligent analysis
        prompt = f"""
        Analyze these {len(articles)} news articles about {data['company']}.
        
        For the TOP 10 most relevant articles, provide:
        1. A concise TLDR (2-3 sentences max)
        2. Trading impact (Positive/Negative/Neutral)
        3. Confidence level
        4. Key takeaways
        
        Then provide an overall synthesis:
        - Overall sentiment
        - Key risks identified
        - Trading recommendation
        - Confidence in recommendation
        
        Articles:
        {json.dumps(articles[:20])}  # Send top 20 for analysis
        """
        
        intelligent_analysis = llm.complete(prompt)
        return intelligent_analysis
```

## Benefits of This Approach

### 1. **Separation of Concerns**
- News Analyst: Data collection expert
- Research Agent: Analysis and summarization expert

### 2. **Better Quality**
- LLM-based summarization > hardcoded rules
- Context-aware summaries
- Adaptive to different article types

### 3. **Flexibility**
- Different agents can process same data differently
- Easy to update summarization logic without touching data collection
- Can experiment with different LLM prompts

### 4. **Efficiency**
- News analyst runs faster (no complex processing)
- Parallel processing possible in aggregator
- Can cache raw data and re-analyze

### 5. **Maintainability**
- Simpler news analyst code
- No complex TLDR generation rules to maintain
- Clear responsibilities

## Migration Path

### Phase 1: Simplify News Analyst
1. Remove all hardcoded analysis functions
2. Focus on complete data collection
3. Output structured JSON

### Phase 2: Enhance Aggregator
1. Add news processing logic
2. Implement LLM-based summarization
3. Generate intelligent insights

### Phase 3: Optimize
1. Cache raw news data
2. Experiment with different prompts
3. A/B test summarization quality

## Example Output Flow

### News Analyst Output (Simple, Complete)
```json
{
  "company": "AAPL",
  "total_articles": 52,
  "articles": [
    {
      "title": "Apple Vision Pro Pre-Orders Exceed 200,000 Units",
      "source": "Reuters",
      "date": "2024-01-14",
      "url": "https://...",
      "content": "[COMPLETE 500+ char article content]",
      "source_authority": "Tier 1"
    }
    // ... 51 more articles with COMPLETE data
  ]
}
```

### Aggregator Processing (Intelligent)
```markdown
## Intelligent News Analysis

### Top Story
**Apple Vision Pro Success** (Reuters, Tier 1)
TLDR: Pre-orders exceeded 200,000 units in first weekend, beating analyst expectations by 33%. Strong indicator of successful AR/VR market entry with implications for services revenue growth.
Impact: POSITIVE (High Confidence)

### Key Risks Identified
1. EU antitrust investigation could result in 10% revenue fine
2. Increased competition in AI from Google and Samsung

### Trading Recommendation
Signal: BUY
Confidence: 82%
Rationale: Strong product momentum and services growth outweigh regulatory risks
```

## Conclusion

By removing hardcoded TLDR generation and letting agents handle intelligent summarization, we achieve:
- **Better quality** through LLM understanding
- **Cleaner architecture** with clear responsibilities  
- **More flexibility** for different analysis needs
- **Easier maintenance** with simpler code

The news analyst becomes a pure data collector, while intelligent agents handle the complex task of understanding and summarizing that data.