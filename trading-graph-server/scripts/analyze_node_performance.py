#!/usr/bin/env python3
"""Analyze node performance from trace data"""
import json
from datetime import datetime
from collections import defaultdict

def get_all_runs(runs_list):
    """Recursively get all runs including nested child runs"""
    all_runs = []
    for run in runs_list:
        all_runs.append(run)
        if 'child_runs' in run and run['child_runs']:
            all_runs.extend(get_all_runs(run['child_runs']))
    return all_runs

def analyze_node_performance(trace_file):
    """Analyze execution times for each node"""
    with open(trace_file, 'r') as f:
        data = json.load(f)
    
    nodes = []
    
    # Handle the structure of the trace data
    runs = []
    if 'trace_data' in data:
        # Get main run
        main_run = data['trace_data']
        if main_run.get('name') and main_run.get('start_time') and main_run.get('end_time'):
            runs.append(main_run)
        # Get child runs recursively
        if 'child_runs' in main_run:
            runs.extend(get_all_runs(main_run['child_runs']))
    
    for run in runs:
        if run.get('name') and run.get('start_time') and run.get('end_time'):
            start = datetime.fromisoformat(run['start_time'])
            end = datetime.fromisoformat(run['end_time'])
            duration = (end - start).total_seconds()
            
            nodes.append({
                'name': run['name'],
                'duration': duration,
                'tokens': run.get('total_tokens', 0),
                'start': run['start_time'],
                'end': run['end_time']
            })
    
    # Sort by duration
    nodes.sort(key=lambda x: x['duration'], reverse=True)
    
    print("=== NODE PERFORMANCE ANALYSIS ===")
    print(f"{'Node Name':<30} {'Duration (s)':<12} {'Tokens':<10}")
    print("-" * 55)
    
    total_duration = 0
    for node in nodes[:20]:  # Top 20 slowest nodes
        print(f"{node['name']:<30} {node['duration']:<12.2f} {node['tokens']:<10}")
        total_duration += node['duration']
    
    # Identify parallelizable operations
    print("\n=== PARALLELIZATION OPPORTUNITIES ===")
    
    # Check analysts
    analysts = ['market_analyst', 'sentiment_analyst', 'news_analyst', 'fundamentals_analyst']
    analyst_times = {}
    for node in nodes:
        if node['name'] in analysts:
            analyst_times[node['name']] = node
    
    if len(analyst_times) > 1:
        print("\n1. ANALYSTS (Currently Parallel):")
        for name, data in analyst_times.items():
            print(f"   - {name}: {data['duration']:.2f}s")
    
    # Check risk debators
    debators = ['aggressive_debator', 'conservative_debator', 'neutral_debator']
    debator_times = {}
    for node in nodes:
        if node['name'] in debators:
            debator_times[node['name']] = node
    
    if len(debator_times) > 1:
        print("\n2. RISK DEBATORS (Currently Sequential):")
        total_sequential = 0
        for name, data in debator_times.items():
            print(f"   - {name}: {data['duration']:.2f}s")
            total_sequential += data['duration']
        print(f"   Total Sequential Time: {total_sequential:.2f}s")
        print(f"   Potential Parallel Time: {max(d['duration'] for d in debator_times.values()):.2f}s")
        print(f"   Time Savings: {total_sequential - max(d['duration'] for d in debator_times.values()):.2f}s")
    
    # Check tool calls
    tool_nodes = [n for n in nodes if '_tools' in n['name']]
    if tool_nodes:
        print("\n3. TOOL EXECUTION NODES:")
        for node in tool_nodes:
            print(f"   - {node['name']}: {node['duration']:.2f}s")

if __name__ == "__main__":
    trace_file = "/Users/bytedance/Documents/TradingAgents/trading-graph-server/scripts/trace_analysis_reports/trace_analysis_1f06d966-092a-6f94-9919-e5b10b235a0d_20250730_160925.json"
    analyze_node_performance(trace_file)