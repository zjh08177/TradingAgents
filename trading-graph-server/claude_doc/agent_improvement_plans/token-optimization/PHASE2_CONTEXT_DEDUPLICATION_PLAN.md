# 🚀 Phase 2: Context Deduplication Implementation Plan

**Priority**: 🔴 **CRITICAL** - Highest impact optimization after news  
**Target Component**: parallel_risk_debators (93,737 tokens → 20,000 tokens)  
**Expected Impact**: 74% reduction in risk debator tokens  
**Implementation Time**: 2-3 days

---

## 🎯 Problem Analysis

### Current State (WASTEFUL)
```python
# Each debator receives FULL context (31,245 tokens each):
prompt = f"""
Investment Plan: {investment_plan}         # 2,000 tokens
Trader Decision: {trader_decision}         # 1,500 tokens  
Market Data: {shared_context.get('market_report', '')}      # 5,000 tokens
Sentiment: {shared_context.get('sentiment_report', '')}     # 3,000 tokens
News: {shared_context.get('news_report', '')}              # 719 tokens (after optimization)
Fundamentals: {shared_context.get('fundamentals_report', '')} # 4,000 tokens
"""
# TOTAL: 31,245 tokens × 3 debators = 93,737 tokens!
```

### Root Cause
- **100% context duplication** across 3 debators
- **No perspective-specific filtering**
- **Full reports passed when summaries would suffice**
- **No caching of processed context**

---

## 🏗️ Solution Architecture

### SmartContextManager Design
```python
class SmartContextManager:
    """
    Intelligent context distribution system
    - Component-specific context views
    - Automatic compression and caching
    - Token budget enforcement
    - Quality preservation
    """
    
    def __init__(self):
        self.context_cache = {}
        self.compressed_cache = {}
        self.token_budgets = {
            "aggressive_debator": 6000,
            "conservative_debator": 6000,
            "neutral_debator": 6000,
            "bull_researcher": 8000,
            "bear_researcher": 8000,
            "risk_manager": 10000
        }
    
    def get_context_for_debator(self, debator_type: str, full_context: dict) -> str:
        """
        Returns optimized context for specific debator perspective
        74% smaller than full context
        """
        if debator_type == "aggressive":
            return self._extract_growth_context(full_context)
        elif debator_type == "conservative":
            return self._extract_risk_context(full_context)
        elif debator_type == "neutral":
            return self._extract_balanced_context(full_context)
```

---

## 📋 Implementation Steps

### Step 1: Create SmartContextManager (Day 1)

#### File: `src/agent/utils/smart_context_manager.py`
```python
#!/usr/bin/env python3
"""
Smart Context Manager - Eliminates context duplication
Reduces token usage by 70%+ through intelligent distribution
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class ContextView:
    """Optimized context for a specific component"""
    component: str
    content: str
    tokens: int
    cache_key: str

class SmartContextManager:
    """
    Manages context distribution to eliminate duplication
    Core optimization for Phase 2
    """
    
    def __init__(self):
        self.context_cache = {}
        self.extraction_rules = self._setup_extraction_rules()
        self.token_budgets = {
            "aggressive_debator": 6000,
            "conservative_debator": 6000,
            "neutral_debator": 6000,
            "bull_researcher": 8000,
            "bear_researcher": 8000,
            "risk_manager": 10000,
            "research_manager": 12000
        }
        logger.info("🧠 SmartContextManager initialized")
    
    def _setup_extraction_rules(self):
        """Define what each component needs from context"""
        return {
            "aggressive_debator": {
                "market": ["bullish_signals", "growth_indicators", "momentum"],
                "news": ["positive_catalysts", "upgrades", "expansion"],
                "fundamentals": ["revenue_growth", "margin_expansion"],
                "focus": "upside_opportunities"
            },
            "conservative_debator": {
                "market": ["bearish_signals", "risk_indicators", "volatility"],
                "news": ["negative_catalysts", "downgrades", "concerns"],
                "fundamentals": ["debt_levels", "cash_burn", "risks"],
                "focus": "downside_protection"
            },
            "neutral_debator": {
                "market": ["key_levels", "trend_summary", "volume"],
                "news": ["balanced_view", "consensus"],
                "fundamentals": ["valuation", "peer_comparison"],
                "focus": "balanced_perspective"
            }
        }
    
    def get_context_for_debator(self, debator_type: str, full_context: Dict) -> str:
        """
        Get optimized context for specific debator
        Reduces tokens by 70-80% while preserving relevant information
        """
        cache_key = self._generate_cache_key(debator_type, full_context)
        
        # Return cached if available
        if cache_key in self.context_cache:
            logger.info(f"✅ Cache hit for {debator_type}")
            return self.context_cache[cache_key]
        
        # Extract relevant context
        if debator_type == "aggressive":
            context = self._extract_aggressive_context(full_context)
        elif debator_type == "conservative":
            context = self._extract_conservative_context(full_context)
        elif debator_type == "neutral":
            context = self._extract_neutral_context(full_context)
        else:
            context = self._extract_default_context(full_context)
        
        # Enforce token budget
        context = self._enforce_token_budget(context, debator_type)
        
        # Cache and return
        self.context_cache[cache_key] = context
        
        # Log token savings
        original_size = len(str(full_context))
        optimized_size = len(context)
        reduction = (1 - optimized_size/original_size) * 100
        logger.critical(f"🔥 CONTEXT OPTIMIZATION for {debator_type}:")
        logger.critical(f"🔥 Original: {original_size} chars")
        logger.critical(f"🔥 Optimized: {optimized_size} chars")
        logger.critical(f"🔥 Reduction: {reduction:.1f}%")
        
        return context
    
    def _extract_aggressive_context(self, full_context: Dict) -> str:
        """Extract growth-focused context for aggressive debator"""
        sections = []
        
        # Investment plan (condensed)
        if "investment_plan" in full_context:
            plan = full_context["investment_plan"]
            # Extract only growth-relevant parts
            sections.append(f"INVESTMENT FOCUS: {self._extract_key_points(plan, 'growth')}")
        
        # Market signals (bullish only)
        if "market_report" in full_context:
            market = full_context["market_report"]
            bullish_signals = self._extract_bullish_signals(market)
            sections.append(f"BULLISH SIGNALS: {bullish_signals}")
        
        # Positive news (headlines only)
        if "news_report" in full_context:
            news = full_context["news_report"]
            positive_news = self._extract_positive_headlines(news)
            sections.append(f"POSITIVE CATALYSTS: {positive_news}")
        
        # Growth fundamentals
        if "fundamentals_report" in full_context:
            fundamentals = full_context["fundamentals_report"]
            growth_metrics = self._extract_growth_metrics(fundamentals)
            sections.append(f"GROWTH METRICS: {growth_metrics}")
        
        return "\n\n".join(sections)
    
    def _extract_conservative_context(self, full_context: Dict) -> str:
        """Extract risk-focused context for conservative debator"""
        sections = []
        
        # Investment plan (risk aspects)
        if "investment_plan" in full_context:
            plan = full_context["investment_plan"]
            sections.append(f"RISK CONSIDERATIONS: {self._extract_key_points(plan, 'risk')}")
        
        # Market risks
        if "market_report" in full_context:
            market = full_context["market_report"]
            risk_signals = self._extract_risk_signals(market)
            sections.append(f"RISK INDICATORS: {risk_signals}")
        
        # Negative news
        if "news_report" in full_context:
            news = full_context["news_report"]
            negative_news = self._extract_negative_headlines(news)
            sections.append(f"CONCERNS: {negative_news}")
        
        # Risk fundamentals
        if "fundamentals_report" in full_context:
            fundamentals = full_context["fundamentals_report"]
            risk_metrics = self._extract_risk_metrics(fundamentals)
            sections.append(f"RISK METRICS: {risk_metrics}")
        
        return "\n\n".join(sections)
    
    def _extract_neutral_context(self, full_context: Dict) -> str:
        """Extract balanced context for neutral debator"""
        sections = []
        
        # Core investment thesis
        if "investment_plan" in full_context:
            plan = full_context["investment_plan"]
            sections.append(f"INVESTMENT THESIS: {self._extract_summary(plan, 200)}")
        
        # Market overview
        if "market_report" in full_context:
            market = full_context["market_report"]
            overview = self._extract_market_overview(market)
            sections.append(f"MARKET OVERVIEW: {overview}")
        
        # News summary
        if "news_report" in full_context:
            news = full_context["news_report"]
            summary = self._extract_news_summary(news)
            sections.append(f"NEWS SUMMARY: {summary}")
        
        # Valuation
        if "fundamentals_report" in full_context:
            fundamentals = full_context["fundamentals_report"]
            valuation = self._extract_valuation(fundamentals)
            sections.append(f"VALUATION: {valuation}")
        
        return "\n\n".join(sections)
    
    # Helper methods for extraction
    def _extract_key_points(self, text: str, focus: str, max_chars: int = 500) -> str:
        """Extract key points based on focus area"""
        if not text:
            return "N/A"
        
        # Look for relevant keywords based on focus
        if focus == "growth":
            keywords = ["growth", "upside", "potential", "opportunity", "expansion"]
        elif focus == "risk":
            keywords = ["risk", "downside", "concern", "threat", "weakness"]
        else:
            keywords = ["summary", "conclusion", "recommendation"]
        
        # Extract sentences containing keywords
        sentences = text.split('.')
        relevant = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                relevant.append(sentence.strip())
                if len(' '.join(relevant)) > max_chars:
                    break
        
        return ' '.join(relevant)[:max_chars] if relevant else text[:max_chars]
    
    def _extract_bullish_signals(self, market_report: str) -> str:
        """Extract bullish market signals"""
        if not market_report:
            return "No market data"
        
        bullish_keywords = ["bullish", "uptrend", "support", "breakout", "momentum", 
                           "oversold", "accumulation", "higher high", "golden cross"]
        
        lines = market_report.split('\n')
        bullish_lines = []
        for line in lines:
            if any(keyword in line.lower() for keyword in bullish_keywords):
                bullish_lines.append(line.strip())
                if len(bullish_lines) >= 5:  # Limit to 5 signals
                    break
        
        return ' | '.join(bullish_lines) if bullish_lines else "No clear bullish signals"
    
    def _extract_risk_signals(self, market_report: str) -> str:
        """Extract bearish/risk signals"""
        if not market_report:
            return "No market data"
        
        risk_keywords = ["bearish", "downtrend", "resistance", "breakdown", "weakness",
                        "overbought", "distribution", "lower low", "death cross", "risk"]
        
        lines = market_report.split('\n')
        risk_lines = []
        for line in lines:
            if any(keyword in line.lower() for keyword in risk_keywords):
                risk_lines.append(line.strip())
                if len(risk_lines) >= 5:
                    break
        
        return ' | '.join(risk_lines) if risk_lines else "No clear risk signals"
    
    def _extract_positive_headlines(self, news_report: str) -> str:
        """Extract positive news headlines only"""
        if not news_report:
            return "No news data"
        
        positive_keywords = ["positive", "beat", "upgrade", "growth", "strong", "gain"]
        headlines = []
        
        for line in news_report.split('\n'):
            if any(keyword in line.lower() for keyword in positive_keywords):
                # Extract just the headline, not the full content
                if "Sentiment: POSITIVE" in line or any(kw in line.lower() for kw in positive_keywords):
                    headlines.append(line.split('|')[0].strip())
                    if len(headlines) >= 3:
                        break
        
        return ' | '.join(headlines) if headlines else "No positive catalysts"
    
    def _extract_negative_headlines(self, news_report: str) -> str:
        """Extract negative news headlines"""
        if not news_report:
            return "No news data"
        
        negative_keywords = ["negative", "miss", "downgrade", "decline", "weak", "loss"]
        headlines = []
        
        for line in news_report.split('\n'):
            if any(keyword in line.lower() for keyword in negative_keywords):
                if "Sentiment: NEGATIVE" in line or any(kw in line.lower() for kw in negative_keywords):
                    headlines.append(line.split('|')[0].strip())
                    if len(headlines) >= 3:
                        break
        
        return ' | '.join(headlines) if headlines else "No major concerns"
    
    def _enforce_token_budget(self, context: str, component: str) -> str:
        """Enforce token budget for component"""
        budget = self.token_budgets.get(component, 8000)
        # Approximate 1 token = 4 chars
        max_chars = budget * 4
        
        if len(context) > max_chars:
            logger.warning(f"⚠️ Truncating context for {component}: {len(context)} > {max_chars}")
            return context[:max_chars] + "\n[TRUNCATED FOR TOKEN LIMIT]"
        
        return context
    
    def _generate_cache_key(self, component: str, context: Dict) -> str:
        """Generate cache key for context"""
        # Create a hash of the context for caching
        context_str = json.dumps({k: str(v)[:100] for k, v in context.items()}, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        return f"{component}_{context_hash}"
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "cache_size": len(self.context_cache),
            "cache_keys": list(self.context_cache.keys()),
            "memory_usage": sum(len(v) for v in self.context_cache.values())
        }

# Singleton instance
_smart_context_manager = None

def get_smart_context_manager() -> SmartContextManager:
    """Get or create SmartContextManager singleton"""
    global _smart_context_manager
    if _smart_context_manager is None:
        _smart_context_manager = SmartContextManager()
    return _smart_context_manager
```

---

### Step 2: Update parallel_risk_debators.py (Day 1-2)

```python
# In src/agent/graph/nodes/parallel_risk_debators.py

# Add import at top
from ...utils.smart_context_manager import get_smart_context_manager

# Update the run_aggressive function:
async def run_aggressive():
    try:
        logger.info("🔴 Starting Aggressive Risk Analyst")
        
        # NEW: Use SmartContextManager
        context_manager = get_smart_context_manager()
        optimized_context = context_manager.get_context_for_debator(
            "aggressive", 
            {
                "investment_plan": investment_plan,
                "trader_decision": trader_decision,
                "market_report": shared_context.get('market_report', ''),
                "sentiment_report": shared_context.get('sentiment_report', ''),
                "news_report": shared_context.get('news_report', ''),
                "fundamentals_report": shared_context.get('fundamentals_report', '')
            }
        )
        
        prompt = f"""As the Aggressive Risk Analyst, champion high-reward opportunities.

{optimized_context}

Provide your aggressive risk perspective emphasizing:
1. High-reward opportunities and growth potential
2. Why the risks are worth taking
3. Potential upside scenarios
4. Risk mitigation for aggressive positions

Be concise. Focus on actionable insights."""
        
        messages = [{"role": "user", "content": prompt}]
        response = await safe_llm_invoke(aggressive_llm, messages)
        logger.info("🔴 Aggressive Risk Analyst completed")
        return ("aggressive", response.content)
```

---

### Step 3: Testing & Validation (Day 2-3)

#### Test Script: `test_context_optimization.py`
```python
#!/usr/bin/env python3
"""Test context optimization impact"""

import asyncio
from src.agent.utils.smart_context_manager import get_smart_context_manager

async def test_context_reduction():
    manager = get_smart_context_manager()
    
    # Mock full context (typical size)
    full_context = {
        "investment_plan": "BUY recommendation..." * 100,  # ~2000 tokens
        "market_report": "Technical analysis..." * 200,    # ~5000 tokens
        "news_report": "Headlines and summaries..." * 50,  # ~1000 tokens
        "fundamentals_report": "Financial data..." * 150   # ~3000 tokens
    }
    
    # Test each debator
    for debator_type in ["aggressive", "conservative", "neutral"]:
        optimized = manager.get_context_for_debator(debator_type, full_context)
        
        print(f"\n{debator_type.upper()} DEBATOR:")
        print(f"Original size: {sum(len(str(v)) for v in full_context.values())} chars")
        print(f"Optimized size: {len(optimized)} chars")
        print(f"Reduction: {(1 - len(optimized)/sum(len(str(v)) for v in full_context.values()))*100:.1f}%")
        print(f"Preview: {optimized[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_context_reduction())
```

---

## 📊 Expected Results

### Before Optimization
```
Component: parallel_risk_debators
Total Tokens: 93,737
Breakdown:
- Aggressive: 31,245 tokens (full context)
- Conservative: 31,245 tokens (full context)  
- Neutral: 31,245 tokens (full context)
```

### After Optimization
```
Component: parallel_risk_debators
Total Tokens: 20,000 (78.7% reduction!)
Breakdown:
- Aggressive: 6,000 tokens (growth-focused context)
- Conservative: 6,000 tokens (risk-focused context)
- Neutral: 6,000 tokens (balanced context)
- Overhead: 2,000 tokens
```

### System-Wide Impact
```
Total System Tokens:
Before: 218,130
After Phase 2: 144,393 (33.8% total reduction)
Progress to Goal: 50% complete
```

---

## 🚦 Rollback Strategy

### Enable/Disable Flag
```python
# In parallel_risk_debators.py
USE_SMART_CONTEXT = True  # Set to False to disable

if USE_SMART_CONTEXT:
    context = context_manager.get_context_for_debator(...)
else:
    context = full_context  # Original behavior
```

---

## ✅ Success Criteria

### Must Achieve
- [ ] 70%+ reduction in parallel_risk_debators tokens
- [ ] No degradation in risk analysis quality
- [ ] <100ms additional latency
- [ ] Cache hit rate >50%

### Quality Validation
1. Compare decisions with/without optimization
2. Verify all key risks are still identified
3. Ensure perspectives remain distinct
4. Test with 10+ different tickers

---

## 📝 Next Steps After Phase 2

1. **Apply same pattern to researchers** (Week 2)
   - bull_researcher: 30,966 → 10,000 tokens
   - bear_researcher: 29,923 → 10,000 tokens
   
2. **Implement ReportSummarizer** (Week 2)
   - Progressive summarization
   - Component-specific summaries
   
3. **Add intelligent caching** (Week 3)
   - Cross-session cache
   - Incremental updates

---

**Implementation Ready**: This plan provides everything needed to implement Phase 2 context deduplication, achieving 74% reduction in the highest token-consuming component.