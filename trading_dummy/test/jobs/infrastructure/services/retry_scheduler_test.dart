import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/services/job_retry_policy.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';
import 'package:trading_dummy/jobs/infrastructure/services/retry_scheduler.dart';

void main() {
  group('RetryScheduler', () {
    late Directory tempDir;
    late HiveJobRepository repository;
    late JobQueueManager queueManager;
    late RetryScheduler scheduler;
    late JobRetryPolicy testPolicy;
    
    setUpAll(() async {
      // Initialize Hive with temporary directory
      tempDir = await Directory.systemTemp.createTemp('retry_scheduler_test_');
      Hive.init(tempDir.path);
      
      // Register Hive adapter
      if (!Hive.isAdapterRegistered(HiveAnalysisJobAdapter().typeId)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      // Create fresh repository and queue manager for each test
      repository = HiveJobRepository();
      await repository.init();
      
      queueManager = JobQueueManager(repository: repository);
      await queueManager.initialize();
      
      testPolicy = JobRetryPolicy.testing(); // Very short delays for testing
      
      scheduler = RetryScheduler(
        repository: repository,
        queueManager: queueManager,
        retryPolicy: testPolicy,
      );
    });
    
    tearDown(() async {
      // Clean up after each test
      await scheduler.dispose();
      queueManager.dispose();
      
      // Clear Hive box data
      try {
        if (Hive.isBoxOpen('analysis_jobs')) {
          await Hive.box('analysis_jobs').clear();
        }
      } catch (e) {
        // Ignore cleanup errors
      }
    });
    
    tearDownAll(() async {
      // Clean up temporary directory
      if (tempDir.existsSync()) {
        tempDir.deleteSync(recursive: true);
      }
    });
    
    group('Initialization', () {
      test('initializes successfully', () async {
        expect(scheduler.scheduledRetryCount, equals(0));
        expect(scheduler.getScheduledRetries(), isEmpty);
        
        await scheduler.initialize();
        
        // Should complete without errors
        expect(scheduler.scheduledRetryCount, equals(0));
      });
      
      test('prevents double initialization', () async {
        await scheduler.initialize();
        
        // Second initialization should not throw but log warning
        await expectLater(
          scheduler.initialize(),
          completes,
        );
      });
      
      test('loads existing failed jobs on initialization', () async {
        // Create a failed job that should be retried
        final failedJob = AnalysisJob(
          id: 'failed-job-1',
          ticker: 'AAPL',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now().subtract(const Duration(minutes: 10)),
          completedAt: DateTime.now().subtract(const Duration(minutes: 5)),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Network timeout',
        );
        
        await repository.save(failedJob);
        
        // Initialize scheduler
        await scheduler.initialize();
        
        // Should have scheduled the retry
        expect(scheduler.scheduledRetryCount, equals(1));
        expect(scheduler.hasScheduledRetry('failed-job-1'), isTrue);
      });
      
      test('immediately retries overdue jobs', () async {
        // Create a job that should have been retried already
        final overdueJob = AnalysisJob(
          id: 'overdue-job-1',
          ticker: 'TSLA',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now().subtract(const Duration(hours: 2)),
          completedAt: DateTime.now().subtract(const Duration(hours: 1)),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Service unavailable',
        );
        
        await repository.save(overdueJob);
        
        // Initialize scheduler
        await scheduler.initialize();
        
        // Wait a moment for async execution
        await Future.delayed(const Duration(milliseconds: 50));
        
        // Job should have been requeued
        final updatedJob = await repository.getById('overdue-job-1');
        expect(updatedJob?.status, equals(JobStatus.queued));
        expect(updatedJob?.retryCount, equals(2));
      });
    });
    
    group('Retry Scheduling', () {
      setUp(() async {
        await scheduler.initialize();
      });
      
      test('schedules retry for eligible failed job', () async {
        final failedJob = AnalysisJob(
          id: 'retry-job-1',
          ticker: 'MSFT',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Connection timeout',
        );
        
        await scheduler.scheduleRetry(failedJob);
        
        expect(scheduler.hasScheduledRetry('retry-job-1'), isTrue);
        expect(scheduler.scheduledRetryCount, equals(1));
        
        final retryTime = scheduler.getScheduledRetryTime('retry-job-1');
        expect(retryTime, isNotNull);
        expect(retryTime!.isAfter(DateTime.now()), isTrue);
      });
      
      test('does not schedule retry for ineligible job', () async {
        final ineligibleJob = AnalysisJob(
          id: 'ineligible-job-1',
          ticker: 'GOOGL',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
          completedAt: DateTime.now(),
          retryCount: 3,
          maxRetries: 3,
          errorMessage: 'Max retries exceeded',
        );
        
        await scheduler.scheduleRetry(ineligibleJob);
        
        expect(scheduler.hasScheduledRetry('ineligible-job-1'), isFalse);
        expect(scheduler.scheduledRetryCount, equals(0));
      });
      
      test('cancels existing retry when scheduling new one', () async {
        final job = AnalysisJob(
          id: 'cancel-job-1',
          ticker: 'AMZN',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Server error',
        );
        
        // Schedule first retry
        await scheduler.scheduleRetry(job);
        final firstRetryTime = scheduler.getScheduledRetryTime('cancel-job-1');
        
        // Schedule again (should cancel first)
        await scheduler.scheduleRetry(job);
        final secondRetryTime = scheduler.getScheduledRetryTime('cancel-job-1');
        
        expect(scheduler.scheduledRetryCount, equals(1));
        expect(secondRetryTime, isNotNull);
        expect(secondRetryTime != firstRetryTime, isTrue);
      });
      
      test('throws error when not initialized', () async {
        final uninitializedScheduler = RetryScheduler(
          repository: repository,
          queueManager: queueManager,
          retryPolicy: testPolicy,
        );
        
        final job = AnalysisJob(
          id: 'test-job',
          ticker: 'TEST',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );
        
        await expectLater(
          uninitializedScheduler.scheduleRetry(job),
          throwsStateError,
        );
      });
    });
    
    group('Retry Cancellation', () {
      setUp(() async {
        await scheduler.initialize();
      });
      
      test('cancels scheduled retry', () async {
        final job = AnalysisJob(
          id: 'cancel-test-1',
          ticker: 'NFLX',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Timeout',
        );
        
        await scheduler.scheduleRetry(job);
        expect(scheduler.hasScheduledRetry('cancel-test-1'), isTrue);
        
        await scheduler.cancelRetry('cancel-test-1');
        expect(scheduler.hasScheduledRetry('cancel-test-1'), isFalse);
        expect(scheduler.scheduledRetryCount, equals(0));
      });
      
      test('handles cancellation of non-existent retry', () async {
        // Should complete without error
        await expectLater(
          scheduler.cancelRetry('non-existent-job'),
          completes,
        );
      });
    });
    
    group('Retry Execution', () {
      setUp(() async {
        await scheduler.initialize();
      });
      
      test('executes retry when timer fires', () async {
        final job = AnalysisJob(
          id: 'execute-test-1',
          ticker: 'ORCL',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
          completedAt: DateTime.now().subtract(const Duration(milliseconds: 200)),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Temporary failure',
        );
        
        await repository.save(job);
        await scheduler.scheduleRetry(job);
        
        // Wait for retry to execute (testing policy has 100ms base delay)
        await Future.delayed(const Duration(milliseconds: 300));
        
        // Job should have been requeued
        final updatedJob = await repository.getById('execute-test-1');
        expect(updatedJob, isNotNull);
        expect(updatedJob!.status, equals(JobStatus.queued));
        expect(updatedJob.retryCount, equals(2));
        
        // Should no longer be scheduled
        expect(scheduler.hasScheduledRetry('execute-test-1'), isFalse);
      });
      
      test('handles retry execution errors gracefully', () async {
        // Create a job that will fail retry (e.g., not found)
        final job = AnalysisJob(
          id: 'error-test-1',
          ticker: 'UNKNOWN',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Test error',
        );
        
        // Don't save to repository to simulate error
        await scheduler.scheduleRetry(job);
        
        // Wait for retry attempt
        await Future.delayed(const Duration(milliseconds: 200));
        
        // Should handle error gracefully without crashing
        expect(scheduler.hasScheduledRetry('error-test-1'), isFalse);
      });
    });
    
    group('Statistics', () {
      setUp(() async {
        await scheduler.initialize();
      });
      
      test('provides accurate statistics', () async {
        final stats = scheduler.getStatistics();
        
        expect(stats.scheduledCount, equals(0));
        expect(stats.activeTimers, equals(0));
        expect(stats.overdueCount, equals(0));
      });
      
      test('tracks scheduled retries in statistics', () async {
        final job1 = AnalysisJob(
          id: 'stats-job-1',
          ticker: 'STAT1',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Error 1',
        );
        
        final job2 = AnalysisJob(
          id: 'stats-job-2',
          ticker: 'STAT2',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Error 2',
        );
        
        await scheduler.scheduleRetry(job1);
        await scheduler.scheduleRetry(job2);
        
        final stats = scheduler.getStatistics();
        expect(stats.scheduledCount, equals(2));
        expect(stats.activeTimers, equals(2));
      });
    });
    
    group('Disposal', () {
      test('cleans up resources on disposal', () async {
        await scheduler.initialize();
        
        // Schedule some retries
        final job = AnalysisJob(
          id: 'dispose-test-1',
          ticker: 'DISP',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Test',
        );
        
        await scheduler.scheduleRetry(job);
        expect(scheduler.scheduledRetryCount, equals(1));
        
        // Dispose
        await scheduler.dispose();
        
        // Should have cleaned up
        expect(scheduler.scheduledRetryCount, equals(0));
        expect(scheduler.getScheduledRetries(), isEmpty);
      });
      
      test('prevents operations after disposal', () async {
        await scheduler.initialize();
        await scheduler.dispose();
        
        final job = AnalysisJob(
          id: 'disposed-test',
          ticker: 'DISPOSED',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );
        
        await expectLater(
          scheduler.scheduleRetry(job),
          throwsStateError,
        );
      });
    });
  });
}