from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json


def create_social_media_analyst(llm, toolkit):
    async def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_stock_news_openai]
        else:
            tools = [
                toolkit.get_reddit_stock_info,
            ]

        system_message = (
            "You are a social media and company specific news researcher/analyst tasked with analyzing social media posts, recent company news, and public sentiment for a specific company over the past week. You will be given a company's name your objective is to write a comprehensive long report detailing your analysis, insights, and implications for traders and investors on this company's current state after looking at social media and what people are saying about that company, analyzing sentiment data of what people feel each day about the company, and looking at recent company news. Try to look at all sources possible from social media to sentiment to news. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."
            + """ Make sure to append a Makrdown table at the end of the report to organize key points in the report, organized and easy to read.""",
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

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        # Use the correct message channel for social media analyst
        messages = state.get("social_messages", [])
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
            summary_prompt = f"""Based on the tool results and data gathered, provide a comprehensive social media sentiment analysis report for {company_name} on {current_date}.
            
Include:
- Social media sentiment trends
- Key themes and discussions
- Public perception analysis
- Sentiment-based trading implications
- Risk factors from social sentiment

Make this a detailed, actionable report for traders."""

            # Generate summary
            summary_result = await llm.ainvoke([{"role": "user", "content": summary_prompt}])
            report = summary_result.content

        # Return the state update
        updated_messages = messages + [result]
        return {
            "social_messages": updated_messages,
            "sentiment_report": report,
            "sender": "Social Media Analyst"
        }

    return social_media_analyst_node
