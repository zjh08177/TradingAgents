"""
Social Media Analyst with Hardcoded Parallel Tool Execution
Ensures all 3 social media tools are ALWAYS called in parallel
"""

import asyncio
import time
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

async def execute_all_social_tools(toolkit, ticker: str, current_date: str) -> Dict[str, Any]:
    """
    Hardcoded parallel execution of all 3 social media tools.
    This bypasses LLM tool selection to ensure 100% tool utilization.
    
    Args:
        toolkit: The analyst toolkit with social media tools
        ticker: Stock ticker symbol
        current_date: Current date for analysis
        
    Returns:
        Combined results from all 3 tools
    """
    logger.info(f"⚡ HARDCODED EXECUTION: Starting parallel execution of ALL 3 social tools for {ticker}")
    
    # Import the tool functions
    from ..dataflows.interface_new_tools import (
        get_reddit_stock_info,
        get_twitter_mentions,
        get_stocktwits_sentiment
    )
    
    # Track execution time
    start_time = time.time()
    
    # Execute all 3 tools in parallel - NO LLM DECISION NEEDED
    try:
        results = await asyncio.gather(
            get_reddit_stock_info(ticker, current_date),
            get_twitter_mentions(ticker),
            get_stocktwits_sentiment(ticker),
            return_exceptions=True  # Don't fail if one tool fails
        )
        
        reddit_result, twitter_result, stocktwits_result = results
        
        # Log execution results
        execution_time = time.time() - start_time
        logger.info(f"✅ HARDCODED EXECUTION: All 3 tools executed in {execution_time:.2f}s")
        
        # Handle any exceptions from individual tools
        if isinstance(reddit_result, Exception):
            logger.error(f"❌ Reddit tool failed: {reddit_result}")
            reddit_result = {"error": str(reddit_result), "posts": 0, "sentiment_score": 0.5}
        else:
            logger.info(f"✅ Reddit: {reddit_result.get('posts', 0)} posts found")
            
        if isinstance(twitter_result, Exception):
            logger.error(f"❌ Twitter tool failed: {twitter_result}")
            twitter_result = {"error": str(twitter_result), "mentions": 0, "sentiment_score": 0.5}
        else:
            logger.info(f"✅ Twitter: {twitter_result.get('mentions', 0)} mentions found")
            
        if isinstance(stocktwits_result, Exception):
            logger.error(f"❌ StockTwits tool failed: {stocktwits_result}")
            stocktwits_result = {"error": str(stocktwits_result), "mentions": 0, "score": 0.5}
        else:
            logger.info(f"✅ StockTwits: {stocktwits_result.get('mentions', 0)} messages found")
        
        # Combine results into structured format
        combined_results = {
            "ticker": ticker,
            "execution_time": execution_time,
            "tools_executed": 3,
            "reddit": reddit_result,
            "twitter": twitter_result,
            "stocktwits": stocktwits_result
        }
        
        logger.info(f"📊 HARDCODED EXECUTION: Successfully gathered data from all 3 social platforms")
        return combined_results
        
    except Exception as e:
        logger.error(f"❌ HARDCODED EXECUTION: Critical failure in parallel execution: {e}")
        raise


def format_tool_results_for_llm(results: Dict[str, Any]) -> str:
    """
    Format the hardcoded tool execution results for LLM analysis.
    
    Args:
        results: Combined results from all 3 tools
        
    Returns:
        Formatted string for LLM to analyze
    """
    reddit_data = results.get("reddit", {})
    twitter_data = results.get("twitter", {})
    stocktwits_data = results.get("stocktwits", {})
    
    formatted = f"""
=== SOCIAL MEDIA DATA COLLECTION COMPLETE ===
Ticker: {results.get('ticker')}
Tools Executed: {results.get('tools_executed')}/3
Execution Time: {results.get('execution_time', 0):.2f}s

=== REDDIT DATA ===
Posts Analyzed: {reddit_data.get('posts', 0)}
Sentiment Score: {reddit_data.get('sentiment_score', 'N/A')}
Average Score: {reddit_data.get('avg_score', 0)}
Average Comments: {reddit_data.get('avg_comments', 0)}
Confidence: {reddit_data.get('confidence', 'low')}
Top Subreddits: {', '.join([f"{k}:{v}" for k,v in reddit_data.get('subreddit_breakdown', {}).items()][:3])}

=== TWITTER DATA ===
Mentions: {twitter_data.get('mentions', 0)}
Sentiment: {twitter_data.get('sentiment', 'neutral')}
Sentiment Score: {twitter_data.get('sentiment_score', 'N/A')}
Trending: {twitter_data.get('trending', False)}
Confidence: {twitter_data.get('confidence', 'low')}
{twitter_data.get('message', '')}

=== STOCKTWITS DATA ===
Messages: {stocktwits_data.get('mentions', 0)}
Sentiment: {stocktwits_data.get('sentiment', 'neutral')}
Sentiment Score: {stocktwits_data.get('score', 'N/A')}
Bullish %: {stocktwits_data.get('bullish_percent', 0)}
Bearish %: {stocktwits_data.get('bearish_percent', 0)}
Confidence: {stocktwits_data.get('confidence', 'low')}

=== YOUR TASK ===
Analyze the above social media data from ALL 3 platforms and provide:
1. Overall sentiment score [-1 to +1]
2. Confidence level [Low/Medium/High]
3. Sentiment trend [Rising/Falling/Stable]
4. Top 3 key insights
5. Trading signal [BUY/SELL/HOLD] with rationale
"""
    return formatted


def create_social_media_analyst_hardcoded(llm, toolkit):
    """
    Create a social media analyst with hardcoded parallel tool execution.
    This ensures all 3 tools are ALWAYS called, regardless of LLM decision.
    
    Args:
        llm: Language model for analysis (NOT for tool selection)
        toolkit: Toolkit with social media tools
        
    Returns:
        Analyst function with hardcoded tool execution
    """
    
    async def social_media_analyst_hardcoded(state):
        """Enhanced social media analyst with guaranteed 3-tool execution"""
        
        logger.info(f"🚀 SOCIAL ANALYST (HARDCODED): Starting analysis")
        start_time = time.time()
        
        # Extract state variables
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # STEP 1: Execute all tools in parallel (hardcoded)
        logger.info(f"📊 HARDCODED: Executing ALL 3 social tools for {ticker}")
        tool_results = await execute_all_social_tools(toolkit, ticker, current_date)
        
        # STEP 2: Format results for LLM
        formatted_results = format_tool_results_for_llm(tool_results)
        
        # STEP 3: Create prompt for LLM to ANALYZE (not execute tools)
        system_message = f"""
You are a Social Media Sentiment Analyst for {ticker}.

You have been provided with data from Reddit, Twitter, and StockTwits.
Your task is to ANALYZE this data and provide insights.

DO NOT attempt to call any tools - the data has already been collected.
Focus on analyzing the sentiment patterns and generating trading insights.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", formatted_results)
        ])
        
        # STEP 4: Get LLM analysis of the pre-collected data
        logger.info(f"🤖 HARDCODED: LLM analyzing pre-collected data from 3 tools")
        chain = prompt | llm
        
        result = await chain.ainvoke({})
        
        # Log completion
        total_time = time.time() - start_time
        logger.info(f"✅ SOCIAL ANALYST (HARDCODED): Completed in {total_time:.2f}s")
        logger.info(f"📊 HARDCODED METRICS: 3/3 tools executed, {tool_results['execution_time']:.2f}s tool time")
        
        # Return the analysis
        if hasattr(result, 'content'):
            content = result.content
        else:
            content = str(result)
            
        return {
            "social_messages": state.get("social_messages", []) + [
                HumanMessage(content=f"Social Media Analysis (3 tools executed):\n{content}")
            ]
        }
    
    return social_media_analyst_hardcoded