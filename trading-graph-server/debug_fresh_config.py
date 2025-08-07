#!/usr/bin/env python3
"""
Test fresh config instance to debug environment variable reading
"""
import os
from dotenv import load_dotenv

# Load .env explicitly
load_dotenv()

print("=" * 60)
print("🔍 TESTING FRESH CONFIG INSTANCE")
print("=" * 60)

print(f"Environment DEEP_THINK_MODEL: '{os.getenv('DEEP_THINK_MODEL')}'")

# Test pydantic-settings directly
from pydantic import Field
from pydantic_settings import BaseSettings

class TestConfig(BaseSettings):
    deep_think_llm: str = Field(default="o1", env="DEEP_THINK_MODEL")
    quick_think_llm: str = Field(default="gpt-4o", env="QUICK_THINK_MODEL") 
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8", 
        "case_sensitive": False,
        "extra": "ignore",
    }

test_config = TestConfig()
print(f"TestConfig deep_think_llm: '{test_config.deep_think_llm}'")
print(f"TestConfig quick_think_llm: '{test_config.quick_think_llm}'")

# Test without env file, relying on already loaded environment
class TestConfig2(BaseSettings):
    deep_think_llm: str = Field(default="o1", env="DEEP_THINK_MODEL")
    
    model_config = {
        "case_sensitive": False,
        "extra": "ignore",
    }

test_config2 = TestConfig2()
print(f"TestConfig2 (no env_file) deep_think_llm: '{test_config2.deep_think_llm}'")

print("=" * 60)