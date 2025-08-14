# News Analyst Data Completeness - Implementation Guide

## Quick Start

This guide provides specific code changes to implement comprehensive data reporting in the news analyst.

## Code Changes Required

### 1. Update `news_analyst_ultra_fast.py`

#### 1.1 Increase Data Collection (Line 154-158)

**Current Code:**
```python
serper_articles = await getNewsDataSerperAPIWithPagination(
    query_or_company=company,
    max_pages=2,  # Limit to 2 pages for speed
    config=config
)
```

**New Code:**
```python
serper_articles = await getNewsDataSerperAPIWithPagination(
    query_or_company=company,
    max_pages=5,  # Increased to 5 pages for comprehensive coverage (50 articles)
    config=config
)
```

#### 1.2 Fix Data Key Naming (Line 162-163)

**Current Code:**
```python
if serper_articles:
    news_data["serper_news"] = serper_articles  # Wrong key name
```

**New Code:**
```python
if serper_articles:
    news_data["serper_articles"] = serper_articles  # Correct key for validation
```

#### 1.3 Add New Helper Functions (After line 515)

**Add these new functions:**

```python
def generate_article_tldr(article: Dict[str, Any], company: str, max_length: int = 200) -> str:
    """Generate comprehensive TLDR for each article"""
    
    # Get title and snippet/summary
    title = article.get('title') or article.get('headline', '')
    snippet = article.get('snippet') or article.get('summary', '')
    
    # Combine for context
    full_text = f"{title}. {snippet}"
    
    # Clean and split into sentences
    sentences = [s.strip() for s in full_text.split('.') if s.strip()]
    
    if not sentences:
        return "No summary available"
    
    # Take first sentence plus most relevant one
    tldr = sentences[0]
    
    # Find most relevant sentence mentioning company or key terms
    if len(sentences) > 1:
        company_sentences = [s for s in sentences[1:] if company.lower() in s.lower()]
        if company_sentences:
            tldr += f". {company_sentences[0]}"
        elif len(sentences) > 1:
            tldr += f". {sentences[1]}"
    
    # Ensure length limit
    if len(tldr) > max_length:
        tldr = tldr[:max_length-3] + "..."
    
    return tldr


def classify_source_authority(source: str) -> str:
    """Classify news source by authority tier"""
    
    source_lower = source.lower()
    
    # Tier 1 - Highest authority
    tier1 = ['reuters', 'bloomberg', 'wall street journal', 'wsj', 'financial times', 'ft']
    if any(t in source_lower for t in tier1):
        return "Tier 1 (Highest)"
    
    # Tier 2 - High authority  
    tier2 = ['cnbc', 'marketwatch', 'forbes', 'yahoo finance', 'business insider', 'barron']
    if any(t in source_lower for t in tier2):
        return "Tier 2 (High)"
    
    # Tier 3 - Medium authority
    tier3 = ['seeking alpha', 'motley fool', 'investorplace', 'the street']
    if any(t in source_lower for t in tier3):
        return "Tier 3 (Medium)"
    
    return "Tier 4 (Standard)"


def extract_article_keywords(article: Dict[str, Any]) -> List[str]:
    """Extract key terms from article"""
    
    text = f"{article.get('title', '')} {article.get('snippet', '')}".lower()
    
    # Key financial terms to look for
    keywords = []
    
    financial_terms = [
        'earnings', 'revenue', 'profit', 'loss', 'growth', 'decline',
        'upgrade', 'downgrade', 'buy', 'sell', 'hold', 'target',
        'ipo', 'merger', 'acquisition', 'partnership', 'deal',
        'lawsuit', 'investigation', 'regulatory', 'sec', 'fda'
    ]
    
    for term in financial_terms:
        if term in text:
            keywords.append(term)
    
    return keywords[:7]  # Limit to 7 most relevant


def format_article_for_report(article: Dict[str, Any], index: int, company: str) -> List[str]:
    """Format a single article for the comprehensive report"""
    
    lines = []
    
    # Article header
    lines.append(f"#### Article {index}")
    
    # Core information
    lines.append(f"**Title**: {article.get('title', 'No title')}")
    
    source = article.get('source', 'Unknown')
    authority = classify_source_authority(source)
    lines.append(f"**Source**: {source} | **Authority Tier**: {authority}")
    
    lines.append(f"**Date**: {article.get('date', 'N/A')}")
    lines.append(f"**URL**: {article.get('link') or article.get('url', 'N/A')}")
    
    # Generate TLDR
    tldr = generate_article_tldr(article, company)
    lines.append(f"**TLDR**: {tldr}")
    
    # Full snippet - NO TRUNCATION
    snippet = article.get('snippet') or article.get('summary', '')
    lines.append(f"**Full Content**: {snippet}")
    
    # Extract keywords
    keywords = extract_article_keywords(article)
    if keywords:
        lines.append(f"**Keywords**: {', '.join(keywords)}")
    
    # Simple sentiment
    sentiment = analyze_single_article_sentiment(article)
    lines.append(f"**Sentiment**: {sentiment}")
    
    # Calculate impact score
    impact = calculate_article_impact(article, company)
    lines.append(f"**Impact Score**: {impact}/100")
    
    lines.append("")  # Empty line for spacing
    
    return lines


def analyze_single_article_sentiment(article: Dict[str, Any]) -> str:
    """Analyze sentiment of a single article"""
    
    text = f"{article.get('title', '')} {article.get('snippet', '')}".lower()
    
    positive_terms = ['growth', 'profit', 'success', 'beat', 'exceed', 'upgrade', 'buy', 'strong']
    negative_terms = ['loss', 'decline', 'miss', 'concern', 'downgrade', 'sell', 'weak', 'risk']
    
    pos_count = sum(1 for term in positive_terms if term in text)
    neg_count = sum(1 for term in negative_terms if term in text)
    
    if pos_count > neg_count:
        return "POSITIVE" if pos_count > neg_count * 1.5 else "SLIGHTLY POSITIVE"
    elif neg_count > pos_count:
        return "NEGATIVE" if neg_count > pos_count * 1.5 else "SLIGHTLY NEGATIVE"
    else:
        return "NEUTRAL"


def calculate_article_impact(article: Dict[str, Any], company: str) -> int:
    """Calculate impact score for an article (0-100)"""
    
    score = 0
    
    # Title and content
    title = (article.get('title') or '').lower()
    snippet = (article.get('snippet') or '').lower()
    source = (article.get('source') or '').lower()
    
    # Company mention in title is high impact
    if company.lower() in title:
        score += 40
    elif company.lower() in snippet:
        score += 20
    
    # Source authority
    if any(t in source for t in ['reuters', 'bloomberg', 'wsj']):
        score += 20
    elif any(t in source for t in ['cnbc', 'marketwatch']):
        score += 10
    
    # High impact keywords in title
    high_impact = ['earnings', 'revenue', 'merger', 'acquisition', 'lawsuit', 'ceo', 'breakthrough']
    for keyword in high_impact:
        if keyword in title:
            score += 15
            break
    
    # Medium impact keywords
    medium_impact = ['analyst', 'upgrade', 'downgrade', 'price target', 'forecast']
    for keyword in medium_impact:
        if keyword in title:
            score += 10
            break
    
    # Recency (would need actual date parsing)
    # For now, assume first articles are more recent
    position = article.get('position', 10)
    if position <= 3:
        score += 10
    elif position <= 10:
        score += 5
    
    return min(score, 100)  # Cap at 100
```

#### 1.4 Replace Report Generation Function (Lines 221-303)

**Replace entire `generate_news_report` function with:**

```python
def generate_news_report(company: str, news_data: Dict[str, Any], current_date: str) -> str:
    """Generate comprehensive news analysis report with ALL data"""
    
    # Extract article counts
    serper_articles = news_data.get("serper_articles", [])
    finnhub_articles = news_data.get("finnhub_news", [])
    total_articles = len(serper_articles) + len(finnhub_articles)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Start building the comprehensive report
    report_lines = [
        f"# 📰 NEWS ANALYSIS REPORT - {company}",
        f"",
        f"**Generated**: {timestamp}",
        f"**Trade Date**: {current_date}",
        f"**Analysis Version**: 2.0 (Data-Complete)",
        f"",
        f"## 📊 EXECUTIVE SUMMARY",
        f"",
        f"- **Total Articles Analyzed**: {total_articles}",
        f"- **Google News (Serper)**: {len(serper_articles)} articles",
        f"- **Financial News (Finnhub)**: {len(finnhub_articles)} articles",
        f"- **Data Sources**: {news_data['sources_successful']}/{news_data['sources_attempted']} successful",
        f"- **Processing Time**: {news_data['data_fetch_time']:.3f} seconds",
        f""
    ]
    
    if total_articles == 0:
        report_lines.extend([
            "## ⚠️ NO NEWS DATA AVAILABLE",
            "",
            "**IMPACT**: Unable to assess current news sentiment for trading decision.",
            "**RECOMMENDATION**: Proceed with caution - manual news research recommended.",
            "",
            "**TRADING SIGNAL**: NEUTRAL (Insufficient Data)",
            "**CONFIDENCE**: LOW"
        ])
    else:
        # Combine all articles for processing
        all_articles = []
        
        # Process Serper articles
        for idx, article in enumerate(serper_articles):
            article['_source_type'] = 'serper'
            article['_index'] = idx
            all_articles.append(article)
        
        # Process Finnhub articles  
        for idx, article in enumerate(finnhub_articles):
            article['_source_type'] = 'finnhub'
            article['_index'] = idx + len(serper_articles)
            all_articles.append(article)
        
        # Calculate overall sentiment
        sentiment_analysis = analyze_news_sentiment(news_data, company)
        
        # Add sentiment overview
        report_lines.extend([
            "## 📈 SENTIMENT OVERVIEW",
            "",
            f"- **Positive Signals**: {sentiment_analysis['positive_count']} articles",
            f"- **Negative Signals**: {sentiment_analysis['negative_count']} articles", 
            f"- **Neutral/Mixed**: {sentiment_analysis['neutral_count']} articles",
            f"- **Overall Sentiment**: {sentiment_analysis['overall_sentiment']}",
            f"- **Confidence Level**: {sentiment_analysis['confidence']}",
            "",
            "## 📝 COMPLETE NEWS DATA",
            ""
        ])
        
        # Separate high-priority (company-specific) and other news
        high_priority = []
        other_news = []
        
        for article in all_articles:
            title = (article.get('title') or article.get('headline', '')).lower()
            snippet = (article.get('snippet') or article.get('summary', '')).lower()
            
            if company.lower() in title or company.lower() in snippet[:200]:
                high_priority.append(article)
            else:
                other_news.append(article)
        
        # Sort by relevance/recency
        high_priority.sort(key=lambda x: x.get('_index', 999))
        other_news.sort(key=lambda x: x.get('_index', 999))
        
        # Add high-priority news section
        if high_priority:
            report_lines.extend([
                "### 🔥 HIGH-PRIORITY NEWS (Company-Specific)",
                f"*{len(high_priority)} articles directly mentioning {company}*",
                ""
            ])
            
            for idx, article in enumerate(high_priority, 1):
                article_lines = format_article_for_report(article, idx, company)
                report_lines.extend(article_lines)
        
        # Add other news section
        if other_news:
            report_lines.extend([
                "### 📰 INDUSTRY & MARKET NEWS",
                f"*{len(other_news)} related articles*",
                ""
            ])
            
            for idx, article in enumerate(other_news, 1):
                article_lines = format_article_for_report(article, idx + len(high_priority), company)
                report_lines.extend(article_lines)
        
        # Add trading implications
        report_lines.extend([
            "## 🎯 TRADING IMPLICATIONS",
            "",
            f"### Investment Signal: **{sentiment_analysis['trading_signal']}**",
            f"**Confidence Level**: {sentiment_analysis['confidence']}",
            "",
            "### Detailed Rationale:",
            sentiment_analysis['rationale'],
            "",
            f"### Risk Assessment: {sentiment_analysis['risk_level']}",
            "",
            "### Key Observations:",
            f"- Analyzed {total_articles} articles from {news_data['sources_successful']} sources",
            f"- {len(high_priority)} articles directly mention {company}",
            f"- Sentiment distribution: {sentiment_analysis['positive_count']} positive, {sentiment_analysis['negative_count']} negative",
            "",
            "## 📊 RAW DATA (JSON FORMAT)",
            "",
            "```json",
            json.dumps({
                "summary": {
                    "total_articles": total_articles,
                    "company_specific": len(high_priority),
                    "sentiment": sentiment_analysis
                },
                "articles": all_articles
            }, indent=2, default=str)[:10000],  # Limit JSON to 10k chars
            "```",
            "",
            "---",
            "*This report preserves complete data from all news sources for comprehensive analysis.*"
        ])
    
    return "\n".join(report_lines)
```

### 2. Testing the Implementation

Create a test script to validate the changes:

```python
# test_news_completeness.py

import asyncio
from src.agent.analysts.news_analyst_ultra_fast import create_news_analyst_ultra_fast
from src.agent.dataflows.interface import Toolkit

async def test_news_analyst():
    """Test the enhanced news analyst"""
    
    # Create mock toolkit
    toolkit = Toolkit(config={"serper_key": "YOUR_KEY"})
    
    # Create analyst
    analyst = create_news_analyst_ultra_fast(None, toolkit)
    
    # Test state
    state = {
        "company_of_interest": "AAPL",
        "trade_date": "2024-01-14"
    }
    
    # Run analyst
    result = await analyst(state)
    
    # Validate results
    report = result.get("news_report", "")
    
    # Check report length (should be much longer)
    assert len(report) > 5000, f"Report too short: {len(report)} chars"
    
    # Check for complete data sections
    assert "COMPLETE NEWS DATA" in report
    assert "HIGH-PRIORITY NEWS" in report
    assert "RAW DATA" in report
    
    # Check for article details
    assert "**TLDR**:" in report
    assert "**Full Content**:" in report
    assert "**Keywords**:" in report
    
    print(f"✅ Test passed! Report length: {len(report)} chars")
    print(f"✅ All data sections present")
    
    # Save report for review
    with open("test_enhanced_report.md", "w") as f:
        f.write(report)
    print("✅ Report saved to test_enhanced_report.md")

if __name__ == "__main__":
    asyncio.run(test_news_analyst())
```

### 3. Integration Checklist

- [ ] Update `news_analyst_ultra_fast.py` with new functions
- [ ] Increase pagination from 2 to 5 pages
- [ ] Fix data key from "serper_news" to "serper_articles"
- [ ] Replace `generate_news_report` function
- [ ] Add helper functions for TLDR, keywords, authority
- [ ] Test with real ticker (AAPL, TSLA)
- [ ] Verify report length > 5000 characters
- [ ] Confirm all articles appear in report
- [ ] Validate JSON raw data section

### 4. Performance Considerations

The enhanced implementation will:
- Increase API calls from 2 to 5 (3 additional Serper requests)
- Increase report size from ~2KB to ~10-15KB
- Add ~2-3 seconds to processing time
- Provide 150% more data for analysis

### 5. Rollback Plan

If issues occur, revert by:
1. Change `max_pages` back to 2
2. Restore original `generate_news_report` function
3. Remove new helper functions

## Summary

This implementation transforms the news analyst from a summarizer to a comprehensive data provider, ensuring ALL signals from API calls are preserved and presented in a structured, analyzable format.