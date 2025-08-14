#!/usr/bin/env python3
"""
Debug Fundamentals Data Structure
Investigate why some sections are missing from the comprehensive report.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from src.agent.analysts.fundamentals_analyst_crypto_aware import create_fundamentals_analyst_crypto_aware

async def debug_fundamentals_data():
    """Debug the fundamentals data structure to see what's missing."""
    print("🔍 FUNDAMENTALS DATA STRUCTURE DEBUG")
    print("=" * 50)
    
    # Create test state
    test_state = {
        "company_of_interest": "GOOG",
        "trade_date": "2025-08-14",
        "finnhub_key": os.environ.get('FINNHUB_API_KEY')
    }
    
    try:
        fundamentals_node = create_fundamentals_analyst_crypto_aware()
        result = await fundamentals_node(test_state)
        
        fundamentals_data = result.get('fundamentals_data', {})
        
        if not fundamentals_data:
            print("❌ No fundamentals_data found")
            return
            
        print(f"📊 Top-level keys ({len(fundamentals_data)}):")
        for key in fundamentals_data.keys():
            print(f"  - {key}")
            
        # Check specific financial statement sections
        sections_to_debug = [
            'income_statement',
            'balance_sheet', 
            'cash_flow',
            'earnings_history',
            'earnings_calendar'
        ]
        
        for section in sections_to_debug:
            print(f"\n🔍 DEBUGGING {section.upper()}:")
            data = fundamentals_data.get(section, {})
            
            if not data:
                print(f"  ❌ {section} is empty or missing")
                continue
                
            print(f"  📊 Type: {type(data)}")
            print(f"  📊 Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            # Check for 'financials' array
            if isinstance(data, dict) and 'financials' in data:
                financials = data['financials']
                print(f"  📊 Financials array length: {len(financials) if isinstance(financials, list) else 'Not a list'}")
                
                if isinstance(financials, list) and len(financials) > 0:
                    first_item = financials[0]
                    print(f"  📊 First item type: {type(first_item)}")
                    if isinstance(first_item, dict):
                        print(f"  📊 First item keys: {list(first_item.keys())}")
                        # Show a few sample values
                        sample_keys = list(first_item.keys())[:5]
                        for key in sample_keys:
                            print(f"    - {key}: {first_item[key]}")
                    else:
                        print(f"  📊 First item content: {first_item}")
                else:
                    print(f"  ❌ Financials array is empty")
            else:
                # Show raw content for debugging
                if isinstance(data, dict):
                    print(f"  📊 Raw data keys: {list(data.keys())}")
                    # Show first few items
                    for i, (k, v) in enumerate(data.items()):
                        if i >= 3:
                            break
                        print(f"    - {k}: {type(v)} = {str(v)[:100]}...")
                else:
                    print(f"  📊 Raw data: {str(data)[:200]}...")
                    
        # Check endpoints success
        endpoints_fetched = fundamentals_data.get('endpoints_fetched', 0)
        endpoints_total = fundamentals_data.get('endpoints_total', 15)
        
        print(f"\n📈 API ENDPOINTS:")
        print(f"  Fetched: {endpoints_fetched}/{endpoints_total}")
        print(f"  Success Rate: {(endpoints_fetched/endpoints_total)*100:.1f}%")
        
        if endpoints_fetched < endpoints_total:
            print(f"  ⚠️ Some endpoints failed - this may explain missing sections")
        
        # Save debug data to file for inspection
        debug_file = "debug_fundamentals_structure.json"
        with open(debug_file, 'w') as f:
            json.dump(fundamentals_data, f, indent=2, default=str)
        print(f"\n💾 Full data saved to: {debug_file}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_fundamentals_data())