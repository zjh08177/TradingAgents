#!/usr/bin/env python3
"""
Diagnose the exact structure of Yahoo Finance data to understand field names.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

async def diagnose_yahoo_structure():
    """Examine the actual Yahoo Finance data structure"""
    
    from agent.dataflows.yahoo_fundamentals_fallback import try_yahoo_fallback
    
    print("🔍 DIAGNOSING YAHOO FINANCE DATA STRUCTURE")
    print("=" * 60)
    
    ticker = "GOOGL"
    blocked_statements = ['balance_sheet', 'income_statement', 'cash_flow']
    
    print(f"📊 Testing {ticker} with blocked statements: {blocked_statements}")
    print()
    
    try:
        yahoo_results = await try_yahoo_fallback(ticker, blocked_statements)
        
        print(f"📈 Yahoo results keys: {list(yahoo_results.keys())}")
        print()
        
        for statement_type, data in yahoo_results.items():
            print(f"🔍 {statement_type.upper()} ANALYSIS:")
            print(f"  Type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"  Top-level keys: {list(data.keys())}")
                
                if 'financials' in data:
                    financials = data['financials']
                    print(f"  Financials type: {type(financials)}")
                    
                    if isinstance(financials, list) and len(financials) > 0:
                        latest = financials[0]
                        print(f"  Latest record type: {type(latest)}")
                        
                        if isinstance(latest, dict):
                            print(f"  Latest record keys (first 5): {list(latest.keys())[:5]}")
                            print(f"  Latest record key types: {[type(k).__name__ for k in list(latest.keys())[:5]]}")
                            
                            # The keys are Timestamps, values are the actual data we need
                            print(f"  🔍 EXAMINING DATA STRUCTURE:")
                            for i, (timestamp, value) in enumerate(list(latest.items())[:3]):
                                print(f"    Timestamp {i}: {timestamp} -> Value: {value} (type: {type(value)})")
                                
                            # This suggests the data is structured as {timestamp: value} not {field_name: value}
                            # We need to examine the actual data structure
                            
                        else:
                            print(f"  Latest record is not a dict: {latest}")
                    else:
                        print(f"  Financials is empty or not a list")
                        
                # Let's also check if there are other keys
                for key, value in data.items():
                    if key != 'financials':
                        print(f"  Additional key '{key}': {type(value)} - {value}")
            print("-" * 40)
    
    except Exception as e:
        print(f"💥 ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose_yahoo_structure())