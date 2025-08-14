# Market Analyst Refactoring Implementation Guide

## Overview

This guide provides step-by-step implementation details for refactoring the market analyst based on the comprehensive analysis findings. The refactoring addresses critical SOLID principle violations, security issues, and architectural problems.

---

## Phase 1: Critical Stability Fixes (2 weeks)

### 1.1 Input Validation and Security (Priority: CRITICAL)

#### Step 1: Create Input Validators
```python
# File: src/agent/utils/market_validators.py
import re
from typing import List, Optional
from datetime import datetime, timedelta

class MarketValidationError(ValueError):
    """Custom exception for market data validation errors"""
    pass

class TickerValidator:
    """Validates stock ticker symbols"""
    
    VALID_TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')
    
    @classmethod
    def validate(cls, ticker: str) -> str:
        """Validate and normalize ticker symbol"""
        if not isinstance(ticker, str):
            raise MarketValidationError(f"Ticker must be string, got {type(ticker)}")
        
        ticker = ticker.upper().strip()
        
        if not cls.VALID_TICKER_PATTERN.match(ticker):
            raise MarketValidationError(f"Invalid ticker format: {ticker}")
        
        return ticker

class PeriodValidator:
    """Validates time periods for market data"""
    
    VALID_PERIODS = {'1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'}
    
    @classmethod
    def validate(cls, period: str) -> str:
        """Validate period string"""
        if period not in cls.VALID_PERIODS:
            raise MarketValidationError(f"Invalid period: {period}. Valid: {cls.VALID_PERIODS}")
        return period

class URLValidator:
    """Validates and sanitizes URLs for API calls"""
    
    ALLOWED_HOSTS = {
        'query1.finance.yahoo.com',
        'finnhub.io',
        'www.alphavantage.co'
    }
    
    @classmethod
    def validate_host(cls, url: str) -> bool:
        """Check if URL host is in allowlist"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.hostname in cls.ALLOWED_HOSTS
```

#### Step 2: Add Security Headers and API Key Protection
```python
# File: src/agent/utils/security.py
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Secure API key management"""
    
    def __init__(self):
        self._keys = {}
    
    def get_finnhub_key(self) -> Optional[str]:
        """Get Finnhub API key securely"""
        key = os.environ.get('FINNHUB_API_KEY')
        if key:
            # Validate key format (should be alphanumeric)
            if not key.replace('_', '').replace('-', '').isalnum():
                logger.warning("Invalid Finnhub API key format detected")
                return None
            # Log only first 4 characters for debugging
            logger.debug(f"Using Finnhub key: {key[:4]}...")
        return key
    
    @staticmethod
    def get_safe_headers() -> dict:
        """Get secure HTTP headers"""
        return {
            'User-Agent': 'TradingAgents/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
```

### 1.2 Proper Error Handling (Priority: CRITICAL)

#### Step 1: Create Exception Hierarchy
```python
# File: src/agent/exceptions/market_exceptions.py
from typing import Optional, Dict, Any

class MarketAnalysisError(Exception):
    """Base exception for market analysis errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code or "MARKET_ERROR"
        self.details = details or {}

class DataFetchError(MarketAnalysisError):
    """Error fetching market data from external APIs"""
    
    def __init__(self, source: str, ticker: str, message: str, status_code: Optional[int] = None):
        super().__init__(f"Failed to fetch {ticker} from {source}: {message}")
        self.error_code = "DATA_FETCH_ERROR"
        self.details = {
            "source": source,
            "ticker": ticker,
            "status_code": status_code
        }

class CalculationError(MarketAnalysisError):
    """Error in technical indicator calculations"""
    
    def __init__(self, indicator: str, message: str):
        super().__init__(f"Calculation failed for {indicator}: {message}")
        self.error_code = "CALCULATION_ERROR" 
        self.details = {"indicator": indicator}

class ConfigurationError(MarketAnalysisError):
    """Configuration or environment setup error"""
    pass
```

#### Step 2: Implement Error Handler Decorator
```python
# File: src/agent/utils/error_handlers.py
import logging
import traceback
from functools import wraps
from typing import Callable, Any, Optional
from ..exceptions.market_exceptions import MarketAnalysisError

logger = logging.getLogger(__name__)

def handle_market_errors(default_return: Any = None, log_traceback: bool = False):
    """Decorator for consistent error handling in market analysis"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MarketAnalysisError as e:
                logger.error(f"Market analysis error in {func.__name__}: {e}")
                logger.error(f"Error code: {e.error_code}, Details: {e.details}")
                if log_traceback:
                    logger.error(f"Traceback: {traceback.format_exc()}")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                if log_traceback:
                    logger.error(f"Traceback: {traceback.format_exc()}")
                return default_return
        return wrapper
    return decorator
```

### 1.3 Basic Unit Testing Framework (Priority: CRITICAL)

#### Step 1: Create Test Structure
```bash
mkdir -p tests/agent/analysts
mkdir -p tests/agent/utils
touch tests/__init__.py
touch tests/agent/__init__.py
touch tests/agent/analysts/__init__.py
touch tests/agent/utils/__init__.py
```

#### Step 2: Create Core Test Cases
```python
# File: tests/agent/utils/test_validators.py
import pytest
from src.agent.utils.market_validators import TickerValidator, PeriodValidator, MarketValidationError

class TestTickerValidator:
    
    def test_valid_tickers(self):
        """Test valid ticker symbols"""
        valid_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        for ticker in valid_tickers:
            assert TickerValidator.validate(ticker) == ticker
    
    def test_lowercase_normalization(self):
        """Test ticker normalization to uppercase"""
        assert TickerValidator.validate("aapl") == "AAPL"
        assert TickerValidator.validate("  msft  ") == "MSFT"
    
    def test_invalid_tickers(self):
        """Test invalid ticker symbols raise errors"""
        invalid_tickers = ["", "TOOLONG", "123", "AA-PL", "AAPL.TO"]
        for ticker in invalid_tickers:
            with pytest.raises(MarketValidationError):
                TickerValidator.validate(ticker)
    
    def test_non_string_input(self):
        """Test non-string input raises error"""
        with pytest.raises(MarketValidationError):
            TickerValidator.validate(123)

class TestPeriodValidator:
    
    def test_valid_periods(self):
        """Test valid period values"""
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
        for period in valid_periods:
            assert PeriodValidator.validate(period) == period
    
    def test_invalid_periods(self):
        """Test invalid period values raise errors"""
        invalid_periods = ["1h", "30d", "3y", "invalid"]
        for period in invalid_periods:
            with pytest.raises(MarketValidationError):
                PeriodValidator.validate(period)
```

#### Step 3: Test Configuration
```python
# File: pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
```

### 1.4 Memory Leak Fixes (Priority: HIGH)

#### Step 1: Fix Global Singleton Pattern
```python
# File: src/agent/utils/connection_manager.py
import asyncio
import weakref
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

class ConnectionManager:
    """Manages connections with proper cleanup"""
    
    _instances: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
    _lock = asyncio.Lock()
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._clients: Dict[str, Any] = {}
        self._cleanup_tasks: set = set()
    
    @classmethod
    async def get_instance(cls, instance_id: str, config: Dict[str, Any]):
        """Get or create connection manager instance"""
        async with cls._lock:
            if instance_id in cls._instances:
                return cls._instances[instance_id]
            
            instance = cls(config)
            cls._instances[instance_id] = instance
            await instance.initialize()
            return instance
    
    async def initialize(self):
        """Initialize connections"""
        # Implementation for connection setup
        pass
    
    async def cleanup(self):
        """Clean up all connections and resources"""
        cleanup_tasks = []
        
        for client in self._clients.values():
            if hasattr(client, 'aclose'):
                cleanup_tasks.append(client.aclose())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self._clients.clear()
    
    def __del__(self):
        """Ensure cleanup on deletion"""
        if self._clients:
            # Log warning about unclean shutdown
            import logging
            logging.warning("ConnectionManager deleted without proper cleanup")
```

---

## Phase 2: Architecture Refactoring (4 weeks)

### 2.1 Break Down God Class (Priority: CRITICAL)

#### Step 1: Create Data Client Interface
```python
# File: src/agent/interfaces/data_client.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class MarketDataClient(ABC):
    """Abstract interface for market data clients"""
    
    @abstractmethod
    async def fetch_ohlcv(self, ticker: str, period: str) -> pd.DataFrame:
        """Fetch OHLCV data for a ticker"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is healthy"""
        pass
    
    @abstractmethod
    async def get_supported_tickers(self) -> list:
        """Get list of supported ticker symbols"""
        pass

class CacheInterface(ABC):
    """Abstract interface for caching"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
```

#### Step 2: Implement Concrete Data Clients
```python
# File: src/agent/clients/yahoo_client.py
import httpx
import pandas as pd
from typing import Dict, Any
from ..interfaces.data_client import MarketDataClient
from ..utils.market_validators import TickerValidator, PeriodValidator
from ..exceptions.market_exceptions import DataFetchError

class YahooFinanceClient(MarketDataClient):
    """Yahoo Finance data client implementation"""
    
    def __init__(self, timeout: int = 15):
        self.base_url = "https://query1.finance.yahoo.com"
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_connections=5)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def fetch_ohlcv(self, ticker: str, period: str) -> pd.DataFrame:
        """Fetch OHLCV data from Yahoo Finance"""
        # Validate inputs
        ticker = TickerValidator.validate(ticker)
        period = PeriodValidator.validate(period)
        
        url = f"{self.base_url}/v8/finance/chart/{ticker}"
        params = {
            'range': period,
            'interval': '1d',
            'includePrePost': 'false'
        }
        
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_yahoo_response(data, ticker)
            
        except httpx.HTTPStatusError as e:
            raise DataFetchError("Yahoo Finance", ticker, f"HTTP {e.response.status_code}", e.response.status_code)
        except httpx.RequestError as e:
            raise DataFetchError("Yahoo Finance", ticker, f"Request error: {e}")
    
    def _parse_yahoo_response(self, data: Dict[str, Any], ticker: str) -> pd.DataFrame:
        """Parse Yahoo Finance API response into DataFrame"""
        try:
            chart = data['chart']['result'][0]
            timestamps = chart['timestamp']
            quote = chart['indicators']['quote'][0]
            
            df = pd.DataFrame({
                'open': quote['open'],
                'high': quote['high'],
                'low': quote['low'],
                'close': quote['close'],
                'volume': quote['volume']
            })
            
            df.index = pd.to_datetime(timestamps, unit='s')
            return df.dropna()
            
        except KeyError as e:
            raise DataFetchError("Yahoo Finance", ticker, f"Invalid response format: missing {e}")
    
    async def health_check(self) -> bool:
        """Check Yahoo Finance API health"""
        try:
            response = await self._client.get(f"{self.base_url}/v8/finance/chart/AAPL?range=1d")
            return response.status_code == 200
        except:
            return False
    
    async def get_supported_tickers(self) -> list:
        """Yahoo Finance supports most US stocks"""
        return []  # Would need separate API call
```

#### Step 3: Create Technical Calculator
```python
# File: src/agent/calculators/technical_calculator.py
import pandas as pd
from typing import Dict, Any, Optional
from ..exceptions.market_exceptions import CalculationError

class TechnicalIndicatorCalculator:
    """Calculates technical indicators from OHLCV data"""
    
    def __init__(self, use_pandas_ta: bool = True):
        self.use_pandas_ta = use_pandas_ta
        self._pandas_ta = None
        
        if use_pandas_ta:
            try:
                import pandas_ta as ta
                self._pandas_ta = ta
            except ImportError:
                self.use_pandas_ta = False
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate all available technical indicators"""
        if self.use_pandas_ta and self._pandas_ta:
            return self._calculate_with_pandas_ta(df)
        else:
            return self._calculate_manually(df)
    
    def _calculate_with_pandas_ta(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate indicators using pandas_ta library"""
        try:
            # Add TA indicators to dataframe
            df.ta.strategy("all")
            
            # Extract latest values
            indicators = {}
            for col in df.columns:
                if col not in ['open', 'high', 'low', 'close', 'volume']:
                    latest_value = df[col].iloc[-1]
                    if pd.notna(latest_value):
                        indicators[col] = float(latest_value)
            
            return indicators
            
        except Exception as e:
            raise CalculationError("pandas_ta_all", str(e))
    
    def _calculate_manually(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate essential indicators manually"""
        indicators = {}
        
        try:
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']
            
            # Moving averages
            for period in [5, 10, 20, 50, 200]:
                if len(df) >= period:
                    indicators[f'sma_{period}'] = close.rolling(window=period).mean().iloc[-1]
            
            # RSI
            if len(df) >= 14:
                delta = close.diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                indicators['rsi_14'] = (100 - (100 / (1 + rs))).iloc[-1]
            
            # MACD
            if len(df) >= 26:
                exp1 = close.ewm(span=12).mean()
                exp2 = close.ewm(span=26).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9).mean()
                
                indicators['macd'] = macd.iloc[-1]
                indicators['macd_signal'] = signal.iloc[-1]
                indicators['macd_histogram'] = (macd - signal).iloc[-1]
            
            return {k: v for k, v in indicators.items() if pd.notna(v)}
            
        except Exception as e:
            raise CalculationError("manual_calculation", str(e))
```

### 2.2 Implement Dependency Injection (Priority: HIGH)

#### Step 1: Create Service Container
```python
# File: src/agent/container/service_container.py
from typing import Dict, Any, TypeVar, Type, Callable
from dataclasses import dataclass
import inspect

T = TypeVar('T')

@dataclass
class ServiceDefinition:
    factory: Callable
    singleton: bool = False
    instance: Any = None

class ServiceContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, ServiceDefinition] = {}
    
    def register(self, service_type: Type[T], factory: Callable[[], T], singleton: bool = False) -> None:
        """Register a service factory"""
        service_name = service_type.__name__
        self._services[service_name] = ServiceDefinition(factory, singleton)
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a service instance"""
        service_name = service_type.__name__
        self._services[service_name] = ServiceDefinition(lambda: instance, True, instance)
    
    def get(self, service_type: Type[T]) -> T:
        """Get service instance"""
        service_name = service_type.__name__
        
        if service_name not in self._services:
            raise ValueError(f"Service {service_name} not registered")
        
        definition = self._services[service_name]
        
        if definition.singleton:
            if definition.instance is None:
                definition.instance = self._create_instance(definition.factory)
            return definition.instance
        
        return self._create_instance(definition.factory)
    
    def _create_instance(self, factory: Callable) -> Any:
        """Create instance with dependency injection"""
        sig = inspect.signature(factory)
        kwargs = {}
        
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                kwargs[param_name] = self.get(param.annotation)
        
        return factory(**kwargs)
```

#### Step 2: Create Market Analysis Service
```python
# File: src/agent/services/market_analysis_service.py
from typing import Dict, Any, List
from ..interfaces.data_client import MarketDataClient, CacheInterface
from ..calculators.technical_calculator import TechnicalIndicatorCalculator
from ..utils.error_handlers import handle_market_errors

class MarketAnalysisService:
    """Main service orchestrating market analysis"""
    
    def __init__(
        self,
        data_client: MarketDataClient,
        calculator: TechnicalIndicatorCalculator,
        cache: CacheInterface = None
    ):
        self.data_client = data_client
        self.calculator = calculator
        self.cache = cache
    
    @handle_market_errors(default_return={})
    async def analyze_ticker(self, ticker: str, period: str = "3mo") -> Dict[str, Any]:
        """Perform complete technical analysis for a ticker"""
        
        # Check cache first
        cache_key = f"analysis:{ticker}:{period}"
        if self.cache:
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # Fetch data
        ohlcv_data = await self.data_client.fetch_ohlcv(ticker, period)
        
        # Calculate indicators
        indicators = self.calculator.calculate_all_indicators(ohlcv_data)
        
        # Generate analysis result
        result = {
            "ticker": ticker,
            "period": period,
            "data_points": len(ohlcv_data),
            "indicators": indicators,
            "latest_price": float(ohlcv_data['close'].iloc[-1]),
            "latest_volume": float(ohlcv_data['volume'].iloc[-1])
        }
        
        # Cache result
        if self.cache:
            await self.cache.set(cache_key, result, ttl=3600)
        
        return result
    
    async def batch_analyze(self, tickers: List[str], period: str = "3mo") -> Dict[str, Dict[str, Any]]:
        """Analyze multiple tickers in parallel"""
        import asyncio
        
        tasks = [self.analyze_ticker(ticker, period) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            ticker: result if not isinstance(result, Exception) else {"error": str(result)}
            for ticker, result in zip(tickers, results)
        }
```

### 2.3 Remove Environment-Specific Code (Priority: HIGH)

#### Step 1: Create Configuration System
```python
# File: src/agent/config/market_config.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import os
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    LANGGRAPH = "langgraph"

@dataclass
class DataSourceConfig:
    name: str
    enabled: bool = True
    timeout: int = 15
    max_retries: int = 3
    priority: int = 1  # Lower number = higher priority

@dataclass
class CacheConfig:
    enabled: bool = True
    url: str = "redis://localhost:6379"
    ttl: int = 3600
    max_connections: int = 10

@dataclass
class MarketAnalysisConfig:
    environment: Environment = Environment.DEVELOPMENT
    data_sources: List[DataSourceConfig] = field(default_factory=list)
    cache: CacheConfig = field(default_factory=CacheConfig)
    use_pandas: bool = True
    enable_advanced_indicators: bool = True
    api_keys: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_environment(cls) -> 'MarketAnalysisConfig':
        """Create configuration from environment variables"""
        
        # Determine environment
        env_str = os.getenv('TRADING_ENVIRONMENT', 'development').lower()
        try:
            environment = Environment(env_str)
        except ValueError:
            environment = Environment.DEVELOPMENT
        
        # Configure based on environment
        config = cls(environment=environment)
        
        if environment == Environment.LANGGRAPH:
            # LangGraph-specific configuration
            config.use_pandas = False
            config.enable_advanced_indicators = False
            config.cache.enabled = False
            
            # Only enable HTTP-based data sources
            config.data_sources = [
                DataSourceConfig(name="yahoo", enabled=True, priority=1),
                DataSourceConfig(name="finnhub", enabled=bool(os.getenv('FINNHUB_API_KEY')), priority=2)
            ]
        else:
            # Standard configuration
            config.use_pandas = True
            config.enable_advanced_indicators = True
            config.cache.enabled = True
            
            config.data_sources = [
                DataSourceConfig(name="yahoo", enabled=True, priority=1),
                DataSourceConfig(name="finnhub", enabled=bool(os.getenv('FINNHUB_API_KEY')), priority=2),
                DataSourceConfig(name="alpha_vantage", enabled=bool(os.getenv('ALPHA_VANTAGE_KEY')), priority=3)
            ]
        
        # Load API keys
        config.api_keys = {
            "finnhub": os.getenv('FINNHUB_API_KEY', ''),
            "alpha_vantage": os.getenv('ALPHA_VANTAGE_KEY', '')
        }
        
        return config
```

#### Step 2: Environment-Agnostic Implementation
```python
# File: src/agent/factory/client_factory.py
from typing import Dict, Type, List
from ..config.market_config import MarketAnalysisConfig, DataSourceConfig
from ..interfaces.data_client import MarketDataClient
from ..clients.yahoo_client import YahooFinanceClient
from ..clients.finnhub_client import FinnhubClient

class DataClientFactory:
    """Factory for creating data clients based on configuration"""
    
    CLIENT_REGISTRY: Dict[str, Type[MarketDataClient]] = {
        "yahoo": YahooFinanceClient,
        "finnhub": FinnhubClient,
    }
    
    @classmethod
    def create_clients(cls, config: MarketAnalysisConfig) -> List[MarketDataClient]:
        """Create data clients based on configuration"""
        clients = []
        
        # Sort by priority (lower number = higher priority)
        sorted_sources = sorted(
            [source for source in config.data_sources if source.enabled],
            key=lambda x: x.priority
        )
        
        for source_config in sorted_sources:
            client_class = cls.CLIENT_REGISTRY.get(source_config.name)
            if client_class:
                # Create client with configuration
                client_kwargs = {
                    "timeout": source_config.timeout
                }
                
                # Add API keys if needed
                if source_config.name == "finnhub":
                    api_key = config.api_keys.get("finnhub")
                    if api_key:
                        client_kwargs["api_key"] = api_key
                
                client = client_class(**client_kwargs)
                clients.append(client)
        
        return clients
```

---

## Phase 3: Performance and Reliability (3 weeks)

### 3.1 Async Operation Optimization (Priority: HIGH)

#### Step 1: Connection Pool Management
```python
# File: src/agent/utils/connection_pool.py
import asyncio
import httpx
from typing import Dict, Optional
from contextlib import asynccontextmanager

class HTTPConnectionPool:
    """Manages HTTP connection pools efficiently"""
    
    def __init__(self):
        self._pools: Dict[str, httpx.AsyncClient] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
    
    async def get_client(self, pool_name: str, **client_kwargs) -> httpx.AsyncClient:
        """Get or create HTTP client for pool"""
        if pool_name not in self._locks:
            self._locks[pool_name] = asyncio.Lock()
        
        async with self._locks[pool_name]:
            if pool_name not in self._pools:
                # Default configuration optimized for financial APIs
                default_config = {
                    "timeout": httpx.Timeout(15.0),
                    "limits": httpx.Limits(
                        max_keepalive_connections=10,
                        max_connections=20,
                        keepalive_expiry=30.0
                    ),
                    "http2": True,
                    "verify": True
                }
                default_config.update(client_kwargs)
                
                self._pools[pool_name] = httpx.AsyncClient(**default_config)
        
        return self._pools[pool_name]
    
    async def close_all(self):
        """Close all connection pools"""
        close_tasks = []
        for client in self._pools.values():
            close_tasks.append(client.aclose())
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        self._pools.clear()
        self._locks.clear()
```

#### Step 2: Async Batch Processing
```python
# File: src/agent/utils/batch_processor.py
import asyncio
from typing import List, Callable, TypeVar, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class BatchResult:
    success: List[R]
    failures: List[Exception]
    execution_time: float

class AsyncBatchProcessor:
    """Efficient batch processing with concurrency control"""
    
    def __init__(self, max_concurrency: int = 10, timeout: Optional[float] = None):
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_batch(
        self, 
        items: List[T], 
        processor: Callable[[T], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> BatchResult[R]:
        """Process items in batches with controlled concurrency"""
        
        async def _process_item(item: T, index: int) -> tuple:
            async with self._semaphore:
                try:
                    result = await processor(item)
                    if progress_callback:
                        progress_callback(index + 1, len(items))
                    return ("success", result)
                except Exception as e:
                    return ("failure", e)
        
        start_time = asyncio.get_event_loop().time()
        
        # Create tasks
        tasks = [_process_item(item, i) for i, item in enumerate(items)]
        
        # Execute with timeout
        try:
            if self.timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=False),
                    timeout=self.timeout
                )
            else:
                results = await asyncio.gather(*tasks, return_exceptions=False)
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Separate successes and failures
        successes = [result[1] for result in results if result[0] == "success"]
        failures = [result[1] for result in results if result[0] == "failure"]
        
        return BatchResult(successes, failures, execution_time)
```

### 3.2 Performance Monitoring (Priority: MEDIUM)

#### Step 1: Create Performance Metrics
```python
# File: src/agent/monitoring/performance_monitor.py
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

@dataclass
class PerformanceMetric:
    name: str
    duration: float
    timestamp: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: defaultdict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._active_operations: Dict[str, float] = {}
    
    def start_operation(self, operation_name: str, operation_id: Optional[str] = None) -> str:
        """Start tracking an operation"""
        op_id = operation_id or f"{operation_name}_{id(object())}"
        self._active_operations[op_id] = time.time()
        return op_id
    
    def end_operation(self, operation_id: str, success: bool = True, metadata: Optional[Dict[str, Any]] = None):
        """End tracking an operation"""
        if operation_id not in self._active_operations:
            return
        
        start_time = self._active_operations.pop(operation_id)
        duration = time.time() - start_time
        
        # Extract operation name from ID
        operation_name = operation_id.split('_')[0]
        
        metric = PerformanceMetric(
            name=operation_name,
            duration=duration,
            timestamp=time.time(),
            success=success,
            metadata=metadata or {}
        )
        
        self._metrics[operation_name].append(metric)
    
    def get_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get performance statistics for an operation"""
        metrics = list(self._metrics[operation_name])
        if not metrics:
            return {}
        
        durations = [m.duration for m in metrics]
        success_rate = sum(1 for m in metrics if m.success) / len(metrics)
        
        return {
            "count": len(metrics),
            "success_rate": success_rate,
            "avg_duration": statistics.mean(durations),
            "median_duration": statistics.median(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "p95_duration": self._percentile(durations, 95),
            "p99_duration": self._percentile(durations, 99)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
```

---

## Phase 4: Long-term Improvements (6 weeks)

### 4.1 Event-Driven Architecture (Priority: LOW)

#### Step 1: Event System
```python
# File: src/agent/events/event_system.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Type
from dataclasses import dataclass
from datetime import datetime
import asyncio
import weakref

@dataclass
class Event:
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str

class EventHandler(ABC):
    @abstractmethod
    async def handle(self, event: Event) -> None:
        pass

class EventBus:
    """Simple event bus for decoupled communication"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._weak_handlers: weakref.WeakSet = weakref.WeakSet()
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]):
        """Subscribe to events of a specific type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        self._weak_handlers.add(handler)
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        handlers = self._handlers.get(event.event_type, [])
        
        if handlers:
            tasks = []
            for handler in handlers:
                if handler in self._weak_handlers:  # Check if handler is still alive
                    tasks.append(self._safe_call_handler(handler, event))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _safe_call_handler(self, handler: Callable, event: Event):
        """Safely call event handler"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            # Log error but don't let it break other handlers
            import logging
            logging.error(f"Error in event handler {handler}: {e}")
```

This implementation guide provides concrete, actionable steps to refactor the market analyst according to SOLID principles and best practices. Each phase builds upon the previous one, ensuring a systematic improvement of the codebase quality and maintainability.