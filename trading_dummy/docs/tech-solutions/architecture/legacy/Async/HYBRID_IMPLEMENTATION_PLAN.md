# Hybrid Implementation Plan: Iterative Migration

## Overview

This plan details how to iterate on the existing architecture, keeping 60% of the code while achieving all new requirements.

## Stage 1: API Integration Layer (Day 1)

### 1.1 Create Analysis API Service

```dart
// lib/jobs/infrastructure/services/analysis_api_service.dart
class AnalysisApiService {
  final Dio dio;
  final String baseUrl;
  
  Future<AnalysisJob> submitToServer(String ticker, String tradeDate) async {
    final response = await dio.post(
      '$baseUrl/api/analyze',
      data: {'ticker': ticker, 'tradeDate': tradeDate},
    );
    
    // Convert server response to existing AnalysisJob model
    return AnalysisJob(
      id: response.data['jobId'],
      ticker: ticker,
      tradeDate: tradeDate,
      status: JobStatus.running, // Server starts processing immediately
      priority: JobPriority.normal, // Ignore priority for now
      createdAt: DateTime.now(),
      retryCount: 0,
    );
  }
  
  Future<List<AnalysisJob>> getJobHistory() async {
    final response = await dio.get('$baseUrl/api/jobs');
    
    return (response.data['jobs'] as List).map((json) => 
      AnalysisJob(
        id: json['jobId'],
        ticker: json['ticker'],
        tradeDate: json['tradeDate'],
        status: _mapServerStatus(json['status']),
        priority: JobPriority.normal,
        createdAt: DateTime.parse(json['submittedAt']),
        completedAt: json['completedAt'] != null 
          ? DateTime.parse(json['completedAt']) 
          : null,
        resultId: json['resultId'],
        errorMessage: json['error'],
      )
    ).toList();
  }
}
```

### 1.2 Add Feature Flag

```dart
// lib/core/config/feature_flags.dart
class FeatureFlags {
  static bool get useServerQueue => 
    const bool.fromEnvironment('USE_SERVER_QUEUE', defaultValue: false);
  
  static bool get enableLangGraphTrace =>
    const bool.fromEnvironment('ENABLE_LANGGRAPH_TRACE', defaultValue: true);
}
```

### 1.3 Modify QueueAnalysisUseCase

```dart
// lib/jobs/application/use_cases/queue_analysis_use_case.dart
class QueueAnalysisUseCase {
  final JobQueueManager _queueManager;
  final IJobRepository _repository; 
  final JobEventBus _eventBus;
  final AnalysisApiService _apiService; // NEW
  
  Future<AnalysisJob> execute(String ticker, String tradeDate, {
    JobPriority priority = JobPriority.normal,
  }) async {
    // Feature flag check
    if (FeatureFlags.useServerQueue) {
      // NEW PATH: Direct server submission
      try {
        final job = await _apiService.submitToServer(ticker, tradeDate);
        
        // Keep using events for UI updates
        _eventBus.publish(JobQueuedEvent(job));
        
        // Store in local repository for UI display
        await _repository.save(job);
        
        return job;
      } catch (e) {
        throw AnalysisException('Failed to submit to server: $e');
      }
    } else {
      // OLD PATH: Local queue (unchanged)
      final job = AnalysisJob(
        id: const Uuid().v4(),
        ticker: ticker,
        tradeDate: tradeDate,
        status: JobStatus.pending,
        priority: priority,
        createdAt: DateTime.now(),
        retryCount: 0,
      );
      
      await _repository.save(job);
      await _queueManager.enqueue(job);
      
      return job;
    }
  }
}
```

## Stage 2: Add Server Polling (Day 2)

### 2.1 Create Server Polling Service

```dart
// lib/jobs/infrastructure/services/server_polling_service.dart
class ServerPollingService {
  final AnalysisApiService _apiService;
  final JobEventBus _eventBus;
  final IJobRepository _repository;
  
  Timer? _pollingTimer;
  Set<String> _knownJobIds = {};
  
  void startPolling() {
    _pollingTimer?.cancel();
    
    // Initial poll
    _pollServer();
    
    // Schedule periodic polls
    _pollingTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      _pollServer();
    });
  }
  
  Future<void> _pollServer() async {
    try {
      final serverJobs = await _apiService.getJobHistory();
      
      for (final job in serverJobs) {
        // Check if we need to update local state
        final localJob = await _repository.getById(job.id);
        
        if (localJob == null) {
          // New job from server
          await _repository.save(job);
          _eventBus.publish(JobQueuedEvent(job));
        } else if (localJob.status != job.status) {
          // Status changed
          await _repository.update(job);
          
          // Publish appropriate event
          switch (job.status) {
            case JobStatus.running:
              _eventBus.publish(JobStartedEvent(job));
              break;
            case JobStatus.completed:
              _eventBus.publish(JobCompletedEvent(job, resultId: job.resultId));
              break;
            case JobStatus.failed:
              _eventBus.publish(JobFailedEvent(job, 
                errorMessage: job.errorMessage ?? 'Unknown error',
                willRetry: false,
              ));
              break;
            default:
              break;
          }
        }
      }
    } catch (e) {
      AppLogger.error('ServerPollingService', 'Polling failed', e);
      // Continue polling even on error
    }
  }
  
  void stopPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = null;
  }
}
```

### 2.2 Initialize Polling in Main

```dart
// lib/main.dart
void main() async {
  // ... existing setup ...
  
  if (FeatureFlags.useServerQueue) {
    // Initialize server polling
    final pollingService = ServerPollingService(
      apiService: getIt<AnalysisApiService>(),
      eventBus: getIt<JobEventBus>(),
      repository: getIt<IJobRepository>(),
    );
    pollingService.startPolling();
  }
  
  runApp(MyApp());
}
```

## Stage 3: Simplify Components (Day 3)

### 3.1 Update JobQueueViewModel

```dart
// lib/jobs/presentation/view_models/job_queue_view_model.dart
class JobQueueViewModel extends ChangeNotifier {
  // KEEP: All existing public methods and properties
  
  Future<void> submitAnalysis(String ticker, String tradeDate, {
    JobPriority priority = JobPriority.normal,
  }) async {
    // Same public interface, different implementation
    _clearError();
    _setLoading(true);
    
    try {
      // Now uses modified QueueAnalysisUseCase
      final job = await queueAnalysis.execute(ticker, tradeDate, priority: priority);
      
      // UI update logic remains the same
      _activeJobs.add(job);
      _sortActiveJobs();
      
      notifyListeners();
    } catch (e) {
      _setError('Failed to submit analysis: ${e.toString()}');
    } finally {
      _setLoading(false);
    }
  }
  
  // KEEP: Event handling unchanged
  void onJobEvent(JobEvent event) {
    // Exact same implementation
  }
}
```

### 3.2 Add History Screen

```dart
// lib/jobs/presentation/screens/job_history_screen.dart
class JobHistoryScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<JobQueueViewModel>(
      builder: (context, viewModel, child) {
        final allJobs = [
          ...viewModel.activeJobs,
          ...viewModel.completedJobs,
          ...viewModel.failedJobs,
        ]..sort((a, b) => b.createdAt.compareTo(a.createdAt));
        
        return Scaffold(
          appBar: AppBar(title: const Text('Job History')),
          body: RefreshIndicator(
            onRefresh: () async => viewModel.refreshJobs(),
            child: ListView.builder(
              itemCount: allJobs.length,
              itemBuilder: (context, index) {
                final job = allJobs[index];
                return JobStatusCard(
                  job: job,
                  onTap: () => _viewJobDetails(context, job),
                );
              },
            ),
          ),
        );
      },
    );
  }
}
```

## Stage 4: Cleanup & Migration (Day 4)

### 4.1 Remove Unused Code (When Stable)

```yaml
# Files to remove after verification
TO_REMOVE:
  - lib/jobs/infrastructure/services/job_processor.dart
  - lib/jobs/infrastructure/services/isolate_manager.dart
  - lib/jobs/infrastructure/services/retry_scheduler.dart
  - lib/jobs/domain/services/job_retry_policy.dart
  
# Files to simplify
TO_SIMPLIFY:
  - lib/jobs/domain/value_objects/job_priority.dart # Remove enum
  - lib/jobs/infrastructure/services/job_queue_manager.dart # Remove if fully migrated
```

### 4.2 Update Tests

```dart
// test/jobs/application/use_cases/queue_analysis_use_case_test.dart
group('QueueAnalysisUseCase', () {
  group('with server queue', () {
    setUp(() {
      // Mock AnalysisApiService
    });
    
    test('submits directly to server', () async {
      // Test server path
    });
  });
  
  group('with local queue', () {
    // Keep existing tests
  });
});
```

## Migration Checklist

### Pre-Migration
- [ ] Set up API endpoints on server
- [ ] Test server endpoints manually
- [ ] Create feature flags
- [ ] Brief team on approach

### Stage 1 (Day 1)
- [ ] Implement AnalysisApiService
- [ ] Add feature flag support
- [ ] Modify QueueAnalysisUseCase
- [ ] Test both paths work
- [ ] Deploy with flag OFF

### Stage 2 (Day 2)
- [ ] Implement ServerPollingService
- [ ] Initialize in main.dart
- [ ] Test polling updates UI
- [ ] Enable flag for test users
- [ ] Monitor server load

### Stage 3 (Day 3)
- [ ] Add history screen
- [ ] Fix UI overflow issues
- [ ] Update navigation
- [ ] Test end-to-end flow
- [ ] Enable flag for 50% users

### Stage 4 (Day 4)
- [ ] Monitor for issues
- [ ] Enable flag for all users
- [ ] Remove dead code
- [ ] Update documentation
- [ ] Final testing

## Rollback Plan

If issues arise at any stage:

```dart
// Quick rollback
FeatureFlags.useServerQueue = false; // Revert to local queue

// UI continues working with local queue
// No data loss
// Fix issues and try again
```

## Success Metrics

1. **No Breaking Changes** - UI works identically
2. **Performance** - Submission <200ms
3. **Reliability** - No lost jobs
4. **User Satisfaction** - No complaints
5. **Code Quality** - Tests still pass

## Conclusion

This hybrid approach achieves all requirements while:
- Keeping 60% of existing code
- Maintaining UI compatibility
- Allowing easy rollback
- Shipping value incrementally
- Reducing risk significantly

The key insight: We don't need to throw away good code, just redirect where it sends data.