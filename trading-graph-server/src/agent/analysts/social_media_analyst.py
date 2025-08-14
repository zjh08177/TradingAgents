from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json
import time
import logging
from ..utils.debug_logging import debug_node, log_llm_interaction
from ..utils.connection_retry import safe_llm_invoke
from ..utils.parallel_tools import log_parallel_execution
from ..utils.agent_prompt_enhancer import enhance_agent_prompt
from ..utils.prompt_compressor import get_prompt_compressor, compress_prompt
from ..utils.token_limiter import get_token_limiter

logger = logging.getLogger(__name__)


def create_social_media_analyst(llm, toolkit):
    """
    Create social media analyst with HARDCODED parallel tool execution.
    This ensures all 3 tools (Reddit, Twitter, StockTwits) are ALWAYS called.
    """
    # Import hardcoded version
    from .social_media_analyst_hardcoded import create_social_media_analyst_hardcoded
    return create_social_media_analyst_hardcoded(llm, toolkit)


def create_social_media_analyst_old_version(llm, toolkit):
    """Original LLM-based tool selection version (kept for reference)"""
    @debug_node("Social_Media_Analyst")
    async def social_media_analyst_node(state):
        # Task: Add Execution Timing Logs
        start_time = time.time()
        logger.info(f"⏱️ social_media_analyst START: {time.time()}")
        
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = []
            # SOCIAL MEDIA TOOLS ONLY - News analysis is handled by News Analyst
            logger.info(f"🔍 SOCIAL ANALYST: Checking for available tools...")
            if hasattr(toolkit, 'get_reddit_stock_info'):
                tools.append(toolkit.get_reddit_stock_info)
                logger.info(f"✅ SOCIAL ANALYST: Added get_reddit_stock_info")
            else:
                logger.warning(f"⚠️ SOCIAL ANALYST: get_reddit_stock_info NOT AVAILABLE")
            if hasattr(toolkit, 'get_stocktwits_sentiment'):
                tools.append(toolkit.get_stocktwits_sentiment)
                logger.info(f"✅ SOCIAL ANALYST: Added get_stocktwits_sentiment")
            else:
                logger.warning(f"⚠️ SOCIAL ANALYST: get_stocktwits_sentiment NOT AVAILABLE")
            if hasattr(toolkit, 'get_twitter_mentions'):
                tools.append(toolkit.get_twitter_mentions)
                logger.info(f"✅ SOCIAL ANALYST: Added get_twitter_mentions")
            else:
                logger.warning(f"⚠️ SOCIAL ANALYST: get_twitter_mentions NOT AVAILABLE")
            
            # IMPORTANT: Do NOT add news tools to social analyst
            # News analysis is handled by the News Analyst
            if hasattr(toolkit, 'get_stock_news_openai'):
                logger.warning(f"🚫 SOCIAL ANALYST: Excluding get_stock_news_openai (handled by News Analyst)")
            logger.info(f"📊 SOCIAL ANALYST: Total tools available: {len(tools)}")
        else:
            tools = []
            # Even in offline mode, try to get social tools if available
            if hasattr(toolkit, 'get_stocktwits_sentiment'):
                tools.append(toolkit.get_stocktwits_sentiment)
            if hasattr(toolkit, 'get_twitter_mentions'):
                tools.append(toolkit.get_twitter_mentions)

        system_message = """
You are a Social Media Sentiment Analyst for {ticker}.

YOUR ROLE: Analyze social media discussions (Reddit, Twitter, StockTwits) to gauge retail investor sentiment.
NOT YOUR ROLE: News analysis (handled by News Analyst).

WORKFLOW:
1. Call get_twitter_mentions(ticker="{ticker}") for Twitter sentiment
2. Call get_stocktwits_sentiment(ticker="{ticker}") for StockTwits data
3. Call get_reddit_stock_info(ticker="{ticker}", date="{current_date}") for Reddit discussions
4. Analyze sentiment patterns across all platforms
5. Generate trading insights from combined social signals

OUTPUT REQUIREMENTS:
SENTIMENT SCORE: [-1 to +1] where -1=bearish, 0=neutral, +1=bullish
CONFIDENCE: [Low/Medium/High] based on data volume and consensus
TREND: [Rising/Falling/Stable] sentiment momentum
KEY INSIGHTS: Top 3 findings from social discussions
SIGNAL: [BUY/SELL/HOLD] with brief rationale

Focus on social sentiment only. Do not analyze news articles.
Available tools: {tool_names}
        """

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The current company we want to analyze is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Format system message with tool names and ticker
        tool_names_str = ", ".join([tool.name for tool in tools])
        system_message = system_message.format(ticker=ticker, tool_names=tool_names_str, current_date=current_date)
        
        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=tool_names_str)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        # Use the correct message channel for social media analyst
        messages = state.get("social_messages", [])
        
        # CRITICAL FIX: Validate message sequence for OpenAI API compliance
        from ..utils.message_validator import clean_messages_for_llm
        messages = clean_messages_for_llm(messages)
        
        # TASK 4.2: Add LLM interaction logging
        prompt_text = f"System: {system_message}\nUser: {current_date}, {ticker}"
        llm_start = time.time()
        # PT1: Log start of LLM invocation for parallel execution visibility
        logger.info(f"⚡ SOCIAL_ANALYST: Starting LLM invocation")
        result = await safe_llm_invoke(chain, messages)
        llm_time = time.time() - llm_start
        logger.info(f"⚡ SOCIAL_ANALYST: LLM invocation completed in {llm_time:.2f}s")
        
        log_llm_interaction(
            model="social_analyst_llm",
            prompt_length=len(prompt_text),
            response_length=len(str(result.content)) if hasattr(result, 'content') else 0,
            execution_time=llm_time
        )

        # TASK 3.1: Single-pass execution - generate report directly from LLM response
        tool_message_count = sum(1 for msg in messages if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool')
        
        # CRITICAL FIX: ENFORCE MANDATORY TOOL USAGE
        tool_calls = getattr(result, 'tool_calls', [])
        # Handle mock objects in testing
        try:
            tool_calls_count = len(tool_calls)
        except TypeError:
            # Mock object - assume no tool calls for testing
            tool_calls_count = 0
            tool_calls = []
        
        if tool_calls_count == 0:
            # No tool calls in current response - THIS IS A PROBLEM!
            if tool_message_count > 0:
                # Tools were executed previously, this should be the final report
                report = result.content
                logger.info(f"📊 SOCIAL_ANALYST: Generated final report after tool execution ({len(report)} chars)")
            else:
                # CRITICAL ERROR: LLM failed to call tools - force error message
                logger.error(f"❌ SOCIAL_ANALYST: NO TOOLS CALLED - Report will be marked as failed")
                report = f"⚠️ Social sentiment analysis for {ticker} completed without live social media data. Please check social media tool availability."
                logger.warning(f"🚨 SOCIAL_ANALYST: Completed WITHOUT tool calls!")
            
            # Apply token limits
            report = get_token_limiter().truncate_response(report, "Social Media Analyst")
        else:
            # Current response contains tool calls - tools need to be executed first
            logger.info(f"⚡ SOCIAL_ANALYST: LLM requested {tool_calls_count} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in tool_calls]
            logger.info(f"⚡ SOCIAL_ANALYST: Tools requested: {tool_names}")
            report = ""  # No report yet, tools need to be executed first

        # Return the state update
        updated_messages = messages + [result]
        
        # Task: Add Execution Timing Logs
        duration = time.time() - start_time
        logger.info(f"⏱️ social_media_analyst END: {time.time()} (duration: {duration:.2f}s)")
        
        return {
            "social_messages": updated_messages,
            "sentiment_report": report,
            "sender": "Social Media Analyst"
        }

    return social_media_analyst_node
