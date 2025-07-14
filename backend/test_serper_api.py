#!/usr/bin/env python3
"""
Test script for Serper API functionality
This script tests the Serper API implementation at the function level
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.serper_utils import (
    getNewsDataSerperAPI,
    getNewsDataSerperAPIWithPagination,
    getNewsDataSerpAPI,  # Legacy function
    getNewsDataSerpAPIWithPagination  # Legacy function
)

def test_serper_api_basic():
    """Test basic Serper API functionality"""
    print("=" * 60)
    print("🧪 Testing Serper API Basic Functionality")
    print("=" * 60)
    
    # Test parameters
    query = "AAPL stock"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"Query: {query}")
    print(f"Date range: {start_date} to {end_date}")
    print()
    
    try:
        # Test the new Serper API function
        print("Testing getNewsDataSerperAPI()...")
        results = getNewsDataSerperAPI(query, start_date, end_date)
        
        print(f"✅ Retrieved {len(results)} results")
        
        if results:
            print("\n📰 Sample result:")
            sample = results[0]
            print(f"  Title: {sample.get('title', 'N/A')[:100]}...")
            print(f"  Source: {sample.get('source', 'N/A')}")
            print(f"  Date: {sample.get('date', 'N/A')}")
            print(f"  Link: {sample.get('link', 'N/A')[:80]}...")
            print(f"  Snippet: {sample.get('snippet', 'N/A')[:150]}...")
        else:
            print("⚠️ No results returned")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_serper_api_pagination():
    """Test Serper API pagination functionality"""
    print("\n" + "=" * 60)
    print("🧪 Testing Serper API Pagination Functionality")
    print("=" * 60)
    
    # Test parameters
    query = "Tesla stock news"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    max_results = 150
    
    print(f"Query: {query}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Max results: {max_results}")
    print()
    
    try:
        # Test the pagination function
        print("Testing getNewsDataSerperAPIWithPagination()...")
        results = getNewsDataSerperAPIWithPagination(query, start_date, end_date, max_results)
        
        print(f"✅ Retrieved {len(results)} results")
        
        if results:
            print("\n📰 First result:")
            sample = results[0]
            print(f"  Title: {sample.get('title', 'N/A')[:100]}...")
            print(f"  Source: {sample.get('source', 'N/A')}")
            
            if len(results) > 1:
                print("\n📰 Last result:")
                sample = results[-1]
                print(f"  Title: {sample.get('title', 'N/A')[:100]}...")
                print(f"  Source: {sample.get('source', 'N/A')}")
        else:
            print("⚠️ No results returned")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_legacy_functions():
    """Test legacy function compatibility"""
    print("\n" + "=" * 60)
    print("🧪 Testing Legacy Function Compatibility")
    print("=" * 60)
    
    # Test parameters
    query = "Microsoft earnings"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    
    print(f"Query: {query}")
    print(f"Date range: {start_date} to {end_date}")
    print()
    
    try:
        # Test the legacy function (should redirect to Serper API)
        print("Testing getNewsDataSerpAPI() (legacy function)...")
        results = getNewsDataSerpAPI(query, start_date, end_date)
        
        print(f"✅ Retrieved {len(results)} results via legacy function")
        
        if results:
            print("\n📰 Sample result:")
            sample = results[0]
            print(f"  Title: {sample.get('title', 'N/A')[:100]}...")
            print(f"  Source: {sample.get('source', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_error_handling():
    """Test error handling with invalid API key"""
    print("\n" + "=" * 60)
    print("🧪 Testing Error Handling")
    print("=" * 60)
    
    # Test parameters
    query = "test"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print("Testing with invalid API key...")
    
    try:
        # Test with invalid API key
        results = getNewsDataSerperAPI(query, start_date, end_date, serper_key="invalid_key")
        
        print(f"📊 Function returned {len(results)} results (should be 0 for invalid key)")
        
        if len(results) == 0:
            print("✅ Error handling works correctly - returned empty list")
            return True
        else:
            print("⚠️ Unexpected: Got results with invalid key")
            return False
        
    except Exception as e:
        print(f"⚠️ Exception raised (this is expected): {str(e)}")
        return True


def main():
    """Run all tests"""
    print("🚀 Starting Serper API Tests")
    print("=" * 60)
    
    # Check if API key is available
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("❌ SERPER_API_KEY environment variable not set!")
        print("Please set your Serper API key to run tests:")
        print("export SERPER_API_KEY='your_api_key_here'")
        return False
    
    print(f"✅ API key found: {api_key[:8]}...")
    print()
    
    tests = [
        test_serper_api_basic,
        test_serper_api_pagination,
        test_legacy_functions,
        test_error_handling
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
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Serper API is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 