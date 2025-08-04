# LangGraph API Implementation Guide

## Server-Side Implementation

### FastAPI Server Structure

```python
# server/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import os

from langgraph_sdk import get_client

app = FastAPI()

# Initialize LangGraph client
LANGGRAPH_URL = os.getenv("LANGGRAPH_API_URL")
langgraph_client = get_client(url=LANGGRAPH_URL)
ASSISTANT_ID = "trading-analyst"

# Request/Response Models
class AnalysisRequest(BaseModel):
    ticker: str
    tradeDate: str

class AnalysisRunResponse(BaseModel):
    runId: str
    threadId: str
    status: str
    createdAt: datetime
    
class RunStatusResponse(BaseModel):
    runId: str
    status: str
    progress: Optional[int] = None
    currentStep: Optional[str] = None
    updatedAt: datetime
    completedAt: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### Core API Endpoints

```python
# server/api/analysis.py
from typing import Dict, List
import asyncio
from datetime import datetime

class AnalysisService:
    def __init__(self, client, assistant_id: str):
        self.client = client
        self.assistant_id = assistant_id
        self.run_cache: Dict[str, dict] = {}  # Simple in-memory cache
    
    async def start_analysis(self, ticker: str, trade_date: str) -> AnalysisRunResponse:
        """Start a LangGraph background run for stock analysis"""
        try:
            # Create a new thread for this analysis
            thread = await self.client.threads.create()
            
            # Prepare the input for LangGraph
            input_data = {
                "messages": [{
                    "role": "user",
                    "content": f"Analyze {ticker} for trading date {trade_date}"
                }],
                "config": {
                    "configurable": {
                        "ticker": ticker,
                        "trade_date": trade_date,
                        "analysis_type": "comprehensive"
                    }
                }
            }
            
            # Start the background run
            run = await self.client.runs.create(
                thread_id=thread["thread_id"],
                assistant_id=self.assistant_id,
                input=input_data,
                config={
                    "tags": ["trading-analysis", f"ticker:{ticker}"],
                    "metadata": {
                        "ticker": ticker,
                        "trade_date": trade_date,
                        "requested_at": datetime.now().isoformat()
                    }
                }
            )
            
            # Cache run info for quick lookups
            self.run_cache[run["run_id"]] = {
                "thread_id": thread["thread_id"],
                "ticker": ticker,
                "trade_date": trade_date
            }
            
            return AnalysisRunResponse(
                runId=run["run_id"],
                threadId=thread["thread_id"],
                status="pending",
                createdAt=datetime.now()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")
    
    async def get_run_status(self, run_id: str) -> RunStatusResponse:
        """Get the current status of a background run"""
        try:
            # Get run details
            run = await self.client.runs.get(run_id=run_id)
            
            # Map LangGraph status to our status
            status_map = {
                "pending": "pending",
                "running": "running",
                "succeeded": "success",
                "failed": "error",
                "cancelled": "cancelled"
            }
            
            response = RunStatusResponse(
                runId=run_id,
                status=status_map.get(run["status"], "unknown"),
                updatedAt=datetime.fromisoformat(run["updated_at"])
            )
            
            # Add progress information if available
            if run.get("metadata", {}).get("progress"):
                response.progress = run["metadata"]["progress"]
                response.currentStep = run["metadata"].get("current_step")
            
            # If completed, get the final state
            if run["status"] == "succeeded":
                thread_id = self.run_cache.get(run_id, {}).get("thread_id")
                if thread_id:
                    thread_state = await self.client.threads.get_state(thread_id)
                    
                    # Extract analysis results
                    response.result = self._extract_analysis_results(thread_state)
                    response.completedAt = datetime.fromisoformat(run["updated_at"])
            
            elif run["status"] == "failed":
                response.error = run.get("error", "Analysis failed")
                response.completedAt = datetime.fromisoformat(run["updated_at"])
            
            return response
            
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Run not found: {str(e)}")
    
    def _extract_analysis_results(self, thread_state: dict) -> dict:
        """Extract structured results from LangGraph thread state"""
        values = thread_state.get("values", {})
        
        # Extract the final analysis from messages or structured output
        messages = values.get("messages", [])
        
        # Look for the final analysis message
        for message in reversed(messages):
            if message.get("type") == "ai" and "analysis_complete" in message.get("content", ""):
                # Parse structured result
                return {
                    "recommendation": message.get("recommendation", "HOLD"),
                    "confidence": message.get("confidence", 0.5),
                    "analysis": message.get("analysis", {}),
                    "signals": message.get("signals", []),
                    "risk_assessment": message.get("risk_assessment", {})
                }
        
        # Fallback to basic structure
        return {
            "recommendation": "HOLD",
            "confidence": 0.5,
            "analysis": {"status": "completed"},
            "raw_messages": messages[-3:]  # Last 3 messages for debugging
        }
    
    async def list_recent_runs(self, limit: int = 20) -> List[dict]:
        """List recent analysis runs"""
        # In production, this would query a database
        # For now, return cached runs
        recent_runs = []
        
        for run_id, info in list(self.run_cache.items())[-limit:]:
            try:
                status = await self.get_run_status(run_id)
                recent_runs.append({
                    "runId": run_id,
                    "ticker": info["ticker"],
                    "tradeDate": info["trade_date"],
                    "status": status.status,
                    "createdAt": status.updatedAt.isoformat(),
                    "completedAt": status.completedAt.isoformat() if status.completedAt else None
                })
            except:
                continue
        
        return recent_runs
```

### API Routes

```python
# server/main.py (continued)
analysis_service = AnalysisService(langgraph_client, ASSISTANT_ID)

@app.post("/api/analyze", response_model=AnalysisRunResponse)
async def start_analysis(request: AnalysisRequest):
    """Start a new stock analysis"""
    return await analysis_service.start_analysis(
        ticker=request.ticker,
        trade_date=request.tradeDate
    )

@app.get("/api/runs/{run_id}", response_model=RunStatusResponse)
async def get_run_status(run_id: str):
    """Get the status of an analysis run"""
    return await analysis_service.get_run_status(run_id)

@app.get("/api/runs")
async def list_runs(limit: int = 20):
    """List recent analysis runs"""
    runs = await analysis_service.list_recent_runs(limit)
    return {"runs": runs}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test LangGraph connection
        await langgraph_client.assistants.get(ASSISTANT_ID)
        return {"status": "healthy", "langgraph": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Error Handling & Monitoring

```python
# server/middleware.py
from fastapi import Request
import time
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response time
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )
```

## Flutter Client Implementation Details

### Complete API Service

```dart
// lib/jobs/infrastructure/services/langgraph_api_service.dart
import 'package:dio/dio.dart';
import '../../domain/entities/analysis_job.dart';
import '../../domain/value_objects/job_status.dart';
import '../../../core/config/api_config.dart';

class LangGraphApiService {
  final Dio dio;
  late final String baseUrl;
  
  LangGraphApiService({Dio? dioClient}) 
    : dio = dioClient ?? _createDio() {
    baseUrl = ApiConfig.baseUrl;
  }
  
  static Dio _createDio() {
    final dio = Dio();
    
    // Add interceptors
    dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));
    
    // Add timeout
    dio.options.connectTimeout = Duration(seconds: 10);
    dio.options.receiveTimeout = Duration(seconds: 10);
    
    return dio;
  }
  
  /// Start analysis and get run ID immediately
  Future<AnalysisJob> startAnalysis({
    required String ticker,
    required String tradeDate,
  }) async {
    try {
      final response = await dio.post(
        '$baseUrl/api/analyze',
        data: {
          'ticker': ticker,
          'tradeDate': tradeDate,
        },
      );
      
      // Map response to our domain model
      return AnalysisJob(
        id: response.data['runId'],
        ticker: ticker,
        tradeDate: tradeDate,
        status: JobStatus.queued,
        priority: JobPriority.normal,
        createdAt: DateTime.parse(response.data['createdAt']),
        retryCount: 0,
        // Store LangGraph metadata
        metadata: {
          'threadId': response.data['threadId'],
          'langGraphRunId': response.data['runId'],
        },
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 400) {
        throw ValidationException(e.response?.data['error'] ?? 'Invalid request');
      } else if (e.response?.statusCode == 500) {
        throw ServerException('Server error: ${e.response?.data['error']}');
      } else {
        throw NetworkException('Network error: ${e.message}');
      }
    }
  }
  
  /// Get current status of a run
  Future<AnalysisJob> getRunStatus(String runId) async {
    try {
      final response = await dio.get('$baseUrl/api/runs/$runId');
      
      final data = response.data;
      
      return AnalysisJob(
        id: runId,
        ticker: '', // Would need to store/retrieve this
        tradeDate: '', // Would need to store/retrieve this
        status: _mapStatus(data['status']),
        priority: JobPriority.normal,
        createdAt: DateTime.parse(data['updatedAt']),
        startedAt: data['status'] == 'running' 
          ? DateTime.parse(data['updatedAt']) 
          : null,
        completedAt: data['completedAt'] != null
          ? DateTime.parse(data['completedAt'])
          : null,
        resultId: data['result'] != null ? runId : null,
        errorMessage: data['error'],
        retryCount: 0,
        metadata: {
          'progress': data['progress'],
          'currentStep': data['currentStep'],
          'result': data['result'],
        },
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw NotFoundException('Run not found: $runId');
      } else {
        throw NetworkException('Failed to get run status: ${e.message}');
      }
    }
  }
  
  /// List recent runs
  Future<List<AnalysisJob>> listRecentRuns({int limit = 20}) async {
    try {
      final response = await dio.get(
        '$baseUrl/api/runs',
        queryParameters: {'limit': limit},
      );
      
      final runs = response.data['runs'] as List;
      
      return runs.map((run) => AnalysisJob(
        id: run['runId'],
        ticker: run['ticker'],
        tradeDate: run['tradeDate'],
        status: _mapStatus(run['status']),
        priority: JobPriority.normal,
        createdAt: DateTime.parse(run['createdAt']),
        completedAt: run['completedAt'] != null
          ? DateTime.parse(run['completedAt'])
          : null,
        retryCount: 0,
      )).toList();
    } on DioException catch (e) {
      throw NetworkException('Failed to list runs: ${e.message}');
    }
  }
  
  JobStatus _mapStatus(String status) {
    switch (status) {
      case 'pending':
        return JobStatus.queued;
      case 'running':
        return JobStatus.running;
      case 'success':
        return JobStatus.completed;
      case 'error':
        return JobStatus.failed;
      case 'cancelled':
        return JobStatus.cancelled;
      default:
        return JobStatus.pending;
    }
  }
}

// Custom exceptions
class ValidationException implements Exception {
  final String message;
  ValidationException(this.message);
}

class ServerException implements Exception {
  final String message;
  ServerException(this.message);
}

class NetworkException implements Exception {
  final String message;
  NetworkException(this.message);
}

class NotFoundException implements Exception {
  final String message;
  NotFoundException(this.message);
}
```

## Testing Strategy

### Server Tests

```python
# tests/test_analysis_api.py
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_start_analysis():
    # Mock LangGraph client
    mock_client = Mock()
    mock_client.threads.create = AsyncMock(return_value={"thread_id": "thread123"})
    mock_client.runs.create = AsyncMock(return_value={
        "run_id": "run123",
        "status": "pending"
    })
    
    # Test API call
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/analyze", json={
            "ticker": "AAPL",
            "tradeDate": "2025-08-02"
        })
    
    assert response.status_code == 200
    assert response.json()["runId"] == "run123"
    assert response.json()["status"] == "pending"
```

### Flutter Tests

```dart
// test/jobs/infrastructure/services/langgraph_api_service_test.dart
void main() {
  group('LangGraphApiService', () {
    late LangGraphApiService service;
    late MockDio mockDio;
    
    setUp(() {
      mockDio = MockDio();
      service = LangGraphApiService(dioClient: mockDio);
    });
    
    test('startAnalysis returns job with run ID', () async {
      // Arrange
      when(mockDio.post(any, data: anyNamed('data')))
        .thenAnswer((_) async => Response(
          data: {
            'runId': 'run123',
            'threadId': 'thread123',
            'status': 'pending',
            'createdAt': '2025-08-02T10:30:00Z',
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        ));
      
      // Act
      final job = await service.startAnalysis(
        ticker: 'AAPL',
        tradeDate: '2025-08-02',
      );
      
      // Assert
      expect(job.id, equals('run123'));
      expect(job.status, equals(JobStatus.queued));
      expect(job.metadata?['threadId'], equals('thread123'));
    });
  });
}
```

## Deployment Considerations

1. **Environment Variables**
   ```bash
   LANGGRAPH_API_URL=https://api.langchain.com/v1
   LANGGRAPH_API_KEY=your-api-key
   ASSISTANT_ID=trading-analyst
   ```

2. **Rate Limiting**
   - Add rate limiting to prevent abuse
   - Consider caching frequently requested runs

3. **Monitoring**
   - Track API response times
   - Monitor LangGraph costs
   - Alert on high error rates

4. **Security**
   - Validate all inputs
   - Use API authentication
   - Sanitize error messages

This implementation provides a clean integration with LangGraph's background run capabilities while maintaining compatibility with the existing Flutter app architecture.