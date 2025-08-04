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

/// Integration test for the complete retry workflow
/// 
/// This test verifies the end-to-end retry functionality including:
/// - Job failing and being scheduled for retry
/// - Retry scheduler executing retries
/// - JobQueueManager integration with retry system
/// - Proper status transitions and event handling
void main() {
  group('Retry Workflow Integration', () {
    late Directory tempDir;
    late HiveJobRepository repository;
    late JobQueueManager queueManager;
    late RetryScheduler retryScheduler;
    
    setUpAll(() async {
      // Initialize Hive with temporary directory
      tempDir = await Directory.systemTemp.createTemp('retry_workflow_test_');
      Hive.init(tempDir.path);
      
      // Register Hive adapter
      if (!Hive.isAdapterRegistered(HiveAnalysisJobAdapter().typeId)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      // Create fresh repository
      repository = HiveJobRepository();
      await repository.init();
      
      // Initialize retry scheduler with very short delays for testing
      // Note: We need to create this first to pass to queue manager
      retryScheduler = RetryScheduler(
        repository: repository,
        queueManager: JobQueueManager(repository: repository), // temporary
        retryPolicy: JobRetryPolicy.testing(),
      );
      await retryScheduler.initialize();
      
      // Initialize queue manager WITH retry scheduler
      queueManager = JobQueueManager(
        repository: repository,
        retryScheduler: retryScheduler,
      );
      await queueManager.initialize();
    });
    
    tearDown(() async {
      // Clean up
      await retryScheduler.dispose();
      queueManager.dispose();
      
      // Clear Hive data
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
    
    test('complete retry workflow - job fails and retries successfully', () async {
      // Create a job
      final job = AnalysisJob(
        id: 'retry-workflow-test-1',
        ticker: 'RETRY',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: DateTime.now(),
        retryCount: 0,
        maxRetries: 3,
      );
      
      // Save and queue the job
      await repository.save(job);
      await queueManager.enqueue(job);
      
      // Dequeue and mark as running
      final dequeuedJob = await queueManager.dequeue();
      expect(dequeuedJob, isNotNull);
      expect(dequeuedJob!.status, equals(JobStatus.running));
      
      // Mark the job as failed (this should trigger retry scheduling)
      await queueManager.markFailed(dequeuedJob, 'Network timeout');
      
      // Verify job is failed and retry is scheduled
      final failedJob = await repository.getById('retry-workflow-test-1');
      expect(failedJob, isNotNull);
      expect(failedJob!.status, equals(JobStatus.failed));
      expect(failedJob.retryCount, equals(0));
      expect(failedJob.errorMessage, equals('Network timeout'));
      
      // Verify retry is scheduled
      expect(retryScheduler.hasScheduledRetry('retry-workflow-test-1'), isTrue);
      
      // Wait for retry to execute (testing policy has 100ms base delay)
      await Future.delayed(const Duration(milliseconds: 200));
      
      // Verify job has been requeued for retry
      final retriedJob = await repository.getById('retry-workflow-test-1');
      expect(retriedJob, isNotNull);
      expect(retriedJob!.status, equals(JobStatus.queued));
      expect(retriedJob.retryCount, equals(1));
      expect(retriedJob.errorMessage, isNull); // Should be cleared on retry
      
      // Verify retry is no longer scheduled
      expect(retryScheduler.hasScheduledRetry('retry-workflow-test-1'), isFalse);
    });
    
    test('retry exhaustion - job fails permanently after max retries', () async {
      // Create a job that's already at max retries
      final job = AnalysisJob(
        id: 'exhausted-retry-test',
        ticker: 'EXHAUST',
        tradeDate: '2024-01-20',
        status: JobStatus.running,
        priority: JobPriority.normal,
        createdAt: DateTime.now(),
        startedAt: DateTime.now(),
        retryCount: 3,
        maxRetries: 3,
      );
      
      await repository.save(job);
      
      // Mark as failed - should not schedule retry
      await queueManager.markFailed(job, 'Permanent failure');
      
      // Verify job is failed and no retry is scheduled
      final failedJob = await repository.getById('exhausted-retry-test');
      expect(failedJob, isNotNull);
      expect(failedJob!.status, equals(JobStatus.failed));
      expect(failedJob.retryCount, equals(3));
      
      // Should not have scheduled a retry
      expect(retryScheduler.hasScheduledRetry('exhausted-retry-test'), isFalse);
      
      // Wait to ensure no retry happens
      await Future.delayed(const Duration(milliseconds: 200));
      
      // Job should still be failed
      final stillFailedJob = await repository.getById('exhausted-retry-test');
      expect(stillFailedJob!.status, equals(JobStatus.failed));
    });
    
    test('job cancellation cancels pending retries', () async {
      // Create and fail a job to trigger retry scheduling
      final job = AnalysisJob(
        id: 'cancel-retry-test',
        ticker: 'CANCEL',
        tradeDate: '2024-01-20',
        status: JobStatus.failed,
        priority: JobPriority.normal,
        createdAt: DateTime.now(),
        completedAt: DateTime.now(),
        retryCount: 1,
        maxRetries: 3,
        errorMessage: 'Retryable error',
      );
      
      await repository.save(job);
      await retryScheduler.scheduleRetry(job);
      
      // Verify retry is scheduled
      expect(retryScheduler.hasScheduledRetry('cancel-retry-test'), isTrue);
      
      // Cancel the job
      final cancelled = await queueManager.cancel('cancel-retry-test');
      expect(cancelled, isFalse); // Should return false as it's not in queue
      
      // But retry should be cancelled
      expect(retryScheduler.hasScheduledRetry('cancel-retry-test'), isFalse);
    });
    
    test('multiple jobs retry scheduling and execution', () async {
      // Create multiple jobs
      final jobs = [
        AnalysisJob(
          id: 'multi-retry-1',
          ticker: 'MULTI1',
          tradeDate: '2024-01-20',
          status: JobStatus.running,
          priority: JobPriority.high,
          createdAt: DateTime.now(),
          startedAt: DateTime.now(),
          retryCount: 0,
          maxRetries: 3,
        ),
        AnalysisJob(
          id: 'multi-retry-2',
          ticker: 'MULTI2',
          tradeDate: '2024-01-20',
          status: JobStatus.running,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          startedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
        ),
      ];
      
      // Save and fail all jobs
      for (final job in jobs) {
        await repository.save(job);
        await queueManager.markFailed(job, 'Test failure');
      }
      
      // Verify all retries are scheduled
      expect(retryScheduler.scheduledRetryCount, equals(2));
      expect(retryScheduler.hasScheduledRetry('multi-retry-1'), isTrue);
      expect(retryScheduler.hasScheduledRetry('multi-retry-2'), isTrue);
      
      // Wait for retries to execute
      await Future.delayed(const Duration(milliseconds: 300));
      
      // Verify all jobs have been requeued
      final retriedJob1 = await repository.getById('multi-retry-1');
      final retriedJob2 = await repository.getById('multi-retry-2');
      
      expect(retriedJob1!.status, equals(JobStatus.queued));
      expect(retriedJob1.retryCount, equals(1));
      
      expect(retriedJob2!.status, equals(JobStatus.queued));
      expect(retriedJob2.retryCount, equals(2));
      
      // No retries should be scheduled now
      expect(retryScheduler.scheduledRetryCount, equals(0));
    });
    
    test('retry statistics are accurate', () async {
      // Create jobs with different retry states
      final jobs = [
        AnalysisJob(
          id: 'stats-test-1',
          ticker: 'STAT1',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 0,
          maxRetries: 3,
          errorMessage: 'Retryable error',
        ),
        AnalysisJob(
          id: 'stats-test-2',
          ticker: 'STAT2',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Another error',
        ),
      ];
      
      // Schedule retries for both jobs
      for (final job in jobs) {
        await repository.save(job);
        await retryScheduler.scheduleRetry(job);
      }
      
      // Check statistics
      final stats = retryScheduler.getStatistics();
      expect(stats.scheduledCount, equals(2));
      expect(stats.activeTimers, equals(2));
      expect(stats.overdueCount, equals(0));
      
      // Wait for one retry to execute
      await Future.delayed(const Duration(milliseconds: 150));
      
      // Statistics should update
      final updatedStats = retryScheduler.getStatistics();
      expect(updatedStats.scheduledCount, lessThan(2));
    });
  });
}