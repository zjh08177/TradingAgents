#!/usr/bin/env python3
"""
Migration Script: Update Twitter Implementation to Enhanced Social Sentiment
Automatically updates the codebase to use aggregated social sentiment APIs
"""

import os
import sys
from pathlib import Path


def check_api_keys():
    """Check if required API keys are configured"""
    print("🔍 Checking API key configuration...")
    
    has_finnhub = os.getenv('FINNHUB_API_KEY') is not None
    has_fmp = os.getenv('FMP_API_KEY') is not None  
    has_alpha = os.getenv('ALPHA_VANTAGE_API_KEY') is not None
    
    if has_finnhub:
        print("✅ Finnhub API key configured (PRIMARY SOURCE)")
    else:
        print("❌ FINNHUB_API_KEY not found - This is REQUIRED")
        print("   Get free key at: https://finnhub.io/register")
    
    if has_fmp:
        print("✅ Financial Modeling Prep API key configured (optional)")
    else:
        print("⚠️  FMP_API_KEY not found (optional)")
        print("   Get free key at: https://site.financialmodelingprep.com/developer/docs")
    
    if has_alpha:
        print("✅ Alpha Vantage API key configured (optional)")
    else:
        print("⚠️  ALPHA_VANTAGE_API_KEY not found (optional)")  
        print("   Get free key at: https://www.alphavantage.co/support/#api-key")
    
    return has_finnhub


def update_interface_file():
    """Update interface_new_tools.py to use enhanced Twitter implementation"""
    interface_path = Path("src/agent/dataflows/interface_new_tools.py")
    
    if not interface_path.exists():
        print(f"❌ File not found: {interface_path}")
        return False
    
    print(f"\n📝 Updating {interface_path}...")
    
    # Read current content
    with open(interface_path, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'twitter_enhanced' in content:
        print("✅ Already using enhanced Twitter implementation")
        return True
    
    # Update the Twitter import
    old_import = "from .twitter_simple import get_twitter_fast"
    new_import = "from .twitter_enhanced import get_twitter_enhanced as get_twitter_fast"
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        print("✅ Updated import to use twitter_enhanced")
    else:
        # Try alternative import pattern
        old_import2 = "from .twitter_simple_fast import get_twitter_fast"
        if old_import2 in content:
            content = content.replace(old_import2, new_import)
            print("✅ Updated import to use twitter_enhanced")
        else:
            print("⚠️  Could not find Twitter import to update")
            print("   Please manually update the import in interface_new_tools.py")
            return False
    
    # Write updated content
    with open(interface_path, 'w') as f:
        f.write(content)
    
    print("✅ File updated successfully")
    return True


def create_env_template():
    """Create .env.template file with required API keys"""
    template_path = Path(".env.template")
    
    print(f"\n📄 Creating {template_path}...")
    
    template_content = """# Social Sentiment API Keys (FREE tiers available)

# REQUIRED - Finnhub (60 calls/minute free)
# Get key at: https://finnhub.io/register
FINNHUB_API_KEY=your_finnhub_key_here

# OPTIONAL - Financial Modeling Prep (250 calls/day free)
# Get key at: https://site.financialmodelingprep.com/developer/docs
FMP_API_KEY=your_fmp_key_here

# OPTIONAL - Alpha Vantage (25 calls/day free)  
# Get key at: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Existing API keys (if any)
OPENAI_API_KEY=your_openai_key_here
SERPER_API_KEY=your_serper_key_here
"""
    
    with open(template_path, 'w') as f:
        f.write(template_content)
    
    print(f"✅ Created {template_path}")
    print("   Copy this to .env and add your API keys")


def test_implementation():
    """Test the enhanced implementation"""
    print("\n🧪 Testing enhanced social sentiment...")
    
    try:
        # Add src to path
        sys.path.insert(0, 'src')
        
        # Import and test
        from agent.dataflows.aggregated_social_sentiment import get_aggregated_sync
        
        # Test with a popular ticker
        result = get_aggregated_sync("AAPL")
        
        if result:
            print(f"✅ Test successful!")
            print(f"   Sentiment: {result.get('sentiment_score', 0):.3f}")
            print(f"   Sources used: {', '.join(result.get('sources_used', []))}")
            print(f"   Confidence: {result.get('confidence', 'unknown')}")
            
            if result.get('fallback_mode'):
                print("⚠️  Using fallback mode - configure API keys for real data")
            else:
                print("✅ Using real data from APIs")
                
            return True
        else:
            print("❌ Test failed - no data returned")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required files are in place")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def main():
    """Run the migration process"""
    print("=" * 60)
    print("🚀 Social Sentiment API Migration Tool")
    print("=" * 60)
    
    # Step 1: Check API keys
    has_keys = check_api_keys()
    
    if not has_keys:
        print("\n⚠️  WARNING: No Finnhub API key found!")
        print("The enhanced implementation will work but will use fallback data.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Migration cancelled. Please set up API keys first.")
            return
    
    # Step 2: Update interface file
    success = update_interface_file()
    
    if not success:
        print("\n❌ Migration failed. Please check the errors above.")
        return
    
    # Step 3: Create env template
    create_env_template()
    
    # Step 4: Test implementation
    print("\n" + "=" * 60)
    test_success = test_implementation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Migration Summary")
    print("=" * 60)
    
    if success and test_success:
        print("✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        if not has_keys:
            print("1. Get your free Finnhub API key at: https://finnhub.io/register")
            print("2. Add it to your .env file: FINNHUB_API_KEY=your_key")
            print("3. Restart your application")
        else:
            print("1. Your social sentiment is now using real API data!")
            print("2. Monitor API usage to stay within free tier limits")
            print("3. Consider adding optional APIs for better coverage")
    else:
        print("⚠️  Migration partially completed")
        print("Please review the errors above and complete manual steps if needed")
    
    print("\n📚 Documentation: claude_doc/SOCIAL_SENTIMENT_API_SETUP.md")


if __name__ == "__main__":
    main()