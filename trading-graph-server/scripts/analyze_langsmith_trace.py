#!/usr/bin/env python3
"""
LangSmith Trace Analyzer - Production Version
Analyzes LangSmith traces with comprehensive error handling and reporting
"""

import os
import sys
import json
import argparse
import logging
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


class TraceAnalyzer:
    """Analyzes LangSmith traces for performance and quality insights"""
    
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
        """Fetch trace data from LangSmith"""
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
            
            # Convert to dict format
            trace_data = {
                "id": str(run.id),
                "name": run.name,
                "run_type": run.run_type,
                "status": run.status,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "inputs": run.inputs,
                "outputs": run.outputs,
                "error": run.error,
                "total_tokens": run.total_tokens,
                "prompt_tokens": run.prompt_tokens,
                "completion_tokens": run.completion_tokens,
                "child_runs": [self._run_to_dict(child) for child in child_runs],
                "extra": run.extra or {}
            }
            
            return trace_data
            
        except Exception as e:
            logger.error(f"Error fetching trace: {e}")
            raise
    
    def _run_to_dict(self, run) -> Dict[str, Any]:
        """Convert a run object to dictionary"""
        return {
            "id": str(run.id),
            "name": run.name,
            "run_type": run.run_type,
            "status": run.status,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "total_tokens": run.total_tokens,
            "error": run.error
        }
    
    def _create_mock_trace(self, trace_id: str) -> Dict[str, Any]:
        """Create a mock trace for testing when langsmith is not available"""
        return {
            "id": trace_id,
            "name": "Mock Trace",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "child_runs": []
        }
    
    def analyze_trace(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trace data and generate insights"""
        analysis = {
            "trace_id": trace_data["id"],
            "summary": self._generate_summary(trace_data),
            "performance_metrics": self._calculate_performance_metrics(trace_data),
            "error_analysis": self._analyze_errors(trace_data),
            "tool_usage": self._analyze_tool_usage(trace_data),
            "recommendations": self._generate_recommendations(trace_data),
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
    
    def _generate_summary(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of the trace"""
        child_runs = trace_data.get("child_runs", [])
        
        # Count runs by type
        run_types = defaultdict(int)
        for run in child_runs:
            run_types[run.get("run_type", "unknown")] += 1
        
        # Calculate duration
        duration = None
        if trace_data.get("start_time") and trace_data.get("end_time"):
            start = datetime.fromisoformat(trace_data["start_time"])
            end = datetime.fromisoformat(trace_data["end_time"])
            duration = (end - start).total_seconds()
        
        return {
            "name": trace_data.get("name", "Unknown"),
            "status": trace_data.get("status", "unknown"),
            "total_runs": len(child_runs) + 1,
            "run_types": dict(run_types),
            "duration_seconds": duration,
            "has_errors": bool(trace_data.get("error") or any(r.get("error") for r in child_runs))
        }
    
    def _calculate_performance_metrics(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        metrics = {
            "total_tokens": trace_data.get("total_tokens", 0),
            "prompt_tokens": trace_data.get("prompt_tokens", 0),
            "completion_tokens": trace_data.get("completion_tokens", 0),
            "child_run_count": len(trace_data.get("child_runs", [])),
            "success_rate": self._calculate_success_rate(trace_data)
        }
        
        return metrics
    
    def _calculate_success_rate(self, trace_data: Dict[str, Any]) -> float:
        """Calculate success rate of runs"""
        all_runs = [trace_data] + trace_data.get("child_runs", [])
        if not all_runs:
            return 0.0
        
        successful = sum(1 for run in all_runs if run.get("status") == "success")
        return (successful / len(all_runs)) * 100
    
    def _analyze_errors(self, trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze errors in the trace"""
        errors = []
        
        # Check main run
        if trace_data.get("error"):
            errors.append({
                "run_id": trace_data["id"],
                "run_name": trace_data.get("name", "Main"),
                "error": trace_data["error"]
            })
        
        # Check child runs
        for run in trace_data.get("child_runs", []):
            if run.get("error"):
                errors.append({
                    "run_id": run["id"],
                    "run_name": run.get("name", "Unknown"),
                    "error": run["error"]
                })
        
        return errors
    
    def _analyze_tool_usage(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tool usage patterns"""
        tool_calls = defaultdict(int)
        tool_errors = defaultdict(int)
        
        for run in trace_data.get("child_runs", []):
            if run.get("run_type") == "tool":
                tool_name = run.get("name", "unknown_tool")
                tool_calls[tool_name] += 1
                if run.get("error"):
                    tool_errors[tool_name] += 1
        
        return {
            "total_tool_calls": sum(tool_calls.values()),
            "unique_tools": len(tool_calls),
            "tool_calls": dict(tool_calls),
            "tool_errors": dict(tool_errors),
            "tool_success_rate": self._calculate_tool_success_rate(tool_calls, tool_errors)
        }
    
    def _calculate_tool_success_rate(self, tool_calls: Dict[str, int], tool_errors: Dict[str, int]) -> float:
        """Calculate overall tool success rate"""
        total_calls = sum(tool_calls.values())
        total_errors = sum(tool_errors.values())
        
        if total_calls == 0:
            return 100.0
        
        return ((total_calls - total_errors) / total_calls) * 100
    
    def _generate_recommendations(self, trace_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check for errors
        errors = self._analyze_errors(trace_data)
        if errors:
            recommendations.append(f"🚨 Fix {len(errors)} errors found in the trace")
        
        # Check success rate
        success_rate = self._calculate_success_rate(trace_data)
        if success_rate < 90:
            recommendations.append(f"⚠️ Improve success rate (currently {success_rate:.1f}%)")
        
        # Check tool usage
        tool_analysis = self._analyze_tool_usage(trace_data)
        if tool_analysis["tool_success_rate"] < 95:
            recommendations.append(f"🔧 Improve tool reliability (currently {tool_analysis['tool_success_rate']:.1f}% success)")
        
        # Check performance
        if trace_data.get("total_tokens", 0) > 10000:
            recommendations.append("💡 Consider optimizing token usage")
        
        return recommendations


def format_analysis_summary(analysis: Dict[str, Any]) -> str:
    """Format analysis as a readable summary"""
    summary = analysis["summary"]
    metrics = analysis["performance_metrics"]
    errors = analysis["error_analysis"]
    tools = analysis["tool_usage"]
    recommendations = analysis["recommendations"]
    
    output = []
    output.append("\n🔍 LangSmith Trace Analysis Summary")
    output.append("=" * 50)
    output.append(f"📍 Trace ID: {analysis['trace_id']}")
    output.append(f"📅 Analysis Time: {analysis['timestamp']}")
    output.append("")
    
    # Summary section
    output.append("📊 Summary")
    output.append("-" * 30)
    output.append(f"Name: {summary['name']}")
    output.append(f"Status: {summary['status']}")
    output.append(f"Total Runs: {summary['total_runs']}")
    output.append(f"Duration: {summary['duration_seconds']:.2f}s" if summary['duration_seconds'] else "Duration: Unknown")
    output.append(f"Has Errors: {'Yes' if summary['has_errors'] else 'No'}")
    output.append("")
    
    # Performance metrics
    output.append("⚡ Performance Metrics")
    output.append("-" * 30)
    output.append(f"Success Rate: {metrics['success_rate']:.1f}%")
    output.append(f"Total Tokens: {metrics['total_tokens']:,}")
    output.append(f"Child Runs: {metrics['child_run_count']}")
    output.append("")
    
    # Tool usage
    if tools["total_tool_calls"] > 0:
        output.append("🔧 Tool Usage")
        output.append("-" * 30)
        output.append(f"Total Tool Calls: {tools['total_tool_calls']}")
        output.append(f"Unique Tools: {tools['unique_tools']}")
        output.append(f"Tool Success Rate: {tools['tool_success_rate']:.1f}%")
        output.append("")
    
    # Errors
    if errors:
        output.append("❌ Errors Found")
        output.append("-" * 30)
        for error in errors[:5]:  # Show first 5 errors
            output.append(f"- {error['run_name']}: {error['error'][:100]}...")
        if len(errors) > 5:
            output.append(f"... and {len(errors) - 5} more errors")
        output.append("")
    
    # Recommendations
    if recommendations:
        output.append("💡 Recommendations")
        output.append("-" * 30)
        for rec in recommendations:
            output.append(f"- {rec}")
        output.append("")
    
    return "\n".join(output)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze LangSmith traces for performance and quality insights"
    )
    parser.add_argument("trace_id", help="The LangSmith trace ID to analyze")
    parser.add_argument("--project", "-p", help="LangSmith project name", default="trading-agent-graph")
    parser.add_argument("--format", "-f", choices=["summary", "json", "both"], 
                       default="both", help="Output format")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize analyzer
        analyzer = TraceAnalyzer()
        
        # Fetch trace
        logger.info(f"Fetching trace {args.trace_id} from project {args.project}...")
        trace_data = analyzer.fetch_trace(args.trace_id, args.project)
        
        # Analyze trace
        logger.info("Analyzing trace...")
        analysis = analyzer.analyze_trace(trace_data)
        
        # Format output
        if args.format in ["summary", "both"]:
            summary = format_analysis_summary(analysis)
            print(summary)
        
        # Save JSON if requested
        if args.format in ["json", "both"]:
            # Generate filename
            if args.output:
                json_file = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_file = f"trace_analysis_{args.trace_id}_{timestamp}.json"
            
            # Save analysis
            with open(json_file, 'w') as f:
                json.dump({
                    "trace_data": trace_data,
                    "analysis": analysis
                }, f, indent=2)
            
            if not args.output:
                logger.info(f"Analysis saved to: {json_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())