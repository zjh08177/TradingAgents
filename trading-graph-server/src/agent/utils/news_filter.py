#!/usr/bin/env python3
"""
Simple news filtering utility to reduce token usage.
Following KISS principle - minimal complexity, maximum benefit.
"""

import json
import re
import logging

logger = logging.getLogger(__name__)


def filter_news_for_llm(news_report: str, max_articles: int = 15) -> str:
    """
    Simple filter: Take top N articles from news report.
    
    The news analyst already returns articles in relevance order
    (Serper API returns by relevance, position preserved).
    
    Args:
        news_report: Raw news report from news analyst
        max_articles: Maximum number of articles to include (default 15)
    
    Returns:
        Filtered news report with top N articles
    """
    try:
        # Extract JSON from report
        json_match = re.search(r'```json\n(.*?)\n```', news_report, re.DOTALL)
        if not json_match:
            logger.debug("No JSON found in news report, returning as-is")
            return news_report
        
        news_data = json.loads(json_match.group(1))
        
        # Simply take first N articles (already ordered by relevance)
        articles = news_data.get('articles', [])
        original_count = len(articles)
        filtered_articles = articles[:max_articles]
        
        # Log the reduction
        reduction = 1 - (len(filtered_articles) / max(1, original_count))
        logger.info(f"📰 News filtering: {original_count} → {len(filtered_articles)} articles ({reduction:.1%} reduction)")
        
        # Rebuild report with filtered articles
        news_data['articles'] = filtered_articles
        news_data['filtered'] = True
        news_data['original_count'] = original_count
        
        # Recreate report structure
        filtered_report = f"""NEWS DATA COLLECTION - {news_data.get('company', 'UNKNOWN')}
================================================================================

COLLECTION METRICS:
- Articles Collected: {len(filtered_articles)} (filtered from {original_count})
- Source: Top results by relevance
- Token Optimization: Active

STRUCTURED DATA:
```json
{json.dumps(news_data, indent=2)}
```
"""
        return filtered_report
        
    except Exception as e:
        logger.warning(f"Failed to filter news report: {e}")
        return news_report


def extract_headlines_and_snippets(news_report: str, max_articles: int = 20) -> str:
    """
    Extract only headlines and short snippets for ultra-light analysis.
    
    Most investment decisions are based on headlines and key facts,
    not full article text. This provides 85%+ token reduction.
    
    Args:
        news_report: Raw news report from news analyst
        max_articles: Maximum number of articles to include (default 20)
    
    Returns:
        Summary report with headlines and snippets only
    """
    try:
        # Extract JSON from report
        json_match = re.search(r'```json\n(.*?)\n```', news_report, re.DOTALL)
        if not json_match:
            logger.debug("No JSON found in news report, returning as-is")
            return news_report
        
        news_data = json.loads(json_match.group(1))
        
        # Create lightweight version
        articles = news_data.get('articles', [])
        original_count = len(articles)
        lightweight = []
        
        for article in articles[:max_articles]:
            lightweight.append({
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'date': article.get('publishedDate', ''),
                'snippet': article.get('snippet', '')[:200]  # First 200 chars
            })
        
        # Log the reduction
        logger.info(f"📰 Headlines extraction: {original_count} articles → {len(lightweight)} headlines")
        
        # Create summary report
        summary_report = f"""NEWS HEADLINES SUMMARY - {news_data.get('company', 'UNKNOWN')}
================================================================================

TOP HEADLINES ({len(lightweight)} articles from {original_count} total):

"""
        for i, article in enumerate(lightweight, 1):
            summary_report += f"""{i}. {article['title']}
   Source: {article['source']} | Date: {article['date']}
   Preview: {article['snippet']}...

"""
        
        return summary_report
        
    except Exception as e:
        logger.warning(f"Failed to extract headlines: {e}")
        return news_report


# Optional: Auto-select based on token budget
def optimize_news_for_token_budget(news_report: str, token_budget: int = 5000) -> str:
    """
    Automatically choose optimization strategy based on token budget.
    
    Simple heuristic:
    - < 3000 tokens: Headlines only
    - 3000-8000 tokens: Top 10 articles  
    - > 8000 tokens: Top 15 articles
    
    Args:
        news_report: Raw news report
        token_budget: Available token budget
    
    Returns:
        Optimized news report
    """
    # Rough estimate: 1 token per 4 characters
    estimated_tokens = len(news_report) // 4
    
    if estimated_tokens <= token_budget:
        logger.info(f"✅ News report within budget ({estimated_tokens} < {token_budget} tokens)")
        return news_report
    
    if token_budget < 3000:
        logger.info(f"⚡ Using headlines mode for tight budget ({token_budget} tokens)")
        return extract_headlines_and_snippets(news_report, max_articles=15)
    elif token_budget < 8000:
        logger.info(f"📊 Using filtered mode for medium budget ({token_budget} tokens)")
        return filter_news_for_llm(news_report, max_articles=10)
    else:
        logger.info(f"📰 Using standard filter for normal budget ({token_budget} tokens)")
        return filter_news_for_llm(news_report, max_articles=15)