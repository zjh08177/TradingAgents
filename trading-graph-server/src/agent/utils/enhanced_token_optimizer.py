#!/usr/bin/env python3
"""
Enhanced Token Optimizer with Response Control
Extends base TokenOptimizer with response length optimization and dynamic limits
"""

import logging
import re
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import tiktoken
import numpy as np
from collections import defaultdict

from .token_optimizer import TokenOptimizer, PromptOptimization

logger = logging.getLogger(__name__)

@dataclass
class ResponsePrediction:
    """Predicted response characteristics"""
    predicted_tokens: int
    confidence: float
    based_on_samples: int

class EnhancedTokenOptimizer(TokenOptimizer):
    """Extended optimizer with response control and predictive capabilities"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(model_name)
        self.response_history = defaultdict(list)
        self.dynamic_limits = {}
        self.quality_metrics = defaultdict(lambda: {"completeness": [], "conciseness": []})
        logger.debug("🚀 Enhanced Token Optimizer initialized")
    
    def optimize_for_response_length(self, prompt: str, target_response_tokens: int, 
                                   agent_type: str = "default") -> str:
        """
        Add response length guidance to prompt
        Injects structured instructions for compact responses
        """
        # Calculate approximate word count (1 token ≈ 0.75 words)
        target_words = int(target_response_tokens * 0.75)
        
        # Agent-specific response templates
        response_templates = {
            "market_analyst": f"""
CRITICAL RESPONSE REQUIREMENTS:
- Maximum: {target_words} words ({target_response_tokens} tokens)
- Format: Structured sections with bullet points
- Data: Only essential metrics (2 decimals)
- Structure:
  1. Key Signal: BUY/SELL/HOLD + confidence % (1 line)
  2. Supporting Indicators: Top 3 only (bullets)
  3. Risk Assessment: Critical risks only (bullets)
  4. Action: Entry/exit/size (1 line)
- Omit: Explanations, context, filler phrases""",
            
            "news_analyst": f"""
RESPONSE LIMITS:
- Max: {target_words} words
- Format:
  • Sentiment: POSITIVE/NEGATIVE/NEUTRAL + score
  • Key Headlines: Top 3 impact items
  • Market Impact: HIGH/MEDIUM/LOW + reason
  • Recommendation: Clear action
- Skip: Background info, detailed analysis""",
            
            "trader": f"""
OUTPUT CONSTRAINTS:
- Max: {target_words} words
- Required:
  • Decision: BUY/SELL/HOLD
  • Entry: $X.XX
  • Stop Loss: $X.XX  
  • Take Profit: $X.XX
  • Position Size: X%
  • Confidence: X/10
- No explanations needed"""
        }
        
        # Get template or use default
        template = response_templates.get(agent_type, f"""
RESPONSE MUST BE UNDER {target_words} WORDS:
1. Main Finding (1 sentence)
2. Key Data (3-5 bullets)  
3. Action/Recommendation (1 sentence)
Omit all unnecessary details.""")
        
        # Prepend to prompt
        return f"{template}\n\n{prompt}"
    
    def calculate_optimal_limits(self, task_type: str, complexity: float, 
                               historical_performance: Optional[Dict] = None) -> Dict[str, int]:
        """
        Dynamic token limits based on task complexity and historical data
        Adjusts limits based on actual usage patterns
        """
        # Base limits by task type
        BASE_LIMITS = {
            "analysis": {"prompt": 1500, "response": 500},
            "summary": {"prompt": 1000, "response": 300},
            "decision": {"prompt": 800, "response": 200},
            "research": {"prompt": 2000, "response": 700},
            "synthesis": {"prompt": 1800, "response": 600},
            "execution": {"prompt": 600, "response": 150}
        }
        
        # Get base limits
        limits = BASE_LIMITS.get(task_type, {"prompt": 1200, "response": 400})
        
        # Adjust for complexity (0.0 to 1.0)
        # Low complexity (0-0.3): Reduce by 30%
        # Medium complexity (0.3-0.7): Use base
        # High complexity (0.7-1.0): Increase by up to 50%
        if complexity < 0.3:
            multiplier = 0.7
        elif complexity < 0.7:
            multiplier = 1.0
        else:
            multiplier = 1.0 + (complexity - 0.7) * 1.67  # Max 1.5x at complexity=1.0
        
        limits["prompt"] = int(limits["prompt"] * multiplier)
        limits["response"] = int(limits["response"] * multiplier)
        
        # Adjust based on historical performance if available
        if historical_performance:
            avg_overage = historical_performance.get("avg_response_overage", 0)
            if avg_overage > 0.2:  # Consistently over by 20%+
                limits["response"] = int(limits["response"] * 0.8)  # Reduce by 20%
            elif avg_overage < -0.1:  # Consistently under by 10%+
                limits["response"] = int(limits["response"] * 1.1)  # Increase by 10%
        
        # Store for monitoring
        self.dynamic_limits[task_type] = limits
        
        return limits
    
    def predict_response_tokens(self, prompt: str, agent_type: str, 
                              prompt_tokens: Optional[int] = None) -> ResponsePrediction:
        """
        Predict response token count based on historical patterns
        Uses agent-specific ratios and prompt analysis
        """
        if prompt_tokens is None:
            prompt_tokens = self.count_tokens(prompt)
        
        # Check historical data
        agent_history = self.response_history.get(agent_type, [])
        
        if len(agent_history) >= 5:
            # Use recent history (last 20 samples)
            recent_samples = agent_history[-20:]
            ratios = [h["response_tokens"] / h["prompt_tokens"] for h in recent_samples]
            
            # Remove outliers (beyond 2 std dev)
            mean_ratio = np.mean(ratios)
            std_ratio = np.std(ratios)
            filtered_ratios = [r for r in ratios if abs(r - mean_ratio) <= 2 * std_ratio]
            
            if filtered_ratios:
                avg_ratio = np.mean(filtered_ratios)
                confidence = min(0.9, 0.5 + len(filtered_ratios) * 0.02)  # Max 90% confidence
                predicted = int(prompt_tokens * avg_ratio)
                
                return ResponsePrediction(
                    predicted_tokens=predicted,
                    confidence=confidence,
                    based_on_samples=len(filtered_ratios)
                )
        
        # Fallback to agent-specific defaults
        DEFAULT_RATIOS = {
            "market_analyst": 0.4,      # Concise technical data
            "news_analyst": 0.35,       # Brief summaries
            "social_media_analyst": 0.3,  # Short sentiment
            "fundamentals_analyst": 0.5,  # More detailed
            "risk_manager": 0.35,       # Focused risks
            "research_manager": 0.45,   # Synthesis
            "trader": 0.2,              # Very brief decisions
            "bull_researcher": 0.4,
            "bear_researcher": 0.4
        }
        
        ratio = DEFAULT_RATIOS.get(agent_type, 0.4)
        predicted = int(prompt_tokens * ratio)
        
        return ResponsePrediction(
            predicted_tokens=predicted,
            confidence=0.3,  # Low confidence for defaults
            based_on_samples=0
        )
    
    async def predict_response_tokens_async(self, prompt: str, agent_type: str, 
                                          prompt_tokens: Optional[int] = None) -> ResponsePrediction:
        """
        Async version of predict_response_tokens
        """
        if prompt_tokens is None:
            prompt_tokens = await self.count_tokens_async(prompt)
        
        # Historical analysis doesn't need async (pure computation)
        return await asyncio.to_thread(
            self.predict_response_tokens, prompt, agent_type, prompt_tokens
        )
    
    def record_actual_usage(self, agent_type: str, prompt_tokens: int, 
                          response_tokens: int, word_count: int):
        """Record actual token usage for learning"""
        record = {
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "word_count": word_count,
            "ratio": response_tokens / prompt_tokens if prompt_tokens > 0 else 0,
            "timestamp": time.time()
        }
        
        self.response_history[agent_type].append(record)
        
        # Keep only last 100 records per agent
        if len(self.response_history[agent_type]) > 100:
            self.response_history[agent_type] = self.response_history[agent_type][-100:]
    
    def analyze_response_quality(self, response: str, agent_type: str, 
                               expected_sections: List[str]) -> Dict[str, float]:
        """
        Analyze response quality for completeness vs conciseness
        Returns quality scores to guide future optimizations
        """
        word_count = len(response.split())
        
        # Check completeness (are expected sections present?)
        completeness_score = 0.0
        for section in expected_sections:
            if section.lower() in response.lower():
                completeness_score += 1.0
        
        if expected_sections:
            completeness_score /= len(expected_sections)
        else:
            completeness_score = 1.0  # No specific requirements
        
        # Check conciseness (using agent-specific targets)
        target_words = self.WORD_LIMITS.get(agent_type, 250)
        if word_count <= target_words:
            conciseness_score = 1.0
        elif word_count <= target_words * 1.2:  # 20% grace
            conciseness_score = 0.8
        elif word_count <= target_words * 1.5:  # 50% over
            conciseness_score = 0.5
        else:
            conciseness_score = 0.2
        
        # Record metrics
        self.quality_metrics[agent_type]["completeness"].append(completeness_score)
        self.quality_metrics[agent_type]["conciseness"].append(conciseness_score)
        
        # Keep only last 50 samples
        for metric in ["completeness", "conciseness"]:
            if len(self.quality_metrics[agent_type][metric]) > 50:
                self.quality_metrics[agent_type][metric] = \
                    self.quality_metrics[agent_type][metric][-50:]
        
        return {
            "completeness": completeness_score,
            "conciseness": conciseness_score,
            "word_count": word_count,
            "target_words": target_words,
            "quality_score": (completeness_score + conciseness_score) / 2
        }
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization metrics"""
        report = {
            "response_predictions": {},
            "quality_metrics": {},
            "dynamic_limits": self.dynamic_limits,
            "recommendations": []
        }
        
        # Analyze each agent
        for agent_type, history in self.response_history.items():
            if history:
                recent = history[-20:]  # Last 20 samples
                avg_ratio = np.mean([h["ratio"] for h in recent])
                avg_words = np.mean([h["word_count"] for h in recent])
                
                report["response_predictions"][agent_type] = {
                    "avg_response_ratio": round(avg_ratio, 3),
                    "avg_word_count": round(avg_words, 1),
                    "samples": len(history)
                }
                
                # Quality metrics
                if agent_type in self.quality_metrics:
                    metrics = self.quality_metrics[agent_type]
                    if metrics["completeness"]:
                        report["quality_metrics"][agent_type] = {
                            "avg_completeness": round(np.mean(metrics["completeness"]), 2),
                            "avg_conciseness": round(np.mean(metrics["conciseness"]), 2)
                        }
                
                # Generate recommendations
                if avg_ratio > 0.5:
                    report["recommendations"].append(
                        f"Reduce {agent_type} response verbosity (ratio: {avg_ratio:.2f})"
                    )
                
                if agent_type in self.quality_metrics:
                    avg_concise = np.mean(self.quality_metrics[agent_type]["conciseness"][-10:])
                    if avg_concise < 0.7:
                        report["recommendations"].append(
                            f"Strengthen {agent_type} word limit enforcement"
                        )
        
        return report
    
    # Word limits from AgentPromptEnhancer for consistency
    WORD_LIMITS = {
        "market_analyst": 300,
        "news_analyst": 250,
        "social_media_analyst": 200,
        "fundamentals_analyst": 350,
        "risk_manager": 250,
        "research_manager": 400,
        "trader": 150,
        "bull_researcher": 300,
        "bear_researcher": 300,
        "default": 250
    }

# Global instance
_enhanced_optimizer: Optional[EnhancedTokenOptimizer] = None

def get_enhanced_token_optimizer() -> EnhancedTokenOptimizer:
    """Get the global enhanced token optimizer instance"""
    global _enhanced_optimizer
    if _enhanced_optimizer is None:
        _enhanced_optimizer = EnhancedTokenOptimizer()
    return _enhanced_optimizer