"""
Crypto-Aware Fundamentals Analyst
Enhanced version that properly handles both stocks and cryptocurrencies.
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import the existing ultra-fast collector for stocks
from ..dataflows.ultra_fast_fundamentals_collector import (
    UltraFastFundamentalsCollector,
    CollectorConfig
)

# Import our new crypto price fetcher
from ..dataflows.crypto_price_fetcher import CryptoPriceFetcher

from ..utils.debug_logging import debug_node, log_llm_interaction

# Import Universal Validator for comprehensive monitoring
from ..monitoring.universal_validator import validate, ValidationSeverity

# Try to import minimalist_log but make it optional
try:
    from ..utils.minimalist_logging import minimalist_log
except ImportError:
    # Fallback if minimalist_log is not available
    def minimalist_log(category, message):
        logger.info(f"[{category}] {message}")

logger = logging.getLogger(__name__)

# Global collector instance for connection pooling
_global_collector: Optional[UltraFastFundamentalsCollector] = None


def transform_price_targets_for_report(fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform price targets data structure to match report generation expectations.
    
    Fixes the mismatch between enhanced price targets (targetMean, numberOfAnalysts) 
    and report generation expectations (mean, analysts).
    """
    if not fundamental_data or 'price_targets' not in fundamental_data:
        return fundamental_data
        
    price_targets = fundamental_data.get('price_targets', {})
    if not price_targets or not isinstance(price_targets, dict):
        return fundamental_data
    
    # Check if transformation is needed (enhanced format detected)
    if ('targetMean' in price_targets or 
        'numberOfAnalysts' in price_targets or 
        'lastPrice' in price_targets):
        
        logger.info(f"🔧 PRICE TARGETS TRANSFORM: Converting enhanced format to report format")
        
        # Transform to expected format
        transformed_targets = {
            'current': price_targets.get('lastPrice', 0),
            'mean': price_targets.get('targetMean', 0),
            'high': price_targets.get('targetHigh', 0), 
            'low': price_targets.get('targetLow', 0),
            'analysts': price_targets.get('numberOfAnalysts', 0),
            # Preserve additional metadata
            'confidence': price_targets.get('confidence', 'UNKNOWN'),
            'source': price_targets.get('source', 'Unknown'),
            'lastUpdated': price_targets.get('lastUpdated', 'N/A')
        }
        
        # Update the data structure
        fundamental_data['price_targets'] = transformed_targets
        
        logger.info(f"✅ PRICE TARGETS TRANSFORMED: Mean=${transformed_targets['mean']:.2f}, "
                   f"Analysts={transformed_targets['analysts']}, "
                   f"Source={transformed_targets.get('source', 'Unknown')}")
    
    return fundamental_data


async def get_or_create_collector(api_key: str) -> UltraFastFundamentalsCollector:
    """Get or create singleton collector instance for connection pooling."""
    global _global_collector
    
    if _global_collector is None:
        # Configure for optimal performance
        config = CollectorConfig(
            max_connections=20,
            max_keepalive_connections=10,
            timeout_connect=2.0,
            timeout_total=10.0,
            max_concurrent_api_calls=10,
            circuit_breaker_failure_threshold=5,
            redis_min_connections=5,
            redis_max_connections=10,
            cache_ttl_days=90
        )
        
        _global_collector = UltraFastFundamentalsCollector(
            finnhub_key=api_key,
            redis_url="redis://localhost",  # Use default Redis
            config=config
        )
        
        # Initialize connection pools
        await _global_collector.setup()
        logger.info("🚀 UltraFastFundamentalsCollector initialized with connection pooling")
    
    return _global_collector


def create_fundamentals_analyst_crypto_aware(llm=None, toolkit=None):
    """
    Create crypto-aware fundamentals analyst that handles both stocks and cryptocurrencies.
    
    This enhanced version:
    - Detects cryptocurrency tickers (BTC, ETH, DOGE, SOL, etc.)
    - Fetches real-time crypto prices using yfinance
    - Falls back to stock fundamentals for traditional assets
    - Prevents AI hallucination by providing actual prices
    
    Args:
        llm: Ignored - kept for interface compatibility
        toolkit: Used to extract API keys if available
    """
    
    @debug_node("Fundamentals_Analyst_CryptoAware")
    async def fundamentals_analyst_crypto_aware_node(state):
        """Crypto-aware fundamentals collection."""
        start_time = time.time()
        logger.info(f"⚡ fundamentals_analyst_crypto_aware START: {time.time()}")
        minimalist_log("FUNDAMENTALS_CRYPTO", "Starting crypto-aware collection")
        
        # Extract ticker and date from state
        ticker = state.get("company_of_interest", "").upper()
        trade_date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))
        
        if not ticker:
            logger.error("❌ No ticker specified in state")
            return {
                "fundamentals_messages": [],
                "fundamentals_report": "Error: No ticker specified",
                "sender": "Fundamentals Analyst CryptoAware"
            }
        
        try:
            # 🚀 CRITICAL: Check if this is a cryptocurrency
            is_crypto = CryptoPriceFetcher.is_crypto(ticker)
            
            if is_crypto:
                logger.info(f"🪙 Detected {ticker} as CRYPTOCURRENCY - using crypto price fetcher")
                minimalist_log("CRYPTO_DETECTED", f"{ticker} identified as cryptocurrency")
                
                # Fetch crypto data
                fetch_start = time.time()
                crypto_data = await CryptoPriceFetcher.get_current_price(ticker)
                fetch_time = time.time() - fetch_start
                
                if crypto_data.get('success') and crypto_data.get('price', 0) > 0:
                    # Generate crypto-specific report
                    report = generate_crypto_fundamentals_report(ticker, crypto_data, fetch_time)
                    
                    logger.info(f"✅ Successfully fetched {ticker} crypto price: ${crypto_data['price']:,.2f}")
                    minimalist_log("CRYPTO_SUCCESS", f"{ticker}: ${crypto_data['price']:,.2f}")
                    
                    # Prepare crypto fundamentals data in a format similar to stocks
                    fundamental_data = {
                        'asset_type': 'cryptocurrency',
                        'profile': {
                            'name': ticker,
                            'ticker': crypto_data.get('original_ticker', ticker),
                            'normalized_ticker': crypto_data.get('ticker', f'{ticker}-USD'),
                            'finnhubIndustry': 'Cryptocurrency',
                            'marketCapitalization': crypto_data.get('market_cap', 0) / 1_000_000  # Convert to millions
                        },
                        'metrics': {
                            'current_price': crypto_data.get('price', 0),
                            'volume_24h': crypto_data.get('volume_24h', 0),
                            'change_24h': crypto_data.get('change_24h', 0),
                            'change_percent_24h': crypto_data.get('change_percent_24h', 0),
                            'high_24h': crypto_data.get('high_24h', 0),
                            'low_24h': crypto_data.get('low_24h', 0),
                            'circulating_supply': crypto_data.get('circulating_supply', 0),
                            'total_supply': crypto_data.get('total_supply', 0)
                        },
                        'price_targets': {
                            'current': crypto_data.get('price', 0),
                            'mean': 0,  # Crypto doesn't have analyst targets
                            'low': crypto_data.get('low_24h', 0),
                            'high': crypto_data.get('high_24h', 0),
                            'analysts': 0
                        }
                    }
                else:
                    # Crypto fetch failed
                    logger.error(f"❌ Failed to fetch crypto data for {ticker}: {crypto_data.get('error')}")
                    report = f"Error fetching crypto data for {ticker}: {crypto_data.get('error', 'Unknown error')}"
                    fundamental_data = {}
                    
            else:
                # Traditional stock - use existing logic
                logger.info(f"📈 Processing {ticker} as TRADITIONAL STOCK")
                minimalist_log("STOCK_DETECTED", f"{ticker} identified as stock")
                
                # Get API key from toolkit or environment
                finnhub_key = None
                if toolkit and hasattr(toolkit, 'config'):
                    finnhub_key = toolkit.config.get('finnhub_key')
                
                if not finnhub_key:
                    # Try to get from environment or state
                    import os
                    finnhub_key = os.environ.get('FINNHUB_API_KEY') or state.get('finnhub_key')
                
                if not finnhub_key:
                    logger.error("❌ No Finnhub API key available")
                    return {
                        "fundamentals_messages": [],
                        "fundamentals_report": "Error: Finnhub API key not configured",
                        "sender": "Fundamentals Analyst CryptoAware"
                    }
                
                # Get or create collector with connection pooling
                collector = await get_or_create_collector(finnhub_key)
                
                # Fetch fundamental data with ultra-fast collector
                logger.info(f"🚀 Fetching stock fundamentals for {ticker}...")
                fetch_start = time.time()
                
                fundamental_data = await collector.get(ticker)
                fetch_time = time.time() - fetch_start
                
                # 🔧 REMOVED: Transform was breaking field names - ultra-fast report expects original format
                # fundamental_data = transform_price_targets_for_report(fundamental_data)
                
                # 🔧 V3: Check if financial statements are blocked and fetch from Yahoo (simplified)
                blocked_statements = [s for s in ['balance_sheet', 'income_statement', 'cash_flow'] 
                                     if fundamental_data.get(s, {}).get('error')]
                
                if blocked_statements:
                    logger.info(f"📊 {len(blocked_statements)} Finnhub statements blocked, using Yahoo fallback for {ticker}")
                    
                    try:
                        from ..dataflows.yahoo_fundamentals_fallback import try_yahoo_fallback
                        # V3 simplified: direct async function call, no class instantiation needed
                        yahoo_results = await try_yahoo_fallback(ticker, blocked_statements)
                        
                        if yahoo_results:
                            # Merge successful Yahoo data into fundamental_data
                            for statement_type, data in yahoo_results.items():
                                if data and fundamental_data.get(statement_type, {}).get('error'):
                                    fundamental_data[statement_type] = data
                                    logger.info(f"✓ {statement_type} updated from Yahoo Finance")
                            
                            # Update endpoints count
                            if 'endpoints_fetched' in fundamental_data:
                                fundamental_data['endpoints_fetched'] += len(yahoo_results)
                            
                            logger.info(f"✅ Yahoo integration complete: {len(yahoo_results)} statements recovered")
                    
                    except Exception as e:
                        logger.error(f"Yahoo fallback failed: {e}")
                        # Continue with partial data - don't fail the entire request
                
                # Generate comprehensive stock report using ultra-fast comprehensive function
                from .fundamentals_analyst_ultra_fast import generate_fundamentals_report
                report = generate_fundamentals_report(ticker, fundamental_data, fetch_time)
            
            # Calculate total execution time
            total_time = time.time() - start_time
            
            logger.info(f"⚡ fundamentals_analyst_crypto_aware COMPLETE: {time.time()}")
            logger.info(f"⏱️ Total execution time: {total_time:.3f}s, Fetch time: {fetch_time:.3f}s")
            
            # Create state update
            new_state = {
                "fundamentals_messages": [],
                "fundamentals_report": report,
                "fundamentals_data": fundamental_data,  # Include raw data for other agents
                "sender": "Fundamentals Analyst CryptoAware",
                "execution_time": total_time,
                "fetch_time": fetch_time,
                "asset_type": 'cryptocurrency' if is_crypto else 'stock'
            }
            
            # Return state update
            return new_state
            
        except Exception as e:
            logger.error(f"❌ Crypto-aware fundamentals failed: {e}")
            duration = time.time() - start_time
            
            return {
                "fundamentals_messages": [],
                "fundamentals_report": f"Error fetching fundamentals: {str(e)}",
                "sender": "Fundamentals Analyst CryptoAware",
                "execution_time": duration
            }
    
    return fundamentals_analyst_crypto_aware_node


def generate_crypto_fundamentals_report(ticker: str, data: Dict[str, Any], fetch_time: float) -> str:
    """
    Generate a comprehensive fundamentals report for cryptocurrencies.
    
    This provides crypto-specific metrics instead of traditional stock metrics.
    """
    # Get the current price - CRITICAL for preventing hallucination
    current_price = data.get('price', 0)
    
    report_lines = [
        f"🪙 CRYPTOCURRENCY FUNDAMENTALS: {ticker}",
        f"⚡ Real-time data fetched in {fetch_time:.3f}s",
        "=" * 60,
        "",
        "📈 CURRENT MARKET DATA:",
        f"  Current Price: ${current_price:,.2f}",  # ACTUAL PRICE, NOT HALLUCINATED!
        f"  24h Change: {data.get('change_percent_24h', 0):.2f}%",
        f"  24h High: ${data.get('high_24h', 0):,.2f}",
        f"  24h Low: ${data.get('low_24h', 0):,.2f}",
        "",
        "📊 MARKET METRICS:",
        f"  Market Cap: ${data.get('market_cap', 0):,.0f}",
        f"  24h Volume: ${data.get('volume_24h', 0):,.0f}",
        f"  Circulating Supply: {data.get('circulating_supply', 0):,.0f}",
        f"  Total Supply: {data.get('total_supply', 0):,.0f}",
        "",
        "🎯 PRICE TARGETS:",
        f"  Current: ${current_price:,.2f}",
        "  No analyst targets available (cryptocurrency)",
        "  Analysts: 0",
        "",
        "=" * 60,
        "🔍 FUNDAMENTAL SIGNAL:",
    ]
    
    # Determine signal based on 24h momentum
    change_24h = data.get('change_percent_24h', 0)
    if change_24h > 5:
        signal = "🟢 STRONG BUY - Strong upward momentum"
    elif change_24h > 2:
        signal = "🟢 BUY - Positive momentum"
    elif change_24h > -2:
        signal = "🟡 HOLD - Neutral momentum"
    elif change_24h > -5:
        signal = "🔴 SELL - Negative momentum"
    else:
        signal = "🔴 STRONG SELL - Strong downward momentum"
    
    report_lines.append(signal)
    report_lines.append(f"  ✅ Real-time price data: ${current_price:,.2f}")
    report_lines.append(f"  ✅ Data source: {data.get('source', 'yfinance')}")
    report_lines.append("")
    report_lines.append(f"⚡ Report generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(report_lines)


# Note: Simplified stock report function removed - now using comprehensive 
# generate_fundamentals_report from fundamentals_analyst_ultra_fast.py 
# which includes all 15 API endpoints data for complete fundamental analysis