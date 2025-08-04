# Async Stock Analysis Jobs - Developer Guide

## Architecture Overview

The async job system is built using Clean Architecture principles with clear separation between domain logic, application services, infrastructure, and presentation layers.

### Core Components

```
Domain Layer (Business Logic)
├── Entities: AnalysisJob
├── Value Objects: JobStatus, JobPriority
├── Services: JobRetryPolicy
└── Repositories: IJobRepository

Application Layer (Use Cases)
├── QueueAnalysisUseCase
├── GetJobStatusUseCase
├── CancelJobUseCase
└── GetJobHistoryUseCase

Infrastructure Layer (Implementation)
├── Repositories: HiveJobRepository
├── Services: JobQueueManager, RetryScheduler, JobMetricsService
├── Events: JobEventBus
└── Models: HiveAnalysisJob

Presentation Layer (UI)
├── ViewModels: JobQueueViewModel, JobListViewModel
├── Widgets: JobSubmissionWidget, ActiveJobsList, JobStatusCard
└── Screens: JobQueueScreen, JobHistoryScreen
```

## Domain Layer

### AnalysisJob Entity

The core domain entity representing a stock analysis job:

```dart
class AnalysisJob {
  final String id;              // Unique job identifier
  final String ticker;          // Stock ticker symbol
  final String tradeDate;       // Analysis date (YYYY-MM-DD)
  final JobStatus status;       // Current job status
  final JobPriority priority;   // Processing priority
  final DateTime createdAt;     // Job creation timestamp
  final DateTime? startedAt;    // Processing start time
  final DateTime? completedAt;  // Processing completion time
  final String? resultId;       // Result identifier (if completed)
  final String? errorMessage;   // Error details (if failed)
  final int retryCount;         // Current retry attempt
  final int maxRetries;         // Maximum retry attempts
}
```

### Value Objects

#### JobStatus Enum
```dart
enum JobStatus {
  pending,    // Newly created, not yet queued
  queued,     // In queue waiting for processing
  running,    // Currently being processed
  completed,  // Successfully finished
  failed,     // Processing failed
  cancelled   // Cancelled by user or system
}
```

#### JobPriority Enum
```dart
enum JobPriority {
  low,        // Background processing
  normal,     // Standard processing (default)
  high,       // Expedited processing
  critical    // Immediate processing
}
```

### Repository Interface

```dart
abstract class IJobRepository {
  Future<void> save(AnalysisJob job);
  Future<AnalysisJob?> getById(String id);
  Future<List<AnalysisJob>> getAll();
  Future<List<AnalysisJob>> getByStatus(JobStatus status);
  Future<List<AnalysisJob>> getActiveJobs();
  Future<void> update(AnalysisJob job);
  Future<void> delete(String id);
  Future<Map<JobStatus, int>> countByStatus();
  Future<int> deleteCompletedBefore(DateTime cutoffDate);
  Future<void> clearAll();
}
```

## Application Layer

### Use Cases

#### QueueAnalysisUseCase
Submits a new analysis job to the queue:

```dart
class QueueAnalysisUseCase {
  final IJobRepository repository;
  final JobQueueManager queueManager;
  
  Future<AnalysisJob> execute(String ticker, String tradeDate, {
    JobPriority priority = JobPriority.normal,
  }) async {
    // Validate input
    // Create job entity
    // Save to repository
    // Enqueue for processing
    // Return job
  }
}
```

#### GetJobStatusUseCase
Retrieves current status of a job:

```dart
class GetJobStatusUseCase {
  final IJobRepository repository;
  
  Future<AnalysisJob?> execute(String jobId) async {
    return await repository.getById(jobId);
  }
}
```

#### CancelJobUseCase
Cancels a pending or queued job:

```dart
class CancelJobUseCase {
  final IJobRepository repository;
  final JobQueueManager queueManager;
  
  Future<bool> execute(String jobId) async {
    // Check if job can be cancelled
    // Remove from queue if pending/queued
    // Update status to cancelled
    // Publish cancellation event
  }
}
```

## Infrastructure Layer

### JobQueueManager

Core service managing the job processing queue:

```dart
class JobQueueManager {
  // Priority-based FIFO queuing
  // Concurrency control (max 5 concurrent jobs)
  // Thread-safe operations with locking
  // Event publishing for state changes
  
  Future<void> enqueue(AnalysisJob job);
  Future<AnalysisJob?> dequeue();
  Future<void> requeue(AnalysisJob job);
  Future<void> markCompleted(AnalysisJob job, String resultId);
  Future<void> markFailed(AnalysisJob job, String errorMessage);
  Future<bool> cancel(String jobId);
}
```

### RetryScheduler

Manages automatic retry of failed jobs:

```dart
class RetryScheduler {
  // Timer-based retry scheduling
  // Exponential backoff with jitter
  // Configurable retry policies
  // Automatic cleanup of completed timers
  
  Future<void> scheduleRetry(AnalysisJob job);
  Future<void> cancelRetry(String jobId);
  DateTime? getScheduledRetryTime(String jobId);
  RetryStatistics getStatistics();
}
```

### JobRetryPolicy

Domain service defining retry strategies:

```dart
class JobRetryPolicy {
  final int maxRetries;               // Default: 3
  final Duration baseDelay;           // Default: 30 seconds
  final Duration maxDelay;            // Default: 30 minutes
  final double backoffMultiplier;     // Default: 2.0
  final double jitterFactor;          // Default: 0.2
  
  bool shouldRetry(AnalysisJob job);
  Duration getRetryDelay(int attemptNumber);
  DateTime? getNextRetryTime(AnalysisJob job);
}
```

### JobMetricsService

Comprehensive metrics and monitoring:

```dart
class JobMetricsService {
  // Real-time performance tracking
  // Error pattern analysis
  // Throughput monitoring
  // System health indicators
  
  void recordJobCompletion(AnalysisJob job);
  void recordJobFailure(AnalysisJob job, String errorMessage);
  Future<JobSystemMetrics> getSystemMetrics();
  Future<PerformanceAnalytics> getPerformanceAnalytics();
  ErrorAnalysisReport getErrorAnalysis();
}
```

### Event System

Event-driven architecture for loose coupling:

```dart
// Event Types
abstract class JobEvent {}
class JobQueuedEvent extends JobEvent {}
class JobStartedEvent extends JobEvent {}
class JobCompletedEvent extends JobEvent {}
class JobFailedEvent extends JobEvent {}
class JobCancelledEvent extends JobEvent {}
class JobRequeuedEvent extends JobEvent {}

// Event Bus (Singleton)
class JobEventBus {
  void publish(JobEvent event);
  Stream<T> on<T extends JobEvent>();
}
```

## Persistence Layer

### Hive Implementation

Using Hive for local persistence with type adapters:

```dart
@HiveType(typeId: 1)
class HiveAnalysisJob extends HiveObject {
  @HiveField(0) String id;
  @HiveField(1) String ticker;
  @HiveField(2) String tradeDate;
  @HiveField(3) int statusIndex;
  @HiveField(4) int priorityIndex;
  @HiveField(5) int createdAtMillis;
  @HiveField(6) int? startedAtMillis;
  @HiveField(7) int? completedAtMillis;
  @HiveField(8) String? resultId;
  @HiveField(9) String? errorMessage;
  @HiveField(10) int retryCount;
  @HiveField(11) int maxRetries;
}
```

### Repository Implementation

```dart
class HiveJobRepository implements IJobRepository {
  static const String _boxName = 'analysis_jobs';
  late Box<HiveAnalysisJob> _box;
  
  Future<void> init() async {
    _box = await Hive.openBox<HiveAnalysisJob>(_boxName);
  }
  
  // All interface methods implemented with Hive operations
  // Domain-Infrastructure mapping via extension methods
}
```

## Presentation Layer

### ViewModels

#### JobQueueViewModel
```dart
class JobQueueViewModel extends ChangeNotifier {
  final QueueAnalysisUseCase _queueAnalysis;
  final GetJobStatusUseCase _getJobStatus;
  final CancelJobUseCase _cancelJob;
  
  List<AnalysisJob> _activeJobs = [];
  List<AnalysisJob> _completedJobs = [];
  bool _isLoading = false;
  String? _error;
  
  // Public interface for UI
  Future<void> submitAnalysis(String ticker, String tradeDate);
  Future<void> cancelJob(String jobId);
  Future<void> refreshJobs();
  void onJobEvent(JobEvent event);
}
```

#### JobListViewModel
```dart
class JobListViewModel extends ChangeNotifier {
  // Advanced job display capabilities
  // Filtering by status, priority, date range
  // Sorting by various criteria
  // Search functionality
  // Pagination for large datasets
  
  Future<void> applyFilter(JobFilter filter);
  Future<void> setSortCriteria(JobSortCriteria criteria);
  Future<void> searchJobs(String query);
  Future<void> loadMoreJobs();
}
```

### UI Widgets

#### JobSubmissionWidget
```dart
class JobSubmissionWidget extends StatefulWidget {
  // Form for submitting new analysis jobs
  // Ticker symbol validation
  // Date picker for trade date
  // Priority selection
  // Submit button with loading states
}
```

#### ActiveJobsList
```dart
class ActiveJobsList extends StatelessWidget {
  // Real-time list of active jobs
  // Status indicators and progress
  // Cancel action for pending jobs
  // Pull-to-refresh capability
  // Auto-refresh every 30 seconds
}
```

#### JobStatusCard
```dart
class JobStatusCard extends StatelessWidget {
  // Individual job display card
  // Status-specific styling and icons
  // Action buttons based on job state
  // Tap to view details/results
  // Swipe actions for quick operations
}
```

## Background Processing

### Isolate Architecture

```dart
// Main Isolate
// ├── UI Thread (Flutter widgets, user interactions)
// ├── Job Queue Manager (coordination)
// └── Event Bus (communication)

// Worker Isolates (up to 5 concurrent)
// ├── Job Processor (actual analysis work)
// ├── LangGraph Service (analysis logic)
// └── Result Generation (report creation)
```

### Isolate Manager

```dart
class IsolateManager {
  final int maxWorkers;
  final List<IsolateWorker> _workers = [];
  final Queue<AnalysisJob> _pendingJobs = Queue();
  
  Future<void> initialize();
  Future<void> processJob(AnalysisJob job);
  Future<void> dispose();
  
  // Worker lifecycle management
  // Load balancing across workers
  // Error handling and recovery
  // Resource cleanup
}
```

## Testing Strategy

### Unit Tests (90%+ Coverage)

```dart
// Domain Layer Tests
test/jobs/domain/
├── entities/analysis_job_test.dart
├── value_objects/job_status_test.dart
├── value_objects/job_priority_test.dart
└── services/job_retry_policy_test.dart

// Application Layer Tests
test/jobs/application/
├── use_cases/queue_analysis_use_case_test.dart
├── use_cases/get_job_status_use_case_test.dart
└── use_cases/cancel_job_use_case_test.dart

// Infrastructure Layer Tests
test/jobs/infrastructure/
├── repositories/hive_job_repository_test.dart
├── services/job_queue_manager_test.dart
├── services/retry_scheduler_test.dart
└── services/job_metrics_service_test.dart
```

### Integration Tests

```dart
integration_test/
├── jobs_e2e_test.dart              // End-to-end workflows
├── performance_test.dart           // Performance benchmarks
└── load_test.dart                  // Load testing scenarios
```

### Widget Tests

```dart
test/jobs/presentation/
├── view_models/job_queue_view_model_test.dart
├── widgets/job_submission_widget_test.dart
├── widgets/active_jobs_list_test.dart
└── widgets/job_status_card_test.dart
```

## Performance Optimization

### Memory Management

- **Object Pooling**: Reuse job objects where possible
- **Lazy Loading**: Load job details only when needed
- **Pagination**: Limit UI data display to prevent memory issues
- **Cleanup**: Regular cleanup of old completed jobs

### Database Optimization

- **Indexing**: Hive boxes optimized for common queries
- **Batch Operations**: Group database operations where possible
- **Async Operations**: All I/O operations are asynchronous
- **Caching**: In-memory cache for frequently accessed jobs

### UI Performance

- **ListView.builder**: Efficient scrolling for large job lists
- **State Management**: Minimal rebuilds using proper state management
- **Debouncing**: Debounce search and filter operations
- **Background Updates**: UI updates happen on background timer

## Error Handling

### Error Categories

1. **Transient Errors**: Network timeouts, temporary service unavailability
   - **Handling**: Automatic retry with exponential backoff
   - **User Experience**: Show retry progress, eventual success/failure

2. **Permanent Errors**: Invalid ticker, authentication failure
   - **Handling**: No automatic retry, user notification
   - **User Experience**: Clear error message, manual retry option

3. **System Errors**: Out of memory, database corruption
   - **Handling**: Graceful degradation, error reporting
   - **User Experience**: Fallback UI, data recovery options

### Error Recovery

```dart
class ErrorRecoveryManager {
  // Automatic error classification
  // Recovery strategy selection
  // Fallback mechanism activation
  // User notification management
  
  Future<void> handleError(JobError error);
  Future<bool> attemptRecovery(AnalysisJob job);
  void notifyUser(ErrorNotification notification);
}
```

## Monitoring & Observability

### Metrics Collection

- **Performance Metrics**: Job completion times, throughput rates
- **Error Metrics**: Failure rates, error patterns, retry success
- **System Metrics**: Memory usage, CPU utilization, queue depth
- **User Metrics**: Job submission patterns, cancellation rates

### Health Monitoring

```dart
class HealthMonitor {
  // System health scoring (0-100)
  // Component health checks
  // Performance threshold monitoring
  // Automatic alerts for degradation
  
  Future<HealthReport> checkSystemHealth();
  Stream<HealthAlert> get healthAlerts;
  Future<void> triggerHealthCheck();
}
```

### Logging Strategy

- **Structured Logging**: JSON format for easy parsing
- **Log Levels**: ERROR, WARN, INFO, DEBUG with appropriate filtering
- **Context Preservation**: Include job ID, user context in all logs
- **Performance Logging**: Track timing for all major operations

## Configuration & Deployment

### Environment Configuration

```dart
class JobSystemConfig {
  static const int maxConcurrentJobs = 5;
  static const Duration defaultJobTimeout = Duration(minutes: 10);
  static const Duration retryBaseDelay = Duration(seconds: 30);
  static const int defaultMaxRetries = 3;
  static const Duration metricsCollectionInterval = Duration(minutes: 1);
}
```

### Feature Flags

```dart
class JobSystemFeatures {
  static bool enableMetricsCollection = true;
  static bool enableNotifications = true;
  static bool enableAutoRetry = true;
  static bool enablePriorityQueue = true;
  static bool enableLoadTesting = false;
}
```

### Production Deployment

1. **Database Migration**: Hive schema migration scripts
2. **Performance Tuning**: Optimized configuration for production
3. **Monitoring Setup**: Metrics collection and alerting
4. **Error Tracking**: Crash reporting and error aggregation
5. **A/B Testing**: Feature flag framework for controlled rollouts

## Security Considerations

### Data Protection

- **Local Storage**: Hive database encrypted at rest
- **Memory Protection**: Sensitive data cleared after use
- **Input Validation**: All user inputs validated and sanitized
- **Access Control**: Job access restricted to creating user

### Error Information

- **Sanitized Errors**: Error messages scrubbed of sensitive data
- **Logging Security**: Logs contain no personal information
- **Debug Information**: Debug data only in development builds

## API Integration

### LangGraph Service Integration

```dart
class LangGraphService {
  // HTTP client with retry logic
  // Request/response serialization
  // Error handling and mapping
  // Rate limiting compliance
  
  Future<FinalReport> analyzeStock(String ticker, String tradeDate);
  Future<HealthStatus> checkServiceHealth();
}
```

### Rate Limiting

```dart
class RateLimiter {
  // Token bucket algorithm
  // Per-endpoint limits
  // Backoff on limit exceeded
  // Queue management during limits
  
  Future<bool> allowRequest(String endpoint);
  Duration getBackoffDelay();
}
```

---

*This developer guide provides comprehensive implementation details for the async job system. For user-facing documentation, see the User Guide.*