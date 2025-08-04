#!/usr/bin/env python3
"""
Analyst Error Handling - Common error handling for analyst nodes
Handles tool failures and empty responses gracefully
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def generate_fallback_report(analyst_type: str, state: Dict[str, Any]) -> str:
    """
    Generate a fallback report when tools fail
    
    Args:
        analyst_type: Type of analyst (market, social, news, fundamentals)
        state: Current agent state
        
    Returns:
        Fallback report string
    """
    ticker = state.get("company_of_interest", "UNKNOWN")
    trade_date = state.get("trade_date", "")
    
    fallback_reports = {
        "market": (
            f"Unable to retrieve market data for {ticker} due to technical issues. "
            "All requested technical indicators and price data are currently unavailable. "
            "Without access to price movements, volume data, or technical indicators, "
            "cannot provide informed market analysis. "
            "Recommendation: HOLD - Insufficient data for trading decision."
        ),
        "social": (
            f"Unable to access social media sentiment data for {ticker}. "
            "StockTwits, Twitter mentions, and Reddit discussions are currently unavailable. "
            "Without social sentiment indicators, cannot gauge retail investor sentiment "
            "or identify trending discussions. "
            "Sentiment: NEUTRAL - No data available for analysis."
        ),
        "news": (
            f"Unable to retrieve news data for {ticker} on {trade_date}. "
            "Global news feeds and company-specific news sources are currently inaccessible. "
            "Without recent news coverage, cannot identify market-moving events "
            "or assess news-driven sentiment. "
            "News Impact: UNKNOWN - Data retrieval failed."
        ),
        "fundamentals": (
            f"Unable to access fundamental data for {ticker}. "
            "Financial statements, earnings data, and insider transactions are unavailable. "
            "Without fundamental metrics, cannot evaluate company financial health "
            "or intrinsic value. "
            "Fundamental Rating: INCOMPLETE - Data sources offline."
        )
    }
    
    report = fallback_reports.get(analyst_type, f"Unable to retrieve {analyst_type} data due to technical issues.")
    logger.error(f"🚨 {analyst_type.upper()}_ANALYST: Using fallback report due to tool failures")
    
    return report


def check_report_validity(report: str, analyst_type: str, min_length: int = 50) -> bool:
    """
    Check if a report is valid and contains actual content
    
    Args:
        report: The report content
        analyst_type: Type of analyst
        min_length: Minimum acceptable length
        
    Returns:
        True if report is valid, False otherwise
    """
    if not report or len(report.strip()) < min_length:
        logger.warning(f"⚠️ {analyst_type.upper()}_ANALYST: Report too short ({len(report)} chars)")
        return False
    
    # Check for error patterns
    error_patterns = [
        "error retrieving",
        "issue obtaining",
        "unable to access",
        "failed to fetch",
        "no data available",
        "technical issues"
    ]
    
    report_lower = report.lower()
    for pattern in error_patterns:
        if pattern in report_lower:
            logger.warning(f"⚠️ {analyst_type.upper()}_ANALYST: Report contains error pattern: {pattern}")
            return False
    
    return True


def handle_analyst_response(
    result: Any,
    messages: list,
    state: Dict[str, Any],
    analyst_type: str,
    tool_message_count: int
) -> str:
    """
    Handle analyst response with proper error checking
    
    Args:
        result: LLM response
        messages: Current messages
        state: Agent state
        analyst_type: Type of analyst (market, social, news, fundamentals)
        tool_message_count: Number of tool messages
        
    Returns:
        Report content
    """
    # Map analyst types to state keys
    tools_failed_key = f"{analyst_type}_tools_failed"
    
    if len(getattr(result, 'tool_calls', [])) == 0:
        # No tool calls in current response
        if tool_message_count > 0:
            # Tools were executed previously
            # Check if all tools failed
            if state.get(tools_failed_key, False):
                # All tools failed, generate a fallback report
                report = generate_fallback_report(analyst_type, state)
                logger.error(f"📊 {analyst_type.upper()}_ANALYST: Using fallback report due to tool failures")
            else:
                # Tools executed, check if report is valid
                report = result.content if hasattr(result, 'content') else ""
                
                if not check_report_validity(report, analyst_type):
                    # Report is invalid, use fallback
                    logger.warning(f"⚠️ {analyst_type.upper()}_ANALYST: Invalid report detected, using fallback")
                    report = generate_fallback_report(analyst_type, state)
                else:
                    logger.info(f"✅ {analyst_type.upper()}_ANALYST: Generated valid report ({len(report)} chars)")
        else:
            # Direct response without tools
            report = result.content if hasattr(result, 'content') else ""
            logger.info(f"📊 {analyst_type.upper()}_ANALYST: Direct response without tools ({len(report)} chars)")
    else:
        # Current response contains tool calls - tools need to be executed first
        tool_calls = getattr(result, 'tool_calls', [])
        logger.info(f"⚡ {analyst_type.upper()}_ANALYST: LLM requested {len(tool_calls)} tool calls")
        tool_names = [tc.get('name', 'unknown') for tc in tool_calls]
        logger.info(f"⚡ {analyst_type.upper()}_ANALYST: Tools requested: {tool_names}")
        report = ""  # No report yet, tools need to be executed first
    
    return report