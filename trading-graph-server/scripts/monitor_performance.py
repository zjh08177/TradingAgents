#!/usr/bin/env python3
"""
Performance Monitoring Script for Trading Agent Graph
Tracks execution times, token usage, and performance metrics across multiple runs
"""

import json
import os
import statistics
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

def load_trace_analysis(file_path: str) -> Dict[str, Any]:
    """Load a trace analysis JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_metrics(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics from trace analysis"""
    return {
        'trace_id': analysis['metadata']['trace_id'],
        'timestamp': analysis['metadata']['analysis_timestamp'],
        'duration': analysis['analysis']['summary']['duration_seconds'],
        'total_tokens': analysis['analysis']['performance_metrics']['total_tokens'],
        'token_throughput': analysis['analysis']['token_analysis']['tokens_per_second'],
        'success_rate': analysis['analysis']['performance_metrics']['success_rate'],
        'quality_grade': analysis['analysis']['quality_metrics']['quality_grade'],
        'avg_chain_time': analysis['analysis']['performance_metrics']['avg_run_duration'],
        'runtime_vs_target': analysis['analysis']['token_analysis']['target_comparison']['runtime_vs_target']
    }

def analyze_performance_trends(reports_dir: str = "trace_analysis_reports") -> None:
    """Analyze performance trends across all trace reports"""
    
    # Find all trace analysis files
    report_files = list(Path(reports_dir).glob("trace_analysis_optimized_*.json"))
    
    if not report_files:
        print("No trace analysis reports found.")
        return
    
    # Load and extract metrics
    metrics = []
    for file_path in sorted(report_files, key=lambda x: x.stat().st_mtime):
        try:
            analysis = load_trace_analysis(str(file_path))
            metric = extract_metrics(analysis)
            metrics.append(metric)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    if not metrics:
        print("No valid metrics extracted.")
        return
    
    # Sort by timestamp
    metrics.sort(key=lambda x: x['timestamp'])
    
    # Calculate statistics
    durations = [m['duration'] for m in metrics]
    tokens = [m['total_tokens'] for m in metrics]
    throughputs = [m['token_throughput'] for m in metrics]
    
    print("🔍 Performance Analysis Report")
    print("=" * 80)
    print(f"📊 Analyzed {len(metrics)} traces")
    print()
    
    # Duration statistics
    print("⏱️  Execution Time Statistics:")
    print(f"  - Average: {statistics.mean(durations):.2f}s")
    print(f"  - Median: {statistics.median(durations):.2f}s")
    print(f"  - Min: {min(durations):.2f}s")
    print(f"  - Max: {max(durations):.2f}s")
    if len(durations) > 1:
        print(f"  - Std Dev: {statistics.stdev(durations):.2f}s")
    print(f"  - Target: 120s")
    print()
    
    # Token statistics
    print("🎯 Token Usage Statistics:")
    print(f"  - Average: {statistics.mean(tokens):,.0f}")
    print(f"  - Min: {min(tokens):,}")
    print(f"  - Max: {max(tokens):,}")
    print(f"  - Target: 40,000")
    print()
    
    # Performance trend
    print("📈 Performance Trend (Last 5 runs):")
    for metric in metrics[-5:]:
        timestamp = datetime.fromisoformat(metric['timestamp']).strftime("%Y-%m-%d %H:%M")
        duration = metric['duration']
        vs_target = metric['runtime_vs_target']
        grade = metric['quality_grade']
        print(f"  {timestamp}: {duration:6.1f}s ({vs_target:5.1f}% of target) - Grade: {grade}")
    
    # Identify performance regression
    if len(durations) >= 2:
        latest_duration = durations[-1]
        previous_duration = durations[-2]
        change = (latest_duration - previous_duration) / previous_duration * 100
        
        print()
        print("🔄 Latest Performance Change:")
        if change > 10:
            print(f"  ⚠️  Performance REGRESSION: {change:.1f}% slower")
        elif change < -10:
            print(f"  ✅ Performance IMPROVEMENT: {abs(change):.1f}% faster")
        else:
            print(f"  ➡️  Performance STABLE: {change:+.1f}% change")
    
    # Recommendations
    print()
    print("💡 Recommendations:")
    avg_duration = statistics.mean(durations)
    if avg_duration > 120:
        over_target = (avg_duration - 120) / 120 * 100
        print(f"  - Average runtime is {over_target:.1f}% over target")
        print("  - Consider implementing additional optimizations:")
        print("    • Install aiohttp for connection pooling")
        print("    • Optimize prompts to reduce token usage")
        print("    • Implement more aggressive caching")
        print("    • Profile slow operations with detailed timing logs")
    else:
        print("  ✅ Performance target achieved!")

if __name__ == "__main__":
    analyze_performance_trends()