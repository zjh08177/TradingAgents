"""Configuration utility for parallel tool execution optimization (PT1)."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def verify_parallel_config(config: Dict[str, Any]) -> Dict[str, bool]:
    """
    Verify that parallel execution features are properly configured.
    
    Returns a dict with status of each parallel feature.
    """
    status = {
        "enable_parallel_tools": config.get("enable_parallel_tools", True),
        "parallel_risk_debate": True,  # Always enabled - sequential mode removed
        "enable_smart_caching": config.get("enable_smart_caching", True),
        "enable_smart_retry": config.get("enable_smart_retry", True),
        "enable_debate_optimization": config.get("enable_debate_optimization", True),
    }
    
    logger.info("⚡ PARALLEL CONFIG STATUS:")
    for feature, enabled in status.items():
        emoji = "✅" if enabled else "❌"
        logger.info(f"  {emoji} {feature}: {enabled}")
    
    # Check if all performance features are enabled
    all_enabled = all(status.values())
    if all_enabled:
        logger.info("🚀 All parallel optimization features are ENABLED!")
    else:
        disabled = [k for k, v in status.items() if not v]
        logger.warning(f"⚠️  Some parallel features are disabled: {disabled}")
    
    return status


def log_parallel_performance_summary(
    analyst_type: str,
    tool_count: int,
    parallel_time: float,
    sequential_estimate: float
) -> None:
    """
    Log a summary of parallel execution performance gains.
    
    Args:
        analyst_type: Type of analyst (market, news, social, fundamentals)
        tool_count: Number of tools executed in parallel
        parallel_time: Actual parallel execution time
        sequential_estimate: Estimated sequential execution time
    """
    if sequential_estimate > 0:
        speedup = sequential_estimate / parallel_time
        time_saved = sequential_estimate - parallel_time
        
        logger.info(f"⚡ {analyst_type.upper()} PARALLEL PERFORMANCE:")
        logger.info(f"  🔧 Tools executed: {tool_count}")
        logger.info(f"  ⏱️  Sequential estimate: {sequential_estimate:.2f}s")
        logger.info(f"  ⚡ Parallel actual: {parallel_time:.2f}s")
        logger.info(f"  🚀 Speedup: {speedup:.2f}x")
        logger.info(f"  💰 Time saved: {time_saved:.2f}s")
        
        # Performance rating
        if speedup >= 3.0:
            logger.info("  🏆 EXCELLENT parallel performance!")
        elif speedup >= 2.0:
            logger.info("  ✅ GOOD parallel performance")
        elif speedup >= 1.5:
            logger.info("  🔶 MODERATE parallel performance")
        else:
            logger.warning("  ⚠️  MINIMAL parallel benefit - investigate")
    else:
        logger.warning(f"⚠️  {analyst_type.upper()}: Cannot calculate speedup (no sequential estimate)")


def get_parallel_execution_tips() -> str:
    """
    Get tips for maximizing parallel execution performance.
    """
    return """
⚡ PARALLEL EXECUTION OPTIMIZATION TIPS:

1. **Batch Similar Operations**: Group similar tool calls together
2. **Minimize Dependencies**: Structure tools to be independent when possible
3. **Use Async Tools**: Ensure all tools support async execution
4. **Monitor Performance**: Track speedup metrics to identify bottlenecks
5. **Cache When Possible**: Enable smart caching for repeated queries
6. **Error Isolation**: Use circuit breakers to prevent cascade failures

Target Performance:
- Market Analyst: <20s for all tools (2-3x speedup)
- News Analyst: <30s for all tools (2-4x speedup)
- Social Analyst: <25s for all tools (2-3x speedup)
- Fundamentals Analyst: <22s for all tools (3-5x speedup)
"""


# Export key functions
__all__ = [
    'verify_parallel_config',
    'log_parallel_performance_summary',
    'get_parallel_execution_tips'
]