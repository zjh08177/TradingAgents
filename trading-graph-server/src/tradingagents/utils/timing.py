"""
Timing utilities for tracking agent and tool execution times
"""
import time
import logging
from functools import wraps
from typing import Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class TimingTracker:
    """Tracks execution times for agents and tools"""
    
    def __init__(self):
        self.agent_times: Dict[str, float] = {}
        self.tool_times: Dict[str, float] = {}
        self.start_times: Dict[str, float] = {}
        self.total_start_time = None
        self.total_end_time = None
    
    def start_total(self):
        """Start tracking total execution time"""
        self.total_start_time = time.time()
        logger.info(f"⏱️ Total execution started at {datetime.now()}")
    
    def end_total(self):
        """End tracking total execution time"""
        self.total_end_time = time.time()
        if self.total_start_time:
            total_duration = self.total_end_time - self.total_start_time
            logger.info(f"⏱️ Total execution completed in {total_duration:.2f}s ({total_duration/60:.2f} minutes)")
            return total_duration
        return 0
    
    def start_agent(self, agent_name: str):
        """Start tracking an agent's execution time"""
        self.start_times[agent_name] = time.time()
        logger.info(f"⏱️ {agent_name}: Started execution")
    
    def end_agent(self, agent_name: str):
        """End tracking an agent's execution time"""
        if agent_name in self.start_times:
            duration = time.time() - self.start_times[agent_name]
            self.agent_times[agent_name] = self.agent_times.get(agent_name, 0) + duration
            logger.info(f"⏱️ {agent_name}: Completed in {duration:.2f}s")
            del self.start_times[agent_name]
            return duration
        return 0
    
    def start_tool(self, tool_name: str):
        """Start tracking a tool's execution time"""
        self.start_times[f"tool_{tool_name}"] = time.time()
        logger.info(f"🔧 Tool {tool_name}: Started")
    
    def end_tool(self, tool_name: str):
        """End tracking a tool's execution time"""
        key = f"tool_{tool_name}"
        if key in self.start_times:
            duration = time.time() - self.start_times[key]
            self.tool_times[tool_name] = self.tool_times.get(tool_name, 0) + duration
            logger.info(f"🔧 Tool {tool_name}: Completed in {duration:.2f}s")
            del self.start_times[key]
            return duration
        return 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all timing information"""
        total_agent_time = sum(self.agent_times.values())
        total_tool_time = sum(self.tool_times.values())
        
        summary = {
            "total_duration": self.total_end_time - self.total_start_time if self.total_start_time and self.total_end_time else 0,
            "agent_times": self.agent_times,
            "tool_times": self.tool_times,
            "total_agent_time": total_agent_time,
            "total_tool_time": total_tool_time,
            "agent_count": len(self.agent_times),
            "tool_call_count": len(self.tool_times)
        }
        
        # Log summary
        logger.info("=" * 60)
        logger.info("⏱️ TIMING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Duration: {summary['total_duration']:.2f}s ({summary['total_duration']/60:.2f} minutes)")
        logger.info(f"Total Agent Time: {total_agent_time:.2f}s")
        logger.info(f"Total Tool Time: {total_tool_time:.2f}s")
        logger.info("\nAgent Times:")
        for agent, duration in sorted(self.agent_times.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {agent}: {duration:.2f}s ({duration/60:.2f} minutes)")
        logger.info("\nTool Times:")
        for tool, duration in sorted(self.tool_times.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {tool}: {duration:.2f}s")
        logger.info("=" * 60)
        
        return summary

# Global timing tracker instance
timing_tracker = TimingTracker()

def timed_agent(agent_name: str):
    """Decorator to time agent execution"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            timing_tracker.start_agent(agent_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                timing_tracker.end_agent(agent_name)
        return wrapper
    return decorator

def timed_tool(tool_name: str):
    """Decorator to time tool execution"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            timing_tracker.start_tool(tool_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                timing_tracker.end_tool(tool_name)
        return wrapper
    return decorator