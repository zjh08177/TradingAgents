# TradingAgents/graph/trading_graph.py

import os
import json
import signal
import asyncio
from datetime import date
from typing import Dict, Any, Tuple
import logging
from functools import wraps

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import from local agent modules
from ..utils.agent_utils import Toolkit, create_msg_delete
from ..utils.agent_states import AgentState
from ..factories.llm_factory import LLMFactory
from ..factories.memory_factory import MemoryFactory
from ..default_config import DEFAULT_CONFIG
from ..dataflows.config import get_config
from .setup import GraphSetup
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Simplified Trading Agents Graph following SOLID principles"""

    def __init__(self, config=None, selected_analysts=None):
        """Initialize with simplified configuration"""
        self.config = config or get_config()
        self.selected_analysts = selected_analysts or ["market", "social", "news", "fundamentals"]
        
        # Log optimization status
        from ..utils.optimization_logger import log_config_status
        log_config_status(self.config)

        # Create LLMs using factory with safe config access
        self.llm_factory = LLMFactory()
        self.quick_thinking_llm = self.llm_factory.create_llm(
            self.config.get("llm_provider", "openai"), 
            self.config.get("quick_thinking_model", "gpt-4o"), 
            self.config
        )
        self.deep_thinking_llm = self.llm_factory.create_llm(
            self.config.get("llm_provider", "openai"), 
            self.config.get("reasoning_model", "o3"), 
            self.config
        )

        # Initialize components 
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.config
        )
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # Build the graph
        self.graph = self.graph_setup.setup_graph(self.selected_analysts)
        
        logger.info("✅ TradingAgentsGraph initialized successfully")

    def _extract_final_signal(self, final_state: Dict[str, Any]) -> str:
        """Extract the final trading signal from state"""
        return final_state.get("final_trade_decision", "HOLD - No decision provided")

    async def propagate(self, company_name: str, date: str):
        """Run analysis through the graph with hard timeout"""
        logger.info(f"🚀 Starting analysis for {company_name} on {date}")
        
        # Get timeout from config or use default 120s
        timeout_seconds = self.config.get('execution_timeout', 120)
        logger.warning(f"⏰ HARD TIMEOUT SET: {timeout_seconds}s")
        
        try:
            # Run with timeout using asyncio
            return await asyncio.wait_for(
                self._execute_graph(company_name, date),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"🚨 EXECUTION TIMEOUT: Graph execution exceeded {timeout_seconds}s limit")
            raise TimeoutError(f"Execution exceeded {timeout_seconds}s limit")
    
    async def _execute_graph(self, company_name: str, date: str):
        """Internal method to execute the graph (separated for timeout wrapper)"""
        logger.info(f"Executing graph for {company_name} on {date}")
        
        # Create initial state (simplified inline)
        initial_state = {
            "company_of_interest": company_name,
            "trade_date": str(date),
            "market_messages": [],
            "social_messages": [],
            "news_messages": [],
            "fundamentals_messages": [],
            "market_report": "",
            "sentiment_report": "",
            "news_report": "",
            "fundamentals_report": "",
            "investment_debate_state": {
                "bull_history": "",
                "bear_history": "",
                "history": "",
                "current_response": "",
                "judge_decision": "",
                "count": 0
            },
            "risk_debate_state": {
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
            },
            "investment_plan": ""
        }
        
        try:
            # Run the graph
            config = {"recursion_limit": 50}
            final_state = await self.graph.ainvoke(initial_state, config)
            
            # Process signal
            signal = self._extract_final_signal(final_state)
            processed_signal = await self.signal_processor.process_signal(signal)
            
            # Return results
            final_state["processed_signal"] = processed_signal
            return final_state, processed_signal
            
        except Exception as e:
            logger.error(f"❌ Graph execution failed: {e}")
            raise
