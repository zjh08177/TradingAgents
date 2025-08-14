# Context Sharing Architecture
## Eliminating Token Duplication Across Components

**Priority**: 🟠 **HIGH** - Second phase optimization  
**Impact**: 30,000 token reduction (14% additional savings)  
**Timeline**: Week 2 implementation  
**Complexity**: High (architectural changes, multiple component coordination)

---

## 🚨 Problem Statement

After news report optimization, the system still suffers from **massive context duplication** where the same compressed reports get sent to multiple components independently. This creates unnecessary token consumption through repeated context transmission.

### Current Post-News-Fix State:
- **Compressed Reports**: Market (116) + Sentiment (730) + News (2000) + Fundamentals (171) = ~3,017 tokens per context
- **Component Duplication**: 8 components × 3,017 tokens = 24,136 tokens in duplicated context
- **Additional Waste**: System prompts, instructions, and formatting multiply this further
- **Remaining Opportunity**: 30,000+ tokens through intelligent context sharing

---

## 🔍 Current Context Flow Analysis

### Duplication Pattern (Post-News-Fix):

```
Compressed Context Package (~3,017 tokens):
├── Market Report: 116 tokens
├── Sentiment Report: 730 tokens  
├── Compressed News: 2,000 tokens
└── Fundamentals Report: 171 tokens

Current Distribution:
├── parallel_risk_debators: 3,017 × 3 debators = 9,051 tokens
├── bull_researcher: 3,017 tokens
├── bear_researcher: 3,017 tokens
├── risk_manager: 3,017 × 2 runs = 6,034 tokens
├── research_manager: Processes bull + bear outputs
└── Total Context Duplication: ~24,136 tokens
```

### Component-Specific Context Needs:

| Component | Needs Market | Needs Sentiment | Needs News | Needs Fundamentals | Focus Area |
|-----------|-------------|----------------|------------|-------------------|------------|
| **Risk Debators** | ✅ Full | ✅ Full | ✅ Catalysts | ✅ Key Ratios | Risk scenarios |
| **Bull Researcher** | ✅ Bullish | ✅ Positive | ✅ Positive | ✅ Strengths | Growth opportunities |
| **Bear Researcher** | ✅ Bearish | ✅ Negative | ✅ Risks | ✅ Weaknesses | Risk factors |
| **Risk Manager** | ✅ Volatility | ⭕ Risk Levels | ✅ Risk Events | ✅ Stability | Risk assessment |
| **Research Manager** | ⭕ Summary | ⭕ Summary | ⭕ Key Points | ⭕ Summary | Synthesis only |

**Key Insight**: Each component only needs a **subset** of the full context, customized for their specific analysis focus.

---

## 🏗️ Proposed Architecture: Smart Context Manager

### Core Design Principles:

1. **Single Source of Truth**: One context manager holds all data
2. **Component-Specific Views**: Each component gets only relevant information
3. **Intelligent Compression**: Context tailored to component needs
4. **Caching Strategy**: Reuse processed context across similar requests
5. **Token Budgeting**: Hard limits per component to prevent expansion

### Architecture Overview:

```
┌─────────────────────────────────────────────────────────┐
│                Smart Context Manager                     │
├─────────────────────────────────────────────────────────┤
│  Raw Data Storage:                                      │
│  ├── Market Report (116 tokens)                        │
│  ├── Sentiment Report (730 tokens)                     │
│  ├── Compressed News (2000 tokens)                     │
│  └── Fundamentals Report (171 tokens)                  │
├─────────────────────────────────────────────────────────┤
│  Component View Generators:                            │
│  ├── Risk View Generator (focus: scenarios)            │
│  ├── Bull View Generator (focus: opportunities)        │
│  ├── Bear View Generator (focus: risks)                │
│  ├── Risk Mgmt View Generator (focus: stability)       │
│  └── Summary View Generator (focus: synthesis)         │
├─────────────────────────────────────────────────────────┤
│  Token Budget Enforcement:                             │
│  ├── Risk Debators: 800 tokens per debator            │
│  ├── Researchers: 600 tokens each                     │
│  ├── Risk Manager: 500 tokens per run                 │
│  └── Research Manager: 400 tokens                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Implementation Plan

### Phase 2A: Core Context Manager (Week 2, Day 1-2)

#### Create Smart Context Manager

```python
# File: src/agent/utils/smart_context_manager.py

from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ComponentType(Enum):
    RISK_AGGRESSIVE = "risk_aggressive"
    RISK_CONSERVATIVE = "risk_conservative"
    RISK_NEUTRAL = "risk_neutral"
    BULL_RESEARCHER = "bull_researcher"
    BEAR_RESEARCHER = "bear_researcher"
    RISK_MANAGER = "risk_manager"
    RESEARCH_MANAGER = "research_manager"

class SmartContextManager:
    """
    Intelligent context sharing with component-specific views
    Reduces token consumption through targeted context delivery
    """
    
    def __init__(self):
        self.raw_data = {}
        self.component_views = {}
        self.token_budgets = {
            ComponentType.RISK_AGGRESSIVE: 800,
            ComponentType.RISK_CONSERVATIVE: 800,
            ComponentType.RISK_NEUTRAL: 800,
            ComponentType.BULL_RESEARCHER: 600,
            ComponentType.BEAR_RESEARCHER: 600,
            ComponentType.RISK_MANAGER: 500,
            ComponentType.RESEARCH_MANAGER: 400,
        }
    
    def update_raw_data(self, market_report: str, sentiment_report: str, 
                       news_report: str, fundamentals_report: str):
        """Store raw data from all analysts"""
        self.raw_data = {
            'market': market_report,
            'sentiment': sentiment_report,
            'news': news_report,
            'fundamentals': fundamentals_report
        }
        # Clear cached views when raw data updates
        self.component_views = {}
    
    def get_context_for_component(self, component_type: ComponentType) -> str:
        """Get optimized context for specific component"""
        if component_type in self.component_views:
            return self.component_views[component_type]
        
        # Generate component-specific view
        context = self._generate_component_view(component_type)
        
        # Enforce token budget
        token_budget = self.token_budgets[component_type]
        context = self._enforce_token_budget(context, token_budget, component_type.value)
        
        # Cache for reuse
        self.component_views[component_type] = context
        
        logger.info(f"🎯 Context generated for {component_type.value}: "
                   f"{len(context)} chars (~{len(context)//4} tokens)")
        
        return context
    
    def _generate_component_view(self, component_type: ComponentType) -> str:
        """Generate context tailored to component needs"""
        
        if component_type in [ComponentType.RISK_AGGRESSIVE, ComponentType.RISK_CONSERVATIVE, ComponentType.RISK_NEUTRAL]:
            return self._generate_risk_view(component_type)
        elif component_type == ComponentType.BULL_RESEARCHER:
            return self._generate_bull_view()
        elif component_type == ComponentType.BEAR_RESEARCHER:
            return self._generate_bear_view()
        elif component_type == ComponentType.RISK_MANAGER:
            return self._generate_risk_manager_view()
        elif component_type == ComponentType.RESEARCH_MANAGER:
            return self._generate_research_manager_view()
        else:
            return self._generate_default_view()
    
    def _generate_risk_view(self, risk_type: ComponentType) -> str:
        """Generate context for risk debators with scenario focus"""
        market = self._extract_market_signals(self.raw_data['market'])
        sentiment = self._extract_sentiment_signals(self.raw_data['sentiment'])
        news = self._extract_news_catalysts(self.raw_data['news'])
        fundamentals = self._extract_key_metrics(self.raw_data['fundamentals'])
        
        if risk_type == ComponentType.RISK_AGGRESSIVE:
            focus = "opportunities and growth catalysts"
            market = self._filter_bullish_signals(market)
            sentiment = self._filter_positive_sentiment(sentiment)
        elif risk_type == ComponentType.RISK_CONSERVATIVE:
            focus = "risks and downside protection"
            market = self._filter_bearish_signals(market)
            sentiment = self._filter_risk_sentiment(sentiment)
        else:  # NEUTRAL
            focus = "balanced risk-reward analysis"
            # Keep full context for neutral perspective
        
        return f"""**Market Signals** ({focus}): {market}

**Sentiment Indicators**: {sentiment}

**News Catalysts**: {news}

**Key Metrics**: {fundamentals}"""
    
    def _generate_bull_view(self) -> str:
        """Generate context focused on bullish opportunities"""
        market_bullish = self._extract_bullish_indicators(self.raw_data['market'])
        positive_sentiment = self._extract_positive_sentiment(self.raw_data['sentiment'])
        growth_catalysts = self._extract_positive_news(self.raw_data['news'])
        strength_metrics = self._extract_strength_metrics(self.raw_data['fundamentals'])
        
        return f"""**Growth Opportunities**: {market_bullish}

**Positive Sentiment**: {positive_sentiment}

**Growth Catalysts**: {growth_catalysts}

**Financial Strengths**: {strength_metrics}"""
    
    def _generate_bear_view(self) -> str:
        """Generate context focused on risk factors"""
        market_risks = self._extract_bearish_indicators(self.raw_data['market'])
        negative_sentiment = self._extract_negative_sentiment(self.raw_data['sentiment'])
        risk_catalysts = self._extract_negative_news(self.raw_data['news'])
        weakness_metrics = self._extract_weakness_metrics(self.raw_data['fundamentals'])
        
        return f"""**Market Risks**: {market_risks}

**Risk Sentiment**: {negative_sentiment}

**Risk Catalysts**: {risk_catalysts}

**Financial Concerns**: {weakness_metrics}"""
    
    def _generate_risk_manager_view(self) -> str:
        """Generate context focused on risk assessment"""
        volatility_data = self._extract_volatility_metrics(self.raw_data['market'])
        risk_levels = self._extract_risk_levels(self.raw_data['sentiment'])
        risk_events = self._extract_risk_events(self.raw_data['news'])
        stability_metrics = self._extract_stability_metrics(self.raw_data['fundamentals'])
        
        return f"""**Volatility**: {volatility_data}

**Risk Levels**: {risk_levels}

**Risk Events**: {risk_events}

**Stability**: {stability_metrics}"""
    
    def _generate_research_manager_view(self) -> str:
        """Generate summary-level context for synthesis"""
        market_summary = self._summarize_market_data(self.raw_data['market'])
        sentiment_summary = self._summarize_sentiment(self.raw_data['sentiment'])
        news_summary = self._summarize_news(self.raw_data['news'])
        fundamentals_summary = self._summarize_fundamentals(self.raw_data['fundamentals'])
        
        return f"""**Market Summary**: {market_summary}

**Sentiment Summary**: {sentiment_summary}

**News Summary**: {news_summary}

**Fundamentals Summary**: {fundamentals_summary}"""
    
    # Content extraction methods (implement based on specific needs)
    def _extract_market_signals(self, market_report: str) -> str:
        """Extract key market signals from technical analysis"""
        # Extract price, volume, technical indicators
        lines = market_report.split('\n')
        signals = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['price:', 'volume:', 'signal:', 'hold', 'buy', 'sell']):
                signals.append(line.strip())
        return '. '.join(signals)[:200]
    
    def _extract_sentiment_signals(self, sentiment_report: str) -> str:
        """Extract sentiment score and key indicators"""
        # Extract sentiment scores and confidence levels
        lines = sentiment_report.split('\n')
        for line in lines:
            if 'sentiment score' in line.lower() or 'overall sentiment' in line.lower():
                return line.strip()[:150]
        return "Sentiment data available"[:100]
    
    def _extract_news_catalysts(self, news_report: str) -> str:
        """Extract key market-moving events"""
        # Extract headlines and key catalysts
        lines = news_report.split('\n')
        catalysts = []
        for line in lines:
            if line.startswith('## ') or 'Key Points:' in line:
                catalysts.append(line.replace('## ', '').replace('Key Points:', '').strip())
                if len(catalysts) >= 3:  # Limit to top 3 catalysts
                    break
        return '. '.join(catalysts)[:300]
    
    def _extract_key_metrics(self, fundamentals_report: str) -> str:
        """Extract essential financial metrics"""
        # Extract P/E, P/B, key ratios
        lines = fundamentals_report.split('\n')
        metrics = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['p/e', 'p/b', 'roe', 'debt', 'price target']):
                metrics.append(line.strip())
                if len(metrics) >= 3:
                    break
        return '. '.join(metrics)[:200]
    
    def _enforce_token_budget(self, content: str, budget: int, component_name: str) -> str:
        """Enforce token budget for component"""
        max_chars = budget * 4  # Rough token-to-char conversion
        if len(content) <= max_chars:
            return content
        
        truncated = content[:max_chars-20] + "\n\n[Content truncated to fit token budget]"
        logger.warning(f"⚠️ Content truncated for {component_name}: {len(content)} → {len(truncated)} chars")
        return truncated
    
    # Additional filtering methods for component-specific views
    def _filter_bullish_signals(self, content: str) -> str:
        """Filter for bullish market signals"""
        bullish_keywords = ['buy', 'bullish', 'uptrend', 'positive', 'growth', 'strong']
        lines = content.split('.')
        filtered = [line for line in lines if any(kw in line.lower() for kw in bullish_keywords)]
        return '. '.join(filtered)
    
    def _filter_bearish_signals(self, content: str) -> str:
        """Filter for bearish market signals"""
        bearish_keywords = ['sell', 'bearish', 'downtrend', 'negative', 'decline', 'weak']
        lines = content.split('.')
        filtered = [line for line in lines if any(kw in line.lower() for kw in bearish_keywords)]
        return '. '.join(filtered)
    
    # ... implement additional filtering methods as needed
```

### Phase 2B: Component Integration (Week 2, Day 3-4)

#### Update Parallel Risk Debators

```python
# File: src/agent/graph/nodes/parallel_risk_debators.py

from ...utils.smart_context_manager import SmartContextManager, ComponentType

def create_parallel_risk_debators(aggressive_llm, conservative_llm, neutral_llm):
    
    async def parallel_risk_node(state: AgentState) -> AgentState:
        # ... existing setup code ...
        
        # Initialize smart context manager
        context_manager = SmartContextManager()
        context_manager.update_raw_data(
            market_report=shared_context.get('market_report', ''),
            sentiment_report=shared_context.get('sentiment_report', ''),
            news_report=shared_context.get('news_report', ''),
            fundamentals_report=shared_context.get('fundamentals_report', '')
        )
        
        # Define async execution with optimized context
        async def run_aggressive():
            try:
                logger.info("🔴 Starting Aggressive Risk Analyst")
                
                # Get optimized context for aggressive risk analysis
                context = context_manager.get_context_for_component(ComponentType.RISK_AGGRESSIVE)
                
                prompt = f"""As the Aggressive Risk Analyst, champion high-reward opportunities while acknowledging risks.

Investment Plan: {investment_plan}
Trader Decision: {trader_decision}

{context}

Provide your aggressive risk perspective emphasizing:
1. High-reward opportunities and growth potential
2. Why the risks are worth taking
3. Potential upside scenarios
4. Risk mitigation strategies for aggressive positions"""
                
                # ... rest of execution logic
        
        async def run_conservative():
            try:
                logger.info("🔵 Starting Conservative Risk Analyst")
                
                # Get optimized context for conservative risk analysis
                context = context_manager.get_context_for_component(ComponentType.RISK_CONSERVATIVE)
                
                prompt = f"""As the Conservative Risk Analyst, emphasize capital preservation and risk mitigation.

Investment Plan: {investment_plan}
Trader Decision: {trader_decision}

{context}

Provide your conservative risk perspective focusing on:
1. Capital preservation strategies
2. Potential downside risks and worst-case scenarios
3. Risk mitigation and hedging strategies
4. Safe position sizing recommendations"""
                
                # ... rest of execution logic
        
        async def run_neutral():
            try:
                logger.info("⚪ Starting Neutral Risk Analyst")
                
                # Get optimized context for neutral risk analysis
                context = context_manager.get_context_for_component(ComponentType.RISK_NEUTRAL)
                
                prompt = f"""As the Neutral Risk Analyst, provide a balanced perspective weighing both risks and opportunities.

Investment Plan: {investment_plan}
Trader Decision: {trader_decision}

{context}

Provide your balanced risk perspective including:
1. Objective risk-reward analysis
2. Balanced position sizing recommendations
3. Conditional strategies based on market scenarios
4. Data-driven recommendations without bias"""
                
                # ... rest of execution logic
        
        # ... rest of parallel execution logic
```

#### Update Research Components

```python
# File: src/agent/researchers/bull_researcher.py

from ..utils.smart_context_manager import SmartContextManager, ComponentType

@debug_node("Bull_Researcher")
async def bull_researcher_node(state):
    # ... existing setup code ...
    
    # Initialize smart context manager
    context_manager = SmartContextManager()
    context_manager.update_raw_data(
        market_report=market_research_report,
        sentiment_report=sentiment_report,
        news_report=filtered_news,
        fundamentals_report=fundamentals_report
    )
    
    # Get optimized context for bull research
    optimized_context = context_manager.get_context_for_component(ComponentType.BULL_RESEARCHER)
    
    # Use optimized context instead of curr_situation
    past_memories = memory.get_memories(optimized_context, n_matches=2)
    
    # ... rest of logic with optimized_context
```

```python
# File: src/agent/researchers/bear_researcher.py

# Similar implementation for bear researcher using ComponentType.BEAR_RESEARCHER
```

```python
# File: src/agent/managers/risk_manager.py

# Similar implementation for risk manager using ComponentType.RISK_MANAGER
```

### Phase 2C: Advanced Context Optimization (Week 2, Day 5)

#### Implement Content-Specific Extractors

```python
# File: src/agent/utils/content_extractors.py

import re
from typing import List, Dict, Any

class ContentExtractors:
    """Specialized content extraction for different analysis needs"""
    
    @staticmethod
    def extract_bullish_indicators(market_report: str) -> str:
        """Extract bullish technical indicators"""
        bullish_patterns = [
            r'buy\s+signal', r'bullish\s+\w+', r'uptrend', r'breakout',
            r'support\s+level', r'positive\s+momentum', r'strong\s+volume'
        ]
        
        matches = []
        for pattern in bullish_patterns:
            found = re.findall(pattern, market_report, re.IGNORECASE)
            matches.extend(found)
        
        return ', '.join(matches[:5])  # Top 5 bullish signals
    
    @staticmethod
    def extract_bearish_indicators(market_report: str) -> str:
        """Extract bearish technical indicators"""
        bearish_patterns = [
            r'sell\s+signal', r'bearish\s+\w+', r'downtrend', r'breakdown',
            r'resistance\s+level', r'negative\s+momentum', r'weak\s+volume'
        ]
        
        matches = []
        for pattern in bearish_patterns:
            found = re.findall(pattern, market_report, re.IGNORECASE)
            matches.extend(found)
        
        return ', '.join(matches[:5])  # Top 5 bearish signals
    
    @staticmethod
    def extract_positive_sentiment(sentiment_report: str) -> str:
        """Extract positive sentiment indicators"""
        # Extract positive sentiment scores, bullish mentions, etc.
        positive_lines = []
        for line in sentiment_report.split('\n'):
            if any(word in line.lower() for word in ['positive', 'bullish', 'optimistic', 'confident']):
                positive_lines.append(line.strip())
        
        return ' | '.join(positive_lines[:3])
    
    @staticmethod
    def extract_negative_sentiment(sentiment_report: str) -> str:
        """Extract negative sentiment indicators"""
        # Extract negative sentiment scores, bearish mentions, etc.
        negative_lines = []
        for line in sentiment_report.split('\n'):
            if any(word in line.lower() for word in ['negative', 'bearish', 'pessimistic', 'concerned']):
                negative_lines.append(line.strip())
        
        return ' | '.join(negative_lines[:3])
    
    @staticmethod
    def extract_key_financial_ratios(fundamentals_report: str) -> str:
        """Extract essential financial ratios"""
        ratio_patterns = [
            r'P/E[:\s]*([0-9.]+)', r'P/B[:\s]*([0-9.]+)', 
            r'ROE[:\s]*([0-9.%]+)', r'Debt/Equity[:\s]*([0-9.]+)'
        ]
        
        ratios = []
        for pattern in ratio_patterns:
            matches = re.findall(pattern, fundamentals_report, re.IGNORECASE)
            if matches:
                ratios.append(f"{pattern.split('[')[0]}: {matches[0]}")
        
        return ', '.join(ratios)
    
    @staticmethod
    def extract_price_catalysts(news_report: str) -> List[str]:
        """Extract news events likely to impact price"""
        catalyst_keywords = [
            'earnings', 'guidance', 'merger', 'acquisition', 'FDA approval',
            'partnership', 'contract', 'lawsuit', 'rating', 'price target'
        ]
        
        catalysts = []
        lines = news_report.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in catalyst_keywords):
                # Clean up the line and extract key information
                clean_line = re.sub(r'^#+\s*', '', line).strip()  # Remove markdown headers
                if len(clean_line) > 20 and len(clean_line) < 150:  # Reasonable length
                    catalysts.append(clean_line)
                    if len(catalysts) >= 5:  # Limit to top 5 catalysts
                        break
        
        return catalysts
```

---

## 📊 Expected Results

### Token Reduction Analysis:

#### Before Context Sharing:
```
Current Context Duplication (Post-News-Fix):
├── Risk Debators: 3,017 × 3 = 9,051 tokens
├── Bull Researcher: 3,017 tokens
├── Bear Researcher: 3,017 tokens  
├── Risk Manager: 3,017 × 2 = 6,034 tokens
├── Research Manager: ~3,000 tokens (processing outputs)
└── Total: ~24,119 tokens in context duplication
```

#### After Smart Context Manager:
```
Optimized Context Distribution:
├── Risk Debators: 800 × 3 = 2,400 tokens
├── Bull Researcher: 600 tokens
├── Bear Researcher: 600 tokens
├── Risk Manager: 500 × 2 = 1,000 tokens  
├── Research Manager: 400 tokens
└── Total: ~5,000 tokens (79% reduction)

Net Savings: ~19,000 tokens (8.7% of total system)
```

### Component-Level Impact (After Both News + Context Optimizations):

| Component | Original | After News | After Context | Total Reduction |
|-----------|----------|------------|---------------|-----------------|
| parallel_risk_debators | 93,737 | 55,727 | 45,000 | 52% |
| bull_researcher | 29,923 | 17,253 | 12,000 | 60% |
| bear_researcher | 30,966 | 18,296 | 12,500 | 60% |
| risk_manager | 30,873 | 5,533 | 8,000 | 74% |
| research_manager | 29,033 | 20,000 | 15,000 | 48% |
| **TOTAL SYSTEM** | **218,130** | **120,000** | **92,500** | **58%** |

---

## 🔍 Quality Preservation Strategy

### Context Adequacy Validation:

1. **Information Completeness Scoring**:
   - Ensure each component receives sufficient context for their analysis
   - Validate that key information isn't lost in filtering
   - Monitor for degradation in analysis quality

2. **Component-Specific Validation**:
   - **Risk Debators**: Verify they can still identify key risk scenarios
   - **Bull Researcher**: Ensure growth opportunities are preserved  
   - **Bear Researcher**: Confirm risk factors are adequately covered
   - **Risk Manager**: Validate risk assessment completeness

3. **Context Relevance Testing**:
   - A/B test focused vs. full context for each component
   - Measure analysis quality and decision consistency
   - Adjust filtering algorithms based on results

### Fallback Mechanisms:

```python
# Smart Context Manager with Quality Safeguards

class SmartContextManager:
    def __init__(self):
        self.quality_monitoring = True
        self.fallback_threshold = 0.95  # Quality score threshold
        self.fallback_enabled = True
    
    def get_context_for_component(self, component_type: ComponentType) -> str:
        if self.should_use_fallback(component_type):
            logger.warning(f"Using fallback full context for {component_type.value}")
            return self._generate_full_context()
        
        return self._generate_optimized_context(component_type)
    
    def should_use_fallback(self, component_type: ComponentType) -> bool:
        # Check if recent quality scores are below threshold
        if not self.fallback_enabled:
            return False
        
        recent_quality = self._get_recent_quality_score(component_type)
        return recent_quality < self.fallback_threshold
```

---

## ⚠️ Implementation Risks & Mitigation

### Risk 1: Context Fragmentation
- **Issue**: Components might lose important cross-domain insights
- **Mitigation**: Include key cross-references in each context view
- **Monitoring**: Track decision consistency across components

### Risk 2: Over-Optimization
- **Issue**: Excessive filtering might remove critical information
- **Mitigation**: Conservative token budgets, gradual reduction approach
- **Validation**: Continuous quality monitoring and adjustment

### Risk 3: Complexity Overhead
- **Issue**: Smart context management adds processing complexity
- **Mitigation**: Simple, fast extraction algorithms with caching
- **Performance**: Monitor context generation time (target: <50ms)

### Risk 4: Maintenance Burden  
- **Issue**: Content extractors need ongoing tuning
- **Mitigation**: Generic extraction patterns, automated validation
- **Evolution**: Regular review and updates based on usage patterns

---

## 📈 Implementation Timeline

### Week 2 Schedule:

#### Day 1-2: Core Development
- [ ] Implement SmartContextManager base class
- [ ] Create ComponentType enum and token budgets
- [ ] Develop basic content extraction methods
- [ ] Add caching and token budget enforcement

#### Day 3-4: Component Integration  
- [ ] Update parallel_risk_debators to use context manager
- [ ] Integrate bull_researcher with optimized context
- [ ] Integrate bear_researcher with optimized context
- [ ] Update risk_manager with focused context

#### Day 5: Testing & Validation
- [ ] Deploy to test environment with monitoring
- [ ] Run quality validation tests
- [ ] Monitor token reduction metrics
- [ ] Validate context adequacy for each component

---

## 📊 Success Metrics

### Primary Metrics:
- **Token Reduction**: >15,000 tokens (7%+ system reduction)
- **Context Efficiency**: >75% reduction in duplicated context
- **Quality Preservation**: >95% of baseline analysis quality
- **Component Satisfaction**: Each component receives adequate context

### Monitoring Dashboard:
- Context generation time per component
- Token usage per component type  
- Quality scores by component
- Fallback usage frequency
- Context adequacy scores

---

## 🔗 Next Phase

After context sharing implementation, proceed to:

1. **[Advanced Token Optimizations](./advanced_optimizations.md)** - Fine-tune remaining components
2. **[Quality Monitoring System](./quality_monitoring.md)** - Continuous optimization validation
3. **[Performance Benchmarking](./performance_benchmarking.md)** - Measure and maintain gains

---

This context sharing architecture represents the **second highest-impact optimization** after news report compression, providing significant additional token savings while maintaining analysis quality through intelligent, component-specific context delivery.