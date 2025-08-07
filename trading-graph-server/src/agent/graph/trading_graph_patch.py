# Patch for trading_graph.py - Add recursion limit configuration
# Apply this patch to fix GraphRecursionError

# In the propagate method, update the graph execution config:

async def propagate(self, company_name: str, date: str):
    """Run analysis through the graph with hard timeout"""
    logger.info(f"🚀 Starting analysis for {company_name} on {date}")
    
    # Get timeout from config or use default 1200s (20 minutes)
    timeout_seconds = self.config.get('execution_timeout', 1200)
    logger.warning(f"⏰ HARD TIMEOUT SET: {timeout_seconds}s ({timeout_seconds/60:.1f} minutes)")
    
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
        "trace_id": f"trace_{company_name}_{date}_{time.time()}",  # Add trace ID for circuit breaker
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
        "investment_plan": "",
        # Add research debate state with max rounds
        "research_debate_state": {
            "current_round": 1,
            "max_rounds": self.config.get('max_research_debate_rounds', 3),
            "consensus_reached": False,
            "judge_feedback": "",
            "debate_history": []
        }
    }
    
    try:
        # CRITICAL FIX: Increase recursion limit
        recursion_limit = self.config.get('recursion_limit', 50)  # Increase from default 25
        config = {"recursion_limit": recursion_limit}
        
        logger.info(f"📊 Graph config: recursion_limit={recursion_limit}")
        
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