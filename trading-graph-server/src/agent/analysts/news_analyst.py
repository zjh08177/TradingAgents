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


def create_news_analyst(llm, toolkit):
    @debug_node("News_Analyst")
    async def news_analyst_node(state):
        # Task: Add Execution Timing Logs
        start_time = time.time()
        logger.info(f"⏱️ news_analyst START: {time.time()}")
        
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_global_news_openai, toolkit.get_google_news]
        else:
            tools = [
                toolkit.get_finnhub_news,
                toolkit.get_reddit_news,
                toolkit.get_google_news,
            ]

        system_message = (
            """Expert news analyst: financial intelligence & market impact.

MANDATORY: Use tools→get real news data before analysis.
Tools: {tool_names}

Workflow: 1)Call tools 2)Get data 3)Analyze 4)Report

After getting real news data from tools, provide analysis:
1. News Summary: Key headlines & market impact
2. Market Direction: BUY/SELL/HOLD signals from news
3. Risk Assessment: Headline risks & catalysts
4. Trading Strategy: Entry/exit points based on news

Focus on actionable trading insights from current news data.
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
                    "For your reference, the current date is {current_date}. We are looking at the company {ticker}",
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
        
        # Use the correct message channel for news analyst
        messages = state.get("news_messages", [])
        
        # CRITICAL FIX: Validate message sequence for OpenAI API compliance
        from ..utils.message_validator import clean_messages_for_llm
        messages = clean_messages_for_llm(messages)
        
        # TASK 4.2: Add LLM interaction logging
        prompt_text = f"System: {system_message}\nUser: {current_date}, {ticker}"
        llm_start = time.time()
        # PT1: Log start of LLM invocation for parallel execution visibility
        logger.info(f"⚡ NEWS_ANALYST: Starting LLM invocation")
        result = await safe_llm_invoke(chain, messages)
        llm_time = time.time() - llm_start
        logger.info(f"⚡ NEWS_ANALYST: LLM invocation completed in {llm_time:.2f}s")
        
        log_llm_interaction(
            model="news_analyst_llm",
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
                logger.info(f"📊 NEWS_ANALYST: Generated final report after tool execution ({len(report)} chars)")
            else:
                # CRITICAL ERROR: LLM failed to call tools - force error message
                logger.error(f"❌ NEWS_ANALYST: NO TOOLS CALLED - Report will be marked as failed")
                report = f"⚠️ WARNING: News analysis conducted without current news data for {ticker}. Tool execution failed."
                logger.warning(f"🚨 NEWS_ANALYST: Completed WITHOUT tool calls!")
            
            # CRITICAL: Apply news filtering BEFORE token limiting to prevent massive prompt tokens
            from ..utils.news_filter import filter_news_for_llm
            logger.info(f"📰 NEWS_ANALYST: Applying news filtering to prevent token explosion")
            report = filter_news_for_llm(report, max_articles=15)
            
            # Apply token limits after filtering
            from ..utils.token_limiter import get_token_limiter
            report = get_token_limiter().truncate_response(report, "News Analyst")
        else:
            # Current response contains tool calls - tools need to be executed first
            logger.info(f"⚡ NEWS_ANALYST: LLM requested {len(result.tool_calls)} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"⚡ NEWS_ANALYST: Tools requested: {tool_names}")
            report = ""  # No report yet, tools need to be executed first

        # Return the state update
        updated_messages = messages + [result]
        
        # Task: Add Execution Timing Logs
        duration = time.time() - start_time
        logger.info(f"⏱️ news_analyst END: {time.time()} (duration: {duration:.2f}s)")
        
        return {
            "news_messages": updated_messages,
            "news_report": report,
            "sender": "News Analyst"
        }

    return news_analyst_node
