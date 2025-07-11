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
from tradingagents.utils.timing import timing_tracker

# Create FastAPI app
app = FastAPI(
    title="TradingAgents API",
    description="API for TradingAgents financial analysis",
    version="1.0.0"
)

# Add CORS middleware for Swift app
# Get allowed origins from environment variable or use defaults
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Production: Use specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _shared_openai_client = OpenAI(api_key=api_key, base_url=config["backend_url"])
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
        
        # Start timing
        timing_tracker.start_total()
        
        # Initialize trading graph with all analysts
        config = get_config()
        graph = TradingAgentsGraph(
            selected_analysts=["market", "social", "news", "fundamentals"],
            debug=False,
            config=config
        )
        
        # Run analysis
        final_state, processed_signal = graph.propagate(ticker, analysis_date)
        
        # End timing and get summary
        timing_tracker.end_total()
        timing_summary = timing_tracker.get_summary()
        
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
            "processed_signal": processed_signal,
            "timing_summary": timing_summary  # Include timing info
        }
        
        # Save results to disk
        saved_path = save_results_to_disk(ticker, analysis_date, results, config)
        print(f"✅ Results saved to: {saved_path}")
        
        # Return API response (without timing_summary as it's not in the model)
        response_data = {k: v for k, v in results.items() if k != 'timing_summary'}
        return AnalysisResponse(**response_data)
        
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
                    "Risky Analyst": "pending",
                    "Safe Analyst": "pending",
                    "Neutral Analyst": "pending",
                    "Risk Manager": "pending"
                }
                print(f"📊 Initial agent progress: {agent_progress}")
                
                reports_completed = []
                trace = []
                chunk_count = 0
                
                print("🔄 Starting real-time streaming using graph.graph.stream()...")
                
                # Send initial status updates
                initial_events = [
                    json.dumps({'type': 'status', 'message': f'Starting analysis for {ticker}...'}),
                    json.dumps({'type': 'agent_status', 'agent': 'market', 'status': 'in_progress'}),
                    json.dumps({'type': 'agent_status', 'agent': 'social', 'status': 'in_progress'}),
                    json.dumps({'type': 'agent_status', 'agent': 'news', 'status': 'in_progress'}),
                    json.dumps({'type': 'agent_status', 'agent': 'fundamentals', 'status': 'in_progress'}),
                    json.dumps({'type': 'progress', 'content': '5'})
                ]
                
                # Update agent progress to reflect parallel execution
                agent_progress["Market Analyst"] = "in_progress"
                agent_progress["Social Media Analyst"] = "in_progress"
                agent_progress["News Analyst"] = "in_progress"
                agent_progress["Fundamentals Analyst"] = "in_progress"
                
                for event in initial_events:
                    print(f"📤 Sending initial: {event[:100]}...")
                    yield f"data: {event}\n\n"
                
                # Real-time streaming using graph.stream()
                for chunk in graph.graph.stream(init_agent_state, **args):
                    chunk_count += 1
                    print(f"\n📦 CHUNK {chunk_count}: {list(chunk.keys()) if chunk else 'Empty'}")
                    trace.append(chunk)
                    
                    # Allow async event loop to process
                    await asyncio.sleep(0.1)
                    
                    # Check all analyst message channels for new messages
                    message_channels = ["market_messages", "social_messages", "news_messages", "fundamentals_messages"]
                    
                    for channel in message_channels:
                        if channel in chunk and len(chunk[channel]) > 0:
                            # Extract agent name from channel (e.g., 'market_messages' -> 'market')
                            agent_name = channel.replace('_messages', '')
                            
                            print(f"💬 Processing {len(chunk[channel])} messages from {channel} ({agent_name.upper()} AGENT)")
                            
                            # Process messages for agent detection
                            last_message = chunk[channel][-1]
                            print(f"📨 Last message type: {type(last_message)}")
                        
                            # Enhanced logging - Print raw message details
                            print(f"🌐 RAW MESSAGE ATTRS: {[attr for attr in dir(last_message) if not attr.startswith('_')]}")
                            
                            # Log different message types
                            if hasattr(last_message, 'name') and last_message.name:
                                print(f"🤖 AGENT NAME: {last_message.name}")
                            
                            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                print(f"🔧 [{agent_name.upper()}] TOOL CALLS: {len(last_message.tool_calls)} tools invoked")
                                for i, tool_call in enumerate(last_message.tool_calls):
                                    tool_name = tool_call.name if hasattr(tool_call, 'name') else 'Unknown'
                                    print(f"🔧 [{agent_name.upper()}] TOOL[{i}]: {tool_name}")
                                    if hasattr(tool_call, 'args'):
                                        print(f"🔧 [{agent_name.upper()}] TOOL[{i}] ARGS: {json.dumps(tool_call.args, indent=2) if isinstance(tool_call.args, dict) else tool_call.args}")
                            
                            if hasattr(last_message, "content"):
                                content = str(last_message.content) if hasattr(last_message.content, '__str__') else str(last_message.content)
                                
                                # Enhanced logging - Print raw content structure
                                print(f"📋 [{agent_name.upper()}] RAW CONTENT TYPE: {type(last_message.content)}")
                                print(f"📋 [{agent_name.upper()}] RAW CONTENT LENGTH: {len(last_message.content) if hasattr(last_message.content, '__len__') else 'N/A'}")
                                
                                # Extract text content if it's a list
                                if isinstance(last_message.content, list):
                                    print(f"📋 [{agent_name.upper()}] CONTENT LIST LENGTH: {len(last_message.content)}")
                                    text_parts = []
                                    for j, part in enumerate(last_message.content):
                                        print(f"📋 [{agent_name.upper()}] CONTENT[{j}] TYPE: {type(part)}")
                                        if hasattr(part, 'text'):
                                            text_parts.append(part.text)
                                            print(f"📋 [{agent_name.upper()}] CONTENT[{j}] TEXT (first 200 chars): {part.text[:200]}...")
                                        elif isinstance(part, str):
                                            text_parts.append(part)
                                            print(f"📋 [{agent_name.upper()}] CONTENT[{j}] STRING (first 200 chars): {part[:200]}...")
                                        else:
                                            text_parts.append(str(part))
                                            print(f"📋 [{agent_name.upper()}] CONTENT[{j}] OTHER: {str(part)[:200]}...")
                                    content = " ".join(text_parts)
                                else:
                                    # Single content item
                                    print(f"📋 [{agent_name.upper()}] SINGLE CONTENT (first 500 chars): {content[:500]}...")
                                
                                # Log full content for debugging (can be toggled)
                                if os.getenv("LOG_FULL_CONTENT", "false").lower() == "true":
                                    print(f"📝 [{agent_name.upper()}] FULL CONTENT:\n{content}\n")
                                
                                # Send reasoning updates WITH agent information
                                if isinstance(content, str) and content.strip():
                                    reasoning_event = json.dumps({
                                        'type': 'reasoning', 
                                        'agent': agent_name,
                                        'content': content[:500]
                                    })
                                    print(f"📤 [{agent_name.upper()}] Sending reasoning: {reasoning_event[:100]}...")
                                    yield f"data: {reasoning_event}\n\n"
                            
                            # Log tool message responses
                            if hasattr(last_message, 'type') and str(last_message.type) == 'tool':
                                print(f"🛠️ TOOL MESSAGE DETECTED")
                                if hasattr(last_message, 'tool_call_id'):
                                    print(f"🛠️ TOOL CALL ID: {last_message.tool_call_id}")
                                if hasattr(last_message, 'content'):
                                    print(f"🛠️ TOOL RESPONSE LENGTH: {len(last_message.content)} chars")
                                    print(f"🛠️ TOOL RESPONSE PREVIEW (first 500 chars):\n{last_message.content[:500]}...")
                    
                    # Handle section completions and send progress updates
                    if "market_report" in chunk and chunk["market_report"] and "market_report" not in reports_completed:
                        print("✅ Market report completed!")
                        agent_progress["Market Analyst"] = "completed"
                        reports_completed.append("market_report")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'market', 'status': 'completed'}),
                            json.dumps({'type': 'report', 'section': 'market_report', 'content': chunk['market_report']}),
                            json.dumps({'type': 'progress', 'content': '25'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    if "sentiment_report" in chunk and chunk["sentiment_report"] and "sentiment_report" not in reports_completed:
                        print("✅ Sentiment report completed!")
                        agent_progress["Social Media Analyst"] = "completed"
                        reports_completed.append("sentiment_report")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'social', 'status': 'completed'}),
                            json.dumps({'type': 'report', 'section': 'sentiment_report', 'content': chunk['sentiment_report']}),
                            json.dumps({'type': 'progress', 'content': '40'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    if "news_report" in chunk and chunk["news_report"] and "news_report" not in reports_completed:
                        print("✅ News report completed!")
                        agent_progress["News Analyst"] = "completed"
                        reports_completed.append("news_report")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'news', 'status': 'completed'}),
                            json.dumps({'type': 'report', 'section': 'news_report', 'content': chunk['news_report']}),
                            json.dumps({'type': 'progress', 'content': '55'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    if "fundamentals_report" in chunk and chunk["fundamentals_report"] and "fundamentals_report" not in reports_completed:
                        print("✅ Fundamentals report completed!")
                        agent_progress["Fundamentals Analyst"] = "completed"
                        
                        # Start research team only if all analysts are done
                        all_analysts_done = all(agent_progress[agent] == "completed" for agent in ["Market Analyst", "Social Media Analyst", "News Analyst", "Fundamentals Analyst"])
                        
                        if all_analysts_done:
                            agent_progress["Bull Researcher"] = "in_progress"
                            agent_progress["Bear Researcher"] = "in_progress"
                        
                        reports_completed.append("fundamentals_report")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'fundamentals', 'status': 'completed'}),
                            json.dumps({'type': 'report', 'section': 'fundamentals_report', 'content': chunk['fundamentals_report']}),
                            json.dumps({'type': 'progress', 'content': '70'})
                        ]
                        
                        # Add research team start events if all analysts are done
                        if all_analysts_done:
                            events.extend([
                                json.dumps({'type': 'agent_status', 'agent': 'bull_researcher', 'status': 'in_progress'}),
                                json.dumps({'type': 'agent_status', 'agent': 'bear_researcher', 'status': 'in_progress'})
                            ])
                        
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
                                json.dumps({'type': 'agent_status', 'agent': 'research_manager', 'status': 'completed'}),
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
                        agent_progress["Risky Analyst"] = "in_progress"  # Start risk analysis phase
                        agent_progress["Safe Analyst"] = "in_progress"
                        agent_progress["Neutral Analyst"] = "in_progress"
                        reports_completed.append("trader_investment_plan")
                        
                        events = [
                            json.dumps({'type': 'agent_status', 'agent': 'trader', 'status': 'completed'}),
                            json.dumps({'type': 'agent_status', 'agent': 'risky_analyst', 'status': 'in_progress'}),
                            json.dumps({'type': 'agent_status', 'agent': 'safe_analyst', 'status': 'in_progress'}),
                            json.dumps({'type': 'agent_status', 'agent': 'neutral_analyst', 'status': 'in_progress'}),
                            json.dumps({'type': 'report', 'section': 'trader_investment_plan', 'content': chunk['trader_investment_plan']}),
                            json.dumps({'type': 'progress', 'content': '90'})
                        ]
                        
                        for event in events:
                            print(f"📤 Sending: {event[:100]}...")
                            yield f"data: {event}\n\n"
                    
                    # Handle risk analysis completion
                    if "risk_debate_state" in chunk and chunk["risk_debate_state"]:
                        print("🔄 Processing risk debate state...")
                        risk_state = chunk["risk_debate_state"]
                        
                        if "judge_decision" in risk_state and risk_state["judge_decision"] and "risk_analysis" not in reports_completed:
                            print("✅ Risk analysis completed!")
                            agent_progress["Risky Analyst"] = "completed"
                            agent_progress["Safe Analyst"] = "completed"
                            agent_progress["Neutral Analyst"] = "completed"
                            agent_progress["Risk Manager"] = "completed"
                            reports_completed.append("risk_analysis")
                            
                            events = [
                                json.dumps({'type': 'agent_status', 'agent': 'risky_analyst', 'status': 'completed'}),
                                json.dumps({'type': 'agent_status', 'agent': 'safe_analyst', 'status': 'completed'}),
                                json.dumps({'type': 'agent_status', 'agent': 'neutral_analyst', 'status': 'completed'}),
                                json.dumps({'type': 'agent_status', 'agent': 'risk_manager', 'status': 'completed'}),
                                json.dumps({'type': 'report', 'section': 'risk_analysis', 'content': risk_state['judge_decision']}),
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
                
                # Save results to disk (same as regular analyze endpoint)
                try:
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
                    
                    config = get_config()
                    saved_path = save_results_to_disk(ticker, analysis_date, results, config)
                    print(f"✅ Results saved to: {saved_path}")
                    
                except Exception as save_error:
                    print(f"⚠️ Failed to save results: {save_error}")
                
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