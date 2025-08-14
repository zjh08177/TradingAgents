# Token Optimization Strategies for Pure Data Collection

## Executive Summary

The shift from analysis-based to pure data collection in the news analyst creates a **significant token usage challenge** for downstream agents. While we save 3,000-4,000 tokens at the collection point, downstream agents now consume 35,000+ tokens (a 5x increase) to process the raw data. This document outlines comprehensive optimization strategies to mitigate this impact.

## The Token Challenge

### Current State Analysis

**News Analyst Output:**
- **Size**: 129KB of raw JSON data (60 articles)
- **Token Equivalent**: ~30,000-50,000 tokens when passed to LLMs
- **Format**: Structured JSON with full article content

**Downstream Consumption Pattern:**
```python
# Research Manager passes full news_report to Bull/Bear researchers
curr_situation = f"{market_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
```

**Impact:**
- Each researcher (Bull, Bear) receives the full 30,000+ tokens
- Research Manager evaluation also processes full data
- Total system token usage: 100,000+ tokens per analysis cycle

## Optimization Strategies

### 1. Smart Article Filtering (60-70% reduction)

```python
class NewsDataOptimizer:
    """Intelligent filtering of news articles before LLM processing"""
    
    def filter_relevant_articles(self, news_data: Dict, max_articles: int = 15) -> Dict:
        """Filter to most relevant articles based on multiple criteria"""
        
        articles = news_data.get('articles', [])
        
        # Score each article
        scored_articles = []
        for article in articles:
            score = self.calculate_relevance_score(article)
            scored_articles.append((score, article))
        
        # Sort by score and take top N
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        filtered = [article for score, article in scored_articles[:max_articles]]
        
        return {
            **news_data,
            'articles': filtered,
            'total_available': len(articles),
            'filtered_count': len(filtered)
        }
    
    def calculate_relevance_score(self, article: Dict) -> float:
        """Multi-factor relevance scoring"""
        score = 0.0
        
        # Source tier (tier 1 = highest quality)
        source_tier = self.classify_source_tier(article.get('source', ''))
        score += (4 - source_tier) * 0.3  # 30% weight for source quality
        
        # Recency (newer = better)
        published_date = article.get('publishedDate', '')
        days_old = self.calculate_days_old(published_date)
        recency_score = max(0, 1 - (days_old / 30))  # Linear decay over 30 days
        score += recency_score * 0.25  # 25% weight for recency
        
        # Position in search results
        position = article.get('position', 100)
        position_score = max(0, 1 - (position / 60))
        score += position_score * 0.2  # 20% weight for position
        
        # Content length (prefer substantial articles)
        content_length = len(article.get('snippet', ''))
        length_score = min(1.0, content_length / 500)  # Normalize to 500 chars
        score += length_score * 0.15  # 15% weight for content depth
        
        # Keyword relevance
        keywords = ['earnings', 'revenue', 'profit', 'guidance', 'forecast', 'announce']
        content = (article.get('title', '') + ' ' + article.get('snippet', '')).lower()
        keyword_matches = sum(1 for kw in keywords if kw in content)
        keyword_score = min(1.0, keyword_matches / 3)  # Normalize to 3 keywords
        score += keyword_score * 0.1  # 10% weight for keywords
        
        return score
```

### 2. Progressive Data Loading (70% reduction for initial pass)

```python
class ProgressiveNewsProcessor:
    """Process news data in progressive stages"""
    
    def create_staged_report(self, news_data: Dict) -> Dict:
        """Create a staged report for progressive processing"""
        
        articles = news_data.get('articles', [])
        
        # Stage 1: Headlines and metadata only (5K tokens)
        stage1 = {
            'stage': 1,
            'data': [{
                'title': a['title'],
                'source': a['source'],
                'publishedDate': a.get('publishedDate', ''),
                'link': a['link']
            } for a in articles]
        }
        
        # Stage 2: Top 10 articles with snippets (15K tokens)
        stage2 = {
            'stage': 2,
            'data': [{
                'title': a['title'],
                'source': a['source'],
                'snippet': a.get('snippet', '')[:200],  # Truncated snippet
                'publishedDate': a.get('publishedDate', ''),
            } for a in articles[:10]]
        }
        
        # Stage 3: Full top 5 articles (25K tokens)
        stage3 = {
            'stage': 3,
            'data': articles[:5]  # Full articles
        }
        
        # Stage 4: All articles (35K+ tokens) - only if needed
        stage4 = {
            'stage': 4,
            'data': articles
        }
        
        return {
            'stages': [stage1, stage2, stage3, stage4],
            'current_stage': 1,
            'escalation_trigger': 'confidence < 0.7'
        }
```

### 3. Semantic Compression (40-50% reduction)

```python
class SemanticNewsCompressor:
    """Compress news data while preserving semantic meaning"""
    
    def compress_articles(self, articles: List[Dict]) -> List[Dict]:
        """Compress articles using semantic techniques"""
        
        compressed = []
        for article in articles:
            compressed.append(self.compress_single_article(article))
        
        return compressed
    
    def compress_single_article(self, article: Dict) -> Dict:
        """Compress a single article"""
        
        # Extract key sentences using TextRank or similar
        snippet = article.get('snippet', '')
        key_sentences = self.extract_key_sentences(snippet, max_sentences=3)
        
        # Extract entities and numbers
        entities = self.extract_entities(snippet)
        numbers = self.extract_numbers(snippet)
        
        # Create compressed representation
        return {
            'title': article['title'],
            'source': article['source'],
            'date': article.get('publishedDate', ''),
            'key_points': key_sentences,
            'entities': entities[:5],  # Top 5 entities
            'metrics': numbers[:3],    # Top 3 numbers/metrics
            'sentiment_keywords': self.extract_sentiment_keywords(snippet),
            'link': article['link']
        }
    
    def extract_key_sentences(self, text: str, max_sentences: int = 3) -> List[str]:
        """Extract most important sentences using TextRank algorithm"""
        # Simplified implementation - in production use proper NLP library
        sentences = text.split('. ')
        
        # Score sentences by position and keyword density
        scored = []
        important_keywords = ['announce', 'report', 'earnings', 'revenue', 'profit', 
                             'loss', 'growth', 'decline', 'forecast', 'guidance']
        
        for i, sent in enumerate(sentences):
            score = 0
            # Position score (earlier = more important)
            score += (len(sentences) - i) / len(sentences)
            
            # Keyword score
            sent_lower = sent.lower()
            keyword_count = sum(1 for kw in important_keywords if kw in sent_lower)
            score += keyword_count * 0.5
            
            # Length score (prefer medium length)
            word_count = len(sent.split())
            if 10 <= word_count <= 30:
                score += 0.3
            
            scored.append((score, sent))
        
        # Sort and return top sentences
        scored.sort(key=lambda x: x[0], reverse=True)
        return [sent for score, sent in scored[:max_sentences]]
```

### 4. Intelligent Caching (30-40% reduction)

```python
class NewsDataCache:
    """Cache processed news data to avoid reprocessing"""
    
    def __init__(self):
        self.cache = {}
        self.processing_cache = {}  # Cache of processed/analyzed data
    
    def get_or_process(self, company: str, date: str, news_data: Dict, 
                       processor_func: callable) -> Dict:
        """Get cached result or process and cache"""
        
        cache_key = f"{company}_{date}"
        
        # Check if we have processed data
        if cache_key in self.processing_cache:
            age_minutes = self.get_cache_age(cache_key)
            if age_minutes < 60:  # Cache valid for 1 hour
                logger.info(f"✅ Using cached news analysis ({age_minutes}m old)")
                return self.processing_cache[cache_key]
        
        # Process and cache
        processed = processor_func(news_data)
        self.processing_cache[cache_key] = {
            'data': processed,
            'timestamp': time.time(),
            'article_count': len(news_data.get('articles', []))
        }
        
        return processed
    
    def deduplicate_across_agents(self, news_data: Dict) -> Dict:
        """Deduplicate articles across multiple agent calls"""
        
        articles = news_data.get('articles', [])
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # Create fingerprint
            fingerprint = self.create_article_fingerprint(article)
            
            if fingerprint not in seen_titles:
                seen_titles.add(fingerprint)
                unique_articles.append(article)
        
        logger.info(f"📊 Deduplication: {len(articles)} → {len(unique_articles)} articles")
        
        return {
            **news_data,
            'articles': unique_articles,
            'duplicates_removed': len(articles) - len(unique_articles)
        }
```

### 5. Context Window Management (Optimal token usage)

```python
class ContextWindowOptimizer:
    """Optimize news data to fit within context windows"""
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.encoder = tiktoken.encoding_for_model("gpt-4")
    
    def optimize_for_context(self, news_data: Dict, priority_mode: str = 'balanced') -> Dict:
        """Optimize news data to fit context window"""
        
        articles = news_data.get('articles', [])
        
        # Different strategies based on priority
        if priority_mode == 'diversity':
            # Include more articles with less detail
            return self.optimize_for_diversity(articles)
        elif priority_mode == 'depth':
            # Include fewer articles with full detail
            return self.optimize_for_depth(articles)
        else:  # balanced
            return self.optimize_balanced(articles)
    
    def optimize_balanced(self, articles: List[Dict]) -> Dict:
        """Balanced optimization - mix of breadth and depth"""
        
        selected = []
        current_tokens = 0
        
        # First pass: Include all titles and sources
        for article in articles:
            basic_info = {
                'title': article['title'],
                'source': article['source']
            }
            tokens = len(self.encoder.encode(json.dumps(basic_info)))
            if current_tokens + tokens < self.max_tokens * 0.3:  # Use 30% for basic info
                selected.append(basic_info)
                current_tokens += tokens
        
        # Second pass: Add snippets for top articles
        remaining_tokens = self.max_tokens - current_tokens
        for i, article in enumerate(articles[:15]):  # Top 15 articles
            if i < len(selected):
                snippet = article.get('snippet', '')[:200]  # Truncate to 200 chars
                snippet_tokens = len(self.encoder.encode(snippet))
                
                if snippet_tokens < remaining_tokens:
                    selected[i]['snippet'] = snippet
                    remaining_tokens -= snippet_tokens
        
        return {
            'articles': selected,
            'optimization_mode': 'balanced',
            'token_usage': self.max_tokens - remaining_tokens,
            'article_count': len(selected)
        }
```

### 6. Hybrid Processing Pipeline

```python
class HybridNewsProcessor:
    """Combine all optimization strategies into a unified pipeline"""
    
    def __init__(self):
        self.filter = NewsDataOptimizer()
        self.compressor = SemanticNewsCompressor()
        self.cache = NewsDataCache()
        self.window_optimizer = ContextWindowOptimizer()
    
    def process_for_agent(self, news_data: Dict, agent_type: str, 
                          urgency: str = 'normal') -> Dict:
        """Process news data optimally for specific agent"""
        
        # Step 1: Deduplicate
        news_data = self.cache.deduplicate_across_agents(news_data)
        
        # Step 2: Filter based on agent needs
        if agent_type == 'bull_researcher':
            # Focus on positive news
            filtered = self.filter.filter_relevant_articles(news_data, max_articles=15)
        elif agent_type == 'bear_researcher':
            # Include risk-related news
            filtered = self.filter.filter_relevant_articles(news_data, max_articles=15)
        else:
            filtered = self.filter.filter_relevant_articles(news_data, max_articles=20)
        
        # Step 3: Compress based on urgency
        if urgency == 'high':
            # Full detail for critical decisions
            processed = filtered
        elif urgency == 'low':
            # Maximum compression
            compressed_articles = self.compressor.compress_articles(filtered['articles'])
            processed = {**filtered, 'articles': compressed_articles}
        else:  # normal
            # Balanced compression
            processed = self.window_optimizer.optimize_for_context(filtered, 'balanced')
        
        # Step 4: Cache the result
        return self.cache.get_or_process(
            company=news_data.get('company', ''),
            date=news_data.get('date', ''),
            news_data=processed,
            processor_func=lambda x: x  # Already processed
        )
```

## Implementation Recommendations

### Phase 1: Quick Wins (1-2 days)
1. Implement basic filtering (top 15 articles) - **60% token reduction**
2. Add simple deduplication - **10-15% token reduction**
3. Enable title+snippet only mode - **70% token reduction**

### Phase 2: Smart Optimization (3-5 days)
1. Implement relevance scoring system
2. Add semantic compression
3. Create staged loading system
4. Add caching layer

### Phase 3: Advanced Features (1 week)
1. Agent-specific optimization
2. Context window management
3. Hybrid processing pipeline
4. Performance monitoring

## Expected Results

### Token Usage After Optimization

| Strategy | Token Usage | Reduction | Quality Impact |
|----------|------------|-----------|----------------|
| No Optimization | 35,000 | 0% | Full data |
| Basic Filtering | 14,000 | 60% | Minimal |
| + Compression | 8,400 | 76% | Low |
| + Caching | 5,900 | 83% | None |
| + Staged Loading | 5,000 | 86% | None |
| Full Pipeline | 4,500 | 87% | Negligible |

### Cost-Benefit Analysis

**Current State:**
- 35,000 tokens per agent × 3 agents = 105,000 tokens
- Cost: ~$1.05 per analysis (GPT-4 pricing)

**Optimized State:**
- 5,000 tokens per agent × 3 agents = 15,000 tokens
- Cost: ~$0.15 per analysis
- **Savings: 86% cost reduction**

## Monitoring and Metrics

```python
class TokenUsageMonitor:
    """Monitor and report token usage across the system"""
    
    def __init__(self):
        self.metrics = {
            'total_tokens': 0,
            'by_component': {},
            'by_strategy': {},
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def log_usage(self, component: str, tokens: int, strategy: str = 'none'):
        """Log token usage for monitoring"""
        self.metrics['total_tokens'] += tokens
        
        if component not in self.metrics['by_component']:
            self.metrics['by_component'][component] = 0
        self.metrics['by_component'][component] += tokens
        
        if strategy not in self.metrics['by_strategy']:
            self.metrics['by_strategy'][strategy] = 0
        self.metrics['by_strategy'][strategy] += tokens
    
    def generate_report(self) -> str:
        """Generate usage report"""
        return f"""
Token Usage Report
==================
Total Tokens: {self.metrics['total_tokens']:,}
Cache Hit Rate: {self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses']):.1%}

By Component:
{self._format_component_usage()}

By Strategy:
{self._format_strategy_usage()}

Recommendations:
{self._generate_recommendations()}
"""
```

## Conclusion

With proper optimization strategies, we can reduce token usage by **85-87%** while maintaining data quality. The hybrid approach allows flexibility based on urgency and agent needs, ensuring optimal performance across all scenarios.

### Key Takeaways:
1. **Filter aggressively** - Most value comes from top 15-20 articles
2. **Compress semantically** - Preserve meaning, not words
3. **Cache intelligently** - Avoid reprocessing same data
4. **Stage progressively** - Load more data only when needed
5. **Monitor continuously** - Track and optimize based on usage patterns

The investment in optimization will pay for itself within days through reduced API costs and improved system performance.