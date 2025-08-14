#!/usr/bin/env python3
"""
Force Collector Reset - Clear singleton cache and test with fresh collector
This script will demonstrate the difference before and after collector reset
"""

import asyncio
import os
import sys
from pathlib import Path
import importlib

# Add project root to Python path  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_collector_reset():
    """Test collector with and without reset to show the issue."""
    print("🔧 FORCE COLLECTOR RESET TEST")
    print("=" * 60)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Import the crypto-aware module
    from src.agent.analysts import fundamentals_analyst_crypto_aware
    
    print("📊 STEP 1: Test with current (potentially cached) collector")
    print("-" * 50)
    
    # Create fake state
    state = {
        "company_of_interest": "TSLA",
        "trade_date": "2025-08-14"
    }
    
    # Test with current collector (may be cached/broken)
    try:
        result = await fundamentals_analyst_crypto_aware.create_fundamentals_analyst_crypto_aware()(state)
        report = result.get('fundamentals_report', 'No report')
        
        # Extract price targets info
        if 'PRICE TARGETS:' in report:
            lines = report.split('\n')
            for i, line in enumerate(lines):
                if 'PRICE TARGETS:' in line:
                    print(f"🎯 Found price targets section:")
                    for j in range(i, min(i+8, len(lines))):
                        print(f"   {lines[j]}")
                    break
        else:
            print("❌ No price targets section found")
            
    except Exception as e:
        print(f"❌ Error with current collector: {e}")
    
    print("\n📊 STEP 2: Force reset global collector and test again")  
    print("-" * 50)
    
    # FORCE RESET: Clear the global collector
    print("🔄 Forcing global collector reset...")
    fundamentals_analyst_crypto_aware._global_collector = None
    
    # Also reload the module to ensure fresh imports
    importlib.reload(fundamentals_analyst_crypto_aware)
    
    # Test with fresh collector (should use our fixes)
    try:
        result = await fundamentals_analyst_crypto_aware.create_fundamentals_analyst_crypto_aware()(state)
        report = result.get('fundamentals_report', 'No report')
        
        # Extract price targets info  
        if 'PRICE TARGETS:' in report:
            lines = report.split('\n')
            for i, line in enumerate(lines):
                if 'PRICE TARGETS:' in line:
                    print(f"🎯 Found price targets section (after reset):")
                    for j in range(i, min(i+8, len(lines))):
                        print(f"   {lines[j]}")
                    break
        else:
            print("❌ No price targets section found")
            
    except Exception as e:
        print(f"❌ Error with reset collector: {e}")
    
    print("\n📊 STEP 3: Direct collector test (bypass crypto-aware wrapper)")
    print("-" * 50)
    
    # Test direct collector to verify our fixes
    try:
        from src.agent.dataflows.ultra_fast_fundamentals_collector import UltraFastFundamentalsCollector
        
        finnhub_key = os.environ.get('FINNHUB_API_KEY')
        collector = UltraFastFundamentalsCollector(finnhub_key)
        
        # This should use our fixed version
        data = await collector.get("TSLA")
        
        if 'error' in data:
            print(f"❌ Collector error: {data['error']}")
        else:
            print("✅ Direct collector working!")
            print(f"📊 Keys: {list(data.keys())[:10]}")
            
            if 'price_targets' in data:
                pt = data['price_targets']
                print(f"🎯 Direct price targets: {pt}")
            else:
                print("❌ No price_targets in direct collector data")
                
        await collector.close()
        
    except Exception as e:
        print(f"❌ Direct collector error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 TEST COMPLETE - Check results above!")

if __name__ == "__main__":
    asyncio.run(test_collector_reset())