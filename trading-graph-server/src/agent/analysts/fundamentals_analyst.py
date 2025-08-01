from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json
import logging
import time
from agent.utils.debug_logging import debug_node, log_llm_interaction
from agent.utils.tool_retry import execute_tool_with_fallback
from agent.utils.connection_retry import safe_llm_invoke
from agent.utils.parallel_tools import log_parallel_execution
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt
from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt
from agent.utils.token_limiter import get_token_limiter

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
            """Expert fundamentals analyst: financial statements, valuation, health assessment.

MANDATORY: Use tools to retrieve actual financial data.
Analysis without real data is prohibited.

Required tools:
1. get_fundamentals_openai (if online) - Primary fundamentals source
OR (if offline):
1. get_finnhub_company_insider_sentiment - Insider sentiment data
2. get_finnhub_company_insider_transactions - Insider trading data
3. get_simfin_balance_sheet - Balance sheet data
4. get_simfin_cashflow - Cash flow data
5. get_simfin_income_stmt - Income statement data

WORKFLOW:
1. Call fundamentals tools (parallel execution enabled for offline tools)
2. Wait for data responses with actual financial metrics
3. Analyze actual financial data from tools
4. Cite data sources and reporting periods
5. NEVER invent financial numbers or ratios

After getting real financial data from tools, provide analysis using structure:

## 💰 Fundamentals Report

### 1. Health Overview
- **Grade**: A-F with rationale
- **Strengths**: Top 3 advantages
- **Concerns**: Critical weaknesses
- **Peer Rank**: Industry quartile

### 2. Key Metrics
| Category | Current | Industry | Trend | Score |
|----------|---------|----------|-------|-------|
| Profitability | [ROE/ROA] | [bench] | [↑↓→] | [1-10] |
| Liquidity | [Current] | [bench] | [↑↓→] | [1-10] |
| Leverage | [D/E] | [bench] | [↑↓→] | [1-10] |
| Efficiency | [Turnover] | [bench] | [↑↓→] | [1-10] |

### 3. Income Statement
- **Revenue**: YoY/QoQ trends
- **Margins**: Gross, operating, net evolution
- **Earnings**: Quality and recurring components
- **Costs**: Fixed vs variable efficiency

### 4. Balance Sheet
- **Assets**: Current vs long-term composition
- **Debt**: Maturity, coverage, covenants
- **Working Capital**: Conversion cycle metrics
- **Equity**: Book value trends

### 5. Cash Flow
- **Operating**: Cash generation quality
- **Free CF**: Available after capex
- **Capital**: Allocation strategy
- **Position**: Liquidity runway

### 6. Valuation
| Method | Current | Target | Upside | Confidence |
|--------|---------|--------|--------|------------|
| P/E | [val] | [target] | [±%] | [H/M/L] |
| P/B | [val] | [target] | [±%] | [H/M/L] |
| EV/EBITDA | [val] | [target] | [±%] | [H/M/L] |
| DCF | [val] | [target] | [±%] | [H/M/L] |

### 7. Growth & Risks
- **Drivers**: Revenue catalysts
- **Risks**: Financial, operational, market
- **Insider**: Recent transactions

### 8. Investment Thesis
- **Bull/Bear/Base**: Cases with targets
- **Catalysts**: Key events timeline

Include specific numbers and ratios.
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

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        # Use the correct message channel for fundamentals analyst
        messages = state.get("fundamentals_messages", [])
        
        # CRITICAL FIX: Validate message sequence for OpenAI API compliance
        from agent.utils.message_validator import clean_messages_for_llm
        messages = clean_messages_for_llm(messages)
        
        # TASK 4.2: Add LLM interaction logging
        # TASK 6.2: Enhanced LLM interaction tracking with token optimization
        from agent.utils.token_optimizer import get_token_optimizer, track_llm_usage
        
        optimizer = get_token_optimizer()
        prompt_text = f"System: {system_message}\nUser: {current_date}, {ticker}"
        prompt_tokens = optimizer.count_tokens(prompt_text)
        
        llm_start = time.time()
        # PT1: Log start of LLM invocation for parallel execution visibility
        logger.info(f"⚡ FUNDAMENTALS_ANALYST: Starting LLM invocation")
        result = await safe_llm_invoke(chain, messages)
        llm_time = time.time() - llm_start
        logger.info(f"⚡ FUNDAMENTALS_ANALYST: LLM invocation completed in {llm_time:.2f}s")
        
        completion_tokens = optimizer.count_tokens(result.content) if hasattr(result, 'content') else 0
        
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
        
        # The LLM response now contains the complete analysis (single-pass)
        if len(result.tool_calls) == 0:
            # Direct comprehensive response from LLM - use as final report
            report = result.content
        else:
            # PT1: LLM wants to make tool calls - log for parallel visibility
            logger.info(f"⚡ FUNDAMENTALS_ANALYST: LLM requested {len(result.tool_calls)} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"⚡ FUNDAMENTALS_ANALYST: Tools requested: {tool_names}")
            report = ""

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
