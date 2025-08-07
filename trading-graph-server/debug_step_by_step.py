#!/usr/bin/env python3
"""
Step by step debugging to understand why pydantic isn't reading env vars
"""
import os
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

print("=" * 60)
print("🔍 STEP BY STEP DEBUGGING")
print("=" * 60)

print("Step 1: Check environment BEFORE load_dotenv")
print(f"  DEEP_THINK_MODEL: {repr(os.getenv('DEEP_THINK_MODEL'))}")

print("\nStep 2: Load .env file")
result = load_dotenv()
print(f"  load_dotenv() returned: {result}")

print("\nStep 3: Check environment AFTER load_dotenv")  
print(f"  DEEP_THINK_MODEL: {repr(os.getenv('DEEP_THINK_MODEL'))}")

print("\nStep 4: Create simple BaseSettings class")
class DebugConfig(BaseSettings):
    # Simple field with debug
    deep_think_llm: str = Field(default="DEFAULT_VALUE", env="DEEP_THINK_MODEL")
    
    def __init__(self, **kwargs):
        print(f"  DebugConfig.__init__ called with kwargs: {kwargs}")
        super().__init__(**kwargs)
        print(f"  After init, deep_think_llm = {repr(self.deep_think_llm)}")

print("\nStep 5: Create instance of DebugConfig")
debug_config = DebugConfig()

print(f"\nStep 6: Final value")
print(f"  debug_config.deep_think_llm = {repr(debug_config.deep_think_llm)}")

print("\nStep 7: Try manual override")
os.environ['DEEP_THINK_MODEL'] = 'MANUAL_OVERRIDE'
print(f"  Set DEEP_THINK_MODEL = 'MANUAL_OVERRIDE'")

class DebugConfig2(BaseSettings):
    deep_think_llm: str = Field(default="DEFAULT_VALUE", env="DEEP_THINK_MODEL")

debug_config2 = DebugConfig2()
print(f"  debug_config2.deep_think_llm = {repr(debug_config2.deep_think_llm)}")

print("=" * 60)