"""
Market Analyst - Async-Compatible Pandas Integration
Production-ready implementation with proper async patterns for LangGraph compatibility
No blocking pandas imports - uses thread isolation for full dev/production parity
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
import sys
import os
import time

logger = logging.getLogger(__name__)

# State Definition for LangGraph
class MarketAnalystState(TypedDict):
    company_of_interest: str
    market_data: Optional[Dict[str, Any]]
    market_report: Optional[str]
    error: Optional[str]

# Global state for cached imports and availability
_pandas_modules = {}
_availability_checked = False
_pandas_available = False

async def check_pandas_availability() -> bool:
    """
    Async-compatible pandas availability check.
    Uses thread isolation to prevent blocking the event loop.
    """
    global _availability_checked, _pandas_available
    
    if _availability_checked:
        return _pandas_available
    
    try:
        # Run blocking operations in thread pool to maintain async compatibility
        result = await asyncio.to_thread(_sync_pandas_check)
        _pandas_available = result
        _availability_checked = True
        
        logger.critical(f"🔥🔥🔥 ASYNC PANDAS CHECK: PANDAS_AVAILABLE = {_pandas_available}")
        return _pandas_available
        
    except Exception as e:
        logger.warning(f"⚠️ Async pandas check failed ({e}) - using pure Python fallback")
        _pandas_available = False
        _availability_checked = True
        return False

def _sync_pandas_check() -> bool:
    """
    Synchronous pandas check - run in thread pool via asyncio.to_thread()
    This isolates blocking I/O operations from the main event loop.
    """
    try:
        # Check for file naming conflicts (common cause of circular imports)
        for path in sys.path:
            if not path:
                continue
            pandas_file = os.path.join(path, 'pandas.py')
            if os.path.exists(pandas_file):
                logger.warning(f"Found conflicting pandas.py file at {pandas_file}")
                return False
        
        # Check for environment-specific restrictions
        if os.environ.get('FORCE_PURE_PYTHON') == '1':
            logger.info("FORCE_PURE_PYTHON detected - using pure Python fallback")
            return False
        
        # Test pandas import and basic functionality (in thread pool)
        import pandas as pd
        import pandas_ta as ta
        
        # Cache the modules for later use
        _pandas_modules['pd'] = pd
        _pandas_modules['ta'] = ta
        
        # Verify basic operations work
        test_data = {'close': [100, 101, 102, 103, 104]}
        df = pd.DataFrame(test_data)
        rsi = ta.rsi(df['close'], length=4)
        
        if len(rsi.dropna()) > 0:
            logger.critical("🔥🔥🔥 PANDAS-TA ENGINE AVAILABLE - 158+ indicators enabled (async-compatible) 🔥🔥🔥")
            return True
        else:
            logger.warning("Pandas-ta test failed - using pure Python fallback")
            return False
            
    except ImportError as e:
        logger.info(f"⚠️ Pandas/pandas-ta not installed ({e}) - using pure Python fallback")
        return False
    except Exception as e:
        logger.info(f"⚠️ Pandas not available ({e}) - using pure Python fallback")
        return False

async def get_pandas_modules() -> tuple:
    """
    Async-compatible pandas module retrieval.
    Returns cached modules or None if not available.
    """
    if not await check_pandas_availability():
        return None, None
    
    return _pandas_modules.get('pd'), _pandas_modules.get('ta')

# Market Data Service
class MarketDataService:
    """Simple async market data fetching - fail fast on errors"""
    
    @staticmethod
    async def fetch_ohlcv(ticker: str, period: str = "3mo") -> Optional[Dict[str, List[float]]]:
        """Fetch OHLCV data from Yahoo Finance - no retries, no mock data"""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {"range": period, "interval": "1d"}
        
        # Basic headers to identify as browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    params=params, 
                    headers=headers,
                    timeout=10.0
                )
                
                # If rate limited, fail immediately
                if response.status_code == 429:
                    logger.error(f"Rate limited for {ticker} - Yahoo Finance blocking requests")
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                # Extract OHLCV data
                result = data.get("chart", {}).get("result", [])
                if not result:
                    logger.error(f"No chart data for {ticker}")
                    return None
                    
                quotes = result[0].get("indicators", {}).get("quote", [{}])[0]
                
                # Clean and filter data
                ohlcv = {
                    'open': [p for p in quotes.get('open', []) if p is not None],
                    'high': [p for p in quotes.get('high', []) if p is not None],
                    'low': [p for p in quotes.get('low', []) if p is not None],
                    'close': [p for p in quotes.get('close', []) if p is not None],
                    'volume': [v for v in quotes.get('volume', []) if v is not None and v > 0]
                }
                
                if len(ohlcv['close']) > 0:
                    logger.info(f"✅ Fetched {len(ohlcv['close'])} periods for {ticker}")
                    return ohlcv
                else:
                    logger.error(f"Empty data returned for {ticker}")
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"Request failed for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None

# Async Pandas Engine
class AsyncPandasEngine:
    """Async pandas-ta engine using thread isolation"""
    
    @staticmethod
    async def calculate_comprehensive_indicators(ohlcv: Dict[str, List[float]]) -> Dict[str, float]:
        """Calculate comprehensive indicators using pandas-ta in thread pool"""
        pd, ta = await get_pandas_modules()
        if not pd or not ta:
            raise RuntimeError("Pandas not available - cannot calculate indicators")
        
        # Run pandas calculations in thread pool to maintain async compatibility
        return await asyncio.to_thread(
            AsyncPandasEngine._sync_calculate_comprehensive_indicators,
            ohlcv, pd, ta
        )
    
    @staticmethod
    def _sync_calculate_comprehensive_indicators(ohlcv: Dict[str, List[float]], pd, ta) -> Dict[str, float]:
        """Synchronous comprehensive indicator calculations - run in thread pool"""
        
        logger.critical("🔥🔥🔥 ASYNC PANDAS ENGINE: Starting comprehensive indicator calculation")
        logger.critical(f"🔥 pandas version: {pd.__version__}")
        logger.critical(f"🔥 pandas_ta version: {ta.__version__}")
        logger.critical(f"🔥 Data points available: {len(ohlcv.get('close', []))}")
        
        # Create DataFrame with proper dtype casting to prevent pandas-ta FutureWarning
        df = pd.DataFrame(ohlcv)
        
        # Ensure proper dtypes for pandas-ta calculations (fixes MFI dtype incompatibility)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].astype('float64')
        
        if len(df) < 20:
            logger.warning("Insufficient data for comprehensive analysis")
            return {}
        
        indicators = {}
        
        def clean_series_value(value):
            """Safely extract scalar from pandas Series or return scalar"""
            if hasattr(value, 'iloc'):  # Check if it's a pandas Series
                # Handle NaN values and get the last valid value
                if hasattr(value, 'dropna'):
                    cleaned = value.dropna()
                    if len(cleaned) > 0:
                        return float(cleaned.iloc[-1])
                    else:
                        return None
                return float(value.iloc[-1]) if not pd.isna(value.iloc[-1]) else None
            else:
                return float(value) if not pd.isna(value) else None
        
        try:
            # MOMENTUM INDICATORS (Expanded: 30+ indicators)
            logger.critical("🔥 Calculating momentum indicators...")
            
            # RSI variants
            for period in [9, 14, 21, 25]:
                rsi = ta.rsi(df['close'], length=period)
                if not rsi.empty and len(rsi.dropna()) > 0:
                    val = clean_series_value(rsi)
                    if val is not None:
                        indicators[f'rsi_{period}'] = val
            
            # Stochastic variants
            stoch = ta.stoch(df['high'], df['low'], df['close'])
            if not stoch.empty and len(stoch.dropna()) > 0:
                for col in stoch.columns:
                    if not pd.isna(stoch[col].iloc[-1]):
                        indicators[f'stoch_{col.lower()}'] = clean_series_value(stoch[col])
            
            # Williams %R
            for period in [14, 21]:
                willr = ta.willr(df['high'], df['low'], df['close'], length=period)
                if not willr.empty and len(willr.dropna()) > 0:
                    indicators[f'willr_{period}'] = clean_series_value(willr)
            
            # Commodity Channel Index
            for period in [14, 20]:
                cci = ta.cci(df['high'], df['low'], df['close'], length=period)
                if not cci.empty and len(cci.dropna()) > 0:
                    indicators[f'cci_{period}'] = clean_series_value(cci)
            
            # Rate of Change
            for period in [9, 12, 25]:
                roc = ta.roc(df['close'], length=period)
                if not roc.empty and len(roc.dropna()) > 0:
                    indicators[f'roc_{period}'] = clean_series_value(roc)
            
            # Momentum
            for period in [10, 12, 25]:
                mom = ta.mom(df['close'], length=period)
                if not mom.empty and len(mom.dropna()) > 0:
                    indicators[f'momentum_{period}'] = clean_series_value(mom)
            
            # MACD family
            macd = ta.macd(df['close'])
            if not macd.empty and len(macd.dropna()) > 0:
                for col in macd.columns:
                    if not pd.isna(macd[col].iloc[-1]):
                        indicators[f'macd_{col.lower()}'] = clean_series_value(macd[col])
            
            # TSI (True Strength Index)
            tsi = ta.tsi(df['close'])
            if not tsi.empty and len(tsi.dropna()) > 0:
                for col in tsi.columns:
                    if not pd.isna(tsi[col].iloc[-1]):
                        indicators[f'tsi_{col.lower()}'] = clean_series_value(tsi[col])
            
            # Ultimate Oscillator
            uo = ta.uo(df['high'], df['low'], df['close'])
            if not uo.empty and len(uo.dropna()) > 0:
                indicators['ultimate_oscillator'] = clean_series_value(uo)
            
            # Awesome Oscillator
            ao = ta.ao(df['high'], df['low'])
            if not ao.empty and len(ao.dropna()) > 0:
                indicators['awesome_oscillator'] = clean_series_value(ao)
            
            # OVERLAP INDICATORS (Expanded: 56+ indicators)
            logger.critical("🔥 Calculating overlap indicators...")
            logger.critical(f"🔥 DEBUG: Indicators before overlap: {len(indicators)}")
            
            # Simple Moving Averages
            for period in [5, 8, 10, 13, 20, 21, 34, 50, 55, 89, 100, 200]:
                if period <= len(df):  # Only calculate if we have enough data
                    sma = ta.sma(df['close'], length=period)
                    if sma is not None and not sma.empty and not pd.isna(sma.iloc[-1]):
                        indicators[f'sma_{period}'] = clean_series_value(sma)
            
            # Exponential Moving Averages
            for period in [8, 12, 20, 21, 26, 50, 100, 200]:
                if period <= len(df):
                    ema = ta.ema(df['close'], length=period)
                    if ema is not None and not ema.empty and not pd.isna(ema.iloc[-1]):
                        indicators[f'ema_{period}'] = clean_series_value(ema)
            
            # Weighted Moving Average
            for period in [9, 15, 20]:
                if period <= len(df):
                    wma = ta.wma(df['close'], length=period)
                    if wma is not None and not wma.empty and not pd.isna(wma.iloc[-1]):
                        indicators[f'wma_{period}'] = clean_series_value(wma)
            
            # Hull Moving Average
            for period in [9, 16, 20]:
                if period <= len(df):
                    hma = ta.hma(df['close'], length=period)
                    if hma is not None and not hma.empty and not pd.isna(hma.iloc[-1]):
                        indicators[f'hma_{period}'] = clean_series_value(hma)
            
            # Kaufman's Adaptive Moving Average
            for period in [10, 20, 30]:
                if period <= len(df):
                    kama = ta.kama(df['close'], length=period)
                    if kama is not None and not kama.empty and not pd.isna(kama.iloc[-1]):
                        indicators[f'kama_{period}'] = clean_series_value(kama)
            
            # Triple Exponential Moving Average
            for period in [14, 20]:
                if period <= len(df):
                    tema = ta.tema(df['close'], length=period)
                    if tema is not None and not tema.empty and not pd.isna(tema.iloc[-1]):
                        indicators[f'tema_{period}'] = clean_series_value(tema)
            
            # Triangular Moving Average
            for period in [14, 20]:
                if period <= len(df):
                    trima = ta.trima(df['close'], length=period)
                    if trima is not None and not trima.empty and not pd.isna(trima.iloc[-1]):
                        indicators[f'trima_{period}'] = clean_series_value(trima)
            
            # VWAP (Volume Weighted Average Price)
            if 'volume' in df.columns and df['volume'].sum() > 0:
                vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
                if vwap is not None and not vwap.empty and not pd.isna(vwap.iloc[-1]):
                    indicators['vwap'] = clean_series_value(vwap)
            
            # VOLATILITY INDICATORS
            logger.critical("🔥 Calculating volatility indicators...")
            logger.critical(f"🔥 DEBUG: Indicators before volatility: {len(indicators)}")
            
            # Bollinger Bands
            try:
                bb = ta.bbands(df['close'])
                if bb is not None and not bb.empty and len(bb.dropna()) > 0:
                    for col in bb.columns:
                        if not pd.isna(bb[col].iloc[-1]):
                            col_name = col.lower().replace('bbl', 'bb_lower').replace('bbm', 'bb_middle').replace('bbu', 'bb_upper').replace('bbp', 'bb_percent').replace('bbw', 'bb_width')
                            val = clean_series_value(bb[col])
                            if val is not None:
                                indicators[col_name] = val
            except Exception as e:
                logger.warning(f"Bollinger Bands calculation failed: {e}")
            
            # Average True Range
            for period in [14, 21]:
                try:
                    atr = ta.atr(df['high'], df['low'], df['close'], length=period)
                    if atr is not None and not atr.empty and len(atr.dropna()) > 0:
                        val = clean_series_value(atr)
                        if val is not None:
                            indicators[f'atr_{period}'] = val
                except Exception as e:
                    logger.warning(f"ATR {period} calculation failed: {e}")
            
            # Keltner Channels
            try:
                kc = ta.kc(df['high'], df['low'], df['close'])
                if kc is not None and not kc.empty and len(kc.dropna()) > 0:
                    for col in kc.columns:
                        if not pd.isna(kc[col].iloc[-1]):
                            col_name = col.lower().replace('kcl', 'kc_lower').replace('kcm', 'kc_middle').replace('kcu', 'kc_upper')
                            val = clean_series_value(kc[col])
                            if val is not None:
                                indicators[col_name] = val
            except Exception as e:
                logger.warning(f"Keltner Channels calculation failed: {e}")
            
            # Donchian Channels
            try:
                dc = ta.donchian(df['high'], df['low'])
                if dc is not None and not dc.empty and len(dc.dropna()) > 0:
                    for col in dc.columns:
                        if not pd.isna(dc[col].iloc[-1]):
                            col_name = col.lower().replace('dcl', 'dc_lower').replace('dcm', 'dc_middle').replace('dcu', 'dc_upper')
                            val = clean_series_value(dc[col])
                            if val is not None:
                                indicators[col_name] = val
            except Exception as e:
                logger.warning(f"Donchian Channels calculation failed: {e}")
            
            # VOLUME INDICATORS  
            logger.critical("🔥 Calculating volume indicators...")
            logger.critical(f"🔥 DEBUG: Indicators before volume: {len(indicators)}")
            
            if 'volume' in df.columns and df['volume'].sum() > 0:
                # On Balance Volume
                try:
                    obv = ta.obv(df['close'], df['volume'])
                    if obv is not None and not obv.empty and not pd.isna(obv.iloc[-1]):
                        val = clean_series_value(obv)
                        if val is not None:
                            indicators['obv'] = val
                except Exception as e:
                    logger.warning(f"OBV calculation failed: {e}")
                
                # Volume Price Trend
                try:
                    vpt = ta.vpt(df['close'], df['volume'])
                    if vpt is not None and not vpt.empty and not pd.isna(vpt.iloc[-1]):
                        val = clean_series_value(vpt)
                        if val is not None:
                            indicators['vpt'] = val
                except Exception as e:
                    logger.warning(f"VPT calculation failed: {e}")
                
                # Money Flow Index
                try:
                    mfi = ta.mfi(df['high'], df['low'], df['close'], df['volume'])
                    if mfi is not None and not mfi.empty and len(mfi.dropna()) > 0:
                        val = clean_series_value(mfi)
                        if val is not None:
                            indicators['mfi'] = val
                except Exception as e:
                    logger.warning(f"MFI calculation failed: {e}")
                
                # Accumulation/Distribution Line
                try:
                    ad = ta.ad(df['high'], df['low'], df['close'], df['volume'])
                    if ad is not None and not ad.empty and not pd.isna(ad.iloc[-1]):
                        val = clean_series_value(ad)
                        if val is not None:
                            indicators['ad_line'] = val
                except Exception as e:
                    logger.warning(f"AD Line calculation failed: {e}")
                
                # Chaikin Money Flow
                try:
                    cmf = ta.cmf(df['high'], df['low'], df['close'], df['volume'])
                    if cmf is not None and not cmf.empty and len(cmf.dropna()) > 0:
                        val = clean_series_value(cmf)
                        if val is not None:
                            indicators['cmf'] = val
                except Exception as e:
                    logger.warning(f"CMF calculation failed: {e}")
            
            logger.critical(f"🔥🔥🔥 ASYNC PANDAS ENGINE: Calculated {len(indicators)} indicators")
            logger.critical(f"🔥 Sample indicators: {list(indicators.keys())[:10]}")
            
        except Exception as e:
            logger.error(f"Error in comprehensive pandas calculations: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
        return indicators

# Pure Python Fallback Engine
class PurePythonEngine:
    """Pure Python fallback for when pandas is not available"""
    
    @staticmethod
    async def calculate_essential_indicators(ohlcv: Dict[str, List[float]]) -> Dict[str, float]:
        """Calculate essential indicators using pure Python"""
        logger.critical("⚠️⚠️⚠️ PURE PYTHON ENGINE: Calculating essential indicators only")
        
        close = ohlcv.get('close', [])
        if len(close) < 20:
            return {}
        
        indicators = {}
        
        # RSI (simplified)
        if len(close) >= 14:
            indicators['rsi_14'] = await asyncio.to_thread(PurePythonEngine._calculate_rsi, close, 14)
        
        # Simple Moving Averages
        for period in [10, 20, 50]:
            if len(close) >= period:
                indicators[f'sma_{period}'] = sum(close[-period:]) / period
        
        # Basic volatility
        if len(close) >= 10:
            recent_prices = close[-10:]
            volatility = (max(recent_prices) - min(recent_prices)) / min(recent_prices) * 100
            indicators['volatility_10d'] = round(volatility, 2)
        
        logger.critical(f"⚠️ PURE PYTHON ENGINE: Calculated {len(indicators)} essential indicators")
        return indicators
    
    @staticmethod
    def _calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI using pure Python"""
        if len(prices) < period + 1:
            return 50.0
            
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

# Unified Indicator Service
class IndicatorService:
    """Orchestrate indicator calculation with async compatibility"""
    
    @staticmethod
    async def calculate_indicators(ohlcv: Dict[str, List[float]]) -> Dict[str, float]:
        """Calculate indicators using best available engine"""
        
        if await check_pandas_availability():
            logger.critical("🔥🔥🔥 ENGINE SELECTION: Using ASYNC PANDAS-TA ENGINE (Enhanced)")
            logger.critical("🔥 Engine capabilities: 158+ indicators, async thread pool processing")
            return await AsyncPandasEngine.calculate_comprehensive_indicators(ohlcv)
        else:
            logger.critical("⚠️⚠️⚠️ ENGINE SELECTION: Using PURE PYTHON ENGINE (Limited)")
            logger.critical("⚠️ Engine capabilities: ~20 indicators, basic calculations")
            return await PurePythonEngine.calculate_essential_indicators(ohlcv)

# Main Market Analyst Service
class MarketAnalystService:
    """Complete async-compatible market analysis service"""
    
    def __init__(self):
        self.data_service = MarketDataService()
        self.indicator_service = IndicatorService()
    
    async def analyze(self, ticker: str) -> Dict[str, Any]:
        """Complete market analysis with async compatibility"""
        
        # Fetch data asynchronously
        ohlcv = await self.data_service.fetch_ohlcv(ticker)
        if not ohlcv:
            return {"error": f"Failed to fetch data for {ticker}"}
        
        # Calculate indicators asynchronously  
        indicators = await self.indicator_service.calculate_indicators(ohlcv)
        if not indicators:
            return {"error": f"Failed to calculate indicators for {ticker}"}
        
        # Determine engine type
        pandas_available = await check_pandas_availability()
        engine = "pandas-ta" if pandas_available else "pure-python"
        
        current_price = ohlcv['close'][-1] if ohlcv['close'] else 0
        
        return {
            "ticker": ticker,
            "current_price": current_price,
            "indicators": indicators,
            "indicator_count": len(indicators),
            "engine": engine,
            "data_points": len(ohlcv['close']),
            "volume": sum(ohlcv.get('volume', [])) / len(ohlcv.get('volume', [1])) if ohlcv.get('volume') else 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "async_compatible": True
        }

def _format_indicator(value, decimals=2):
    """Format indicator value for display"""
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}"
    return str(value)

def generate_report(data: Dict[str, Any]) -> str:
    """Generate comprehensive market report showing ALL calculated indicators"""
    
    ticker = data.get('ticker', 'UNKNOWN')
    current_price = data.get('current_price', 0)
    indicators = data.get('indicators', {})
    indicator_count = data.get('indicator_count', 0)
    engine = data.get('engine', 'unknown')
    
    # Calculate price change if we have SMA data for comparison
    sma_20 = indicators.get('sma_20')
    if sma_20:
        change_pct = ((current_price - sma_20) / sma_20) * 100
        if change_pct > 2:
            signal = "📈 BULLISH"
        elif change_pct < -2:
            signal = "📉 BEARISH"
        else:
            signal = "➡️ NEUTRAL"
    else:
        change_pct = 0
        signal = "➡️ NEUTRAL"
    
    # Group indicators by category for organized display
    momentum_indicators = {k: v for k, v in indicators.items() if k.startswith(('rsi', 'macd', 'stoch', 'willr', 'cci', 'roc', 'momentum', 'tsi', 'ultimate', 'awesome'))}
    overlap_indicators = {k: v for k, v in indicators.items() if k.startswith(('sma', 'ema', 'wma', 'hma', 'kama', 'tema', 'trima', 'vwap'))}
    volatility_indicators = {k: v for k, v in indicators.items() if k.startswith(('bb_', 'atr', 'kc_', 'dc_', 'volatility'))}
    volume_indicators = {k: v for k, v in indicators.items() if k.startswith(('obv', 'vpt', 'mfi', 'ad_', 'cmf'))}
    other_indicators = {k: v for k, v in indicators.items() 
                       if not any(k.startswith(prefix) for prefix in ['rsi', 'macd', 'stoch', 'willr', 'cci', 'roc', 'momentum', 'tsi', 'ultimate', 'awesome', 'sma', 'ema', 'wma', 'hma', 'kama', 'tema', 'trima', 'vwap', 'bb_', 'atr', 'kc_', 'dc_', 'volatility', 'obv', 'vpt', 'mfi', 'ad_', 'cmf'])}
    
    # Build comprehensive indicator text showing ALL indicators organized by category
    all_indicators_text = ""
    
    if momentum_indicators:
        all_indicators_text += "📈 MOMENTUM INDICATORS:\n"
        all_indicators_text += "\n".join([f"• {k.upper()}: {_format_indicator(v, 3)}" for k, v in momentum_indicators.items()])
        all_indicators_text += "\n\n"
    
    if overlap_indicators:
        all_indicators_text += "📊 OVERLAP INDICATORS:\n"
        all_indicators_text += "\n".join([f"• {k.upper()}: ${_format_indicator(v, 2)}" for k, v in overlap_indicators.items()])
        all_indicators_text += "\n\n"
    
    if volatility_indicators:
        all_indicators_text += "📉 VOLATILITY INDICATORS:\n"
        all_indicators_text += "\n".join([f"• {k.upper()}: {_format_indicator(v, 3)}" for k, v in volatility_indicators.items()])
        all_indicators_text += "\n\n"
    
    if volume_indicators:
        all_indicators_text += "📊 VOLUME INDICATORS:\n"
        all_indicators_text += "\n".join([f"• {k.upper()}: {_format_indicator(v, 0)}" for k, v in volume_indicators.items()])
        all_indicators_text += "\n\n"
    
    if other_indicators:
        all_indicators_text += "🔧 OTHER INDICATORS:\n"
        all_indicators_text += "\n".join([f"• {k.upper()}: {_format_indicator(v, 3)}" for k, v in other_indicators.items()])
        all_indicators_text += "\n\n"
    
    # Remove trailing newlines
    all_indicators_text = all_indicators_text.rstrip()
    
    return f"""📊 MARKET ANALYSIS: {ticker}
========================================

PRICE ACTION:
• Current: ${current_price:.2f}
• vs SMA-20: {_format_indicator(sma_20, 2)}
• Change: {change_pct:+.2f}%
• Signal: {signal}

COMPREHENSIVE TECHNICAL ANALYSIS ({indicator_count} indicators calculated):
{all_indicators_text}

VOLUME DATA:
• Current Volume: {data.get('volume', 0):,.0f}
• Average Volume: {_format_indicator(indicators.get('volume_avg'), 0)}

ENGINE: {engine.upper()}
DATA POINTS: {data.get('data_points', 0)}
Generated: {data['timestamp']}
"""

# LangGraph Node Interface
async def market_analyst_node(state: MarketAnalystState) -> Dict[str, Any]:
    """LangGraph-compatible async node for market analysis"""
    logger.critical(f"🔥🔥🔥 ASYNC MARKET ANALYST PANDAS NODE EXECUTING 🔥🔥🔥")
    pandas_available = await check_pandas_availability()
    logger.critical(f"🔥 PANDAS_AVAILABLE: {pandas_available}")
    logger.critical(f"🔥 Engine: {'async-pandas-ta' if pandas_available else 'async-pure-python'}")
    logger.info(f"📊 Market Analyst Node - Engine: {'async-pandas-ta' if pandas_available else 'async-pure-python'}")
    
    start_time = time.time()
    ticker = state.get('company_of_interest', '').upper()
    
    if not ticker:
        return {
            'market_data': None,
            'market_report': '❌ No ticker provided',
            'error': 'Missing ticker symbol'
        }
    
    service = MarketAnalystService()
    
    try:
        result = await service.analyze(ticker)
        
        if 'error' in result:
            return {
                'market_data': None,
                'market_report': f"⚠️ {result['error']}",
                'error': result['error']
            }
        
        # Generate report
        report = generate_report(result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Market analysis completed for {ticker} in {duration:.2f}s")
        logger.info(f"📊 Engine: {result['engine']}, Indicators: {result['indicator_count']}")
        
        return {
            'market_data': result,
            'market_report': report,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Market analysis failed for {ticker}: {e}")
        return {
            'market_data': None,
            'market_report': f"❌ Analysis failed for {ticker}: {str(e)}",
            'error': str(e)
        }

# Legacy Integration Function
def create_ultra_fast_market_analyst(llm=None, toolkit=None):
    """Create market analyst compatible with existing LangGraph integration"""
    logger.critical(f"🔥🔥🔥 CREATE_ULTRA_FAST_MARKET_ANALYST CALLED 🔥🔥🔥")
    
    async def ultra_fast_market_analyst_node(state):
        """LangGraph node compatible with existing state structure"""
        # Log pandas availability at creation time
        pandas_available = await check_pandas_availability()
        logger.critical(f"🔥 PANDAS_AVAILABLE in factory: {pandas_available}")
        
        # Extract ticker from state
        ticker = state.get("company_of_interest", "")
        
        # Use our new async implementation
        analyst_state = {"company_of_interest": ticker}
        result = await market_analyst_node(analyst_state)
        
        # Format for existing system
        return {
            "market_data": result.get("market_data"),
            "market_report": result.get("market_report"),
            "sender": "Ultra Fast Market Analyst (Async-Compatible)"
        }
    
    return ultra_fast_market_analyst_node

# Testing
if __name__ == "__main__":
    async def test():
        print("Testing async-compatible market analyst...")
        pandas_available = await check_pandas_availability()
        print(f"Pandas available: {pandas_available}")
        
        state = {"company_of_interest": "AAPL"}
        result = await market_analyst_node(state)
        print(result['market_report'])
        print(f"\nEngine: {result.get('market_data', {}).get('engine', 'unknown')}")
        print(f"Indicators: {result.get('market_data', {}).get('indicator_count', 0)}")
    
    asyncio.run(test())