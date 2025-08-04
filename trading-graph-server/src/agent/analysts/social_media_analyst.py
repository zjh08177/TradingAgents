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
    @debug_node("Social_Media_Analyst")
    async def social_media_analyst_node(state):
        # Task: Add Execution Timing Logs
        start_time = time.time()
        logger.info(f"⏱️ social_media_analyst START: {time.time()}")
        
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_stock_news_openai,
                # toolkit.get_reddit_stock_info,      # DISABLED: Division by zero error
            ]
            # Add additional tools if available
            if hasattr(toolkit, 'get_stocktwits_sentiment'):
                tools.append(toolkit.get_stocktwits_sentiment)
            if hasattr(toolkit, 'get_twitter_mentions'):
                tools.append(toolkit.get_twitter_mentions)
        else:
            tools = [
                # toolkit.get_reddit_stock_info,    # DISABLED: Division by zero error
            ]
            # Add fallback tool when Reddit is disabled
            if hasattr(toolkit, 'get_stock_news_openai'):
                tools.append(toolkit.get_stock_news_openai)

        system_message = (
            """Expert social media analyst: sentiment & public perception.

MANDATORY: Use tools→get real social data before analysis.
Tools: {tool_names}

Workflow: 1)Call tools 2)Get data 3)Analyze 4)Report

After getting real social sentiment data from tools, provide analysis:
1. Sentiment Score: Quantified sentiment (-100 to +100)
2. Trend Direction: Rising/Falling/Stable momentum
3. Trading Signals: BUY/SELL/HOLD based on sentiment
4. Risk Assessment: Reputation & viral risks

Focus on actionable trading insights from current social data.
            """
        )

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

        # Format system message with tool names first
        tool_names_str = ", ".join([tool.name for tool in tools])
        system_message = system_message.format(tool_names=tool_names_str)
        
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
            response_length=len(result.content) if hasattr(result, 'content') else 0,
            execution_time=llm_time
        )

        # TASK 3.1: Single-pass execution - generate report directly from LLM response
        tool_message_count = sum(1 for msg in messages if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool')
        
        # CRITICAL FIX: ENFORCE MANDATORY TOOL USAGE
        if len(result.tool_calls) == 0:
            # No tool calls in current response - THIS IS A PROBLEM!
            if tool_message_count > 0:
                # Tools were executed previously, this should be the final report
                report = result.content
                logger.info(f"📊 SOCIAL_ANALYST: Generated final report after tool execution ({len(report)} chars)")
            else:
                # CRITICAL ERROR: LLM failed to call tools - force error message
                logger.error(f"❌ SOCIAL_ANALYST: NO TOOLS CALLED - Report will be marked as failed")
                report = f"⚠️ WARNING: Social sentiment analysis conducted without current social data for {ticker}. Tool execution failed."
                logger.warning(f"🚨 SOCIAL_ANALYST: Completed WITHOUT tool calls!")
            
            # Apply token limits
            report = get_token_limiter().truncate_response(report, "Social Media Analyst")
        else:
            # Current response contains tool calls - tools need to be executed first
            logger.info(f"⚡ SOCIAL_ANALYST: LLM requested {len(result.tool_calls)} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
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
