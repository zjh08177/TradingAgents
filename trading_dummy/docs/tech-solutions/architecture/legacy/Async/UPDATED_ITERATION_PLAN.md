# Updated Iteration Plan: LangGraph Background Runs

## Overview

With LangGraph's native background run support, our iteration becomes even simpler. We replace the local queue with LangGraph's async execution, getting better reliability and visibility.

## Architecture Comparison

### Before: Complex Client Queue
```
Flutter App → Local Queue → Isolates → Eventually Server
```

### After: Direct LangGraph Integration
```
Flutter App → Server API → LangGraph Background Run → Immediate Response
```

## Implementation Plan

### Stage 1: Add LangGraph API Layer (Day 1)

#### 1.1 Create LangGraph API Service

```dart
// lib/jobs/infrastructure/services/langgraph_api_service.dart
class LangGraphApiService {
  final Dio dio;
  final String baseUrl;
  
  /// Start analysis - returns immediately with run ID
  Future<AnalysisRun> startAnalysis({
    required String ticker,
    required String tradeDate,
  }) async {
    final response = await dio.post(
      '$baseUrl/api/analyze',
      data: {'ticker': ticker, 'tradeDate': tradeDate},
    );
    
    // Convert to our existing AnalysisJob model for compatibility
    final run = AnalysisRun.fromJson(response.data);
    
    return AnalysisJob(
      id: run.runId,
      ticker: ticker,
      tradeDate: tradeDate,
      status: _mapRunStatus(run.status),
      priority: JobPriority.normal, // Ignore for now
      createdAt: run.createdAt,
      retryCount: 0,
      // Store LangGraph-specific data
      metadata: {
        'threadId': run.threadId,
        'langGraphStatus': run.status.name,
      },
    );
  }
  
  JobStatus _mapRunStatus(RunStatus runStatus) {
    switch (runStatus) {
      case RunStatus.pending:
        return JobStatus.queued;
      case RunStatus.running:
        return JobStatus.running;
      case RunStatus.success:
        return JobStatus.completed;
      case RunStatus.error:
        return JobStatus.failed;
    }
  }
}
```

#### 1.2 Update QueueAnalysisUseCase

```dart
// lib/jobs/application/use_cases/queue_analysis_use_case.dart
class QueueAnalysisUseCase {
  final JobQueueManager _queueManager;
  final IJobRepository _repository;
  final JobEventBus _eventBus;
  final LangGraphApiService? _langGraphApi; // NEW - optional for gradual migration
  
  Future<AnalysisJob> execute(String ticker, String tradeDate, {
    JobPriority priority = JobPriority.normal,
  }) async {
    // Feature flag check
    if (FeatureFlags.useLangGraphBackground) {
      // NEW PATH: Direct LangGraph submission
      try {
        final job = await _langGraphApi!.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        );
        
        // Store locally for UI display
        await _repository.save(job);
        
        // Emit event for UI update (reuse existing event system!)
        _eventBus.publish(JobQueuedEvent(job));
        
        // Start polling automatically
        _startPollingForJob(job);
        
        return job;
      } catch (e) {
        throw AnalysisException('Failed to start LangGraph analysis: $e');
      }
    } else {
      // OLD PATH: Local queue (unchanged for safety)
      return _existingImplementation(ticker, tradeDate, priority);
    }
  }
  
  void _startPollingForJob(AnalysisJob job) {
    // Polling will update job status via events
    getIt<RunPollingService>().pollRun(job.id);
  }
}
```

### Stage 2: Add Smart Polling (Day 2)

#### 2.1 Create Run Polling Service

```dart
// lib/jobs/infrastructure/services/run_polling_service.dart
class RunPollingService {
  final LangGraphApiService _apiService;
  final JobEventBus _eventBus;
  final IJobRepository _repository;
  
  final Map<String, Timer> _activePolls = {};
  
  void pollRun(String runId) {
    if (_activePolls.containsKey(runId)) return; // Already polling
    
    // Start with fast polling, then slow down
    int pollCount = 0;
    
    void poll() async {
      try {
        final updatedJob = await _apiService.getRunStatus(runId);
        
        // Update repository
        await _repository.update(updatedJob);
        
        // Emit appropriate event based on status change
        _emitStatusEvent(updatedJob);
        
        // Stop polling if complete
        if (updatedJob.status == JobStatus.completed || 
            updatedJob.status == JobStatus.failed) {
          _activePolls[runId]?.cancel();
          _activePolls.remove(runId);
        }
      } catch (e) {
        AppLogger.error('RunPollingService', 'Poll failed for $runId', e);
      }
    }
    
    // Initial poll
    poll();
    
    // Schedule periodic polls with backoff
    _activePolls[runId] = Timer.periodic(
      _getInterval(pollCount++),
      (_) => poll(),
    );
  }
  
  Duration _getInterval(int count) {
    if (count < 5) return Duration(seconds: 2);    // First 10s: every 2s
    if (count < 15) return Duration(seconds: 5);   // Next 50s: every 5s
    return Duration(seconds: 10);                   // Then: every 10s
  }
  
  void _emitStatusEvent(AnalysisJob job) {
    // Reuse existing events!
    switch (job.status) {
      case JobStatus.running:
        _eventBus.publish(JobStartedEvent(job));
        break;
      case JobStatus.completed:
        _eventBus.publish(JobCompletedEvent(job, resultId: job.resultId));
        break;
      case JobStatus.failed:
        _eventBus.publish(JobFailedEvent(
          job,
          errorMessage: job.errorMessage ?? 'Analysis failed',
          willRetry: false, // LangGraph handles retries
        ));
        break;
      default:
        break;
    }
  }
  
  void dispose() {
    for (final timer in _activePolls.values) {
      timer.cancel();
    }
    _activePolls.clear();
  }
}
```

### Stage 3: UI Remains Unchanged! (Day 3)

The beauty of this approach is that the UI doesn't need to change:

```dart
// lib/jobs/presentation/view_models/job_queue_view_model.dart
class JobQueueViewModel extends ChangeNotifier {
  // NO CHANGES NEEDED!
  // The ViewModel already listens to JobEvents
  // It will automatically update when polling emits events
  
  void onJobEvent(JobEvent event) {
    // This existing method handles all the UI updates
    // Whether events come from local queue or LangGraph polling
  }
}
```

### Stage 4: Add History View (Day 3)

```dart
// lib/jobs/presentation/screens/job_history_screen.dart
class JobHistoryScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<JobQueueViewModel>(
      builder: (context, viewModel, child) {
        // Reuse existing JobStatusCard widgets!
        return ListView.builder(
          itemCount: viewModel.allJobs.length,
          itemBuilder: (context, index) {
            final job = viewModel.allJobs[index];
            
            return JobStatusCard(
              job: job,
              onTap: () {
                // If completed, navigate to results
                if (job.status == JobStatus.completed) {
                  _navigateToResults(context, job);
                }
              },
            );
          },
        );
      },
    );
  }
}
```

### Stage 5: Cleanup (Day 4)

Once stable with LangGraph:
1. Remove `JobProcessor`
2. Remove `IsolateManager`
3. Remove `RetryScheduler`
4. Simplify `JobQueueManager` to just track running count

## Feature Flags

```dart
class FeatureFlags {
  /// Use LangGraph background runs instead of local queue
  static bool get useLangGraphBackground =>
    const bool.fromEnvironment('USE_LANGGRAPH_BACKGROUND', defaultValue: false);
  
  /// Show LangGraph trace links in UI
  static bool get showLangGraphTraces =>
    const bool.fromEnvironment('SHOW_LANGGRAPH_TRACES', defaultValue: true);
}
```

## Migration Strategy

### Phase 1: Deploy with Flag OFF
- All code deployed but inactive
- Existing queue continues working
- No user impact

### Phase 2: Test with Internal Users
- Enable flag for developers
- Monitor LangGraph performance
- Verify trace visibility

### Phase 3: Gradual Rollout
- 10% of users → 50% → 100%
- Monitor error rates
- Check LangGraph costs

### Phase 4: Cleanup
- Remove old queue code
- Remove feature flags
- Celebrate! 🎉

## Benefits of This Approach

### 1. Minimal Code Changes
- Add 2 new services
- Modify 1 use case
- Everything else unchanged

### 2. Reuse Everything
- ✅ Existing UI components
- ✅ Existing event system
- ✅ Existing ViewModels
- ✅ Existing test structure

### 3. Better Than Original
- Real async execution
- LangGraph Studio visibility
- Built-in retry handling
- Production-grade infrastructure

### 4. Risk Mitigation
- Feature flag for instant rollback
- Gradual rollout possible
- No data migration needed
- Can run both systems in parallel

## Implementation Timeline

**Monday (Day 1)**
- [ ] Create LangGraphApiService
- [ ] Add server endpoints
- [ ] Update QueueAnalysisUseCase
- [ ] Deploy with flag OFF

**Tuesday (Day 2)**
- [ ] Create RunPollingService
- [ ] Wire up polling to events
- [ ] Test end-to-end flow
- [ ] Enable for dev team

**Wednesday (Day 3)**
- [ ] Add history screen
- [ ] Fix any UI issues
- [ ] Performance testing
- [ ] Enable for 10% users

**Thursday (Day 4)**
- [ ] Monitor and fix issues
- [ ] Gradual rollout
- [ ] Remove old code
- [ ] Documentation

## Success Metrics

1. **Submission latency** < 200ms
2. **Polling efficiency** < 1% CPU
3. **LangGraph traces** visible for all runs
4. **Zero lost jobs**
5. **User satisfaction** maintained

## Conclusion

LangGraph's background run support makes our iteration even better. We get:
- Simpler implementation
- Better reliability
- Full visibility
- Less code to maintain

The key insight remains: iterate on what works, replace only what doesn't. With LangGraph, we're replacing even less than before!