"""
Optimization Logger - Track Phase 1 optimizations execution
"""
import logging
import time
from typing import Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

class OptimizationTracker:
    """Track optimization execution and performance"""
    
    def __init__(self):
        self.start_times: Dict[str, float] = {}
        self.optimizations_used: Dict[str, bool] = {}
        self.time_saved: Dict[str, float] = {}
        
    def log_optimization_start(self, optimization: str, details: str = ""):
        """Log when an optimization starts"""
        self.start_times[optimization] = time.time()
        self.optimizations_used[optimization] = True
        logger.info(f"🚀 OPTIMIZATION ACTIVE: {optimization} - {details}")
        
    def log_optimization_end(self, optimization: str, time_saved: float = 0):
        """Log when an optimization completes"""
        if optimization in self.start_times:
            duration = time.time() - self.start_times[optimization]
            self.time_saved[optimization] = time_saved
            logger.info(f"✅ OPTIMIZATION COMPLETE: {optimization} - Duration: {duration:.2f}s, Saved: {time_saved:.2f}s")
        
    def log_skip(self, optimization: str, reason: str):
        """Log when an optimization is skipped"""
        logger.warning(f"⚠️ OPTIMIZATION SKIPPED: {optimization} - Reason: {reason}")
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of optimizations used"""
        total_saved = sum(self.time_saved.values())
        return {
            "optimizations_active": list(self.optimizations_used.keys()),
            "total_time_saved": total_saved,
            "details": self.time_saved
        }

# Global tracker instance
optimization_tracker = OptimizationTracker()

def track_optimization(name: str):
    """Decorator to track optimization execution"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimization_tracker.log_optimization_start(name, f"Function: {func.__name__}")
            result = await func(*args, **kwargs)
            # Time saved would be calculated based on the specific optimization
            return result
        return wrapper
    return decorator

def log_config_status(config: Dict[str, Any]):
    """Log the status of all optimization flags"""
    logger.info("🔍 OPTIMIZATION CONFIGURATION STATUS:")
    logger.info(f"   Parallel Risk Debate: ✅ ALWAYS ENABLED (sequential mode removed)")
    logger.info(f"   Smart Retry Logic: {'✅ ENABLED' if config.get('enable_smart_retry') else '❌ DISABLED'}")
    logger.info(f"   Parallel Tools: {'✅ ENABLED' if config.get('enable_parallel_tools') else '❌ DISABLED'}")
    logger.info(f"   Smart Caching: {'✅ ENABLED' if config.get('enable_smart_caching') else '❌ DISABLED'}")
    logger.info(f"   Debate Optimization: {'✅ ENABLED' if config.get('enable_debate_optimization') else '❌ DISABLED'}")