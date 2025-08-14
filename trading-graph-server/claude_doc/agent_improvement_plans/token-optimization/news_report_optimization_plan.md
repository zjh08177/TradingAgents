# News Report Optimization Plan
## The Primary Token Consumption Fix

**Priority**: 🔴 **CRITICAL** - Highest Impact Optimization  
**Impact**: 85,000 token reduction (39% of total system)  
**Timeline**: Week 1 implementation  
**Complexity**: Medium (focused changes, clear benefits)

---

## 🚨 Problem Statement

The **News Report is consuming 101,360 tokens (46.5% of the entire system)** through context duplication. A single news report containing 50,682 characters gets passed to 8 different components, creating massive token waste.

### Current State Analysis:
- **Raw Size**: 50,682 characters (~12,670 tokens per copy)
- **Content**: 15 full articles with complete text
- **Duplication**: 8× across different components
- **Total Impact**: 101,360 tokens
- **Cost Impact**: $1.01 per execution just for news context

---

## 🔍 Root Cause Analysis

### News Report Structure (From Trace Data):
```
# NEWS DATA COLLECTION - AAPL

Generated: 2025-08-13 23:24:48
Trade Date: 2025-08-13

## COLLECTION METRICS (TOKEN OPTIMIZED)
- Articles Used: 15 (filtered for optimal token usage)
- Serper: 15 articles (from 20 available) 
- Finnhub: 0 articles (from 0 available)
- Collection Time: 2.708s
- Token Optimization: Active (max 15 articles)

## RAW ARTICLE DATA

### Article 1
Title: As Elon Musk Lashes Out at Apple, How Should You Play TSLA and AAPL Stock?
Source: Yahoo Finance  
Date: 16 hours ago
URL: https://finance.yahoo.com/...
Content: [FULL ARTICLE TEXT - 3,000+ characters per article]

### Article 2
[ANOTHER FULL ARTICLE...]

...continues for 15 articles
```

### Issues Identified:
1. **Full Article Content**: Complete article text included (~3,000 chars each)
2. **No Summarization**: Raw collection without analysis or compression
3. **Non-Trading Focus**: Articles include general news not relevant to trading decisions
4. **Redundant Information**: Multiple articles covering same events
5. **No Token Budgeting**: No limits on content length per article

---

## 🎯 Optimization Strategy

### Target Metrics:
- **Current**: 50,682 characters → 12,670 tokens per copy
- **Target**: 8,000 characters → 2,000 tokens per copy  
- **Reduction**: 84% size reduction
- **Total Savings**: 85,000+ tokens across all components

---

## 🚀 Implementation Plan

### Phase 1A: Content Filtering (Week 1, Day 1-2)

#### Create News Compression Utility

```python
# File: src/agent/utils/news_compressor.py

import re
import json
from typing import Dict, List, Any

class NewsCompressor:
    """Compress news reports for token-optimized context sharing"""
    
    def __init__(self, max_articles: int = 15, max_tokens_per_article: int = 133):
        self.max_articles = max_articles
        self.max_tokens_per_article = max_tokens_per_article  # 2000 total / 15 articles
        self.max_chars_per_article = max_tokens_per_article * 4  # ~533 chars per article
    
    def compress_news_report(self, news_report: str) -> str:
        """
        Compress news report to trading-relevant information only
        Target: 2000 tokens (vs 12,670 current)
        """
        try:
            # Extract JSON data from report
            json_match = re.search(r'```json\n(.*?)\n```', news_report, re.DOTALL)
            if not json_match:
                return self._create_fallback_summary(news_report)
            
            news_data = json.loads(json_match.group(1))
            articles = news_data.get('articles', [])
            
            if not articles:
                return self._create_fallback_summary(news_report)
            
            # Compress each article to key trading information
            compressed_articles = []
            for article in articles[:self.max_articles]:
                compressed = self._compress_single_article(article)
                if compressed:
                    compressed_articles.append(compressed)
            
            # Generate compressed report
            return self._generate_compressed_report(compressed_articles, news_data)
            
        except Exception as e:
            logger.warning(f"News compression failed: {e}, using fallback")
            return self._create_fallback_summary(news_report)
    
    def _compress_single_article(self, article: Dict[str, Any]) -> Dict[str, str]:
        """Compress single article to trading essentials"""
        title = article.get('title', '')
        content = article.get('content', article.get('snippet', ''))
        
        # Extract trading-relevant information
        compressed_content = self._extract_trading_signals(content)
        
        # Apply character limits
        if len(compressed_content) > self.max_chars_per_article:
            compressed_content = compressed_content[:self.max_chars_per_article-3] + "..."
        
        return {
            'title': title[:100],  # Limit title length
            'key_points': compressed_content,
            'source': article.get('source', 'Unknown'),
            'date': article.get('publishedAt', article.get('date', 'Recent'))
        }
    
    def _extract_trading_signals(self, content: str) -> str:
        """Extract trading-relevant information from article content"""
        # Trading signal keywords
        signal_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'guidance', 'outlook',
            'price target', 'upgrade', 'downgrade', 'rating', 'analyst',
            'merger', 'acquisition', 'partnership', 'contract', 'deal',
            'FDA approval', 'regulatory', 'lawsuit', 'settlement',
            'launch', 'release', 'product', 'service', 'expansion',
            'bankruptcy', 'debt', 'financing', 'dividend', 'split'
        ]
        
        # Extract sentences containing trading signals
        sentences = content.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in signal_keywords):
                relevant_sentences.append(sentence)
                if len(' '.join(relevant_sentences)) > 400:  # Stop at reasonable length
                    break
        
        if not relevant_sentences:
            # Fallback: take first few sentences
            relevant_sentences = sentences[:2]
        
        return '. '.join(relevant_sentences).strip()
    
    def _generate_compressed_report(self, articles: List[Dict], metadata: Dict) -> str:
        """Generate token-optimized news report"""
        company = metadata.get('query', 'Unknown')
        
        report = f"# MARKET NEWS SUMMARY - {company}\n\n"
        report += f"**Articles**: {len(articles)} key stories\n"
        report += f"**Focus**: Trading catalysts and market signals\n\n"
        
        for i, article in enumerate(articles, 1):
            report += f"## {i}. {article['title']}\n"
            report += f"**Source**: {article['source']} | {article['date']}\n"
            report += f"**Key Points**: {article['key_points']}\n\n"
        
        return report
    
    def _create_fallback_summary(self, news_report: str) -> str:
        """Fallback when JSON parsing fails"""
        # Extract headlines using regex patterns
        headlines = re.findall(r'Title: ([^\n]+)', news_report)
        
        summary = f"# MARKET NEWS SUMMARY\n\n"
        summary += f"**Headlines** ({len(headlines)} articles):\n"
        
        for i, headline in enumerate(headlines[:self.max_articles], 1):
            summary += f"{i}. {headline}\n"
        
        if len(summary) > 2000:
            summary = summary[:1997] + "..."
        
        return summary
```

### Phase 1B: Integration Points (Week 1, Day 3-4)

#### Update Research Components

```python
# File: src/agent/researchers/bull_researcher.py (line 46)
# File: src/agent/researchers/bear_researcher.py (line 46) 
# File: src/agent/managers/risk_manager.py (line 50)

# Before:
curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{filtered_news}\n\n{fundamentals_report}"

# After:
from ..utils.news_compressor import NewsCompressor

news_compressor = NewsCompressor()
compressed_news = news_compressor.compress_news_report(filtered_news)
curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{compressed_news}\n\n{fundamentals_report}"
```

#### Update Parallel Risk Debators

```python
# File: src/agent/graph/nodes/parallel_risk_debators.py (lines 54-57, 83-86, 112-115)

# Before:
News: {shared_context.get('news_report', '')}

# After:
from ...utils.news_compressor import NewsCompressor

# In create_parallel_risk_debators function, add compression:
news_compressor = NewsCompressor()
compressed_news = news_compressor.compress_news_report(shared_context.get('news_report', ''))

# Update all three debator prompts:
News: {compressed_news}
```

### Phase 1C: Token Monitoring (Week 1, Day 5)

#### Add Compression Metrics

```python
# File: src/agent/utils/news_compressor.py

import logging
logger = logging.getLogger(__name__)

class NewsCompressor:
    def compress_news_report(self, news_report: str) -> str:
        original_size = len(news_report)
        
        # ... compression logic ...
        
        compressed_size = len(compressed_report)
        reduction_pct = (1 - compressed_size/original_size) * 100
        token_estimate_original = original_size // 4
        token_estimate_compressed = compressed_size // 4
        
        logger.info(f"📰 NEWS COMPRESSION: {original_size} → {compressed_size} chars "
                   f"({reduction_pct:.1f}% reduction, ~{token_estimate_original} → ~{token_estimate_compressed} tokens)")
        
        return compressed_report
```

---

## 📊 Expected Results

### Token Reduction Calculation:

```
Current State:
├── News Report Size: 12,670 tokens per copy
├── Component Consumers: 8 components
├── Total News Tokens: 101,360 tokens
└── System Impact: 46.5% of all tokens

Optimized State:
├── News Report Size: 2,000 tokens per copy (84% reduction)
├── Component Consumers: 8 components  
├── Total News Tokens: 16,000 tokens (84% reduction)
└── System Impact: 7.3% of total tokens

Net Savings: 85,360 tokens (39% of entire system)
```

### Component-Level Impact:

| Component | Current | After News Fix | Reduction |
|-----------|---------|----------------|-----------|
| parallel_risk_debators | 93,737 | 55,727 | -38,010 (41%) |
| bull_researcher | 29,923 | 17,253 | -12,670 (42%) |
| bear_researcher | 30,966 | 18,296 | -12,670 (41%) |
| risk_manager | 30,873 | 5,533 | -25,340 (82%) |
| research_manager | 29,033 | ~20,000 | -9,033 (31%) |
| **TOTAL SYSTEM** | **218,130** | **~120,000** | **-98,130 (45%)** |

---

## 🔍 Quality Preservation Strategy

### Information Retention Approach:

1. **Preserve Critical Signals**:
   - Earnings announcements and guidance
   - Analyst ratings and price targets  
   - Major corporate actions (M&A, partnerships)
   - Regulatory approvals and legal events

2. **Focus on Trading Impact**:
   - Price-moving catalysts only
   - Market sentiment drivers
   - Sector and competitive dynamics
   - Risk factors and opportunities

3. **Remove Non-Essential Content**:
   - General corporate background
   - Historical context not relevant to current trade
   - Redundant information across articles
   - Non-financial operational details

### Validation Approach:

1. **A/B Testing**:
   - Run compressed and full versions in parallel
   - Compare trading decision quality
   - Monitor for information loss

2. **Content Validation**:
   - Ensure key market catalysts preserved
   - Verify trading signal extraction accuracy
   - Check for critical information omissions

3. **Performance Monitoring**:
   - Track decision accuracy vs. baseline
   - Monitor for quality degradation signals
   - Measure information sufficiency scores

---

## ⚠️ Risk Mitigation

### Potential Risks:

1. **Information Loss**: Critical market information might be filtered out
   - **Mitigation**: Conservative filtering, manual validation of key events
   - **Rollback**: Quick switch to full reports if quality degrades

2. **Context Fragmentation**: Compressed reports might lose narrative coherence
   - **Mitigation**: Preserve article relationships, maintain logical flow
   - **Validation**: Human review of compressed outputs

3. **Signal Extraction Errors**: Important trading signals might be missed
   - **Mitigation**: Comprehensive keyword lists, pattern recognition
   - **Testing**: Compare signal detection vs. full articles

### Fallback Strategy:

```python
# Emergency fallback configuration
NEWS_COMPRESSION_CONFIG = {
    "enabled": True,  # Can be disabled instantly
    "fallback_on_error": True,  # Use full report on compression failure
    "quality_threshold": 0.95,  # Auto-disable if quality drops
    "monitoring_enabled": True  # Track all compression metrics
}
```

---

## 📈 Implementation Timeline

### Day 1-2: Core Implementation
- [ ] Create NewsCompressor utility class
- [ ] Implement article compression logic
- [ ] Add trading signal extraction
- [ ] Create compression metrics logging

### Day 3-4: Integration
- [ ] Update bull_researcher context usage
- [ ] Update bear_researcher context usage  
- [ ] Update risk_manager context usage
- [ ] Update parallel_risk_debators prompts

### Day 5: Testing & Validation
- [ ] Deploy to test environment
- [ ] Run A/B comparison tests
- [ ] Validate information preservation
- [ ] Monitor token reduction metrics

### Day 6-7: Production Deployment
- [ ] Deploy to 10% of production traffic
- [ ] Monitor for 24 hours
- [ ] Scale to 50% if stable
- [ ] Full deployment if no issues

---

## 📊 Success Metrics

### Primary KPIs:
- **Token Reduction**: >80% news report compression
- **System Impact**: >35% total system token reduction
- **Quality Score**: >95% vs. baseline trading decisions
- **Cost Savings**: >$15K annually from news optimization alone

### Monitoring Dashboard:
- News compression ratio (target: 84%)
- Total system token count (target: <120K)
- Component-level token usage
- Quality preservation metrics
- Error rates and fallback usage

---

## 🔗 Next Steps

After news report optimization, proceed to:

1. **[Context Sharing Architecture](./context_sharing_architecture.md)** - Eliminate remaining duplication
2. **[Advanced Token Optimizations](./advanced_optimizations.md)** - Fine-tune remaining components
3. **[Quality Monitoring System](./quality_monitoring.md)** - Continuous optimization validation

---

This news report optimization represents the **single highest-impact token optimization** with clear implementation path and immediate benefits. Success here will reduce system tokens by 45% while preserving trading decision quality.