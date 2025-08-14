"""
Yahoo Finance fallback for Finnhub free tier limitations.
V3 Simplified implementation with LangGraph compliance.
"""

import asyncio
import logging
import re
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


def validate_ticker(ticker: str) -> bool:
    """
    Validate ticker symbol for security and format compliance.
    
    Args:
        ticker: Stock symbol to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Handle non-string inputs
    if not isinstance(ticker, str):
        return False
    
    if not ticker or len(ticker) > 10 or len(ticker) < 1:
        return False
    return re.match(r'^[A-Z0-9\-\.]+$', ticker.upper()) is not None


async def try_yahoo_fallback(ticker: str, blocked_statements: List[str]) -> Dict[str, Any]:
    """
    V3 Simplified Yahoo fallback - LangGraph compliant async implementation.
    
    Only fetches blocked statements in parallel to maximize performance.
    
    Args:
        ticker: Stock symbol (validated)
        blocked_statements: List of statement types that are blocked
        
    Returns:
        Dictionary with successfully fetched financial statements
    """
    # Input validation - security critical
    if not validate_ticker(ticker):
        logger.warning(f"Invalid ticker format: {ticker}")
        return {}
    
    if not blocked_statements:
        return {}
    
    try:
        logger.info(f"📊 Yahoo fallback for {ticker}: {len(blocked_statements)} statements")
        
        # Use proper async execution with thread pool
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Create ticker object once
            stock = yf.Ticker(ticker)
            
            # Prepare parallel tasks for only blocked statements
            tasks = []
            task_mapping = {}
            
            if 'balance_sheet' in blocked_statements:
                task = loop.run_in_executor(executor, lambda: stock.balance_sheet)
                tasks.append(task)
                task_mapping[len(tasks) - 1] = 'balance_sheet'
                
            if 'income_statement' in blocked_statements:
                task = loop.run_in_executor(executor, lambda: stock.income_stmt)
                tasks.append(task)
                task_mapping[len(tasks) - 1] = 'income_statement'
                
            if 'cash_flow' in blocked_statements:
                task = loop.run_in_executor(executor, lambda: stock.cash_flow)
                tasks.append(task)
                task_mapping[len(tasks) - 1] = 'cash_flow'
            
            if not tasks:
                return {}
            
            # Execute all tasks in parallel
            results_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_results = {}
            for i, data in enumerate(results_data):
                statement_type = task_mapping[i]
                
                try:
                    # Handle exceptions from gather
                    if isinstance(data, Exception):
                        logger.warning(f"{statement_type} failed: {data}")
                        continue
                    
                    # Validate data
                    if data is not None and hasattr(data, 'empty') and not data.empty:
                        # 🔧 CRITICAL FIX: Transpose DataFrame to get proper structure
                        # Original: rows=metrics, cols=dates → to_dict('records') gives {date: value} per metric
                        # Fixed: rows=dates, cols=metrics → to_dict('records') gives {metric: value} per date
                        transposed_data = data.transpose()
                        
                        successful_results[statement_type] = {
                            'financials': transposed_data.to_dict('records')
                        }
                        logger.info(f"✓ {statement_type} fetched for {ticker} (transposed {data.shape} -> {transposed_data.shape})")
                    else:
                        logger.warning(f"{statement_type} empty for {ticker}")
                        
                except Exception as e:
                    logger.warning(f"{statement_type} processing failed: {e}")
                    continue
            
            logger.info(f"✅ Yahoo fallback complete: {len(successful_results)}/{len(blocked_statements)} successful")
            return successful_results
            
    except Exception as e:
        logger.error(f"Yahoo fallback failed for {ticker}: {e}")
        return {}


class YahooFundamentalsFallback:
    """
    V3 Simplified Yahoo Finance integration.
    LangGraph compliant with async parallel execution.
    Redis caching removed for KISS principle compliance.
    """
    
    def __init__(self, redis_client=None):
        """Initialize - redis_client maintained for backward compatibility but not used."""
        pass
        
    async def get_missing_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch financial statements - V3 simplified interface.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Success/failure result with data
        """
        # Assume all statements are blocked for backward compatibility
        blocked = ['balance_sheet', 'income_statement', 'cash_flow']
        results = await try_yahoo_fallback(ticker, blocked)
        
        return {
            'source': 'yahoo_finance',
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'success': bool(results),
            'data': results
        }
    
    def format_for_report(self, yahoo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Yahoo data to match Finnhub structure."""
        if not yahoo_data.get('success'):
            return {}
            
        return yahoo_data.get('data', {})