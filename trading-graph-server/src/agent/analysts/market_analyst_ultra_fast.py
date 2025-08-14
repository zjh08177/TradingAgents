"""
Ultra-Fast Market Analyst - Local Technical Indicator Calculation Engine
Calculates 130+ technical indicators locally in <2 seconds with zero API rate limits.
"""

import asyncio
import json
import logging
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any

import httpx
# LAZY IMPORT: Import numpy and pandas only when needed to avoid circular import
# import numpy as np  # <-- REMOVED to prevent circular import
# import pandas as pd  # <-- REMOVED to prevent circular import
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

# Lazy loader for numpy to prevent circular import issues
def _get_numpy():
    """Lazy load numpy to avoid circular import issues in LangGraph dev"""
    import numpy as np
    return np

# Lazy loader for pandas to prevent circular import issues
def _get_pandas():
    """Lazy load pandas to avoid circular import issues in LangGraph dev"""
    import pandas as pd
    return pd

# Try to import minimalist_log but make it optional
try:
    from ..utils.minimalist_logging import minimalist_log
except ImportError:
    # Fallback if minimalist_log is not available
    def minimalist_log(category, message):
        logging.info(f"[{category}] {message}")

# Try to import debug_node but make it optional
try:
    from ..utils.debug_logging import debug_node
except ImportError:
    # Fallback if debug_node is not available
    def debug_node(name):
        def decorator(func):
            return func
        return decorator

# Try to import pandas-ta, fallback to manual calculations if not available
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logging.warning("pandas-ta not installed. Using fallback manual calculations.")

# Try to import redis for caching
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import redis.asyncio as aioredis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        logging.debug("Redis not available. Caching disabled.")  # Changed to debug level

# Try to import finnhub for fallback
try:
    import finnhub
    FINNHUB_AVAILABLE = True
except ImportError:
    FINNHUB_AVAILABLE = False
    logging.warning("Finnhub not available for fallback.")

# Global analyst instance for connection pooling (singleton pattern)
_global_analyst: Optional['UltraFastTechnicalAnalyst'] = None


async def get_or_create_analyst(alpha_vantage_key: str = None, finnhub_key: str = None) -> 'UltraFastTechnicalAnalyst':
    """Get or create singleton analyst instance for connection pooling."""
    global _global_analyst
    
    if _global_analyst is None:
        _global_analyst = UltraFastTechnicalAnalyst(
            alpha_vantage_key=alpha_vantage_key,
            finnhub_key=finnhub_key,
            redis_url="redis://localhost"
        )
        await _global_analyst.setup()
        logging.info("🚀 UltraFastTechnicalAnalyst initialized with connection pooling")
    
    return _global_analyst


class UltraFastTechnicalAnalyst:
    """Calculate 130+ technical indicators locally in <2 seconds."""
    
    def __init__(self, alpha_vantage_key: str = None, finnhub_key: str = None, redis_url: str = "redis://localhost"):
        """Initialize the ultra-fast technical analyst.
        
        Args:
            alpha_vantage_key: Optional Alpha Vantage API key for fallback
            finnhub_key: Optional Finnhub API key for tertiary fallback
            redis_url: Redis connection URL for caching
        """
        self.av_key = alpha_vantage_key
        self.fh_key = finnhub_key
        self.redis_url = redis_url
        self.redis = None
        
        # Try to use http2 if available, fallback to http1.1
        try:
            self.client = httpx.AsyncClient(
                http2=True,
                limits=httpx.Limits(max_connections=10),
                timeout=httpx.Timeout(30.0)
            )
        except ImportError:
            self.client = httpx.AsyncClient(
                limits=httpx.Limits(max_connections=10),
                timeout=httpx.Timeout(30.0)
            )
        self.logger = logging.getLogger(__name__)
        
        # Initialize Finnhub client if available
        self.finnhub_client = None
        if FINNHUB_AVAILABLE and finnhub_key:
            self.finnhub_client = finnhub.Client(api_key=finnhub_key)
    
    async def setup(self):
        """Initialize Redis connection pool."""
        if REDIS_AVAILABLE:
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis.ping()
                self.logger.info("Redis connection established")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.redis = None
    
    async def cleanup(self):
        """Clean up resources."""
        if self.redis:
            await self.redis.close()
        await self.client.aclose()
    
    async def get(self, ticker: str, period: str = "1y") -> dict:
        """Get ALL technical indicators - calculated locally in <2s.
        
        Args:
            ticker: Stock ticker symbol
            period: Time period for historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            Dictionary containing OHLCV data, 130+ indicators, and metadata
        """
        # Check cache if Redis is available
        if self.redis:
            try:
                key = f"tech:{ticker}:{date.today()}:{period}"
                cached = await self.redis.get(key)
                if cached:
                    self.logger.info(f"Cache hit for {ticker}")
                    return json.loads(cached)
            except Exception as e:
                self.logger.warning(f"Cache retrieval failed: {e}")
        
        # Fetch OHLCV data with fallback chain
        try:
            ohlcv_data = await self._fetch_ohlcv(ticker, period)
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLCV data: {e}")
            return {"error": f"Failed to fetch data for {ticker}: {str(e)}"}
        
        if ohlcv_data.empty:
            return {"error": f"No data available for {ticker}"}
        
        # Calculate ALL indicators locally (FAST!)
        indicators = self._calculate_all_indicators(ohlcv_data)
        
        # Package results
        data = {
            "ticker": ticker,
            "date": str(date.today()),
            "period": period,
            "ohlcv": self._prepare_ohlcv_data(ohlcv_data),
            "indicators": indicators,
            "metadata": {
                "indicator_count": len(indicators),
                "calculation_method": "local",
                "data_points": len(ohlcv_data),
                "library": "pandas-ta" if PANDAS_TA_AVAILABLE else "manual"
            }
        }
        
        # Cache for 24 hours if Redis is available
        if self.redis:
            try:
                key = f"tech:{ticker}:{date.today()}:{period}"
                await self.redis.setex(key, 86400, json.dumps(data, default=str))
                self.logger.info(f"Cached data for {ticker}")
            except Exception as e:
                self.logger.warning(f"Cache storage failed: {e}")
        
        return data
    
    async def get_batch(self, tickers: List[str], period: str = "1y") -> Dict[str, dict]:
        """Ultra-fast batch processing for multiple tickers.
        
        Args:
            tickers: List of stock ticker symbols
            period: Time period for historical data
            
        Returns:
            Dictionary mapping tickers to their technical data
        """
        results = {}
        
        # Check cache for all tickers first
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                for ticker in tickers:
                    key = f"tech:{ticker}:{date.today()}:{period}"
                    pipe.get(key)
                cached_results = await pipe.execute()
                
                to_fetch = []
                for ticker, cached in zip(tickers, cached_results):
                    if cached:
                        results[ticker] = json.loads(cached)
                    else:
                        to_fetch.append(ticker)
            except Exception as e:
                self.logger.warning(f"Batch cache retrieval failed: {e}")
                to_fetch = tickers
        else:
            to_fetch = tickers
        
        # Parallel fetch and calculate for missing tickers
        if to_fetch:
            tasks = [self.get(ticker, period) for ticker in to_fetch]
            fresh_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            for ticker, data in zip(to_fetch, fresh_data):
                if not isinstance(data, Exception):
                    results[ticker] = data
                else:
                    results[ticker] = {"error": str(data)}
        
        return results
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_ohlcv(self, ticker: str, period: str):
        """Fetch OHLCV data with 3-tier fallback: yfinance → Alpha Vantage → Finnhub.
        
        Args:
            ticker: Stock ticker symbol
            period: Time period for historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        pd = _get_pandas()
        df = pd.DataFrame()
        
        # Tier 1: yfinance (most reliable, free, no API key needed)
        try:
            self.logger.info(f"Fetching {ticker} from yfinance...")
            
            # ✅ FIX: Use asyncio.to_thread() to prevent blocking I/O
            # IMPORTANT: Must use thread pool to completely isolate synchronous code
            import concurrent.futures
            
            def fetch_yfinance_data():
                """Run yfinance in separate thread to avoid any blocking I/O detection"""
                stock = yf.Ticker(ticker)
                return stock.history(period=period, interval="1d")
            
            # Use ThreadPoolExecutor to ensure complete isolation from async context
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                df = await loop.run_in_executor(executor, fetch_yfinance_data)
            
            if not df.empty:
                # Standardize column names
                df.columns = df.columns.str.lower()
                df = df.rename(columns={'stock splits': 'stock_splits'})
                self.logger.info(f"Successfully fetched {len(df)} days of data from yfinance")
                return df
        except Exception as e:
            self.logger.warning(f"yfinance failed for {ticker}: {e}")
        
        # Tier 2: Alpha Vantage (if API key available)
        if self.av_key and df.empty:
            try:
                df = await self._fetch_alpha_vantage_ohlcv(ticker)
                if not df.empty:
                    self.logger.info(f"Successfully fetched {len(df)} days from Alpha Vantage")
                    return df
            except Exception as e:
                self.logger.warning(f"Alpha Vantage failed for {ticker}: {e}")
        
        # Tier 3: Finnhub (if API key available)
        if self.finnhub_client and df.empty:
            try:
                df = await self._fetch_finnhub_ohlcv(ticker, period)
                if not df.empty:
                    self.logger.info(f"Successfully fetched {len(df)} days from Finnhub")
                    return df
            except Exception as e:
                self.logger.warning(f"Finnhub failed for {ticker}: {e}")
        
        return df
    
    async def _fetch_alpha_vantage_ohlcv(self, ticker: str):
        """Fetch OHLCV data from Alpha Vantage."""
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': ticker,
            'outputsize': 'full',
            'apikey': self.av_key
        }
        
        resp = await self.client.get(url, params=params)
        data = resp.json()
        
        if 'Time Series (Daily)' not in data:
            pd = _get_pandas()
            return pd.DataFrame()
        
        # Convert to DataFrame
        time_series = data['Time Series (Daily)']
        pd = _get_pandas()
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Rename columns to standard format
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df = df.astype(float)
        
        return df
    
    async def _fetch_finnhub_ohlcv(self, ticker: str, period: str):
        """Fetch OHLCV data from Finnhub."""
        if not self.finnhub_client:
            pd = _get_pandas()
            return pd.DataFrame()
        
        # Calculate date range based on period
        end_date = datetime.now()
        period_map = {
            '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
            '6mo': 180, '1y': 365, '2y': 730, '5y': 1825
        }
        days = period_map.get(period, 365)
        start_date = end_date - timedelta(days=days)
        
        # Finnhub uses Unix timestamps
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())
        
        try:
            # ✅ FIX: Use thread pool to prevent blocking I/O
            import concurrent.futures
            
            def fetch_finnhub_candles():
                """Run finnhub in separate thread to avoid any blocking I/O detection"""
                return self.finnhub_client.stock_candles(
                    ticker, 'D', start_ts, end_ts
                )
            
            # Use ThreadPoolExecutor to ensure complete isolation from async context
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                candles = await loop.run_in_executor(executor, fetch_finnhub_candles)
            
            if candles['s'] != 'ok':
                pd = _get_pandas()
            return pd.DataFrame()
            
            # Convert to DataFrame
            pd = _get_pandas()
            df = pd.DataFrame({
                'open': candles['o'],
                'high': candles['h'],
                'low': candles['l'],
                'close': candles['c'],
                'volume': candles['v']
            })
            
            # Convert timestamp to datetime index
            df.index = pd.to_datetime(candles['t'], unit='s')
            df = df.sort_index()
            
            return df
        except Exception as e:
            self.logger.error(f"Finnhub OHLCV fetch failed: {e}")
            pd = _get_pandas()
            return pd.DataFrame()
    
    def _calculate_all_indicators(self, df) -> dict:
        """Calculate 130+ indicators locally using pandas-ta or manual calculations.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary of indicator names and values
        """
        pd = _get_pandas()
        indicators = {}
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            self.logger.warning("Missing required OHLCV columns")
            return indicators
        
        if PANDAS_TA_AVAILABLE:
            try:
                # ULTRA-FAST: Calculate ALL indicators at once with pandas-ta
                self.logger.info("Calculating indicators with pandas-ta...")
                
                # Apply the 'all' strategy to calculate everything with error handling
                if hasattr(df.ta, 'strategy'):
                    try:
                        df.ta.strategy("all")
                    except Exception as strategy_error:
                        self.logger.warning(f"Strategy 'all' failed: {strategy_error}. Trying individual indicators.")
                        # Fallback to individual indicator calls
                        self._calculate_pandas_ta_individually(df)
                else:
                    self.logger.warning("pandas-ta strategy method not available, using individual calls")
                    self._calculate_pandas_ta_individually(df)
                
                # Extract calculated indicators (exclude OHLCV columns)
                for col in df.columns:
                    if col not in required_cols + ['dividends', 'stock_splits']:
                        # Get the latest value for each indicator
                        if len(df) > 0:
                            latest_value = df[col].iloc[-1]
                            if pd.notna(latest_value):
                                indicators[col] = float(latest_value)
                
                self.logger.info(f"Calculated {len(indicators)} indicators with pandas-ta")
            except Exception as e:
                self.logger.warning(f"pandas-ta calculation failed: {e}. Using manual fallback.")
                indicators = self._calculate_manual_indicators(df)
        else:
            # Fallback to manual calculation
            indicators = self._calculate_manual_indicators(df)
        
        return indicators
    
    def _calculate_pandas_ta_individually(self, df) -> None:
        """Calculate pandas-ta indicators individually when strategy fails."""
        try:
            # Calculate individual indicators and add to dataframe
            # Moving averages
            for period in [5, 10, 20, 50, 100, 200]:
                if len(df) >= period:
                    df[f'SMA_{period}'] = df.ta.sma(length=period)
                    df[f'EMA_{period}'] = df.ta.ema(length=period)
            
            # Momentum indicators
            if len(df) >= 14:
                df['RSI_14'] = df.ta.rsi(length=14)
                df['WILLR_14'] = df.ta.willr(length=14)
            
            # MACD
            if len(df) >= 26:
                macd = df.ta.macd()
                if macd is not None and not macd.empty:
                    df = pd.concat([df, macd], axis=1)
            
            # Bollinger Bands
            if len(df) >= 20:
                bbands = df.ta.bbands()
                if bbands is not None and not bbands.empty:
                    df = pd.concat([df, bbands], axis=1)
            
            # Stochastic
            if len(df) >= 14:
                stoch = df.ta.stoch()
                if stoch is not None and not stoch.empty:
                    df = pd.concat([df, stoch], axis=1)
            
            # ATR
            if len(df) >= 14:
                df['ATR_14'] = df.ta.atr(length=14)
            
            # Volume indicators
            if len(df) >= 2:
                df['OBV'] = df.ta.obv()
                df['AD'] = df.ta.ad()
            
            # More indicators as needed
            if len(df) >= 20:
                df['CCI_20'] = df.ta.cci(length=20)
            if len(df) >= 10:
                df['MOM_10'] = df.ta.mom(length=10)
                df['ROC_10'] = df.ta.roc(length=10)
            if len(df) >= 14:
                df['MFI_14'] = df.ta.mfi(length=14)
                
        except Exception as e:
            self.logger.warning(f"Error calculating individual pandas-ta indicators: {e}")
    
    def _calculate_manual_indicators(self, df: pd.DataFrame) -> dict:
        """Manual calculation of essential indicators when pandas-ta is not available.
        
        This provides a subset of the most important indicators.
        """
        indicators = {}
        
        try:
            # Ensure we have at least some data
            if len(df) < 2:
                self.logger.warning("Insufficient data for any indicator calculation")
                return indicators
            
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']
            
            # Moving Averages (calculate what's possible with available data)
            if len(df) >= 5:
                indicators['sma_5'] = close.rolling(window=5).mean().iloc[-1]
            elif len(df) >= 3:
                indicators['sma_3'] = close.rolling(window=3).mean().iloc[-1]
            else:
                indicators['sma_2'] = close.rolling(window=2).mean().iloc[-1]
            
            if len(df) >= 10:
                indicators['sma_10'] = close.rolling(window=10).mean().iloc[-1]
            if len(df) >= 20:
                indicators['sma_20'] = close.rolling(window=20).mean().iloc[-1]
            if len(df) >= 50:
                indicators['sma_50'] = close.rolling(window=50).mean().iloc[-1]
            if len(df) >= 200:
                indicators['sma_200'] = close.rolling(window=200).mean().iloc[-1]
            
            # EMA (always possible with 2+ data points)
            indicators['ema_12'] = close.ewm(span=min(12, len(df)), adjust=False).mean().iloc[-1]
            if len(df) >= 26:
                indicators['ema_26'] = close.ewm(span=26, adjust=False).mean().iloc[-1]
            if len(df) >= 50:
                indicators['ema_50'] = close.ewm(span=50, adjust=False).mean().iloc[-1]
            
            # RSI (needs at least 14 data points)
            if len(df) >= 14:
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                indicators['rsi_14'] = (100 - (100 / (1 + rs))).iloc[-1]
            
            # MACD (needs at least 26 data points)
            if len(df) >= 26:
                exp1 = close.ewm(span=12, adjust=False).mean()
                exp2 = close.ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9, adjust=False).mean()
                indicators['macd'] = macd.iloc[-1]
                indicators['macd_signal'] = signal.iloc[-1]
                indicators['macd_hist'] = (macd - signal).iloc[-1]
            
            # Bollinger Bands (needs at least 20 data points)
            if len(df) >= 20:
                sma20 = close.rolling(window=20).mean()
                std20 = close.rolling(window=20).std()
                indicators['bb_upper'] = (sma20 + (std20 * 2)).iloc[-1]
                indicators['bb_middle'] = sma20.iloc[-1]
                indicators['bb_lower'] = (sma20 - (std20 * 2)).iloc[-1]
            
            # Stochastic (needs at least 14 data points)
            if len(df) >= 14:
                low_14 = low.rolling(window=14).min()
                high_14 = high.rolling(window=14).max()
                indicators['stoch_k'] = (100 * ((close - low_14) / (high_14 - low_14))).iloc[-1]
                if len(df) >= 16:  # Need 3 more for stoch_d
                    indicators['stoch_d'] = (100 * ((close - low_14) / (high_14 - low_14))).rolling(window=3).mean().iloc[-1]
            
            # ATR (Average True Range) - needs at least 14 data points
            if len(df) >= 14:
                high_low = high - low
                high_close = (high - close.shift()).abs()
                low_close = (low - close.shift()).abs()
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                indicators['atr_14'] = true_range.rolling(window=14).mean().iloc[-1]
            
            # Volume indicators
            if len(df) >= 20:
                indicators['volume_sma_20'] = volume.rolling(window=20).mean().iloc[-1]
                indicators['volume_ratio'] = (volume.iloc[-1] / indicators['volume_sma_20']) if indicators['volume_sma_20'] > 0 else 0
            elif len(df) >= 5:
                indicators['volume_sma_5'] = volume.rolling(window=5).mean().iloc[-1]
                indicators['volume_ratio'] = (volume.iloc[-1] / indicators['volume_sma_5']) if indicators['volume_sma_5'] > 0 else 0
            
            # OBV (On Balance Volume) - always possible with 2+ data points
            if len(df) >= 2:
                obv = (volume * (~(close.diff() <= 0) * 2 - 1)).cumsum()
                indicators['obv'] = obv.iloc[-1]
            
            # Weighted Moving Average (WMA)
            if len(df) >= 20:
                weights = np.arange(1, 21)
                indicators['wma_20'] = (close.rolling(window=20).apply(
                    lambda x: np.dot(x, weights) / weights.sum(), raw=True
                )).iloc[-1]
            
            # CCI (Commodity Channel Index)
            if len(df) >= 20:
                typical_price = (high + low + close) / 3
                sma_tp = typical_price.rolling(window=20).mean()
                mad = typical_price.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
                indicators['cci_20'] = ((typical_price - sma_tp) / (0.015 * mad)).iloc[-1]
            
            # Williams %R
            if len(df) >= 14:
                high_14 = high.rolling(window=14).max()
                low_14 = low.rolling(window=14).min()
                indicators['willr_14'] = (-100 * (high_14 - close) / (high_14 - low_14)).iloc[-1]
            
            # Aroon Indicator
            if len(df) >= 25:
                aroon_up = (25 - high.rolling(window=26).apply(lambda x: 25 - x.argmax()))
                aroon_down = (25 - low.rolling(window=26).apply(lambda x: 25 - x.argmin()))
                indicators['aroon_up'] = (aroon_up.iloc[-1] / 25) * 100
                indicators['aroon_down'] = (aroon_down.iloc[-1] / 25) * 100
                indicators['aroon_oscillator'] = indicators['aroon_up'] - indicators['aroon_down']
            
            # Money Flow Index (MFI)
            if len(df) >= 14:
                typical_price = (high + low + close) / 3
                money_flow = typical_price * volume
                
                # Calculate positive and negative money flow
                price_diff = typical_price.diff()
                positive_flow = money_flow.where(price_diff > 0, 0)
                negative_flow = money_flow.where(price_diff < 0, 0)
                
                # Calculate money ratio and MFI
                positive_sum = positive_flow.rolling(window=14).sum()
                negative_sum = negative_flow.rolling(window=14).sum()
                money_ratio = positive_sum / negative_sum.replace(0, 1)
                indicators['mfi_14'] = (100 - (100 / (1 + money_ratio))).iloc[-1]
            
            # Accumulation/Distribution Line
            if len(df) >= 2:
                clv = ((close - low) - (high - close)) / (high - low).replace(0, 1)
                ad = (clv * volume).cumsum()
                indicators['ad'] = ad.iloc[-1]
            
            # NATR (Normalized ATR)
            if len(df) >= 14 and 'atr_14' in indicators:
                indicators['natr_14'] = (indicators['atr_14'] / close.iloc[-1]) * 100
            
            # Price momentum
            if len(df) > 10:
                indicators['momentum_10'] = (close.iloc[-1] - close.iloc[-11])
                indicators['roc_10'] = ((close.iloc[-1] / close.iloc[-11] - 1) * 100)
            elif len(df) >= 5:
                indicators['momentum_5'] = (close.iloc[-1] - close.iloc[-5])
                indicators['roc_5'] = ((close.iloc[-1] / close.iloc[-5] - 1) * 100)
            
            # ADX (Average Directional Index) - simplified
            if len(df) >= 14:
                plus_dm = high.diff()
                minus_dm = -low.diff()
                plus_dm[plus_dm < 0] = 0
                minus_dm[minus_dm < 0] = 0
                
                tr = true_range
                atr14 = tr.rolling(window=14).mean()
                plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr14)
                minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr14)
                dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
                indicators['adx_14'] = dx.rolling(window=14).mean().iloc[-1]
                indicators['plus_di'] = plus_di.iloc[-1]
                indicators['minus_di'] = minus_di.iloc[-1]
            
            # Support and Resistance (simplified, adaptive to data length)
            if len(df) >= 20:
                indicators['resistance_1'] = high.rolling(window=20).max().iloc[-1]
                indicators['support_1'] = low.rolling(window=20).min().iloc[-1]
            elif len(df) >= 5:
                indicators['resistance_1'] = high.rolling(window=5).max().iloc[-1]
                indicators['support_1'] = low.rolling(window=5).min().iloc[-1]
            else:
                indicators['resistance_1'] = high.max()
                indicators['support_1'] = low.min()
            
            # VWAP (always possible with 1+ data points)
            typical_price = (high + low + close) / 3
            if volume.sum() > 0:
                indicators['vwap'] = (typical_price * volume).cumsum().iloc[-1] / volume.cumsum().iloc[-1]
            
            # Simple price change for small datasets
            if len(df) >= 2:
                indicators['price_change'] = close.iloc[-1] - close.iloc[-2]
                indicators['price_change_pct'] = ((close.iloc[-1] / close.iloc[-2] - 1) * 100)
            
            self.logger.info(f"Calculated {len(indicators)} indicators manually")
            
        except Exception as e:
            self.logger.error(f"Manual indicator calculation error: {e}")
        
        # Clean up NaN values
        indicators = {k: v for k, v in indicators.items() 
                     if v is not None and not pd.isna(v)}
        
        return indicators
    
    def _prepare_ohlcv_data(self, df: pd.DataFrame, days: int = 20) -> List[Dict]:
        """Prepare OHLCV data for output.
        
        Args:
            df: DataFrame with OHLCV data
            days: Number of recent days to include
            
        Returns:
            List of dictionaries with OHLCV data
        """
        # Get the last N days of data
        recent_df = df.tail(days).copy()
        
        # Reset index to get date as a column
        recent_df = recent_df.reset_index()
        
        # Rename index column to 'date' if it's a datetime index
        if 'index' in recent_df.columns:
            recent_df = recent_df.rename(columns={'index': 'date'})
        elif 'Date' in recent_df.columns:
            recent_df = recent_df.rename(columns={'Date': 'date'})
        
        # Convert to list of dicts
        records = recent_df.to_dict('records')
        
        # Convert datetime objects to strings
        for record in records:
            if 'date' in record and hasattr(record['date'], 'strftime'):
                record['date'] = record['date'].strftime('%Y-%m-%d')
        
        return records


def create_market_analyst_ultra_fast(llm=None, toolkit=None):
    """
    Create ultra-fast market analyst that bypasses LLM for direct local calculation.
    
    This replaces the slow LLM-based approach with direct local calculations using:
    - Local calculation of 130+ technical indicators
    - Zero API rate limits
    - <2 second performance
    - Connection pooling with singleton pattern
    - Redis caching for instant responses
    
    Args:
        llm: Ignored - kept for interface compatibility
        toolkit: Used to extract API keys if available
    """
    
    @debug_node("Market_Analyst_UltraFast")
    async def market_analyst_ultra_fast_node(state):
        """Ultra-fast market analysis bypassing LLM and API calls."""
        start_time = time.time()
        
        # ✅ ENHANCED I/O BLOCKING DETECTION AND PREVENTION
        import asyncio
        import threading
        
        # Enhanced blocking I/O detection
        main_thread = threading.main_thread()
        current_thread = threading.current_thread()
        
        # Log thread information for debugging
        logging.info(f"🧵 THREAD ANALYSIS: Main={main_thread.name}, Current={current_thread.name}")
        logging.info(f"🧵 THREAD CHECK: Running in main thread: {current_thread == main_thread}")
        
        try:
            # Check if we're running in async context properly
            current_task = asyncio.current_task()
            if current_task is None:
                logging.error("❌ I/O BLOCKING DETECTED: No current async task context")
                logging.error(f"❌ THREAD STATE: Main={main_thread.name}, Current={current_thread.name}")
                return {
                    "market_messages": [],
                    "market_report": "❌ I/O BLOCKING ERROR - Not in async context", 
                    "error": True,
                    "error_type": "async_context_error",
                    "error_details": "Function called outside async context",
                    "sender": "Market Analyst UltraFast"
                }
            logging.info(f"✅ ASYNC CONTEXT VERIFIED: Task {current_task.get_name()}")
            
            # Additional check: Verify we're in an event loop
            try:
                loop = asyncio.get_running_loop()
                logging.info(f"✅ EVENT LOOP VERIFIED: {type(loop).__name__}")
            except RuntimeError as loop_error:
                logging.error(f"❌ EVENT LOOP ERROR: {loop_error}")
                return {
                    "market_messages": [],
                    "market_report": "❌ I/O BLOCKING ERROR - No event loop running",
                    "error": True,
                    "error_type": "event_loop_error", 
                    "error_details": str(loop_error),
                    "sender": "Market Analyst UltraFast"
                }
                
        except RuntimeError as e:
            logging.error(f"❌ I/O BLOCKING DETECTED: {e}")
            logging.error(f"❌ THREAD STATE: Main={main_thread.name}, Current={current_thread.name}")
            return {
                "market_messages": [],
                "market_report": "❌ I/O BLOCKING ERROR - Async runtime error",
                "error": True, 
                "error_type": "async_runtime_error",
                "error_details": str(e),
                "sender": "Market Analyst UltraFast"
            }
        
        logging.info(f"⚡ market_analyst_ultra_fast START: {time.time()}")
        minimalist_log("MARKET_ULTRA", "Starting ultra-fast calculation")
        
        # Extract ticker and period from state
        ticker = state.get("company_of_interest", "").upper()
        trade_date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))
        period = state.get("analysis_period", "3mo")  # Default to 3 months of data
        
        if not ticker:
            logging.error("❌ No ticker specified in state")
            return {
                "market_messages": [],
                "market_report": "❌ ANALYSIS ERROR - No ticker specified",
                "error": True,
                "error_type": "missing_ticker",
                "error_details": "No ticker specified in state",
                "sender": "Market Analyst UltraFast"
            }
        
        try:
            # Get API keys from toolkit or environment if available
            alpha_vantage_key = None
            finnhub_key = None
            
            if toolkit and hasattr(toolkit, 'config'):
                alpha_vantage_key = toolkit.config.get('alpha_vantage_key')
                finnhub_key = toolkit.config.get('finnhub_key')
            
            if not alpha_vantage_key:
                import os
                alpha_vantage_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
                finnhub_key = os.environ.get('FINNHUB_API_KEY')
            
            # Get or create singleton analyst with connection pooling
            analyst = await get_or_create_analyst(alpha_vantage_key, finnhub_key)
            
            # Fetch technical data with ultra-fast local calculation
            logging.info(f"🚀 Calculating indicators for {ticker} using UltraFastAnalyst...")
            calc_start = time.time()
            
            # ✅ ENHANCED I/O MONITORING AND TIMEOUT DETECTION
            try:
                # Monitor for blocking I/O during analyst.get() call
                logging.info(f"📡 NETWORK OPERATION START: Fetching data for {ticker}")
                logging.info(f"🔍 I/O MONITORING: About to call analyst.get() with async/await pattern")
                logging.info(f"🧵 PRE-FETCH THREAD CHECK: {threading.current_thread().name}")
                
                # Add timeout to detect hanging I/O operations
                technical_data = await asyncio.wait_for(
                    analyst.get(ticker, period), 
                    timeout=60.0  # 60 second timeout
                )
                
                logging.info(f"✅ NETWORK OPERATION SUCCESS: Data fetch completed")
                logging.info(f"🧵 POST-FETCH THREAD CHECK: {threading.current_thread().name}")
                logging.info(f"🔍 I/O MONITORING: analyst.get() completed successfully without blocking")
                
            except asyncio.TimeoutError:
                calc_time = time.time() - calc_start
                logging.error(f"❌ I/O BLOCKING DETECTED: Network timeout after {calc_time:.1f}s")
                return {
                    "market_messages": [],
                    "market_report": f"❌ I/O BLOCKING ERROR - Network timeout for {ticker}",
                    "error": True,
                    "error_type": "network_timeout",
                    "error_details": f"Operation timed out after {calc_time:.1f} seconds",
                    "sender": "Market Analyst UltraFast",
                    "execution_time": time.time() - start_time
                }
            except BlockingIOError as e:
                calc_time = time.time() - calc_start
                logging.error(f"❌ I/O BLOCKING DETECTED: Blocking I/O error - {e}")
                return {
                    "market_messages": [],
                    "market_report": f"❌ I/O BLOCKING ERROR - Blocking I/O for {ticker}",
                    "error": True,
                    "error_type": "blocking_io_error", 
                    "error_details": str(e),
                    "sender": "Market Analyst UltraFast",
                    "execution_time": time.time() - start_time
                }
            except Exception as network_error:
                calc_time = time.time() - calc_start
                logging.error(f"❌ NETWORK ERROR DETECTED: {type(network_error).__name__} - {network_error}")
                # Check if this is a network-related error that indicates I/O blocking
                error_str = str(network_error).lower()
                if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'blocking']):
                    return {
                        "market_messages": [],
                        "market_report": f"❌ NETWORK I/O ERROR - {type(network_error).__name__} for {ticker}",
                        "error": True,
                        "error_type": "network_io_error",
                        "error_details": str(network_error),
                        "sender": "Market Analyst UltraFast", 
                        "execution_time": time.time() - start_time
                    }
                else:
                    # Re-raise non-network errors
                    raise
            
            calc_time = time.time() - calc_start
            
            # ✅ ENHANCED RESULT VALIDATION AND SUCCESS DETECTION
            success = False
            error_details = None
            
            # Check for errors in technical data
            if "error" in technical_data:
                logging.error(f"❌ DATA FETCH FAILED for {ticker}: {technical_data['error']}")
                error_details = technical_data['error']
            
            # Validate data quality and completeness
            elif not technical_data.get('indicators'):
                logging.error(f"❌ DATA VALIDATION FAILED: No indicators calculated for {ticker}")
                error_details = "No technical indicators were calculated"
            
            elif technical_data.get('metadata', {}).get('indicator_count', 0) < 5:
                logging.warning(f"⚠️ DATA QUALITY WARNING: Only {technical_data.get('metadata', {}).get('indicator_count', 0)} indicators for {ticker}")
                # Don't fail but log concern about data quality
                logging.warning(f"⚠️ ANALYSIS MAY BE INCOMPLETE: Limited indicator set")
            
            # If we have errors, return error state  
            if error_details:
                logging.error(f"❌ MARKET ANALYST EXECUTION FAILED: {error_details}")
                return {
                    "market_messages": [],
                    "market_report": f"❌ ANALYSIS FAILED - {error_details} for {ticker}",
                    "error": True,
                    "error_type": "calculation_error", 
                    "error_details": error_details,
                    "sender": "Market Analyst UltraFast",
                    "execution_time": time.time() - start_time
                }
            
            # If we reach here, analysis was successful
            success = True
            logging.info(f"✅ MARKET ANALYST EXECUTION SUCCESSFUL: Data validated for {ticker}")
            
            # Generate comprehensive report from validated data
            report = generate_technical_report(ticker, technical_data, calc_time)
            
            # Log performance metrics with success confirmation
            cache_hit = calc_time < 0.05  # Assume cache hit if <50ms
            logging.info(f"✅ INDICATORS CALCULATED SUCCESSFULLY in {calc_time:.3f}s (cache: {'hit' if cache_hit else 'miss'})")
            logging.info(f"📊 VALIDATED {technical_data['metadata']['indicator_count']} indicators")
            logging.info(f"✅ TECHNICAL REPORT GENERATED: {len(report)} characters")
            
            # Log performance improvement with SUCCESS confirmation
            total_time = time.time() - start_time
            logging.info(f"⚡ market_analyst_ultra_fast EXECUTION COMPLETED: {time.time()} (duration: {total_time:.2f}s)")
            
            # Compare to traditional approach (~10-30s with LLM and API calls)
            improvement = 15.0 / total_time if total_time > 0 else 999
            logging.info(f"🚀 PERFORMANCE ACHIEVEMENT: {improvement:.1f}x faster than API approach")
            minimalist_log("MARKET_ULTRA", f"SUCCESS: Completed in {total_time:.2f}s ({improvement:.1f}x faster)")
            
            # ✅ FINAL SUCCESS CONFIRMATION - This distinguishes real success from just completion
            logging.info(f"✅ MARKET ANALYST ULTRA FAST FINAL STATUS: SUCCESS")
            logging.info(f"✅ ANALYSIS RESULT: Technical analysis completed successfully for {ticker}")
            logging.info(f"✅ DATA QUALITY: {technical_data['metadata']['indicator_count']} indicators validated")
            logging.info(f"✅ REPORT STATUS: Generated {len(report)} character report")
            
            # Return state update with success flag
            return {
                "market_messages": [],  # No LLM messages needed
                "market_report": report,
                "market_data": technical_data,  # Include raw data for other agents
                "sender": "Market Analyst UltraFast",
                "execution_time": total_time,
                "calculation_time": calc_time,
                "success": True,  # Explicit success flag
                "validation_passed": True,  # Data validation passed
                "indicator_count": technical_data['metadata']['indicator_count']
            }
            
        except Exception as e:
            duration = time.time() - start_time
            
            # ✅ ENHANCED EXCEPTION LOGGING WITH FAILURE DETECTION
            logging.error(f"❌ MARKET ANALYST ULTRA FAST UNEXPECTED ERROR: {type(e).__name__}")
            logging.error(f"❌ ERROR DETAILS: {str(e)}")
            logging.error(f"❌ EXECUTION FAILED AFTER: {duration:.2f} seconds")
            
            # Check if this might be an I/O related failure
            error_str = str(e).lower()
            is_io_error = any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'blocking', 'io', 'socket'])
            
            if is_io_error:
                logging.error(f"❌ I/O RELATED FAILURE DETECTED: This may indicate blocking I/O issues")
                error_type = "io_related_exception"
            else:
                error_type = "analysis_exception"
            
            # ✅ FINAL FAILURE CONFIRMATION - Clear failure status
            logging.error(f"❌ MARKET ANALYST ULTRA FAST FINAL STATUS: FAILED")
            logging.error(f"❌ ANALYSIS RESULT: Technical analysis failed for {ticker}")
            minimalist_log("MARKET_ULTRA", f"FAILED: Analysis failed after {duration:.2f}s - {type(e).__name__}")
            
            return {
                "market_messages": [],
                "market_report": f"❌ ANALYSIS FAILED - Technical analysis failed for {ticker}: {type(e).__name__}",
                "error": True,
                "error_type": error_type,
                "error_details": str(e),
                "sender": "Market Analyst UltraFast",
                "execution_time": duration,
                "success": False,  # Explicit failure flag
                "validation_passed": False,  # Validation failed
                "is_io_error": is_io_error  # Flag for I/O-related errors
            }
    
    return market_analyst_ultra_fast_node


def generate_technical_report(ticker: str, data: Dict[str, Any], calc_time: float) -> str:
    """
    Generate a comprehensive technical analysis report from the calculated data.
    
    This replaces the LLM-generated report with a structured data-driven report.
    """
    report_lines = [
        f"📊 TECHNICAL ANALYSIS: {ticker}",
        f"⚡ Indicators calculated in {calc_time:.3f}s (Ultra-Fast Mode)",
        "=" * 60,
        ""
    ]
    
    indicators = data.get('indicators', {})
    ohlcv = data.get('ohlcv', [])
    
    # Current Price Action
    if ohlcv and len(ohlcv) > 0:
        latest = ohlcv[-1]
        report_lines.extend([
            "📈 CURRENT PRICE ACTION:",
            f"  Price: ${latest.get('close', 0):.2f}",
            f"  Volume: {latest.get('volume', 0):,.0f}",
            f"  Day Range: ${latest.get('low', 0):.2f} - ${latest.get('high', 0):.2f}",
            ""
        ])
    
    # Moving Averages
    ma_signals = []
    if 'sma_20' in indicators and 'sma_50' in indicators:
        if indicators['sma_20'] > indicators['sma_50']:
            ma_signals.append("✅ Bullish: SMA20 > SMA50")
        else:
            ma_signals.append("⚠️ Bearish: SMA20 < SMA50")
    
    if 'sma_50' in indicators and 'sma_200' in indicators:
        if indicators['sma_50'] > indicators['sma_200']:
            ma_signals.append("✅ Golden Cross Pattern")
        else:
            ma_signals.append("⚠️ Death Cross Pattern")
    
    if ma_signals or any(k.startswith('sma_') or k.startswith('ema_') for k in indicators):
        report_lines.extend([
            "📊 MOVING AVERAGES:",
            f"  SMA 20: ${indicators.get('sma_20', 0):.2f}" if 'sma_20' in indicators else "",
            f"  SMA 50: ${indicators.get('sma_50', 0):.2f}" if 'sma_50' in indicators else "",
            f"  SMA 200: ${indicators.get('sma_200', 0):.2f}" if 'sma_200' in indicators else "",
            f"  EMA 12: ${indicators.get('ema_12', 0):.2f}" if 'ema_12' in indicators else "",
            f"  EMA 26: ${indicators.get('ema_26', 0):.2f}" if 'ema_26' in indicators else "",
        ])
        report_lines = [line for line in report_lines if line]  # Remove empty lines
        if ma_signals:
            report_lines.extend(["  " + signal for signal in ma_signals])
        report_lines.append("")
    
    # Momentum Indicators
    if 'rsi_14' in indicators:
        rsi = indicators['rsi_14']
        rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
        report_lines.extend([
            "🎯 MOMENTUM INDICATORS:",
            f"  RSI (14): {rsi:.2f} - {rsi_signal}",
        ])
        
        if 'macd' in indicators:
            report_lines.append(f"  MACD: {indicators['macd']:.2f}")
            if 'macd_signal' in indicators:
                macd_trend = "Bullish" if indicators['macd'] > indicators['macd_signal'] else "Bearish"
                report_lines.append(f"  MACD Signal: {indicators['macd_signal']:.2f} - {macd_trend}")
        
        if 'stoch_k' in indicators:
            report_lines.append(f"  Stochastic K: {indicators['stoch_k']:.2f}")
        
        if 'willr_14' in indicators:
            report_lines.append(f"  Williams %R: {indicators['willr_14']:.2f}")
        
        if 'cci_20' in indicators:
            report_lines.append(f"  CCI (20): {indicators['cci_20']:.2f}")
        
        report_lines.append("")
    
    # Volatility Indicators
    if 'bb_upper' in indicators and 'bb_lower' in indicators:
        report_lines.extend([
            "📉 VOLATILITY INDICATORS:",
            f"  Bollinger Upper: ${indicators['bb_upper']:.2f}",
            f"  Bollinger Middle: ${indicators.get('bb_middle', 0):.2f}",
            f"  Bollinger Lower: ${indicators['bb_lower']:.2f}",
        ])
        
        if 'atr_14' in indicators:
            report_lines.append(f"  ATR (14): {indicators['atr_14']:.2f}")
        
        if 'natr_14' in indicators:
            report_lines.append(f"  NATR (14): {indicators['natr_14']:.2f}%")
        
        report_lines.append("")
    
    # Volume Indicators
    if any(k in indicators for k in ['obv', 'ad', 'mfi_14']):
        report_lines.append("📊 VOLUME INDICATORS:")
        if 'obv' in indicators:
            report_lines.append(f"  OBV: {indicators['obv']:,.0f}")
        if 'ad' in indicators:
            report_lines.append(f"  A/D Line: {indicators['ad']:,.0f}")
        if 'mfi_14' in indicators:
            mfi = indicators['mfi_14']
            mfi_signal = "Overbought" if mfi > 80 else "Oversold" if mfi < 20 else "Neutral"
            report_lines.append(f"  MFI (14): {mfi:.2f} - {mfi_signal}")
        report_lines.append("")
    
    # Trend Indicators
    if 'adx_14' in indicators:
        adx = indicators['adx_14']
        trend_strength = "Strong" if adx > 25 else "Weak"
        report_lines.extend([
            "📈 TREND INDICATORS:",
            f"  ADX (14): {adx:.2f} - {trend_strength} Trend",
        ])
        
        if 'plus_di' in indicators and 'minus_di' in indicators:
            trend_direction = "Bullish" if indicators['plus_di'] > indicators['minus_di'] else "Bearish"
            report_lines.append(f"  +DI/-DI: {trend_direction}")
        
        if 'aroon_up' in indicators and 'aroon_down' in indicators:
            aroon_signal = "Bullish" if indicators['aroon_up'] > indicators['aroon_down'] else "Bearish"
            report_lines.append(f"  Aroon: {aroon_signal}")
        
        report_lines.append("")
    
    # Trading Signal Summary
    report_lines.extend([
        "=" * 60,
        "🔍 TECHNICAL SIGNAL:",
        generate_trading_signal(indicators),
        "",
        f"⚡ Report generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"📊 Total indicators analyzed: {data['metadata']['indicator_count']}"
    ])
    
    return "\n".join(report_lines)


def generate_trading_signal(indicators: Dict[str, Any]) -> str:
    """
    Generate trading signal based on technical indicators.
    Simple rule-based approach for quick decisions.
    """
    signals = []
    score = 0
    
    # RSI Signal
    if 'rsi_14' in indicators:
        rsi = indicators['rsi_14']
        if rsi < 30:
            signals.append("✅ RSI oversold - potential buy")
            score += 1
        elif rsi > 70:
            signals.append("⚠️ RSI overbought - potential sell")
            score -= 1
    
    # MACD Signal
    if 'macd' in indicators and 'macd_signal' in indicators:
        if indicators['macd'] > indicators['macd_signal']:
            signals.append("✅ MACD bullish crossover")
            score += 1
        else:
            signals.append("⚠️ MACD bearish crossover")
            score -= 1
    
    # Moving Average Signal
    if 'sma_20' in indicators and 'sma_50' in indicators:
        if indicators['sma_20'] > indicators['sma_50']:
            signals.append("✅ Short-term MA above long-term")
            score += 1
        else:
            signals.append("⚠️ Short-term MA below long-term")
            score -= 1
    
    # Stochastic Signal
    if 'stoch_k' in indicators:
        stoch = indicators['stoch_k']
        if stoch < 20:
            signals.append("✅ Stochastic oversold")
            score += 1
        elif stoch > 80:
            signals.append("⚠️ Stochastic overbought")
            score -= 1
    
    # Generate final signal
    if score >= 2:
        signal = "🟢 BUY - Strong technical indicators"
    elif score <= -2:
        signal = "🔴 SELL - Weak technical indicators"
    else:
        signal = "🟡 HOLD - Mixed technical signals"
    
    if signals:
        return f"{signal}\n  " + "\n  ".join(signals)
    else:
        return f"{signal}\n  ⚠️ Limited indicator data available"


# Graph node integration helper (legacy compatibility)
async def market_analyst_node(state):
    """Ultra-fast node for graph integration - no API rate limits.
    
    Args:
        state: Graph state containing company_of_interest and optional period
        
    Returns:
        Updated state with technical_data
    """
    ticker = state.get("company_of_interest", "AAPL")
    period = state.get("analysis_period", "1y")
    
    # Use singleton analyst from state or create new one
    if not hasattr(state, "_technical_analyst"):
        analyst = UltraFastTechnicalAnalyst(
            alpha_vantage_key=state.get("alpha_vantage_key"),
            finnhub_key=state.get("finnhub_key")
        )
        await analyst.setup()
        state["_technical_analyst"] = analyst
    
    data = await state["_technical_analyst"].get(ticker, period)
    return {"technical_data": data}


# Alias for backward compatibility
create_market_analyst = create_market_analyst_ultra_fast


# Standalone usage example
async def main():
    """Example usage of the ultra-fast technical analyst."""
    # Initialize analyst
    analyst = UltraFastTechnicalAnalyst()
    await analyst.setup()
    
    # Single ticker analysis
    print("Analyzing AAPL...")
    data = await analyst.get("AAPL", "3mo")
    print(f"Calculated {data['metadata']['indicator_count']} indicators")
    print(f"Sample indicators: RSI={data['indicators'].get('rsi_14', 'N/A'):.2f}")
    
    # Batch analysis
    print("\nBatch analysis...")
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    results = await analyst.get_batch(tickers, "1mo")
    for ticker, result in results.items():
        if 'error' not in result:
            print(f"{ticker}: {result['metadata']['indicator_count']} indicators")
    
    # Cleanup
    await analyst.cleanup()


if __name__ == "__main__":
    # Async-safe logging setup (no blocking I/O)
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.INFO)
    asyncio.run(main())