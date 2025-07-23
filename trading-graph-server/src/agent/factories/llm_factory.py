# TradingAgents/factories/llm_factory.py

import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from ..interfaces import ILLMProvider

class LLMFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create_llm(provider: str, model: str, config: Dict[str, Any]) -> ILLMProvider:
        """Create LLM instance based on provider type"""
        
        if provider.lower() in ["openai", "ollama", "openrouter"]:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            return ChatOpenAI(
                model=model, 
                base_url=config.get("backend_url"), 
                api_key=api_key
            )
        
        elif provider.lower() == "anthropic":
            return ChatAnthropic(
                model=model, 
                base_url=config.get("backend_url")
            )
        
        elif provider.lower() == "google":
            return ChatGoogleGenerativeAI(model=model)
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def create_quick_thinking_llm(config: Dict[str, Any]) -> ILLMProvider:
        """Create quick thinking LLM"""
        return LLMFactory.create_llm(
            config["llm_provider"], 
            config["quick_thinking_model"], 
            config
        )
    
    @staticmethod
    def create_deep_thinking_llm(config: Dict[str, Any]) -> ILLMProvider:
        """Create deep thinking LLM"""
        return LLMFactory.create_llm(
            config["llm_provider"], 
            config["reasoning_model"], 
            config
        ) 