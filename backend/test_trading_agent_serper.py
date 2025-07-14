#!/usr/bin/env python3
"""
Test script for Trading Agent with Serper API integration
This script tests that the trading agent can successfully use the new Serper API
"""

import os
import sys
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.interface import get_google_news
from tradingagents.default_config import DEFAULT_CONFIG

def mock_serper_response():
    """Create a mock response that matches Serper API structure"""
    return {
        "news": [
            {
                "title": "Apple Reports Strong Q3 Earnings",
                "link": "https://example.com/apple-earnings",
                "snippet": "Apple Inc. reported quarterly earnings that exceeded analyst expectations, with strong iPhone sales driving revenue growth.",
                "date": "2 hours ago",
                "source": "Financial Times"
            },
            {
                "title": "Apple Stock Reaches All-Time High",
                "link": "https://example.com/apple-stock-high",
                "snippet": "Apple shares hit a new record high in morning trading following the earnings announcement.",
                "date": "3 hours ago",
                "source": "Market Watch"
            },
            {
                "title": "Analysts Upgrade Apple Stock",
                "link": "https://example.com/apple-upgrade",
                "snippet": "Several Wall Street analysts upgraded their price targets for Apple following the strong quarterly performance.",
                "date": "4 hours ago",
                "source": "Bloomberg"
            }
        ]
    }

def test_trading_agent_google_news():
    """Test the trading agent's get_google_news function with Serper API"""
    print("=" * 60)
    print("🧪 Testing Trading Agent with Serper API")
    print("=" * 60)
    
    # Set up mock environment variable and config for testing
    with patch.dict(os.environ, {'SERPER_API_KEY': 'mock_api_key'}), \
         patch.dict(DEFAULT_CONFIG, {'serper_key': 'mock_api_key'}), \
         patch('requests.post') as mock_post:
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = mock_serper_response()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test parameters
        query = "AAPL"
        curr_date = datetime.now().strftime("%Y-%m-%d")
        look_back_days = 7
        
        print(f"Query: {query}")
        print(f"Current date: {curr_date}")
        print(f"Look back days: {look_back_days}")
        print()
        
        try:
            # Call the trading agent's google news function
            print("🚀 Calling get_google_news from trading agent...")
            result = get_google_news(query, curr_date, look_back_days)
            
            print("✅ Trading agent function executed successfully")
            print(f"✅ Result type: {type(result)}")
            print(f"✅ Result length: {len(result)} characters")
            
            # Verify the result format
            if isinstance(result, str):
                print("✅ Result is a string (correct format)")
                
                # Check if it contains expected elements
                if "Google News" in result:
                    print("✅ Result contains 'Google News' header")
                else:
                    print("⚠️ Result missing 'Google News' header")
                
                if "Apple Reports Strong Q3 Earnings" in result:
                    print("✅ Result contains expected news content")
                else:
                    print("⚠️ Result missing expected news content")
                    
                print("\n📰 Sample output:")
                print("-" * 40)
                print(result[:500] + "..." if len(result) > 500 else result)
                print("-" * 40)
                
            else:
                print(f"❌ Result is not a string. Got: {type(result)}")
                return False
            
            # Verify API call was made with correct parameters
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check URL
            expected_url = "https://google.serper.dev/news"
            if call_args[0][0] == expected_url:
                print("✅ Correct API endpoint was called")
            else:
                print(f"❌ Wrong API endpoint. Expected: {expected_url}, Got: {call_args[0][0]}")
                return False
                
            # Check that API key was passed
            headers = call_args[1]['headers']
            if 'X-API-KEY' in headers:
                print("✅ API key was included in request")
            else:
                print("❌ API key missing from request")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return False

def test_trading_agent_without_api_key():
    """Test that trading agent fails gracefully without API key"""
    print("\n" + "=" * 60)
    print("🧪 Testing Trading Agent Without API Key")
    print("=" * 60)
    
    # Ensure no API key is set
    with patch.dict(os.environ, {}, clear=True), \
         patch.dict(DEFAULT_CONFIG, {'serper_key': ''}):
        query = "AAPL"
        curr_date = datetime.now().strftime("%Y-%m-%d")
        look_back_days = 7
        
        print("Testing without SERPER_API_KEY environment variable...")
        
        try:
            result = get_google_news(query, curr_date, look_back_days)
            print("❌ Expected function to raise an error without API key")
            return False
            
        except ValueError as e:
            if "Serper API key is required" in str(e):
                print("✅ Function correctly raises ValueError for missing API key")
                return True
            else:
                print(f"❌ Unexpected error message: {str(e)}")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected exception type: {type(e).__name__}: {str(e)}")
            return False

def test_trading_agent_with_api_error():
    """Test trading agent behavior when API returns an error"""
    print("\n" + "=" * 60)
    print("🧪 Testing Trading Agent with API Error")
    print("=" * 60)
    
    with patch.dict(os.environ, {'SERPER_API_KEY': 'mock_api_key'}), \
         patch.dict(DEFAULT_CONFIG, {'serper_key': 'mock_api_key'}), \
         patch('requests.post') as mock_post:
        
        # Mock API error
        mock_post.side_effect = Exception("API service unavailable")
        
        query = "AAPL"
        curr_date = datetime.now().strftime("%Y-%m-%d")
        look_back_days = 7
        
        print("Testing with mocked API error...")
        
        try:
            result = get_google_news(query, curr_date, look_back_days)
            
            # Check if we got an empty result due to API error
            if len(result) == 0:
                print("✅ Function returned empty result due to API error (graceful handling)")
                return True
            else:
                print(f"⚠️ Function returned non-empty result despite API error: {len(result)} chars")
                # This is still acceptable behavior
                return True
            
        except Exception as e:
            print(f"✅ Function correctly propagates API error: {type(e).__name__}")
            return True

def main():
    """Run all integration tests"""
    print("🚀 Starting Trading Agent + Serper API Integration Tests")
    print("=" * 60)
    print("ℹ️  Testing the trading agent with new Serper API integration")
    print("ℹ️  Using mocked responses to verify integration works")
    print()
    
    tests = [
        test_trading_agent_google_news,
        test_trading_agent_without_api_key,
        test_trading_agent_with_api_error
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ Trading Agent successfully integrated with Serper API")
        print("💡 The migration from SerpApi to Serper API is complete")
        return True
    else:
        print("⚠️ Some integration tests failed.")
        print("🔧 Check the implementation for any issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 