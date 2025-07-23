#!/usr/bin/env python3
"""
Parse debug logs to extract tool call counts per agent and execution times.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path


def parse_execution_time(log_content):
    """Extract execution time from log content."""
    # Pattern: Script completed in Xs (under 720s timeout)
    pattern = r"Script completed in (\d+)s \(under (\d+)s timeout\)"
    match = re.search(pattern, log_content)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def parse_tool_calls(log_content):
    """Extract tool call counts per agent from log content."""
    tool_calls = {}
    
    # Pattern for tool calls (common patterns in LangGraph)
    patterns = [
        # Pattern: Agent X calling tool Y
        r"(\w+_(?:analyst|researcher|manager|debator|trader))\s*.*calling tool\s*(\w+)",
        # Pattern: Tool call from agent X
        r"Tool call from\s*(\w+_(?:analyst|researcher|manager|debator|trader))",
        # Pattern: [AGENT_NAME] Tool: TOOL_NAME
        r"\[(\w+_(?:analyst|researcher|manager|debator|trader))\]\s*Tool:\s*(\w+)",
        # Pattern: Agent=AGENT_NAME tool=TOOL_NAME
        r"[Aa]gent=(\w+_(?:analyst|researcher|manager|debator|trader))\s*tool=(\w+)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, log_content, re.IGNORECASE)
        for match in matches:
            agent = match[0] if isinstance(match, tuple) else match
            agent = agent.lower()
            tool_calls[agent] = tool_calls.get(agent, 0) + 1
    
    # Also check for node execution patterns
    node_pattern = r"Executing node:\s*(\w+_(?:analyst|researcher|manager|debator|trader))"
    node_matches = re.findall(node_pattern, log_content, re.IGNORECASE)
    for agent in node_matches:
        agent = agent.lower()
        # Count node executions as potential tool calls
        tool_calls[agent] = tool_calls.get(agent, 0) + 1
    
    return tool_calls


def find_most_recent_successful_log(log_dir, max_execution_time=720):
    """Find the most recent successful debug log with execution time < max_execution_time."""
    log_files = []
    
    for file in Path(log_dir).glob("debug_session_*.log"):
        try:
            # Read the log file
            with open(file, 'r') as f:
                content = f.read()
            
            # Check execution time
            exec_time, timeout = parse_execution_time(content)
            if exec_time is None:
                continue
                
            if exec_time >= max_execution_time:
                continue
            
            # Check if it's a successful run (no critical errors)
            if "Debug session completed successfully" in content:
                is_successful = True
            elif "Debug session completed with errors detected" in content:
                # For now, accept runs with non-critical errors
                is_successful = True
            else:
                is_successful = False
            
            if is_successful:
                log_files.append({
                    'file': file,
                    'timestamp': file.stat().st_mtime,
                    'execution_time': exec_time,
                    'content': content
                })
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue
    
    # Sort by timestamp and return the most recent
    if log_files:
        log_files.sort(key=lambda x: x['timestamp'], reverse=True)
        return log_files[0]
    
    return None


def main():
    """Main function to parse logs and determine MAX_TOOL_CALLS."""
    log_dir = Path(__file__).parent / "debug_logs"
    
    print("🔍 Parsing debug logs for tool call analysis...")
    print(f"📂 Log directory: {log_dir}")
    
    # Find most recent successful log
    log_info = find_most_recent_successful_log(log_dir, max_execution_time=720)
    
    if not log_info:
        print("❌ No successful debug logs found with execution time < 720s")
        return
    
    print(f"\n✅ Found successful log: {log_info['file'].name}")
    print(f"   Execution time: {log_info['execution_time']}s")
    
    # Parse tool calls
    tool_calls = parse_tool_calls(log_info['content'])
    
    if not tool_calls:
        print("\n⚠️  No tool calls found in log (might be a setup-only run)")
        print("   Setting default MAX_TOOL_CALLS = 20")
        max_tool_calls = 20
    else:
        print("\n📊 Tool call counts per agent:")
        for agent, count in sorted(tool_calls.items(), key=lambda x: x[1], reverse=True):
            print(f"   {agent}: {count}")
        
        max_tool_calls = max(tool_calls.values())
        print(f"\n🎯 Highest tool call count: {max_tool_calls}")
    
    # Save results to a file
    results = {
        'log_file': str(log_info['file'].name),
        'execution_time': log_info['execution_time'],
        'tool_calls': tool_calls,
        'max_tool_calls': max_tool_calls,
        'parsed_at': datetime.now().isoformat()
    }
    
    output_file = Path(__file__).parent / "tool_call_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"\n📋 Recommended MAX_TOOL_CALLS setting: {max_tool_calls}")
    
    # Update or create a config file with MAX_TOOL_CALLS
    config_file = Path(__file__).parent / "debug_config.env"
    with open(config_file, 'w') as f:
        f.write(f"# Auto-generated debug configuration\n")
        f.write(f"# Generated at: {datetime.now().isoformat()}\n")
        f.write(f"# Based on log: {log_info['file'].name}\n")
        f.write(f"MAX_TOOL_CALLS={max_tool_calls}\n")
    
    print(f"📝 Configuration saved to: {config_file}")


if __name__ == "__main__":
    main()