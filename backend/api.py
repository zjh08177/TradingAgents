from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import datetime
import os
import json
import asyncio
from pathlib import Path
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

# Shared OpenAI client factory (reused by interface.py tools)
_shared_openai_client = None

def get_shared_openai_client():
    """Get a shared OpenAI client with proper configuration"""
    global _shared_openai_client
    if _shared_openai_client is None:
        config = get_config()
        from openai import OpenAI
        _shared_openai_client = OpenAI(base_url=config["backend_url"])
    return _shared_openai_client

def get_compatible_model_for_tools():
    """Get a model that's compatible with web_search_preview tools"""
    config = get_config()
    model = config["quick_think_llm"]
    
    # Models that don't support web_search_preview
    incompatible_models = ["gpt-4.1-nano", "gpt-4.1-mini"]
    
    if model in incompatible_models:
        # Fallback to a compatible model
        fallback_model = "gpt-4o-mini"
        print(f"⚠️  Model {model} doesn't support web_search_preview. Using {fallback_model} for tools.")
        return fallback_model
    
    return model

def save_results_to_disk(ticker: str, analysis_date: str, results: dict, config: dict):
    """Save analysis results to disk like the CLI does"""
    results_dir = Path(config["results_dir"]) / ticker / analysis_date
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save full results as JSON
    results_file = results_dir / "api_analysis_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save individual reports
    reports_dir = results_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Save each report as a separate file
    report_types = [
        ('market_report', 'market_analysis.txt'),
        ('sentiment_report', 'sentiment_analysis.txt'),
        ('news_report', 'news_analysis.txt'),
        ('fundamentals_report', 'fundamentals_analysis.txt'),
        ('investment_plan', 'investment_plan.txt'),
        ('trader_investment_plan', 'trader_investment_plan.txt'),
        ('final_trade_decision', 'final_trade_decision.txt'),
        ('processed_signal', 'signal.txt')
    ]
    
    for key, filename in report_types:
        if results.get(key):
            report_file = reports_dir / filename
            with open(report_file, 'w') as f:
                f.write(str(results[key]))
    
    return str(results_dir)

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
        
        # Prepare results
        results = {
            "ticker": ticker,
            "analysis_date": analysis_date,
            "market_report": final_state.get("market_report"),
            "sentiment_report": final_state.get("sentiment_report"),
            "news_report": final_state.get("news_report"),
            "fundamentals_report": final_state.get("fundamentals_report"),
            "investment_plan": final_state.get("investment_plan"),
            "trader_investment_plan": final_state.get("trader_investment_plan"),
            "final_trade_decision": final_state.get("final_trade_decision"),
            "processed_signal": processed_signal
        }
        
        # Save results to disk
        saved_path = save_results_to_disk(ticker, analysis_date, results, config)
        print(f"✅ Results saved to: {saved_path}")
        
        # Return API response
        return AnalysisResponse(**results)
        
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

# Simple SSE test endpoint
@app.get("/test-stream")
async def test_stream():
    """Simple SSE test endpoint"""
    def event_stream():
        import time
        for i in range(5):
            yield f"data: {json.dumps({'count': i, 'message': f'Test message {i}'})}\n\n"
            time.sleep(1)
        yield f"data: {json.dumps({'message': 'Test complete'})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.get("/analyze/stream")
async def stream_analysis(ticker: str):
    """Stream real-time analysis updates using SSE"""
    print(f"\n🚀 NEW STREAM REQUEST: ticker={ticker}")
    try:
        # Validate ticker
        ticker = ticker.strip().upper()
        if not ticker:
            print("❌ Empty ticker provided")
            raise HTTPException(status_code=400, detail="Ticker cannot be empty")
        
        print(f"✅ Validated ticker: {ticker}")
        
        # Use current date
        analysis_date = datetime.datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Analysis date: {analysis_date}")
        
        async def event_stream():
            try:
                print(f"📡 Starting event stream for {ticker}")
                
                # Send initial status immediately
                initial_event = json.dumps({'type': 'status', 'message': f'Starting analysis for {ticker}...'})
                print(f"📤 Sending initial status: {initial_event}")
                yield f"data: {initial_event}\n\n"
                
                # Initialize trading graph with all analysts
                print("🔧 Initializing trading graph...")
                config = get_config()
                print(f"📋 Config: {config}")
                
                graph = TradingAgentsGraph(
                    selected_analysts=["market", "social", "news", "fundamentals"],
                    debug=True,  # Enable debug mode
                    config=config
                )
                print("✅ Trading graph initialized")
                
                # Initialize state and get graph args
                print("🔧 Creating initial state...")
                init_agent_state = graph.propagator.create_initial_state(ticker, analysis_date)
                print(f"📊 Initial state keys: {list(init_agent_state.keys()) if init_agent_state else 'None'}")
                
                args = graph.propagator.get_graph_args()
                print(f"🔧 Graph args: {args}")
                
                # Track progress and reports
                agent_progress = {
                    "Market Analyst": "pending",
                    "Social Media Analyst": "pending",
                    "News Analyst": "pending", 
                    "Fundamentals Analyst": "pending",
                    "Bull Researcher": "pending",
                    "Bear Researcher": "pending",
                    "Research Manager": "pending",
                    "Trading Team": "pending",
                    "Portfolio Manager": "pending"
                }
                print(f"📊 Initial agent progress: {agent_progress}")
                
                reports_completed = []
                trace = []
                chunk_count = 0
                
                print("🔄 Starting real-time streaming using graph.graph.stream()...")
                
                # Real-time streaming using graph.stream()
                for chunk in graph.graph.stream(init_agent_state, **args):
                    chunk_count += 1
                    print(f"\n📦 CHUNK {chunk_count}: {list(chunk.keys()) if chunk else 'Empty'}")
                    trace.append(chunk)
                    
                    # Allow async event loop to process
                    await asyncio.sleep(0.1)
                    
                    if len(chunk.get("messages", [])) > 0:
                        print(f"💬 Processing {len(chunk['messages'])} messages")
                        
                        # Process messages for agent detection
                        last_message = chunk["messages"][-1]
                        print(f"📨 Last message type: {type(last_message)}")
                        
                        if hasattr(last_message, "content"):
                            content = str(last_message.content) if hasattr(last_message.content, '__str__') else str(last_message.content)
                            
                            # Extract text content if it's a list
                            if isinstance(last_message.content, list):
                                text_parts = []
                                for part in last_message.content:
                                    if hasattr(part, 'text'):
                                        text_parts.append(part.text)
                                    elif isinstance(part, str):
                                        text_parts.append(part)
                                    else:
                                        text_parts.append(str(part))
                                content = " ".join(text_parts)
                            
                            # Send reasoning updates
                            reasoning_event = json.dumps({'type': 'reasoning', 'content': content[:500]})
                            print(f"📤 Sending reasoning: {reasoning_event[:100]}...")
                            yield f"data: {reasoning_event}\n\n"
                    
                    # Handle section completions and send progress updates
                    if "market_report" in chunk and chunk["market_report"] and "market_report" not in reports_completed:
                        print("✅ Market report completed!")
                        agent_progress["Market Analyst"] = "completed"
                        agent_progress["Social Media Analyst"] = "in_progress"
                        reports_completed.append("market_report")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'market', 'status': 'completed'}),
                            json.dumps({'type': 'agent_status', 'agent': 'social', 'status': 'in_progress'}),
                            json.dumps({'type': 'report', 'section': 'market_report', 'content': chunk['market_report']}),
                            json.dumps({'type': 'progress', 'content': '25'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    if "sentiment_report" in chunk and chunk["sentiment_report"] and "sentiment_report" not in reports_completed:
                        print("✅ Sentiment report completed!")
                        agent_progress["Social Media Analyst"] = "completed"
                        agent_progress["News Analyst"] = "in_progress"
                        reports_completed.append("sentiment_report")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'social', 'status': 'completed'}),
                            json.dumps({'type': 'agent_status', 'agent': 'news', 'status': 'in_progress'}),
                            json.dumps({'type': 'report', 'section': 'sentiment_report', 'content': chunk['sentiment_report']}),
                            json.dumps({'type': 'progress', 'content': '40'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    if "news_report" in chunk and chunk["news_report"] and "news_report" not in reports_completed:
                        print("✅ News report completed!")
                        agent_progress["News Analyst"] = "completed"
                        agent_progress["Fundamentals Analyst"] = "in_progress"
                        reports_completed.append("news_report")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'news', 'status': 'completed'}),
                            json.dumps({'type': 'agent_status', 'agent': 'fundamentals', 'status': 'in_progress'}),
                            json.dumps({'type': 'report', 'section': 'news_report', 'content': chunk['news_report']}),
                            json.dumps({'type': 'progress', 'content': '55'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    if "fundamentals_report" in chunk and chunk["fundamentals_report"] and "fundamentals_report" not in reports_completed:
                        print("✅ Fundamentals report completed!")
                        agent_progress["Fundamentals Analyst"] = "completed"
                        agent_progress["Bull Researcher"] = "in_progress"
                        agent_progress["Bear Researcher"] = "in_progress"
                        reports_completed.append("fundamentals_report")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'fundamentals', 'status': 'completed'}),
                            json.dumps({'type': 'agent_status', 'agent': 'bull_researcher', 'status': 'in_progress'}),
                            json.dumps({'type': 'agent_status', 'agent': 'bear_researcher', 'status': 'in_progress'}),
                            json.dumps({'type': 'report', 'section': 'fundamentals_report', 'content': chunk['fundamentals_report']}),
                            json.dumps({'type': 'progress', 'content': '70'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    # Handle research team debates
                    if "investment_debate_state" in chunk and chunk["investment_debate_state"]:
                        print("🔄 Processing investment debate state...")
                        debate_state = chunk["investment_debate_state"]
                        
                        if "judge_decision" in debate_state and debate_state["judge_decision"] and "investment_plan" not in reports_completed:
                            print("✅ Investment plan completed!")
                            agent_progress["Bull Researcher"] = "completed"
                            agent_progress["Bear Researcher"] = "completed"
                            agent_progress["Research Manager"] = "completed"
                            agent_progress["Trading Team"] = "in_progress"
                            reports_completed.append("investment_plan")
                            
                            events = [
                                json.dumps({'type': 'agent_status', 'agent': 'bull_researcher', 'status': 'completed'}),
                                json.dumps({'type': 'agent_status', 'agent': 'bear_researcher', 'status': 'completed'}),
                                json.dumps({'type': 'agent_status', 'agent': 'trader', 'status': 'in_progress'}),
                                json.dumps({'type': 'report', 'section': 'investment_plan', 'content': debate_state['judge_decision']}),
                                json.dumps({'type': 'progress', 'content': '85'})
                            ]
                            
                            for event in events:
                                print(f"📤 Sending: {event[:100]}...")
                                yield f"data: {event}\n\n"
                    
                    # Handle trading team
                    if "trader_investment_plan" in chunk and chunk["trader_investment_plan"] and "trader_investment_plan" not in reports_completed:
                        print("✅ Trading plan completed!")
                        agent_progress["Trading Team"] = "completed"
                        reports_completed.append("trader_investment_plan")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'trader', 'status': 'completed'}),
                            json.dumps({'type': 'report', 'section': 'trader_investment_plan', 'content': chunk['trader_investment_plan']}),
                            json.dumps({'type': 'progress', 'content': '95'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    # Handle final decision
                    if "final_trade_decision" in chunk and chunk["final_trade_decision"] and "final_trade_decision" not in reports_completed:
                        print("✅ Final decision completed!")
                        reports_completed.append("final_trade_decision")
                        
                        events = [
                            json.dumps({'type': 'report', 'section': 'final_trade_decision', 'content': chunk['final_trade_decision']}),
                            json.dumps({'type': 'progress', 'content': '100'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                
                print(f"🔄 Streaming completed. Processed {chunk_count} chunks, {len(reports_completed)} reports completed")
                
                # Get final state and process signal
                final_state = trace[-1] if trace else {}
                processed_signal = graph.process_signal(final_state.get("final_trade_decision", ""))
                
                # Send completion
                completion_event = json.dumps({'type': 'complete', 'message': 'Analysis completed successfully', 'signal': processed_signal})
                print(f"📤 Sending completion: {completion_event}")
                yield f"data: {completion_event}\n\n"
                
            except Exception as e:
                print(f"💥 Error in streaming: {str(e)}")
                import traceback
                traceback.print_exc()
                error_event = json.dumps({'type': 'error', 'message': str(e)})
                print(f"📤 Sending error: {error_event}")
                yield f"data: {error_event}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        print(f"💥 Error in stream_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))