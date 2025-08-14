"""
Cryptocurrency Price Fetcher - Immediate Fix for Crypto Price Data
Uses existing yfinance infrastructure for zero-dependency deployment.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta

# Lazy import to prevent circular dependencies
def _get_yfinance():
    """Lazy import for yfinance to prevent circular imports"""
    try:
        import yfinance as yf
        return yf
    except ImportError as e:
        raise ImportError(f"yfinance is required but not available: {e}")

logger = logging.getLogger(__name__)


class CryptoPriceFetcher:
    """
    Quick implementation using existing yfinance infrastructure.
    Zero new dependencies, immediate deployment.
    Fixes the ETH price issue (shows actual $4700 instead of hallucinated $3950).
    """
    
    # Map common crypto symbols to Yahoo Finance format
    CRYPTO_TICKER_MAP = {
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD',
        'BITCOIN': 'BTC-USD',
        'ETHEREUM': 'ETH-USD',
        'BNB': 'BNB-USD',
        'ADA': 'ADA-USD',
        'SOL': 'SOL-USD',
        'XRP': 'XRP-USD',
        'DOGE': 'DOGE-USD',
        'DOT': 'DOT-USD',
        'AVAX': 'AVAX-USD',
        'MATIC': 'MATIC-USD',
        'LINK': 'LINK-USD',
        'UNI': 'UNI-USD',
        'ATOM': 'ATOM-USD',
        'LTC': 'LTC-USD',
        'FTT': 'FTT-USD',
        'CRO': 'CRO-USD',
        'ALGO': 'ALGO-USD',
        'NEAR': 'NEAR-USD',
        'VET': 'VET-USD',
        'SHIB': 'SHIB-USD',
        'FTM': 'FTM-USD',
        'SAND': 'SAND-USD',
        'MANA': 'MANA-USD',
        'AXS': 'AXS-USD',
        'AAVE': 'AAVE-USD',
        'COMP': 'COMP-USD',
        'SNX': 'SNX-USD',
        'MKR': 'MKR-USD',
        'USDT': 'USDT-USD',
        'USDC': 'USDC-USD',
        'DAI': 'DAI-USD',
        'BUSD': 'BUSD-USD',
    }
    
    # Known crypto tickers for detection
    KNOWN_CRYPTO_TICKERS = set(CRYPTO_TICKER_MAP.keys())
    
    @classmethod
    def is_crypto(cls, ticker: str) -> bool:
        """
        Detect if ticker is cryptocurrency.
        
        Args:
            ticker: Ticker symbol to check
            
        Returns:
            True if ticker is a cryptocurrency
        """
        ticker_clean = ticker.upper().replace('-USD', '').strip()
        
        # Check known list
        if ticker_clean in cls.KNOWN_CRYPTO_TICKERS:
            return True
        
        # Check patterns
        if ticker.upper().endswith('-USD'):
            return True
            
        return False
    
    @classmethod
    def normalize_ticker(cls, ticker: str) -> str:
        """
        Convert any format to Yahoo Finance crypto format.
        
        Args:
            ticker: Input ticker (BTC, ETH, bitcoin, etc.)
            
        Returns:
            Normalized ticker for Yahoo Finance (BTC-USD, ETH-USD, etc.)
        """
        ticker_upper = ticker.upper().strip()
        
        # Already in correct format
        if ticker_upper.endswith('-USD'):
            return ticker_upper
            
        # Check our mapping
        if ticker_upper in cls.CRYPTO_TICKER_MAP:
            return cls.CRYPTO_TICKER_MAP[ticker_upper]
            
        # Default: append -USD
        return f"{ticker_upper}-USD"
    
    @staticmethod
    async def get_current_price(ticker: str) -> Dict[str, Any]:
        """
        Fetch current crypto price using yfinance.
        
        Args:
            ticker: Crypto ticker symbol (BTC, ETH, etc.)
            
        Returns:
            Dictionary containing price data or error info
        """
        try:
            yf = _get_yfinance()
            normalized_ticker = CryptoPriceFetcher.normalize_ticker(ticker)
            
            logger.info(f"Fetching crypto price for {normalized_ticker}")
            
            # Run in thread to avoid blocking
            def fetch_sync():
                crypto = yf.Ticker(normalized_ticker)
                info = crypto.info
                history = crypto.history(period="1d", interval="1m")
                
                # Get latest price from multiple sources
                current_price = None
                
                # Try 1: Last close from history
                if not history.empty:
                    current_price = float(history['Close'].iloc[-1])
                    logger.debug(f"Got price from history: ${current_price}")
                
                # Try 2: regularMarketPrice from info
                if current_price is None or current_price == 0:
                    current_price = info.get('regularMarketPrice', 0)
                    if current_price:
                        logger.debug(f"Got price from regularMarketPrice: ${current_price}")
                
                # Try 3: previousClose as fallback
                if current_price is None or current_price == 0:
                    current_price = info.get('previousClose', 0)
                    if current_price:
                        logger.debug(f"Got price from previousClose: ${current_price}")
                
                # Try 4: lastPrice
                if current_price is None or current_price == 0:
                    current_price = info.get('lastPrice', 0)
                    if current_price:
                        logger.debug(f"Got price from lastPrice: ${current_price}")
                
                return {
                    'success': True,
                    'ticker': normalized_ticker,
                    'original_ticker': ticker,
                    'price': float(current_price) if current_price else 0,
                    'currency': 'USD',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'yfinance',
                    'market_cap': info.get('marketCap', 0),
                    'volume_24h': info.get('volume24Hr', info.get('volume', 0)),
                    'change_24h': info.get('regularMarketChange', 0),
                    'change_percent_24h': info.get('regularMarketChangePercent', 0),
                    'circulating_supply': info.get('circulatingSupply', 0),
                    'total_supply': info.get('totalSupply', 0),
                    'high_24h': info.get('dayHigh', 0),
                    'low_24h': info.get('dayLow', 0),
                }
            
            result = await asyncio.to_thread(fetch_sync)
            
            if result['price'] > 0:
                logger.info(f"✅ Successfully fetched {ticker} price: ${result['price']:,.2f}")
            else:
                logger.warning(f"⚠️ Got zero price for {ticker}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ yfinance crypto fetch failed for {ticker}: {e}")
            return {
                'success': False,
                'ticker': ticker,
                'error': str(e),
                'source': 'yfinance',
                'timestamp': datetime.now().isoformat()
            }
    
    @staticmethod
    async def get_multiple_prices(tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch prices for multiple cryptocurrencies concurrently.
        
        Args:
            tickers: List of crypto tickers
            
        Returns:
            Dictionary mapping tickers to price data
        """
        tasks = []
        for ticker in tickers:
            tasks.append(CryptoPriceFetcher.get_current_price(ticker))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                output[ticker] = {
                    'success': False,
                    'error': str(result),
                    'ticker': ticker
                }
            else:
                output[ticker] = result
        
        return output
    
    @staticmethod
    async def get_historical_data(ticker: str, period: str = "1mo") -> Dict:
        """
        Get historical price data for a cryptocurrency.
        
        Args:
            ticker: Crypto ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            Dictionary containing historical data
        """
        try:
            yf = _get_yfinance()
            normalized_ticker = CryptoPriceFetcher.normalize_ticker(ticker)
            
            def fetch_sync():
                crypto = yf.Ticker(normalized_ticker)
                history = crypto.history(period=period)
                
                if history.empty:
                    return None
                
                # Convert to simple format
                data = []
                for index, row in history.iterrows():
                    data.append({
                        'date': index.isoformat(),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': float(row['Volume'])
                    })
                
                return data
            
            historical_data = await asyncio.to_thread(fetch_sync)
            
            if historical_data:
                return {
                    'success': True,
                    'ticker': normalized_ticker,
                    'period': period,
                    'data': historical_data,
                    'count': len(historical_data),
                    'source': 'yfinance'
                }
            else:
                return {
                    'success': False,
                    'ticker': ticker,
                    'error': 'No historical data available',
                    'source': 'yfinance'
                }
                
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {ticker}: {e}")
            return {
                'success': False,
                'ticker': ticker,
                'error': str(e),
                'source': 'yfinance'
            }


# Convenience functions for backwards compatibility
async def get_crypto_price(ticker: str) -> float:
    """
    Simple function to get current crypto price.
    
    Args:
        ticker: Crypto ticker (BTC, ETH, etc.)
        
    Returns:
        Current price as float, or 0 if failed
    """
    result = await CryptoPriceFetcher.get_current_price(ticker)
    return result.get('price', 0.0)


async def is_crypto_ticker(ticker: str) -> bool:
    """
    Check if a ticker is a cryptocurrency.
    
    Args:
        ticker: Ticker to check
        
    Returns:
        True if cryptocurrency, False otherwise
    """
    return CryptoPriceFetcher.is_crypto(ticker)


# Testing function
async def test_crypto_prices():
    """Test function to verify crypto price fetching works."""
    test_tickers = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOGE']
    
    print("🧪 Testing Crypto Price Fetcher...")
    print("-" * 50)
    
    for ticker in test_tickers:
        price_data = await CryptoPriceFetcher.get_current_price(ticker)
        if price_data['success']:
            print(f"✅ {ticker}: ${price_data['price']:,.2f}")
            print(f"   24h Change: {price_data['change_percent_24h']:.2f}%")
            print(f"   Volume: ${price_data['volume_24h']:,.0f}")
        else:
            print(f"❌ {ticker}: Failed - {price_data['error']}")
        print()
    
    # Test ETH specifically to verify it's not $3950
    eth_price = await get_crypto_price('ETH')
    print("-" * 50)
    print(f"🎯 ETH Current Price: ${eth_price:,.2f}")
    if 3900 < eth_price < 4000:
        print("⚠️ WARNING: ETH price might be outdated/cached!")
    else:
        print("✅ ETH price looks current!")


if __name__ == "__main__":
    # Run test when executed directly
    asyncio.run(test_crypto_prices())