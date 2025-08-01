#!/usr/bin/env python3
"""
Token Management System - Central coordination for all token optimization
Provides unified interface for token management across the trading system
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import asyncio
from collections import defaultdict

from .enhanced_token_optimizer import EnhancedTokenOptimizer, get_enhanced_token_optimizer
from .intelligent_token_limiter import IntelligentTokenLimiter, get_intelligent_token_limiter
from .agent_prompt_enhancer import AgentPromptEnhancer, get_prompt_enhancer
from .prompt_compressor import AdvancedPromptCompressor, get_prompt_compressor

logger = logging.getLogger(__name__)

@dataclass
class TokenAllocation:
    """Token allocation for an agent interaction"""
    agent_type: str
    prompt_tokens: int
    response_tokens: int
    word_limit: int
    total_budget: int
    optimization_applied: bool
    compression_applied: bool

@dataclass
class TokenUsageMetrics:
    """Metrics for token usage tracking"""
    total_prompt_tokens: int
    total_response_tokens: int
    total_cost: float
    interactions: int
    avg_prompt_tokens: float
    avg_response_tokens: float
    optimization_savings: int
    compression_ratio: float

class TokenManagementConfig:
    """Configuration for token management system"""
    
    def __init__(self):
        self.models = {
            "gpt-4o-mini": {
                "max_prompt_tokens": 8000,
                "max_response_tokens": 2000,
                "cost_per_1k_prompt": 0.00015,
                "cost_per_1k_completion": 0.0006,
                "total_context_limit": 10000
            },
            "gpt-4": {
                "max_prompt_tokens": 6000,
                "max_response_tokens": 1500,
                "cost_per_1k_prompt": 0.03,
                "cost_per_1k_completion": 0.06,
                "total_context_limit": 8000
            }
        }
        
        self.agent_limits = {
            "market_analyst": {"prompt": 1500, "response": 400, "words": 300},
            "news_analyst": {"prompt": 1200, "response": 350, "words": 250},
            "social_media_analyst": {"prompt": 1000, "response": 300, "words": 200},
            "fundamentals_analyst": {"prompt": 1800, "response": 500, "words": 350},
            "risk_manager": {"prompt": 1200, "response": 350, "words": 250},
            "research_manager": {"prompt": 2000, "response": 600, "words": 400},
            "trader": {"prompt": 800, "response": 200, "words": 150},
            "bull_researcher": {"prompt": 1500, "response": 400, "words": 300},
            "bear_researcher": {"prompt": 1500, "response": 400, "words": 300},
            "aggressive_debator": {"prompt": 1000, "response": 300, "words": 200},
            "conservative_debator": {"prompt": 1000, "response": 300, "words": 200},
            "neutral_debator": {"prompt": 1000, "response": 300, "words": 200}
        }
        
        self.optimization_targets = {
            "total_tokens_per_run": 40000,  # Target from requirements
            "avg_tokens_per_agent": 2500,
            "response_conciseness": 0.7,    # Response/prompt ratio target
            "min_quality_score": 0.85       # Minimum quality threshold
        }
        
        self.monitoring = {
            "track_usage": True,
            "alert_threshold": 0.8,          # Alert at 80% of limits
            "report_frequency": "run",       # Per run reporting
            "quality_tracking": True
        }

class TokenManagementSystem:
    """
    Central system for all token management
    Coordinates optimization, limiting, and monitoring across all agents
    """
    
    def __init__(self, config: Optional[TokenManagementConfig] = None, 
                 model_name: str = "gpt-4o-mini"):
        self.config = config or TokenManagementConfig()
        self.model_name = model_name
        
        # Initialize components
        self.optimizer = get_enhanced_token_optimizer()
        self.limiter = get_intelligent_token_limiter(self.config.models)
        self.enhancer = get_prompt_enhancer()
        self.compressor = get_prompt_compressor()
        
        # Set model for limiter
        self.limiter.set_model(model_name)
        
        # Usage tracking
        self.usage_tracker = defaultdict(lambda: {
            "prompt_tokens": 0,
            "response_tokens": 0,
            "interactions": 0,
            "cost": 0,
            "optimizations": 0,
            "quality_scores": []
        })
        
        # Session tracking
        self.session_start = time.time()
        self.total_tokens_used = 0
        
        logger.info(f"🎯 Token Management System initialized for {model_name}")
    
    async def prepare_agent_interaction(self, agent_type: str, base_prompt: str,
                                      messages: List[Dict[str, Any]], 
                                      task_complexity: float = 0.5) -> Dict[str, Any]:
        """
        Prepare optimized interaction for an agent
        Applies all optimization layers and returns configuration
        
        Args:
            agent_type: Type of agent (e.g., 'market_analyst')
            base_prompt: Base system prompt for the agent
            messages: Conversation history
            task_complexity: Task complexity (0.0 to 1.0)
            
        Returns:
            Dict with optimized prompt, limits, and predictions
        """
        start_time = time.time()
        
        # Get agent-specific limits
        limits = self.config.agent_limits.get(agent_type, 
                                             {"prompt": 1200, "response": 400, "words": 250})
        
        # Step 1: Compress the base prompt
        compressed_result = self.compressor.compress_prompt(base_prompt)
        optimized_prompt = compressed_result.compressed
        
        # Step 2: Optimize for token reduction
        optimization = self.optimizer.optimize_system_prompt(optimized_prompt, agent_type)
        if optimization.quality_preserved and optimization.reduction_percentage > 10:
            optimized_prompt = optimization.optimized_prompt
        
        # Step 3: Add response length control
        controlled_prompt = self.optimizer.optimize_for_response_length(
            optimized_prompt, 
            limits["response"],
            agent_type
        )
        
        # Step 4: Enhance with word limits
        final_prompt = self.enhancer.enhance_prompt(controlled_prompt, agent_type)
        
        # Step 5: Calculate dynamic limits based on complexity
        dynamic_limits = self.optimizer.calculate_optimal_limits(
            self._get_task_type(agent_type),
            task_complexity,
            self._get_historical_performance(agent_type)
        )
        
        # Step 6: Prepare context with intelligent limiting
        context_result = self.limiter.check_and_prepare_context(
            messages, agent_type, include_prediction=True
        )
        
        # Step 7: Predict total usage
        prompt_tokens = self.optimizer.count_tokens(final_prompt) + context_result["prompt_tokens"]
        predicted_response = self.limiter.predict_response_tokens(
            final_prompt, agent_type, messages
        )
        
        # Check against targets
        total_predicted = prompt_tokens + predicted_response
        within_target = total_predicted <= self.config.optimization_targets["avg_tokens_per_agent"]
        
        if not within_target:
            logger.warning(f"⚠️ {agent_type} predicted to use {total_predicted} tokens "
                         f"(target: {self.config.optimization_targets['avg_tokens_per_agent']})")
        
        # Create allocation
        allocation = TokenAllocation(
            agent_type=agent_type,
            prompt_tokens=prompt_tokens,
            response_tokens=predicted_response,
            word_limit=limits["words"],
            total_budget=dynamic_limits["prompt"] + dynamic_limits["response"],
            optimization_applied=True,
            compression_applied=True
        )
        
        # Track preparation time
        prep_time = time.time() - start_time
        
        return {
            "prompt": final_prompt,
            "messages": context_result["messages"],
            "allocation": allocation,
            "max_tokens": dynamic_limits["response"],
            "word_limit": limits["words"],
            "predicted_usage": total_predicted,
            "within_target": within_target,
            "optimization_stats": {
                "original_tokens": compressed_result.original_tokens,
                "compressed_tokens": compressed_result.compressed_tokens,
                "reduction_percentage": compressed_result.reduction_percentage,
                "preparation_time": prep_time
            },
            "context_truncated": context_result["truncated"]
        }
    
    def post_interaction_analysis(self, agent_type: str, actual_response: str,
                                prompt_tokens: int, completion_tokens: int,
                                expected_sections: Optional[List[str]] = None):
        """
        Analyze and learn from actual usage
        Updates tracking and prediction models
        
        Args:
            agent_type: Type of agent
            actual_response: The actual response generated
            prompt_tokens: Actual prompt tokens used
            completion_tokens: Actual completion tokens used
            expected_sections: Expected sections for quality analysis
        """
        # Record usage
        self.usage_tracker[agent_type]["prompt_tokens"] += prompt_tokens
        self.usage_tracker[agent_type]["response_tokens"] += completion_tokens
        self.usage_tracker[agent_type]["interactions"] += 1
        
        # Calculate cost
        model_costs = self.config.models[self.model_name]
        cost = ((prompt_tokens / 1000) * model_costs["cost_per_1k_prompt"] +
                (completion_tokens / 1000) * model_costs["cost_per_1k_completion"])
        self.usage_tracker[agent_type]["cost"] += cost
        
        # Update total tracking
        self.total_tokens_used += prompt_tokens + completion_tokens
        
        # Record for prediction improvement
        word_count = len(actual_response.split())
        self.optimizer.record_actual_usage(agent_type, prompt_tokens, 
                                         completion_tokens, word_count)
        
        # Update limiter predictions
        predicted = self.limiter.predict_response_tokens("", agent_type)
        self.limiter.record_actual_response(agent_type, prompt_tokens, 
                                          completion_tokens, predicted)
        
        # Analyze quality if expected sections provided
        if expected_sections:
            quality_analysis = self.optimizer.analyze_response_quality(
                actual_response, agent_type, expected_sections
            )
            self.usage_tracker[agent_type]["quality_scores"].append(
                quality_analysis["quality_score"]
            )
            
            # Check word limit compliance
            word_limit = self.config.agent_limits[agent_type]["words"]
            if word_count > word_limit * 1.1:  # 10% tolerance
                logger.warning(f"📝 {agent_type} exceeded word limit: "
                             f"{word_count} > {word_limit}")
                self.usage_tracker[agent_type]["optimizations"] += 1
    
    def check_run_target(self) -> Dict[str, Any]:
        """
        Check if current run is meeting token targets
        
        Returns:
            Dict with target status and recommendations
        """
        run_target = self.config.optimization_targets["total_tokens_per_run"]
        current_usage = self.total_tokens_used
        
        # Calculate projection based on typical run pattern
        # Assume 12-15 agent interactions per full run
        avg_interactions = sum(data["interactions"] for data in self.usage_tracker.values())
        if avg_interactions > 0:
            projected_total = (current_usage / avg_interactions) * 13  # Use 13 as average
        else:
            projected_total = current_usage
        
        status = {
            "current_usage": current_usage,
            "projected_total": int(projected_total),
            "target": run_target,
            "on_track": projected_total <= run_target,
            "usage_percentage": (projected_total / run_target) * 100,
            "recommendations": []
        }
        
        if not status["on_track"]:
            overage = projected_total - run_target
            status["recommendations"].append(
                f"Reduce usage by {overage:,} tokens ({overage/run_target*100:.1f}%)"
            )
            
            # Find highest users
            by_usage = sorted(
                [(agent, data["prompt_tokens"] + data["response_tokens"]) 
                 for agent, data in self.usage_tracker.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            if by_usage:
                top_users = by_usage[:3]
                for agent, usage in top_users:
                    if usage > 3000:
                        status["recommendations"].append(
                            f"Optimize {agent} (currently using {usage:,} tokens)"
                        )
        
        return status
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        # Calculate aggregate metrics
        total_prompt = sum(data["prompt_tokens"] for data in self.usage_tracker.values())
        total_response = sum(data["response_tokens"] for data in self.usage_tracker.values())
        total_interactions = sum(data["interactions"] for data in self.usage_tracker.values())
        total_cost = sum(data["cost"] for data in self.usage_tracker.values())
        
        # Get component reports
        optimizer_report = self.optimizer.generate_optimization_report()
        limiter_accuracy = self.limiter.get_prediction_accuracy_report()
        compressor_stats = self.compressor.get_compression_stats()
        enhancer_usage = self.enhancer.get_usage_report()
        
        # Check against targets
        run_target_status = self.check_run_target()
        
        # Build comprehensive report
        report = {
            "summary": {
                "total_tokens": total_prompt + total_response,
                "total_cost": round(total_cost, 4),
                "total_interactions": total_interactions,
                "avg_tokens_per_interaction": (total_prompt + total_response) / max(total_interactions, 1),
                "session_duration": time.time() - self.session_start
            },
            
            "by_agent": {},
            
            "optimization_effectiveness": {
                "prompt_compression": compressor_stats,
                "response_control": enhancer_usage,
                "prediction_accuracy": limiter_accuracy,
                "quality_metrics": optimizer_report.get("quality_metrics", {})
            },
            
            "target_analysis": run_target_status,
            
            "recommendations": self._generate_recommendations(),
            
            "component_reports": {
                "optimizer": optimizer_report,
                "limiter": limiter_accuracy,
                "compressor": compressor_stats,
                "enhancer": enhancer_usage
            }
        }
        
        # Add per-agent details
        for agent_type, data in self.usage_tracker.items():
            if data["interactions"] > 0:
                avg_quality = (sum(data["quality_scores"]) / len(data["quality_scores"]) 
                             if data["quality_scores"] else 0)
                
                report["by_agent"][agent_type] = {
                    "interactions": data["interactions"],
                    "avg_prompt_tokens": data["prompt_tokens"] / data["interactions"],
                    "avg_response_tokens": data["response_tokens"] / data["interactions"],
                    "total_tokens": data["prompt_tokens"] + data["response_tokens"],
                    "cost": round(data["cost"], 4),
                    "avg_quality_score": round(avg_quality, 2),
                    "optimizations_triggered": data["optimizations"]
                }
        
        return report
    
    def _get_task_type(self, agent_type: str) -> str:
        """Map agent type to task type for optimization"""
        task_mapping = {
            "market_analyst": "analysis",
            "news_analyst": "summary",
            "fundamentals_analyst": "analysis",
            "risk_manager": "analysis",
            "research_manager": "synthesis",
            "trader": "decision",
            "bull_researcher": "research",
            "bear_researcher": "research",
            "aggressive_debator": "analysis",
            "conservative_debator": "analysis",
            "neutral_debator": "analysis"
        }
        return task_mapping.get(agent_type, "analysis")
    
    def _get_historical_performance(self, agent_type: str) -> Optional[Dict]:
        """Get historical performance metrics for an agent"""
        if agent_type not in self.usage_tracker:
            return None
        
        data = self.usage_tracker[agent_type]
        if data["interactions"] == 0:
            return None
        
        avg_response = data["response_tokens"] / data["interactions"]
        target_response = self.config.agent_limits.get(agent_type, {}).get("response", 400)
        
        return {
            "avg_response_overage": (avg_response - target_response) / target_response
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check overall token usage
        if self.total_tokens_used > self.config.optimization_targets["total_tokens_per_run"] * 0.8:
            recommendations.append("Approaching token limit - increase compression aggressiveness")
        
        # Check per-agent performance
        for agent_type, data in self.usage_tracker.items():
            if data["interactions"] > 0:
                avg_tokens = (data["prompt_tokens"] + data["response_tokens"]) / data["interactions"]
                
                if avg_tokens > self.config.optimization_targets["avg_tokens_per_agent"]:
                    recommendations.append(
                        f"Optimize {agent_type} prompts (avg: {avg_tokens:.0f} tokens)"
                    )
                
                # Check quality scores
                if data["quality_scores"]:
                    avg_quality = sum(data["quality_scores"]) / len(data["quality_scores"])
                    if avg_quality < self.config.optimization_targets["min_quality_score"]:
                        recommendations.append(
                            f"Improve {agent_type} response quality (score: {avg_quality:.2f})"
                        )
        
        # Check prediction accuracy
        accuracy_report = self.limiter.get_prediction_accuracy_report()
        if accuracy_report["overall"]["avg_error_rate"] > 0.3:
            recommendations.append(
                "Improve response prediction models (30%+ error rate)"
            )
        
        return recommendations
    
    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """Export detailed metrics to JSON file"""
        report = self.generate_optimization_report()
        
        # Add timestamp
        report["exported_at"] = datetime.now().isoformat()
        report["model"] = self.model_name
        
        if filepath is None:
            filepath = f"token_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Exported token metrics to {filepath}")
        return filepath
    
    def reset_session_tracking(self):
        """Reset session tracking for new run"""
        self.session_start = time.time()
        self.total_tokens_used = 0
        self.usage_tracker.clear()
        logger.info("🔄 Reset token tracking for new session")

# Global instance
_token_management_system: Optional[TokenManagementSystem] = None

def get_token_management_system(config: Optional[TokenManagementConfig] = None,
                               model_name: str = "gpt-4o-mini") -> TokenManagementSystem:
    """Get the global token management system instance"""
    global _token_management_system
    
    if _token_management_system is None:
        _token_management_system = TokenManagementSystem(config, model_name)
    
    return _token_management_system