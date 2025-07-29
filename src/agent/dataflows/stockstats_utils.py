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
    """Lazy loader for pandas to prevent circular import issues"""
    try:
        import pandas as pd
        return pd
    except ImportError as e:
        raise ImportError(f"Pandas is required but not available: {e}")

# LAZY LOADER for yfinance - prevents pandas circular import via yfinance
def _get_yfinance():
    """Lazy loader for yfinance to prevent circular import issues"""
    try:
        import yfinance as yf
        return yf
    except ImportError as e:
        raise ImportError(f"yfinance is required but not available: {e}")

# LAZY LOADER for stockstats - prevents pandas circular import via stockstats
def _get_stockstats():
    """Lazy loader for stockstats to prevent circular import issues"""
    try:
        from stockstats import wrap
        return wrap
    except ImportError as e:
        raise ImportError(f"stockstats is required but not available: {e}")

SavePathType = Annotated[str, "File path to save data. If None, data is not saved."] 


class StockstatsUtils:
    
    @staticmethod
    def prepare_data_for_stockstats(data):
        """Prepare data specifically for stockstats processing"""
        pd = _get_pandas()  # Lazy load pandas here
        
        # Ensure we have the required columns for stockstats
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"Warning: Missing required columns for stockstats: {missing_columns}")

        # Ensure proper data types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        # If Date is still not datetime, convert it
        if 'Date' in data.columns and not _get_pandas().api.types.is_datetime64_any_dtype(data['Date']):
            try:
                data['Date'] = _get_pandas().to_datetime(data['Date'], errors='coerce')
            except Exception as e:
                print(f"Error converting Date column: {e}")

        # Ensure index is set properly (stockstats might need this)
        if 'Date' in data.columns:
            data = data.set_index('Date', drop=False)

        return data

    @staticmethod
    def get_stock_stats_indicators_window(
        symbol, curr_date, config, online=True, save_path: SavePathType = None
    ):
        try:
            pd = _get_pandas()  # Lazy load pandas here
            
            if not online:
                try:
                    data_dir = config.get("data_cache_dir", "src/agent/dataflows/data_cache")
                    data = _get_pandas().read_csv(
                        os.path.join(
                            data_dir,
                            f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
                        )
                    )
                except Exception as e:
                    print(f"Error loading offline data for {symbol}: {e}")
                    return f"Error: Failed to load offline data - {str(e)}"

                # Now convert to proper datetime format
                try:
                    pd = _get_pandas()
                    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
                    # Drop any rows where date conversion failed (NaT values)
                    data = data.dropna(subset=['Date'])
                    
                    # Ensure we have a proper datetime column
                    if not pd.api.types.is_datetime64_any_dtype(data['Date']):
                        # If still not datetime, try alternative parsing
                        data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d', errors='coerce')
                except Exception as e:
                    print(f"Error processing Date column for {symbol}: {e}")
                    return f"Error: Failed to process dates - {str(e)}"

                # Prepare data for stockstats processing
                data = StockstatsUtils.prepare_data_for_stockstats(data)

                print("Wrapping data with stockstats...")
                df = _get_stockstats()(data)
            else:
                # Get today's date as YYYY-mm-dd to add to cache
                pd = _get_pandas()
                today_date = pd.Timestamp.today()
                curr_date_dt = pd.to_datetime(curr_date)

                end_date = today_date
                start_date = today_date - pd.DateOffset(years=15)

                # Use cached data if available
                data_dir = config.get("data_cache_dir", "src/agent/dataflows/data_cache")
                data_file = os.path.join(data_dir, f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv")

                if os.path.exists(data_file):
                    try:
                        data = _get_pandas().read_csv(data_file)
                    except Exception as e:
                        print(f"Error reading cached data for {symbol}: {e}")
                        # Fall back to online download
                        data = None
                else:
                    data = None

                # Download fresh data if no cache or cache is old
                if data is None:
                    try:
                        # Prepare data for stockstats processing
                        data = StockstatsUtils.prepare_data_for_stockstats(data)
                    except Exception as e:
                        print(f"Error preparing data for {symbol}: {e}")
                        return f"Error: Failed to prepare data - {str(e)}"

                    try:
                        data = _get_yfinance().download(
                            symbol.upper(),
                            start=start_date.strftime('%Y-%m-%d'),
                            end=end_date.strftime('%Y-%m-%d'),
                            progress=False
                        )
                        
                        # Reset index to make Date a column
                        data = data.reset_index()
                        
                        # Save to cache
                        os.makedirs(data_dir, exist_ok=True)
                        data.to_csv(data_file, index=False)
                        
                    except Exception as e:
                        print(f"Error downloading data for {symbol}: {e}")
                        return f"Error: Failed to download data - {str(e)}"

            # Prepare data for stockstats processing
            data = StockstatsUtils.prepare_data_for_stockstats(data)

            try:
                df = _get_stockstats()(data)
            except Exception as e:
                print(f"Error wrapping data with stockstats for {symbol}: {e}")
                return f"Error: Failed to process data with stockstats - {str(e)}"

            # Get the most recent date for which we have data
            # Trigger stockstats to calculate the indicator
            try:
                # Convert Date column to string for comparison if it's datetime
                if 'Date' in df.columns and _get_pandas().api.types.is_datetime64_any_dtype(df['Date']):
                    date_strings = df['Date'].dt.strftime('%Y-%m-%d')
                else:
                    date_strings = df['Date'].astype(str)

                # Get recent data (up to the current date)
                curr_date_dt = pd.to_datetime(curr_date)
                recent_mask = pd.to_datetime(date_strings) <= curr_date_dt
                recent_data = df[recent_mask].tail(10)

                if recent_data.empty:
                    return f"No data available for {symbol} up to {curr_date}"

                # Get the most recent row
                most_recent = recent_data.iloc[-1]
                result_data = recent_data.to_dict('records')

                return {"recent_data": result_data, "latest_close": float(most_recent.get('close', 0))}

            except Exception as e:
                print(f"Error getting stockstats indicator data for {symbol}: {e}")
                return f"Error: Failed to get indicator data - {str(e)}"

        except Exception as e:
            print(f"Error getting stockstats indicator data for indicator {symbol} on {curr_date}: {e}")
            return f"Error: {str(e)}" 