"""
Smart Retry System for Tool Execution
Optimization 4: Skip unnecessary retries when valid data is present
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SmartRetryValidator:
    """Smart retry validation system that prevents unnecessary retries"""
    
    @staticmethod
    def should_skip_retry(analyst_type: str, messages: List[Any], state: Dict[str, Any]) -> bool:
        """
        Determine if retry should be skipped based on data quality
        
        Args:
            analyst_type: Type of analyst (market, social, news, fundamentals)
            messages: List of messages from the analyst
            state: Current state dictionary
            
        Returns:
            True if retry should be skipped, False if retry is needed
        """
        if not messages:
            return False
        
        # Check retry count to avoid infinite loops
        retry_count = state.get(f"{analyst_type}_retry_count", 0)
        if retry_count >= 2:
            logger.info(f"🛑 {analyst_type.upper()}: Max retries reached, skipping")
            return True
        
        # Check if we have valid tool responses
        tool_messages = SmartRetryValidator._get_tool_messages(messages)
        
        if not tool_messages:
            logger.info(f"📋 {analyst_type.upper()}: No tool responses found, retry may be needed")
            return False
        
        # Analyze tool response quality
        quality_score = SmartRetryValidator._assess_data_quality(analyst_type, tool_messages)
        
        if quality_score >= 0.7:
            logger.info(f"✅ {analyst_type.upper()}: High quality data (score: {quality_score:.2f}), skipping retry")
            return True
        elif quality_score >= 0.4:
            logger.info(f"⚠️ {analyst_type.upper()}: Moderate quality data (score: {quality_score:.2f}), skipping retry for efficiency")
            return True
        else:
            logger.info(f"❌ {analyst_type.upper()}: Low quality data (score: {quality_score:.2f}), retry needed")
            return False
    
    @staticmethod
    def _get_tool_messages(messages: List[Any]) -> List[Any]:
        """Extract tool messages from message list"""
        tool_messages = []
        
        for msg in messages:
            # Check for ToolMessage type
            if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool':
                tool_messages.append(msg)
            elif hasattr(msg, '__class__') and 'ToolMessage' in str(msg.__class__):
                tool_messages.append(msg)
            elif hasattr(msg, 'content') and hasattr(msg, 'tool_call_id'):
                tool_messages.append(msg)
        
        return tool_messages
    
    @staticmethod
    def _assess_data_quality(analyst_type: str, tool_messages: List[Any]) -> float:
        """
        Assess the quality of tool response data
        
        Returns:
            Quality score from 0.0 to 1.0
        """
        if not tool_messages:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for msg in tool_messages:
            content = getattr(msg, 'content', '')
            if not content:
                continue
            
            score = 0.0
            weight = 1.0
            
            # Check for error messages
            if content.startswith('Error') or 'error' in content.lower():
                score = 0.1  # Very low score for errors
            elif len(content) < 50:
                score = 0.2  # Low score for very short responses
            elif len(content) < 200:
                score = 0.5  # Moderate score for short responses
            else:
                score = 0.8  # Good base score for substantial responses
                
                # Bonus for analyst-specific indicators
                score += SmartRetryValidator._get_analyst_specific_bonus(analyst_type, content)
            
            # Weight by content length (longer content = more important)
            weight = min(len(content) / 1000, 2.0)  # Cap at 2x weight
            
            total_score += score * weight
            total_weight += weight
        
        # Calculate weighted average
        if total_weight == 0:
            return 0.0
        
        final_score = total_score / total_weight
        return min(final_score, 1.0)  # Cap at 1.0
    
    @staticmethod
    def _get_analyst_specific_bonus(analyst_type: str, content: str) -> float:
        """Get bonus points for analyst-specific quality indicators"""
        content_lower = content.lower()
        bonus = 0.0
        
        if analyst_type == "market":
            # Look for market data indicators
            indicators = ['price', 'volume', 'change', 'high', 'low', 'open', 'close']
            bonus += sum(0.02 for indicator in indicators if indicator in content_lower)
            
        elif analyst_type == "social":
            # Look for sentiment indicators
            indicators = ['sentiment', 'bullish', 'bearish', 'positive', 'negative', 'mentions']
            bonus += sum(0.02 for indicator in indicators if indicator in content_lower)
            
        elif analyst_type == "news":
            # Look for news indicators
            indicators = ['news', 'article', 'headline', 'report', 'announcement', 'earnings']
            bonus += sum(0.02 for indicator in indicators if indicator in content_lower)
            
        elif analyst_type == "fundamentals":
            # Look for fundamental indicators
            indicators = ['revenue', 'profit', 'earnings', 'debt', 'cash', 'ratio', 'balance sheet']
            bonus += sum(0.02 for indicator in indicators if indicator in content_lower)
        
        return min(bonus, 0.2)  # Cap bonus at 0.2
    
    @staticmethod
    def log_retry_decision(analyst_type: str, should_skip: bool, reason: str):
        """Log the retry decision for debugging"""
        if should_skip:
            logger.info(f"🚀 OPTIMIZATION 4: {analyst_type.upper()} retry SKIPPED - {reason}")
        else:
            logger.info(f"🔄 RETRY: {analyst_type.upper()} retry NEEDED - {reason}")

def should_skip_analyst_retry(analyst_type: str, messages: List[Any], state: Dict[str, Any]) -> bool:
    """
    Main function to determine if analyst retry should be skipped
    
    This is the primary interface for the retry optimization system.
    
    Args:
        analyst_type: Type of analyst
        messages: Messages from the analyst
        state: Current state
        
    Returns:
        True if retry should be skipped, False otherwise
    """
    from .optimization_logger import optimization_tracker
    
    result = SmartRetryValidator.should_skip_retry(analyst_type, messages, state)
    
    if result:
        optimization_tracker.log_optimization_start("SMART_RETRY_SKIP", f"{analyst_type} analyst - skipping unnecessary retry")
        optimization_tracker.log_optimization_end("SMART_RETRY_SKIP", time_saved=2.5)  # Average retry time saved
    
    return result