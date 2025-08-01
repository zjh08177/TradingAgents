from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import json
import time
import logging
from agent.utils.debug_logging import debug_node, log_llm_interaction
from agent.utils.connection_retry import safe_llm_invoke
from agent.utils.parallel_tools import log_parallel_execution
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt
from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt
from agent.utils.token_limiter import get_token_limiter

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
            """You are an expert news analyst specializing in financial market intelligence and macroeconomic impact assessment.

CRITICAL REQUIREMENT: You MUST use tools to gather real news data.
Analysis without tool data is NOT acceptable.

Required tools:
1. get_global_news_openai (if online) OR get_finnhub_news - Get market-wide news
2. get_google_news - Get Google news coverage
3. get_reddit_news (if offline) - Get social sentiment from news

WORKFLOW:
1. Call ALL available news tools
2. Wait for responses with actual news data
3. Analyze the actual news data from tools
4. NEVER generate fictional news or analysis without data

TASK 3.2 OPTIMIZED NEWS INTELLIGENCE FRAMEWORK:
After getting real news from tools, provide a comprehensive analysis following this exact structure:

## 📰 Market News Intelligence Report

### 1. Breaking News Impact Assessment
- **Priority Level**: Critical/High/Medium/Low classification
- **Market Relevance Score**: Quantified impact (1-10 scale)
- **Time Horizon**: Immediate/Short-term/Long-term effects
- **Affected Sectors**: Specific industries and correlation strength

### 2. News Catalyst Matrix

| Event Category | Impact Score | Time Frame | Market Direction | Confidence |
|----------------|--------------|------------|------------------|------------|
| Earnings/Guidance | [1-10] | [timeline] | [↑↓→] | [H/M/L] |
| Regulatory News | [1-10] | [timeline] | [↑↓→] | [H/M/L] |
| Economic Data | [1-10] | [timeline] | [↑↓→] | [H/M/L] |
| Company Events | [1-10] | [timeline] | [↑↓→] | [H/M/L] |

### 3. Macroeconomic Context
- **Fed Policy Signals**: Interest rate trajectory and monetary policy shifts
- **Economic Indicators**: GDP, inflation, employment trend analysis
- **Global Factors**: International events affecting domestic markets
- **Currency Implications**: USD strength/weakness impact on operations

### 4. Sector-Specific Analysis
- **Direct Industry Impact**: Company's sector-specific news and trends
- **Supply Chain Effects**: Upstream/downstream disruptions or opportunities
- **Competitive Landscape**: Peer company developments and market share shifts
- **Regulatory Environment**: Policy changes affecting the industry

### 5. News-Driven Trading Strategies
- **Event Trading Opportunities**: Specific price targets based on news catalysts
- **Volatility Expectations**: Expected price movement ranges
- **Options Market Implications**: IV changes and strategic considerations
- **Pairs Trading Ideas**: Relative value opportunities from news divergence

### 6. Risk Monitoring Dashboard
- **Headline Risk Factors**: Potential negative news catalysts
- **Regulatory Risks**: Policy changes that could impact operations
- **Geopolitical Exposure**: International developments affecting business
- **Black Swan Indicators**: Low-probability, high-impact event monitoring

### 7. Forward-Looking Intelligence
- **Upcoming Catalysts**: Scheduled events and their potential impact
- **Earnings Preview**: Key metrics and guidance expectations
- **Calendar Risks**: Important dates that could drive volatility
- **Narrative Shifts**: Changing market themes and sentiment drivers

### 8. Trading Recommendations
- **News-Based Entry Points**: Specific trigger events for position initiation
- **Risk Management**: News-driven stop-loss and position sizing
- **Timeline Expectations**: Expected duration of news impact
- **Monitoring Protocol**: Key developments to track for position management

CRITICAL: Prioritize market-moving news with quantified impact assessments. Include specific price implications and probability estimates for each scenario.
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

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)
        
        # Use the correct message channel for news analyst
        messages = state.get("news_messages", [])
        
        # CRITICAL FIX: Validate message sequence for OpenAI API compliance
        from agent.utils.message_validator import clean_messages_for_llm
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
        
        # The LLM response now contains the complete analysis (single-pass)
        if len(result.tool_calls) == 0:
            # Direct comprehensive response from LLM - use as final report
            report = result.content
        else:
            # PT1: LLM wants to make tool calls - log for parallel visibility
            logger.info(f"⚡ NEWS_ANALYST: LLM requested {len(result.tool_calls)} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"⚡ NEWS_ANALYST: Tools requested: {tool_names}")
            report = ""

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
