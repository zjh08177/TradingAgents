# TradingAgents/factories/memory_factory.py

from typing import Dict, Any
from ..utils.memory import FinancialSituationMemory
from ..interfaces import IMemoryProvider

class MemoryFactory:
    """Factory for creating memory providers"""
    
    @staticmethod
    def create_memory(memory_type: str, config: Dict[str, Any]) -> IMemoryProvider:
        """Create memory instance"""
        return FinancialSituationMemory(memory_type, config)
    
    @staticmethod  
    def create_bull_memory(config: Dict[str, Any]) -> IMemoryProvider:
        """Create bull researcher memory"""
        return MemoryFactory.create_memory("bull_researcher", config)
        
    @staticmethod
    def create_bear_memory(config: Dict[str, Any]) -> IMemoryProvider:
        """Create bear researcher memory"""
        return MemoryFactory.create_memory("bear_researcher", config)
        
    @staticmethod
    def create_research_memory(config: Dict[str, Any]) -> IMemoryProvider:
        """Create research manager memory"""
        return MemoryFactory.create_memory("research_manager", config)
        
    @staticmethod
    def create_risk_memory(config: Dict[str, Any]) -> IMemoryProvider:
        """Create risk manager memory"""
        return MemoryFactory.create_memory("risk_manager", config)
        
    @staticmethod
    def create_trader_memory(config: Dict[str, Any]) -> IMemoryProvider:
        """Create trader memory"""
        return MemoryFactory.create_memory("trader", config) 