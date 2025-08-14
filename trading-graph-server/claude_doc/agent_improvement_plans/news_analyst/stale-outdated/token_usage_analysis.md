# Token Usage Analysis - News Analyst Pure Data Collection

## Executive Summary

The transformation of the news analyst from analysis-based to pure data collection has **significant implications for token usage**, with both increases and optimizations depending on the perspective.

## Token Usage Changes

### 1. News Analyst Node (Direct Impact)

#### Before (Analysis-Based)
- **Input Tokens**: ~500-1,000 (LLM prompt + 20 articles)
- **Output Tokens**: ~2,000-3,000 (analysis report)
- **Total per run**: ~3,000-4,000 tokens

#### After (Pure Data Collection)
- **Input Tokens**: 0 (no LLM calls)
- **Output Tokens**: 0 (no LLM generation)
- **Data Storage**: 129KB raw data (not tokens)
- **Total per run**: 0 tokens

**Direct Savings: 100% reduction (3,000-4,000 tokens saved per execution)**

### 2. Downstream Agent Impact

#### Research/Aggregator Agents (Increased Usage)

**Before**: Received pre-analyzed summary
- Input: ~2,000 tokens (summary)
- Processing: Standard analysis
- Output: ~1,500 tokens

**After**: Receive raw data
- Input: ~30,000-50,000 tokens (60 articles)
- Processing: Deep analysis required
- Output: ~3,000-5,000 tokens (more detailed)

**Increase: 10-15x more input tokens for downstream agents**

### 3. System-Wide Token Usage

#### Scenario A: Single Analysis Pass
```
Before:
- News Analyst: 3,500 tokens
- Downstream Agent: 3,500 tokens
- Total: 7,000 tokens

After:
- News Analyst: 0 tokens
- Downstream Agent: 35,000 tokens
- Total: 35,000 tokens

Net Change: +400% increase
```

#### Scenario B: Multiple Specialized Agents
```
Before (3 agents analyzing same summary):
- News Analyst: 3,500 tokens
- Agent 1: 3,500 tokens
- Agent 2: 3,500 tokens
- Agent 3: 3,500 tokens
- Total: 14,000 tokens

After (3 agents with different analysis needs):
- News Analyst: 0 tokens
- Agent 1 (uses 10 articles): 8,000 tokens
- Agent 2 (uses 20 articles): 15,000 tokens
- Agent 3 (uses all 60): 35,000 tokens
- Total: 58,000 tokens

Net Change: +314% increase
```

## Token Optimization Strategies

### 1. Selective Article Processing
```python
def optimize_token_usage(news_data, max_articles=10):
    """Process only most relevant articles to reduce tokens"""
    
    # Sort by relevance/source tier
    articles = sorted(news_data['articles'], 
                     key=lambda x: classify_source_tier(x['source']))
    
    # Take only top articles
    return articles[:max_articles]
```

**Savings: 60-80% token reduction**

### 2. Progressive Enhancement
```python
def progressive_analysis(news_data):
    """Analyze in stages to minimize token usage"""
    
    # Stage 1: Headlines only (5K tokens)
    headlines = [a['title'] for a in news_data['articles']]
    initial_analysis = analyze_headlines(headlines)
    
    # Stage 2: If needed, analyze top 10 articles (15K tokens)
    if needs_deeper_analysis(initial_analysis):
        top_articles = news_data['articles'][:10]
        deep_analysis = analyze_articles(top_articles)
    
    return combine_analyses(initial_analysis, deep_analysis)
```

**Savings: 70% for most cases**

### 3. Caching and Deduplication
```python
def cache_and_deduplicate(news_data):
    """Cache processed articles to avoid reprocessing"""
    
    cache_key = f"{news_data['company']}_{news_data['date']}"
    
    if cache_key in processed_cache:
        return processed_cache[cache_key]
    
    # Deduplicate similar articles
    unique_articles = deduplicate_by_similarity(news_data['articles'])
    
    # Process and cache
    result = process_articles(unique_articles)
    processed_cache[cache_key] = result
    
    return result
```

**Savings: 30-50% through deduplication**

### 4. Context Window Management
```python
def manage_context_window(news_data, window_size=8000):
    """Fit articles into context window efficiently"""
    
    articles_with_size = []
    for article in news_data['articles']:
        # Estimate tokens (rough: 1 token per 4 chars)
        tokens = len(json.dumps(article)) / 4
        articles_with_size.append((article, tokens))
    
    # Greedy packing algorithm
    selected = []
    current_size = 0
    
    for article, size in sorted(articles_with_size, 
                                key=lambda x: classify_source_tier(x[0]['source'])):
        if current_size + size <= window_size:
            selected.append(article)
            current_size += size
    
    return selected
```

**Optimization: Maximum articles within token budget**

## Cost-Benefit Analysis

### Benefits of Increased Token Usage

1. **Complete Information**: 60 articles vs 20 = 3x more data
2. **No Analysis Bias**: Raw data allows custom analysis
3. **Flexibility**: Different agents can analyze differently
4. **Transparency**: Full article content available

### Costs

1. **Token Increase**: 400-500% for single-pass analysis
2. **Context Limits**: May exceed context windows (8K-32K)
3. **Processing Time**: Longer LLM processing
4. **API Costs**: Higher costs for token-based pricing

### Break-Even Analysis

```
Old System (with bias):
- 7,000 tokens per analysis
- Limited to pre-defined sentiment
- May miss critical information

New System (pure data):
- 35,000 tokens per analysis
- Custom analysis possible
- Complete information available

Break-even point: When custom analysis provides 5x better insights
```

## Recommendations

### 1. Implement Smart Filtering
- Filter by source tier (tier 1 first)
- Filter by date relevance
- Filter by keyword matching
- **Potential Savings**: 60-70% token reduction

### 2. Use Chunking Strategies
- Process in batches of 10-15 articles
- Implement progressive refinement
- Use summaries for initial screening
- **Potential Savings**: 50-60% token reduction

### 3. Hybrid Approach
```python
def hybrid_news_processing(news_data, urgency='normal'):
    """Hybrid approach based on urgency"""
    
    if urgency == 'high':
        # Full analysis for critical decisions
        return process_all_articles(news_data)  # 35K tokens
    
    elif urgency == 'normal':
        # Balanced approach
        return process_top_articles(news_data, count=20)  # 15K tokens
    
    else:  # low urgency
        # Efficient processing
        return process_headlines_only(news_data)  # 5K tokens
```

### 4. Implement Token Budgets
```python
class TokenBudgetManager:
    """Manage token budgets across agents"""
    
    def __init__(self, daily_budget=1_000_000):
        self.daily_budget = daily_budget
        self.used_today = 0
    
    def allocate_for_news(self, priority='normal'):
        """Allocate tokens for news analysis"""
        
        allocations = {
            'critical': 50_000,  # Full analysis
            'high': 30_000,      # Top 30 articles
            'normal': 15_000,    # Top 15 articles
            'low': 5_000         # Headlines only
        }
        
        requested = allocations.get(priority, 15_000)
        
        if self.used_today + requested <= self.daily_budget:
            self.used_today += requested
            return requested
        else:
            # Fallback to lower priority
            return allocations['low']
```

## Conclusion

The shift to pure data collection represents a **trade-off**:

### Pros:
- ✅ Zero tokens at collection point
- ✅ Complete data availability (3x more articles)
- ✅ No hardcoded bias
- ✅ Flexible downstream analysis

### Cons:
- ❌ 4-5x increase in total token usage
- ❌ Context window challenges
- ❌ Higher API costs
- ❌ Increased processing complexity

### Optimization Potential:
With smart filtering and chunking strategies, token usage can be reduced by **60-70%**, bringing the increase down to only **1.5-2x** while maintaining most benefits.

### Recommendation:
Implement a **hybrid approach** with:
1. Smart filtering by source tier
2. Progressive analysis stages
3. Token budget management
4. Caching for repeated queries

This balances the benefits of complete data with manageable token costs.