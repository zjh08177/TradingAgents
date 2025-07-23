from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json
import functools
import time
from agent.utils.debug_logging import debug_node, log_llm_interaction


def create_market_analyst(llm, toolkit):
    @debug_node("Market_Analyst") 
    async def market_analyst_node(state):
        current_date = state.get("trade_date", "")
        ticker = state.get("company_of_interest", "")
        company_name = state.get("company_of_interest", "")

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_YFin_data_online,
                toolkit.get_stockstats_indicators_report_online,
            ]
        else:
            tools = [
                toolkit.get_YFin_data,
                toolkit.get_stockstats_indicators_report,
            ]

        system_message = (
            """You are a trading assistant tasked with analyzing financial markets. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. Categories and each category's indicators are:

Moving Averages:
- close_50_sma: 50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.
- close_200_sma: 200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.
- close_10_ema: 10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.

MACD Related:
- macd: MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.
- macds: MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.
- macdh: MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.

Momentum Indicators:
- rsi: RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.

Volatility Indicators:
- boll: Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.
- boll_ub: Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.
- boll_lb: Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.
- atr: ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.

Volume-Based Indicators:
- vwma: VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.

- Select indicators, gather market data, and provide comprehensive analysis.

IMPORTANT: After you have gathered all the necessary data through tool calls, you must provide a comprehensive final analysis report. Do not just make tool calls without providing a final written analysis.
            """ + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
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

        # Use the correct message channel for market analyst
        messages = state.get("market_messages", [])

        # Log LLM interaction
        prompt_text = f"System: {system_message}\nUser: Current date: {current_date}, Company: {ticker}"
        llm_start = time.time()
        result = await chain.ainvoke(messages)
        llm_time = time.time() - llm_start
        
        log_llm_interaction(
            model="market_analyst_llm",
            prompt_length=len(prompt_text),
            response_length=len(result.content) if hasattr(result, 'content') else 0,
            execution_time=llm_time
        )

        # Generate report when no tool calls are present OR when we have enough tool data
        tool_message_count = sum(1 for msg in messages if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool')
        
        report = ""
        if len(result.tool_calls) == 0:
            # Direct response from LLM - use as report
            report = result.content
        else:
            # LLM wants to make tool calls - wait for tool execution
            report = ""  # Will be generated after tool execution
        
        # ALWAYS generate a summary report if we have tool results available
        if tool_message_count >= 1 and not result.tool_calls:
            # Create a summary prompt to generate final report
            summary_prompt = f"""Based on the tool results and data gathered, provide a comprehensive market analysis report for {company_name} on {current_date}. 
            
Include:
- Technical analysis findings
- Key indicators and their implications
- Market trends and patterns
- Trading recommendations
- Risk assessment

Make this a detailed, actionable report for traders."""

            # Create a separate LLM call for summary
            summary_chain = llm
            
            # Log the summary generation
            start_time = time.time()
            summary_result = await summary_chain.ainvoke([{"role": "user", "content": summary_prompt}])
            summary_time = time.time() - start_time
            
            log_llm_interaction(
                model="market_summary_llm",
                prompt_length=len(summary_prompt),
                response_length=len(summary_result.content) if hasattr(summary_result, 'content') else 0,
                execution_time=summary_time
            )
            
            report = summary_result.content

        # Return updated messages and report
        updated_messages = messages + [result]
        return {
            "market_messages": updated_messages,
            "market_report": report,
            "sender": "Market Analyst"
        }

    return market_analyst_node
