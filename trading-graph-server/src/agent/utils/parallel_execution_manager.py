#!/usr/bin/env python3
"""
Parallel Agent Execution Framework - Phase 1, Task 1.3
Achieves 2-3x speedup through true parallel execution with error isolation
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import traceback

logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    """Result of parallel agent execution"""
    agent_name: str
    success: bool
    result: Any
    error: Optional[str]
    execution_time: float
    
@dataclass
class ParallelExecutionStats:
    """Statistics for parallel execution performance"""
    total_agents: int
    successful_agents: int
    failed_agents: int
    total_execution_time: float
    parallel_execution_time: float
    speedup_factor: float
    error_rate: float

class ParallelExecutionManager:
    """
    Manages true parallel execution of agents with error isolation
    Targets 2-3x speedup while maintaining reliability
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._execution_history = []
        
        logger.info(f"⚡ ParallelExecutionManager initialized with {max_workers} workers")
    
    async def execute_agents_parallel(
        self,
        agents: Dict[str, Callable],
        state: Dict[str, Any],
        timeout_per_agent: float = 30.0
    ) -> Tuple[Dict[str, Any], ParallelExecutionStats]:
        """
        Execute multiple agents in true parallel with error isolation
        Returns merged results and execution statistics
        """
        start_time = time.time()
        
        # Create tasks for all agents
        tasks = []
        for agent_name, agent_func in agents.items():
            task = self._execute_single_agent(
                agent_name, 
                agent_func, 
                state.copy(),  # Give each agent its own state copy
                timeout_per_agent
            )
            tasks.append(task)
        
        # Execute all agents in parallel
        logger.info(f"⚡ Starting parallel execution of {len(agents)} agents")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and merge
        merged_state = state.copy()
        execution_results = []
        successful = 0
        failed = 0
        
        for i, (agent_name, result) in enumerate(zip(agents.keys(), results)):
            if isinstance(result, ExecutionResult):
                execution_results.append(result)
                
                if result.success:
                    # Merge successful results into state
                    if isinstance(result.result, dict):
                        merged_state.update(result.result)
                    successful += 1
                    logger.info(
                        f"✅ {agent_name} completed in {result.execution_time:.2f}s"
                    )
                else:
                    failed += 1
                    # Add error information to state
                    merged_state[f"{agent_name}_error"] = result.error
                    logger.error(f"❌ {agent_name} failed: {result.error}")
            else:
                # Unexpected error
                failed += 1
                error_msg = str(result) if result else "Unknown error"
                merged_state[f"{agents.keys()[i]}_error"] = error_msg
                logger.error(f"❌ Unexpected error in agent {i}: {error_msg}")
        
        parallel_time = time.time() - start_time
        
        # Calculate speedup vs sequential
        total_sequential_time = sum(
            r.execution_time for r in execution_results if r.execution_time > 0
        )
        speedup = total_sequential_time / parallel_time if parallel_time > 0 else 1.0
        
        stats = ParallelExecutionStats(
            total_agents=len(agents),
            successful_agents=successful,
            failed_agents=failed,
            total_execution_time=total_sequential_time,
            parallel_execution_time=parallel_time,
            speedup_factor=speedup,
            error_rate=failed / len(agents) if agents else 0
        )
        
        # Log performance summary
        logger.info(
            f"⚡ Parallel execution complete: {successful}/{len(agents)} successful, "
            f"{parallel_time:.2f}s total ({speedup:.1f}x speedup)"
        )
        
        # Store in history
        self._execution_history.append(stats)
        
        return merged_state, stats
    
    async def _execute_single_agent(
        self,
        agent_name: str,
        agent_func: Callable,
        state: Dict[str, Any],
        timeout: float
    ) -> ExecutionResult:
        """
        Execute a single agent with timeout and error handling
        Provides complete error isolation
        """
        start_time = time.time()
        
        try:
            # Execute agent with timeout
            if asyncio.iscoroutinefunction(agent_func):
                # Async agent
                result = await asyncio.wait_for(
                    agent_func(state),
                    timeout=timeout
                )
            else:
                # Sync agent - run in thread pool
                result = await asyncio.wait_for(
                    asyncio.to_thread(agent_func, state),
                    timeout=timeout
                )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                agent_name=agent_name,
                success=True,
                result=result,
                error=None,
                execution_time=execution_time
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"Timeout after {timeout}s"
            logger.error(f"⏱️ {agent_name} timed out after {timeout}s")
            
            return ExecutionResult(
                agent_name=agent_name,
                success=False,
                result=self._create_safe_error_state(agent_name, error_msg),
                error=error_msg,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            error_trace = traceback.format_exc()
            logger.error(f"💥 {agent_name} failed with error: {error_msg}\n{error_trace}")
            
            return ExecutionResult(
                agent_name=agent_name,
                success=False,
                result=self._create_safe_error_state(agent_name, error_msg),
                error=error_msg,
                execution_time=execution_time
            )
    
    def _create_safe_error_state(self, agent_name: str, error: str) -> Dict[str, Any]:
        """Create safe error state for failed agent"""
        # Map agent names to their output keys
        output_mapping = {
            "market_analyst": "market_report",
            "news_analyst": "news_report",
            "social_analyst": "sentiment_report",
            "fundamentals_analyst": "fundamentals_report",
            "financial_analyst": "financial_report",
            "sentiment_analyst": "sentiment_report"
        }
        
        report_key = output_mapping.get(agent_name, f"{agent_name}_report")
        
        return {
            report_key: f"Analysis failed: {error}",
            f"{agent_name}_messages": [],
            f"{agent_name}_status": "error",
            "error": error
        }
    
    async def execute_with_fallback(
        self,
        primary_agents: Dict[str, Callable],
        fallback_agents: Dict[str, Callable],
        state: Dict[str, Any],
        fallback_threshold: float = 0.5
    ) -> Tuple[Dict[str, Any], ParallelExecutionStats]:
        """
        Execute agents with fallback strategy
        If more than threshold fail, execute fallback agents
        """
        # Execute primary agents
        primary_result, primary_stats = await self.execute_agents_parallel(
            primary_agents, state
        )
        
        # Check if we need fallback
        if primary_stats.error_rate > fallback_threshold:
            logger.warning(
                f"⚠️ High error rate ({primary_stats.error_rate:.1%}), "
                f"executing fallback agents"
            )
            
            # Execute fallback agents
            fallback_result, fallback_stats = await self.execute_agents_parallel(
                fallback_agents, primary_result
            )
            
            # Merge stats
            total_stats = ParallelExecutionStats(
                total_agents=primary_stats.total_agents + fallback_stats.total_agents,
                successful_agents=primary_stats.successful_agents + fallback_stats.successful_agents,
                failed_agents=primary_stats.failed_agents + fallback_stats.failed_agents,
                total_execution_time=primary_stats.total_execution_time + fallback_stats.total_execution_time,
                parallel_execution_time=primary_stats.parallel_execution_time + fallback_stats.parallel_execution_time,
                speedup_factor=(primary_stats.speedup_factor + fallback_stats.speedup_factor) / 2,
                error_rate=(primary_stats.failed_agents + fallback_stats.failed_agents) / 
                          (primary_stats.total_agents + fallback_stats.total_agents)
            )
            
            return fallback_result, total_stats
        
        return primary_result, primary_stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of all executions"""
        if not self._execution_history:
            return {"message": "No executions yet"}
        
        avg_speedup = sum(s.speedup_factor for s in self._execution_history) / len(self._execution_history)
        avg_error_rate = sum(s.error_rate for s in self._execution_history) / len(self._execution_history)
        total_agents = sum(s.total_agents for s in self._execution_history)
        total_successful = sum(s.successful_agents for s in self._execution_history)
        
        return {
            "total_executions": len(self._execution_history),
            "average_speedup": avg_speedup,
            "average_error_rate": avg_error_rate,
            "total_agents_executed": total_agents,
            "total_successful": total_successful,
            "success_rate": total_successful / total_agents if total_agents > 0 else 0
        }
    
    def __del__(self):
        """Cleanup thread pool executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Testing functions
async def test_parallel_execution():
    """Test parallel execution framework"""
    
    print("🧪 Testing Parallel Execution Framework\n")
    
    # Create test agents
    async def fast_agent(state):
        await asyncio.sleep(0.5)  # Simulate work
        return {"fast_report": "Fast analysis complete", "fast_data": 123}
    
    async def medium_agent(state):
        await asyncio.sleep(1.0)  # Simulate work
        return {"medium_report": "Medium analysis complete", "medium_data": 456}
    
    async def slow_agent(state):
        await asyncio.sleep(1.5)  # Simulate work
        return {"slow_report": "Slow analysis complete", "slow_data": 789}
    
    async def failing_agent(state):
        await asyncio.sleep(0.3)
        raise ValueError("Simulated agent failure")
    
    # Test 1: Basic parallel execution
    print("✅ Test 1 - Basic Parallel Execution:")
    manager = ParallelExecutionManager(max_workers=4)
    
    agents = {
        "fast_agent": fast_agent,
        "medium_agent": medium_agent,
        "slow_agent": slow_agent
    }
    
    test_state = {"ticker": "AAPL", "date": "2024-08-02"}
    
    start = time.time()
    result, stats = await manager.execute_agents_parallel(agents, test_state)
    parallel_time = time.time() - start
    
    print(f"  Parallel execution time: {parallel_time:.2f}s")
    print(f"  Sequential time (sum): {stats.total_execution_time:.2f}s")
    print(f"  Speedup: {stats.speedup_factor:.1f}x")
    print(f"  Success rate: {(1 - stats.error_rate):.1%}")
    
    assert stats.speedup_factor >= 2.0  # Should be ~3x for 3 agents
    assert stats.successful_agents == 3
    assert "fast_report" in result
    assert "medium_report" in result
    assert "slow_report" in result
    
    # Test 2: Error isolation
    print("\n✅ Test 2 - Error Isolation:")
    agents_with_error = {
        "fast_agent": fast_agent,
        "failing_agent": failing_agent,
        "medium_agent": medium_agent
    }
    
    result, stats = await manager.execute_agents_parallel(agents_with_error, test_state)
    
    print(f"  Successful agents: {stats.successful_agents}/{stats.total_agents}")
    print(f"  Error rate: {stats.error_rate:.1%}")
    print(f"  Failed agent error: {result.get('failing_agent_error', 'N/A')}")
    
    assert stats.successful_agents == 2  # fast and medium should succeed
    assert stats.failed_agents == 1  # failing_agent should fail
    assert "failing_agent_error" in result
    assert "fast_report" in result  # Other agents should still complete
    
    # Test 3: Timeout handling
    print("\n✅ Test 3 - Timeout Handling:")
    
    async def timeout_agent(state):
        await asyncio.sleep(5.0)  # Will timeout
        return {"timeout_report": "Should not see this"}
    
    agents_with_timeout = {
        "fast_agent": fast_agent,
        "timeout_agent": timeout_agent
    }
    
    result, stats = await manager.execute_agents_parallel(
        agents_with_timeout, test_state, timeout_per_agent=2.0
    )
    
    print(f"  Completed with timeout: {stats.successful_agents}/{stats.total_agents}")
    print(f"  Timeout error: {result.get('timeout_agent_error', 'N/A')}")
    
    assert "timeout_agent_error" in result
    assert "Timeout" in result["timeout_agent_error"]
    assert stats.failed_agents == 1
    
    # Test 4: Performance summary
    print("\n✅ Test 4 - Performance Summary:")
    summary = manager.get_performance_summary()
    
    print(f"  Total executions: {summary['total_executions']}")
    print(f"  Average speedup: {summary['average_speedup']:.1f}x")
    print(f"  Overall success rate: {summary['success_rate']:.1%}")
    
    assert summary['total_executions'] == 3
    assert summary['average_speedup'] >= 1.5
    
    print("\n✅ All tests passed! Achieved 2-3x speedup with error isolation.")
    return True


if __name__ == "__main__":
    asyncio.run(test_parallel_execution())