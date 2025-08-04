# Async Analysis Solution Design

## Architecture Overview

### Simplified Architecture

```
┌─────────────────────────────────────────────────┐
│                   Flutter App                    │
├─────────────────────────────────────────────────┤
│  Presentation Layer                              │
│  - AnalysisScreen (submit)                      │
│  - HistoryScreen (view jobs)                    │
│  - Simple ViewModels                             │
├─────────────────────────────────────────────────┤
│  Service Layer                                   │
│  - AnalysisApiService (direct API calls)        │
│  - StatusPollingService (5s polling)            │
└─────────────────────────────────────────────────┘
                          │
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────┐
│                  Server API                      │
│  - POST /api/analyze                             │
│  - GET /api/jobs                                 │
│  - GET /api/jobs/{id}                            │
│  - Manages queue & LangGraph                     │
└─────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────┐
│              LangGraph Studio                    │
│  - Immediate trace visibility                    │
│  - Full execution graphs                         │
└─────────────────────────────────────────────────┘
```

## Detailed Component Design

### 1. API Service Layer

```dart
// lib/analysis/services/analysis_api_service.dart
class AnalysisApiService {
  final String baseUrl;
  final Dio dio;
  
  /// Submit analysis request directly to server
  Future<AnalysisStatus> submitAnalysis({
    required String ticker,
    required String tradeDate,
  }) async {
    final response = await dio.post(
      '/api/analyze',
      data: {
        'ticker': ticker,
        'tradeDate': tradeDate,
      },
    );
    
    return AnalysisStatus.fromJson(response.data);
  }
  
  /// Get job history from server
  Future<List<AnalysisStatus>> getJobHistory({
    int limit = 50,
  }) async {
    final response = await dio.get(
      '/api/jobs',
      queryParameters: {'limit': limit},
    );
    
    return (response.data['jobs'] as List)
        .map((json) => AnalysisStatus.fromJson(json))
        .toList();
  }
  
  /// Get single job status
  Future<AnalysisStatus> getJobStatus(String jobId) async {
    final response = await dio.get('/api/jobs/$jobId');
    return AnalysisStatus.fromJson(response.data);
  }
}
```

### 2. Simplified Models

```dart
// lib/analysis/models/analysis_models.dart

/// Simple request model
class AnalysisRequest {
  final String ticker;
  final String tradeDate;
  
  const AnalysisRequest({
    required this.ticker,
    required this.tradeDate,
  });
}

/// Simple status model
class AnalysisStatus {
  final String jobId;
  final String ticker;
  final String tradeDate;
  final JobStatus status;
  final DateTime submittedAt;
  final DateTime? completedAt;
  final int? duration; // milliseconds
  final String? resultId;
  final String? error;
  final String? traceId; // LangGraph Studio
  
  bool get isComplete => status == JobStatus.completed || status == JobStatus.failed;
  bool get isProcessing => status == JobStatus.processing;
}

enum JobStatus {
  submitted,
  processing,
  completed,
  failed;
  
  static JobStatus fromString(String value) {
    return JobStatus.values.firstWhere(
      (e) => e.name == value,
      orElse: () => JobStatus.submitted,
    );
  }
}
```

### 3. Status Polling Service

```dart
// lib/analysis/services/status_polling_service.dart
class StatusPollingService {
  final AnalysisApiService apiService;
  final Duration pollInterval = const Duration(seconds: 5);
  
  Timer? _timer;
  final _statusController = StreamController<List<AnalysisStatus>>.broadcast();
  
  Stream<List<AnalysisStatus>> get statusStream => _statusController.stream;
  
  void startPolling() {
    stopPolling();
    _timer = Timer.periodic(pollInterval, (_) => _pollJobs());
    _pollJobs(); // Initial poll
  }
  
  void stopPolling() {
    _timer?.cancel();
    _timer = null;
  }
  
  Future<void> _pollJobs() async {
    try {
      final jobs = await apiService.getJobHistory();
      _statusController.add(jobs);
    } catch (e) {
      // Log error but continue polling
    }
  }
  
  void dispose() {
    stopPolling();
    _statusController.close();
  }
}
```

### 4. Simplified ViewModels

```dart
// lib/analysis/view_models/analysis_view_model.dart
class AnalysisViewModel extends ChangeNotifier {
  final AnalysisApiService apiService;
  
  bool _isSubmitting = false;
  String? _error;
  
  bool get isSubmitting => _isSubmitting;
  String? get error => _error;
  
  Future<void> submitAnalysis(String ticker, String tradeDate) async {
    _isSubmitting = true;
    _error = null;
    notifyListeners();
    
    try {
      final status = await apiService.submitAnalysis(
        ticker: ticker,
        tradeDate: tradeDate,
      );
      
      // Navigate to history tab to see job
      // Job will appear via polling
    } catch (e) {
      _error = 'Failed to submit: ${e.toString()}';
    } finally {
      _isSubmitting = false;
      notifyListeners();
    }
  }
}

// lib/analysis/view_models/history_view_model.dart
class HistoryViewModel extends ChangeNotifier {
  final StatusPollingService pollingService;
  
  List<AnalysisStatus> _jobs = [];
  bool _isLoading = true;
  
  List<AnalysisStatus> get jobs => _jobs;
  bool get isLoading => _isLoading;
  
  HistoryViewModel({required this.pollingService}) {
    _initPolling();
  }
  
  void _initPolling() {
    pollingService.statusStream.listen((jobs) {
      _jobs = jobs;
      _isLoading = false;
      notifyListeners();
    });
    
    pollingService.startPolling();
  }
  
  void refresh() {
    _isLoading = true;
    notifyListeners();
    pollingService.startPolling();
  }
  
  @override
  void dispose() {
    pollingService.stopPolling();
    super.dispose();
  }
}
```

### 5. Fixed UI Components

```dart
// lib/analysis/widgets/job_card.dart
class JobCard extends StatelessWidget {
  final AnalysisStatus job;
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Fixed overflow with Flexible widgets
            Row(
              children: [
                Expanded(
                  child: Text(
                    job.ticker,
                    style: Theme.of(context).textTheme.titleMedium,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                _StatusChip(status: job.status),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Flexible(
                  child: Text(
                    'Date: ${job.tradeDate}',
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (job.duration != null) ...[
                  const SizedBox(width: 16),
                  Text('${(job.duration! / 1000).toStringAsFixed(1)}s'),
                ],
              ],
            ),
            if (job.traceId != null) ...[
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => _openLangGraphTrace(job.traceId!),
                child: const Text('View Trace'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

### 6. History Screen

```dart
// lib/analysis/screens/history_screen.dart
class HistoryScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<HistoryViewModel>(
      builder: (context, viewModel, child) {
        if (viewModel.isLoading && viewModel.jobs.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }
        
        return RefreshIndicator(
          onRefresh: () async => viewModel.refresh(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: viewModel.jobs.length,
            itemBuilder: (context, index) {
              return JobCard(job: viewModel.jobs[index]);
            },
          ),
        );
      },
    );
  }
}
```

## Implementation Plan

### Phase 1: Server API Integration (2 days)
- [ ] Create AnalysisApiService
- [ ] Implement API endpoints
- [ ] Add error handling
- [ ] Test with Postman/curl

### Phase 2: Simplify Models (1 day)
- [ ] Create simplified models
- [ ] Remove complex job states
- [ ] Remove priority levels
- [ ] Update DTOs

### Phase 3: UI Implementation (2 days)
- [ ] Create analysis submission screen
- [ ] Create history screen
- [ ] Fix overflow issues
- [ ] Add loading states

### Phase 4: Polling & Real-time Updates (1 day)
- [ ] Implement StatusPollingService
- [ ] Add stream-based updates
- [ ] Handle connection errors
- [ ] Optimize polling

### Phase 5: Cleanup (1 day)
- [ ] Remove old job queue code
- [ ] Remove Hive persistence
- [ ] Remove isolate processing
- [ ] Update tests

## Testing Strategy

### Unit Tests
```dart
// test/analysis/services/analysis_api_service_test.dart
group('AnalysisApiService', () {
  test('submitAnalysis sends correct request', () async {
    // Mock Dio
    // Verify POST /api/analyze
    // Check request body
    // Verify response parsing
  });
  
  test('handles API errors gracefully', () async {
    // Mock error responses
    // Verify error handling
  });
});
```

### Integration Tests
```dart
// integration_test/analysis_flow_test.dart
testWidgets('Complete analysis flow', (tester) async {
  // Submit analysis
  // Verify API call
  // Navigate to history
  // Verify job appears
  // Wait for completion
  // Verify status update
});
```

### Manual Testing Checklist
- [ ] Submit job → Appears in LangGraph Studio
- [ ] History updates every 5 seconds
- [ ] No UI overflow on any screen size
- [ ] Error messages are user-friendly
- [ ] Offline behavior is graceful

## Migration Checklist

### Remove
- [ ] JobQueueManager
- [ ] JobProcessor
- [ ] IsolateManager
- [ ] JobRetryPolicy
- [ ] RetryScheduler
- [ ] Complex job entities
- [ ] Hive repositories
- [ ] Background processing

### Add
- [ ] AnalysisApiService
- [ ] StatusPollingService
- [ ] Simplified models
- [ ] History screen
- [ ] API error handling

### Update
- [ ] Submission flow
- [ ] Navigation structure
- [ ] Test suites
- [ ] Documentation