#!/usr/bin/env python3
"""
Token Configuration for Trading Agents
Central configuration for token management across the system
"""

from typing import Dict, Any

# Token limits and targets
TOKEN_LIMITS = {
    "models": {
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
    },
    
    "agent_limits": {
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
    },
    
    "optimization_targets": {
        "total_tokens_per_run": 40000,     # Target from trace analysis
        "avg_tokens_per_agent": 2500,      # Average per agent interaction
        "response_conciseness": 0.7,       # Response/prompt ratio target
        "min_quality_score": 0.85,         # Minimum quality threshold
        "compression_target": 0.22         # 22% reduction target
    }
}

# Feature flags for token optimization
TOKEN_OPTIMIZATION_FLAGS = {
    "enable_compression": True,           # Enable prompt compression
    "enable_response_control": True,      # Enable response length control
    "enable_intelligent_limiting": True,  # Enable predictive token limiting
    "enable_quality_tracking": True,      # Track response quality
    "enable_cost_tracking": True,         # Track API costs
    "enable_auto_adjustment": True,       # Auto-adjust limits based on performance
    "enable_session_reports": True,       # Generate per-session reports
    "debug_mode": False                   # Extra logging for debugging
}

# Quality requirements by agent type
QUALITY_REQUIREMENTS = {
    "market_analyst": [
        "recommendation",          # BUY/SELL/HOLD
        "indicators",             # Technical indicators
        "risk",                   # Risk assessment
        "strategy"                # Entry/exit strategy
    ],
    "news_analyst": [
        "sentiment",              # Sentiment score
        "impact",                 # Market impact
        "headlines",              # Key headlines
        "recommendation"          # Trading recommendation
    ],
    "fundamentals_analyst": [
        "valuation",              # Valuation metrics
        "metrics",                # Financial metrics
        "outlook",                # Future outlook
        "recommendation"          # Investment recommendation
    ],
    "risk_manager": [
        "risks",                  # Identified risks
        "mitigation",             # Mitigation strategies
        "assessment",             # Overall assessment
        "recommendation"          # Risk-adjusted recommendation
    ],
    "trader": [
        "decision",               # BUY/SELL/HOLD decision
        "entry",                  # Entry price
        "exit",                   # Exit price (SL/TP)
        "position"                # Position size
    ]
}

def get_agent_token_config(agent_type: str) -> Dict[str, Any]:
    """Get token configuration for a specific agent"""
    return {
        "limits": TOKEN_LIMITS["agent_limits"].get(
            agent_type, 
            {"prompt": 1200, "response": 400, "words": 250}
        ),
        "quality_requirements": QUALITY_REQUIREMENTS.get(agent_type, []),
        "optimization_enabled": TOKEN_OPTIMIZATION_FLAGS["enable_compression"],
        "response_control_enabled": TOKEN_OPTIMIZATION_FLAGS["enable_response_control"]
    }

def get_model_token_config(model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Get token configuration for a specific model"""
    return TOKEN_LIMITS["models"].get(
        model_name,
        TOKEN_LIMITS["models"]["gpt-4o-mini"]
    )

def should_enable_token_optimization() -> bool:
    """Check if token optimization should be enabled"""
    return (TOKEN_OPTIMIZATION_FLAGS["enable_compression"] or 
            TOKEN_OPTIMIZATION_FLAGS["enable_response_control"] or
            TOKEN_OPTIMIZATION_FLAGS["enable_intelligent_limiting"])