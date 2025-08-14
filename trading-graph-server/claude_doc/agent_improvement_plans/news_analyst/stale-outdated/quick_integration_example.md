# Quick Integration Example (30 Minutes Implementation)

## Problem
- News analyst now outputs 35,000+ tokens
- Bull/Bear researchers consume full data
- 5x token usage increase

## Solution (KISS-Compliant)
Single function, single line change, 70%+ reduction

## Step 1: Add the Filter Function (Already Done)
Location: `/src/agent/utils/news_filter.py`

## Step 2: Apply in Researchers (2 Line Changes)

### Bull Researcher
File: `/src/agent/researchers/bull_researcher.py`

```python
# Add import at top
from ..utils.news_filter import filter_news_for_llm

# Find this line (around line 42):
curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

# Replace with:
filtered_news = filter_news_for_llm(news_report, max_articles=15)
curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{filtered_news}\n\n{fundamentals_report}"
```

### Bear Researcher
File: `/src/agent/researchers/bear_researcher.py`

```python
# Add import at top
from ..utils.news_filter import filter_news_for_llm

# Find similar line and replace:
filtered_news = filter_news_for_llm(news_report, max_articles=15)
curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{filtered_news}\n\n{fundamentals_report}"
```

### Research Manager
File: `/src/agent/managers/research_manager.py`

```python
# Add import at top
from ..utils.news_filter import filter_news_for_llm

# Find the investment plan prompt (around line 183):
News Analysis: {news_report}

# Replace with:
News Analysis: {filter_news_for_llm(news_report, max_articles=12)}
```

## Step 3: Test (5 Minutes)

```bash
# Test with any ticker
./debug_local.sh AAPL

# Check logs for filtering message:
# "📰 News filtering: 60 → 15 articles (75% reduction)"
```

## Expected Results

### Token Usage
- **Before**: 35,000 tokens per researcher
- **After**: 10,000 tokens per researcher
- **System Total**: 100,000 → 30,000 tokens (70% reduction)

### Quality Impact
- **Minimal**: Top 15 articles contain key information
- **Investment quality**: No degradation expected
- **Analysis speed**: 3x faster

## If Further Reduction Needed

Replace `filter_news_for_llm` with `extract_headlines_and_snippets`:

```python
# For ultra-light processing (85% reduction)
headlines_only = extract_headlines_and_snippets(news_report, max_articles=20)
curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{headlines_only}\n\n{fundamentals_report}"
```

## Rollback Plan

If any issues, simply remove the filter:
```python
# Back to original
curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
```

## Why This Works

1. **Serper API already ranks by relevance** - Top articles are most important
2. **Diminishing returns** - Articles 16-60 add little value
3. **LLM efficiency** - Models excel at processing 10-15 articles
4. **Position preservation** - Order from API is meaningful

## Monitoring

The function automatically logs reductions:
```
📰 News filtering: 60 → 15 articles (75.0% reduction)
```

## Next Steps (Only If Needed)

1. Measure actual token usage reduction
2. Monitor investment decision quality
3. Adjust `max_articles` parameter if needed
4. Consider headlines-only mode for non-critical analysis

**Total Implementation Time: 30 minutes**
**Code Added: <50 lines**
**Complexity: Minimal**
**Token Savings: 70%+**