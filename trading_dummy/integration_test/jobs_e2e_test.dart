import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:trading_dummy/main.dart' as app;
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/sqlite_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_notification_service.dart';
import 'package:trading_dummy/jobs/infrastructure/services/retry_scheduler.dart';

/// End-to-End integration tests for the async job system
/// 
/// This test suite validates the complete user journey from job submission
/// to completion, including UI interactions, background processing, 
/// notifications, and error scenarios.
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Jobs E2E Tests', () {
    late SQLiteJobRepository repository;
    late JobQueueManager queueManager;
    late JobNotificationService notificationService;
    late RetryScheduler retryScheduler;

    setUpAll(() async {
      // Setup test environment
      // SQLite will use in-memory database for tests
    });

    setUp(() async {
      // Initialize test services
      repository = SQLiteJobRepository();
      await repository.init();
      
      queueManager = JobQueueManager(repository: repository);
      await queueManager.initialize();
      
      notificationService = JobNotificationService();
      await notificationService.initialize();
      
      retryScheduler = RetryScheduler(
        repository: repository,
        queueManager: queueManager,
      );
      await retryScheduler.initialize();
    });

    tearDown(() async {
      // Clean up after each test
      await retryScheduler.dispose();
      queueManager.dispose();
      
      // SQLite uses in-memory database for tests, auto-cleared
    });

    tearDownAll(() async {
      // SQLite cleanup is handled automatically
    });

    group('Complete User Journey', () {
      testWidgets('submit job and track completion', (WidgetTester tester) async {
        // Start the app
        app.main();
        await tester.pumpAndSettle();

        // Find and tap the "Start Analysis" button (assuming it exists)
        // This test would need to be adapted based on actual UI
        final analysisButton = find.text('Start Analysis');
        if (analysisButton.evaluate().isNotEmpty) {
          await tester.tap(analysisButton);
          await tester.pumpAndSettle();
        }

        // Enter ticker symbol
        final tickerField = find.byType(TextField).first;
        await tester.enterText(tickerField, 'AAPL');
        await tester.pumpAndSettle();

        // Submit the job
        final submitButton = find.text('Submit');
        if (submitButton.evaluate().isNotEmpty) {
          await tester.tap(submitButton);
          await tester.pumpAndSettle();
        }

        // Verify job appears in UI
        await tester.pump(const Duration(seconds: 1));
        
        // Check that job was actually created in repository
        final jobs = await repository.getAll();
        expect(jobs.length, greaterThan(0));
        
        final job = jobs.first;
        expect(job.ticker, equals('AAPL'));
        expect(job.status, anyOf([JobStatus.pending, JobStatus.queued]));
      });

      testWidgets('multiple concurrent jobs workflow', (WidgetTester tester) async {
        // Create multiple jobs programmatically for testing
        final jobs = [
          AnalysisJob(
            id: 'job-1',
            ticker: 'AAPL',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: JobPriority.high,
            createdAt: DateTime.now(),
            retryCount: 0,
          ),
          AnalysisJob(
            id: 'job-2',
            ticker: 'MSFT',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            retryCount: 0,
          ),
          AnalysisJob(
            id: 'job-3',
            ticker: 'GOOGL',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: JobPriority.low,
            createdAt: DateTime.now(),
            retryCount: 0,
          ),
        ];

        // Enqueue all jobs
        for (final job in jobs) {
          await queueManager.enqueue(job);
        }

        // Start the app
        app.main();
        await tester.pumpAndSettle();

        // Verify all jobs appear in the queue
        await tester.pump(const Duration(milliseconds: 500));
        
        // Check repository state
        final allJobs = await repository.getAll();
        expect(allJobs.length, equals(3));
        
        // Verify priority ordering in queue
        final pendingJobs = await queueManager.getPending();
        expect(pendingJobs.first.priority, equals(JobPriority.high));
      });

      testWidgets('job cancellation workflow', (WidgetTester tester) async {
        // Create and enqueue a job
        final job = AnalysisJob(
          id: 'cancel-job',
          ticker: 'TSLA',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        await queueManager.enqueue(job);

        // Start the app
        app.main();
        await tester.pumpAndSettle();

        // Find the cancel button (this would depend on actual UI implementation)
        final cancelButton = find.text('Cancel');
        if (cancelButton.evaluate().isNotEmpty) {
          await tester.tap(cancelButton);
          await tester.pumpAndSettle();
        }

        // Verify job was cancelled
        await tester.pump(const Duration(milliseconds: 500));
        
        final updatedJob = await repository.getById('cancel-job');
        expect(updatedJob?.status, equals(JobStatus.cancelled));
      });
    });

    group('Background Processing', () {
      testWidgets('job processing simulation', (WidgetTester tester) async {
        // Create a job that would normally be processed
        final job = AnalysisJob(
          id: 'process-job',
          ticker: 'NVDA',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        await queueManager.enqueue(job);

        // Simulate dequeue and processing
        final dequeuedJob = await queueManager.dequeue();
        expect(dequeuedJob, isNotNull);
        expect(dequeuedJob!.status, equals(JobStatus.running));

        // Simulate successful completion
        await queueManager.markCompleted(dequeuedJob, 'result-123');

        // Verify final state
        final completedJob = await repository.getById('process-job');
        expect(completedJob?.status, equals(JobStatus.completed));
        expect(completedJob?.resultId, equals('result-123'));
      });

      testWidgets('concurrent job processing', (WidgetTester tester) async {
        // Create multiple jobs
        final jobs = List.generate(5, (i) => AnalysisJob(
          id: 'concurrent-job-$i',
          ticker: 'STOCK$i',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        ));

        // Enqueue all jobs
        for (final job in jobs) {
          await queueManager.enqueue(job);
        }

        // Simulate processing within concurrency limits
        final processingJobs = <AnalysisJob>[];
        
        // Dequeue up to max concurrent jobs
        for (int i = 0; i < queueManager.maxConcurrentJobs; i++) {
          final job = await queueManager.dequeue();
          if (job != null) {
            processingJobs.add(job);
          }
        }

        // Should not be able to dequeue more
        final extraJob = await queueManager.dequeue();
        expect(extraJob, isNull);

        // Complete one job
        await queueManager.markCompleted(processingJobs.first, 'result-1');

        // Should now be able to dequeue one more
        final nextJob = await queueManager.dequeue();
        expect(nextJob, isNotNull);
      });
    });

    group('Error Handling & Retry', () {
      testWidgets('job failure and retry workflow', (WidgetTester tester) async {
        // Create a job that will fail
        final job = AnalysisJob(
          id: 'retry-job',
          ticker: 'FAIL',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        await queueManager.enqueue(job);

        // Simulate processing and failure
        final dequeuedJob = await queueManager.dequeue();
        expect(dequeuedJob, isNotNull);

        await queueManager.markFailed(dequeuedJob!, 'Network timeout');

        // Verify job is marked as failed
        final failedJob = await repository.getById('retry-job');
        expect(failedJob?.status, equals(JobStatus.failed));
        expect(failedJob?.errorMessage, equals('Network timeout'));

        // Verify retry was scheduled
        expect(retryScheduler.hasScheduledRetry('retry-job'), isTrue);
      });

      testWidgets('retry execution workflow', (WidgetTester tester) async {
        // Create a failed job eligible for retry
        final failedJob = AnalysisJob(
          id: 'retry-execute-job',
          ticker: 'RETRY',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
          completedAt: DateTime.now().subtract(const Duration(seconds: 30)),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Temporary failure',
        );

        await repository.save(failedJob);

        // Schedule and wait for retry
        await retryScheduler.scheduleRetry(failedJob);
        
        // Wait a moment for retry to execute (using test policy with short delays)
        await tester.pump(const Duration(milliseconds: 200));

        // Verify job was requeued
        final requeuedJob = await repository.getById('retry-execute-job');
        expect(requeuedJob?.status, equals(JobStatus.queued));
        expect(requeuedJob?.retryCount, equals(2));
      });

      testWidgets('maximum retries reached workflow', (WidgetTester tester) async {
        // Create a job that has reached max retries
        final maxRetriesJob = AnalysisJob(
          id: 'max-retries-job',
          ticker: 'MAXRETRY',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 3,
          maxRetries: 3,
          errorMessage: 'Permanent failure',
        );

        await repository.save(maxRetriesJob);

        // Attempt to schedule retry
        await retryScheduler.scheduleRetry(maxRetriesJob);

        // Should not be scheduled
        expect(retryScheduler.hasScheduledRetry('max-retries-job'), isFalse);
      });
    });

    group('Notification System', () {
      testWidgets('job completion notification', (WidgetTester tester) async {
        // Create and complete a job
        final job = AnalysisJob(
          id: 'notify-job',
          ticker: 'NOTIFY',
          tradeDate: '2024-01-20',
          status: JobStatus.completed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          resultId: 'result-notify',
          retryCount: 0,
        );

        // Test notification (this would show notification if platform supports it)
        await notificationService.notifyJobComplete(job, resultId: 'result-notify');

        // Verify no exceptions were thrown
        expect(true, isTrue);
      });

      testWidgets('job failure notification', (WidgetTester tester) async {
        // Create a failed job
        final failedJob = AnalysisJob(
          id: 'failed-notify-job',
          ticker: 'FAILED',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          errorMessage: 'Test failure',
          retryCount: 1,
        );

        // Test failure notification
        await notificationService.notifyJobFailed(
          failedJob,
          errorMessage: 'Test failure',
          willRetry: true,
        );

        // Verify no exceptions were thrown
        expect(true, isTrue);
      });
    });

    group('Performance & Load Testing', () {
      testWidgets('high volume job submission', (WidgetTester tester) async {
        final stopwatch = Stopwatch()..start();

        // Create 50 jobs to test performance
        final jobs = List.generate(50, (i) => AnalysisJob(
          id: 'perf-job-$i',
          ticker: 'PERF$i',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: i % 2 == 0 ? JobPriority.high : JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        ));

        // Enqueue all jobs
        for (final job in jobs) {
          await queueManager.enqueue(job);
        }

        stopwatch.stop();

        // Verify performance target (<100ms per job on average)
        final avgTimePerJob = stopwatch.elapsedMilliseconds / jobs.length;
        expect(avgTimePerJob, lessThan(100.0));

        // Verify all jobs were queued
        final allJobs = await repository.getAll();
        expect(allJobs.length, equals(50));
      });

      testWidgets('queue statistics accuracy', (WidgetTester tester) async {
        // Create jobs in different states
        final pendingJob = AnalysisJob(
          id: 'stats-pending',
          ticker: 'PENDING',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        final completedJob = AnalysisJob(
          id: 'stats-completed',
          ticker: 'COMPLETED',
          tradeDate: '2024-01-20',
          status: JobStatus.completed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          resultId: 'result-123',
          retryCount: 0,
        );

        await queueManager.enqueue(pendingJob);
        await repository.save(completedJob);

        // Get statistics
        final stats = await queueManager.getStatistics();

        expect(stats.pendingCount, equals(1));
        expect(stats.completedCount, equals(1));
        expect(stats.runningCount, equals(0));
        expect(stats.successRate, equals(1.0));
      });
    });

    group('Data Persistence & Recovery', () {
      testWidgets('app restart recovery', (WidgetTester tester) async {
        // Create jobs in various states
        final jobs = [
          AnalysisJob(
            id: 'restart-pending',
            ticker: 'RESTART1',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            retryCount: 0,
          ),
          AnalysisJob(
            id: 'restart-running',
            ticker: 'RESTART2',
            tradeDate: '2024-01-20',
            status: JobStatus.running,
            priority: JobPriority.high,
            createdAt: DateTime.now(),
            startedAt: DateTime.now(),
            retryCount: 0,
          ),
          AnalysisJob(
            id: 'restart-failed',
            ticker: 'RESTART3',
            tradeDate: '2024-01-20',
            status: JobStatus.failed,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            completedAt: DateTime.now(),
            errorMessage: 'Network error',
            retryCount: 1,
            maxRetries: 3,
          ),
        ];

        // Save jobs directly to repository
        for (final job in jobs) {
          await repository.save(job);
        }

        // Simulate app restart by creating new managers
        final newQueueManager = JobQueueManager(repository: repository);
        await newQueueManager.initialize();

        final newRetryScheduler = RetryScheduler(
          repository: repository,
          queueManager: newQueueManager,
        );
        await newRetryScheduler.initialize();

        // Verify recovery
        final pendingJobs = await newQueueManager.getPending();
        expect(pendingJobs.length, equals(1));
        expect(pendingJobs.first.id, equals('restart-pending'));

        // Verify retry scheduling was restored
        expect(newRetryScheduler.hasScheduledRetry('restart-failed'), isTrue);

        // Clean up
        await newRetryScheduler.dispose();
        newQueueManager.dispose();
      });

      testWidgets('data integrity validation', (WidgetTester tester) async {
        // Create a job with all fields populated
        final originalJob = AnalysisJob(
          id: 'integrity-job',
          ticker: 'INTEGRITY',
          tradeDate: '2024-01-20',
          status: JobStatus.completed,
          priority: JobPriority.high,
          createdAt: DateTime.now(),
          startedAt: DateTime.now().add(const Duration(seconds: 1)),
          completedAt: DateTime.now().add(const Duration(seconds: 30)),
          resultId: 'result-integrity-123',
          errorMessage: null,
          retryCount: 2,
          maxRetries: 3,
        );

        // Save and retrieve
        await repository.save(originalJob);
        final retrievedJob = await repository.getById('integrity-job');

        // Verify all fields match
        expect(retrievedJob, isNotNull);
        expect(retrievedJob!.id, equals(originalJob.id));
        expect(retrievedJob.ticker, equals(originalJob.ticker));
        expect(retrievedJob.tradeDate, equals(originalJob.tradeDate));
        expect(retrievedJob.status, equals(originalJob.status));
        expect(retrievedJob.priority, equals(originalJob.priority));
        expect(retrievedJob.resultId, equals(originalJob.resultId));
        expect(retrievedJob.retryCount, equals(originalJob.retryCount));
        expect(retrievedJob.maxRetries, equals(originalJob.maxRetries));
      });
    });
  });
}