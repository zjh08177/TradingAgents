import json
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio
import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
)


def is_rate_limited(response):
    """Check if the response indicates rate limiting (status code 429)"""
    return response.status_code == 429


@retry(
    retry=(retry_if_result(is_rate_limited)),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
)
async def make_request(url, headers):
    """Make an async request with retry logic for rate limiting"""
    # Random delay before each request to avoid detection
    await asyncio.sleep(random.uniform(2, 6))
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    return response


async def getNewsDataGoogleNews(query: str, start_date: str, end_date: str) -> list:
    """
    Get news data from Google News using async httpx.
    """
    try:
        # Build the search query
        query = query.replace(" ", "+")
        search_url = f"https://news.google.com/search?q={query}+after:{start_date}+before:{end_date}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = await make_request(search_url, headers)
        response.raise_for_status()
        
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract news articles (this is a simplified example)
        articles = []
        for article in soup.find_all('article'):
            title = article.find('h3')
            link = article.find('a')
            snippet = article.find('p')
            
            if title and link:
                articles.append({
                    'title': title.get_text(strip=True),
                    'link': link.get('href', ''),
                    'snippet': snippet.get_text(strip=True) if snippet else '',
                    'date': 'N/A',  # Google News doesn't always provide clear dates
                    'source': 'Google News'
                })
        
        return articles
        
    except Exception as e:
        print(f"Error fetching Google News data: {e}")
        return []
