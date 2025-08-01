from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json
import functools
import time
import logging
from agent.utils.debug_logging import debug_node, log_llm_interaction
from agent.utils.token_limiter import get_token_limiter
from agent.utils.connection_retry import safe_llm_invoke
from agent.utils.parallel_tools import log_parallel_execution
from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt

logger = logging.getLogger(__name__)


def create_market_analyst(llm, toolkit):
    @debug_node("Market_Analyst") 
    async def market_analyst_node(state):
        # Task: Add Execution Timing Logs
        start_time = time.time()
        logger.info(f"⏱️ market_analyst START: {time.time()}")
        
        current_date = state.get("trade_date", "")
        ticker = state.get("company_of_interest", "")
        company_name = state.get("company_of_interest", "")

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_YFin_data_online,
                toolkit.get_stockstats_indicators_report_online,
            ]
            # Add additional tools if available
            if hasattr(toolkit, 'get_volume_analysis'):
                tools.append(toolkit.get_volume_analysis)
            if hasattr(toolkit, 'get_support_resistance'):
                tools.append(toolkit.get_support_resistance)
        else:
            tools = [
                toolkit.get_YFin_data,
                toolkit.get_stockstats_indicators_report,
            ]

        # Check for preprocessed prompt (Phase 3.2 optimization)
        from agent.utils.prompt_injection import get_preprocessed_prompt
        preprocessed = get_preprocessed_prompt("market")
        
        if preprocessed:
            # Use preprocessed prompt - already compressed and enhanced
            system_message = preprocessed
            logger.info("💉 Using pre-processed prompt for market analyst")
        else:
            # Create compressed system message
            base_system_message = """Expert market analyst: TA & trading signals.

MANDATORY: Use tools→get real data before analysis.
Tools: get_YFin_data, get_stockstats_indicators_report

Workflow: 1)Call tools 2)Get data 3)Analyze 4)Report

Analyze (max 8): MA(50,200), EMA(10), MACD, RSI, BB, ATR, VWMA

Output structure:
1. Summary: Position|Signal|BUY/SELL/HOLD|Confidence|Target
2. Indicators: Trend(MA)|Momentum(MACD,RSI)|Volatility(BB,ATR)|Volume(VWMA)
3. Metrics table: Indicator|Value|Signal(↑↓→)|Weight(H/M/L)
4. Strategy: Entry|SL|TP|Size
5. Risk: Technical|Market|Volatility
6. Rec: Decision|Confidence(1-10)|1w/1m outlook"""

            # Compress the system message
            compressor = get_prompt_compressor()
            compressed_result = compressor.compress_prompt(base_system_message)
            system_message = compressed_result.compressed
            
            # Add word limit enforcement
            system_message = enhance_agent_prompt(system_message, "market_analyst")
            
            logger.info(f"📊 Market Analyst prompt compression: {compressed_result.original_tokens} → {compressed_result.compressed_tokens} tokens ({compressed_result.reduction_percentage:.1f}% reduction)")

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
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        # Use the correct message channel for market analyst
        messages = state.get("market_messages", [])
        
        # TASK C4: Token limits temporarily disabled for debugging
        messages = get_token_limiter().check_and_enforce_limit(messages, "Market Analyst")
        
        # CRITICAL FIX: Validate message sequence AFTER token limiting for OpenAI API compliance
        from agent.utils.message_validator import clean_messages_for_llm
        messages = clean_messages_for_llm(messages)

        # TASK 6.2: Enhanced LLM interaction tracking with token optimization
        from agent.utils.token_optimizer import get_token_optimizer, track_llm_usage
        
        optimizer = get_token_optimizer()
        prompt_text = f"System: {system_message}\nUser: Current date: {current_date}, Company: {ticker}"
        prompt_tokens = optimizer.count_tokens(prompt_text)
        
        llm_start = time.time()
        # PT1: Log start of LLM invocation for parallel execution visibility
        logger.info(f"⚡ MARKET_ANALYST: Starting LLM invocation")
        result = await safe_llm_invoke(chain, messages)
        llm_time = time.time() - llm_start
        logger.info(f"⚡ MARKET_ANALYST: LLM invocation completed in {llm_time:.2f}s")
        
        completion_tokens = optimizer.count_tokens(result.content) if hasattr(result, 'content') else 0
        
        # Track token usage for optimization analysis
        track_llm_usage(
            analyst_type="market",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            execution_time=llm_time
        )
        
        log_llm_interaction(
            model="market_analyst_llm",
            prompt_length=len(prompt_text),
            response_length=len(result.content) if hasattr(result, 'content') else 0,
            execution_time=llm_time
        )

        # TASK 3.1: Single-pass execution - generate report directly from LLM response
        tool_message_count = sum(1 for msg in messages if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool')
        
        # The LLM response now contains the complete analysis (single-pass)
        if len(result.tool_calls) == 0:
            # Direct comprehensive response from LLM - use as final report
            report = result.content
            # TASK C4: Enforce token limits on response
            report = get_token_limiter().truncate_response(report, "Market Analyst")
        else:
            # PT1: LLM wants to make tool calls - log for parallel visibility
            logger.info(f"⚡ MARKET_ANALYST: LLM requested {len(result.tool_calls)} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"⚡ MARKET_ANALYST: Tools requested: {tool_names}")
            report = ""

        # Return updated messages and report
        updated_messages = messages + [result]
        
        # Task: Add Execution Timing Logs
        duration = time.time() - start_time
        logger.info(f"⏱️ market_analyst END: {time.time()} (duration: {duration:.2f}s)")
        
        return {
            "market_messages": updated_messages,
            "market_report": report,
            "sender": "Market Analyst"
        }

    return market_analyst_node
