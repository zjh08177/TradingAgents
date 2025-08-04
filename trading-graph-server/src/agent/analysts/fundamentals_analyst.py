from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json
import logging
import time
from ..utils.debug_logging import debug_node, log_llm_interaction
from ..utils.tool_retry import execute_tool_with_fallback
from ..utils.connection_retry import safe_llm_invoke
from ..utils.parallel_tools import log_parallel_execution
from ..utils.agent_prompt_enhancer import enhance_agent_prompt
from ..utils.prompt_compressor import get_prompt_compressor, compress_prompt
from ..utils.token_limiter import get_token_limiter

logger = logging.getLogger(__name__)


def create_fundamentals_analyst(llm, toolkit):
    @debug_node("Fundamentals_Analyst")
    async def fundamentals_analyst_node(state):
        # Task: Add Execution Timing Logs
        start_time = time.time()
        logger.info(f"⏱️ fundamentals_analyst START: {time.time()}")
        
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_fundamentals_openai]
        else:
            tools = [
                toolkit.get_finnhub_company_insider_sentiment,
                toolkit.get_finnhub_company_insider_transactions,
                toolkit.get_simfin_balance_sheet,
                toolkit.get_simfin_cashflow,
                toolkit.get_simfin_income_stmt,
            ]

        # TASK 0.1.4 & 6.2: Token-optimized system message with MANDATORY tool usage
        system_message = (
            """Expert fundamentals analyst: financial statements & valuation.

MANDATORY: Use tools→get real financial data before analysis.
Tools: {tool_names}

Workflow: 1)Call tools 2)Get data 3)Analyze 4)Report

After getting real financial data from tools, provide analysis:
1. Health Grade: A-F with key metrics (ROE, ROA, D/E)
2. Valuation: P/E, P/B, EV/EBITDA vs industry
3. Trading Signals: BUY/SELL/HOLD based on fundamentals
4. Risk Assessment: Financial & operational risks

Focus on actionable investment insights from current financial data.
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
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
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

        # Use the correct message channel for fundamentals analyst
        messages = state.get("fundamentals_messages", [])
        
        # CRITICAL FIX: Validate message sequence for OpenAI API compliance
        from ..utils.message_validator import clean_messages_for_llm
        messages = clean_messages_for_llm(messages)
        
        # TASK 4.2: Add LLM interaction logging
        # TASK 6.2: Enhanced LLM interaction tracking with token optimization
        from ..utils.token_optimizer import get_token_optimizer, track_llm_usage
        
        # CRITICAL FIX: Use async tokenizer initialization to prevent blocking calls
        optimizer = get_token_optimizer()
        prompt_text = f"System: {system_message}\nUser: {current_date}, {ticker}"
        
        # Use async-safe token counting to prevent os.getcwd() blocking calls
        try:
            prompt_tokens = await asyncio.to_thread(optimizer.count_tokens, prompt_text)
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using fallback")
            prompt_tokens = len(prompt_text) // 4  # Rough estimate fallback
        
        llm_start = time.time()
        # PT1: Log start of LLM invocation for parallel execution visibility
        logger.info(f"⚡ FUNDAMENTALS_ANALYST: Starting LLM invocation")
        result = await safe_llm_invoke(chain, messages)
        llm_time = time.time() - llm_start
        logger.info(f"⚡ FUNDAMENTALS_ANALYST: LLM invocation completed in {llm_time:.2f}s")
        
        # Use async-safe token counting for completion
        try:
            completion_tokens = await asyncio.to_thread(optimizer.count_tokens, result.content) if hasattr(result, 'content') else 0
        except Exception as e:
            logger.warning(f"Completion token counting failed: {e}, using fallback")
            completion_tokens = len(result.content) // 4 if hasattr(result, 'content') else 0
        
        # Track token usage for optimization analysis
        track_llm_usage(
            analyst_type="fundamentals",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            execution_time=llm_time
        )
        
        log_llm_interaction(
            model="fundamentals_analyst_llm",
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
                logger.info(f"📊 FUNDAMENTALS_ANALYST: Generated final report after tool execution ({len(report)} chars)")
            else:
                # CRITICAL ERROR: LLM failed to call tools - force error message
                logger.error(f"❌ FUNDAMENTALS_ANALYST: NO TOOLS CALLED - Report will be marked as failed")
                report = f"⚠️ WARNING: Fundamental analysis conducted without current financial data for {ticker}. Tool execution failed."
                logger.warning(f"🚨 FUNDAMENTALS_ANALYST: Completed WITHOUT tool calls!")
            
            # Apply token limits
            from ..utils.token_limiter import get_token_limiter
            report = get_token_limiter().truncate_response(report, "Fundamentals Analyst")
        else:
            # Current response contains tool calls - tools need to be executed first
            logger.info(f"⚡ FUNDAMENTALS_ANALYST: LLM requested {len(result.tool_calls)} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"⚡ FUNDAMENTALS_ANALYST: Tools requested: {tool_names}")
            report = ""  # No report yet, tools need to be executed first

        # Return the state update
        updated_messages = messages + [result]
        
        # Task: Add Execution Timing Logs
        duration = time.time() - start_time
        logger.info(f"⏱️ fundamentals_analyst END: {time.time()} (duration: {duration:.2f}s)")
        
        return {
            "fundamentals_messages": updated_messages,
            "fundamentals_report": report,
            "sender": "Fundamentals Analyst"
        }

    return fundamentals_analyst_node
