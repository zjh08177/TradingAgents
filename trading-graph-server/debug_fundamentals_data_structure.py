#!/usr/bin/env python3
"""
Debug Fundamentals Data Structure
Investigates the actual keys and structure returned by the ultra-fast collector
to identify why price_targets and EPS are showing as $0.00
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.dataflows.ultra_fast_fundamentals_collector import UltraFastFundamentalsCollector

async def debug_data_structure(ticker: str = "TSLA"):
    """Debug the actual data structure returned by the collector."""
    print(f"🔍 DEBUGGING FUNDAMENTALS DATA STRUCTURE FOR {ticker}")
    print("=" * 80)
    
    # Get API key
    finnhub_key = os.environ.get('FINNHUB_API_KEY')
    if not finnhub_key:
        print("❌ FINNHUB_API_KEY not found in environment")
        return
    
    # Create collector
    collector = UltraFastFundamentalsCollector(finnhub_key)
    
    try:
        # Fetch data
        print(f"🚀 Fetching data for {ticker}...")
        data = await collector.get(ticker)
        
        # Check for error first
        if 'error' in data:
            print(f"❌ API ERROR DETECTED!")
            print(f"📊 Error: {data.get('error')}")
            print(f"🎫 Ticker: {data.get('ticker')}")
            print(f"⏰ Timestamp: {data.get('timestamp')}")
            print()
            print("🚨 This explains why price targets and EPS are $0.00!")
            print("   The collector is not successfully fetching data.")
            
            # Print traceback if available
            if 'traceback' in data:
                print()
                print("📍 DETAILED TRACEBACK:")
                print(data['traceback'])
            
            return
        
        print(f"✅ Data fetched successfully!")
        print(f"📊 Top-level keys: {list(data.keys())}")
        print()
        
        # Debug price targets specifically
        print("🎯 PRICE TARGETS INVESTIGATION:")
        if 'price_targets' in data:
            price_targets = data['price_targets']
            print(f"  ✅ price_targets found: {type(price_targets)}")
            if isinstance(price_targets, dict):
                print(f"  🔑 Keys: {list(price_targets.keys())}")
                for key, value in price_targets.items():
                    print(f"    {key}: {value}")
            else:
                print(f"  📄 Content: {price_targets}")
        else:
            print("  ❌ price_targets key NOT FOUND")
            # Check for similar keys
            target_keys = [k for k in data.keys() if 'price' in k.lower() or 'target' in k.lower()]
            if target_keys:
                print(f"  🔍 Similar keys found: {target_keys}")
                for key in target_keys:
                    print(f"    {key}: {data[key]}")
        print()
        
        # Debug income statement and EPS
        print("💰 INCOME STATEMENT & EPS INVESTIGATION:")
        if 'income_statement' in data:
            income_stmt = data['income_statement']
            print(f"  ✅ income_statement found: {type(income_stmt)}")
            
            if isinstance(income_stmt, dict):
                print(f"  🔑 Top-level keys: {list(income_stmt.keys())}")
                
                # Look for quarterly data (latest)
                quarterly_data = income_stmt.get('quarterly', income_stmt.get('annual', {}))
                if quarterly_data:
                    print(f"  📊 Quarterly/Latest data type: {type(quarterly_data)}")
                    
                    if isinstance(quarterly_data, list) and len(quarterly_data) > 0:
                        latest = quarterly_data[0]  # Most recent quarter
                        print(f"  📅 Latest quarter keys: {list(latest.keys()) if isinstance(latest, dict) else 'Not a dict'}")
                        
                        # Search for EPS-related keys
                        eps_keys = [k for k in latest.keys() if 'eps' in k.lower() if isinstance(latest, dict)]
                        print(f"  🔍 EPS-related keys: {eps_keys}")
                        for key in eps_keys:
                            print(f"    {key}: {latest[key]}")
                        
                        # Search for earnings keys
                        earnings_keys = [k for k in latest.keys() if 'earning' in k.lower() if isinstance(latest, dict)]
                        print(f"  🔍 Earnings-related keys: {earnings_keys}")
                        for key in earnings_keys:
                            print(f"    {key}: {latest[key]}")
                    else:
                        print(f"  📄 Quarterly data content: {quarterly_data}")
            else:
                print(f"  📄 Income statement content: {income_stmt}")
        else:
            print("  ❌ income_statement key NOT FOUND")
        print()
        
        # Debug recommendations (might contain price targets)
        print("🎯 RECOMMENDATIONS INVESTIGATION (possible price targets source):")
        if 'recommendations' in data:
            recommendations = data['recommendations'] 
            print(f"  ✅ recommendations found: {type(recommendations)}")
            if isinstance(recommendations, list) and len(recommendations) > 0:
                sample = recommendations[0]
                print(f"  📊 First recommendation keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
                print(f"  📄 Sample content: {sample}")
            elif isinstance(recommendations, dict):
                print(f"  🔑 Keys: {list(recommendations.keys())}")
                print(f"  📄 Content: {recommendations}")
            else:
                print(f"  📄 Content: {recommendations}")
        else:
            print("  ❌ recommendations key NOT FOUND")
        print()
        
        # Show all top-level data for complete analysis
        print("📋 COMPLETE DATA STRUCTURE:")
        for key, value in data.items():
            print(f"  {key}: {type(value)}")
            if isinstance(value, dict):
                print(f"    └─ Keys: {list(value.keys())}")
            elif isinstance(value, list):
                print(f"    └─ Length: {len(value)}")
                if len(value) > 0:
                    print(f"    └─ First item type: {type(value[0])}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await collector.close()

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "TSLA"
    asyncio.run(debug_data_structure(ticker))