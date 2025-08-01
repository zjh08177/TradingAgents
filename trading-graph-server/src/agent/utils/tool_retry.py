import asyncio
import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class ToolRetryManager:
    """Manages tool execution with retry and fallback logic"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.execution_history = []
    
    async def execute_with_retry(
        self, 
        tool: Callable, 
        params: Dict[str, Any],
        tool_name: str,
        fallback_tool: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute tool with retry logic and optional fallback"""
        
        for attempt in range(self.max_retries):
            try:
                start_time = datetime.now()
                logger.info(f"🔧 Executing {tool_name} (attempt {attempt + 1}/{self.max_retries})")
                
                # Handle both LangChain tools and regular async functions
                if hasattr(tool, 'ainvoke'):
                    result = await tool.ainvoke(params)
                elif asyncio.iscoroutinefunction(tool):
                    result = await tool(params)
                else:
                    result = tool(params)
                
                # Validate result
                if self._is_valid_result(result):
                    execution_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"✅ {tool_name} succeeded in {execution_time:.2f}s")
                    
                    self.execution_history.append({
                        "tool": tool_name,
                        "success": True,
                        "attempts": attempt + 1,
                        "execution_time": execution_time
                    })
                    
                    return result
                else:
                    raise ValueError(f"Invalid result from {tool_name}")
                    
            except Exception as e:
                logger.warning(f"⚠️ {tool_name} failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(f"⏳ Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    logger.error(f"❌ {tool_name} failed after {self.max_retries} attempts")
                    
                    if fallback_tool:
                        logger.info(f"🔄 Attempting fallback tool for {tool_name}")
                        try:
                            # Handle both LangChain tools and regular async functions
                            if hasattr(fallback_tool, 'ainvoke'):
                                fallback_result = await fallback_tool.ainvoke(params)
                            elif asyncio.iscoroutinefunction(fallback_tool):
                                fallback_result = await fallback_tool(params)
                            else:
                                fallback_result = fallback_tool(params)
                            if self._is_valid_result(fallback_result):
                                logger.info(f"✅ Fallback succeeded for {tool_name}")
                                return fallback_result
                        except Exception as fallback_e:
                            logger.error(f"❌ Fallback also failed: {str(fallback_e)}")
                    
                    # Return error result
                    self.execution_history.append({
                        "tool": tool_name,
                        "success": False,
                        "attempts": self.max_retries,
                        "error": str(e)
                    })
                    
                    return {
                        "error": f"Tool {tool_name} failed after all attempts",
                        "fallback": True,
                        "original_error": str(e)
                    }
    
    def _is_valid_result(self, result: Any) -> bool:
        """Validate tool result"""
        if result is None:
            return False
        if isinstance(result, dict) and "error" in result:
            return False
        if isinstance(result, str) and len(result) < 10:
            return False
        return True
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        if not self.execution_history:
            return 0.0
        
        successful = sum(1 for exec in self.execution_history if exec["success"])
        return successful / len(self.execution_history) * 100

# Global retry manager instance
retry_manager = ToolRetryManager()

async def execute_tool_with_fallback(
    primary_tool: Callable,
    fallback_tool: Optional[Callable],
    params: Dict[str, Any],
    tool_name: str
) -> Dict[str, Any]:
    """Convenience function for tool execution with retry and fallback"""
    return await retry_manager.execute_with_retry(
        tool=primary_tool,
        params=params,
        tool_name=tool_name,
        fallback_tool=fallback_tool
    )