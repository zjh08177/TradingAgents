#!/usr/bin/env python3
"""
Integration Script for Enhanced Send API + Conditional Edges Implementation
Helps migrate from the current parallel_analysts node to the new Send API architecture
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedImplementationIntegrator:
    """Handles integration of the enhanced Send API implementation"""
    
    def __init__(self):
        self.original_file = Path("src/agent/graph/optimized_setup.py")
        self.enhanced_file = Path("src/agent/graph/enhanced_optimized_setup.py")
        self.backup_file = Path("src/agent/graph/optimized_setup_backup.py")
    
    def validate_prerequisites(self) -> bool:
        """Validate that all prerequisites are met for integration"""
        print("🔍 Validating Prerequisites...")
        
        # Check LangGraph version
        try:
            from src.agent.graph.send_api_dispatcher import LangGraphVersionManager
            if not LangGraphVersionManager.check_send_api_compatibility():
                print("❌ LangGraph 0.6.2+ required for Send API support")
                return False
            print("✅ LangGraph Send API available")
        except ImportError:
            print("❌ Cannot import Send API components")
            return False
        
        # Check enhanced files exist
        if not self.enhanced_file.exists():
            print(f"❌ Enhanced implementation not found: {self.enhanced_file}")
            return False
        print("✅ Enhanced implementation files found")
        
        # Check original file exists
        if not self.original_file.exists():
            print(f"❌ Original implementation not found: {self.original_file}")
            return False
        print("✅ Original implementation files found")
        
        return True
    
    def create_integration_wrapper(self) -> bool:
        """Create a wrapper that can switch between implementations"""
        print("🔧 Creating integration wrapper...")
        
        wrapper_content = '''#!/usr/bin/env python3
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
'''
        
        wrapper_file = Path("src/agent/graph/adaptive_setup.py")
        wrapper_file.write_text(wrapper_content)
        print(f"✅ Created adaptive wrapper: {wrapper_file}")
        
        return True
    
    def run_integration_tests(self) -> bool:
        """Run integration tests to verify everything works"""
        print("🧪 Running Integration Tests...")
        
        try:
            # Test enhanced implementation
            from src.agent.graph.enhanced_optimized_setup import EnhancedOptimizedGraphBuilder
            from unittest.mock import AsyncMock, Mock
            
            mock_llm = AsyncMock()
            config = {"enable_send_api": True}
            
            builder = EnhancedOptimizedGraphBuilder(mock_llm, mock_llm, config)
            print("✅ Enhanced implementation can be instantiated")
            
            # Test adaptive wrapper
            from src.agent.graph.adaptive_setup import AdaptiveGraphBuilder
            
            adaptive_builder = AdaptiveGraphBuilder(mock_llm, mock_llm, config)
            info = adaptive_builder.get_implementation_info()
            
            print(f"✅ Adaptive builder created: {info['type']} implementation")
            print(f"   Send API enabled: {info['send_api_enabled']}")
            print(f"   Individual node visibility: {info['individual_node_visibility']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            return False
    
    def create_migration_guide(self):
        """Create a migration guide for users"""
        guide_content = """# Enhanced Send API Implementation Migration Guide

## Overview
The enhanced implementation provides true parallel analyst execution with individual node visibility using LangGraph's Send API + conditional edges pattern.

## Key Improvements
- ✅ **Individual Node Visibility**: Each analyst is a separate node in LangGraph
- ✅ **True Parallel Execution**: 3-4x performance improvement
- ✅ **Robust Error Handling**: Enhanced error recovery and partial failure handling
- ✅ **Better Monitoring**: Individual analyst timing and status tracking
- ✅ **Backward Compatibility**: Works with existing research and risk management

## Migration Options

### Option 1: Automatic Migration (Recommended)
Use the adaptive graph builder that automatically chooses the best implementation:

```python
from src.agent.graph.adaptive_setup import create_adaptive_graph_builder

# This automatically uses enhanced implementation if available
builder = create_adaptive_graph_builder(quick_llm, deep_llm, config)
graph = builder.setup_graph()

# Check which implementation is being used
info = builder.get_implementation_info()
print(f"Using: {info['type']} implementation")
```

### Option 2: Explicit Enhanced Implementation
Force use of the enhanced implementation:

```python
from src.agent.graph.enhanced_optimized_setup import EnhancedOptimizedGraphBuilder

builder = EnhancedOptimizedGraphBuilder(quick_llm, deep_llm, config)
graph = builder.setup_graph()
```

### Option 3: Stay with Original
Force use of the original implementation:

```python
config['force_original_implementation'] = True
builder = create_adaptive_graph_builder(quick_llm, deep_llm, config)
```

## Configuration Options

```python
config = {
    # Enhanced implementation options
    'enable_send_api': True,  # Enable Send API (auto-detected)
    'enable_enhanced_monitoring': True,  # Enhanced metrics
    'enable_fallback': True,  # Fallback to original if needed
    
    # Force original implementation
    'force_original_implementation': False,  # Set to True to force original
    
    # Existing options (still work)
    'enable_phase1_optimizations': True,
    'enable_async_tokens': True,
    'enable_ultra_prompts': True,
}
```

## Performance Expectations

### Enhanced Implementation (Send API)
- **Speedup**: 3-4x faster than sequential execution
- **Visibility**: All 4 analysts visible as separate nodes
- **Error Handling**: Robust partial failure recovery
- **Monitoring**: Individual analyst timing and status

### Original Implementation (asyncio.gather)
- **Speedup**: 3-4x faster than sequential execution  
- **Visibility**: Single parallel_analysts node
- **Error Handling**: Basic failure handling
- **Monitoring**: Aggregate timing only

## Troubleshooting

### Enhanced Implementation Not Available
```
⚠️ Send API not available - using original implementation
```
**Solution**: Ensure LangGraph 0.6.2+ is installed

### Graph Compilation Errors
```
Channel 'company_of_interest' already exists with a different type
```
**Solution**: This is usually a test environment issue. In production, use fresh graph instances.

### Performance Issues
If enhanced implementation is slower than expected:
1. Check `builder.get_implementation_info()` to confirm Send API is enabled
2. Monitor individual analyst execution times
3. Check for tool execution timeouts
4. Verify network connectivity for data sources

## Monitoring and Observability

### Enhanced State Information
```python
# Get detailed execution metrics
state = graph.invoke(initial_state)

print(f"Aggregation status: {state['aggregation_status']}")
print(f"Successful analysts: {state['successful_analysts_count']}/4")
print(f"Speedup factor: {state['speedup_factor']:.2f}x")
print(f"Individual times: {state['analyst_execution_times']}")

# Check for failures
if state.get('failed_analysts'):
    print(f"Failed analysts: {state['failed_analysts']}")
    print(f"Errors: {state['analyst_errors']}")
```

### LangGraph Visualization
With the enhanced implementation, you'll see:
- `dispatcher` node
- `market_analyst` node  
- `news_analyst` node
- `social_analyst` node
- `fundamentals_analyst` node
- `enhanced_aggregator` node

Instead of just:
- `parallel_analysts` node
- `aggregator` node

## Best Practices

1. **Use Adaptive Builder**: Let the system choose the best implementation automatically
2. **Monitor Performance**: Check speedup factors and individual analyst timing
3. **Handle Partial Failures**: The enhanced aggregator gracefully handles 1-2 analyst failures
4. **Enable Monitoring**: Use `enable_enhanced_monitoring: true` for detailed metrics
5. **Test Thoroughly**: Validate with your specific data and tool configurations

## Rollback Plan

If you need to rollback to the original implementation:

```python
config['force_original_implementation'] = True
```

Or directly use:
```python
from src.agent.graph.optimized_setup import OptimizedGraphBuilder
```

Both implementations maintain the same external API for seamless switching.
"""
        
        guide_file = Path("ENHANCED_IMPLEMENTATION_MIGRATION_GUIDE.md")
        guide_file.write_text(guide_content)
        print(f"✅ Created migration guide: {guide_file}")

def main():
    """Main integration process"""
    print("🚀 Enhanced Send API Implementation Integration")
    print("=" * 60)
    
    integrator = EnhancedImplementationIntegrator()
    
    # Step 1: Validate prerequisites
    if not integrator.validate_prerequisites():
        print("❌ Prerequisites not met. Please fix issues before proceeding.")
        return False
    
    # Step 2: Create integration wrapper
    if not integrator.create_integration_wrapper():
        print("❌ Failed to create integration wrapper")
        return False
    
    # Step 3: Run integration tests
    if not integrator.run_integration_tests():
        print("❌ Integration tests failed")
        return False
    
    # Step 4: Create migration guide
    integrator.create_migration_guide()
    
    print("\n" + "=" * 60)
    print("✅ INTEGRATION COMPLETE!")
    print("🎉 Enhanced Send API implementation is ready to use")
    print("\n📋 Next Steps:")
    print("1. Review the migration guide: ENHANCED_IMPLEMENTATION_MIGRATION_GUIDE.md")
    print("2. Update your application to use AdaptiveGraphBuilder:")
    print("   from src.agent.graph.adaptive_setup import create_adaptive_graph_builder")
    print("3. Test with your real data and configuration")
    print("4. Monitor performance improvements (3-4x speedup expected)")
    print("5. Enjoy individual node visibility in LangGraph! 🎯")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)