#!/usr/bin/env python3
"""
Enhanced Verification Logging for Trading Graph Agents
Provides comprehensive tool call verification, data parsing validation, and analyst completion tracking.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import functools

# Create specialized verification logger
verification_logger = logging.getLogger('verification_tracker')
verification_logger.setLevel(logging.INFO)

# Console handler for verification logs
if not verification_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - VERIFY - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    verification_logger.addHandler(console_handler)

class ToolCallTracker:
    """Tracks tool call execution and validation across all analysts."""
    
    def __init__(self):
        self.tool_calls = {}
        self.analyst_metrics = {}
        self.session_start = time.time()
    
    def log_tool_call_start(self, analyst: str, tool_name: str, tool_id: str, args: Dict[str, Any]):
        """Log the initiation of a tool call."""
        call_info = {
            'analyst': analyst,
            'tool_name': tool_name,
            'tool_id': tool_id,
            'args': args,
            'start_time': time.time(),
            'status': 'started',
            'execution_time': None,
            'response_size': None,
            'data_quality': None,
            'error': None
        }
        
        self.tool_calls[tool_id] = call_info
        
        verification_logger.info(f"🔧 TOOL START - {analyst}: {tool_name}")
        verification_logger.info(f"   📋 Tool ID: {tool_id}")
        verification_logger.info(f"   📤 Args: {json.dumps(args, default=str)[:200]}...")
        
        # Update analyst metrics
        if analyst not in self.analyst_metrics:
            self.analyst_metrics[analyst] = {
                'tools_started': 0,
                'tools_completed': 0,
                'tools_failed': 0,
                'total_execution_time': 0,
                'status': 'pending'
            }
        
        self.analyst_metrics[analyst]['tools_started'] += 1
    
    def log_tool_call_success(self, tool_id: str, response: Any, execution_time: float):
        """Log successful tool call completion with response validation."""
        if tool_id not in self.tool_calls:
            verification_logger.warning(f"⚠️ Tool ID {tool_id} not found in tracker")
            return
        
        call_info = self.tool_calls[tool_id]
        call_info['status'] = 'completed'
        call_info['execution_time'] = execution_time
        
        # Analyze response quality
        response_analysis = self._analyze_response_quality(response)
        call_info['response_size'] = response_analysis['size']
        call_info['data_quality'] = response_analysis['quality']
        
        analyst = call_info['analyst']
        tool_name = call_info['tool_name']
        
        verification_logger.info(f"✅ TOOL SUCCESS - {analyst}: {tool_name}")
        verification_logger.info(f"   ⏱️ Execution: {execution_time:.3f}s")
        verification_logger.info(f"   📊 Response Size: {response_analysis['size']} chars")
        verification_logger.info(f"   🎯 Data Quality: {response_analysis['quality']}")
        
        # Log data structure validation
        if response_analysis['structure_valid']:
            verification_logger.info(f"   ✅ Data Structure: Valid")
        else:
            verification_logger.warning(f"   ⚠️ Data Structure: Issues detected - {response_analysis['structure_issues']}")
        
        # Update analyst metrics
        self.analyst_metrics[analyst]['tools_completed'] += 1
        self.analyst_metrics[analyst]['total_execution_time'] += execution_time
    
    def log_tool_call_failure(self, tool_id: str, error: str, execution_time: float):
        """Log failed tool call with error details."""
        if tool_id not in self.tool_calls:
            verification_logger.warning(f"⚠️ Tool ID {tool_id} not found in tracker")
            return
        
        call_info = self.tool_calls[tool_id]
        call_info['status'] = 'failed'
        call_info['execution_time'] = execution_time
        call_info['error'] = error
        
        analyst = call_info['analyst']
        tool_name = call_info['tool_name']
        
        verification_logger.error(f"❌ TOOL FAILED - {analyst}: {tool_name}")
        verification_logger.error(f"   ⏱️ Execution: {execution_time:.3f}s")
        verification_logger.error(f"   💥 Error: {error}")
        
        # Update analyst metrics
        self.analyst_metrics[analyst]['tools_failed'] += 1
    
    def log_analyst_completion(self, analyst: str, status: str, total_time: float, report_length: int):
        """Log analyst completion with comprehensive metrics."""
        if analyst in self.analyst_metrics:
            self.analyst_metrics[analyst]['status'] = status
            self.analyst_metrics[analyst]['analyst_total_time'] = total_time
            self.analyst_metrics[analyst]['report_length'] = report_length
        
        metrics = self.analyst_metrics.get(analyst, {})
        tools_started = metrics.get('tools_started', 0)
        tools_completed = metrics.get('tools_completed', 0)
        tools_failed = metrics.get('tools_failed', 0)
        
        success_rate = (tools_completed / tools_started * 100) if tools_started > 0 else 0
        
        verification_logger.info(f"🏁 ANALYST COMPLETE - {analyst}")
        verification_logger.info(f"   📊 Status: {status}")
        verification_logger.info(f"   ⏱️ Total Time: {total_time:.3f}s")
        verification_logger.info(f"   📝 Report Length: {report_length} chars")
        verification_logger.info(f"   🔧 Tools: {tools_completed}/{tools_started} completed ({success_rate:.1f}% success)")
        
        if tools_failed > 0:
            verification_logger.warning(f"   ⚠️ Failed Tools: {tools_failed}")
    
    def _analyze_response_quality(self, response: Any) -> Dict[str, Any]:
        """Analyze response quality and data structure."""
        analysis = {
            'size': 0,
            'quality': 'unknown',
            'structure_valid': True,
            'structure_issues': []
        }
        
        try:
            # Convert response to string for size analysis
            if isinstance(response, dict):
                response_str = json.dumps(response, default=str)
                analysis['size'] = len(response_str)
                
                # Check for common data quality issues
                if not response or response == {}:
                    analysis['quality'] = 'empty'
                    analysis['structure_valid'] = False
                    analysis['structure_issues'].append('Empty response')
                elif 'error' in response:
                    analysis['quality'] = 'error'
                    analysis['structure_valid'] = False
                    analysis['structure_issues'].append('Contains error field')
                elif len(response_str) < 50:
                    analysis['quality'] = 'minimal'
                    analysis['structure_issues'].append('Very short response')
                else:
                    analysis['quality'] = 'good'
            
            elif isinstance(response, str):
                analysis['size'] = len(response)
                if not response or response.strip() == '':
                    analysis['quality'] = 'empty'
                    analysis['structure_valid'] = False
                    analysis['structure_issues'].append('Empty string')
                elif len(response) < 50:
                    analysis['quality'] = 'minimal'
                elif 'error' in response.lower() or 'failed' in response.lower():
                    analysis['quality'] = 'error_indication'
                    analysis['structure_issues'].append('Contains error keywords')
                else:
                    analysis['quality'] = 'good'
            
            elif isinstance(response, list):
                analysis['size'] = len(response)
                if not response:
                    analysis['quality'] = 'empty'
                    analysis['structure_valid'] = False
                    analysis['structure_issues'].append('Empty list')
                else:
                    analysis['quality'] = 'good'
            
            else:
                analysis['size'] = len(str(response))
                analysis['quality'] = 'basic'
        
        except Exception as e:
            analysis['quality'] = 'analysis_error'
            analysis['structure_valid'] = False
            analysis['structure_issues'].append(f'Analysis failed: {str(e)}')
        
        return analysis
    
    def generate_session_report(self) -> Dict[str, Any]:
        """Generate comprehensive session verification report."""
        session_time = time.time() - self.session_start
        
        total_tools = len(self.tool_calls)
        completed_tools = sum(1 for call in self.tool_calls.values() if call['status'] == 'completed')
        failed_tools = sum(1 for call in self.tool_calls.values() if call['status'] == 'failed')
        
        report = {
            'session_duration': session_time,
            'timestamp': datetime.now().isoformat(),
            'total_tool_calls': total_tools,
            'completed_tool_calls': completed_tools,
            'failed_tool_calls': failed_tools,
            'overall_success_rate': (completed_tools / total_tools * 100) if total_tools > 0 else 0,
            'analysts': self.analyst_metrics,
            'tool_calls_detail': self.tool_calls
        }
        
        verification_logger.info(f"📋 SESSION REPORT GENERATED")
        verification_logger.info(f"   ⏱️ Duration: {session_time:.1f}s")
        verification_logger.info(f"   🔧 Tools: {completed_tools}/{total_tools} successful")
        verification_logger.info(f"   👥 Analysts: {len(self.analyst_metrics)}")
        
        return report

# Global tracker instance
global_tracker = ToolCallTracker()

def track_tool_calls(analyst_name: str):
    """Decorator to track tool calls for verification."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract tool call info if available
            if len(args) > 0 and isinstance(args[0], dict):
                tool_call = args[0]
                tool_name = tool_call.get('name', func.__name__)
                tool_id = tool_call.get('id', f"{func.__name__}_{int(time.time() * 1000)}")
                tool_args = tool_call.get('args', {})
                
                # Log tool start
                global_tracker.log_tool_call_start(analyst_name, tool_name, tool_id, tool_args)
                
                start_time = time.time()
                try:
                    # Execute the function
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Log success
                    global_tracker.log_tool_call_success(tool_id, result, execution_time)
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    # Log failure
                    global_tracker.log_tool_call_failure(tool_id, str(e), execution_time)
                    raise
            else:
                # No tool call info available, execute normally
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def verify_analyst_completion(analyst_name: str, status: str, total_time: float, report: str):
    """Public function to log analyst completion."""
    report_length = len(report) if report else 0
    global_tracker.log_analyst_completion(analyst_name, status, total_time, report_length)

def get_session_report() -> Dict[str, Any]:
    """Get the current session verification report."""
    return global_tracker.generate_session_report()

def log_verification_summary():
    """Log a summary of verification results."""
    report = global_tracker.generate_session_report()
    
    verification_logger.info("="*60)
    verification_logger.info("🎯 VERIFICATION SUMMARY")
    verification_logger.info("="*60)
    
    for analyst, metrics in report['analysts'].items():
        verification_logger.info(f"👤 {analyst.upper()}:")
        verification_logger.info(f"   Status: {metrics.get('status', 'unknown')}")
        verification_logger.info(f"   Tools: {metrics.get('tools_completed', 0)}/{metrics.get('tools_started', 0)}")
        verification_logger.info(f"   Time: {metrics.get('analyst_total_time', 0):.2f}s")
        
        if metrics.get('tools_failed', 0) > 0:
            verification_logger.warning(f"   ⚠️ Failures: {metrics['tools_failed']}")
    
    verification_logger.info(f"🎯 Overall Success Rate: {report['overall_success_rate']:.1f}%")
    verification_logger.info("="*60)