#!/usr/bin/env python3
"""
Adaptive Graph Builder - Automatically chooses best implementation
Switches between original and enhanced implementations based on environment
"""

import logging
from typing import Dict, Any, List
from langgraph.graph.state import CompiledStateGraph

from ..interfaces import ILLMProvider, IGraphBuilder

logger = logging.getLogger(__name__)

class AdaptiveGraphBuilder(IGraphBuilder):
    """
    Adaptive graph builder that automatically chooses the best implementation
    Falls back gracefully if enhanced features are not available
    """
    
    def __init__(self, 
                 quick_thinking_llm: ILLMProvider,
                 deep_thinking_llm: ILLMProvider,
                 config: Dict[str, Any]):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.config = config
        
        # Determine which implementation to use
        self.implementation_type = self._choose_implementation()
        self.builder = self._create_builder()
        
        logger.info(f"🚀 AdaptiveGraphBuilder using: {self.implementation_type}")
    
    def _choose_implementation(self) -> str:
        """Choose the best available implementation"""
        
        # Check if user explicitly disabled enhanced features
        if self.config.get('force_original_implementation', False):
            return "original"
        
        # Check if enhanced implementation is available and compatible
        try:
            from .send_api_dispatcher import LangGraphVersionManager
            
            if LangGraphVersionManager.check_send_api_compatibility():
                # Enhanced implementation available
                return "enhanced"
            else:
                logger.warning("⚠️ Send API not available - using original implementation")
                return "original"
                
        except ImportError:
            logger.warning("⚠️ Enhanced implementation not available - using original")
            return "original"
    
    def _create_builder(self):
        """Create the appropriate builder instance"""
        
        if self.implementation_type == "enhanced":
            from .enhanced_optimized_setup import EnhancedOptimizedGraphBuilder
            return EnhancedOptimizedGraphBuilder(
                self.quick_thinking_llm,
                self.deep_thinking_llm,
                self.config
            )
        else:
            from .optimized_setup import OptimizedGraphBuilder
            return OptimizedGraphBuilder(
                self.quick_thinking_llm,
                self.deep_thinking_llm,
                self.config
            )
    
    def setup_graph(self, selected_analysts: List[str] = None) -> CompiledStateGraph:
        """Build graph using the selected implementation"""
        return self.builder.setup_graph(selected_analysts)
    
    def get_implementation_info(self) -> Dict[str, Any]:
        """Get information about the current implementation"""
        info = {
            "type": self.implementation_type,
            "send_api_enabled": self.implementation_type == "enhanced",
            "individual_node_visibility": self.implementation_type == "enhanced",
            "parallel_execution": True,  # Both implementations support parallel execution
        }
        
        if hasattr(self.builder, 'implementation_strategy'):
            info["strategy"] = self.builder.implementation_strategy
        
        return info

def create_adaptive_graph_builder(quick_thinking_llm: ILLMProvider, 
                                 deep_thinking_llm: ILLMProvider, 
                                 config: Dict[str, Any]) -> AdaptiveGraphBuilder:
    """Create adaptive graph builder that chooses the best implementation"""
    return AdaptiveGraphBuilder(quick_thinking_llm, deep_thinking_llm, config)
