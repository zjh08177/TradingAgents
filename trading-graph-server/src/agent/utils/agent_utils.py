from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from datetime import date, timedelta, datetime
import functools
import os
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
from ..dataflows import interface
from ..default_config import DEFAULT_CONFIG
from langchain_core.messages import HumanMessage
from .tool_caching import cache_tool_result

# IMPORTANT: Pandas import moved to lazy loading to prevent circular imports
# This fixes the Studio compilation error where pandas circular import occurs

def _get_pandas():
    """Lazy loader for pandas to prevent circular import issues"""
    try:
        import pandas as pd
        return pd
    except ImportError as e:
        raise ImportError(f"Pandas is required but not available: {e}")


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages


class Toolkit:
    _config = DEFAULT_CONFIG.copy()

    @classmethod
    def update_config(cls, config):
        """Update the class-level configuration."""
        cls._config.update(config)

    @property
    def config(self):
        """Access the configuration."""
        return self._config

    def __init__(self, config=None):
        if config:
            self.update_config(config)

    @staticmethod
    @tool
    def get_reddit_news(
        curr_date: Annotated[str, "Date you want to get news for in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve global news from Reddit within a specified time frame.
        Args:
            curr_date (str): Date you want to get news for in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the latest global news from Reddit in the specified time frame.
        """
        
        global_news_result = interface.get_reddit_global_news(curr_date, 7, 5)

        return global_news_result

    @staticmethod
    @tool
    @cache_tool_result(ttl=300)  # Cache for 5 minutes
    def get_finnhub_news(
        ticker: Annotated[
            str,
            "Search query of a company, e.g. 'AAPL, TSM, etc.",
        ],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock from Finnhub within a date range
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing news about the company within the date range from start_date to end_date
        """

        end_date_str = end_date

        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        look_back_days = (end_date - start_date).days

        finnhub_news_result = interface.get_finnhub_news(
            ticker, end_date_str, look_back_days
        )

        return finnhub_news_result

    @staticmethod
    @tool
    def get_reddit_stock_info(
        ticker: Annotated[
            str,
            "Ticker of a company. e.g. AAPL, TSM",
        ],
        curr_date: Annotated[str, "Current date you want to get news for"],
    ) -> str:
        """
        Retrieve the latest news about a given stock from Reddit, given the current date.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): current date in yyyy-mm-dd format to get news for
        Returns:
            str: A formatted dataframe containing the latest news about the company on the given date
        """

        stock_news_results = interface.get_reddit_company_news(ticker, curr_date, 7, 5)

        return stock_news_results

    @staticmethod
    @tool
    @cache_tool_result(ttl=300)  # Cache for 5 minutes
    def get_YFin_data(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    @cache_tool_result(ttl=300)  # Cache for 5 minutes
    def get_YFin_data_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data_online(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    @cache_tool_result(ttl=300)  # Cache for 5 minutes
    def get_stockstats_indicators_report(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, False
        )

        return result_stockstats

    @staticmethod
    @tool
    @cache_tool_result(ttl=300)  # Cache for 5 minutes
    def get_stockstats_indicators_report_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get - valid options: 'close_50_sma', 'close_200_sma', 'close_10_ema', 'macd', 'macds', 'macdh', 'rsi', 'boll', 'boll_ub', 'boll_lb', 'atr', 'vwma', 'mfi'. Use 'boll' instead of 'bollinger', 'close_50_sma' instead of 'sma'"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, True
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_finnhub_company_insider_sentiment(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[
            str,
            "current date of you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider sentiment information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the sentiment in the past 30 days starting at curr_date
        """

        data_sentiment = interface.get_finnhub_company_insider_sentiment(
            ticker, curr_date, 30
        )

        return data_sentiment

    @staticmethod
    @tool
    def get_finnhub_company_insider_transactions(
        ticker: Annotated[str, "ticker symbol"],
        curr_date: Annotated[
            str,
            "current date you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider transaction information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's insider transactions/trading information in the past 30 days
        """

        data_trans = interface.get_finnhub_company_insider_transactions(
            ticker, curr_date, 30
        )

        return data_trans

    @staticmethod
    @tool
    def get_simfin_balance_sheet(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent balance sheet of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's most recent balance sheet
        """

        data_balance_sheet = interface.get_simfin_balance_sheet(ticker, freq, curr_date)

        return data_balance_sheet

    @staticmethod
    @tool
    def get_simfin_cashflow(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent cash flow statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent cash flow statement
        """

        data_cashflow = interface.get_simfin_cashflow(ticker, freq, curr_date)

        return data_cashflow

    @staticmethod
    @tool
    def get_simfin_income_stmt(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent income statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent income statement
        """

        data_income_stmt = interface.get_simfin_income_statements(
            ticker, freq, curr_date
        )

        return data_income_stmt

    @staticmethod
    @tool
    async def get_google_news(
        query: Annotated[str, "Query to search with"],
        curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news from Google News based on a query and date range.
        Args:
            query (str): Query to search with
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): How many days to look back
        Returns:
            str: A formatted string containing the latest news from Google News based on the query and date range.
        """

        google_news_results = await interface.get_google_news(query, curr_date, 7)

        return google_news_results

    @staticmethod
    @tool
    async def get_stock_news_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest news about the company on the given date.
        """

        openai_news_results = await interface.get_stock_news_openai(ticker, curr_date)

        return openai_news_results

    @staticmethod
    @tool
    async def get_global_news_openai(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest macroeconomics news on a given date using OpenAI's macroeconomics news API.
        Args:
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest macroeconomic news on the given date.
        """

        openai_news_results = await interface.get_global_news_openai(curr_date)

        return openai_news_results

    @staticmethod
    @tool
    async def get_fundamentals_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest fundamental information about a given stock on a given date by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest fundamental information about the company on the given date.
        """

        openai_fundamentals_results = await interface.get_fundamentals_openai(
            ticker, curr_date
        )

        return openai_fundamentals_results
    
    # Task 7.4.3: New placeholder tools for enhanced coverage
    @staticmethod
    @tool
    async def get_stocktwits_sentiment(
        ticker: Annotated[str, "the company's ticker"],
    ):
        """
        Get StockTwits sentiment data for a given stock ticker.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
        Returns:
            str: A formatted string containing StockTwits sentiment data.
        """
        from ..dataflows.interface_new_tools import get_stocktwits_sentiment as _get_stocktwits
        result = await _get_stocktwits(ticker)
        return str(result)
    
    @staticmethod
    @tool
    async def get_twitter_mentions(
        ticker: Annotated[str, "the company's ticker"],
    ):
        """
        Get Twitter/X mentions and sentiment for a given stock ticker.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
        Returns:
            str: A formatted string containing Twitter mention data.
        """
        from ..dataflows.interface_new_tools import get_twitter_mentions as _get_twitter
        result = await _get_twitter(ticker)
        return str(result)
    
    @staticmethod
    @tool
    async def get_volume_analysis(
        ticker: Annotated[str, "the company's ticker"],
    ):
        """
        Get volume analysis and unusual activity detection for a given stock.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
        Returns:
            str: A formatted string containing volume analysis data.
        """
        from ..dataflows.interface_new_tools import get_volume_analysis as _get_volume
        result = await _get_volume(ticker)
        return str(result)
    
    @staticmethod
    @tool
    async def get_support_resistance(
        ticker: Annotated[str, "the company's ticker"],
    ):
        """
        Get support and resistance levels for a given stock.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
        Returns:
            str: A formatted string containing support/resistance levels.
        """
        from ..dataflows.interface_new_tools import get_support_resistance as _get_sr
        result = await _get_sr(ticker)
        return str(result)
    
    # Priority 2: Create Async Market Data Fetcher
    async def get_all_market_data(
        self,
        symbol: Annotated[str, "ticker symbol of the company"],
        date: Annotated[str, "The trading date in YYYY-mm-dd format"],
    ) -> dict:
        """
        Get all market data in parallel for maximum performance.
        
        This is the implementation for Priority 2: Async Market Data Fetcher.
        Fetches price data and all technical indicators concurrently.
        
        Args:
            symbol: Stock ticker symbol
            date: Trading date
            
        Returns:
            Dictionary containing all market data
        """
        import asyncio
        
        # Define all the data fetching tasks
        tasks = []
        
        # Price data task
        async def get_price_data():
            try:
                # For YFin data, we need start and end dates
                start_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
                return ("price_data", self.get_YFin_data(symbol, start_date, date))
            except Exception as e:
                return ("price_data", f"Error fetching price data: {str(e)}")
        
        # Technical indicator tasks
        indicators = ["close_50_sma", "close_200_sma", "macd", "rsi"]
        
        async def get_indicator(indicator_name):
            try:
                return (indicator_name, self.get_stockstats_indicators_report(symbol, indicator_name, date))
            except Exception as e:
                return (indicator_name, f"Error fetching {indicator_name}: {str(e)}")
        
        # Add price data task
        tasks.append(get_price_data())
        
        # Add indicator tasks
        for indicator in indicators:
            tasks.append(get_indicator(indicator))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks)
        
        # Convert results to dictionary
        market_data = {}
        for key, value in results:
            market_data[key] = value
        
        return self._combine_market_data(market_data)
    
    def _combine_market_data(self, results: dict) -> str:
        """
        Combine all market data results into a formatted string.
        
        Args:
            results: Dictionary of market data results
            
        Returns:
            Formatted string with all market data
        """
        combined_report = "=== COMPREHENSIVE MARKET DATA ===\n\n"
        
        # Add price data
        if "price_data" in results:
            combined_report += "📈 PRICE DATA:\n"
            combined_report += results["price_data"] + "\n\n"
        
        # Add technical indicators
        combined_report += "📊 TECHNICAL INDICATORS:\n"
        for indicator in ["close_50_sma", "close_200_sma", "macd", "rsi"]:
            if indicator in results:
                combined_report += f"\n{indicator.upper()}:\n"
                combined_report += results[indicator] + "\n"
        
        return combined_report
    
    # Async versions of existing methods for parallel execution
    async def get_YFin_data_async(self, symbol: str, start_date: str, end_date: str) -> str:
        """Async wrapper for get_YFin_data."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_YFin_data, symbol, start_date, end_date)
    
    async def get_stockstats_indicators_async(self, symbol: str, indicator: str, date: str) -> str:
        """Async wrapper for get_stockstats_indicators_report."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_stockstats_indicators_report, symbol, indicator, date)
