"""
Multi-Round Debate Optimizer
Optimization 5: Optimize multi-round research debate for performance and quality
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DebateOptimizer:
    """Optimizes multi-round research debate for performance and quality"""
    
    def __init__(self):
        self._round_metrics = {}
        self._quality_history = []
        self._performance_targets = {
            "max_rounds": 3,
            "target_round_time": 30.0,  # seconds per round
            "min_quality_score": 7,     # minimum score to proceed
            "early_consensus_threshold": 8.5  # score to stop early
        }
        
        logger.info("🎯 DebateOptimizer initialized")
    
    def should_continue_debate(self, 
                             debate_state: Dict[str, Any], 
                             round_performance: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Determine if debate should continue based on performance and quality metrics
        
        Args:
            debate_state: Current debate state
            round_performance: Performance metrics for the current round
            
        Returns:
            Dict with decision and reasoning
        """
        current_round = debate_state.get("current_round", 0)
        max_rounds = debate_state.get("max_rounds", self._performance_targets["max_rounds"])
        consensus_reached = debate_state.get("consensus_reached", False)
        quality_score = debate_state.get("last_quality_score", 0)
        
        # Record performance metrics
        if round_performance:
            self._record_round_metrics(current_round, round_performance)
        
        # Decision logic
        decision = {
            "continue": False,
            "reason": "",
            "optimization_applied": None,
            "next_round_focus": ""
        }
        
        # 1. Check if max rounds reached
        if current_round >= max_rounds:
            decision["reason"] = f"Max rounds ({max_rounds}) reached"
            logger.info(f"🔚 OPTIMIZATION 5: Stopping debate - {decision['reason']}")
            return decision
        
        # 2. Check if consensus already reached
        if consensus_reached:
            decision["reason"] = "Consensus already reached"
            logger.info(f"✅ OPTIMIZATION 5: Stopping debate - {decision['reason']}")
            return decision
        
        # 3. OPTIMIZATION: Early consensus detection based on quality score
        if quality_score >= self._performance_targets["early_consensus_threshold"]:
            decision["reason"] = f"High quality achieved (score: {quality_score}) - early consensus"
            decision["optimization_applied"] = "EARLY_CONSENSUS"
            logger.info(f"🚀 OPTIMIZATION 5: Early consensus detected - {decision['reason']}")
            # Force consensus in debate state
            debate_state["consensus_reached"] = True
            return decision
        
        # 4. OPTIMIZATION: Performance-based decision
        if round_performance:
            round_time = round_performance.get("duration", 0)
            if round_time > self._performance_targets["target_round_time"] * 1.5:
                logger.warning(f"⚠️ OPTIMIZATION 5: Round {current_round} took {round_time:.1f}s (target: {self._performance_targets['target_round_time']}s)")
                
                # If performance is poor and quality isn't improving, consider stopping
                if quality_score < self._performance_targets["min_quality_score"] and current_round >= 2:
                    decision["reason"] = f"Poor performance ({round_time:.1f}s) and quality ({quality_score})"
                    decision["optimization_applied"] = "PERFORMANCE_CUTOFF"
                    logger.info(f"🚀 OPTIMIZATION 5: Performance cutoff applied - {decision['reason']}")
                    return decision
        
        # 5. Continue debate with optimized focus
        decision["continue"] = True
        decision["reason"] = f"Continuing to round {current_round + 1}"
        decision["next_round_focus"] = self._get_next_round_focus(debate_state)
        decision["optimization_applied"] = "FOCUSED_CONTINUATION"
        
        logger.info(f"🔄 OPTIMIZATION 5: {decision['reason']} - Focus: {decision['next_round_focus']}")
        return decision
    
    def _record_round_metrics(self, round_num: int, metrics: Dict[str, Any]):
        """Record performance metrics for a round"""
        self._round_metrics[round_num] = {
            **metrics,
            "timestamp": datetime.now()
        }
        
        # Track quality progression
        if "quality_score" in metrics:
            self._quality_history.append(metrics["quality_score"])
        
        logger.info(f"📊 OPTIMIZATION 5: Round {round_num} metrics recorded")
    
    def _get_next_round_focus(self, debate_state: Dict[str, Any]) -> str:
        """Determine focus for next round to optimize efficiency"""
        current_round = debate_state.get("current_round", 0)
        quality_score = debate_state.get("last_quality_score", 0)
        judge_feedback = debate_state.get("judge_feedback", "")
        
        # Analyze feedback for focus areas
        feedback_lower = judge_feedback.lower()
        
        if "data" in feedback_lower or "evidence" in feedback_lower:
            return "DATA_EVIDENCE"
        elif "risk" in feedback_lower or "downside" in feedback_lower:
            return "RISK_ANALYSIS"
        elif "valuation" in feedback_lower or "price" in feedback_lower:
            return "VALUATION"
        elif "competitive" in feedback_lower or "market" in feedback_lower:
            return "COMPETITIVE_ANALYSIS"
        elif current_round == 1:
            return "DEEP_FUNDAMENTALS"
        else:
            return "SYNTHESIS_DECISION"
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization performance"""
        if not self._round_metrics:
            return {"status": "No rounds recorded"}
        
        total_rounds = len(self._round_metrics)
        total_time = sum(metrics.get("duration", 0) for metrics in self._round_metrics.values())
        avg_time_per_round = total_time / total_rounds if total_rounds > 0 else 0
        
        quality_trend = "IMPROVING" if len(self._quality_history) >= 2 and self._quality_history[-1] > self._quality_history[0] else "STABLE"
        
        summary = {
            "total_rounds": total_rounds,
            "total_time": round(total_time, 2),
            "avg_time_per_round": round(avg_time_per_round, 2),
            "target_time_per_round": self._performance_targets["target_round_time"],
            "performance_ratio": round(avg_time_per_round / self._performance_targets["target_round_time"], 2),
            "quality_trend": quality_trend,
            "quality_scores": self._quality_history.copy(),
            "optimization_effective": avg_time_per_round <= self._performance_targets["target_round_time"] * 1.2
        }
        
        logger.info(f"📊 OPTIMIZATION 5 Summary: {total_rounds} rounds, {total_time:.1f}s total, {quality_trend} quality")
        return summary

# Global optimizer instance
_global_optimizer: Optional[DebateOptimizer] = None

def get_debate_optimizer() -> DebateOptimizer:
    """Get the global debate optimizer instance"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = DebateOptimizer()
    return _global_optimizer

def optimize_research_debate_routing(state: Dict[str, Any], round_start_time: float = None) -> str:
    """
    Optimized routing logic for research debate with performance monitoring
    
    Args:
        state: Current agent state
        round_start_time: Start time of the current round (for performance tracking)
        
    Returns:
        Next node to route to
    """
    debate_state = state.get("research_debate_state", {})
    optimizer = get_debate_optimizer()
    
    # Calculate round performance if timing provided
    round_performance = None
    if round_start_time:
        round_performance = {
            "duration": time.time() - round_start_time,
            "quality_score": debate_state.get("last_quality_score", 0)
        }
    
    # Get optimization decision
    decision = optimizer.should_continue_debate(debate_state, round_performance)
    
    # Apply any state modifications from optimizer
    if decision.get("optimization_applied") == "EARLY_CONSENSUS":
        state["research_debate_state"] = debate_state  # Updated with consensus_reached=True
    
    # Determine routing
    if decision["continue"]:
        # Add focus for next round
        debate_state["next_round_focus"] = decision["next_round_focus"]
        state["research_debate_state"] = debate_state
        
        logger.info(f"🔄 OPTIMIZATION 5: Continuing to research_debate_controller")
        return "research_debate_controller"
    else:
        logger.info(f"✅ OPTIMIZATION 5: Proceeding to research_manager - {decision['reason']}")
        return "research_manager"

def log_debate_optimization_summary():
    """Log the final optimization summary"""
    optimizer = get_debate_optimizer()
    summary = optimizer.get_optimization_summary()
    
    logger.info(f"""
🎯 OPTIMIZATION 5: Multi-Round Debate Performance Summary
   📊 Total Rounds: {summary.get('total_rounds', 0)}
   ⏱️ Total Time: {summary.get('total_time', 0)}s
   📈 Avg Time/Round: {summary.get('avg_time_per_round', 0)}s (target: <{summary.get('target_time_per_round', 30)}s)
   🎯 Performance Ratio: {summary.get('performance_ratio', 0)} {'✅' if summary.get('performance_ratio', 0) <= 1.2 else '❌'}
   📊 Quality Trend: {summary.get('quality_trend', 'N/A')}
   🏆 Optimization Effective: {'✅ YES' if summary.get('optimization_effective', False) else '❌ NO'}
    """)