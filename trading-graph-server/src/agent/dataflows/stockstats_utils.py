# FIXED: Lazy imports for pandas, yfinance AND stockstats to prevent circular import issues in Studio
# import pandas as pd  # <- REMOVED module-level import
# import yfinance as yf  # <- REMOVED module-level import  
# from stockstats import wrap  # <- REMOVED module-level import - THIS WAS THE ROOT CAUSE!
from typing import Annotated
import os
import re
from .config import get_config

# LAZY LOADER for pandas - prevents pandas circular import in Studio
def _get_pandas():
    """Lazy import for pandas to prevent circular imports"""
    import pandas as pd
    return pd

def _get_yfinance():
    """Lazy import for yfinance to prevent circular imports"""
    import yfinance as yf
    return yf

def _get_stockstats_wrap():
    """Lazy import for stockstats wrap to prevent circular imports"""
    from stockstats import wrap
    return wrap


class StockstatsUtils:
    @staticmethod
    def clean_date_data(data):
        """Clean malformed date data where years might be duplicated and ensure proper datetime format"""
        if 'Date' in data.columns:
            # Convert Date column to string if it's not already
            data['Date'] = data['Date'].astype(str)
            
            # Fix malformed dates like "20182018-04-02" -> "2018-04-02"
            # Pattern: match YYYY + YYYY + rest of date, capture the first year and rest
            pattern = r'(\d{4})\1(.*)$'  # \1 refers to the first captured group (year)
            data['Date'] = data['Date'].str.replace(pattern, r'\1\2', regex=True)
            
            # Also handle any other malformed date patterns
            # Remove any duplicate year patterns more broadly
            data['Date'] = data['Date'].str.replace(r'(\d{4})(\d{4})-', r'\1-', regex=True)
            
            # Now convert to proper datetime format
            try:
                data['Date'] = _get_pandas().to_datetime(data['Date'], errors='coerce')
                # Drop any rows where date conversion failed (NaT values)
                data = data.dropna(subset=['Date'])
                
                # Ensure we have a proper datetime column
                if not _get_pandas().api.types.is_datetime64_any_dtype(data['Date']):
                    # If still not datetime, try alternative parsing
                    data['Date'] = _get_pandas().to_datetime(data['Date'], format='%Y-%m-%d', errors='coerce')
                    data = data.dropna(subset=['Date'])
                    
            except Exception as e:
                print(f"Warning: Could not convert Date column to datetime: {e}")
                # Fall back to string format but ensure consistency
                data['Date'] = data['Date'].astype(str)
            
        return data

    @staticmethod
    def prepare_data_for_stockstats(data):
        """Prepare data specifically for stockstats processing"""
        if data is None or data.empty:
            return data
            
        # Ensure we have the required columns for stockstats
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            print(f"Warning: Missing required columns for stockstats: {missing_columns}")
            return data
            
        # Clean and prepare data
        data = StockstatsUtils.clean_date_data(data)
        
        # If Date is still not datetime, convert it
        if 'Date' in data.columns and not _get_pandas().api.types.is_datetime64_any_dtype(data['Date']):
            try:
                data['Date'] = _get_pandas().to_datetime(data['Date'], errors='coerce')
                data = data.dropna(subset=['Date'])
            except Exception as e:
                print(f"Final datetime conversion failed: {e}")
        
        # Sort by date to ensure proper order
        if 'Date' in data.columns:
            data = data.sort_values('Date').reset_index(drop=True)
            
        return data

    @staticmethod
    def get_stock_stats(
        symbol: Annotated[str, "ticker symbol for the company"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
        data_dir: Annotated[
            str,
            "directory where the stock data is stored.",
        ],
        online: Annotated[
            bool,
            "whether to use online tools to fetch data or offline tools. If True, will use online tools.",
        ] = False,
    ):
        df = None
        data = None

        if not online:
            try:
                data = _get_pandas().read_csv(
                    os.path.join(
                        data_dir,
                        f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
                    )
                )
                # Prepare data for stockstats processing
                data = StockstatsUtils.prepare_data_for_stockstats(data)
                
                if data.empty:
                    return "Error: No valid data after cleaning"
                
                df = _get_stockstats_wrap()(data)
            except FileNotFoundError:
                raise Exception("Stockstats fail: Yahoo Finance data not fetched yet!")
            except Exception as e:
                print(f"Error processing offline data for {symbol}: {e}")
                return f"Error: {str(e)}"
        else:
            # Get today's date as YYYY-mm-dd to add to cache
            today_date = _get_pandas().Timestamp.today()
            curr_date_dt = _get_pandas().to_datetime(curr_date)

            end_date = today_date
            start_date = today_date - _get_pandas().DateOffset(years=15)
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            # Get config and ensure cache directory exists
            config = get_config()
            os.makedirs(config["data_cache_dir"], exist_ok=True)

            data_file = os.path.join(
                config["data_cache_dir"],
                f"{symbol}-YFin-data-{start_date}-{end_date}.csv",
            )

            if os.path.exists(data_file):
                try:
                    data = _get_pandas().read_csv(data_file)
                    # Prepare data for stockstats processing
                    data = StockstatsUtils.prepare_data_for_stockstats(data)
                    
                    if data.empty:
                        print(f"No valid data found in cache for {symbol}")
                        # Remove the corrupted cache file and re-download
                        os.remove(data_file)
                        return StockstatsUtils.get_stock_stats(symbol, indicator, curr_date, data_dir, online=True)
                        
                except Exception as e:
                    print(f"Error reading cached data for {symbol}: {e}")
                    # Remove corrupted cache file and retry
                    if os.path.exists(data_file):
                        os.remove(data_file)
                    return StockstatsUtils.get_stock_stats(symbol, indicator, curr_date, data_dir, online=True)
            else:
                try:
                    data = _get_yfinance().download(
                        symbol,
                        start=start_date,
                        end=end_date,
                        multi_level_index=False,
                        progress=False,
                        auto_adjust=True,
                    )
                    if data.empty:
                        return f"Error: No data available for {symbol}"
                        
                    data = data.reset_index()
                    data.to_csv(data_file, index=False)
                    
                except Exception as e:
                    print(f"Error downloading data for {symbol}: {e}")
                    return f"Error: {str(e)}"

            # Prepare data for stockstats processing
            data = StockstatsUtils.prepare_data_for_stockstats(data)
            
            if data.empty:
                return "Error: No valid data after cleaning"
            
            try:
                df = _get_stockstats_wrap()(data)
                # Convert curr_date back to string format for comparison
                curr_date = curr_date_dt.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"Error wrapping data with stockstats for {symbol}: {e}")
                return f"Error: Failed to process data with stockstats - {str(e)}"

        try:
            # Trigger stockstats to calculate the indicator
            df[indicator]
            
            # Convert Date column to string for comparison if it's datetime
            if 'Date' in df.columns and _get_pandas().api.types.is_datetime64_any_dtype(df['Date']):
                date_strings = df['Date'].dt.strftime('%Y-%m-%d')
                matching_rows = df[date_strings == curr_date]
            else:
                # If Date is already string, use string comparison
                matching_rows = df[df["Date"].astype(str).str.startswith(curr_date)]

            if not matching_rows.empty:
                indicator_value = matching_rows[indicator].values[0]
                return indicator_value
            else:
                return "N/A: Not a trading day (weekend or holiday)"
        except KeyError as e:
            print(f"Error: Indicator '{indicator}' not found. Available indicators: {list(df.columns)}")
            return f"Error: Invalid indicator '{indicator}'"
        except Exception as e:
            print(f"Error getting stockstats indicator data for indicator {indicator} on {curr_date}: {e}")
            return f"Error: {str(e)}"
