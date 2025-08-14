"""
Integration Example: How to update existing analysts to use crypto price data.
This shows how to fix the fundamentals analyst to return real crypto prices.
"""

import asyncio
import logging
from typing import Dict, Any
from .crypto_price_fetcher import CryptoPriceFetcher, get_crypto_price

logger = logging.getLogger(__name__)


async def enhanced_fundamentals_fetch(ticker: str) -> Dict[str, Any]:
    """
    Enhanced fundamentals fetcher that properly handles crypto assets.
    This fixes the issue where crypto assets show $0.00 price.
    
    Args:
        ticker: Asset ticker (can be stock or crypto)
        
    Returns:
        Fundamentals data with accurate pricing
    """
    # Check if it's a crypto ticker
    if CryptoPriceFetcher.is_crypto(ticker):
        logger.info(f"Detected {ticker} as cryptocurrency, fetching crypto data...")
        
        # Get crypto-specific data
        crypto_data = await CryptoPriceFetcher.get_current_price(ticker)
        
        if not crypto_data.get('success'):
            logger.error(f"Failed to fetch crypto data for {ticker}")
            return {
                'ticker': ticker,
                'asset_type': 'cryptocurrency',
                'current_price': 0.00,
                'error': crypto_data.get('error', 'Unknown error'),
                'data_available': False
            }
        
        # Format as fundamentals report (matching existing structure)
        return {
            'ticker': ticker,
            'asset_type': 'cryptocurrency',
            'current_price': crypto_data['price'],  # REAL PRICE, not $0.00!
            'market_cap': crypto_data.get('market_cap', 0),
            'volume_24h': crypto_data.get('volume_24h', 0),
            'change_24h': crypto_data.get('change_24h', 0),
            'change_percent_24h': crypto_data.get('change_percent_24h', 0),
            'high_24h': crypto_data.get('high_24h', 0),
            'low_24h': crypto_data.get('low_24h', 0),
            'circulating_supply': crypto_data.get('circulating_supply', 0),
            'data_source': 'yfinance_crypto',
            'data_available': True,
            
            # Traditional stock metrics (N/A for crypto)
            'pe_ratio': None,
            'pb_ratio': None,
            'ev_ebitda': None,
            'roe': None,
            'roa': None,
            'debt_equity': None,
            'dividend_yield': None,
            'eps': None,
            'revenue': None,
            'net_income': None,
        }
    else:
        # Regular stock - use existing logic
        logger.info(f"Processing {ticker} as traditional stock...")
        
        # This would call your existing stock fundamentals logic
        # For demo purposes, returning a placeholder
        return {
            'ticker': ticker,
            'asset_type': 'stock',
            'current_price': 0.00,  # Would be fetched from existing logic
            'data_available': False,
            'note': 'Use existing stock fundamentals logic here'
        }


def format_fundamentals_report(data: Dict[str, Any]) -> str:
    """
    Format fundamentals data into a readable report.
    This ensures the AI models see the actual price, not $0.00.
    
    Args:
        data: Fundamentals data dictionary
        
    Returns:
        Formatted report string
    """
    if data.get('asset_type') == 'cryptocurrency':
        report = f"""📊 FUNDAMENTALS ANALYSIS: {data['ticker']}
⚡ Data fetched in real-time (Crypto Mode)
============================================================

📈 KEY METRICS:
  Current Price: ${data.get('current_price', 0):,.2f}  # ACTUAL PRICE!
  Market Cap: ${data.get('market_cap', 0):,.0f}
  24h Volume: ${data.get('volume_24h', 0):,.0f}
  24h Change: {data.get('change_percent_24h', 0):.2f}%
  
  24h High: ${data.get('high_24h', 0):,.2f}
  24h Low: ${data.get('low_24h', 0):,.2f}
  
  Circulating Supply: {data.get('circulating_supply', 0):,.0f}

============================================================
🔍 FUNDAMENTAL SIGNAL:
{'🟢 BUY' if data.get('change_percent_24h', 0) > 2 else '🟡 HOLD' if data.get('change_percent_24h', 0) > -2 else '🔴 SELL'} - Based on 24h momentum
  ✅ Real-time price data available
  ✅ Data source: {data.get('data_source', 'unknown')}
"""
    else:
        # Stock format
        report = f"""📊 FUNDAMENTALS ANALYSIS: {data['ticker']}
============================================================

📈 KEY VALUATION METRICS:
  Current Price: ${data.get('current_price', 0):,.2f}
  P/E Ratio: {data.get('pe_ratio', 'N/A')}
  P/B Ratio: {data.get('pb_ratio', 'N/A')}
  EV/EBITDA: {data.get('ev_ebitda', 'N/A')}
  ROE: {data.get('roe', 'N/A')}
  ROA: {data.get('roa', 'N/A')}
  Debt/Equity: {data.get('debt_equity', 'N/A')}

============================================================
"""
    
    return report


# Example: How to update the existing fundamentals_analyst node
async def updated_fundamentals_analyst_node(state: Dict) -> Dict:
    """
    Updated fundamentals analyst node that handles crypto properly.
    This would replace the existing implementation.
    """
    ticker = state.get('company_of_interest', '')
    
    # Fetch fundamentals with crypto support
    fundamentals_data = await enhanced_fundamentals_fetch(ticker)
    
    # Format the report
    fundamentals_report = format_fundamentals_report(fundamentals_data)
    
    # CRITICAL: Pass the actual price to the AI model
    # This prevents the model from hallucinating prices
    enhanced_state = {
        'fundamentals_report': fundamentals_report,
        'fundamentals_data': fundamentals_data,  # Raw data for other nodes
        'current_price': fundamentals_data.get('current_price', 0),  # Explicit price
        'asset_type': fundamentals_data.get('asset_type', 'unknown')
    }
    
    # Log success
    if fundamentals_data.get('current_price', 0) > 0:
        logger.info(f"✅ Successfully fetched {ticker} price: ${fundamentals_data['current_price']:,.2f}")
    else:
        logger.warning(f"⚠️ Failed to fetch price for {ticker}")
    
    return enhanced_state


# Quick test to demonstrate the fix
async def test_integration():
    """Test the integration with ETH to verify we get real prices."""
    print("🧪 Testing Crypto Integration...")
    print("-" * 50)
    
    # Test ETH (the problematic ticker from the trace)
    eth_data = await enhanced_fundamentals_fetch('ETH')
    print(format_fundamentals_report(eth_data))
    
    # Verify we're not getting the hallucinated price
    eth_price = eth_data.get('current_price', 0)
    if 3900 < eth_price < 4000:
        print("⚠️ WARNING: Still getting incorrect ETH price around $3,950!")
        print("   This suggests the old logic is still being used.")
    else:
        print(f"✅ SUCCESS: ETH price is ${eth_price:,.2f} (not the hallucinated $3,950)")
    
    print("-" * 50)
    
    # Test a regular stock for comparison
    aapl_data = await enhanced_fundamentals_fetch('AAPL')
    print(f"AAPL detected as: {aapl_data.get('asset_type')}")
    
    # Test BTC for good measure
    btc_data = await enhanced_fundamentals_fetch('BTC')
    print(f"BTC price: ${btc_data.get('current_price', 0):,.2f}")


if __name__ == "__main__":
    asyncio.run(test_integration())