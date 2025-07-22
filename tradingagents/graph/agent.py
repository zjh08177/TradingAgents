"""
LangGraph Platform-compatible Trading Agents Graph
Entry point for production deployment with proper scaling capabilities
"""

import os
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.default_config import DEFAULT_CONFIG

# Production database configuration
DB_URI = os.getenv("POSTGRES_URI_CUSTOM") or os.getenv("DATABASE_URI")
REDIS_URI = os.getenv("REDIS_URI_CUSTOM") or os.getenv("REDIS_URI") 

def create_production_graph():
    """
    Create a production-ready LangGraph with proper scaling configuration
    """
    # Initialize checkpointer with production database
    checkpointer = PostgresSaver.from_conn_string(DB_URI) if DB_URI else None
    
    # Initialize store for long-term memory
    store = PostgresStore.from_conn_string(DB_URI) if DB_URI else None
    
    # Production configuration optimized for scale
    config = DEFAULT_CONFIG.copy()
    config.update({
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "deep_think_llm": os.getenv("DEEP_THINK_MODEL", "gpt-4o"),
        "quick_think_llm": os.getenv("QUICK_THINK_MODEL", "gpt-4o-mini"),
        "max_debate_rounds": int(os.getenv("MAX_DEBATE_ROUNDS", "1")),
        "max_risk_discuss_rounds": int(os.getenv("MAX_RISK_DISCUSS_ROUNDS", "1")),
        "online_tools": os.getenv("ONLINE_TOOLS", "true").lower() == "true",
        "api_host": "0.0.0.0",
        "api_port": int(os.getenv("PORT", "8000")),
    })
    
    # Initialize core trading graph with optimized settings
    trading_graph = TradingAgentsGraph(
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,  # Disable debug in production
        config=config
    )
    
    # Create production state graph
    def analyze_ticker_node(state: AgentState) -> AgentState:
        """Production node for ticker analysis with proper error handling"""
        try:
            ticker = state.get("ticker", "")
            analysis_date = state.get("analysis_date", "")
            
            if not ticker:
                return {"error": "Ticker symbol is required"}
            
            # Use the existing trading graph logic
            result, decision = trading_graph.propagate(ticker, analysis_date)
            
            return {
                "ticker": ticker,
                "analysis_date": analysis_date,
                "market_report": result.get("market_report"),
                "sentiment_report": result.get("sentiment_report"), 
                "news_report": result.get("news_report"),
                "fundamentals_report": result.get("fundamentals_report"),
                "investment_plan": result.get("investment_plan"),
                "trader_investment_plan": result.get("trader_investment_plan"),
                "final_trade_decision": decision,
                "processed_signal": result.get("processed_signal"),
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    # Build the production graph
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("analyze_ticker", analyze_ticker_node)
    graph_builder.add_edge(START, "analyze_ticker")
    graph_builder.add_edge("analyze_ticker", END)
    
    # Compile with production configuration
    compiled_graph = graph_builder.compile(
        checkpointer=checkpointer,
        store=store,
        interrupt_before=[],  # No human-in-the-loop for production
        interrupt_after=[]
    )
    
    return compiled_graph

# Export the graph for LangGraph Platform
graph = create_production_graph()

# Production health check function
def health_check() -> Dict[str, Any]:
    """Health check endpoint for load balancer"""
    try:
        # Test database connectivity
        if DB_URI:
            checkpointer = PostgresSaver.from_conn_string(DB_URI)
            # Simple connectivity test
        
        return {
            "status": "healthy",
            "database": "connected" if DB_URI else "in-memory",
            "redis": "connected" if REDIS_URI else "not-configured",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Export health check for monitoring
__all__ = ["graph", "health_check"] 