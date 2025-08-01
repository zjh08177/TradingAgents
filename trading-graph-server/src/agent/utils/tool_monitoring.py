#!/usr/bin/env python3
"""
Tool Execution Monitoring and Alerting System - Task 6.1
Provides real-time monitoring of tool execution patterns, performance tracking, and alerting.
"""

import time
import logging
import json
import statistics
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import asyncio
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ToolExecution:
    """Records a single tool execution"""
    tool_name: str
    analyst_type: str
    start_time: float
    end_time: float
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    input_size: int = 0
    output_size: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.fromtimestamp(self.start_time).isoformat()

@dataclass
class ToolHealthMetrics:
    """Health metrics for a specific tool"""
    tool_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    recent_executions: List[float] = None
    last_execution: Optional[str] = None
    recent_errors: List[str] = None

    def __post_init__(self):
        if self.recent_executions is None:
            self.recent_executions = []
        if self.recent_errors is None:
            self.recent_errors = []

class ToolPerformanceMonitor:
    """
    Task 6.1: Tool execution monitoring and alerting system
    Tracks tool performance, detects anomalies, and provides health dashboards
    """
    
    def __init__(self, max_history: int = 1000, alert_threshold: float = 2.0):
        self.max_history = max_history
        self.alert_threshold = alert_threshold  # Standard deviations for anomaly detection
        
        # Storage
        self.executions: deque = deque(maxlen=max_history)
        self.tool_metrics: Dict[str, ToolHealthMetrics] = {}
        self.analyst_metrics: Dict[str, Dict[str, ToolHealthMetrics]] = defaultdict(dict)
        
        # Performance baselines
        self.performance_baselines: Dict[str, float] = {}
        self.anomaly_alerts: List[Dict[str, Any]] = []
        
        # Thread-safe access
        self._lock = threading.Lock()
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        logger.info("🔧 Tool Performance Monitor initialized")

    def record_execution(self, 
                        tool_name: str, 
                        analyst_type: str,
                        start_time: float,
                        end_time: float,
                        success: bool,
                        error_message: Optional[str] = None,
                        input_data: Any = None,
                        output_data: Any = None) -> ToolExecution:
        """Record a tool execution for monitoring"""
        
        execution_time = end_time - start_time
        input_size = len(str(input_data)) if input_data else 0
        output_size = len(str(output_data)) if output_data else 0
        
        execution = ToolExecution(
            tool_name=tool_name,
            analyst_type=analyst_type,
            start_time=start_time,
            end_time=end_time,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            input_size=input_size,
            output_size=output_size
        )
        
        with self._lock:
            # Store execution
            self.executions.append(execution)
            
            # Update tool metrics
            self._update_tool_metrics(execution)
            
            # Update analyst-specific metrics
            self._update_analyst_metrics(execution)
            
            # Check for anomalies
            self._check_anomalies(execution)
        
        # Log execution
        status = "✅" if success else "❌"
        logger.info(f"🔧 TOOL MONITOR: {status} {tool_name} ({analyst_type}) - {execution_time:.3f}s")
        
        if not success and error_message:
            logger.warning(f"🚨 TOOL ERROR: {tool_name} - {error_message}")
        
        return execution

    def _update_tool_metrics(self, execution: ToolExecution):
        """Update metrics for a specific tool"""
        if execution.tool_name not in self.tool_metrics:
            self.tool_metrics[execution.tool_name] = ToolHealthMetrics(tool_name=execution.tool_name)
        
        metrics = self.tool_metrics[execution.tool_name]
        
        # Update counters
        metrics.total_executions += 1
        if execution.success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1
            if execution.error_message:
                metrics.recent_errors.append(execution.error_message)
                # Keep only last 10 errors
                if len(metrics.recent_errors) > 10:
                    metrics.recent_errors.pop(0)
        
        # Update success rate
        metrics.success_rate = metrics.successful_executions / metrics.total_executions
        
        # Update timing metrics
        metrics.recent_executions.append(execution.execution_time)
        if len(metrics.recent_executions) > 50:  # Keep last 50 executions for baseline
            metrics.recent_executions.pop(0)
        
        if execution.execution_time < metrics.min_execution_time:
            metrics.min_execution_time = execution.execution_time
        if execution.execution_time > metrics.max_execution_time:
            metrics.max_execution_time = execution.execution_time
        
        # Calculate average from recent executions
        if metrics.recent_executions:
            metrics.avg_execution_time = statistics.mean(metrics.recent_executions)
        
        metrics.last_execution = execution.timestamp

    def _update_analyst_metrics(self, execution: ToolExecution):
        """Update metrics for analyst-specific tool usage"""
        if execution.tool_name not in self.analyst_metrics[execution.analyst_type]:
            self.analyst_metrics[execution.analyst_type][execution.tool_name] = ToolHealthMetrics(tool_name=execution.tool_name)
        
        metrics = self.analyst_metrics[execution.analyst_type][execution.tool_name]
        
        # Same update logic as tool metrics
        self._update_metrics_object(metrics, execution)

    def _update_metrics_object(self, metrics: ToolHealthMetrics, execution: ToolExecution):
        """Common metrics update logic"""
        metrics.total_executions += 1
        if execution.success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1
        
        metrics.success_rate = metrics.successful_executions / metrics.total_executions
        
        metrics.recent_executions.append(execution.execution_time)
        if len(metrics.recent_executions) > 50:
            metrics.recent_executions.pop(0)
        
        if execution.execution_time < metrics.min_execution_time:
            metrics.min_execution_time = execution.execution_time
        if execution.execution_time > metrics.max_execution_time:
            metrics.max_execution_time = execution.execution_time
        
        if metrics.recent_executions:
            metrics.avg_execution_time = statistics.mean(metrics.recent_executions)
        
        metrics.last_execution = execution.timestamp

    def _check_anomalies(self, execution: ToolExecution):
        """Detect performance anomalies and trigger alerts"""
        tool_name = execution.tool_name
        
        # Get baseline for this tool
        baseline = self.performance_baselines.get(tool_name)
        if baseline is None:
            # Establish baseline after 10 executions
            tool_executions = [e for e in self.executions if e.tool_name == tool_name and e.success]
            if len(tool_executions) >= 10:
                times = [e.execution_time for e in tool_executions[-10:]]
                self.performance_baselines[tool_name] = statistics.mean(times)
            return
        
        # Check for performance anomalies
        if execution.success:
            metrics = self.tool_metrics[tool_name]
            if len(metrics.recent_executions) >= 5:
                recent_avg = statistics.mean(metrics.recent_executions[-5:])
                recent_stdev = statistics.stdev(metrics.recent_executions[-5:]) if len(metrics.recent_executions[-5:]) > 1 else 0
                
                # Anomaly: execution time significantly higher than baseline
                if recent_stdev > 0 and abs(execution.execution_time - recent_avg) > (self.alert_threshold * recent_stdev):
                    self._trigger_alert(
                        alert_type="performance_anomaly",
                        tool_name=tool_name,
                        message=f"Tool {tool_name} execution time {execution.execution_time:.3f}s significantly differs from recent average {recent_avg:.3f}s",
                        severity="warning",
                        execution=execution
                    )
        
        # Check for failure patterns
        recent_failures = [e for e in list(self.executions)[-10:] if e.tool_name == tool_name and not e.success]
        if len(recent_failures) >= 3:
            self._trigger_alert(
                alert_type="repeated_failures",
                tool_name=tool_name,
                message=f"Tool {tool_name} has {len(recent_failures)} failures in last 10 executions",
                severity="critical",
                execution=execution
            )

    def _trigger_alert(self, alert_type: str, tool_name: str, message: str, severity: str, execution: ToolExecution):
        """Trigger an alert for detected anomaly"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": alert_type,
            "tool_name": tool_name,
            "analyst_type": execution.analyst_type,
            "message": message,
            "severity": severity,
            "execution_time": execution.execution_time,
            "success": execution.success
        }
        
        self.anomaly_alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.anomaly_alerts) > 100:
            self.anomaly_alerts.pop(0)
        
        # Log alert
        if severity == "critical":
            logger.error(f"🚨 CRITICAL ALERT: {message}")
        else:
            logger.warning(f"⚠️ ALERT: {message}")
        
        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"❌ Alert callback failed: {e}")

    def register_alert_callback(self, callback: Callable):
        """Register a callback function for alerts"""
        self.alert_callbacks.append(callback)
        logger.info(f"🔔 Alert callback registered: {callback.__name__}")

    def get_tool_health_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive tool health dashboard"""
        with self._lock:
            dashboard = {
                "timestamp": datetime.now().isoformat(),
                "overview": {
                    "total_executions": len(self.executions),
                    "total_tools": len(self.tool_metrics),
                    "total_analysts": len(self.analyst_metrics),
                    "recent_alerts": len([a for a in self.anomaly_alerts if 
                                        datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=1)])
                },
                "tool_health": {},
                "analyst_health": {},
                "recent_alerts": self.anomaly_alerts[-10:],  # Last 10 alerts
                "performance_summary": self._generate_performance_summary()
            }
            
            # Tool health details
            for tool_name, metrics in self.tool_metrics.items():
                dashboard["tool_health"][tool_name] = asdict(metrics)
            
            # Analyst health details
            for analyst_type, analyst_tools in self.analyst_metrics.items():
                dashboard["analyst_health"][analyst_type] = {}
                for tool_name, metrics in analyst_tools.items():
                    dashboard["analyst_health"][analyst_type][tool_name] = asdict(metrics)
            
            return dashboard

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary statistics"""
        if not self.executions:
            return {"message": "No executions recorded"}
        
        executions_list = list(self.executions)
        total_executions = len(executions_list)
        successful_executions = len([e for e in executions_list if e.success])
        
        execution_times = [e.execution_time for e in executions_list if e.success]
        
        summary = {
            "total_executions": total_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "avg_execution_time": statistics.mean(execution_times) if execution_times else 0,
            "median_execution_time": statistics.median(execution_times) if execution_times else 0,
            "min_execution_time": min(execution_times) if execution_times else 0,
            "max_execution_time": max(execution_times) if execution_times else 0
        }
        
        # Recent performance (last hour)
        recent_cutoff = time.time() - 3600  # 1 hour ago
        recent_executions = [e for e in executions_list if e.start_time > recent_cutoff]
        
        if recent_executions:
            recent_times = [e.execution_time for e in recent_executions if e.success]
            summary["recent_performance"] = {
                "executions_last_hour": len(recent_executions),
                "success_rate_last_hour": len([e for e in recent_executions if e.success]) / len(recent_executions),
                "avg_time_last_hour": statistics.mean(recent_times) if recent_times else 0
            }
        
        return summary

    def export_metrics(self, filepath: str):
        """Export all metrics to JSON file"""
        dashboard = self.get_tool_health_dashboard()
        
        try:
            with open(filepath, 'w') as f:
                json.dump(dashboard, f, indent=2, default=str)
            logger.info(f"📊 Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"❌ Failed to export metrics: {e}")

    def get_tool_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on tool performance analysis"""
        recommendations = []
        
        with self._lock:
            for tool_name, metrics in self.tool_metrics.items():
                # Recommend optimization for slow tools
                if metrics.avg_execution_time > 10.0:  # > 10 seconds
                    recommendations.append({
                        "type": "performance_optimization",
                        "tool": tool_name,
                        "message": f"Tool {tool_name} averages {metrics.avg_execution_time:.2f}s - consider optimization",
                        "priority": "medium",
                        "metric": metrics.avg_execution_time
                    })
                
                # Recommend investigation for unreliable tools
                if metrics.success_rate < 0.8 and metrics.total_executions > 5:
                    recommendations.append({
                        "type": "reliability_issue",
                        "tool": tool_name,
                        "message": f"Tool {tool_name} has {metrics.success_rate:.1%} success rate - investigate failures",
                        "priority": "high",
                        "metric": metrics.success_rate
                    })
                
                # Recommend parallel execution for frequently used tools
                if metrics.total_executions > 20 and metrics.avg_execution_time > 5.0:
                    recommendations.append({
                        "type": "parallelization_candidate",
                        "tool": tool_name,
                        "message": f"Tool {tool_name} used frequently ({metrics.total_executions} times) - consider parallel execution",
                        "priority": "low",
                        "metric": metrics.total_executions
                    })
        
        return sorted(recommendations, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)

# Global monitor instance
_global_monitor: Optional[ToolPerformanceMonitor] = None

def get_tool_monitor() -> ToolPerformanceMonitor:
    """Get the global tool monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ToolPerformanceMonitor()
    return _global_monitor

def monitor_tool_execution(tool_name: str, analyst_type: str):
    """
    Decorator to automatically monitor tool execution
    
    Usage:
    @monitor_tool_execution("get_stock_data", "market")
    async def tool_function():
        pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitor = get_tool_monitor()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                end_time = time.time()
                
                # Record successful execution
                monitor.record_execution(
                    tool_name=tool_name,
                    analyst_type=analyst_type,
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                    input_data=kwargs,
                    output_data=result
                )
                
                return result
                
            except Exception as e:
                end_time = time.time()
                
                # Record failed execution
                monitor.record_execution(
                    tool_name=tool_name,
                    analyst_type=analyst_type,
                    start_time=start_time,
                    end_time=end_time,
                    success=False,
                    error_message=str(e),
                    input_data=kwargs
                )
                
                raise
        
        return wrapper
    return decorator

def log_tool_health_summary():
    """Log a summary of tool health metrics"""
    monitor = get_tool_monitor()
    dashboard = monitor.get_tool_health_dashboard()
    
    logger.info("\n" + "="*80)
    logger.info("🔧 TOOL HEALTH DASHBOARD")
    logger.info("="*80)
    
    overview = dashboard["overview"]
    logger.info(f"📊 Total Executions: {overview['total_executions']}")
    logger.info(f"🔧 Tools Monitored: {overview['total_tools']}")
    logger.info(f"👥 Analysts Active: {overview['total_analysts']}")
    logger.info(f"🚨 Recent Alerts: {overview['recent_alerts']}")
    
    # Performance summary
    perf = dashboard["performance_summary"]
    if "success_rate" in perf:
        logger.info(f"✅ Overall Success Rate: {perf['success_rate']:.1%}")
        logger.info(f"⏱️  Average Execution Time: {perf['avg_execution_time']:.3f}s")
    
    # Tool recommendations
    recommendations = monitor.get_tool_recommendations()
    if recommendations:
        logger.info("\n🎯 RECOMMENDATIONS:")
        for rec in recommendations[:5]:  # Top 5 recommendations
            priority = rec['priority'].upper()
            logger.info(f"   {priority}: {rec['message']}")
    
    logger.info("="*80)