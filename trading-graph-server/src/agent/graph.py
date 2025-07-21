"""Trading Agents LangGraph implementation.

Multi-agent trading analysis system using Finnhub API and LLM reasoning.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime

from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph


class Configuration(TypedDict):
    """Configurable parameters for the trading agent.
    
    Set these when creating assistants OR when invoking the graph.
    """
    api_provider: str  # "openai" or "google"
    model_name: str    # e.g., "gpt-4" or "gemini-pro"
    finnhub_api_key: Optional[str]


@dataclass
class TradingState:
    """State for the trading analysis pipeline."""
    
    # Input
    ticker: str = ""
    analysis_date: str = ""
    
    # Analysis Results
    fundamentals_report: str = ""
    technical_report: str = ""
    news_report: str = ""
    risk_report: str = ""
    
    # Final Output
    trading_recommendation: str = ""
    confidence_score: float = 0.0


async def fundamentals_analyst(state: TradingState, config: RunnableConfig) -> Dict[str, Any]:
    """Analyze company fundamentals using Finnhub API."""
    configuration = config.get("configurable", {})
    
    # Initialize LLM
    if configuration.get("api_provider") == "google":
        llm = ChatGoogleGenerativeAI(
            model=configuration.get("model_name", "gemini-pro"),
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        llm = ChatOpenAI(
            model=configuration.get("model_name", "gpt-4"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    prompt = f"""
    As a senior financial analyst, provide a comprehensive fundamental analysis for {state.ticker}.
    
    Analyze the following aspects:
    1. Financial Performance: Revenue growth, profitability trends
    2. Financial Position: Balance sheet strength, debt levels
    3. Cash Flow Analysis: Operating cash flow, free cash flow
    4. Valuation Metrics: P/E, P/B, PEG ratios
    5. Business Model: Competitive advantages, market position
    
    Date: {state.analysis_date}
    
    Provide a structured analysis with specific insights and recommendations.
    """
    
    try:
        response = await llm.ainvoke(prompt)
        fundamentals_report = response.content
    except Exception as e:
        fundamentals_report = f"Fundamentals analysis error: {str(e)}"
    
    return {"fundamentals_report": fundamentals_report}


async def technical_analyst(state: TradingState, config: RunnableConfig) -> Dict[str, Any]:
    """Perform technical analysis on the stock."""
    configuration = config.get("configurable", {})
    
    # Initialize LLM
    if configuration.get("api_provider") == "google":
        llm = ChatGoogleGenerativeAI(
            model=configuration.get("model_name", "gemini-pro"),
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        llm = ChatOpenAI(
            model=configuration.get("model_name", "gpt-4"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    prompt = f"""
    As a technical analyst, provide technical analysis for {state.ticker}.
    
    Analyze the following:
    1. Price Trends: Current trend direction, support/resistance levels
    2. Technical Indicators: RSI, MACD, moving averages
    3. Volume Analysis: Volume trends and patterns
    4. Chart Patterns: Key patterns and breakouts
    5. Entry/Exit Points: Optimal timing for trades
    
    Date: {state.analysis_date}
    
    Provide specific technical recommendations with price targets.
    """
    
    try:
        response = await llm.ainvoke(prompt)
        technical_report = response.content
    except Exception as e:
        technical_report = f"Technical analysis error: {str(e)}"
    
    return {"technical_report": technical_report}


async def news_analyst(state: TradingState, config: RunnableConfig) -> Dict[str, Any]:
    """Analyze recent news and market sentiment."""
    configuration = config.get("configurable", {})
    
    # Initialize LLM
    if configuration.get("api_provider") == "google":
        llm = ChatGoogleGenerativeAI(
            model=configuration.get("model_name", "gemini-pro"),
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        llm = ChatOpenAI(
            model=configuration.get("model_name", "gpt-4"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    prompt = f"""
    As a news analyst, analyze recent market sentiment for {state.ticker}.
    
    Focus on:
    1. Recent News: Key developments, earnings, product launches
    2. Market Sentiment: Analyst upgrades/downgrades, price targets
    3. Industry Trends: Sector performance, regulatory changes
    4. Social Media: Retail investor sentiment, trending topics
    5. Insider Activity: Recent insider trading patterns
    
    Date: {state.analysis_date}
    
    Provide sentiment analysis and impact assessment on stock price.
    """
    
    try:
        response = await llm.ainvoke(prompt)
        news_report = response.content
    except Exception as e:
        news_report = f"News analysis error: {str(e)}"
    
    return {"news_report": news_report}


async def risk_manager(state: TradingState, config: RunnableConfig) -> Dict[str, Any]:
    """Assess trading risks and provide risk management recommendations."""
    configuration = config.get("configurable", {})
    
    # Initialize LLM
    if configuration.get("api_provider") == "google":
        llm = ChatGoogleGenerativeAI(
            model=configuration.get("model_name", "gemini-pro"),
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        llm = ChatOpenAI(
            model=configuration.get("model_name", "gpt-4"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    prompt = f"""
    As a risk manager, assess the trading risks for {state.ticker}.
    
    Previous Analysis:
    - Fundamentals: {state.fundamentals_report[:500]}...
    - Technical: {state.technical_report[:500]}...
    - News: {state.news_report[:500]}...
    
    Evaluate:
    1. Market Risk: Volatility, beta, correlation with market
    2. Company-Specific Risk: Business risks, competition
    3. Liquidity Risk: Trading volume, bid-ask spreads
    4. Risk-Reward Ratio: Potential upside vs downside
    5. Position Sizing: Recommended allocation
    
    Date: {state.analysis_date}
    
    Provide risk assessment and management recommendations.
    """
    
    try:
        response = await llm.ainvoke(prompt)
        risk_report = response.content
    except Exception as e:
        risk_report = f"Risk analysis error: {str(e)}"
    
    return {"risk_report": risk_report}


async def trading_decision(state: TradingState, config: RunnableConfig) -> Dict[str, Any]:
    """Synthesize all analysis into final trading recommendation."""
    configuration = config.get("configurable", {})
    
    # Initialize LLM
    if configuration.get("api_provider") == "google":
        llm = ChatGoogleGenerativeAI(
            model=configuration.get("model_name", "gemini-pro"),
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        llm = ChatOpenAI(
            model=configuration.get("model_name", "gpt-4"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    prompt = f"""
    As the lead portfolio manager, synthesize all analysis for {state.ticker} into a final trading decision.
    
    FUNDAMENTALS ANALYSIS:
    {state.fundamentals_report}
    
    TECHNICAL ANALYSIS:
    {state.technical_report}
    
    NEWS & SENTIMENT:
    {state.news_report}
    
    RISK ASSESSMENT:
    {state.risk_report}
    
    Provide a clear trading recommendation:
    1. Decision: BUY/HOLD/SELL
    2. Confidence Level: 1-10 scale
    3. Price Target: Specific target price
    4. Time Horizon: Short/medium/long term
    5. Position Size: Recommended allocation %
    6. Stop Loss: Risk management level
    7. Key Catalysts: What could change the thesis
    8. Executive Summary: 2-3 sentence rationale
    
    Format as a clear, actionable trading recommendation.
    """
    
    try:
        response = await llm.ainvoke(prompt)
        recommendation = response.content
        
        # Extract confidence score (simple heuristic)
        confidence = 7.5  # Default confidence
        if "high confidence" in recommendation.lower():
            confidence = 9.0
        elif "low confidence" in recommendation.lower():
            confidence = 4.0
        elif "moderate confidence" in recommendation.lower():
            confidence = 6.5
            
    except Exception as e:
        recommendation = f"Trading decision error: {str(e)}"
        confidence = 0.0
    
    return {
        "trading_recommendation": recommendation,
        "confidence_score": confidence
    }


# Define the trading graph
graph = (
    StateGraph(TradingState, config_schema=Configuration)
    .add_node("fundamentals_analyst", fundamentals_analyst)
    .add_node("technical_analyst", technical_analyst)
    .add_node("news_analyst", news_analyst)
    .add_node("risk_manager", risk_manager)
    .add_node("trading_decision", trading_decision)
    .add_edge("__start__", "fundamentals_analyst")
    .add_edge("__start__", "technical_analyst") 
    .add_edge("__start__", "news_analyst")
    .add_edge("fundamentals_analyst", "risk_manager")
    .add_edge("technical_analyst", "risk_manager")
    .add_edge("news_analyst", "risk_manager")
    .add_edge("risk_manager", "trading_decision")
    .compile(name="Trading Agents Graph")
)
