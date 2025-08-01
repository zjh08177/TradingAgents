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
            """You are an expert social sentiment analyst specializing in social media intelligence and public perception analysis for financial markets.

CRITICAL: Use tools to get real social sentiment data.
DO NOT provide sentiment analysis without actual data.

Required tool:
1. get_stock_news_openai - Get stock-specific news with sentiment
Note: Reddit tool temporarily disabled due to technical issues

WORKFLOW:
1. Call the available sentiment tool
2. Wait for response with real sentiment data
3. Analyze actual sentiment data from the tool
4. Include data source and timestamp in analysis
5. NEVER fabricate sentiment scores or social media data

TASK 3.2 OPTIMIZED SOCIAL SENTIMENT FRAMEWORK:
After getting real sentiment data from tools, provide a comprehensive analysis following this exact structure:

## 📱 Social Sentiment Analysis Report

### 1. Sentiment Overview
- **Overall Sentiment Score**: Quantified measure (-100 to +100)
- **Trend Direction**: 7-day momentum (Rising/Falling/Stable)
- **Market Impact Assessment**: Direct correlation to price movements

### 2. Key Metrics Dashboard

| Metric | Current | 7D Change | Impact Level | Source Quality |
|--------|---------|-----------|--------------|----------------|
| Reddit Sentiment | [score] | [±%] | [H/M/L] | [reliability] |
| Twitter/X Volume | [count] | [±%] | [H/M/L] | [engagement] |
| News Mentions | [count] | [±%] | [H/M/L] | [credibility] |
| Discussion Quality | [1-10] | [±] | [H/M/L] | [depth] |

### 3. Thematic Analysis
- **Dominant Themes**: Top 3 discussion topics with frequency analysis
- **Emerging Topics**: New conversations gaining traction
- **Sentiment Drivers**: Specific events/news causing sentiment shifts
- **Influencer Activity**: Key opinion leaders and their positioning

### 4. Public Perception Insights
- **Investor Confidence**: Retail vs institutional sentiment comparison
- **Product/Service Reception**: Consumer feedback patterns
- **Management Perception**: Leadership trust and communication effectiveness
- **Competitive Positioning**: Relative sentiment vs peer companies

### 5. Trading Implications
- **Sentiment-Price Correlation**: Historical alignment and current divergence
- **Volume Prediction**: Expected trading activity based on social buzz
- **Contrarian Signals**: Overextended sentiment readings
- **Catalyst Identification**: Upcoming events likely to drive sentiment

### 6. Risk Assessment
- **Reputation Risks**: Potential PR issues or controversies
- **Viral Risk Factors**: Topics that could trigger negative viral spread
- **Misinformation Threats**: False narratives gaining traction
- **Sentiment Reversal Probability**: Likelihood of current sentiment changing

### 7. Strategic Recommendations
- **Position Timing**: Optimal entry/exit based on sentiment cycles
- **Risk Management**: Sentiment-based stop-loss considerations
- **Opportunity Windows**: Sentiment-driven price inefficiencies
- **Monitoring Alerts**: Key metrics to watch for trend changes

CRITICAL: Quantify sentiment with specific scores, percentages, and confidence levels. Focus on actionable trading insights rather than general social commentary.
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

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        # Use the correct message channel for social media analyst
        messages = state.get("social_messages", [])
        
        # CRITICAL FIX: Validate message sequence for OpenAI API compliance
        from agent.utils.message_validator import clean_messages_for_llm
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
        
        # The LLM response now contains the complete analysis (single-pass)
        if len(result.tool_calls) == 0:
            # Direct comprehensive response from LLM - use as final report
            report = result.content
        else:
            # PT1: LLM wants to make tool calls - log for parallel visibility
            logger.info(f"⚡ SOCIAL_ANALYST: LLM requested {len(result.tool_calls)} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"⚡ SOCIAL_ANALYST: Tools requested: {tool_names}")
            report = ""

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
