#!/usr/bin/env python3
"""
Debug EPS data structure to identify field names
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def debug_eps_data():
    """Check what EPS fields are available in the raw data."""
    print("🔍 DEBUGGING EPS DATA STRUCTURE")
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
        
        # Check income statement for EPS-related fields
        if 'income_statement' in data:
            income = data['income_statement']
            print(f"\n📊 INCOME STATEMENT KEYS:")
            if 'financials' in income:
                for entry in income['financials'][:2]:  # Show first 2 entries
                    print(f"  📅 Entry keys: {list(entry.keys())[:15]}...")  # First 15 keys
                    
                    # Look for any EPS-related fields
                    eps_fields = [k for k in entry.keys() if 'eps' in k.lower() or 'earnings' in k.lower() or 'share' in k.lower()]
                    if eps_fields:
                        print(f"  🎯 EPS-related fields: {eps_fields}")
                        for field in eps_fields:
                            print(f"     {field}: {entry.get(field)}")
                    break
        
        # Check earnings history  
        if 'earnings_history' in data:
            earnings = data['earnings_history']
            print(f"\n📈 EARNINGS HISTORY:")
            if 'earnings' in earnings:
                for entry in earnings['earnings'][:3]:  # Show first 3
                    print(f"  📅 {entry.get('period')}: actual={entry.get('actual')}, estimate={entry.get('estimate')}")
                    
        # Check metrics for EPS
        if 'metrics' in data:
            metrics = data['metrics']
            print(f"\n📊 METRICS KEYS:")
            print(f"  Keys: {list(metrics.keys())[:20]}...")
            
            # Look for EPS in metrics
            eps_fields = [k for k in metrics.keys() if 'eps' in k.lower()]
            if eps_fields:
                print(f"  🎯 EPS fields in metrics: {eps_fields}")
                for field in eps_fields:
                    print(f"     {field}: {metrics.get(field)}")
        
        # Check if we can calculate EPS manually
        if 'metrics' in data:
            metrics = data['metrics']
            net_income = metrics.get('netIncomeCommonStockholders')
            shares = metrics.get('sharesOutstanding') 
            
            if net_income and shares:
                calculated_eps = net_income / shares
                print(f"\n🧮 MANUAL EPS CALCULATION:")
                print(f"  Net Income: ${net_income:,.0f}M")
                print(f"  Shares Outstanding: {shares:,.0f}M")
                print(f"  Calculated EPS: ${calculated_eps:.2f}")
        
        await collector.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 DEBUG COMPLETE")

if __name__ == "__main__":
    asyncio.run(debug_eps_data())