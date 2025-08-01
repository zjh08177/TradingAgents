#!/usr/bin/env python3
"""
Agent Prompt Enhancer - Adds response word limits and optimization to all agent prompts
Part of the Enhanced Token Optimization Strategy
"""

import logging
import asyncio
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AgentPromptEnhancer:
    """Enhances agent prompts with response control and word limits"""
    
    # Agent-specific word limits based on analysis needs
    WORD_LIMITS = {
        "market_analyst": 300,          # Technical data is concise
        "news_analyst": 250,            # Headlines and impacts
        "social_media_analyst": 200,    # Sentiment summaries  
        "fundamentals_analyst": 350,    # Financial data needs more
        "risk_manager": 250,            # Risk points are brief
        "research_manager": 400,        # Synthesis needs space
        "trader": 150,                  # Decisions are binary
        "bull_researcher": 300,         # Bullish analysis
        "bear_researcher": 300,         # Bearish analysis
        "default": 250                  # Fallback limit
    }
    
    # Response control template to inject into prompts
    RESPONSE_CONTROL_TEMPLATE = """
RESPONSE CONSTRAINTS (MANDATORY):
- Maximum response: {max_words} words (STRICT LIMIT)
- Format: Use bullet points and tables over paragraphs
- Focus: Key insights only, no filler content  
- Structure: Clear headers and sections
- Conciseness: Every word must add value
- Data: Include only essential metrics
- Clarity: Be direct and actionable

FORMATTING RULES:
- Use "•" for bullet points
- Keep sections short (2-3 sentences max)
- Tables: Maximum 5 rows, 4 columns
- Numbers: Round to 2 decimal places
- Avoid: Repetition, obvious statements, lengthy explanations
"""
    
    # Concise summary template for end of prompts
    SUMMARY_REMINDER = """

FINAL REMINDER: Your response MUST be under {max_words} words. 
Focus on: 1) Key finding, 2) Critical data, 3) Clear recommendation.
Omit: Verbose explanations, redundant information, filler phrases."""
    
    def __init__(self):
        self.applied_count = 0
        self.effectiveness_tracker = {}
        logger.info("🎯 Agent Prompt Enhancer initialized")
    
    def enhance_prompt(self, base_prompt: str, agent_type: str, 
                      custom_limit: Optional[int] = None) -> str:
        """
        Enhance an agent prompt with response control and word limits
        
        Args:
            base_prompt: Original agent prompt
            agent_type: Type of agent (e.g., 'market_analyst')
            custom_limit: Optional custom word limit override
            
        Returns:
            Enhanced prompt with response controls
        """
        # Get word limit for this agent type
        max_words = custom_limit or self.WORD_LIMITS.get(
            agent_type, 
            self.WORD_LIMITS["default"]
        )
        
        # Create response control section
        response_control = self.RESPONSE_CONTROL_TEMPLATE.format(max_words=max_words)
        
        # Create summary reminder
        summary_reminder = self.SUMMARY_REMINDER.format(max_words=max_words)
        
        # Construct enhanced prompt
        enhanced_prompt = f"{response_control}\n\n{base_prompt}{summary_reminder}"
        
        # Track application
        self.applied_count += 1
        if agent_type not in self.effectiveness_tracker:
            self.effectiveness_tracker[agent_type] = {
                "applications": 0,
                "word_limit": max_words
            }
        self.effectiveness_tracker[agent_type]["applications"] += 1
        
        logger.info(f"✅ Enhanced {agent_type} prompt with {max_words} word limit")
        
        return enhanced_prompt
    
    async def enhance_prompt_async(self, base_prompt: str, agent_type: str, 
                                  custom_limit: Optional[int] = None) -> str:
        """
        Async version of enhance_prompt - runs enhancement in thread pool
        """
        # Run the enhancement in a thread pool (though it's mostly string operations)
        return await asyncio.to_thread(self.enhance_prompt, base_prompt, agent_type, custom_limit)
    
    def add_inline_limits(self, prompt: str, agent_type: str) -> str:
        """
        Add inline word limit reminders throughout the prompt
        Useful for long prompts where agents might forget the limit
        """
        max_words = self.WORD_LIMITS.get(agent_type, self.WORD_LIMITS["default"])
        
        # Add reminders after each major section header
        import re
        
        # Pattern to find section headers (###, ##, #)
        section_pattern = r'(#{1,3}\s+\d*\.?\s*[A-Za-z\s]+)(\n)'
        
        # Counter for sections
        section_count = 0
        
        def add_reminder(match):
            nonlocal section_count
            section_count += 1
            
            # Add reminder every 3 sections
            if section_count % 3 == 0:
                return f"{match.group(1)} (Remember: {max_words} word limit){match.group(2)}"
            return match.group(0)
        
        enhanced = re.sub(section_pattern, add_reminder, prompt)
        
        return enhanced
    
    def create_compact_instruction(self, instruction_type: str) -> str:
        """
        Create compact versions of common instructions
        Reduces token usage in prompts
        """
        compact_instructions = {
            "analysis": "Analyze and provide insights in bullet points",
            "recommendation": "Give clear BUY/SELL/HOLD with confidence %",
            "metrics": "Show key metrics in a simple table",
            "summary": "Summarize in 2-3 sentences max",
            "risks": "List top 3 risks with mitigation",
            "data": "Include only essential numbers (2 decimals)",
            "format": "Use headers, bullets, and tables",
            "conclusion": "End with 1 actionable recommendation"
        }
        
        return compact_instructions.get(instruction_type, "")
    
    def optimize_agent_prompts(self, prompts_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Batch optimize multiple agent prompts
        
        Args:
            prompts_dict: Dictionary of {agent_type: prompt}
            
        Returns:
            Dictionary of {agent_type: enhanced_prompt}
        """
        optimized_prompts = {}
        
        for agent_type, prompt in prompts_dict.items():
            # Enhance with word limits
            enhanced = self.enhance_prompt(prompt, agent_type)
            
            # Add inline reminders for long prompts
            if len(prompt) > 2000:  # Long prompt threshold
                enhanced = self.add_inline_limits(enhanced, agent_type)
            
            optimized_prompts[agent_type] = enhanced
            
        logger.info(f"🚀 Batch optimized {len(optimized_prompts)} agent prompts")
        
        return optimized_prompts
    
    def get_usage_report(self) -> Dict:
        """Get report on prompt enhancement effectiveness"""
        return {
            "total_enhanced": self.applied_count,
            "by_agent": self.effectiveness_tracker,
            "average_word_limit": sum(
                limits["word_limit"] for limits in self.effectiveness_tracker.values()
            ) / max(len(self.effectiveness_tracker), 1)
        }
    
    def create_example_enhanced_prompt(self, agent_type: str) -> str:
        """Create an example enhanced prompt for demonstration"""
        
        base_examples = {
            "market_analyst": """You are an expert market analyst.
Analyze technical indicators and provide trading recommendations.""",
            
            "news_analyst": """You are a news analyst.
Analyze news sentiment and market impact.""",
            
            "trader": """You are a trader.
Make trading decisions based on analysis."""
        }
        
        base_prompt = base_examples.get(agent_type, "You are an AI agent.")
        enhanced = self.enhance_prompt(base_prompt, agent_type)
        
        return enhanced


# Global instance for easy access
_prompt_enhancer = None

def get_prompt_enhancer() -> AgentPromptEnhancer:
    """Get global prompt enhancer instance"""
    global _prompt_enhancer
    if _prompt_enhancer is None:
        _prompt_enhancer = AgentPromptEnhancer()
    return _prompt_enhancer


def enhance_agent_prompt(base_prompt: str, agent_type: str) -> str:
    """Convenience function to enhance a single prompt"""
    enhancer = get_prompt_enhancer()
    return enhancer.enhance_prompt(base_prompt, agent_type)


# Example usage and testing
if __name__ == "__main__":
    # Test the enhancer
    enhancer = AgentPromptEnhancer()
    
    # Test with market analyst
    test_prompt = """You are an expert market analyst specializing in technical analysis.
    
Your role is to analyze market data and provide trading recommendations based on technical indicators."""
    
    enhanced = enhancer.enhance_prompt(test_prompt, "market_analyst")
    print("Enhanced Market Analyst Prompt:")
    print("-" * 50)
    print(enhanced)
    print("-" * 50)
    
    # Show usage report
    print("\nUsage Report:")
    print(enhancer.get_usage_report())