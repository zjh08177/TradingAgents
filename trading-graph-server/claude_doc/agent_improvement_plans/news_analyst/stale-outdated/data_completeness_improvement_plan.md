# News Analyst Data Completeness Improvement Plan

## Executive Summary

The current news analyst implementation produces reports that are too short and lack comprehensive data from tool calls. This plan addresses these issues by implementing complete data extraction and structured reporting that captures ALL signals from API responses.

## Current Issues Analysis

### 1. Data Collection Limitations
- **Problem**: Only fetching 2 pages (20 articles) from Serper API
- **Impact**: Missing potentially important news signals
- **Current Code**: `news_analyst_ultra_fast.py:156` - `max_pages=2`

### 2. Over-Summarization in Reports
- **Problem**: Only displaying top 5 headlines with 100-char snippets
- **Impact**: Losing 75%+ of collected data in final report
- **Current Code**: `news_analyst_ultra_fast.py:267-277` - Loop limited to 5 items

### 3. Missing Article Details
- **Problem**: Not including URLs, full snippets, publication dates, source details
- **Impact**: Insufficient information for downstream analysis agents
- **Current Code**: Truncating snippets, omitting URLs and dates

### 4. Inadequate Data Structure
- **Problem**: Report focuses on summary rather than complete data preservation
- **Impact**: Research agents cannot access raw data for detailed analysis
- **Current Structure**: Summary-first approach instead of data-first

## Proposed Solution Architecture

### Phase 1: Enhanced Data Collection

#### 1.1 Increase Data Coverage
```python
# Increase pagination for comprehensive coverage
serper_articles = await getNewsDataSerperAPIWithPagination(
    query_or_company=company,
    max_pages=5,  # Increase from 2 to 5 pages (50 articles)
    config=config
)
```

#### 1.2 Preserve Complete Article Data
- Keep ALL fields from API responses
- No truncation of snippets or summaries
- Maintain original timestamps and metadata

### Phase 2: Comprehensive Report Structure

#### 2.1 New Report Format
```markdown
# 📰 NEWS ANALYSIS REPORT - {COMPANY}

## 📊 EXECUTIVE SUMMARY
- Total Articles: {count}
- Sources: {unique_sources}
- Time Range: {earliest} to {latest}
- Data Quality Score: {score}/100

## 📈 SENTIMENT OVERVIEW
- Positive Signals: {pos_count} articles
- Negative Signals: {neg_count} articles
- Neutral/Mixed: {neutral_count} articles
- Overall Sentiment: {sentiment}
- Confidence: {confidence}

## 📝 COMPLETE NEWS DATA

### 🔥 HIGH-PRIORITY NEWS (Company-Specific)
[Articles directly mentioning company with high-impact keywords]

#### Article 1 of {N}
**Title**: {full_title}
**Source**: {source_name} | **Authority Tier**: {tier}
**Date**: {publication_date}
**URL**: {article_url}
**TLDR**: {auto_generated_summary}
**Full Snippet**: {complete_snippet_no_truncation}
**Keywords**: {extracted_keywords}
**Sentiment**: {article_sentiment}
**Impact Score**: {0-100}

[Repeat for ALL high-priority articles]

### 📰 INDUSTRY & MARKET NEWS
[Articles about sector, competitors, market conditions]

[Same detailed format for each article]

### 📑 ADDITIONAL CONTEXT
[Other relevant articles]

[Same detailed format for each article]

## 🎯 TRADING IMPLICATIONS
- Signal: {signal}
- Rationale: {detailed_rationale}
- Risk Factors: {risks}
- Key Catalysts: {catalysts}

## 📊 RAW DATA APPENDIX
[JSON dump of all article data for downstream processing]
```

### Phase 3: Implementation Details

#### 3.1 Enhanced Data Extraction Function
```python
def extract_complete_article_data(article: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    """Extract and preserve ALL article data"""
    
    # Map fields based on source type
    if source_type == "serper":
        return {
            'title': article.get('title', ''),
            'source': article.get('source', ''),
            'date': article.get('date', ''),
            'url': article.get('link', ''),
            'snippet': article.get('snippet', ''),  # FULL snippet
            'position': article.get('position', 0),
            'imageUrl': article.get('imageUrl', ''),
            # Additional metadata
            'source_type': 'serper',
            'authority_tier': classify_source_authority(article.get('source', '')),
            'relevance_score': calculate_relevance(article, company),
            'sentiment': analyze_article_sentiment(article),
            'tldr': generate_tldr(article),  # NEW: Auto-generate summary
            'keywords': extract_keywords(article),  # NEW: Key terms
        }
    elif source_type == "finnhub":
        return {
            'title': article.get('headline', ''),
            'source': article.get('source', 'Finnhub'),
            'date': format_timestamp(article.get('datetime', 0)),
            'url': article.get('url', ''),
            'snippet': article.get('summary', ''),  # FULL summary
            'category': article.get('category', ''),
            'id': article.get('id', ''),
            # Additional metadata
            'source_type': 'finnhub',
            'authority_tier': 'financial',
            'relevance_score': calculate_relevance(article, company),
            'sentiment': analyze_article_sentiment(article),
            'tldr': generate_tldr(article),
            'keywords': extract_keywords(article),
        }
```

#### 3.2 TLDR Generation
```python
def generate_tldr(article: Dict[str, Any], max_length: int = 150) -> str:
    """Generate concise TLDR for each article"""
    
    # Combine title and snippet
    full_text = f"{article.get('title', '')} {article.get('snippet', '')}"
    
    # Extract key sentences
    sentences = full_text.split('.')
    
    # Priority: First sentence + most relevant sentence
    tldr = sentences[0].strip()
    
    # Add most relevant sentence if space allows
    if len(tldr) < max_length and len(sentences) > 1:
        # Find sentence with most keywords
        relevant_sentence = find_most_relevant_sentence(sentences[1:], company)
        if relevant_sentence:
            tldr += f". {relevant_sentence.strip()}"
    
    # Ensure within length limit
    if len(tldr) > max_length:
        tldr = tldr[:max_length-3] + "..."
    
    return tldr
```

#### 3.3 Complete Report Generation
```python
def generate_comprehensive_news_report(company: str, news_data: Dict[str, Any], current_date: str) -> str:
    """Generate complete news report with ALL data"""
    
    # Process ALL articles with complete data
    all_articles = []
    
    # Extract and enrich Serper articles
    for article in news_data.get("serper_articles", []):
        enriched = extract_complete_article_data(article, "serper")
        all_articles.append(enriched)
    
    # Extract and enrich Finnhub articles
    for article in news_data.get("finnhub_news", []):
        enriched = extract_complete_article_data(article, "finnhub")
        all_articles.append(enriched)
    
    # Sort by relevance and priority
    all_articles.sort(key=lambda x: (
        x['relevance_score'],
        x['authority_tier'],
        x.get('date', '')
    ), reverse=True)
    
    # Categorize articles
    high_priority = [a for a in all_articles if a['relevance_score'] > 70]
    industry_news = [a for a in all_articles if 30 < a['relevance_score'] <= 70]
    context_news = [a for a in all_articles if a['relevance_score'] <= 30]
    
    # Build comprehensive report
    report = build_detailed_report(
        company=company,
        high_priority=high_priority,
        industry_news=industry_news,
        context_news=context_news,
        total_articles=len(all_articles),
        current_date=current_date
    )
    
    # Append raw data for downstream processing
    report += "\n\n## 📊 RAW DATA (JSON)\n```json\n"
    report += json.dumps(all_articles, indent=2, default=str)
    report += "\n```\n"
    
    return report
```

## Implementation Timeline

### Day 1: Data Collection Enhancement
1. **Hour 1-2**: Update pagination to 5 pages
2. **Hour 3-4**: Implement complete data extraction
3. **Hour 5-6**: Add TLDR generation and keyword extraction

### Day 2: Report Structure Overhaul
1. **Hour 1-3**: Implement new comprehensive report format
2. **Hour 4-5**: Add article categorization logic
3. **Hour 6**: Add raw data appendix

### Day 3: Testing & Validation
1. **Hour 1-2**: Test with high-volume tickers
2. **Hour 3-4**: Validate data completeness
3. **Hour 5-6**: Performance optimization

## Success Metrics

### Quantitative Metrics
- **Article Coverage**: 50+ articles per analysis (up from 20)
- **Data Completeness**: 100% of API fields preserved
- **Report Length**: 10,000+ chars (up from 2,000)
- **TLDR Coverage**: Every article has TLDR
- **Source Attribution**: 100% articles with source/date/URL

### Qualitative Metrics
- **Signal Capture**: ALL news signals preserved
- **Downstream Usability**: Research agents have complete data
- **Traceability**: Every claim traceable to source
- **Flexibility**: Raw data available for custom analysis

## Risk Mitigation

### Performance Risks
- **Issue**: Larger reports may increase token usage
- **Mitigation**: Implement smart compression for repeated data
- **Fallback**: Paginate reports if needed

### API Limits
- **Issue**: More API calls may hit rate limits
- **Mitigation**: Implement exponential backoff
- **Fallback**: Cache results for 30 minutes

### Data Quality
- **Issue**: More data may include noise
- **Mitigation**: Implement relevance scoring
- **Fallback**: Priority-based filtering

## Testing Strategy

### Unit Tests
```python
def test_complete_data_extraction():
    """Verify all fields are preserved"""
    
def test_tldr_generation():
    """Verify TLDR quality and length"""
    
def test_report_completeness():
    """Verify all articles appear in report"""
```

### Integration Tests
- Test with AAPL (high volume)
- Test with small-cap stocks (low volume)
- Test with breaking news scenarios
- Test with API failures/partial data

### Validation Checklist
- [ ] All 50 articles appear in report
- [ ] Each article has title, source, date, URL, TLDR
- [ ] Full snippets preserved (no truncation)
- [ ] Raw data appendix is valid JSON
- [ ] Report is structured and readable
- [ ] Trading implications based on ALL data

## Conclusion

This improvement plan transforms the news analyst from a summarizer to a comprehensive data provider. By preserving ALL signals from tool calls and structuring them clearly, we enable downstream agents to perform deeper research while maintaining human readability.

The key principle: **"Collect everything, organize intelligently, summarize thoughtfully, but never discard data."**

## Appendix: Example Enhanced Report

See `example_enhanced_report.md` for a complete example of the new report format with 50+ articles.