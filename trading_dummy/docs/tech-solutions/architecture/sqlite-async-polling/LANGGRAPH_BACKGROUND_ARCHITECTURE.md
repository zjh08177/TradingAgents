# LangGraph Background Run Architecture

## Executive Summary

LangGraph Platform natively supports background runs, eliminating the need for custom queue implementation. This architecture leverages LangGraph's built-in async capabilities for a simpler, more robust solution.

## Architecture Overview

```mermaid
graph TD
    A[Flutter App] -->|POST /api/analyze| B[Server API]
    B -->|Create Thread & Run| C[LangGraph Platform]
    C -->|Immediate return| B
    B -->|Return run_id| A
    
    A -->|GET /api/runs/{run_id}| B
    B -->|Get Run Status| C
    C -->|Status & Results| B
    B -->|JSON Response| A
    
    A -->|Update UI| D[Trading UI]
    
    style C fill:#f9f,stroke:#333,stroke-width:4px
```

## How It Works

### 1. Submission Flow

```dart
// User taps analyze button
POST /api/analyze
{
  "ticker": "AAPL",
  "tradeDate": "2025-08-02"
}

// Server creates LangGraph run
Response (immediate):
{
  "runId": "run_abc123",
  "threadId": "thread_xyz789",
  "status": "pending",
  "createdAt": "2025-08-02T10:30:00Z"
}
```

### 2. Polling Flow

```dart
// Client polls every 3-5 seconds
GET /api/runs/run_abc123

// Server checks LangGraph status
Response:
{
  "runId": "run_abc123",
  "status": "running", // pending -> running -> success/error
  "progress": 45,
  "currentStep": "analyzing_fundamentals",
  "updatedAt": "2025-08-02T10:30:15Z"
}

// When complete
{
  "runId": "run_abc123",
  "status": "success",
  "completedAt": "2025-08-02T10:31:30Z",
  "result": {
    "recommendation": "BUY",
    "confidence": 0.85,
    "analysis": { ... }
  }
}
```

### 3. Server Implementation

```python
# server/api/analyze.py
from langgraph_sdk import get_client

class AnalysisAPI:
    def __init__(self):
        self.client = get_client(url=LANGGRAPH_URL)
        self.assistant_id = "trading-analyst"
    
    async def start_analysis(self, ticker: str, trade_date: str):
        # Create thread for this analysis
        thread = await self.client.threads.create()
        
        # Prepare input
        input_data = {
            "messages": [{
                "role": "user",
                "content": f"Analyze {ticker} for {trade_date}"
            }],
            "config": {
                "ticker": ticker,
                "trade_date": trade_date
            }
        }
        
        # Start background run
        run = await self.client.runs.create(
            thread_id=thread["thread_id"],
            assistant_id=self.assistant_id,
            input=input_data
        )
        
        return {
            "runId": run["run_id"],
            "threadId": thread["thread_id"],
            "status": "pending",
            "createdAt": datetime.now().isoformat()
        }
    
    async def get_run_status(self, run_id: str):
        # Get run details
        run = await self.client.runs.get(thread_id=None, run_id=run_id)
        
        if run["status"] == "success":
            # Get final state
            thread_state = await self.client.threads.get_state(
                thread_id=run["thread_id"]
            )
            
            return {
                "runId": run_id,
                "status": "success",
                "completedAt": run["updated_at"],
                "result": thread_state["values"]
            }
        
        return {
            "runId": run_id,
            "status": run["status"],
            "updatedAt": run["updated_at"]
        }
```

## Flutter Client Implementation

### API Service Layer

```dart
// lib/jobs/infrastructure/services/langgraph_api_service.dart
class LangGraphApiService {
  final Dio dio;
  final String baseUrl;
  
  /// Start analysis and get run ID immediately
  Future<AnalysisRun> startAnalysis({
    required String ticker,
    required String tradeDate,
  }) async {
    final response = await dio.post(
      '$baseUrl/api/analyze',
      data: {
        'ticker': ticker,
        'tradeDate': tradeDate,
      },
    );
    
    return AnalysisRun.fromJson(response.data);
  }
  
  /// Poll run status
  Future<AnalysisRun> getRunStatus(String runId) async {
    final response = await dio.get('$baseUrl/api/runs/$runId');
    return AnalysisRun.fromJson(response.data);
  }
}
```

### Simple Models

```dart
// lib/jobs/domain/models/analysis_run.dart
class AnalysisRun {
  final String runId;
  final String? threadId;
  final RunStatus status;
  final DateTime createdAt;
  final DateTime? completedAt;
  final Map<String, dynamic>? result;
  final String? currentStep;
  final int? progress;
  
  bool get isComplete => status == RunStatus.success || status == RunStatus.error;
  bool get isRunning => status == RunStatus.running;
}

enum RunStatus {
  pending,   // Queued in LangGraph
  running,   // Actively processing
  success,   // Completed successfully
  error;     // Failed
  
  static RunStatus fromString(String value) {
    return RunStatus.values.firstWhere(
      (e) => e.name == value,
      orElse: () => RunStatus.pending,
    );
  }
}
```

### Smart Polling Service

```dart
// lib/jobs/infrastructure/services/run_polling_service.dart
class RunPollingService {
  final LangGraphApiService apiService;
  final Map<String, Timer> _activePolls = {};
  final Map<String, StreamController<AnalysisRun>> _runStreams = {};
  
  /// Start polling a specific run
  Stream<AnalysisRun> pollRun(String runId) {
    // Return existing stream if already polling
    if (_runStreams.containsKey(runId)) {
      return _runStreams[runId]!.stream;
    }
    
    // Create new stream
    final controller = StreamController<AnalysisRun>.broadcast();
    _runStreams[runId] = controller;
    
    // Start polling
    _startPolling(runId);
    
    return controller.stream;
  }
  
  void _startPolling(String runId) {
    // Initial poll
    _pollOnce(runId);
    
    // Schedule periodic polls with backoff
    int pollCount = 0;
    _activePolls[runId] = Timer.periodic(
      _getPollingInterval(pollCount++),
      (_) => _pollOnce(runId),
    );
  }
  
  Duration _getPollingInterval(int pollCount) {
    // Start fast, then slow down
    if (pollCount < 10) return Duration(seconds: 2);
    if (pollCount < 20) return Duration(seconds: 5);
    return Duration(seconds: 10);
  }
  
  Future<void> _pollOnce(String runId) async {
    try {
      final run = await apiService.getRunStatus(runId);
      
      // Emit update
      _runStreams[runId]?.add(run);
      
      // Stop polling if complete
      if (run.isComplete) {
        _stopPolling(runId);
      }
    } catch (e) {
      _runStreams[runId]?.addError(e);
    }
  }
  
  void _stopPolling(String runId) {
    _activePolls[runId]?.cancel();
    _activePolls.remove(runId);
    _runStreams[runId]?.close();
    _runStreams.remove(runId);
  }
}
```

### ViewModel Integration

```dart
// lib/jobs/presentation/view_models/analysis_view_model.dart
class AnalysisViewModel extends ChangeNotifier {
  final LangGraphApiService apiService;
  final RunPollingService pollingService;
  
  final Map<String, AnalysisRun> _activeRuns = {};
  
  Map<String, AnalysisRun> get activeRuns => Map.unmodifiable(_activeRuns);
  
  Future<void> startAnalysis(String ticker, String tradeDate) async {
    try {
      // Start analysis - returns immediately
      final run = await apiService.startAnalysis(
        ticker: ticker,
        tradeDate: tradeDate,
      );
      
      // Add to active runs
      _activeRuns[run.runId] = run;
      notifyListeners();
      
      // Start polling for updates
      pollingService.pollRun(run.runId).listen(
        (updatedRun) {
          _activeRuns[run.runId] = updatedRun;
          notifyListeners();
          
          if (updatedRun.isComplete) {
            _handleCompletion(updatedRun);
          }
        },
        onError: (error) {
          _handleError(run.runId, error);
        },
      );
      
    } catch (e) {
      // Handle submission error
      _showError('Failed to start analysis: $e');
    }
  }
  
  void _handleCompletion(AnalysisRun run) {
    if (run.status == RunStatus.success) {
      // Navigate to results or show notification
      _showNotification('Analysis complete for ${run.result?['ticker']}');
    } else {
      _showError('Analysis failed');
    }
  }
}
```

## Key Benefits

### 1. Simplicity
- No custom queue implementation needed
- LangGraph handles all async complexity
- Clean API with immediate feedback

### 2. Reliability
- LangGraph manages retries and failures
- Built-in monitoring and logging
- Production-ready infrastructure

### 3. Scalability
- LangGraph handles concurrent runs
- No client-side resource management
- Server can scale horizontally

### 4. Visibility
- Native LangGraph Studio integration
- Full trace visibility
- Debug capabilities built-in

## Migration from Current Architecture

### What to Keep
- ✅ UI components (with minor updates)
- ✅ Event system (for local UI updates)
- ✅ Domain models (simplified)
- ✅ Test structure

### What to Replace
- ❌ JobQueueManager → LangGraphApiService
- ❌ JobProcessor → LangGraph handles this
- ❌ RetryScheduler → LangGraph handles this
- ❌ Complex job states → Simple run states

### What to Add
- ✅ LangGraphApiService
- ✅ RunPollingService
- ✅ Server API endpoints

## Implementation Steps

### Phase 1: Server API (Day 1)
1. Create `/api/analyze` endpoint
2. Integrate LangGraph SDK
3. Test with curl/Postman

### Phase 2: Flutter Integration (Day 2)
1. Create LangGraphApiService
2. Add RunPollingService
3. Update ViewModels

### Phase 3: UI Updates (Day 3)
1. Update submission flow
2. Add progress indicators
3. Polish status displays

### Phase 4: Testing & Polish (Day 4)
1. End-to-end testing
2. Error handling
3. Performance tuning

## API Specification

### Start Analysis
```http
POST /api/analyze
Content-Type: application/json

{
  "ticker": "AAPL",
  "tradeDate": "2025-08-02"
}

Response 200:
{
  "runId": "run_abc123",
  "threadId": "thread_xyz789",
  "status": "pending",
  "createdAt": "2025-08-02T10:30:00Z"
}
```

### Get Run Status
```http
GET /api/runs/{runId}

Response 200 (Running):
{
  "runId": "run_abc123",
  "status": "running",
  "progress": 45,
  "currentStep": "analyzing_fundamentals",
  "updatedAt": "2025-08-02T10:30:15Z"
}

Response 200 (Complete):
{
  "runId": "run_abc123",
  "status": "success",
  "completedAt": "2025-08-02T10:31:30Z",
  "result": {
    "recommendation": "BUY",
    "confidence": 0.85,
    "analysis": { ... }
  }
}
```

### List Recent Runs
```http
GET /api/runs?limit=20

Response 200:
{
  "runs": [
    {
      "runId": "run_abc123",
      "ticker": "AAPL",
      "tradeDate": "2025-08-02",
      "status": "success",
      "createdAt": "2025-08-02T10:30:00Z",
      "completedAt": "2025-08-02T10:31:30Z"
    },
    ...
  ]
}
```

## Conclusion

Using LangGraph's native background run capabilities provides a much cleaner architecture than building our own queue system. This approach gives us:

1. **Immediate feedback** - User gets run ID instantly
2. **Simple implementation** - Leverage existing infrastructure
3. **Better visibility** - LangGraph Studio integration
4. **Production ready** - Battle-tested platform

The iteration approach still applies, but now we're iterating toward LangGraph integration instead of a custom server queue.