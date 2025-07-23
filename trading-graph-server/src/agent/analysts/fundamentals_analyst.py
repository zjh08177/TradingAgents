from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


def create_fundamentals_analyst(llm, toolkit):
    async def fundamentals_analyst_node(state):
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

        system_message = (
            "You are a researcher tasked with analyzing fundamental information over the past week about a company. Please write a comprehensive report of the company's fundamental information such as financial documents, company profile, basic company financials, company financial history, insider sentiment and insider transactions to gain a full view of the company's fundamental information to inform traders. Make sure to include as much detail as possible. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."
            + " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read.",
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
        result = await chain.ainvoke(messages)

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
            summary_prompt = f"""Based on the tool results and data gathered, provide a comprehensive fundamentals analysis report for {company_name} on {current_date}.
            
Include:
- Financial statement analysis
- Company fundamentals assessment
- Valuation analysis
- Growth prospects evaluation
- Fundamental-based trading recommendations

Make this a detailed, actionable report for traders."""

            # Generate summary
            summary_result = await llm.ainvoke([{"role": "user", "content": summary_prompt}])
            report = summary_result.content

        # Return the state update
        updated_messages = messages + [result]
        return {
            "fundamentals_messages": updated_messages,
            "fundamentals_report": report,
            "sender": "Fundamentals Analyst"
        }

    return fundamentals_analyst_node
