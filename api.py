from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import trading agents
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create FastAPI app
app = FastAPI(
    title="TradingAgents API",
    description="API for TradingAgents financial analysis",
    version="1.0.0"
)

# Add CORS middleware for Swift app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Swift app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class AnalysisRequest(BaseModel):
    ticker: str

# Response model
class AnalysisResponse(BaseModel):
    ticker: str
    analysis_date: str
    market_report: Optional[str] = None
    sentiment_report: Optional[str] = None
    news_report: Optional[str] = None
    fundamentals_report: Optional[str] = None
    investment_plan: Optional[str] = None
    trader_investment_plan: Optional[str] = None
    final_trade_decision: Optional[str] = None
    processed_signal: Optional[str] = None
    error: Optional[str] = None

# Simple configuration
def get_config():
    config = DEFAULT_CONFIG.copy()
    config.update({
        "llm_provider": "openai",
        "deep_think_llm": os.getenv("DEEP_THINK_MODEL", "o3"),
        "quick_think_llm": os.getenv("QUICK_THINK_MODEL", "gpt-4o"),
        "backend_url": os.getenv("BACKEND_URL", "https://api.openai.com/v1"),
        "max_debate_rounds": 5,
        "max_risk_discuss_rounds": 3,
        "online_tools": True,
    })
    return config

@app.get("/")
async def root():
    return {"message": "TradingAgents API is running"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_ticker(request: AnalysisRequest):
    """Analyze a stock ticker and return trading recommendations"""
    try:
        # Validate ticker
        ticker = request.ticker.strip().upper()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker cannot be empty")
        
        # Use current date
        analysis_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Initialize trading graph with all analysts
        config = get_config()
        graph = TradingAgentsGraph(
            selected_analysts=["market", "social", "news", "fundamentals"],
            debug=False,
            config=config
        )
        
        # Run analysis
        final_state, processed_signal = graph.propagate(ticker, analysis_date)
        
        # Extract results
        return AnalysisResponse(
            ticker=ticker,
            analysis_date=analysis_date,
            market_report=final_state.get("market_report"),
            sentiment_report=final_state.get("sentiment_report"),
            news_report=final_state.get("news_report"),
            fundamentals_report=final_state.get("fundamentals_report"),
            investment_plan=final_state.get("investment_plan"),
            trader_investment_plan=final_state.get("trader_investment_plan"),
            final_trade_decision=final_state.get("final_trade_decision"),
            processed_signal=processed_signal
        )
        
    except Exception as e:
        # Return error in response
        return AnalysisResponse(
            ticker=request.ticker,
            analysis_date=datetime.datetime.now().strftime("%Y-%m-%d"),
            error=str(e)
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}