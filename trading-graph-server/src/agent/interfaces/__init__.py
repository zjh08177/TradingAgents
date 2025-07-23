"""
Core interfaces for dependency inversion and abstraction
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ILLMProvider(ABC):
    """Interface for LLM providers"""
    
    @abstractmethod
    async def ainvoke(self, messages: List[Dict[str, str]]) -> Any:
        """Invoke LLM asynchronously"""
        pass

class IAnalystToolkit(ABC):
    """Interface for analyst toolkits"""
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        pass

class IAnalystNode(ABC):
    """Interface for analyst nodes"""
    
    @abstractmethod
    async def execute(self, state: Any) -> Any:
        """Execute analyst node"""
        pass

class IMemoryProvider(ABC):
    """Interface for memory providers"""
    
    @abstractmethod
    def add_message(self, message: str):
        """Add message to memory"""
        pass
        
    @abstractmethod
    def get_messages(self) -> List[str]:
        """Get messages from memory"""
        pass

class IGraphBuilder(ABC):
    """Interface for graph builders"""
    
    @abstractmethod
    def setup_graph(self, selected_analysts: List[str]) -> Any:
        """Setup and return graph"""
        pass

__all__ = [
    "ILLMProvider",
    "IAnalystToolkit", 
    "IAnalystNode",
    "IMemoryProvider",
    "IGraphBuilder"
] 