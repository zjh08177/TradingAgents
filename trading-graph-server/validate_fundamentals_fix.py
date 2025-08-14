#!/usr/bin/env python3
"""
Validate Fundamentals Analyst Fix
Test script to verify the comprehensive report generation is working.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from src.agent.analysts.fundamentals_analyst_crypto_aware import create_fundamentals_analyst_crypto_aware

async def test_fundamentals_fix():
    """Test the fixed fundamentals analyst implementation."""
    print("🧪 FUNDAMENTALS ANALYST FIX VALIDATION")
    print("=" * 50)
    
    # Create test state
    test_state = {
        "company_of_interest": "GOOG",
        "trade_date": "2025-08-14",
        "finnhub_key": os.environ.get('FINNHUB_API_KEY')
    }
    
    if not test_state["finnhub_key"]:
        print("❌ No FINNHUB_API_KEY found in environment")
        return False
    
    # Create fundamentals analyst
    print(f"🔍 Testing fundamentals for: {test_state['company_of_interest']}")
    
    try:
        fundamentals_node = create_fundamentals_analyst_crypto_aware()
        
        start_time = time.time()
        result = await fundamentals_node(test_state)
        execution_time = time.time() - start_time
        
        print(f"⚡ Execution time: {execution_time:.3f}s")
        print(f"🎯 Report length: {len(result.get('fundamentals_report', ''))}")
        
        # Analyze report content
        report = result.get('fundamentals_report', '')
        
        if not report:
            print("❌ No report generated")
            return False
            
        # Check for comprehensive sections
        sections_to_check = [
            "COMPANY PROFILE",
            "KEY VALUATION METRICS", 
            "FINANCIAL PERFORMANCE",
            "BALANCE SHEET STRENGTH", 
            "ANALYST CONSENSUS",
            "PRICE TARGETS",
            "EARNINGS INTELLIGENCE",
            "CASH FLOW ANALYSIS",
            "DATA QUALITY ASSESSMENT"
        ]
        
        found_sections = []
        missing_sections = []
        
        for section in sections_to_check:
            if section in report:
                found_sections.append(section)
            else:
                missing_sections.append(section)
                
        print(f"\n✅ Found sections ({len(found_sections)}):")
        for section in found_sections:
            print(f"  - {section}")
            
        if missing_sections:
            print(f"\n❌ Missing sections ({len(missing_sections)}):")
            for section in missing_sections:
                print(f"  - {section}")
        
        # Check for specific enhanced metrics
        enhanced_metrics = [
            "Dividend Yield",
            "Revenue Growth", 
            "Data Quality Assessment",
            "Operating Cash Flow",
            "Free Cash Flow"
        ]
        
        enhanced_found = []
        for metric in enhanced_metrics:
            if metric in report:
                enhanced_found.append(metric)
                
        print(f"\n🔥 Enhanced metrics found ({len(enhanced_found)}):")
        for metric in enhanced_found:
            print(f"  - {metric}")
            
        # Show report preview
        print(f"\n📊 REPORT PREVIEW (first 1000 chars):")
        print("-" * 60)
        print(report[:1000])
        if len(report) > 1000:
            print(f"\n... ({len(report) - 1000} more characters)")
        
        # Success criteria
        success = (
            len(found_sections) >= 6 and  # At least 6 major sections
            len(enhanced_found) >= 2 and  # At least 2 enhanced metrics
            len(report) > 2000  # Substantial report length
        )
        
        print(f"\n🎯 VALIDATION RESULT:")
        print(f"  Sections: {len(found_sections)}/9 ({'✅' if len(found_sections) >= 6 else '❌'})")
        print(f"  Enhanced: {len(enhanced_found)}/5 ({'✅' if len(enhanced_found) >= 2 else '❌'})")
        print(f"  Length: {len(report)} chars ({'✅' if len(report) > 2000 else '❌'})")
        print(f"  Overall: {'✅ SUCCESS' if success else '❌ NEEDS MORE WORK'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_fundamentals_fix())
    sys.exit(0 if result else 1)