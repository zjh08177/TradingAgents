#!/usr/bin/env python3
"""
Debug script to check if .env variables are being read correctly
"""
import os
from dotenv import load_dotenv

print("=" * 60)
print("🔍 DEBUGGING ENVIRONMENT VARIABLE READING")
print("=" * 60)

# Load .env file explicitly
load_dotenv()

print("\n1️⃣ CHECKING DIRECT OS.GETENV:")
print(f"   DEEP_THINK_MODEL = '{os.getenv('DEEP_THINK_MODEL')}'")
print(f"   QUICK_THINK_MODEL = '{os.getenv('QUICK_THINK_MODEL')}'")
print(f"   BACKEND_URL = '{os.getenv('BACKEND_URL')}'")
print(f"   SERPER_API_KEY = '{os.getenv('SERPER_API_KEY')[:20]}...' (truncated)")

print("\n2️⃣ CHECKING PYDANTIC CONFIG:")
import sys
sys.path.insert(0, '.')
from src.agent.config import get_trading_config

config = get_trading_config()
print(f"   deep_think_model = '{config.deep_think_model}'")
print(f"   quick_think_model = '{config.quick_think_model}'")
print(f"   backend_url = '{config.backend_url}'")
print(f"   serper_api_key present = {bool(config.serper_api_key)}")

print("\n3️⃣ EXPECTED vs ACTUAL:")
expected_deep = os.getenv('DEEP_THINK_MODEL')
actual_deep = config.deep_think_model
print(f"   Expected DEEP_THINK_MODEL: '{expected_deep}'")
print(f"   Actual deep_think_model: '{actual_deep}'")
print(f"   Match: {'✅' if expected_deep == actual_deep else '❌'}")

if expected_deep != actual_deep:
    print(f"\n🔧 DIAGNOSIS: The env var is being read as '{expected_deep}' but config shows '{actual_deep}'")
    print("   This suggests the default value is overriding the .env value")
else:
    print(f"\n✅ SUCCESS: Environment variable is now being read correctly!")
    print("   The unified config system is working as expected.")
    
print("=" * 60)