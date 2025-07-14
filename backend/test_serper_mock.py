#!/usr/bin/env python3
"""
Mock test script for Serper API functionality
This script tests the Serper API implementation structure without requiring a real API key
"""

import os
import sys
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.serper_utils import (
    getNewsDataSerperAPI,
    getNewsDataSerperAPIWithPagination,
    getNewsDataSerpAPI,  # Legacy function
    getNewsDataSerpAPIWithPagination  # Legacy function
)

def mock_serper_response():
    """Create a mock response that matches Serper API structure"""
    return {
        "news": [
            {
                "title": "Apple Stock Reaches New High",
                "link": "https://example.com/news1",
                "snippet": "Apple Inc. stock reached a new high today amid strong earnings expectations.",
                "date": "2 hours ago",
                "source": "Financial News"
            },
            {
                "title": "Tesla Reports Strong Q3 Results",
                "link": "https://example.com/news2", 
                "snippet": "Tesla Motors reported better than expected quarterly results.",
                "date": "1 day ago",
                "source": "Tech Times"
            }
        ]
    }

def test_serper_api_structure():
    """Test Serper API function structure with mocked response"""
    print("=" * 60)
    print("🧪 Testing Serper API Structure (Mocked)")
    print("=" * 60)
    
    with patch('requests.post') as mock_post:
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = mock_serper_response()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test parameters
        query = "AAPL stock"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        print(f"Query: {query}")
        print(f"Date range: {start_date} to {end_date}")
        print()
        
        try:
            # Test the function with a mock API key
            results = getNewsDataSerperAPI(query, start_date, end_date, "mock_api_key")
            
            print(f"✅ Function executed successfully")
            print(f"✅ Retrieved {len(results)} results")
            
            # Verify structure
            if results:
                sample = results[0]
                expected_keys = {'title', 'link', 'snippet', 'date', 'source'}
                actual_keys = set(sample.keys())
                
                if expected_keys.issubset(actual_keys):
                    print("✅ Result structure is correct")
                    print(f"  Sample title: {sample['title']}")
                    print(f"  Sample source: {sample['source']}")
                else:
                    print(f"❌ Result structure mismatch. Expected: {expected_keys}, Got: {actual_keys}")
                    return False
            
            # Verify API call was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check URL
            expected_url = "https://google.serper.dev/news"
            if call_args[0][0] == expected_url:
                print("✅ API URL is correct")
            else:
                print(f"❌ API URL mismatch. Expected: {expected_url}, Got: {call_args[0][0]}")
                return False
            
            # Check headers
            headers = call_args[1]['headers']
            if 'X-API-KEY' in headers and headers['X-API-KEY'] == 'mock_api_key':
                print("✅ API key header is correct")
            else:
                print("❌ API key header is missing or incorrect")
                return False
            
            # Check payload structure
            payload = call_args[1]['json']
            required_payload_keys = {'q', 'gl', 'hl', 'num'}
            if required_payload_keys.issubset(set(payload.keys())):
                print("✅ Request payload structure is correct")
            else:
                print(f"❌ Request payload missing required keys. Expected: {required_payload_keys}, Got: {payload.keys()}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

def test_error_handling():
    """Test error handling with mocked API errors"""
    print("\n" + "=" * 60)
    print("🧪 Testing Error Handling (Mocked)")
    print("=" * 60)
    
    with patch('requests.post') as mock_post:
        # Mock HTTP error
        mock_post.side_effect = Exception("Connection error")
        
        query = "test"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        print("Testing with mocked connection error...")
        
        try:
            results = getNewsDataSerperAPI(query, start_date, end_date, "mock_api_key")
            
            # Should return empty list on error, not raise exception
            if len(results) == 0:
                print("✅ Error handling works correctly - returned empty list")
                return True
            else:
                print("⚠️ Unexpected: Got results despite error")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected exception raised: {str(e)}")
            return False

def test_legacy_functions():
    """Test legacy function compatibility with mocking"""
    print("\n" + "=" * 60)
    print("🧪 Testing Legacy Function Compatibility (Mocked)")
    print("=" * 60)
    
    with patch('requests.post') as mock_post:
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = mock_serper_response()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        query = "Microsoft earnings"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        
        print(f"Query: {query}")
        print(f"Date range: {start_date} to {end_date}")
        print()
        
        try:
            # Test the legacy function (should redirect to Serper API)
            results = getNewsDataSerpAPI(query, start_date, end_date, "mock_api_key")
            
            print(f"✅ Legacy function executed successfully")
            print(f"✅ Retrieved {len(results)} results via legacy function")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

def test_pagination_structure():
    """Test pagination function structure"""
    print("\n" + "=" * 60)
    print("🧪 Testing Pagination Function Structure (Mocked)")
    print("=" * 60)
    
    with patch('requests.post') as mock_post:
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = mock_serper_response()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        query = "Tesla stock news"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        max_results = 5
        
        print(f"Query: {query}")
        print(f"Date range: {start_date} to {end_date}")
        print(f"Max results: {max_results}")
        print()
        
        try:
            results = getNewsDataSerperAPIWithPagination(query, start_date, end_date, max_results, "mock_api_key")
            
            print(f"✅ Pagination function executed successfully")
            print(f"✅ Retrieved {len(results)} results")
            
            # Should not exceed max_results
            if len(results) <= max_results:
                print("✅ Result count respects max_results limit")
            else:
                print(f"❌ Result count ({len(results)}) exceeds max_results ({max_results})")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

def main():
    """Run all mock tests"""
    print("🚀 Starting Serper API Mock Tests")
    print("=" * 60)
    print("ℹ️  These tests use mocked responses to verify function structure")
    print("ℹ️  No real API key required")
    print()
    
    tests = [
        test_serper_api_structure,
        test_error_handling,
        test_legacy_functions,
        test_pagination_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MOCK TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All mock tests passed! Serper API structure is correct.")
        print("💡 To test with real API: set SERPER_API_KEY and run test_serper_api.py")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 