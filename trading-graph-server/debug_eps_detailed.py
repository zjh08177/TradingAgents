#!/usr/bin/env python3
"""
Detailed EPS debugging with actual values
"""
import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to Python path  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def debug_eps_detailed():
    """Detailed debug of EPS data."""
    print("🔍 DETAILED EPS DEBUGGING")
    print("=" * 50)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from src.agent.dataflows.ultra_fast_fundamentals_collector import UltraFastFundamentalsCollector
        
        finnhub_key = os.environ.get('FINNHUB_API_KEY')
        collector = UltraFastFundamentalsCollector(finnhub_key)
        
        print("🚀 Getting raw TSLA data from collector...")
        data = await collector.get("TSLA")
        
        print(f"\n📊 TOP-LEVEL DATA KEYS: {list(data.keys())}")
        
        # Look for EPS in earnings history (which we know works)
        if 'earnings_history' in data:
            earnings = data['earnings_history']
            print(f"\n📈 EARNINGS HISTORY STRUCTURE:")
            print(f"  Type: {type(earnings)}")
            print(f"  Keys: {list(earnings.keys()) if isinstance(earnings, dict) else 'Not a dict'}")
            
            if 'earnings' in earnings:
                earnings_data = earnings['earnings']
                print(f"  Earnings data type: {type(earnings_data)}")
                if earnings_data:
                    print(f"  First entry: {earnings_data[0] if len(earnings_data) > 0 else 'Empty'}")
        
        # Check income statement structure
        if 'income_statement' in data:
            income = data['income_statement']
            print(f"\n💰 INCOME STATEMENT STRUCTURE:")
            print(f"  Type: {type(income)}")
            print(f"  Keys: {list(income.keys()) if isinstance(income, dict) else 'Not a dict'}")
            
            # If there's an error, show it
            if 'error' in income:
                print(f"  ❌ ERROR: {income['error']}")
            elif 'financials' in income:
                financials = income['financials']
                print(f"  Financials type: {type(financials)}")
                if financials and len(financials) > 0:
                    first_entry = financials[0]
                    print(f"  Sample financial entry keys: {list(first_entry.keys())[:10]}...")
                    
                    # Look specifically for EPS patterns
                    all_keys = list(first_entry.keys())
                    eps_keys = [k for k in all_keys if 'eps' in k.lower()]
                    earnings_keys = [k for k in all_keys if 'earnings' in k.lower()]
                    share_keys = [k for k in all_keys if 'share' in k.lower()]
                    
                    print(f"  EPS keys: {eps_keys}")
                    print(f"  Earnings keys: {earnings_keys}")
                    print(f"  Share keys: {share_keys}")
        
        # Check metrics structure
        if 'metrics' in data:
            metrics = data['metrics']
            print(f"\n📊 METRICS STRUCTURE:")
            print(f"  Type: {type(metrics)}")
            if isinstance(metrics, dict):
                print(f"  Keys: {list(metrics.keys())}")
                # Show actual values for debugging
                print(f"  Sample values: {dict(list(metrics.items())[:5])}")
        
        await collector.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 DETAILED DEBUG COMPLETE")

if __name__ == "__main__":
    asyncio.run(debug_eps_detailed())