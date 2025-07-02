#!/usr/bin/env python3
"""
Check if the environment is properly set up for TradingAgents
"""
import os
import sys

print("🔍 TradingAgents Environment Check")
print("=" * 50)

# Check Python version
print(f"✓ Python version: {sys.version.split()[0]}")

# Check required packages
required_packages = [
    'fastapi',
    'uvicorn',
    'pydantic',
    'openai',
    'langchain',
    'langchain_openai',
    'langgraph'
]

print("\nChecking required packages:")
missing_packages = []
for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        print(f"✓ {package} is installed")
    except ImportError:
        print(f"✗ {package} is NOT installed")
        missing_packages.append(package)

# Check environment variables
print("\nChecking environment variables:")
env_vars = {
    'OPENAI_API_KEY': 'Required for AI agents',
    'FINNHUB_API_KEY': 'Required for market data',
    'REDDIT_CLIENT_ID': 'Optional for sentiment analysis',
    'REDDIT_CLIENT_SECRET': 'Optional for sentiment analysis'
}

missing_required = []
for var, description in env_vars.items():
    value = os.getenv(var)
    if value:
        print(f"✓ {var} is set ({description})")
    else:
        if 'Required' in description:
            print(f"✗ {var} is NOT set ({description})")
            missing_required.append(var)
        else:
            print(f"⚠ {var} is not set ({description})")

# Summary
print("\n" + "=" * 50)
if missing_packages:
    print("❌ Missing packages:")
    for pkg in missing_packages:
        print(f"   - {pkg}")
    print("\nInstall with: pip install -r requirements.txt")
    
if missing_required:
    print("❌ Missing required environment variables:")
    for var in missing_required:
        print(f"   - {var}")
    print("\nAdd these to your .env file")

if not missing_packages and not missing_required:
    print("✅ Environment is properly configured!")
    print("\nYou can now run:")
    print("   uv run python3 run_api.py")
else:
    print("\n⚠️  Fix the issues above before running the API") 