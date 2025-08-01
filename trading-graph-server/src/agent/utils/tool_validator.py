"""Tool usage validation to ensure data integrity"""
import logging
from typing import List, Dict, Any
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

class ToolUsageValidator:
    """Validates that analysts use tools before providing analysis"""
    
    REQUIRED_TOOLS = {
        "market": ["get_YFin_data", "get_stockstats_indicators_report"],
        "news": ["get_global_news_openai", "get_finnhub_news", "get_google_news"],
        "social": ["get_reddit_stock_info", "get_stock_news_openai"],
        "fundamentals": ["get_fundamentals_openai", "get_simfin_balance_sheet", "get_simfin_income_stmt"]
    }
    
    @classmethod
    def validate_analyst_response(cls, 
                                analyst_type: str, 
                                messages: List[Any]) -> bool:
        """Check if analyst called required tools"""
        if not messages:
            logger.error(f"{analyst_type} analyst: No messages")
            return False
            
        # Check for tool calls in messages
        has_tool_calls = any(
            hasattr(msg, 'tool_calls') and msg.tool_calls 
            for msg in messages
        )
        
        if not has_tool_calls:
            logger.error(f"❌ {analyst_type} analyst: NO TOOLS CALLED - Analysis invalid!")
            return False
            
        # Verify required tools were called
        called_tools = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                called_tools.extend([tc['name'] for tc in msg.tool_calls])
        
        required = cls.REQUIRED_TOOLS.get(analyst_type, [])
        
        # For flexibility, check if at least one required tool was called
        # since some tools may be alternatives (online vs offline)
        has_required_tool = any(
            any(req_tool in tool for tool in called_tools)
            for req_tool in required
        )
        
        if not has_required_tool and required:
            logger.warning(f"⚠️ {analyst_type}: No required tools called. Called: {called_tools}, Required: {required}")
            return False
            
        logger.info(f"✅ {analyst_type}: Tool validation passed. Called tools: {called_tools}")
        return True
    
    @classmethod
    def get_validation_message(cls, analyst_type: str) -> str:
        """Get a message to prompt the analyst to use tools"""
        required = cls.REQUIRED_TOOLS.get(analyst_type, [])
        return f"You MUST call at least one of these tools before providing analysis: {', '.join(required)}. No analysis is allowed without real data from tools."