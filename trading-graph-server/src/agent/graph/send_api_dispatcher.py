#!/usr/bin/env python3
"""
Send API Dispatcher and Routing Functions
Implements LangGraph 0.6.2 Send API for true parallel analyst execution
"""

import time
import logging
from typing import List
from langgraph.graph._branch import Send

from ..utils.enhanced_agent_states import EnhancedAnalystState

logger = logging.getLogger(__name__)

async def create_dispatcher_node() -> callable:
    """
    Create dispatcher node that prepares state for parallel execution
    This node runs before the routing function and sets up timing/state
    """
    
    async def dispatcher_node(state: EnhancedAnalystState) -> EnhancedAnalystState:
        """Dispatcher node that prepares state and marks parallel execution start"""
        logger.info("🚀 DISPATCHER: Preparing for parallel analyst execution")
        
        # Record start time for performance tracking
        start_time = time.time()
        
        # Initialize analyst status tracking
        state_update = {
            "parallel_start_time": start_time,
            "send_api_enabled": True,
            "step": "parallel_dispatch",
            
            # Initialize all analyst statuses
            "market_analyst_status": "pending",
            "news_analyst_status": "pending", 
            "social_analyst_status": "pending",
            "fundamentals_analyst_status": "pending",
            
            # Initialize metrics tracking
            "analyst_execution_times": {},
            "analyst_errors": {},
            "failed_analysts": [],
            
            # Reset aggregation status
            "aggregation_status": "pending",
            "aggregation_ready": False,
            "successful_analysts_count": 0
        }
        
        logger.info("✅ DISPATCHER: State prepared for parallel execution")
        return state_update
    
    return dispatcher_node

def create_routing_function(selected_analysts: List[str] = None) -> callable:
    """
    Create routing function that uses Send API to dispatch to parallel analysts
    This is the key function that enables true parallel execution
    
    Args:
        selected_analysts: List of analyst types to enable (default: all 4)
    
    Returns:
        Routing function that returns List[Send] for conditional edges
    """
    
    if selected_analysts is None:
        selected_analysts = ["market", "news", "social", "fundamentals"]
    
    def dispatch_to_analysts(state: EnhancedAnalystState) -> List[Send]:
        """
        Route to all analysts in parallel using Send API
        
        This function is called by LangGraph's conditional_edges and must return
        a List[Send] objects to trigger parallel execution
        """
        logger.info(f"🎯 ROUTING: Dispatching to {len(selected_analysts)} analysts in parallel")
        
        # Create Send objects for each selected analyst
        send_objects = []
        
        for analyst_type in selected_analysts:
            analyst_node_name = f"{analyst_type}_analyst"
            logger.info(f"📤 ROUTING: Sending to {analyst_node_name}")
            
            # Create Send object with node name and current state
            send_obj = Send(analyst_node_name, state)
            send_objects.append(send_obj)
        
        logger.info(f"✅ ROUTING: Created {len(send_objects)} Send objects for parallel execution")
        return send_objects
    
    return dispatch_to_analysts

async def create_robust_aggregator() -> callable:
    """
    Create enhanced aggregator with comprehensive error handling and validation
    Collects results from all parallel analysts and validates quality
    """
    
    async def robust_aggregator_node(state: EnhancedAnalystState) -> EnhancedAnalystState:
        """Enhanced aggregator with error handling and quality validation"""
        logger.info("📊 ROBUST AGGREGATOR: Collecting parallel analyst results")
        
        # Record end time for performance tracking
        end_time = time.time()
        start_time = state.get("parallel_start_time", end_time)
        total_parallel_time = end_time - start_time
        
        # Analyze results from each analyst
        reports = {}
        errors = {}
        successful_analysts = 0
        total_tool_calls = 0
        
        # Check each analyst type
        analyst_mappings = {
            "market": "market_report",
            "news": "news_report", 
            "social": "sentiment_report",  # Note: social uses sentiment_report key
            "fundamentals": "fundamentals_report"
        }
        
        for analyst_name, report_key in analyst_mappings.items():
            status_key = f"{analyst_name}_analyst_status"
            error_key = f"{analyst_name}_error"
            tool_calls_key = f"{analyst_name}_tool_calls"
            
            # Check analyst status
            status = state.get(status_key, "unknown")
            report = state.get(report_key, "")
            tool_calls = state.get(tool_calls_key, 0)
            
            total_tool_calls += tool_calls or 0
            
            # Check for errors in the analyst_errors dict
            analyst_errors = state.get("analyst_errors", {})
            if analyst_name in analyst_errors:
                errors[analyst_name] = analyst_errors[analyst_name]
                logger.warning(f"⚠️ AGGREGATOR: {analyst_name} analyst had errors: {analyst_errors[analyst_name]}")
                continue
            
            # Validate report quality
            if report and len(report.strip()) > 50:
                # Check for error indicators in the report content
                error_phrases = [
                    "unable to retrieve", "technical issues", "unavailable",
                    "error", "failed", "no data", "analysis failed"
                ]
                
                if not any(error_phrase in report.lower() for error_phrase in error_phrases):
                    reports[analyst_name] = report
                    successful_analysts += 1
                    logger.info(f"✅ AGGREGATOR: {analyst_name} analyst - valid report ({len(report)} chars)")
                else:
                    errors[analyst_name] = "Report contains error indicators"
                    logger.warning(f"⚠️ AGGREGATOR: {analyst_name} analyst - report contains errors")
            else:
                error_msg = f"Report too short ({len(report)} chars)" if report else "No report generated"
                errors[analyst_name] = error_msg
                logger.warning(f"⚠️ AGGREGATOR: {analyst_name} analyst - {error_msg}")
        
        # Calculate performance metrics
        execution_times = state.get("analyst_execution_times", {})
        speedup_factor = 1.0
        
        if execution_times:
            total_sequential_time = sum(execution_times.values())
            max_parallel_time = max(execution_times.values())
            speedup_factor = total_sequential_time / max_parallel_time if max_parallel_time > 0 else 1.0
        
        # Determine aggregation status
        if successful_analysts >= 3:
            aggregation_status = "success"
            aggregation_ready = True
            logger.info(f"✅ AGGREGATOR: SUCCESS - {successful_analysts}/4 analysts completed successfully")
        elif successful_analysts >= 2:
            aggregation_status = "partial_success"
            aggregation_ready = True
            logger.warning(f"⚠️ AGGREGATOR: PARTIAL SUCCESS - {successful_analysts}/4 analysts completed")
        elif successful_analysts == 1:
            aggregation_status = "minimal_success"
            aggregation_ready = True
            logger.warning(f"⚠️ AGGREGATOR: MINIMAL SUCCESS - only {successful_analysts}/4 analysts completed")
        else:
            aggregation_status = "complete_failure"
            aggregation_ready = False
            logger.error(f"🚨 AGGREGATOR: COMPLETE FAILURE - {successful_analysts}/4 analysts completed")
        
        # Prepare state update
        state_update = {
            "parallel_end_time": end_time,
            "total_parallel_time": total_parallel_time,
            "aggregation_status": aggregation_status,
            "aggregation_ready": aggregation_ready,
            "successful_analysts_count": successful_analysts,
            "speedup_factor": speedup_factor,
            "step": "aggregation_complete",
            
            # Performance metrics
            "parallel_execution_metrics": {
                "total_time": total_parallel_time,
                "successful_analysts": successful_analysts,
                "total_tool_calls": total_tool_calls,
                "speedup_factor": speedup_factor,
                "individual_times": execution_times
            }
        }
        
        # Add error tracking if any failures occurred
        if errors:
            state_update["failed_analysts"] = list(errors.keys())
            logger.warning(f"⚠️ AGGREGATOR: Failed analysts: {list(errors.keys())}")
        
        # Legacy compatibility flags
        if successful_analysts < 2:
            state_update["low_quality_reports"] = True
            state_update["empty_reports"] = list(errors.keys())
        
        # Initialize debate states if needed (for downstream compatibility)
        if "investment_debate_state" not in state:
            state_update["investment_debate_state"] = {
                "bull_history": "",
                "bear_history": "",
                "history": "",
                "current_response": "",
                "judge_decision": "",
                "count": 0
            }
        
        if "risk_debate_state" not in state:
            state_update["risk_debate_state"] = {
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "history": "",
                "latest_speaker": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
                "count": 0
            }
        
        # Log final performance metrics
        logger.info(f"⚡ AGGREGATOR METRICS:")
        logger.info(f"   Total parallel time: {total_parallel_time:.2f}s")
        logger.info(f"   Speedup factor: {speedup_factor:.2f}x")
        logger.info(f"   Successful analysts: {successful_analysts}/4")
        logger.info(f"   Total tool calls: {total_tool_calls}")
        
        if execution_times:
            logger.info(f"   Individual times: {execution_times}")
        
        logger.info("📊 ROBUST AGGREGATOR: ✅ Collection and validation complete")
        return state_update
    
    return robust_aggregator_node

class FallbackExecutionManager:
    """Manages fallback to sequential execution if parallel fails"""
    
    @staticmethod
    async def execute_with_fallback(state: EnhancedAnalystState, parallel_executor: callable, sequential_executor: callable) -> EnhancedAnalystState:
        """Try parallel execution, fallback to sequential if needed"""
        try:
            # Attempt parallel execution
            logger.info("🚀 FALLBACK MANAGER: Attempting parallel execution")
            result = await parallel_executor(state)
            
            # Validate result quality
            if FallbackExecutionManager.is_result_acceptable(result):
                logger.info("✅ FALLBACK MANAGER: Parallel execution successful")
                return result
            else:
                logger.warning("⚠️ FALLBACK MANAGER: Parallel execution produced low quality results, falling back")
                return await sequential_executor(state)
                
        except Exception as e:
            logger.error(f"❌ FALLBACK MANAGER: Parallel execution failed: {e}, falling back to sequential")
            return await sequential_executor(state)
    
    @staticmethod
    def is_result_acceptable(result: EnhancedAnalystState) -> bool:
        """Check if parallel execution result is acceptable"""
        successful_count = result.get("successful_analysts_count", 0)
        aggregation_status = result.get("aggregation_status", "pending")
        
        # Accept if at least 2 analysts succeeded and status is not complete failure
        return successful_count >= 2 and aggregation_status != "complete_failure"

class LangGraphVersionManager:
    """Manage LangGraph version compatibility"""
    
    @staticmethod
    def check_send_api_compatibility() -> bool:
        """Verify Send API is available"""
        try:
            from langgraph.graph._branch import Send
            return True
        except ImportError:
            logger.error("❌ Send API not available - LangGraph version too old")
            return False
    
    @staticmethod 
    def get_implementation_strategy() -> str:
        """Choose implementation based on available features"""
        if LangGraphVersionManager.check_send_api_compatibility():
            logger.info("✅ Send API available - using parallel Send implementation")
            return "send_api_parallel"
        else:
            logger.warning("⚠️ Send API not available - falling back to asyncio.gather implementation")
            return "asyncio_gather_fallback"