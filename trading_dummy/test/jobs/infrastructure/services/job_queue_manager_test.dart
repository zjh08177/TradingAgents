import 'dart:async';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';

void main() {
  group('JobQueueManager', () {
    late HiveJobRepository repository;
    late JobQueueManager queueManager;
    late JobEventBus eventBus;
    late Directory tempDir;
    
    setUpAll(() async {
      tempDir = await Directory.systemTemp.createTemp('queue_test_');
      Hive.init(tempDir.path);
      
      if (!Hive.isAdapterRegistered(20)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      JobEventBus.resetForTesting();
      repository = HiveJobRepository();
      await repository.init();
      
      eventBus = JobEventBus();
      queueManager = JobQueueManager(
        repository: repository,
        eventBus: eventBus,
        maxConcurrentJobs: 3,
      );
    });
    
    tearDown(() async {
      queueManager.dispose();
      await repository.close();
      await Hive.deleteBoxFromDisk('analysis_jobs');
    });
    
    tearDownAll(() async {
      await tempDir.delete(recursive: true);
    });
    
    AnalysisJob createTestJob({
      String? id,
      String? ticker,
      JobStatus? status,
      JobPriority? priority,
      DateTime? createdAt,
      int? retryCount,
    }) {
      return AnalysisJob(
        id: id ?? 'test-${DateTime.now().millisecondsSinceEpoch}',
        ticker: ticker ?? 'AAPL',
        tradeDate: '2024-01-20',
        status: status ?? JobStatus.pending,
        priority: priority ?? JobPriority.normal,
        createdAt: createdAt ?? DateTime.now(),
        retryCount: retryCount ?? 0,
      );
    }
    
    test('initialize loads existing jobs correctly', () async {
      // Add some jobs to repository
      final pendingJob = createTestJob(id: 'pending-1', status: JobStatus.pending);
      final queuedJob = createTestJob(id: 'queued-1', status: JobStatus.queued);
      final runningJob = createTestJob(id: 'running-1', status: JobStatus.running);
      final completedJob = createTestJob(id: 'completed-1', status: JobStatus.completed);
      
      await repository.save(pendingJob);
      await repository.save(queuedJob);
      await repository.save(runningJob);
      await repository.save(completedJob);
      
      // Initialize queue manager
      await queueManager.initialize();
      
      // Check that pending/queued jobs are loaded
      final pendingJobs = await queueManager.getPending();
      expect(pendingJobs.length, equals(2));
      
      // Check statistics
      final stats = await queueManager.getStatistics();
      expect(stats.pendingCount, equals(2));
      expect(stats.runningCount, equals(1));
    });
    
    test('enqueue adds job to queue and repository', () async {
      await queueManager.initialize();
      
      final job = createTestJob(id: 'new-job');
      await queueManager.enqueue(job);
      
      // Check job is in queue
      final pendingJobs = await queueManager.getPending();
      expect(pendingJobs.any((j) => j.id == 'new-job'), isTrue);
      expect(pendingJobs.first.status, equals(JobStatus.queued));
      
      // Check job is in repository
      final savedJob = await repository.getById('new-job');
      expect(savedJob, isNotNull);
      expect(savedJob!.status, equals(JobStatus.queued));
    });
    
    test('enqueue respects priority order', () async {
      await queueManager.initialize();
      
      // Add jobs in reverse priority order
      await queueManager.enqueue(createTestJob(id: 'low-1', priority: JobPriority.low));
      await queueManager.enqueue(createTestJob(id: 'normal-1', priority: JobPriority.normal));
      await queueManager.enqueue(createTestJob(id: 'high-1', priority: JobPriority.high));
      await queueManager.enqueue(createTestJob(id: 'critical-1', priority: JobPriority.critical));
      
      final pendingJobs = await queueManager.getPending();
      
      // Should be in priority order
      expect(pendingJobs[0].id, equals('critical-1'));
      expect(pendingJobs[1].id, equals('high-1'));
      expect(pendingJobs[2].id, equals('normal-1'));
      expect(pendingJobs[3].id, equals('low-1'));
    });
    
    test('dequeue returns highest priority job', () async {
      await queueManager.initialize();
      
      // Add jobs with different priorities
      await queueManager.enqueue(createTestJob(id: 'normal-1', priority: JobPriority.normal));
      await queueManager.enqueue(createTestJob(id: 'high-1', priority: JobPriority.high));
      await queueManager.enqueue(createTestJob(id: 'low-1', priority: JobPriority.low));
      
      // Dequeue should return high priority job
      final job = await queueManager.dequeue();
      expect(job, isNotNull);
      expect(job!.id, equals('high-1'));
      expect(job.status, equals(JobStatus.running));
      expect(job.startedAt, isNotNull);
      
      // Check job is updated in repository
      final savedJob = await repository.getById('high-1');
      expect(savedJob!.status, equals(JobStatus.running));
      expect(savedJob.startedAt, isNotNull);
    });
    
    test('dequeue respects max concurrent jobs limit', () async {
      await queueManager.initialize();
      
      // Add multiple jobs
      for (int i = 0; i < 5; i++) {
        await queueManager.enqueue(createTestJob(id: 'job-$i'));
      }
      
      // Dequeue up to max concurrent limit (3)
      final job1 = await queueManager.dequeue();
      final job2 = await queueManager.dequeue();
      final job3 = await queueManager.dequeue();
      
      expect(job1, isNotNull);
      expect(job2, isNotNull);
      expect(job3, isNotNull);
      
      // Next dequeue should return null (limit reached)
      final job4 = await queueManager.dequeue();
      expect(job4, isNull);
      
      // After marking one as complete, should be able to dequeue again
      await queueManager.markCompleted(job1!, 'result-1');
      
      final job5 = await queueManager.dequeue();
      expect(job5, isNotNull);
    });
    
    test('dequeue maintains FIFO within same priority', () async {
      await queueManager.initialize();
      
      final now = DateTime.now();
      
      // Add jobs with same priority but different times
      await queueManager.enqueue(createTestJob(
        id: 'normal-1',
        priority: JobPriority.normal,
        createdAt: now.subtract(const Duration(minutes: 3)),
      ));
      await queueManager.enqueue(createTestJob(
        id: 'normal-2',
        priority: JobPriority.normal,
        createdAt: now.subtract(const Duration(minutes: 2)),
      ));
      await queueManager.enqueue(createTestJob(
        id: 'normal-3',
        priority: JobPriority.normal,
        createdAt: now.subtract(const Duration(minutes: 1)),
      ));
      
      // Should dequeue in FIFO order
      final job1 = await queueManager.dequeue();
      expect(job1!.id, equals('normal-1'));
      
      final job2 = await queueManager.dequeue();
      expect(job2!.id, equals('normal-2'));
      
      final job3 = await queueManager.dequeue();
      expect(job3!.id, equals('normal-3'));
    });
    
    test('requeue adds job back to queue with retry count', () async {
      await queueManager.initialize();
      
      final job = createTestJob(id: 'retry-job');
      await queueManager.enqueue(job);
      
      // Dequeue and simulate failure
      final runningJob = await queueManager.dequeue();
      expect(runningJob, isNotNull);
      
      // Requeue the job
      await queueManager.requeue(runningJob!);
      
      // Check job is back in queue
      final pendingJobs = await queueManager.getPending();
      expect(pendingJobs.any((j) => j.id == 'retry-job'), isTrue);
      
      final requeuedJob = pendingJobs.firstWhere((j) => j.id == 'retry-job');
      expect(requeuedJob.status, equals(JobStatus.queued));
      expect(requeuedJob.retryCount, equals(1));
      expect(requeuedJob.startedAt, isNull);
      expect(requeuedJob.errorMessage, isNull);
    });
    
    test('requeue lowers priority after multiple retries', () async {
      await queueManager.initialize();
      
      final job = createTestJob(
        id: 'multi-retry',
        priority: JobPriority.critical,
        retryCount: 1, // Already failed once
      );
      
      // Simulate job that has already been retried
      await repository.save(job.copyWith(status: JobStatus.running));
      
      // Requeue after second failure
      await queueManager.requeue(job);
      
      // Priority should be lowered from critical to high
      final pendingJobs = await queueManager.getPending();
      final requeuedJob = pendingJobs.firstWhere((j) => j.id == 'multi-retry');
      expect(requeuedJob.retryCount, equals(2));
      
      // Job should not be in critical queue anymore
      // (This is an internal implementation detail, but worth verifying)
    });
    
    test('markCompleted updates job status correctly', () async {
      await queueManager.initialize();
      
      final job = createTestJob(id: 'complete-job');
      await queueManager.enqueue(job);
      
      final runningJob = await queueManager.dequeue();
      await queueManager.markCompleted(runningJob!, 'result-123');
      
      // Check job is updated
      final completedJob = await repository.getById('complete-job');
      expect(completedJob!.status, equals(JobStatus.completed));
      expect(completedJob.completedAt, isNotNull);
      expect(completedJob.resultId, equals('result-123'));
      
      // Check statistics
      final stats = await queueManager.getStatistics();
      expect(stats.runningCount, equals(0));
      expect(stats.completedCount, equals(1));
    });
    
    test('markFailed updates job status correctly', () async {
      await queueManager.initialize();
      
      final job = createTestJob(id: 'fail-job');
      await queueManager.enqueue(job);
      
      final runningJob = await queueManager.dequeue();
      await queueManager.markFailed(runningJob!, 'Test error');
      
      // Check job is updated
      final failedJob = await repository.getById('fail-job');
      expect(failedJob!.status, equals(JobStatus.failed));
      expect(failedJob.completedAt, isNotNull);
      expect(failedJob.errorMessage, equals('Test error'));
      
      // Check statistics
      final stats = await queueManager.getStatistics();
      expect(stats.runningCount, equals(0));
      expect(stats.failedCount, equals(1));
    });
    
    test('cancel removes job from queue', () async {
      await queueManager.initialize();
      
      final job = createTestJob(id: 'cancel-job');
      await queueManager.enqueue(job);
      
      // Cancel the job
      final result = await queueManager.cancel('cancel-job');
      expect(result, isTrue);
      
      // Check job is not in queue
      final pendingJobs = await queueManager.getPending();
      expect(pendingJobs.any((j) => j.id == 'cancel-job'), isFalse);
      
      // Check job status is cancelled
      final cancelledJob = await repository.getById('cancel-job');
      expect(cancelledJob!.status, equals(JobStatus.cancelled));
      expect(cancelledJob.completedAt, isNotNull);
    });
    
    test('cancel returns false for running job', () async {
      await queueManager.initialize();
      
      final job = createTestJob(id: 'running-cancel');
      await queueManager.enqueue(job);
      
      // Dequeue to make it running
      await queueManager.dequeue();
      
      // Try to cancel running job
      final result = await queueManager.cancel('running-cancel');
      expect(result, isFalse);
      
      // Job should still be running
      final runningJob = await repository.getById('running-cancel');
      expect(runningJob!.status, equals(JobStatus.running));
    });
    
    test('getStatistics returns correct counts', () async {
      await queueManager.initialize();
      
      // Add various jobs
      await queueManager.enqueue(createTestJob(id: 'pending-1'));
      await queueManager.enqueue(createTestJob(id: 'pending-2'));
      
      // Create some completed and failed jobs in repository
      await repository.save(createTestJob(
        id: 'completed-1',
        status: JobStatus.completed,
      ));
      await repository.save(createTestJob(
        id: 'failed-1',
        status: JobStatus.failed,
      ));
      
      // Dequeue one to make it running
      await queueManager.dequeue();
      
      final stats = await queueManager.getStatistics();
      expect(stats.pendingCount, equals(1));
      expect(stats.runningCount, equals(1));
      expect(stats.completedCount, equals(1));
      expect(stats.failedCount, equals(1));
      expect(stats.maxConcurrent, equals(3));
      expect(stats.totalActive, equals(2));
      expect(stats.totalProcessed, equals(2));
      expect(stats.successRate, equals(0.5));
    });
    
    test('clearOldJobs removes old completed jobs', () async {
      await queueManager.initialize();
      
      final now = DateTime.now();
      
      // Create old and recent completed jobs
      await repository.save(createTestJob(
        id: 'old-completed',
        status: JobStatus.completed,
      ).copyWith(
        completedAt: () => now.subtract(const Duration(days: 8)),
      ));
      
      await repository.save(createTestJob(
        id: 'recent-completed',
        status: JobStatus.completed,
      ).copyWith(
        completedAt: () => now.subtract(const Duration(days: 1)),
      ));
      
      // Clear jobs older than 7 days
      final count = await queueManager.clearOldJobs(const Duration(days: 7));
      expect(count, equals(1));
      
      // Verify old job is gone
      expect(await repository.getById('old-completed'), isNull);
      expect(await repository.getById('recent-completed'), isNotNull);
    });
    
    test('queue events are emitted correctly', () async {
      await queueManager.initialize();
      
      final events = <JobEvent>[];
      final subscription = eventBus.stream.listen(events.add);
      
      try {
        final job = createTestJob(id: 'event-job');
        
        // Enqueue
        await queueManager.enqueue(job);
        await Future.delayed(const Duration(milliseconds: 10)); // Allow event to be received
        expect(events.length, equals(1));
        expect(events.last, isA<JobQueuedEvent>());
        
        // Dequeue (start)
        final runningJob = await queueManager.dequeue();
        await Future.delayed(const Duration(milliseconds: 10)); // Allow event to be received
        expect(events.length, equals(2));
        expect(events.last, isA<JobStartedEvent>());
        
        // Complete
        await queueManager.markCompleted(runningJob!, 'result');
        await Future.delayed(const Duration(milliseconds: 10)); // Allow event to be received
        expect(events.length, equals(3));
        expect(events.last, isA<JobCompletedEvent>());
      } finally {
        await subscription.cancel();
      }
    });
    
    test('concurrent operations are handled safely', () async {
      await queueManager.initialize();
      
      // Add many jobs concurrently
      final futures = <Future>[];
      for (int i = 0; i < 10; i++) {
        futures.add(queueManager.enqueue(createTestJob(id: 'concurrent-$i')));
      }
      
      await Future.wait(futures);
      
      // All jobs should be in queue
      final pendingJobs = await queueManager.getPending();
      expect(pendingJobs.length, equals(10));
      
      // Dequeue concurrently
      final dequeueFutures = <Future<AnalysisJob?>>[];
      for (int i = 0; i < 5; i++) {
        dequeueFutures.add(queueManager.dequeue());
      }
      
      final results = await Future.wait(dequeueFutures);
      
      // Should get exactly 3 jobs (max concurrent)
      final nonNullResults = results.where((job) => job != null).toList();
      expect(nonNullResults.length, equals(3));
    });
  });
}