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

async def execute_single_tool_with_retry(tool_func, tool_name: str, *args, **kwargs) -> Dict[str, Any]:
    """
    Execute a single social media tool with enhanced retry and fallback.
    
    Args:
        tool_func: The tool function to execute
        tool_name: Name of the tool for logging
        *args, **kwargs: Arguments for the tool function
        
    Returns:
        Tool result or fallback data
    """
    import asyncio
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    
    # Enhanced retry decorator with exponential backoff
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError, OSError)),
        reraise=True
    )
    async def execute_with_timeout():
        """Execute tool with timeout protection."""
        try:
            # Add timeout to prevent hanging I/O operations
            return await asyncio.wait_for(tool_func(*args, **kwargs), timeout=30.0)
        except asyncio.TimeoutError:
            logger.error(f"❌ {tool_name} TIMEOUT: Operation timed out after 30 seconds")
            raise
        except (ConnectionError, OSError) as e:
            logger.error(f"❌ {tool_name} NETWORK ERROR: {e}")
            raise
    
    try:
        logger.info(f"🔄 {tool_name}: Starting execution with retry protection")
        result = await execute_with_timeout()
        logger.info(f"✅ {tool_name}: Successfully executed")
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"❌ {tool_name} FINAL TIMEOUT: All retry attempts timed out")
        return {
            "error": "Network timeout after multiple retries",
            "error_type": "timeout_error",
            "fallback_used": True,
            "posts" if tool_name == "Reddit" else "mentions": 0,
            "sentiment_score" if tool_name != "StockTwits" else "score": 0.5,
            "confidence": "low"
        }
        
    except (ConnectionError, OSError) as e:
        logger.error(f"❌ {tool_name} NETWORK FAILURE: Network error after retries - {e}")
        return {
            "error": f"Network connection failed: {str(e)}",
            "error_type": "network_error", 
            "fallback_used": True,
            "posts" if tool_name == "Reddit" else "mentions": 0,
            "sentiment_score" if tool_name != "StockTwits" else "score": 0.5,
            "confidence": "low"
        }
        
    except Exception as e:
        logger.error(f"❌ {tool_name} UNEXPECTED ERROR: {type(e).__name__} - {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unexpected_error",
            "fallback_used": True,
            "posts" if tool_name == "Reddit" else "mentions": 0,
            "sentiment_score" if tool_name != "StockTwits" else "score": 0.5,
            "confidence": "low"
        }


async def execute_all_social_tools(toolkit, ticker: str, current_date: str) -> Dict[str, Any]:
    """
    Enhanced parallel execution of all 3 social media tools with retry and fallback.
    Now includes timeout protection, retry mechanisms, and detailed error handling.
    
    Args:
        toolkit: The analyst toolkit with social media tools
        ticker: Stock ticker symbol
        current_date: Current date for analysis
        
    Returns:
        Combined results from all 3 tools with enhanced error handling
    """
    # 🚨 RUNTIME VERIFICATION: Confirm hardcoded version is running
    logger.critical("🔥🔥🔥 RUNTIME VERIFICATION: social_media_analyst_hardcoded.py VERSION ACTIVE 🔥🔥🔥")
    logger.critical(f"🔥 TOKEN REDUCTION ENABLED: MAX_SOCIAL_TOKENS=3000 limit is ACTIVE")
    logger.critical(f"🔥 Code version timestamp: 2025-01-14 - Hardcoded with token limits")
    
    logger.info(f"⚡ ENHANCED EXECUTION: Starting parallel execution of ALL 3 social tools for {ticker}")
    
    # Import the tool functions
    from ..dataflows.interface_new_tools import (
        get_reddit_stock_info,
        get_twitter_mentions,
        get_stocktwits_sentiment
    )
    
    # Track execution time
    start_time = time.time()
    
    try:
        # Execute all 3 tools in parallel with enhanced error handling
        logger.info(f"🚀 ENHANCED EXECUTION: Starting parallel execution with timeout and retry protection")
        
        reddit_task = execute_single_tool_with_retry(
            get_reddit_stock_info, "Reddit", ticker, current_date
        )
        twitter_task = execute_single_tool_with_retry(
            get_twitter_mentions, "Twitter", ticker
        )
        stocktwits_task = execute_single_tool_with_retry(
            get_stocktwits_sentiment, "StockTwits", ticker
        )
        
        # Wait for all tasks to complete
        reddit_result, twitter_result, stocktwits_result = await asyncio.gather(
            reddit_task, twitter_task, stocktwits_task,
            return_exceptions=False  # All tools now handle their own exceptions
        )
        
        # Log execution results with success/failure tracking
        execution_time = time.time() - start_time
        
        # Count successful vs failed executions
        successes = sum([
            1 for result in [reddit_result, twitter_result, stocktwits_result]
            if not result.get('error')
        ])
        failures = 3 - successes
        
        logger.info(f"📊 ENHANCED EXECUTION: Completed in {execution_time:.2f}s")
        logger.info(f"✅ ENHANCED EXECUTION: {successes}/3 tools successful, {failures}/3 with fallbacks")
        
        # Log individual tool results
        if not reddit_result.get('error'):
            logger.info(f"✅ Reddit: {reddit_result.get('posts', 0)} posts found")
        else:
            logger.warning(f"⚠️ Reddit: Using fallback data - {reddit_result.get('error')}")
            
        if not twitter_result.get('error'):
            logger.info(f"✅ Twitter: {twitter_result.get('mentions', 0)} mentions found")
        else:
            logger.warning(f"⚠️ Twitter: Using fallback data - {twitter_result.get('error')}")
            
        if not stocktwits_result.get('error'):
            logger.info(f"✅ StockTwits: {stocktwits_result.get('mentions', 0)} messages found")
        else:
            logger.warning(f"⚠️ StockTwits: Using fallback data - {stocktwits_result.get('error')}")
        
        # Combine results into structured format with enhanced metadata
        combined_results = {
            "ticker": ticker,
            "execution_time": execution_time,
            "tools_executed": 3,
            "tools_successful": successes,
            "tools_failed": failures,
            "has_real_data": successes > 0,
            "all_fallback": successes == 0,
            "reddit": reddit_result,
            "twitter": twitter_result,
            "stocktwits": stocktwits_result
        }
        
        if successes > 0:
            logger.info(f"✅ ENHANCED EXECUTION: Successfully gathered real data from {successes}/3 social platforms")
        else:
            logger.warning(f"⚠️ ENHANCED EXECUTION: All tools failed - using fallback data for analysis")
        
        return combined_results
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ ENHANCED EXECUTION: Critical system failure in parallel execution: {e}")
        logger.error(f"❌ ENHANCED EXECUTION: Failed after {execution_time:.2f} seconds")
        
        # Return emergency fallback data
        return {
            "ticker": ticker,
            "execution_time": execution_time,
            "tools_executed": 0,
            "tools_successful": 0, 
            "tools_failed": 3,
            "has_real_data": False,
            "all_fallback": True,
            "system_error": str(e),
            "reddit": {"error": "System failure", "posts": 0, "sentiment_score": 0.5, "confidence": "low"},
            "twitter": {"error": "System failure", "mentions": 0, "sentiment_score": 0.5, "confidence": "low"},
            "stocktwits": {"error": "System failure", "mentions": 0, "score": 0.5, "confidence": "low"}
        }


def format_tool_results_for_llm(results: Dict[str, Any]) -> str:
    """
    Format the hardcoded tool execution results for LLM analysis.
    Handles empty responses gracefully - no mock data, clean reporting.
    
    Args:
        results: Combined results from all 3 tools
        
    Returns:
        Formatted string for LLM to analyze
    """
    from ..dataflows.empty_response_handler import is_empty_response, has_real_data
    
    reddit_data = results.get("reddit", {})
    twitter_data = results.get("twitter", {})
    stocktwits_data = results.get("stocktwits", {})
    
    # Count available data sources
    available_sources = []
    if has_real_data(reddit_data):
        available_sources.append("Reddit")
    if has_real_data(twitter_data):
        available_sources.append("Twitter")
    if has_real_data(stocktwits_data):
        available_sources.append("StockTwits")
    
    # Create the report
    formatted = f"""
=== SOCIAL MEDIA DATA COLLECTION COMPLETE ===
Ticker: {results.get('ticker')}
Tools Executed: {results.get('tools_executed')}/3
Execution Time: {results.get('execution_time', 0):.2f}s
Data Sources Available: {len(available_sources)}/3 ({', '.join(available_sources) if available_sources else 'None'})

"""

    # Reddit section
    if has_real_data(reddit_data):
        formatted += f"""=== REDDIT DATA (AVAILABLE) ===
Posts Analyzed: {reddit_data.get('posts', 0)}
Sentiment Score: {reddit_data.get('sentiment_score', 'N/A')}
Average Score: {reddit_data.get('avg_score', 0)}
Average Comments: {reddit_data.get('avg_comments', 0)}
Confidence: {reddit_data.get('confidence', 'low')}
Top Subreddits: {', '.join([f"{k}:{v}" for k,v in reddit_data.get('subreddit_breakdown', {}).items()][:3])}

"""
    else:
        reason = reddit_data.get('reason', 'No data available')
        formatted += f"=== REDDIT DATA (UNAVAILABLE) ===\nStatus: No real data available\nReason: {reason}\n\n"

    # Twitter section  
    if has_real_data(twitter_data):
        formatted += f"""=== TWITTER DATA (AVAILABLE) ===
Mentions: {twitter_data.get('mentions', 0)}
Sentiment: {twitter_data.get('sentiment', 'neutral')}
Sentiment Score: {twitter_data.get('sentiment_score', 'N/A')}
Trending: {twitter_data.get('trending', False)}
Confidence: {twitter_data.get('confidence', 'low')}
Source: {twitter_data.get('source', 'unknown')}

"""
    else:
        reason = twitter_data.get('reason', 'No data available')
        formatted += f"=== TWITTER DATA (UNAVAILABLE) ===\nStatus: No real data available\nReason: {reason}\n\n"

    # StockTwits section
    if has_real_data(stocktwits_data):
        formatted += f"""=== STOCKTWITS DATA (AVAILABLE) ===
Messages: {stocktwits_data.get('mentions', 0)}
Sentiment: {stocktwits_data.get('sentiment', 'neutral')}
Sentiment Score: {stocktwits_data.get('score', 'N/A')}
Bullish %: {stocktwits_data.get('bullish_percent', 0)}
Bearish %: {stocktwits_data.get('bearish_percent', 0)}
Confidence: {stocktwits_data.get('confidence', 'low')}

"""
    else:
        reason = stocktwits_data.get('reason', 'No data available')
        formatted += f"=== STOCKTWITS DATA (UNAVAILABLE) ===\nStatus: No real data available\nReason: {reason}\n\n"

    # Instructions based on available data
    if len(available_sources) == 0:
        formatted += """=== YOUR TASK ===
NO REAL SOCIAL MEDIA DATA IS AVAILABLE for this analysis.

Please respond with:
1. Overall sentiment score: NULL (no data available)
2. Confidence level: None (no social media data)
3. Sentiment trend: Unknown (insufficient data)
4. Key insight: No social media data available for sentiment analysis
5. Trading signal: SKIP (proceed without social sentiment data)

IMPORTANT: Do not fabricate or simulate sentiment data. Report the lack of data transparently.
"""
    else:
        formatted += f"""=== YOUR TASK ===
Analyze the available social media data from {len(available_sources)}/3 platforms and provide:
1. Overall sentiment score [-1 to +1] (based only on available data)
2. Confidence level [Low/Medium/High] (adjusted for limited data sources)
3. Sentiment trend [Rising/Falling/Stable]
4. Top 3 key insights (note which platforms lack data)
5. Trading signal [BUY/SELL/HOLD] with rationale

IMPORTANT: Base analysis only on platforms with real data. Note data limitations in your insights.
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
        
        # CRITICAL: Apply token limiting to prevent massive prompt tokens
        if hasattr(result, 'content'):
            content = result.content
        else:
            content = str(result)
        
        # Apply token-aware truncation to social media analysis
        MAX_SOCIAL_TOKENS = 3000  # ~750 words max for social analysis
        MAX_SOCIAL_CHARS = MAX_SOCIAL_TOKENS * 4  # Rough estimate: 1 token = 4 chars
        
        # 🚨 RUNTIME VERIFICATION: Log truncation behavior
        logger.critical(f"🔥🔥🔥 SOCIAL MEDIA TOKEN LIMIT VERIFICATION 🔥🔥🔥")
        logger.critical(f"🔥 Content length before truncation: {len(content)} chars")
        logger.critical(f"🔥 MAX_SOCIAL_CHARS limit: {MAX_SOCIAL_CHARS}")
        
        if len(content) > MAX_SOCIAL_CHARS:
            logger.critical(f"🔥 TRUNCATING: {len(content)} > {MAX_SOCIAL_CHARS}")
            logger.info(f"📰 SOCIAL ANALYST TOKEN OPTIMIZATION: Truncating from {len(content)} to {MAX_SOCIAL_CHARS} chars")
            # Keep the beginning and end, truncate middle
            truncated_content = (
                content[:MAX_SOCIAL_CHARS//2] + 
                "\n\n[... Analysis truncated for token optimization ...]\n\n" +
                content[-MAX_SOCIAL_CHARS//4:]
            )
            content = truncated_content
            logger.critical(f"✅ Content length after truncation: {len(content)} chars")
        else:
            logger.critical(f"✅ No truncation needed: {len(content)} ≤ {MAX_SOCIAL_CHARS}")
        
        logger.info(f"📰 SOCIAL ANALYST: Final content length: {len(content)} chars (~{len(content)//4} tokens)")
            
        return {
            "social_messages": state.get("social_messages", []) + [
                HumanMessage(content=f"Social Media Analysis (3 tools executed):\n{content}")
            ]
        }
    
    return social_media_analyst_hardcoded