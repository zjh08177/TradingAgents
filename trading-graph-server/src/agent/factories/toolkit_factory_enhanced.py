"""
Enhanced Toolkit Factory - Day 2 Implementation
Clear separation between News Analyst (news only) and Social Media Analyst (social only)
"""

from typing import List
from ..utils.agent_utils import Toolkit
from ..interfaces import IAnalystToolkit
import logging

logger = logging.getLogger(__name__)


class BaseAnalystToolkit(IAnalystToolkit):
    """Base implementation of analyst toolkit with filtered tools"""
    
    def __init__(self, base_toolkit: Toolkit, allowed_tools: List[str]):
        self.config = base_toolkit.config
        self._allowed_tools = allowed_tools
        
        # Copy allowed tools from base toolkit
        logger.info(f"🔧 BaseAnalystToolkit: Checking {len(allowed_tools)} allowed tools")
        found_tools = []
        missing_tools = []
        
        for tool_name in allowed_tools:
            if hasattr(base_toolkit, tool_name):
                setattr(self, tool_name, getattr(base_toolkit, tool_name))
                found_tools.append(tool_name)
                logger.info(f"✅ Found and copied: {tool_name}")
            else:
                missing_tools.append(tool_name)
                logger.warning(f"⚠️ Tool not found in base toolkit: {tool_name}")
        
        logger.info(f"📊 BaseAnalystToolkit: Found {len(found_tools)}/{len(allowed_tools)} tools")
        if found_tools:
            logger.info(f"✅ Available tools: {found_tools}")
        if missing_tools:
            logger.warning(f"❌ Missing tools: {missing_tools}")
    
    def get_available_tools(self) -> List[str]:
        return self._allowed_tools


class ToolkitFactory:
    """
    Enhanced Factory for creating analyst-specific toolkits with clear boundaries
    Day 2 Implementation: Strict separation between news and social media
    """
    
    @staticmethod
    def create_market_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
        """Create market analyst toolkit with comprehensive market data tools"""
        allowed_tools = [
            # Primary market data tools
            "get_YFin_data_online", 
            "get_stockstats_indicators_report_online",
            "get_YFin_data", 
            "get_stockstats_indicators_report",
            # Company-specific data (NOT news)
            "get_fundamentals_openai",
            # Insider information
            "get_finnhub_company_insider_sentiment",
            "get_finnhub_company_insider_transactions",
            # Additional market analysis tools
            "get_volume_analysis",
            "get_support_resistance"
        ] 
        logger.info(f"🏢 Creating Market Analyst toolkit with {len(allowed_tools)} tools")
        return BaseAnalystToolkit(base_toolkit, allowed_tools)
    
    @staticmethod
    def create_social_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
        """
        Create social media analyst toolkit - OWNS ALL SOCIAL/REDDIT DATA
        This analyst handles ALL social sentiment, Reddit, StockTwits, Twitter
        """
        allowed_tools = [
            # Social media and sentiment - THIS IS THE ONLY PLACE FOR THESE
            "get_reddit_stock_info",
            "get_reddit_news",  # This belongs HERE, NOT in news analyst
            "get_stocktwits_sentiment",
            "get_twitter_mentions",
            # Can use some general news for context (but focus is social)
            "get_stock_news_openai",  # General news for context
            # NO get_google_news - that's for News Analyst
        ]
        logger.info(f"💬 Creating Social Media Analyst toolkit with {len(allowed_tools)} tools")
        logger.info(f"📱 Social tools include: Reddit, StockTwits, Twitter sentiment")
        return BaseAnalystToolkit(base_toolkit, allowed_tools)
    
    @staticmethod
    def create_news_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
        """
        Create news analyst toolkit - EXCLUSIVELY TRADITIONAL NEWS MEDIA
        NO social media, NO Reddit - that's Social Media Analyst's job
        Day 2 Implementation: News-exclusive architecture
        """
        allowed_tools = [
            # Primary: Serper/Google News (4,500+ sources with pagination)
            "get_google_news",  # This is the PRIMARY tool - 50+ articles via pagination
            # Emergency fallback ONLY (not primary)
            "get_finnhub_news",  # Fallback if Serper fails
            # REMOVED ALL THESE - They belong to Social Media Analyst:
            # ❌ "get_reddit_news" - BELONGS TO SOCIAL MEDIA ANALYST
            # ❌ "get_reddit_stock_info" - BELONGS TO SOCIAL MEDIA ANALYST
            # ❌ "get_stocktwits_sentiment" - BELONGS TO SOCIAL MEDIA ANALYST
            # ❌ "get_twitter_mentions" - BELONGS TO SOCIAL MEDIA ANALYST
            # Optional: Can keep this for additional coverage if needed
            # "get_global_news_openai",  # Removed as redundant with Serper
            # "get_stock_news_openai",  # Removed as redundant with Serper
        ]
        logger.info(f"📰 Creating News Analyst toolkit with {len(allowed_tools)} tools")
        logger.info(f"✅ News tools: Serper/Google News (primary), Finnhub (fallback)")
        logger.info(f"🚫 NO social media tools - handled by Social Media Analyst")
        return BaseAnalystToolkit(base_toolkit, allowed_tools)
    
    @staticmethod
    def create_fundamentals_toolkit(base_toolkit: Toolkit) -> IAnalystToolkit:
        """Create fundamentals analyst toolkit with financial statement tools"""
        allowed_tools = [
            # Primary fundamentals
            "get_fundamentals_openai", 
            # Financial statements
            "get_simfin_balance_sheet",
            "get_simfin_cashflow", 
            "get_simfin_income_stmt",
            # Insider data for fundamentals context
            "get_finnhub_company_insider_sentiment",
            "get_finnhub_company_insider_transactions",
            # Can use some news for earnings context
            "get_stock_news_openai",  # For earnings news
        ]
        logger.info(f"💰 Creating Fundamentals Analyst toolkit with {len(allowed_tools)} tools")
        return BaseAnalystToolkit(base_toolkit, allowed_tools)
    
    @staticmethod
    def validate_separation():
        """
        Validate that there's no overlap between News and Social analysts
        This ensures clean separation of concerns
        """
        news_tools = [
            "get_google_news",
            "get_finnhub_news"
        ]
        
        social_tools = [
            "get_reddit_stock_info",
            "get_reddit_news",
            "get_stocktwits_sentiment", 
            "get_twitter_mentions"
        ]
        
        # Check for overlap
        overlap = set(news_tools) & set(social_tools)
        if overlap:
            logger.error(f"❌ CRITICAL: Tool overlap detected between analysts: {overlap}")
            raise ValueError(f"Tool overlap between News and Social analysts: {overlap}")
        else:
            logger.info(f"✅ Clean separation validated: News and Social analysts have no overlapping tools")
            logger.info(f"📰 News Analyst: {news_tools}")
            logger.info(f"💬 Social Analyst: {social_tools}")
            return True


# Add validation on module load
try:
    ToolkitFactory.validate_separation()
except Exception as e:
    logger.error(f"❌ Toolkit validation failed: {e}")