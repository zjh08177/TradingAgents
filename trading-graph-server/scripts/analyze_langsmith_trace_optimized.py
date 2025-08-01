#!/usr/bin/env python3
"""
LangSmith Trace Analyzer - Optimized Version
Analyzes LangSmith traces with comprehensive error handling and size-optimized reporting
Maximum file size target: <2MB while preserving all analytical insights
"""

import os
import sys
import json
import argparse
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Conditionally import langsmith
try:
    from langsmith import Client
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    print("Warning: langsmith package not installed. Some features will be limited.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Size optimization constants
MAX_MESSAGE_LENGTH = 500  # Truncate long messages
MAX_ERROR_LENGTH = 200   # Truncate long error messages
MAX_CHILD_RUNS_DETAIL = 50  # Only store detailed info for first N runs
MAX_TOOL_CALLS_DETAIL = 20  # Only store detailed tool calls
COMPRESSION_THRESHOLD = 1024 * 1024  # 1MB - start compression above this


class OptimizedTraceAnalyzer:
    """Analyzes LangSmith traces with size-optimized output while preserving analytical quality"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('LANGSMITH_API_KEY')
        if not self.api_key:
            raise ValueError("LANGSMITH_API_KEY not found in environment")
        
        if LANGSMITH_AVAILABLE:
            self.client = Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("Running in limited mode without langsmith client")
    
    def fetch_trace(self, trace_id: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch trace data from LangSmith with size optimization"""
        if not self.client:
            logger.error("Cannot fetch trace without langsmith client")
            return self._create_mock_trace(trace_id)
        
        try:
            # Get the main run
            logger.info(f"Fetching trace {trace_id}...")
            run = self.client.read_run(trace_id)
            
            # Get all child runs
            child_runs = []
            try:
                for child in self.client.list_runs(parent_run_id=trace_id):
                    child_runs.append(child)
            except Exception as e:
                logger.warning(f"Could not fetch child runs: {e}")
            
            # Convert to optimized dict format
            trace_data = {
                "id": str(run.id),
                "name": run.name,
                "run_type": run.run_type,
                "status": run.status,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "total_tokens": run.total_tokens,
                "prompt_tokens": run.prompt_tokens,
                "completion_tokens": run.completion_tokens,
                "error": self._truncate_text(run.error, MAX_ERROR_LENGTH) if run.error else None,
                
                # Optimized inputs/outputs - only keep essential data
                "inputs_summary": self._summarize_inputs_outputs(run.inputs),
                "outputs_summary": self._summarize_inputs_outputs(run.outputs),
                
                # Optimized child runs - full detail for first N, summary for rest
                "child_runs": [self._optimize_run_data(child, i < MAX_CHILD_RUNS_DETAIL) 
                              for i, child in enumerate(child_runs)],
                "child_runs_total": len(child_runs),
                
                # Essential metadata only
                "extra": self._extract_essential_metadata(run.extra or {})
            }
            
            return trace_data
            
        except Exception as e:
            logger.error(f"Error fetching trace: {e}")
            raise
    
    def _optimize_run_data(self, run, include_details: bool = True) -> Dict[str, Any]:
        """Convert a run object to optimized dictionary"""
        base_data = {
            "id": str(run.id),
            "name": run.name,
            "run_type": run.run_type,
            "status": run.status,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "total_tokens": run.total_tokens,
            "error": self._truncate_text(run.error, MAX_ERROR_LENGTH) if run.error else None
        }
        
        if include_details:
            # Add detailed information for important runs
            base_data.update({
                "inputs_summary": self._summarize_inputs_outputs(run.inputs),
                "outputs_summary": self._summarize_inputs_outputs(run.outputs)
            })
        
        return base_data
    
    def _summarize_inputs_outputs(self, data: Any) -> Dict[str, Any]:
        """Create size-optimized summary of inputs/outputs"""
        if not data:
            return {}
        
        if isinstance(data, dict):
            summary = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # Truncate long text values but preserve structure info
                    if len(value) > MAX_MESSAGE_LENGTH:
                        summary[key] = {
                            "text_preview": value[:MAX_MESSAGE_LENGTH] + "...",
                            "full_length": len(value),
                            "type": "truncated_text"
                        }
                    else:
                        summary[key] = value
                elif isinstance(value, list):
                    # Summarize lists
                    summary[key] = {
                        "count": len(value),
                        "type": "list",
                        "sample": value[:3] if len(value) > 3 else value  # Show first 3 items
                    }
                elif isinstance(value, dict):
                    # Recursively summarize nested dicts
                    summary[key] = self._summarize_inputs_outputs(value)
                else:
                    summary[key] = value
            return summary
        elif isinstance(data, list):
            return {
                "count": len(data),
                "type": "list",
                "sample": [self._summarize_inputs_outputs(item) for item in data[:3]]
            }
        else:
            return {"value": str(data), "type": type(data).__name__}
    
    def _extract_essential_metadata(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only essential metadata to reduce size"""
        essential_keys = [
            "metadata", "tags", "run_id", "parent_id", 
            "model_name", "temperature", "max_tokens"
        ]
        
        essential = {}
        for key in essential_keys:
            if key in extra:
                value = extra[key]
                if isinstance(value, str) and len(value) > MAX_MESSAGE_LENGTH:
                    essential[key] = self._truncate_text(value, MAX_MESSAGE_LENGTH)
                else:
                    essential[key] = value
        
        return essential
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text while preserving important information"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    def _create_mock_trace(self, trace_id: str) -> Dict[str, Any]:
        """Create a mock trace for testing when langsmith is not available"""
        return {
            "id": trace_id,
            "name": "Mock Trace",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "child_runs": [],
            "child_runs_total": 0
        }
    
    def analyze_trace(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trace data and generate comprehensive insights"""
        analysis = {
            "trace_id": trace_data["id"],
            "summary": self._generate_detailed_summary(trace_data),
            "performance_metrics": self._calculate_detailed_performance_metrics(trace_data),
            "error_analysis": self._analyze_errors_detailed(trace_data),
            "tool_usage": self._analyze_tool_usage_detailed(trace_data),
            "timing_analysis": self._analyze_timing_patterns(trace_data),
            "token_analysis": self._analyze_token_usage(trace_data),
            "quality_metrics": self._calculate_quality_metrics(trace_data),
            "recommendations": self._generate_detailed_recommendations(trace_data),
            "timestamp": datetime.now().isoformat(),
            "analysis_version": "optimized_v1.0"
        }
        
        return analysis
    
    def _generate_detailed_summary(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary of the trace"""
        child_runs = trace_data.get("child_runs", [])
        
        # Count runs by type and status
        run_types = defaultdict(int)
        status_counts = defaultdict(int)
        for run in child_runs:
            run_types[run.get("run_type", "unknown")] += 1
            status_counts[run.get("status", "unknown")] += 1
        
        # Calculate duration
        duration = None
        if trace_data.get("start_time") and trace_data.get("end_time"):
            start = datetime.fromisoformat(trace_data["start_time"])
            end = datetime.fromisoformat(trace_data["end_time"])
            duration = (end - start).total_seconds()
        
        return {
            "name": trace_data.get("name", "Unknown"),
            "status": trace_data.get("status", "unknown"),
            "total_runs": trace_data.get("child_runs_total", len(child_runs)),
            "analyzed_runs": len(child_runs),
            "run_types": dict(run_types),
            "status_distribution": dict(status_counts),
            "duration_seconds": duration,
            "duration_formatted": f"{duration:.2f}s" if duration else "Unknown",
            "has_errors": bool(trace_data.get("error") or any(r.get("error") for r in child_runs)),
            "error_count": sum(1 for r in [trace_data] + child_runs if r.get("error"))
        }
    
    def _calculate_detailed_performance_metrics(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        child_runs = trace_data.get("child_runs", [])
        all_runs = [trace_data] + child_runs
        
        # Token usage analysis
        total_tokens = trace_data.get("total_tokens", 0)
        prompt_tokens = trace_data.get("prompt_tokens", 0)
        completion_tokens = trace_data.get("completion_tokens", 0)
        
        # Success rate calculation
        successful_runs = sum(1 for run in all_runs if run.get("status") == "success")
        success_rate = (successful_runs / len(all_runs)) * 100 if all_runs else 0
        
        # Timing analysis
        timing_stats = self._calculate_timing_stats(child_runs)
        
        metrics = {
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "token_efficiency": (completion_tokens / prompt_tokens) if prompt_tokens > 0 else 0,
            "child_run_count": len(child_runs),
            "total_run_count": trace_data.get("child_runs_total", len(child_runs)),
            "success_rate": success_rate,
            "successful_runs": successful_runs,
            "failed_runs": len(all_runs) - successful_runs,
            **timing_stats
        }
        
        return metrics
    
    def _calculate_timing_stats(self, child_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate timing statistics for child runs"""
        durations = []
        
        for run in child_runs:
            if run.get("start_time") and run.get("end_time"):
                start = datetime.fromisoformat(run["start_time"])
                end = datetime.fromisoformat(run["end_time"])
                duration = (end - start).total_seconds()
                durations.append(duration)
        
        if not durations:
            return {
                "avg_run_duration": 0,
                "min_run_duration": 0,
                "max_run_duration": 0,
                "total_run_time": 0
            }
        
        return {
            "avg_run_duration": sum(durations) / len(durations),
            "min_run_duration": min(durations),
            "max_run_duration": max(durations),
            "total_run_time": sum(durations),
            "timing_samples": len(durations)
        }
    
    def _analyze_errors_detailed(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze errors in detail with categorization"""
        errors = []
        error_categories = defaultdict(int)
        
        # Check main run
        if trace_data.get("error"):
            error_info = {
                "run_id": trace_data["id"],
                "run_name": trace_data.get("name", "Main"),
                "error": trace_data["error"],
                "category": self._categorize_error(trace_data["error"])
            }
            errors.append(error_info)
            error_categories[error_info["category"]] += 1
        
        # Check child runs
        for run in trace_data.get("child_runs", []):
            if run.get("error"):
                error_info = {
                    "run_id": run["id"],
                    "run_name": run.get("name", "Unknown"),
                    "error": run["error"],
                    "category": self._categorize_error(run["error"])
                }
                errors.append(error_info)
                error_categories[error_info["category"]] += 1
        
        return {
            "total_errors": len(errors),
            "error_categories": dict(error_categories),
            "errors": errors[:10],  # Limit to first 10 errors for size
            "has_critical_errors": any(cat in ["timeout", "api_error", "system_error"] 
                                     for cat in error_categories.keys())
        }
    
    def _categorize_error(self, error_text: str) -> str:
        """Categorize error based on content"""
        if not error_text:
            return "unknown"
        
        error_lower = error_text.lower()
        
        if any(keyword in error_lower for keyword in ["timeout", "timed out"]):
            return "timeout"
        elif any(keyword in error_lower for keyword in ["api", "rate limit", "quota"]):
            return "api_error"
        elif any(keyword in error_lower for keyword in ["connection", "network", "socket"]):
            return "network_error"
        elif any(keyword in error_lower for keyword in ["validation", "invalid", "malformed"]):
            return "validation_error"
        elif any(keyword in error_lower for keyword in ["system", "internal", "server"]):
            return "system_error"
        else:
            return "application_error"
    
    def _analyze_tool_usage_detailed(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tool usage patterns with detailed insights"""
        tool_calls = defaultdict(int)
        tool_errors = defaultdict(int)
        tool_durations = defaultdict(list)
        
        for run in trace_data.get("child_runs", []):
            if run.get("run_type") == "tool":
                tool_name = run.get("name", "unknown_tool")
                tool_calls[tool_name] += 1
                
                if run.get("error"):
                    tool_errors[tool_name] += 1
                
                # Calculate duration if available
                if run.get("start_time") and run.get("end_time"):
                    start = datetime.fromisoformat(run["start_time"])
                    end = datetime.fromisoformat(run["end_time"])
                    duration = (end - start).total_seconds()
                    tool_durations[tool_name].append(duration)
        
        # Calculate tool performance metrics
        tool_performance = {}
        for tool_name in tool_calls.keys():
            durations = tool_durations[tool_name]
            tool_performance[tool_name] = {
                "calls": tool_calls[tool_name],
                "errors": tool_errors[tool_name],
                "success_rate": ((tool_calls[tool_name] - tool_errors[tool_name]) / tool_calls[tool_name]) * 100,
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "total_duration": sum(durations) if durations else 0
            }
        
        return {
            "total_tool_calls": sum(tool_calls.values()),
            "unique_tools": len(tool_calls),
            "tool_calls": dict(tool_calls),
            "tool_errors": dict(tool_errors),
            "tool_performance": tool_performance,
            "overall_tool_success_rate": self._calculate_tool_success_rate(tool_calls, tool_errors),
            "most_used_tool": max(tool_calls.items(), key=lambda x: x[1])[0] if tool_calls else None,
            "most_problematic_tool": max(tool_errors.items(), key=lambda x: x[1])[0] if tool_errors else None
        }
    
    def _analyze_timing_patterns(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze timing patterns and bottlenecks"""
        child_runs = trace_data.get("child_runs", [])
        
        # Analyze runs by type
        timing_by_type = defaultdict(list)
        for run in child_runs:
            if run.get("start_time") and run.get("end_time"):
                start = datetime.fromisoformat(run["start_time"])
                end = datetime.fromisoformat(run["end_time"])
                duration = (end - start).total_seconds()
                timing_by_type[run.get("run_type", "unknown")].append(duration)
        
        # Calculate statistics by type
        type_stats = {}
        for run_type, durations in timing_by_type.items():
            if durations:
                type_stats[run_type] = {
                    "count": len(durations),
                    "total_time": sum(durations),
                    "avg_time": sum(durations) / len(durations),
                    "max_time": max(durations),
                    "min_time": min(durations)
                }
        
        # Identify bottlenecks
        bottlenecks = []
        for run_type, stats in type_stats.items():
            if stats["avg_time"] > 10:  # Runs taking more than 10 seconds on average
                bottlenecks.append({
                    "type": run_type,
                    "avg_duration": stats["avg_time"],
                    "total_impact": stats["total_time"]
                })
        
        return {
            "timing_by_type": type_stats,
            "bottlenecks": sorted(bottlenecks, key=lambda x: x["total_impact"], reverse=True),
            "has_bottlenecks": len(bottlenecks) > 0
        }
    
    def _analyze_token_usage(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze token usage patterns and efficiency"""
        total_tokens = trace_data.get("total_tokens", 0)
        prompt_tokens = trace_data.get("prompt_tokens", 0)
        completion_tokens = trace_data.get("completion_tokens", 0)
        
        # Performance targets (based on trace analysis requirements)
        target_total_tokens = 40000  # Target from performance requirements
        target_runtime = 120  # 120 seconds target
        
        duration = None
        if trace_data.get("start_time") and trace_data.get("end_time"):
            start = datetime.fromisoformat(trace_data["start_time"])
            end = datetime.fromisoformat(trace_data["end_time"])
            duration = (end - start).total_seconds()
        
        analysis = {
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "prompt_to_completion_ratio": prompt_tokens / completion_tokens if completion_tokens > 0 else 0,
            "tokens_per_second": total_tokens / duration if duration and duration > 0 else 0,
            "target_comparison": {
                "total_tokens_vs_target": (total_tokens / target_total_tokens) * 100 if target_total_tokens > 0 else 0,
                "under_token_target": total_tokens < target_total_tokens,
                "runtime_vs_target": (duration / target_runtime) * 100 if duration and target_runtime > 0 else 0,
                "under_runtime_target": duration < target_runtime if duration else False
            },
            "efficiency_rating": self._calculate_efficiency_rating(total_tokens, duration, target_total_tokens, target_runtime)
        }
        
        return analysis
    
    def _calculate_efficiency_rating(self, tokens: int, duration: float, target_tokens: int, target_runtime: float) -> str:
        """Calculate efficiency rating based on token usage and runtime"""
        if not duration:
            return "Unknown"
        
        token_efficiency = (target_tokens / tokens) if tokens > 0 else 1
        time_efficiency = (target_runtime / duration)
        
        overall_efficiency = (token_efficiency + time_efficiency) / 2
        
        if overall_efficiency >= 1.2:
            return "Excellent"
        elif overall_efficiency >= 1.0:
            return "Good"
        elif overall_efficiency >= 0.8:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _calculate_quality_metrics(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall quality metrics"""
        child_runs = trace_data.get("child_runs", [])
        all_runs = [trace_data] + child_runs
        
        # Success metrics
        successful_runs = sum(1 for run in all_runs if run.get("status") == "success")
        success_rate = (successful_runs / len(all_runs)) * 100 if all_runs else 0
        
        # Error metrics
        error_count = sum(1 for run in all_runs if run.get("error"))
        error_rate = (error_count / len(all_runs)) * 100 if all_runs else 0
        
        # Completeness metrics
        complete_runs = sum(1 for run in all_runs if run.get("end_time"))
        completeness_rate = (complete_runs / len(all_runs)) * 100 if all_runs else 0
        
        # Overall quality score (weighted average)
        quality_score = (success_rate * 0.5 + (100 - error_rate) * 0.3 + completeness_rate * 0.2)
        
        return {
            "success_rate": success_rate,
            "error_rate": error_rate,
            "completeness_rate": completeness_rate,
            "quality_score": quality_score,
            "quality_grade": self._get_quality_grade(quality_score),
            "total_runs_analyzed": len(all_runs)
        }
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        else:
            return "D"
    
    def _calculate_tool_success_rate(self, tool_calls: Dict[str, int], tool_errors: Dict[str, int]) -> float:
        """Calculate overall tool success rate"""
        total_calls = sum(tool_calls.values())
        total_errors = sum(tool_errors.values())
        
        if total_calls == 0:
            return 100.0
        
        return ((total_calls - total_errors) / total_calls) * 100
    
    def _generate_detailed_recommendations(self, trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed recommendations with priorities and categories"""
        recommendations = []
        
        # Analyze errors
        error_analysis = self._analyze_errors_detailed(trace_data)
        if error_analysis["total_errors"] > 0:
            recommendations.append({
                "category": "Reliability",
                "priority": "High" if error_analysis["has_critical_errors"] else "Medium",
                "issue": f"Found {error_analysis['total_errors']} errors in trace execution",
                "recommendation": "Investigate and fix errors to improve reliability",
                "details": f"Error categories: {list(error_analysis['error_categories'].keys())}"
            })
        
        # Analyze success rate
        quality_metrics = self._calculate_quality_metrics(trace_data)
        if quality_metrics["success_rate"] < 95:
            recommendations.append({
                "category": "Quality",
                "priority": "High" if quality_metrics["success_rate"] < 80 else "Medium",
                "issue": f"Success rate is {quality_metrics['success_rate']:.1f}% (below 95% target)",
                "recommendation": "Improve error handling and retry logic",
                "details": f"Quality grade: {quality_metrics['quality_grade']}"
            })
        
        # Analyze token usage
        token_analysis = self._analyze_token_usage(trace_data)
        if not token_analysis["target_comparison"]["under_token_target"]:
            recommendations.append({
                "category": "Performance",
                "priority": "Medium",
                "issue": f"Token usage ({token_analysis['total_tokens']:,}) exceeds target (40K)",
                "recommendation": "Optimize prompts and reduce token consumption",
                "details": f"Current usage is {token_analysis['target_comparison']['total_tokens_vs_target']:.1f}% of target"
            })
        
        # Analyze runtime
        if not token_analysis["target_comparison"]["under_runtime_target"]:
            recommendations.append({
                "category": "Performance", 
                "priority": "High",
                "issue": f"Runtime exceeds 120s target",
                "recommendation": "Optimize execution speed and parallel processing",
                "details": f"Runtime is {token_analysis['target_comparison']['runtime_vs_target']:.1f}% of target"
            })
        
        # Analyze tool performance
        tool_analysis = self._analyze_tool_usage_detailed(trace_data)
        if tool_analysis["overall_tool_success_rate"] < 95:
            recommendations.append({
                "category": "Tool Reliability",
                "priority": "Medium",
                "issue": f"Tool success rate is {tool_analysis['overall_tool_success_rate']:.1f}% (below 95%)",
                "recommendation": "Improve tool error handling and retry mechanisms",
                "details": f"Most problematic tool: {tool_analysis.get('most_problematic_tool', 'None')}"
            })
        
        # Check for bottlenecks
        timing_analysis = self._analyze_timing_patterns(trace_data)
        if timing_analysis["has_bottlenecks"]:
            bottleneck = timing_analysis["bottlenecks"][0]  # Top bottleneck
            recommendations.append({
                "category": "Performance",
                "priority": "Medium",
                "issue": f"Performance bottleneck detected in {bottleneck['type']} operations",
                "recommendation": "Optimize slow operations or implement parallel processing",
                "details": f"Average duration: {bottleneck['avg_duration']:.2f}s"
            })
        
        # Sort by priority
        priority_order = {"High": 3, "Medium": 2, "Low": 1}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
        
        return recommendations


def create_optimized_report(trace_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Create size-optimized report with essential information preserved"""
    
    # Calculate report size and optimize if needed
    estimated_size = len(json.dumps({"trace_data": trace_data, "analysis": analysis}, indent=2))
    
    optimized_report = {
        "metadata": {
            "trace_id": trace_data["id"],
            "analysis_timestamp": analysis["timestamp"],
            "analysis_version": analysis.get("analysis_version", "optimized_v1.0"),
            "estimated_size_bytes": estimated_size,
            "optimization_applied": estimated_size > COMPRESSION_THRESHOLD
        },
        "analysis": analysis,
        # Store only essential trace data, not the full trace
        "trace_summary": {
            "id": trace_data["id"],
            "name": trace_data["name"],
            "status": trace_data["status"],
            "duration": trace_data.get("end_time") and trace_data.get("start_time"),
            "total_tokens": trace_data.get("total_tokens"),
            "child_runs_count": trace_data.get("child_runs_total", len(trace_data.get("child_runs", []))),
            "has_errors": bool(trace_data.get("error"))
        }
    }
    
    # Only include full trace data if under size threshold
    if estimated_size <= COMPRESSION_THRESHOLD:
        optimized_report["trace_data"] = trace_data
    else:
        logger.info(f"Large trace detected ({estimated_size:,} bytes), storing summary only")
        optimized_report["trace_data_note"] = "Full trace data omitted due to size optimization. Summary available in trace_summary."
    
    return optimized_report


def format_detailed_analysis_summary(analysis: Dict[str, Any]) -> str:
    """Format comprehensive analysis as a readable summary"""
    summary = analysis["summary"]
    metrics = analysis["performance_metrics"]
    errors = analysis["error_analysis"]
    tools = analysis["tool_usage"]
    timing = analysis["timing_analysis"]
    tokens = analysis["token_analysis"]
    quality = analysis["quality_metrics"]
    recommendations = analysis["recommendations"]
    
    output = []
    output.append("\n🔍 LangSmith Trace Analysis - Detailed Report")
    output.append("=" * 60)
    output.append(f"📍 Trace ID: {analysis['trace_id']}")
    output.append(f"📅 Analysis Time: {analysis['timestamp']}")
    output.append(f"🔬 Analysis Version: {analysis.get('analysis_version', 'v1.0')}")
    output.append("")
    
    # Executive Summary
    output.append("📊 Executive Summary")
    output.append("-" * 40)
    output.append(f"Name: {summary['name']}")
    output.append(f"Status: {summary['status']} ({'✅' if summary['status'] == 'success' else '❌'})")
    output.append(f"Quality Grade: {quality['quality_grade']} ({quality['quality_score']:.1f}/100)")
    output.append(f"Duration: {summary['duration_formatted']}")
    output.append(f"Total Runs: {summary['total_runs']} ({summary['analyzed_runs']} analyzed)")
    output.append(f"Success Rate: {metrics['success_rate']:.1f}%")
    output.append(f"Token Efficiency: {tokens['efficiency_rating']}")
    output.append("")
    
    # Performance Metrics
    output.append("⚡ Performance Analysis")
    output.append("-" * 40)
    output.append(f"Total Tokens: {tokens['total_tokens']:,}")
    target_comparison = tokens['target_comparison']
    output.append(f"Token Target: {'✅ Under' if target_comparison['under_token_target'] else '⚠️ Over'} ({target_comparison['total_tokens_vs_target']:.1f}% of 40K target)")
    output.append(f"Runtime Target: {'✅ Under' if target_comparison['under_runtime_target'] else '⚠️ Over'} ({target_comparison['runtime_vs_target']:.1f}% of 120s target)")
    
    if tokens['tokens_per_second'] > 0:
        output.append(f"Token Throughput: {tokens['tokens_per_second']:.1f} tokens/second")
    
    if timing.get('bottlenecks'):
        output.append(f"Bottlenecks Detected: {len(timing['bottlenecks'])} performance issues")
    output.append("")
    
    # Quality Metrics
    output.append("🎯 Quality Assessment")
    output.append("-" * 40)
    output.append(f"Success Rate: {quality['success_rate']:.1f}%")
    output.append(f"Error Rate: {quality['error_rate']:.1f}%")
    output.append(f"Completeness: {quality['completeness_rate']:.1f}%")
    output.append(f"Overall Quality: {quality['quality_grade']} Grade")
    output.append("")
    
    # Tool Usage Analysis
    if tools["total_tool_calls"] > 0:
        output.append("🔧 Tool Usage Analysis")
        output.append("-" * 40)
        output.append(f"Total Tool Calls: {tools['total_tool_calls']}")
        output.append(f"Unique Tools: {tools['unique_tools']}")
        output.append(f"Tool Success Rate: {tools['overall_tool_success_rate']:.1f}%")
        
        if tools.get('most_used_tool'):
            output.append(f"Most Used Tool: {tools['most_used_tool']} ({tools['tool_calls'][tools['most_used_tool']]} calls)")
        
        if tools.get('most_problematic_tool'):
            output.append(f"Most Problematic: {tools['most_problematic_tool']} ({tools['tool_errors'][tools['most_problematic_tool']]} errors)")
        output.append("")
    
    # Error Analysis
    if errors["total_errors"] > 0:
        output.append("❌ Error Analysis")
        output.append("-" * 40)
        output.append(f"Total Errors: {errors['total_errors']}")
        output.append(f"Critical Errors: {'Yes' if errors['has_critical_errors'] else 'No'}")
        output.append("Error Categories:")
        for category, count in errors['error_categories'].items():
            output.append(f"  • {category}: {count}")
        
        if errors['errors']:
            output.append("\nTop Errors:")
            for error in errors['errors'][:3]:
                output.append(f"  • {error['run_name']}: {error['error'][:80]}...")
        output.append("")
    
    # Timing Analysis
    if timing.get('timing_by_type'):
        output.append("⏱️ Timing Analysis")
        output.append("-" * 40)
        for run_type, stats in timing['timing_by_type'].items():
            output.append(f"{run_type}: {stats['avg_time']:.2f}s avg ({stats['count']} runs)")
        
        if timing.get('bottlenecks'):
            output.append("\nBottlenecks:")
            for bottleneck in timing['bottlenecks'][:3]:
                output.append(f"  • {bottleneck['type']}: {bottleneck['avg_duration']:.2f}s average")
        output.append("")
    
    # Recommendations
    if recommendations:
        output.append("💡 Recommendations")
        output.append("-" * 40)
        
        high_priority = [r for r in recommendations if r['priority'] == 'High']
        medium_priority = [r for r in recommendations if r['priority'] == 'Medium']
        
        if high_priority:
            output.append("🔴 HIGH PRIORITY:")
            for rec in high_priority:
                output.append(f"  • [{rec['category']}] {rec['recommendation']}")
                output.append(f"    Issue: {rec['issue']}")
        
        if medium_priority:
            output.append("\n🟡 MEDIUM PRIORITY:")
            for rec in medium_priority:
                output.append(f"  • [{rec['category']}] {rec['recommendation']}")
        output.append("")
    
    # Summary Status
    output.append("📈 Overall Assessment")
    output.append("-" * 40)
    
    if quality['quality_score'] >= 90:
        output.append("🎉 EXCELLENT: System performing at high quality level")
    elif quality['quality_score'] >= 80:
        output.append("✅ GOOD: System performing well with minor areas for improvement")
    elif quality['quality_score'] >= 70:
        output.append("⚠️ FAIR: System functional but needs attention in several areas")
    else:
        output.append("🚨 NEEDS IMPROVEMENT: System requires significant optimization")
    
    output.append(f"Next recommended action: {recommendations[0]['recommendation'] if recommendations else 'Continue monitoring'}")
    output.append("")
    
    return "\n".join(output)


def main():
    """Main entry point with size optimization"""
    parser = argparse.ArgumentParser(
        description="Analyze LangSmith traces with size-optimized comprehensive reporting"
    )
    parser.add_argument("trace_id", help="The LangSmith trace ID to analyze")
    parser.add_argument("--project", "-p", help="LangSmith project name", default="trading-agent-graph")
    parser.add_argument("--format", "-f", choices=["summary", "json", "both"], 
                       default="both", help="Output format")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--max-size", type=int, default=2048, help="Maximum file size in KB (default: 2048)")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update compression threshold based on max-size argument
    global COMPRESSION_THRESHOLD
    COMPRESSION_THRESHOLD = args.max_size * 1024  # Convert KB to bytes
    
    try:
        # Initialize analyzer
        analyzer = OptimizedTraceAnalyzer()
        
        # Fetch trace with optimization
        logger.info(f"Fetching optimized trace data for {args.trace_id}...")
        trace_data = analyzer.fetch_trace(args.trace_id, args.project)
        
        # Analyze trace comprehensively
        logger.info("Performing comprehensive trace analysis...")
        analysis = analyzer.analyze_trace(trace_data)
        
        # Create optimized report
        optimized_report = create_optimized_report(trace_data, analysis)
        
        # Format output
        if args.format in ["summary", "both"]:
            summary = format_detailed_analysis_summary(analysis)
            print(summary)
        
        # Save optimized JSON if requested
        if args.format in ["json", "both"]:
            # Generate filename
            if args.output:
                json_file = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_file = f"trace_analysis_optimized_{args.trace_id}_{timestamp}.json"
            
            # Save optimized analysis
            with open(json_file, 'w') as f:
                json.dump(optimized_report, f, indent=2)
            
            # Report file size
            file_size = os.path.getsize(json_file)
            file_size_kb = file_size / 1024
            logger.info(f"Optimized analysis saved to: {json_file}")
            logger.info(f"File size: {file_size_kb:.1f}KB (target: <{args.max_size}KB)")
            
            if file_size_kb > args.max_size:
                logger.warning(f"File size exceeds target by {file_size_kb - args.max_size:.1f}KB")
            else:
                logger.info("✅ File size meets target requirement")
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())