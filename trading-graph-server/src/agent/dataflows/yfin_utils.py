# gets data/stats

from typing import Annotated, Callable, Any, Optional
# FIXED: ALL pandas imports made lazy to prevent circular import in Studio
# from pandas import _get_dataframe()  # <- REMOVED
# import pandas as pd  # <- REMOVED
from functools import wraps

# FIXED: Lazy import for yfinance to prevent pandas circular import in Studio
# import yfinance as yf  # <- REMOVED module-level import

from .utils import save_output, SavePathType

# LAZY LOADER for yfinance - prevents pandas circular import via yfinance
def _get_yfinance():
    """Lazy loader for yfinance to prevent circular import issues"""
    try:
        import yfinance as yf
        return yf
    except ImportError as e:
        raise ImportError(f"yfinance is required but not available: {e}")

# LAZY LOADER for pandas - prevents pandas circular import in Studio
def _get_pandas():
    """Lazy loader for pandas to prevent circular import issues"""
    try:
        import pandas as pd
        return pd
    except ImportError as e:
        raise ImportError(f"Pandas is required but not available: {e}")

def _get_dataframe():
    """Lazy loader for DataFrame to prevent circular import issues"""
    try:
        from pandas import DataFrame
        return DataFrame
    except ImportError as e:
        raise ImportError(f"Pandas DataFrame is required but not available: {e}")

def init_ticker(func: Callable) -> Callable:
    """Decorator to initialize yf.Ticker and pass it to the function."""

    @wraps(func)
    def wrapper(symbol: Annotated[str, "ticker symbol"], *args, **kwargs) -> Any:
        yf = _get_yfinance()  # Lazy load yfinance here
        ticker = yf.Ticker(symbol)
        return func(ticker, *args, **kwargs)

    return wrapper

def decorate_all_methods(decorator):
    """Class decorator to apply a decorator to all methods"""
    def class_decorator(cls):
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if callable(attr) and not attr_name.startswith('_'):
                setattr(cls, attr_name, decorator(attr))
        return cls
    return class_decorator


@decorate_all_methods(init_ticker)
class YFinanceUtils:

    def get_stock_data(
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[
            str, "start date for retrieving stock price data, YYYY-mm-dd"
        ],
        end_date: Annotated[
            str, "end date for retrieving stock price data, YYYY-mm-dd"
        ],
        save_path: SavePathType = None,
    ) -> "DataFrame":  # FIXED: Use string literal to prevent NameError
        """retrieve stock price data for designated ticker symbol"""
        ticker = symbol
        try:
            # add one day to the end_date so that the data range is inclusive
            end_date = _get_pandas().to_datetime(end_date) + _get_pandas().DateOffset(days=1)
            end_date = end_date.strftime("%Y-%m-%d")
            stock_data = ticker.history(start=start_date, end=end_date)
            if stock_data is None or (hasattr(stock_data, 'empty') and stock_data.empty):
                raise AttributeError("ticker.history returned None or empty data")
            # save_output(stock_data, f"Stock data for {ticker.ticker}", save_path)
            return stock_data
        except AttributeError as e:
            from .empty_response_handler import create_empty_market_data_response
            error_msg = f"AttributeError accessing stock data: {str(e)}"
            # Return empty DataFrame with error info
            pd = _get_pandas()
            empty_df = pd.DataFrame()
            empty_df.attrs['error'] = create_empty_market_data_response(symbol, error_msg)
            return empty_df

    def get_stock_info(
        symbol: Annotated[str, "ticker symbol"],
    ) -> dict:
        """Fetches and returns latest stock information."""
        ticker = symbol
        try:
            stock_info = ticker.info
            if stock_info is None:
                raise AttributeError("ticker.info returned None")
            return stock_info
        except AttributeError as e:
            from .empty_response_handler import create_empty_market_data_response
            error_msg = f"AttributeError accessing stock info: {str(e)}"
            return {"error": create_empty_market_data_response(symbol, error_msg)}

    def get_company_info(
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> "DataFrame":  # FIXED: Use string literal to prevent NameError
        """Fetches and returns company information as a DataFrame."""
        ticker = symbol
        info = ticker.info
        company_info = {
            "Company Name": info.get("shortName", "N/A"),
            "Industry": info.get("industry", "N/A"),
            "Sector": info.get("sector", "N/A"),
            "Country": info.get("country", "N/A"),
            "Website": info.get("website", "N/A"),
        }
        company_info_df = _get_dataframe()([company_info])  # FIXED: Use lazy loader
        if save_path:
            company_info_df.to_csv(save_path)
            print(f"Company info for {ticker.ticker} saved to {save_path}")
        return company_info_df

    def get_stock_dividends(
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> "DataFrame":  # FIXED: Use string literal to prevent NameError
        """Fetches and returns the latest dividends data as a DataFrame."""
        ticker = symbol
        dividends = ticker.dividends
        if save_path:
            dividends.to_csv(save_path)
            print(f"Dividends for {ticker.ticker} saved to {save_path}")
        return dividends

    def get_income_stmt(symbol: Annotated[str, "ticker symbol"]) -> "DataFrame":  # FIXED: Use string literal
        """Fetches and returns the latest income statement of the company as a DataFrame."""
        ticker = symbol
        income_stmt = ticker.financials
        return income_stmt

    def get_balance_sheet(symbol: Annotated[str, "ticker symbol"]) -> "DataFrame":  # FIXED: Use string literal
        """Fetches and returns the latest balance sheet of the company as a DataFrame."""
        ticker = symbol
        balance_sheet = ticker.balance_sheet
        return balance_sheet

    def get_cash_flow(symbol: Annotated[str, "ticker symbol"]) -> "DataFrame":  # FIXED: Use string literal
        """Fetches and returns the latest cash flow statement of the company as a DataFrame."""
        ticker = symbol
        cash_flow = ticker.cashflow
        return cash_flow

    def get_analyst_recommendations(symbol: Annotated[str, "ticker symbol"]) -> tuple:
        """Fetches the latest analyst recommendations and returns the most common recommendation and its count."""
        ticker = symbol
        recommendations = ticker.recommendations
        if recommendations.empty:
            return None, 0  # No recommendations available

        # Assuming 'period' column exists and needs to be excluded
        row_0 = recommendations.iloc[0, 1:]  # Exclude 'period' column if necessary

        # Find the maximum voting result
        max_votes = row_0.max()
        majority_voting_result = row_0[row_0 == max_votes].index.tolist()

        return majority_voting_result[0], max_votes
