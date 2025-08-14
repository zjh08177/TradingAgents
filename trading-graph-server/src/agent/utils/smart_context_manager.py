#!/usr/bin/env python3
"""
Smart Context Manager - Phase 2 Token Optimization
Eliminates context duplication through intelligent perspective-specific distribution
Target: 74% reduction in parallel_risk_debators tokens (93,737 → 20,000)
"""

import logging
import re
import hashlib
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

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
    Core optimization for Phase 2: Context Deduplication
    
    Reduces token usage by 70-80% through:
    - Component-specific context views
    - Automatic compression and caching
    - Token budget enforcement
    - Quality preservation through perspective-aware filtering
    """
    
    def __init__(self):
        self.context_cache = {}
        self.extraction_rules = self._setup_extraction_rules()
        self.token_budgets = {
            "aggressive_debator": 6000,      # Growth-focused context
            "conservative_debator": 6000,     # Risk-focused context  
            "neutral_debator": 6000,          # Balanced context
            "bull_researcher": 8000,          # Future expansion
            "bear_researcher": 8000,          # Future expansion
            "risk_manager": 10000,            # Future expansion
            "research_manager": 12000         # Future expansion
        }
        logger.info("🧠 SmartContextManager initialized - Phase 2 Context Deduplication")
        logger.info(f"🎯 Target: 74% reduction in parallel_risk_debators tokens")
    
    def _setup_extraction_rules(self) -> Dict[str, Dict]:
        """Define what each component needs from context"""
        return {
            "aggressive": {
                "market": ["bullish_signals", "growth_indicators", "momentum", "breakout"],
                "news": ["positive_catalysts", "upgrades", "expansion", "beat"],
                "fundamentals": ["revenue_growth", "margin_expansion", "strong"],
                "sentiment": ["bullish", "positive", "optimistic"],
                "focus": "upside_opportunities"
            },
            "conservative": {
                "market": ["bearish_signals", "risk_indicators", "volatility", "breakdown"],
                "news": ["negative_catalysts", "downgrades", "concerns", "miss"],
                "fundamentals": ["debt_levels", "cash_burn", "risks", "weak"],
                "sentiment": ["bearish", "negative", "cautious"],
                "focus": "downside_protection"
            },
            "neutral": {
                "market": ["key_levels", "trend_summary", "volume", "overview"],
                "news": ["balanced_view", "consensus", "summary"],
                "fundamentals": ["valuation", "peer_comparison", "metrics"],
                "sentiment": ["neutral", "mixed", "balanced"],
                "focus": "balanced_perspective"
            }
        }
    
    def get_context_for_debator(self, debator_type: str, full_context: Dict[str, Any]) -> str:
        """
        Get optimized context for specific debator
        
        Args:
            debator_type: "aggressive", "conservative", or "neutral"
            full_context: Complete context with all reports
            
        Returns:
            Optimized context string (70-80% smaller than full context)
        """
        cache_key = self._generate_cache_key(debator_type, full_context)
        
        # Return cached if available
        if cache_key in self.context_cache:
            logger.info(f"✅ Cache hit for {debator_type} debator")
            return self.context_cache[cache_key]
        
        # Extract relevant context based on debator type
        if debator_type == "aggressive":
            context = self._extract_aggressive_context(full_context)
        elif debator_type == "conservative": 
            context = self._extract_conservative_context(full_context)
        elif debator_type == "neutral":
            context = self._extract_neutral_context(full_context)
        else:
            logger.warning(f"Unknown debator type: {debator_type}, using default")
            context = self._extract_default_context(full_context)
        
        # Enforce token budget
        context = self._enforce_token_budget(context, f"{debator_type}_debator")
        
        # Cache the result
        self.context_cache[cache_key] = context
        
        # Log optimization metrics
        self._log_optimization_metrics(debator_type, full_context, context)
        
        return context
    
    def _extract_aggressive_context(self, full_context: Dict[str, Any]) -> str:
        """Extract growth-focused context for aggressive debator"""
        sections = []
        
        # Investment plan - focus on growth opportunities
        if "investment_plan" in full_context:
            plan = full_context["investment_plan"]
            growth_focus = self._extract_key_points(plan, "growth", 400)
            sections.append(f"GROWTH OPPORTUNITIES:\n{growth_focus}")
        
        # Market signals - bullish indicators only
        if "market_report" in full_context:
            market = full_context["market_report"]
            bullish_signals = self._extract_bullish_signals(market)
            sections.append(f"BULLISH MARKET SIGNALS:\n{bullish_signals}")
        
        # Positive news catalysts
        if "news_report" in full_context:
            news = full_context["news_report"]
            positive_news = self._extract_positive_headlines(news)
            sections.append(f"POSITIVE CATALYSTS:\n{positive_news}")
        
        # Growth fundamentals
        if "fundamentals_report" in full_context:
            fundamentals = full_context["fundamentals_report"]
            growth_metrics = self._extract_growth_metrics(fundamentals)
            sections.append(f"GROWTH FUNDAMENTALS:\n{growth_metrics}")
        
        # Social sentiment - bullish only
        if "sentiment_report" in full_context:
            sentiment = full_context["sentiment_report"]
            bullish_sentiment = self._extract_bullish_sentiment(sentiment)
            sections.append(f"BULLISH SENTIMENT:\n{bullish_sentiment}")
        
        return "\n\n".join(sections)
    
    def _extract_conservative_context(self, full_context: Dict[str, Any]) -> str:
        """Extract risk-focused context for conservative debator"""
        sections = []
        
        # Investment plan - risk considerations
        if "investment_plan" in full_context:
            plan = full_context["investment_plan"]
            risk_focus = self._extract_key_points(plan, "risk", 400)
            sections.append(f"RISK CONSIDERATIONS:\n{risk_focus}")
        
        # Market risks and warning signals
        if "market_report" in full_context:
            market = full_context["market_report"]
            risk_signals = self._extract_risk_signals(market)
            sections.append(f"MARKET RISK INDICATORS:\n{risk_signals}")
        
        # Negative news and concerns
        if "news_report" in full_context:
            news = full_context["news_report"]
            negative_news = self._extract_negative_headlines(news)
            sections.append(f"RISK CATALYSTS:\n{negative_news}")
        
        # Risk fundamentals
        if "fundamentals_report" in full_context:
            fundamentals = full_context["fundamentals_report"]
            risk_metrics = self._extract_risk_metrics(fundamentals)
            sections.append(f"FINANCIAL RISKS:\n{risk_metrics}")
        
        # Bearish sentiment
        if "sentiment_report" in full_context:
            sentiment = full_context["sentiment_report"]
            bearish_sentiment = self._extract_bearish_sentiment(sentiment)
            sections.append(f"BEARISH SENTIMENT:\n{bearish_sentiment}")
        
        return "\n\n".join(sections)
    
    def _extract_neutral_context(self, full_context: Dict[str, Any]) -> str:
        """Extract balanced context for neutral debator"""
        sections = []
        
        # Core investment thesis - balanced view
        if "investment_plan" in full_context:
            plan = full_context["investment_plan"]
            summary = self._extract_summary(plan, 300)
            sections.append(f"INVESTMENT THESIS:\n{summary}")
        
        # Market overview - key levels and trends
        if "market_report" in full_context:
            market = full_context["market_report"]
            overview = self._extract_market_overview(market)
            sections.append(f"MARKET OVERVIEW:\n{overview}")
        
        # News summary - balanced perspective
        if "news_report" in full_context:
            news = full_context["news_report"]
            summary = self._extract_news_summary(news)
            sections.append(f"NEWS SUMMARY:\n{summary}")
        
        # Valuation metrics
        if "fundamentals_report" in full_context:
            fundamentals = full_context["fundamentals_report"]
            valuation = self._extract_valuation_summary(fundamentals)
            sections.append(f"VALUATION SUMMARY:\n{valuation}")
        
        # Overall sentiment
        if "sentiment_report" in full_context:
            sentiment = full_context["sentiment_report"]
            sentiment_overview = self._extract_sentiment_overview(sentiment)
            sections.append(f"SENTIMENT OVERVIEW:\n{sentiment_overview}")
        
        return "\n\n".join(sections)
    
    def _extract_default_context(self, full_context: Dict[str, Any]) -> str:
        """Fallback context extraction for unknown component types"""
        sections = []
        for key, value in full_context.items():
            if isinstance(value, str) and value.strip():
                summary = self._extract_summary(value, 200)
                sections.append(f"{key.upper()}: {summary}")
        return "\n\n".join(sections)
    
    # Context extraction helper methods
    
    def _extract_key_points(self, text: str, focus: str, max_chars: int = 500) -> str:
        """Extract key points based on focus area"""
        if not text or not isinstance(text, str):
            return "N/A"
        
        # Define focus keywords
        focus_keywords = {
            "growth": ["growth", "upside", "potential", "opportunity", "expansion", "increase", "strong", "beat"],
            "risk": ["risk", "downside", "concern", "threat", "weakness", "decline", "miss", "problem"],
            "summary": ["recommendation", "conclusion", "summary", "decision", "action", "plan"]
        }
        
        keywords = focus_keywords.get(focus, focus_keywords["summary"])
        
        # Extract sentences containing focus keywords
        sentences = re.split(r'[.!?]+', text)
        relevant_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and any(keyword in sentence.lower() for keyword in keywords):
                relevant_sentences.append(sentence)
                if len(' '.join(relevant_sentences)) > max_chars:
                    break
        
        result = ' '.join(relevant_sentences)[:max_chars]
        return result if result else text[:max_chars]
    
    def _extract_bullish_signals(self, market_report: str) -> str:
        """Extract bullish market signals"""
        if not market_report:
            return "No market data available"
        
        bullish_patterns = [
            r'bullish.*signal', r'uptrend.*continue', r'support.*strong',
            r'breakout.*confirm', r'momentum.*positive', r'oversold.*bounce',
            r'accumulation.*pattern', r'higher.*high', r'golden.*cross',
            r'buy.*signal', r'bullish.*outlook', r'upward.*trend'
        ]
        
        signals = []
        lines = market_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and any(re.search(pattern, line, re.IGNORECASE) for pattern in bullish_patterns):
                signals.append(line)
                if len(signals) >= 5:  # Limit to top 5 signals
                    break
        
        return ' | '.join(signals) if signals else "No clear bullish signals detected"
    
    def _extract_risk_signals(self, market_report: str) -> str:
        """Extract bearish/risk market signals"""
        if not market_report:
            return "No market data available"
        
        risk_patterns = [
            r'bearish.*signal', r'downtrend.*confirm', r'resistance.*strong',
            r'breakdown.*pattern', r'momentum.*negative', r'overbought.*risk',
            r'distribution.*pattern', r'lower.*low', r'death.*cross',
            r'sell.*signal', r'bearish.*outlook', r'downward.*trend'
        ]
        
        signals = []
        lines = market_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and any(re.search(pattern, line, re.IGNORECASE) for pattern in risk_patterns):
                signals.append(line)
                if len(signals) >= 5:
                    break
        
        return ' | '.join(signals) if signals else "No clear risk signals detected"
    
    def _extract_positive_headlines(self, news_report: str) -> str:
        """Extract positive news headlines"""
        if not news_report:
            return "No news data available"
        
        positive_patterns = [
            r'Sentiment: POSITIVE', r'upgrade', r'beat.*expect', r'strong.*result',
            r'growth.*accelerat', r'positive.*outlook', r'exceeds.*estimate',
            r'bullish.*view', r'buy.*rating', r'target.*raise'
        ]
        
        headlines = []
        lines = news_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and any(re.search(pattern, line, re.IGNORECASE) for pattern in positive_patterns):
                # Extract just the headline part
                if '|' in line:
                    headline = line.split('|')[0].strip()
                else:
                    headline = line
                headlines.append(headline)
                if len(headlines) >= 3:
                    break
        
        return ' | '.join(headlines) if headlines else "No significant positive catalysts"
    
    def _extract_negative_headlines(self, news_report: str) -> str:
        """Extract negative news headlines"""
        if not news_report:
            return "No news data available"
        
        negative_patterns = [
            r'Sentiment: NEGATIVE', r'downgrade', r'miss.*expect', r'weak.*result',
            r'decline.*revenue', r'negative.*outlook', r'below.*estimate',
            r'bearish.*view', r'sell.*rating', r'target.*cut'
        ]
        
        headlines = []
        lines = news_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and any(re.search(pattern, line, re.IGNORECASE) for pattern in negative_patterns):
                if '|' in line:
                    headline = line.split('|')[0].strip()
                else:
                    headline = line
                headlines.append(headline)
                if len(headlines) >= 3:
                    break
        
        return ' | '.join(headlines) if headlines else "No significant risk catalysts"
    
    def _extract_growth_metrics(self, fundamentals_report: str) -> str:
        """Extract growth-related fundamental metrics"""
        if not fundamentals_report:
            return "No fundamentals data available"
        
        growth_patterns = [
            r'Revenue Growth.*?(\d+\.?\d*%)', r'Margin.*expansion', r'ROE.*(\d+\.?\d*%)',
            r'Earnings.*growth', r'Free Cash Flow.*positive', r'Revenue.*(\$[\d,]+M)',
            r'P/E Ratio.*(\d+\.?\d*)', r'Market Cap.*(\$[\d,]+M)'
        ]
        
        metrics = []
        lines = fundamentals_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if line:
                for pattern in growth_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        metrics.append(line)
                        break
                if len(metrics) >= 6:
                    break
        
        return ' | '.join(metrics) if metrics else "Limited growth metrics available"
    
    def _extract_risk_metrics(self, fundamentals_report: str) -> str:
        """Extract risk-related fundamental metrics"""
        if not fundamentals_report:
            return "No fundamentals data available"
        
        risk_patterns = [
            r'Debt.*Equity.*(\d+\.?\d*)', r'Current.*Ratio.*(\d+\.?\d*)',
            r'Cash.*(\$[\d,]+M)', r'Debt.*(\$[\d,]+M)', r'Liquidity',
            r'Bankruptcy', r'Default', r'Credit.*rating'
        ]
        
        metrics = []
        lines = fundamentals_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if line:
                for pattern in risk_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        metrics.append(line)
                        break
                if len(metrics) >= 6:
                    break
        
        return ' | '.join(metrics) if metrics else "Limited risk metrics available"
    
    def _extract_summary(self, text: str, max_chars: int = 300) -> str:
        """Extract general summary from text"""
        if not text:
            return "N/A"
        
        # Look for conclusion/summary sections first
        summary_patterns = [
            r'conclusion.*?(?=\n\n|\n[A-Z]|$)',
            r'summary.*?(?=\n\n|\n[A-Z]|$)',
            r'recommendation.*?(?=\n\n|\n[A-Z]|$)',
            r'final.*?(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0)[:max_chars]
        
        # Fallback to first paragraph
        first_para = text.split('\n\n')[0]
        return first_para[:max_chars]
    
    def _extract_market_overview(self, market_report: str) -> str:
        """Extract market overview information"""
        if not market_report:
            return "No market data available"
        
        overview_lines = []
        lines = market_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in 
                          ['overview', 'summary', 'trend', 'price', 'volume', 'signal']):
                overview_lines.append(line)
                if len(overview_lines) >= 4:
                    break
        
        return ' | '.join(overview_lines) if overview_lines else "Limited market data"
    
    def _extract_news_summary(self, news_report: str) -> str:
        """Extract balanced news summary"""
        if not news_report:
            return "No news data available"
        
        # Count sentiment distribution
        positive_count = news_report.lower().count('sentiment: positive')
        negative_count = news_report.lower().count('sentiment: negative')
        neutral_count = news_report.lower().count('sentiment: neutral')
        
        summary = f"News Sentiment Distribution: {positive_count} Positive, {neutral_count} Neutral, {negative_count} Negative"
        
        # Extract a few key headlines
        headlines = []
        lines = news_report.split('\n')
        for line in lines:
            if line.strip() and ('.' in line or 'Source:' in line):
                headlines.append(line.strip())
                if len(headlines) >= 2:
                    break
        
        if headlines:
            summary += f" | Key Headlines: {' | '.join(headlines)}"
        
        return summary[:400]  # Limit length
    
    def _extract_valuation_summary(self, fundamentals_report: str) -> str:
        """Extract valuation metrics summary"""
        if not fundamentals_report:
            return "No fundamentals data available"
        
        valuation_metrics = []
        lines = fundamentals_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(metric in line for metric in ['P/E', 'P/B', 'EV', 'Dividend', 'Market Cap']):
                valuation_metrics.append(line)
                if len(valuation_metrics) >= 5:
                    break
        
        return ' | '.join(valuation_metrics) if valuation_metrics else "Limited valuation data"
    
    def _extract_bullish_sentiment(self, sentiment_report: str) -> str:
        """Extract bullish social sentiment indicators"""
        if not sentiment_report:
            return "No sentiment data available"
        
        bullish_indicators = []
        lines = sentiment_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in 
                  ['bullish', 'buy', 'positive', 'optimistic', 'strong']):
                bullish_indicators.append(line)
                if len(bullish_indicators) >= 3:
                    break
        
        return ' | '.join(bullish_indicators) if bullish_indicators else "Mixed sentiment signals"
    
    def _extract_bearish_sentiment(self, sentiment_report: str) -> str:
        """Extract bearish social sentiment indicators"""  
        if not sentiment_report:
            return "No sentiment data available"
        
        bearish_indicators = []
        lines = sentiment_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in 
                  ['bearish', 'sell', 'negative', 'pessimistic', 'weak']):
                bearish_indicators.append(line)
                if len(bearish_indicators) >= 3:
                    break
        
        return ' | '.join(bearish_indicators) if bearish_indicators else "Limited bearish signals"
    
    def _extract_sentiment_overview(self, sentiment_report: str) -> str:
        """Extract overall sentiment overview"""
        if not sentiment_report:
            return "No sentiment data available"
        
        # Look for summary or score information
        overview_lines = []
        lines = sentiment_report.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in 
                  ['score', 'average', 'overall', 'summary', 'sentiment', 'recommendation']):
                overview_lines.append(line)
                if len(overview_lines) >= 3:
                    break
        
        return ' | '.join(overview_lines) if overview_lines else "Neutral sentiment signals"
    
    def _enforce_token_budget(self, context: str, component: str) -> str:
        """Enforce token budget for component"""
        budget = self.token_budgets.get(component, 8000)
        # Approximate 1 token ≈ 4 characters
        max_chars = budget * 4
        
        if len(context) > max_chars:
            logger.warning(f"⚠️ Truncating context for {component}: {len(context)} > {max_chars} chars")
            return context[:max_chars] + "\n\n[TRUNCATED FOR TOKEN BUDGET]"
        
        return context
    
    def _generate_cache_key(self, component: str, context: Dict[str, Any]) -> str:
        """Generate cache key for context"""
        # Create hash of context for caching
        context_str = json.dumps({
            k: str(v)[:100] if isinstance(v, str) else str(v) 
            for k, v in context.items() if v
        }, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        return f"{component}_{context_hash}"
    
    def _log_optimization_metrics(self, debator_type: str, full_context: Dict, optimized_context: str):
        """Log context optimization metrics"""
        original_size = sum(len(str(v)) for v in full_context.values())
        optimized_size = len(optimized_context)
        reduction_pct = (1 - optimized_size/original_size) * 100 if original_size > 0 else 0
        
        # Estimate tokens (1 token ≈ 4 chars)
        original_tokens = original_size // 4
        optimized_tokens = optimized_size // 4
        token_reduction = original_tokens - optimized_tokens
        
        logger.critical(f"🔥 CONTEXT OPTIMIZATION - {debator_type.upper()} DEBATOR")
        logger.critical(f"🔥 Original: {original_size:,} chars ({original_tokens:,} tokens)")
        logger.critical(f"🔥 Optimized: {optimized_size:,} chars ({optimized_tokens:,} tokens)")
        logger.critical(f"🔥 Reduction: {reduction_pct:.1f}% ({token_reduction:,} tokens saved)")
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        return {
            "cache_size": len(self.context_cache),
            "cache_keys": list(self.context_cache.keys()),
            "memory_usage": sum(len(v) for v in self.context_cache.values()),
            "token_budgets": self.token_budgets
        }
    
    def clear_cache(self):
        """Clear context cache"""
        self.context_cache.clear()
        logger.info("🗑️ Context cache cleared")

# Global singleton instance
_smart_context_manager: Optional[SmartContextManager] = None

def get_smart_context_manager() -> SmartContextManager:
    """Get or create SmartContextManager singleton"""
    global _smart_context_manager
    if _smart_context_manager is None:
        _smart_context_manager = SmartContextManager()
    return _smart_context_manager