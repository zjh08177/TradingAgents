# News Analyst Improvement Plan — Serper-Exclusive Architecture with Quality Focus

All analysis, architecture, and code must follow the principles in `trading-graph-server/claude_doc/agent_improvement_plans/news_analyst`.

## Role & Scope
- **Role**: Provide comprehensive, accurate, and actionable NEWS analysis. Focus exclusively on news, NOT social sentiment.
- **Source strategy**: Serper API as primary and only source (covers 4,500+ news outlets via Google News), with Finnhub as emergency fallback.
- **Quality focus**: Deep news analysis with comprehensive context, detailed temporal assessment, and news-based trading insights.
- **Clear separation**: Social Media Analyst handles ALL Reddit/social data. News Analyst handles ONLY news sources.

## Current Implementation Analysis

### Working Well
- Graph architecture with separate analyst and tool nodes enables parallel execution
- Serper integration via `get_google_news` provides reliable news data
- Message channel isolation (news_messages) prevents cross-contamination
- Token management and prompt compression infrastructure already in place

### Critical Issues
1. **Tool Call Enforcement**: LLM sometimes fails to call tools on first iteration
2. **Underutilized Pagination**: `getNewsDataSerperAPIWithPagination` exists but not integrated
3. **Limited Coverage**: Single-source approach misses important news from diverse sources
4. **Shallow Analysis**: Current prompts don't encourage deep, comprehensive analysis
5. **Weak Error Recovery**: No robust fallback when primary sources fail

### Architecture Strengths to Preserve
- Analyst/tool node separation for error isolation
- Conditional routing for flexible workflow
- Parallel execution capabilities
- Message validation for OpenAI compliance

## Strategic Architecture Decision: Why Serper-Primary is Optimal

### Deep Analysis Findings

**Serper/Google News Coverage:**
- Aggregates from 4,500+ sources globally
- Includes: Reuters, Bloomberg, WSJ, FT, CNBC, Yahoo Finance, MarketWatch, SEC filings
- Built-in: Deduplication, relevance ranking, freshness scoring, authority weighting
- Supports: Deep pagination (5+ pages = 50+ articles), date filtering, query refinement

**Source Value Assessment:**
- **Serper**: Complete news coverage (4,500+ sources), already deduplicated and ranked ✅
- **Reddit**: BELONGS TO SOCIAL MEDIA ANALYST - removing to avoid duplication ❌
- **Finnhub**: Emergency fallback only (overlaps with Google News) ⚠️
- **OpenAI News Tools**: Redundant aggregator, should be removed ❌

### Quality-First Target Architecture

1. **Streamlined News Gathering**
   - **Primary**: Serper with deep pagination (5 pages minimum = 50+ articles)
   - **Fallback**: Finnhub only if Serper fails or returns <10 articles
   - **Remove**: ALL Reddit tools (handled by Social Media Analyst)
   - **Remove**: OpenAI news tools (redundant with Serper)
   
2. **Enhanced Analysis Quality**
   - **Comprehensive analysis**: Full market context without token limits
   - **Multi-dimensional assessment**: 
     - Immediate impact (0-24 hours)
     - Short-term outlook (1-7 days)  
     - Medium-term implications (1-4 weeks)
     - Long-term considerations (1-3 months)
   - **Confidence scoring**: Rate reliability of each news source
   - **News authority scoring**: Rate reliability based on source reputation

3. **Efficient Query Strategy**
   - **Primary query**: `"{ticker} stock news"` with 5-page pagination
   - **Supplementary queries** (if needed):
     - `"{company_name} announcement earnings"`
     - `"{ticker} analyst upgrade downgrade"`
   - **Let Google News handle**: Deduplication, ranking, relevance
   - **No social queries**: Leave ALL social/Reddit to Social Media Analyst

4. **Smart Error Handling**
   - **Primary path**: Serper with retry on failure
   - **Fallback cascade**: Serper → Finnhub → Return partial results
   - **Quality threshold**: Minimum 20 articles from Serper alone
   - **Clear boundaries**: NO social media data - that's Social Media Analyst's job

### Architecture Principles
- **Clear separation of concerns**: News Analyst = news only, Social Analyst = social only
- **Leverage platform strengths**: Use Google's existing algorithms
- **Avoid redundant processing**: Don't re-implement deduplication/ranking
- **No duplication**: Each data source belongs to ONE analyst only
- **Quality through depth**: 5+ pages from one good source > multiple redundant sources

## Implementation Plan (2-Day Focused Sprint)

### Day 1: Serper Optimization & Cleanup
1. **Optimize Serper Integration** (3 hours)
   - Update `get_google_news` to use `getNewsDataSerperAPIWithPagination` 
   - Set default pagination to 5 pages (50+ articles)
   - Implement smart query generation for comprehensive coverage
   - Add detailed logging for coverage metrics

2. **Remove ALL Redundancy** (2 hours)
   - Remove Reddit tools completely (belongs to Social Media Analyst)
   - Remove OpenAI news tools (redundant with Serper)
   - Configure Finnhub as emergency fallback only
   - Update toolkit to have ONLY: get_google_news, get_finnhub_news

3. **Clear Role Definition** (1 hour)
   - Update prompts to focus exclusively on NEWS analysis
   - Remove any social sentiment references
   - Emphasize news authority and credibility scoring

### Day 2: Quality Enhancement & Testing
1. **Enhanced Analysis Prompts** (2 hours)
   - Design comprehensive analysis prompt (no token limits)
   - Include temporal analysis requirements
   - Add source authority and reliability scoring
   - Focus purely on news-based insights

2. **Comprehensive Testing** (3 hours)
   - Test Serper pagination with high-volume tickers (AAPL, TSLA)
   - Verify NO Reddit data leakage (strict separation)
   - Test Finnhub fallback scenarios
   - Measure coverage (target: 50+ articles per analysis)

3. **Performance Validation** (1 hour)
   - Benchmark response times with 5-page pagination
   - Validate clean separation from Social Media Analyst
   - Document quality improvements

## Code Changes Required

### 1. News Analyst Node (`news_analyst.py`)
```python
# News-exclusive prompt (NO social media mixing)
system_message = """You are a senior financial NEWS analyst specializing in traditional news media.

MANDATORY WORKFLOW:
1. Call get_google_news FIRST - this will return 50+ articles from 4,500+ sources
2. Perform deep NEWS analysis (NOT social sentiment - that's another analyst's job)

Tools available: {tool_names}

ANALYSIS STRUCTURE:

1. News Coverage Summary
   - Total articles analyzed (should be 50+)
   - Key headlines with impact assessment
   - Source authority ranking (Reuters, Bloomberg, WSJ, FT, CNBC)
   - Coverage completeness and gaps

2. Temporal News Impact
   - Immediate (0-24 hours): Breaking news implications
   - Short-term (1-7 days): News momentum analysis
   - Medium-term (1-4 weeks): Story development trajectory
   - Long-term (1-3 months): Strategic news themes

3. News Authority Assessment
   - Tier 1 sources (Reuters, Bloomberg): High confidence
   - Tier 2 sources (CNBC, MarketWatch): Medium confidence
   - Tier 3 sources (Others): Lower confidence
   - Conflicting reports analysis

4. News-Based Risk Assessment
   - Headline risks from authoritative sources
   - Regulatory/compliance news
   - M&A and corporate action news
   - Macro-economic news impact

5. News-Driven Trading Signals
   - Primary signal: BUY/HOLD/SELL based on NEWS only
   - Confidence level based on source authority
   - Key catalysts from news
   - News momentum indicators

6. Evidence & Attribution
   - Top 10 most impactful articles with sources
   - Direct quotes from authoritative sources
   - Fact verification across multiple sources
   - News consensus vs outliers

Focus ONLY on news. Social sentiment is handled by Social Media Analyst."""

# Clean tool configuration - NO REDDIT
if toolkit.config["online_tools"]:
    tools = [toolkit.get_google_news]  # Primary
else:
    tools = [toolkit.get_finnhub_news]  # Offline fallback
    
# REMOVED: ALL Reddit tools, OpenAI news tools
```

### 2. Interface Enhancement (`interface.py`)
```python
# Optimized Serper-primary approach with deep pagination
async def get_google_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    logger = logging.getLogger(__name__)
    logger.info(f"🔧 TOOL START: get_google_news | Query: {query} | Date: {curr_date}")
    
    try:
        # Date range setup
        start_date = datetime.strptime(curr_date, "%Y-%m-%d")
        before = start_date - relativedelta(days=look_back_days)
        before = before.strftime("%Y-%m-%d")

        # Use deep pagination for comprehensive coverage
        serper_key = DEFAULT_CONFIG.get("serper_key", "")
        if not serper_key:
            raise ValueError("Serper API key required")
        
        # ENHANCEMENT: Use pagination for 50+ articles
        logger.info(f"🌐 Fetching news with 5-page pagination for comprehensive coverage")
        news_results = await getNewsDataSerperAPIWithPagination(
            query, before, curr_date, 
            max_pages=5,  # 50 articles for thorough analysis
            serper_key=serper_key
        )
        
        # Fallback to Finnhub if Serper fails or returns insufficient data
        if not news_results or len(news_results) < 10:
            logger.warning(f"⚠️ Serper returned {len(news_results)} articles, trying Finnhub fallback")
            # Extract ticker from query for Finnhub
            ticker = query.split()[0]  # Simple extraction
            finnhub_results = get_finnhub_news(ticker, curr_date, look_back_days)
            if finnhub_results:
                news_results.extend(finnhub_results)
        
        logger.info(f"✅ Successfully gathered {len(news_results)} articles")
        logger.info(f"📊 Coverage breakdown by source: {_analyze_sources(news_results)}")
        
        # Format results with source attribution
        news_str = ""
        for i, news in enumerate(news_results[:50], 1):  # Cap at 50 for readability
            news_str += f"### [{i}] {news.get('title', 'No title')} \n"
            news_str += f"**Source**: {news.get('source', 'Unknown')} | "
            news_str += f"**Date**: {news.get('date', 'N/A')}\n"
            news_str += f"{news.get('snippet', '')}\n\n"
        
        result = f"## News Analysis: {len(news_results)} articles from {before} to {curr_date}\n\n"
        result += f"Coverage: Google News (4,500+ sources) with 5-page deep scan\n\n"
        result += news_str
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in get_google_news: {str(e)}")
        # Final fallback - return error message rather than empty
        return f"News gathering failed: {str(e)}. Please retry."

def _analyze_sources(news_results):
    """Analyze source diversity for quality metrics"""
    sources = {}
    for item in news_results:
        source = item.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    # Top 5 sources
    top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]
    return f"{len(sources)} unique sources, top: {top_sources}"
```

### 3. Toolkit Configuration (`toolkit_factory.py`)
```python
@staticmethod
def create_news_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
    """Create news-exclusive analyst toolkit (NO social media)"""
    allowed_tools = [
        # Primary: Serper for comprehensive news (4,500+ sources)
        "get_google_news",
        # Emergency fallback only
        "get_finnhub_news"
        # REMOVED: ALL Reddit tools (belong to Social Media Analyst)
        # REMOVED: OpenAI news tools (redundant with Serper)
    ]
    return BaseAnalystToolkit(base_toolkit, allowed_tools)

@staticmethod
def create_social_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
    """Social media analyst owns ALL Reddit/social data"""
    allowed_tools = [
        # Social sentiment (Reddit, StockTwits, Twitter)
        "get_reddit_stock_info",
        "get_reddit_news",  # This belongs HERE, not in news
        "get_stocktwits_sentiment",
        "get_twitter_mentions",
        # Can use some news for context
        "get_stock_news_openai"
    ]
    return BaseAnalystToolkit(base_toolkit, allowed_tools)
```

## Comprehensive Test Plan

### Unit Tests (Day 1)
1. **Tool Call Validation**
   - Test: LLM must call tools on first iteration
   - Test: Validate error when no tools called
   - Test: Retry mechanism when tools fail
   - Test: Parallel tool execution

2. **Multi-Source Integration**
   - Test: All tools are accessible (Serper, Reddit, Finnhub)
   - Test: Parallel execution completes successfully
   - Test: Aggregation handles different data formats
   - Test: Source attribution is maintained

3. **Query Generation**
   - Test: Multiple query angles are generated
   - Test: Competitor identification works
   - Test: Sector context queries are included
   - Test: Date filtering is applied correctly

### Integration Tests (Day 2)
1. **End-to-End Scenarios**
   - Test: Complete flow with real ticker (AAPL)
   - Test: High-news-volume events (earnings day)
   - Test: Low-news-volume stocks
   - Test: International/ADR stocks

2. **Quality Validation**
   - Test: Minimum 10 articles threshold
   - Test: Source diversity (at least 2 sources)
   - Test: Temporal analysis present
   - Test: Confidence scoring included

3. **Error Recovery**
   - Test: Serper API failure → fallback to others
   - Test: All sources fail → graceful error message
   - Test: Partial failures → use available data
   - Test: Rate limit handling

### Performance Tests (Day 3)
1. **Load Testing**
   - Test: 10 concurrent ticker analyses
   - Test: High-volume tickers (TSLA, NVDA, AMC)
   - Test: Response time with 5-page pagination
   - Test: Memory usage with large datasets

2. **Quality Benchmarks**
   - Test: Coverage vs. manual search (>90% match)
   - Test: Analysis depth (avg 3000+ words)
   - Test: Source diversity (avg 3+ sources)
   - Test: Temporal accuracy validation

3. **Stress Testing**
   - Test: 50+ articles aggregation
   - Test: API timeout scenarios
   - Test: Network interruption recovery
   - Test: Cache performance under load

### Acceptance Tests
1. **Business Requirements**
   - Comprehensive news coverage achieved
   - Multiple perspectives included
   - Actionable trading insights provided
   - Risk factors clearly identified

2. **Quality Metrics**
   - Analysis completeness score >90%
   - Source reliability score >85%
   - Temporal prediction accuracy >70%
   - User satisfaction rating >4.5/5

## Quality Success Metrics
- **Coverage**: 50+ articles from Serper (via 5-page pagination)
- **Source Diversity**: 20+ unique sources from Google News aggregation
- **Authority Score**: Clear tier ranking of source reliability
- **Analysis Depth**: Comprehensive 6-section NEWS-ONLY analysis
- **Temporal Accuracy**: Clear predictions for 4 time horizons
- **Response Time**: <6s (faster without Reddit parallel calls)
- **Clean Separation**: ZERO social media data in news analysis

## Risk Mitigation (News-Exclusive)
- **Serper API failure**: Automatic fallback to Finnhub
- **Insufficient coverage**: Increase pagination up to 10 pages if needed
- **Rate limiting**: Implement exponential backoff with retry
- **Role confusion**: Strict enforcement - NO social media data allowed

## Key Architecture Decisions

### Why News-Exclusive Architecture is Correct:
1. **Clear Separation**: Each analyst has distinct role - no overlap
2. **Serper Completeness**: Google News indexes 4,500+ sources - sufficient for news
3. **Avoid Duplication**: Reddit data belongs to Social Media Analyst ONLY
4. **Simpler Testing**: Can validate news analysis independently
5. **Better Performance**: Faster without parallel Reddit calls

### What We're NOT Doing (and Why):
- **NOT using multiple aggregators**: Redundant processing of same content
- **NOT implementing deduplication**: Google already does this
- **NOT complex ranking algorithms**: Leverage Google's existing ranking
- **NOT token optimization**: Quality and completeness are paramount

## Summary

This corrected plan establishes clear separation of concerns:
- **News Analyst**: Exclusively handles traditional news media via Serper (4,500+ sources)
- **Social Media Analyst**: Exclusively handles Reddit, StockTwits, Twitter sentiment

By removing Reddit from News Analyst, we:
1. Eliminate duplication between analysts
2. Improve performance (no parallel Reddit calls needed)
3. Simplify testing and maintenance
4. Create clearer, more focused analysis

The architecture leverages Serper's comprehensive news aggregation (with 5-page deep pagination for 50+ articles) while maintaining strict boundaries between news and social sentiment analysis. Each analyst now has a clear, non-overlapping domain of expertise.