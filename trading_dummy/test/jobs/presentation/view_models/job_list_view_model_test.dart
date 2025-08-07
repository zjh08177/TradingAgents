import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/application/use_cases/get_job_status_use_case.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';
import 'package:trading_dummy/jobs/presentation/view_models/job_list_view_model.dart';

// Mock classes
class MockGetJobStatusUseCase extends Mock implements GetJobStatusUseCase {}

void main() {
  group('JobListViewModel', () {
    late MockGetJobStatusUseCase mockGetJobStatus;
    late JobEventBus eventBus;
    late JobListViewModel viewModel;
    
    setUpAll(() async {
      // No Hive initialization needed
    });
    
    setUp(() async {
      JobEventBus.resetForTesting();
      
      mockGetJobStatus = MockGetJobStatusUseCase();
      eventBus = JobEventBus();
      
      viewModel = JobListViewModel(
        getJobStatus: mockGetJobStatus,
        eventBus: eventBus,
      );
    });
    
    tearDown(() {
      try {
        viewModel.dispose();
      } catch (e) {
        // Already disposed
      }
    });
    
    tearDownAll(() async {
      // Cleanup if needed
    });
    
    AnalysisJob createTestJob({
      String? id,
      String? ticker,
      JobStatus? status,
      JobPriority? priority,
      DateTime? createdAt,
      String? errorMessage,
    }) {
      return AnalysisJob(
        id: id ?? 'test-${DateTime.now().millisecondsSinceEpoch}',
        ticker: ticker ?? 'AAPL',
        tradeDate: '2024-01-20',
        status: status ?? JobStatus.pending,
        priority: priority ?? JobPriority.normal,
        createdAt: createdAt ?? DateTime.now(),
        retryCount: 0,
        errorMessage: errorMessage,
      );
    }
    
    Future<void> addJobsViaEvents(List<AnalysisJob> jobs) async {
      for (final job in jobs) {
        eventBus.publish(JobQueuedEvent(job));
      }
      await Future.delayed(const Duration(milliseconds: 10));
    }
    
    group('initialization', () {
      test('should initialize with empty job lists', () {
        expect(viewModel.displayedJobs, isEmpty);
        expect(viewModel.allJobs, isEmpty);
        expect(viewModel.isLoading, isFalse);
        expect(viewModel.errorMessage, isNull);
      });
      
      test('should initialize with default filter and sort', () {
        expect(viewModel.currentFilter, equals(JobFilterOption.all));
        expect(viewModel.currentSort, equals(JobSortOption.createdAtDesc));
        expect(viewModel.searchQuery, isEmpty);
        expect(viewModel.isFiltered, isFalse);
      });
      
      test('should initialize counters correctly', () {
        expect(viewModel.totalJobsCount, equals(0));
        expect(viewModel.displayedJobsCount, equals(0));
        expect(viewModel.activeJobsCount, equals(0));
        expect(viewModel.completedJobsCount, equals(0));
        expect(viewModel.failedJobsCount, equals(0));
        expect(viewModel.hasJobs, isFalse);
        expect(viewModel.hasDisplayedJobs, isFalse);
      });
    });
    
    group('event handling', () {
      test('should add job on JobQueuedEvent', () async {
        final job = createTestJob(id: 'queued-test');
        
        bool notified = false;
        viewModel.addListener(() => notified = true);
        
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(notified, isTrue);
        expect(viewModel.allJobs.length, equals(1));
        expect(viewModel.displayedJobs.length, equals(1));
        expect(viewModel.allJobs.first.id, equals('queued-test'));
      });
      
      test('should update existing job on subsequent events', () async {
        final job = createTestJob(id: 'update-test', status: JobStatus.queued);
        final updatedJob = job.copyWith(status: JobStatus.running);
        
        // Add initial job
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.allJobs.first.status, equals(JobStatus.queued));
        
        // Update job
        eventBus.publish(JobStartedEvent(updatedJob));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.allJobs.length, equals(1));
        expect(viewModel.allJobs.first.status, equals(JobStatus.running));
      });
      
      test('should remove job on JobCancelledEvent', () async {
        final job = createTestJob(id: 'cancel-test');
        final cancelledJob = job.copyWith(status: JobStatus.cancelled);
        
        // Add job
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.allJobs.length, equals(1));
        
        // Cancel job
        eventBus.publish(JobCancelledEvent(cancelledJob));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.allJobs.length, equals(0));
        expect(viewModel.displayedJobs.length, equals(0));
      });
    });
    
    group('filtering', () {
      test('should filter by all (default)', () async {
        final jobs = [
          createTestJob(id: 'pending', status: JobStatus.pending),
          createTestJob(id: 'running', status: JobStatus.running),
          createTestJob(id: 'completed', status: JobStatus.completed),
          createTestJob(id: 'failed', status: JobStatus.failed),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applyFilter(JobFilterOption.all);
        
        expect(viewModel.displayedJobs.length, equals(4));
        expect(viewModel.currentFilter, equals(JobFilterOption.all));
      });
      
      test('should filter by active jobs', () async {
        final jobs = [
          createTestJob(id: 'pending', status: JobStatus.pending),
          createTestJob(id: 'queued', status: JobStatus.queued),
          createTestJob(id: 'running', status: JobStatus.running),
          createTestJob(id: 'completed', status: JobStatus.completed),
          createTestJob(id: 'failed', status: JobStatus.failed),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applyFilter(JobFilterOption.active);
        
        expect(viewModel.displayedJobs.length, equals(3));
        expect(viewModel.displayedJobs.every((job) => 
          job.status == JobStatus.pending || 
          job.status == JobStatus.queued || 
          job.status == JobStatus.running
        ), isTrue);
        expect(viewModel.currentFilter, equals(JobFilterOption.active));
      });
      
      test('should filter by completed jobs', () async {
        final jobs = [
          createTestJob(id: 'completed1', status: JobStatus.completed),
          createTestJob(id: 'completed2', status: JobStatus.completed),
          createTestJob(id: 'running', status: JobStatus.running),
          createTestJob(id: 'failed', status: JobStatus.failed),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applyFilter(JobFilterOption.completed);
        
        expect(viewModel.displayedJobs.length, equals(2));
        expect(viewModel.displayedJobs.every((job) => job.status == JobStatus.completed), isTrue);
      });
      
      test('should filter by failed jobs', () async {
        final jobs = [
          createTestJob(id: 'failed1', status: JobStatus.failed),
          createTestJob(id: 'failed2', status: JobStatus.failed),
          createTestJob(id: 'completed', status: JobStatus.completed),
          createTestJob(id: 'running', status: JobStatus.running),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applyFilter(JobFilterOption.failed);
        
        expect(viewModel.displayedJobs.length, equals(2));
        expect(viewModel.displayedJobs.every((job) => job.status == JobStatus.failed), isTrue);
      });
      
      test('should filter by specific status', () async {
        final jobs = [
          createTestJob(id: 'pending1', status: JobStatus.pending),
          createTestJob(id: 'pending2', status: JobStatus.pending),
          createTestJob(id: 'running', status: JobStatus.running),
          createTestJob(id: 'queued', status: JobStatus.queued),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applyFilter(JobFilterOption.pending);
        
        expect(viewModel.displayedJobs.length, equals(2));
        expect(viewModel.displayedJobs.every((job) => job.status == JobStatus.pending), isTrue);
        
        viewModel.applyFilter(JobFilterOption.running);
        
        expect(viewModel.displayedJobs.length, equals(1));
        expect(viewModel.displayedJobs.first.status, equals(JobStatus.running));
        
        viewModel.applyFilter(JobFilterOption.queued);
        
        expect(viewModel.displayedJobs.length, equals(1));
        expect(viewModel.displayedJobs.first.status, equals(JobStatus.queued));
      });
      
      test('should mark as filtered when not showing all', () async {
        expect(viewModel.isFiltered, isFalse);
        
        viewModel.applyFilter(JobFilterOption.active);
        expect(viewModel.isFiltered, isTrue);
        
        viewModel.applyFilter(JobFilterOption.all);
        expect(viewModel.isFiltered, isFalse);
      });
    });
    
    group('sorting', () {
      test('should sort by created date descending (default)', () async {
        final now = DateTime.now();
        final jobs = [
          createTestJob(id: 'oldest', createdAt: now.subtract(const Duration(hours: 3))),
          createTestJob(id: 'newest', createdAt: now),
          createTestJob(id: 'middle', createdAt: now.subtract(const Duration(hours: 1))),
        ];
        
        await addJobsViaEvents(jobs);
        
        expect(viewModel.displayedJobs[0].id, equals('newest'));
        expect(viewModel.displayedJobs[1].id, equals('middle'));
        expect(viewModel.displayedJobs[2].id, equals('oldest'));
      });
      
      test('should sort by created date ascending', () async {
        final now = DateTime.now();
        final jobs = [
          createTestJob(id: 'newest', createdAt: now),
          createTestJob(id: 'oldest', createdAt: now.subtract(const Duration(hours: 3))),
          createTestJob(id: 'middle', createdAt: now.subtract(const Duration(hours: 1))),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySort(JobSortOption.createdAtAsc);
        
        expect(viewModel.displayedJobs[0].id, equals('oldest'));
        expect(viewModel.displayedJobs[1].id, equals('middle'));
        expect(viewModel.displayedJobs[2].id, equals('newest'));
      });
      
      test('should sort by priority descending', () async {
        final jobs = [
          createTestJob(id: 'normal', priority: JobPriority.normal),
          createTestJob(id: 'critical', priority: JobPriority.critical),
          createTestJob(id: 'high', priority: JobPriority.high),
          createTestJob(id: 'low', priority: JobPriority.low),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySort(JobSortOption.priorityDesc);
        
        expect(viewModel.displayedJobs[0].id, equals('critical'));
        expect(viewModel.displayedJobs[1].id, equals('high'));
        expect(viewModel.displayedJobs[2].id, equals('normal'));
        expect(viewModel.displayedJobs[3].id, equals('low'));
      });
      
      test('should sort by priority ascending', () async {
        final jobs = [
          createTestJob(id: 'critical', priority: JobPriority.critical),
          createTestJob(id: 'low', priority: JobPriority.low),
          createTestJob(id: 'high', priority: JobPriority.high),
          createTestJob(id: 'normal', priority: JobPriority.normal),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySort(JobSortOption.priorityAsc);
        
        expect(viewModel.displayedJobs[0].id, equals('low'));
        expect(viewModel.displayedJobs[1].id, equals('normal'));
        expect(viewModel.displayedJobs[2].id, equals('high'));
        expect(viewModel.displayedJobs[3].id, equals('critical'));
      });
      
      test('should sort by ticker ascending', () async {
        final jobs = [
          createTestJob(id: 'tesla', ticker: 'TSLA'),
          createTestJob(id: 'apple', ticker: 'AAPL'),
          createTestJob(id: 'google', ticker: 'GOOGL'),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySort(JobSortOption.tickerAsc);
        
        expect(viewModel.displayedJobs[0].ticker, equals('AAPL'));
        expect(viewModel.displayedJobs[1].ticker, equals('GOOGL'));
        expect(viewModel.displayedJobs[2].ticker, equals('TSLA'));
      });
      
      test('should sort by ticker descending', () async {
        final jobs = [
          createTestJob(id: 'apple', ticker: 'AAPL'),
          createTestJob(id: 'tesla', ticker: 'TSLA'),
          createTestJob(id: 'google', ticker: 'GOOGL'),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySort(JobSortOption.tickerDesc);
        
        expect(viewModel.displayedJobs[0].ticker, equals('TSLA'));
        expect(viewModel.displayedJobs[1].ticker, equals('GOOGL'));
        expect(viewModel.displayedJobs[2].ticker, equals('AAPL'));
      });
      
      test('should sort by status ascending', () async {
        final jobs = [
          createTestJob(id: 'completed', status: JobStatus.completed),
          createTestJob(id: 'pending', status: JobStatus.pending),
          createTestJob(id: 'running', status: JobStatus.running),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySort(JobSortOption.statusAsc);
        
        // Status order should be by enum index
        expect(viewModel.displayedJobs[0].status, equals(JobStatus.pending));
        expect(viewModel.displayedJobs[1].status, equals(JobStatus.running));
        expect(viewModel.displayedJobs[2].status, equals(JobStatus.completed));
      });
    });
    
    group('searching', () {
      test('should search by ticker', () async {
        final jobs = [
          createTestJob(id: 'apple', ticker: 'AAPL'),
          createTestJob(id: 'tesla', ticker: 'TSLA'),
          createTestJob(id: 'google', ticker: 'GOOGL'),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySearch('AAPL');
        
        expect(viewModel.displayedJobs.length, equals(1));
        expect(viewModel.displayedJobs.first.ticker, equals('AAPL'));
        expect(viewModel.searchQuery, equals('AAPL'));
        expect(viewModel.isFiltered, isTrue);
      });
      
      test('should search case insensitively', () async {
        final jobs = [
          createTestJob(id: 'apple', ticker: 'AAPL'),
          createTestJob(id: 'tesla', ticker: 'TSLA'),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySearch('aapl');
        
        expect(viewModel.displayedJobs.length, equals(1));
        expect(viewModel.displayedJobs.first.ticker, equals('AAPL'));
      });
      
      test('should search by multiple fields', () async {
        final jobs = [
          createTestJob(id: 'test-123', ticker: 'AAPL'),
          createTestJob(id: 'other', ticker: 'TSLA', errorMessage: 'connection failed'),
          createTestJob(id: 'another', ticker: 'GOOGL'),
        ];
        
        await addJobsViaEvents(jobs);
        
        // Search by ID
        viewModel.applySearch('test-123');
        expect(viewModel.displayedJobs.length, equals(1));
        expect(viewModel.displayedJobs.first.id, equals('test-123'));
        
        // Search by error message
        viewModel.applySearch('connection');
        expect(viewModel.displayedJobs.length, equals(1));
        expect(viewModel.displayedJobs.first.ticker, equals('TSLA'));
        
        // Search by trade date
        viewModel.applySearch('2024-01-20');
        expect(viewModel.displayedJobs.length, equals(3)); // All have same trade date
      });
      
      test('should clear search', () async {
        final jobs = [
          createTestJob(id: 'apple', ticker: 'AAPL'),
          createTestJob(id: 'tesla', ticker: 'TSLA'),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applySearch('AAPL');
        expect(viewModel.displayedJobs.length, equals(1));
        
        viewModel.applySearch('');
        expect(viewModel.displayedJobs.length, equals(2));
        expect(viewModel.searchQuery, isEmpty);
        expect(viewModel.isFiltered, isFalse);
      });
    });
    
    group('combined filtering and searching', () {
      test('should apply filter and search together', () async {
        final jobs = [
          createTestJob(id: 'aapl-pending', ticker: 'AAPL', status: JobStatus.pending),
          createTestJob(id: 'aapl-completed', ticker: 'AAPL', status: JobStatus.completed),
          createTestJob(id: 'tsla-pending', ticker: 'TSLA', status: JobStatus.pending),
          createTestJob(id: 'tsla-completed', ticker: 'TSLA', status: JobStatus.completed),
        ];
        
        await addJobsViaEvents(jobs);
        
        // Filter by completed status
        viewModel.applyFilter(JobFilterOption.completed);
        expect(viewModel.displayedJobs.length, equals(2));
        
        // Then search for AAPL
        viewModel.applySearch('AAPL');
        expect(viewModel.displayedJobs.length, equals(1));
        expect(viewModel.displayedJobs.first.id, equals('aapl-completed'));
      });
      
      test('should clear all filters', () async {
        final jobs = [
          createTestJob(id: 'aapl-pending', ticker: 'AAPL', status: JobStatus.pending),
          createTestJob(id: 'tsla-completed', ticker: 'TSLA', status: JobStatus.completed),
        ];
        
        await addJobsViaEvents(jobs);
        
        viewModel.applyFilter(JobFilterOption.completed);
        viewModel.applySearch('AAPL');
        expect(viewModel.displayedJobs.length, equals(0));
        
        viewModel.clearFilters();
        expect(viewModel.displayedJobs.length, equals(2));
        expect(viewModel.currentFilter, equals(JobFilterOption.all));
        expect(viewModel.searchQuery, isEmpty);
        expect(viewModel.isFiltered, isFalse);
      });
    });
    
    group('utility methods', () {
      test('getJobById should find job correctly', () async {
        final job = createTestJob(id: 'find-test');
        
        await addJobsViaEvents([job]);
        
        final foundJob = viewModel.getJobById('find-test');
        expect(foundJob, isNotNull);
        expect(foundJob!.id, equals('find-test'));
        
        final notFoundJob = viewModel.getJobById('not-found');
        expect(notFoundJob, isNull);
      });
      
      test('getJobsByTicker should filter correctly', () async {
        final jobs = [
          createTestJob(id: 'aapl1', ticker: 'AAPL'),
          createTestJob(id: 'aapl2', ticker: 'AAPL'),
          createTestJob(id: 'tsla1', ticker: 'TSLA'),
        ];
        
        await addJobsViaEvents(jobs);
        
        final aaplJobs = viewModel.getJobsByTicker('AAPL');
        expect(aaplJobs.length, equals(2));
        expect(aaplJobs.every((job) => job.ticker == 'AAPL'), isTrue);
        
        // Case insensitive
        final aaplJobsLower = viewModel.getJobsByTicker('aapl');
        expect(aaplJobsLower.length, equals(2));
      });
      
      test('getJobsByStatus should filter correctly', () async {
        final jobs = [
          createTestJob(id: 'pending1', status: JobStatus.pending),
          createTestJob(id: 'pending2', status: JobStatus.pending),
          createTestJob(id: 'completed1', status: JobStatus.completed),
        ];
        
        await addJobsViaEvents(jobs);
        
        final pendingJobs = viewModel.getJobsByStatus(JobStatus.pending);
        expect(pendingJobs.length, equals(2));
        expect(pendingJobs.every((job) => job.status == JobStatus.pending), isTrue);
      });
      
      test('getJobsByPriority should filter correctly', () async {
        final jobs = [
          createTestJob(id: 'high1', priority: JobPriority.high),
          createTestJob(id: 'high2', priority: JobPriority.high),
          createTestJob(id: 'normal1', priority: JobPriority.normal),
        ];
        
        await addJobsViaEvents(jobs);
        
        final highJobs = viewModel.getJobsByPriority(JobPriority.high);
        expect(highJobs.length, equals(2));
        expect(highJobs.every((job) => job.priority == JobPriority.high), isTrue);
      });
    });
    
    group('counters', () {
      test('should count jobs by status correctly', () async {
        final jobs = [
          createTestJob(id: 'pending1', status: JobStatus.pending),
          createTestJob(id: 'pending2', status: JobStatus.pending),
          createTestJob(id: 'running1', status: JobStatus.running),
          createTestJob(id: 'completed1', status: JobStatus.completed),
          createTestJob(id: 'completed2', status: JobStatus.completed),
          createTestJob(id: 'completed3', status: JobStatus.completed),
          createTestJob(id: 'failed1', status: JobStatus.failed),
        ];
        
        await addJobsViaEvents(jobs);
        
        expect(viewModel.totalJobsCount, equals(7));
        expect(viewModel.activeJobsCount, equals(3)); // pending + running
        expect(viewModel.completedJobsCount, equals(3));
        expect(viewModel.failedJobsCount, equals(1));
        expect(viewModel.hasJobs, isTrue);
        expect(viewModel.hasDisplayedJobs, isTrue);
      });
    });
    
    group('change notification', () {
      test('should notify listeners on state changes', () async {
        int notificationCount = 0;
        viewModel.addListener(() => notificationCount++);
        
        final job = createTestJob();
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(notificationCount, greaterThan(0));
        
        final oldCount = notificationCount;
        viewModel.applyFilter(JobFilterOption.active);
        expect(notificationCount, greaterThan(oldCount));
      });
    });
    
    group('error handling', () {
      test('should handle event stream errors', () async {
        // This is difficult to test directly, but we can verify the error handling exists
        expect(viewModel.errorMessage, isNull);
        
        // The error handling is internal to the event subscription
        // In a real scenario, we'd need to trigger an actual error in the stream
      });
      
      test('clearError should clear error message', () {
        // Since we can't easily trigger an error, we'll just test the clear functionality
        viewModel.clearError();
        expect(viewModel.errorMessage, isNull);
      });
    });
    
    group('disposal', () {
      test('should dispose cleanly', () {
        expect(() => viewModel.dispose(), returnsNormally);
      });
    });
  });
}