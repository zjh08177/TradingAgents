import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_serper_articles():
    """Mock Serper API response"""
    return [
        {
            "title": "Apple Stock Rises on Strong Earnings",
            "source": "Reuters",
            "date": "2024-01-14",
            "link": "https://reuters.com/1",
            "snippet": "Apple Inc reported better than expected quarterly earnings with revenue beating analyst estimates by 5%...",
            "position": 1,
            "imageUrl": "https://example.com/image1.jpg"
        },
        {
            "title": "Tech Giants Lead Market Rally",
            "source": "Bloomberg",
            "date": "2024-01-14",
            "link": "https://bloomberg.com/2",
            "snippet": "Technology stocks including Apple, Microsoft, and Google led a broad market rally on Tuesday...",
            "position": 2
        },
        {
            "title": "Apple Announces New Product Launch",
            "source": "CNBC",
            "date": "2024-01-13",
            "link": "https://cnbc.com/3",
            "snippet": "Apple is set to unveil its latest product lineup at an event scheduled for next month...",
            "position": 3
        },
        {
            "title": "iPhone Sales Beat Expectations",
            "source": "Wall Street Journal",
            "date": "2024-01-13",
            "link": "https://wsj.com/4",
            "snippet": "Apple's iPhone sales exceeded analyst expectations for the holiday quarter, driving revenue growth...",
            "position": 4
        },
        {
            "title": "Apple's AI Strategy Gains Momentum",
            "source": "Financial Times",
            "date": "2024-01-12",
            "link": "https://ft.com/5",
            "snippet": "Apple is accelerating its artificial intelligence initiatives with new partnerships and research investments...",
            "position": 5
        }
    ]


@pytest.fixture
def mock_finnhub_response():
    """Mock Finnhub API response"""
    return """
    Title: Tech Stocks Rally on Earnings Optimism
    Summary: Technology stocks led market gains as investors showed renewed optimism ahead of earnings season.
    Source: Bloomberg
    Date: 2024-01-14
    URL: https://bloomberg.com/tech-rally
    
    Title: Apple Expands Services Revenue
    Summary: Apple's services division continues to show strong growth, offsetting slower hardware sales.
    Source: Reuters
    Date: 2024-01-14
    URL: https://reuters.com/apple-services
    
    Title: Market Analysis: Tech Sector Outlook
    Summary: Analysts remain bullish on technology sector despite macroeconomic headwinds.
    Source: MarketWatch
    Date: 2024-01-13
    URL: https://marketwatch.com/tech-outlook
    """


@pytest.fixture
def mock_toolkit():
    """Mock toolkit with API methods"""
    toolkit = Mock()
    toolkit.config = {"serper_key": "test_key", "finnhub_key": "test_key"}
    toolkit.get_finnhub_news = Mock()
    toolkit.get_finnhub_news.invoke = Mock(return_value=mock_finnhub_response())
    return toolkit


@pytest.fixture
def sample_state():
    """Sample state for testing"""
    return {
        "company_of_interest": "AAPL",
        "trade_date": "2024-01-14",
        "messages": [],
        "sender": "test"
    }


@pytest.fixture
def large_article_set():
    """Generate a large set of test articles"""
    articles = []
    sources = ["Reuters", "Bloomberg", "CNBC", "WSJ", "Financial Times", "MarketWatch", "Forbes"]
    
    for i in range(100):
        articles.append({
            "title": f"News Article {i}: Market Update",
            "source": sources[i % len(sources)],
            "date": f"2024-01-{14 - (i // 10)}",
            "link": f"https://example.com/article_{i}",
            "snippet": f"This is the content of article {i}. " * 10,  # Substantial content
            "position": i + 1
        })
    
    return articles


@pytest.fixture
def empty_news_data():
    """Empty news data structure"""
    return {
        "serper_articles": [],
        "finnhub_articles": [],
        "total_articles": 0,
        "sources_attempted": 2,
        "sources_successful": 0,
        "data_fetch_time": 0.5
    }


@pytest.fixture
def full_news_data(mock_serper_articles):
    """Full news data structure with articles"""
    return {
        "serper_articles": mock_serper_articles,
        "finnhub_articles": [
            {
                "headline": "Tech Stocks Rally",
                "summary": "Technology stocks led gains",
                "source": "Bloomberg",
                "date": "2024-01-14",
                "url": "https://bloomberg.com/1"
            },
            {
                "headline": "Apple Services Growth",
                "summary": "Services revenue expands",
                "source": "Reuters",
                "date": "2024-01-14",
                "url": "https://reuters.com/2"
            }
        ],
        "total_articles": 7,
        "sources_attempted": 2,
        "sources_successful": 2,
        "data_fetch_time": 1.5
    }