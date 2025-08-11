"""
Enhanced News Analyst - Day 2 Implementation
Focused exclusively on traditional news media analysis
NO social media sentiment (handled by Social Media Analyst)
"""

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
    """
    Create enhanced news analyst with comprehensive analysis capabilities
    Focused ONLY on traditional news media - NO social sentiment
    """
    @debug_node("News_Analyst_Enhanced")
    async def news_analyst_node(state):
        # Task: Add Execution Timing Logs
        start_time = time.time()
        logger.info(f"⏱️ news_analyst_enhanced START: {time.time()}")
        
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # CRITICAL: News-only toolkit configuration
        # NO Reddit, NO social media tools
        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_google_news,  # Primary: Serper API (4,500+ sources)
                toolkit.get_finnhub_news   # Emergency fallback only
            ]
        else:
            tools = [
                toolkit.get_finnhub_news  # Offline fallback
            ]

        # Enhanced comprehensive analysis prompt - Day 2
        system_message = """You are a senior financial NEWS analyst specializing in traditional news media.

CRITICAL BOUNDARIES:
- You handle ONLY traditional news media (newspapers, financial sites, wire services)
- Social media sentiment is handled by Social Media Analyst - DO NOT analyze Reddit/Twitter/social
- Focus exclusively on NEWS from authoritative sources

MANDATORY WORKFLOW:
1. Call get_google_news FIRST - this will return 50+ articles from 4,500+ sources via pagination
2. If needed, call get_finnhub_news as fallback for additional coverage
3. Perform deep NEWS analysis (NOT social sentiment - that's another analyst's job)

Tools available: {tool_names}

COMPREHENSIVE ANALYSIS STRUCTURE (provide ALL sections):

## 1. NEWS COVERAGE SUMMARY
- Total articles analyzed (target: 50+ from Google News)
- Key headlines with immediate market impact assessment
- Source distribution and authority ranking:
  * Tier 1 (Reuters, Bloomberg, WSJ, FT): Highest confidence
  * Tier 2 (CNBC, MarketWatch, Yahoo Finance): Medium confidence  
  * Tier 3 (Other sources): Lower confidence
- Coverage completeness assessment and any gaps identified
- News velocity: How fast is news spreading across sources?

## 2. TEMPORAL NEWS IMPACT ANALYSIS
- **Immediate (0-24 hours)**: Breaking news implications and likely market reaction
- **Short-term (1-7 days)**: News momentum analysis and follow-up coverage expected
- **Medium-term (1-4 weeks)**: Story development trajectory and potential catalysts
- **Long-term (1-3 months)**: Strategic news themes and fundamental implications

## 3. NEWS AUTHORITY & CREDIBILITY ASSESSMENT
- Source reliability scoring based on historical accuracy
- Consensus vs. outlier reporting analysis
- Fact verification across multiple authoritative sources
- Conflicting reports identification and resolution
- Information quality confidence score (0-100%)

## 4. NEWS-BASED RISK ASSESSMENT
- **Headline Risks**: Negative news that could impact stock price
- **Regulatory/Compliance News**: SEC, DOJ, regulatory body mentions
- **M&A and Corporate Actions**: Merger, acquisition, restructuring news
- **Macro-Economic Impact**: How broader economic news affects this stock
- **Competitive Landscape**: News about competitors affecting relative position
- **Risk Severity Score**: Critical/High/Medium/Low with justification

## 5. NEWS-DRIVEN TRADING SIGNALS
- **Primary Signal**: BUY/HOLD/SELL based ONLY on news analysis
- **Confidence Level**: High/Medium/Low based on source authority and consensus
- **Key Catalysts**: Specific news events driving the recommendation
- **News Momentum**: Positive/Negative/Neutral trend in coverage
- **Entry/Exit Points**: Suggested levels based on news-driven volatility
- **Risk/Reward Assessment**: Based on news sentiment and coverage

## 6. EVIDENCE & ATTRIBUTION
- **Top 10 Most Impactful Articles**:
  * Include: Headline, Source, Date, Key Quote
  * Rank by: Market impact potential
- **Direct Quotes**: From CEOs, analysts, regulators (with attribution)
- **Fact Verification**: Cross-referenced facts from 3+ sources
- **News Consensus**: What majority of authoritative sources agree on
- **Contrarian Views**: Minority opinions from credible sources

## 7. MARKET REACTION PREDICTION
- Expected price movement based on news sentiment
- Volume implications from news coverage intensity
- Institutional vs. retail reaction differences
- Time horizon for news to be fully priced in

## FINAL NEWS-BASED RECOMMENDATION
Provide clear BUY/HOLD/SELL recommendation based EXCLUSIVELY on news analysis.
Include confidence score (0-100%) and top 3 reasons from news coverage.

Remember: You are the NEWS analyst. Social sentiment is NOT your domain.
Focus on facts, authoritative sources, and journalistic reporting ONLY.
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant NEWS analyst, collaborating with other assistants."
                    " Use the provided tools to gather comprehensive news data (50+ articles target)."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "\nFor your reference, the current date is {current_date}. We are analyzing {ticker}."
                    "\nIMPORTANT: You must gather real news data using tools before analysis. Target 50+ articles.",
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
        
        # Add LLM interaction logging
        prompt_text = f"System: {system_message}\nUser: {current_date}, {ticker}"
        llm_start = time.time()
        
        # Log start of LLM invocation for parallel execution visibility
        logger.info(f"⚡ NEWS_ANALYST_ENHANCED: Starting LLM invocation for {ticker}")
        logger.info(f"📊 NEWS_ANALYST_ENHANCED: Available tools: {tool_names_str}")
        
        result = await safe_llm_invoke(chain, messages)
        llm_time = time.time() - llm_start
        logger.info(f"⚡ NEWS_ANALYST_ENHANCED: LLM invocation completed in {llm_time:.2f}s")
        
        log_llm_interaction(
            model="news_analyst_llm",
            prompt_length=len(prompt_text),
            response_length=len(result.content) if hasattr(result, 'content') else 0,
            execution_time=llm_time
        )

        # Single-pass execution - generate report directly from LLM response
        tool_message_count = sum(1 for msg in messages if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool')
        
        # CRITICAL FIX: ENFORCE MANDATORY TOOL USAGE
        if len(result.tool_calls) == 0:
            # No tool calls in current response
            if tool_message_count > 0:
                # Tools were executed previously, this should be the final report
                report = result.content
                logger.info(f"📊 NEWS_ANALYST_ENHANCED: Generated comprehensive report after tool execution ({len(report)} chars)")
                
                # Verify NO social media contamination
                forbidden_terms = ['reddit', 'wsb', 'wallstreetbets', 'stocktwits', 'twitter']
                report_lower = report.lower()
                contamination = [term for term in forbidden_terms if term in report_lower]
                if contamination:
                    logger.warning(f"⚠️ NEWS_ANALYST_ENHANCED: Social media terms detected: {contamination}")
                    # Clean the report - case insensitive replacement
                    import re
                    for term in contamination:
                        # Use regex for case-insensitive replacement
                        report = re.sub(re.escape(term), "[REDACTED-SOCIAL]", report, flags=re.IGNORECASE)
                    logger.info(f"✅ NEWS_ANALYST_ENHANCED: Cleaned social media contamination")
                    
            else:
                # CRITICAL ERROR: LLM failed to call tools - force error message
                logger.error(f"❌ NEWS_ANALYST_ENHANCED: NO TOOLS CALLED - Report will be marked as failed")
                report = f"⚠️ WARNING: News analysis failed for {ticker}. No news data was retrieved. Tool execution required."
                logger.warning(f"🚨 NEWS_ANALYST_ENHANCED: Completed WITHOUT tool calls!")
            
            # Apply token limits if needed (but quality is priority)
            # Only truncate if absolutely necessary
            max_tokens = 8000  # Increased limit for comprehensive analysis
            if len(report) > max_tokens * 4:  # Rough char to token ratio
                logger.warning(f"⚠️ NEWS_ANALYST_ENHANCED: Report exceeds {max_tokens} tokens, truncating")
                report = get_token_limiter().truncate_response(report, "News Analyst Enhanced")
            else:
                logger.info(f"✅ NEWS_ANALYST_ENHANCED: Report within token limits")
                
        else:
            # Current response contains tool calls - tools need to be executed first
            logger.info(f"⚡ NEWS_ANALYST_ENHANCED: LLM requested {len(result.tool_calls)} tool calls")
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"⚡ NEWS_ANALYST_ENHANCED: Tools requested: {tool_names}")
            
            # Verify only news tools are being called
            allowed_news_tools = ['get_google_news', 'get_finnhub_news']
            invalid_tools = [t for t in tool_names if t not in allowed_news_tools]
            if invalid_tools:
                logger.error(f"❌ NEWS_ANALYST_ENHANCED: Invalid tools requested: {invalid_tools}")
                # Remove invalid tool calls
                result.tool_calls = [tc for tc in result.tool_calls if tc.get('name') in allowed_news_tools]
                logger.info(f"✅ NEWS_ANALYST_ENHANCED: Filtered to valid news tools only")
            
            report = ""  # No report yet, tools need to be executed first

        # Return the state update
        updated_messages = messages + [result]
        
        # Add execution timing logs
        duration = time.time() - start_time
        logger.info(f"⏱️ news_analyst_enhanced END: {time.time()} (duration: {duration:.2f}s)")
        
        # Log quality metrics
        if report:
            sections = ['NEWS COVERAGE SUMMARY', 'TEMPORAL NEWS IMPACT', 'NEWS AUTHORITY', 
                       'RISK ASSESSMENT', 'TRADING SIGNALS', 'EVIDENCE', 'MARKET REACTION']
            sections_found = sum(1 for s in sections if s in report.upper())
            logger.info(f"📊 NEWS_ANALYST_ENHANCED: Report completeness: {sections_found}/{len(sections)} sections")
        
        return {
            "news_messages": updated_messages,
            "news_report": report,
            "sender": "News Analyst Enhanced"
        }

    return news_analyst_node