"""
Toolkit Factory - Single responsibility for creating analyst-specific toolkits
"""

from typing import List
from ..utils.agent_utils import Toolkit
from ..interfaces import IAnalystToolkit

class BaseAnalystToolkit(IAnalystToolkit):
    """Base implementation of analyst toolkit with filtered tools"""
    
    def __init__(self, base_toolkit: Toolkit, allowed_tools: List[str]):
        self.config = base_toolkit.config
        self._allowed_tools = allowed_tools
        
        # Copy allowed tools from base toolkit
        for tool_name in allowed_tools:
            if hasattr(base_toolkit, tool_name):
                setattr(self, tool_name, getattr(base_toolkit, tool_name))
    
    def get_available_tools(self) -> List[str]:
        return self._allowed_tools

class ToolkitFactory:
    """Factory for creating analyst-specific toolkits"""
    
    @staticmethod
    def create_market_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
        """Create market analyst toolkit with comprehensive market data tools"""
        allowed_tools = [
            # Primary market data tools
            "get_YFin_data_online", 
            "get_stockstats_indicators_report_online",
            "get_YFin_data", 
            "get_stockstats_indicators_report",
            # Company-specific data
            "get_stock_news_openai",
            "get_fundamentals_openai",
            # Insider information
            "get_finnhub_company_insider_sentiment",
            "get_finnhub_company_insider_transactions"
        ] 
        return BaseAnalystToolkit(base_toolkit, allowed_tools)
    
    @staticmethod
    def create_social_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
        """Create social media analyst toolkit with sentiment and social data tools"""
        allowed_tools = [
            # Social media and sentiment
            "get_google_news",
            "get_stock_news_openai",
            "get_reddit_stock_info",
            # General social sentiment  
            "get_reddit_news"
        ]
        return BaseAnalystToolkit(base_toolkit, allowed_tools)
    
    @staticmethod
    def create_news_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
        """Create news analyst toolkit with comprehensive news sources"""
        allowed_tools = [
            # Global news sources
            "get_global_news_openai", 
            "get_google_news",
            "get_reddit_news",
            # Company-specific news
            "get_finnhub_news",
            "get_stock_news_openai"
        ]
        return BaseAnalystToolkit(base_toolkit, allowed_tools)
    
    @staticmethod
    def create_fundamentals_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
        """Create fundamentals analyst toolkit with financial statement tools"""
        allowed_tools = [
            # Primary fundamentals
            "get_fundamentals_openai", 
            "get_stock_news_openai",
            # Financial statements
            "get_simfin_balance_sheet",
            "get_simfin_cashflow", 
            "get_simfin_income_stmt",
            # Insider data for fundamentals context
            "get_finnhub_company_insider_sentiment",
            "get_finnhub_company_insider_transactions"
        ]
        return BaseAnalystToolkit(base_toolkit, allowed_tools) 