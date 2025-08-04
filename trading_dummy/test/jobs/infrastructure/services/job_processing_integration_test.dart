import 'dart:async';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:mocktail/mocktail.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_processor_v2.dart';
import 'package:trading_dummy/services/langgraph_service.dart';
import 'package:trading_dummy/models/final_report.dart';

// Mock classes
class MockLangGraphService extends Mock implements ILangGraphService {}

void main() {
  group('Job Processing Integration', () {
    late HiveJobRepository repository;
    late MockLangGraphService mockAnalysisService;
    late JobQueueManager queueManager;
    late JobEventBus eventBus;
    late JobProcessorV2 processor;
    late Directory tempDir;
    
    setUpAll(() async {
      tempDir = await Directory.systemTemp.createTemp('integration_test_');
      Hive.init(tempDir.path);
      
      if (!Hive.isAdapterRegistered(20)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      JobEventBus.resetForTesting();
      repository = HiveJobRepository();
      await repository.init();
      
      mockAnalysisService = MockLangGraphService();
      eventBus = JobEventBus();
      
      queueManager = JobQueueManager(
        repository: repository,
        eventBus: eventBus,
        maxConcurrentJobs: 3,
      );
      await queueManager.initialize();
      
      processor = JobProcessorV2(
        repository: repository,
        analysisService: mockAnalysisService,
        baseUrl: 'http://test.com',
        apiKey: 'test-key',
        assistantId: 'test-assistant',
        maxConcurrentJobs: 3,
      );
      await processor.initialize();
    });
    
    tearDown(() async {
      processor.dispose();
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
      JobPriority? priority,
    }) {
      return AnalysisJob(
        id: id ?? 'test-${DateTime.now().millisecondsSinceEpoch}',
        ticker: ticker ?? 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: priority ?? JobPriority.normal,
        createdAt: DateTime.now(),
        retryCount: 0,
      );
    }
    
    test('complete job processing flow from queue to completion', () async {
      // Create and enqueue jobs
      final job1 = createTestJob(id: 'flow-1', priority: JobPriority.high);
      final job2 = createTestJob(id: 'flow-2', priority: JobPriority.normal);
      final job3 = createTestJob(id: 'flow-3', priority: JobPriority.low);
      
      await queueManager.enqueue(job1);
      await queueManager.enqueue(job2);
      await queueManager.enqueue(job3);
      
      // Verify jobs are queued
      var stats = await queueManager.getStatistics();
      expect(stats.pendingCount, equals(3));
      
      // Process jobs from queue
      final jobsToProcess = <AnalysisJob>[];
      
      // Try to dequeue all available jobs
      for (int i = 0; i < 3; i++) {
        final job = await queueManager.dequeue();
        if (job != null) {
          jobsToProcess.add(job);
        }
      }
      
      expect(jobsToProcess.length, equals(3));
      expect(jobsToProcess[0].id, equals('flow-1')); // High priority first
      
      // Process jobs in isolates
      await processor.processJobs(jobsToProcess);
      
      // Give time for processing
      await Future.delayed(const Duration(seconds: 3));
      
      // Verify all jobs completed
      final completedJob1 = await repository.getById('flow-1');
      final completedJob2 = await repository.getById('flow-2');
      final completedJob3 = await repository.getById('flow-3');
      
      expect(completedJob1!.status, equals(JobStatus.completed));
      expect(completedJob2!.status, equals(JobStatus.completed));
      expect(completedJob3!.status, equals(JobStatus.completed));
      
      // Verify queue statistics
      stats = await queueManager.getStatistics();
      expect(stats.pendingCount, equals(0));
      expect(stats.completedCount, equals(3));
    });
    
    test('queue events integrate with processor', () async {
      // Listen to queue events
      final events = <JobEvent>[];
      final subscription = eventBus.stream.listen(events.add);
      
      try {
        // Create and process a job
        final job = createTestJob(id: 'event-test');
        await queueManager.enqueue(job);
        
        // Dequeue and process
        final dequeuedJob = await queueManager.dequeue();
        expect(dequeuedJob, isNotNull);
        
        await processor.processJob(dequeuedJob!);
        
        // Mark as completed (processor would do this)
        await queueManager.markCompleted(dequeuedJob, 'result-123');
        
        // Give time for events
        await Future.delayed(const Duration(milliseconds: 100));
        
        // Verify events
        expect(events.length, greaterThanOrEqualTo(3));
        expect(events.any((e) => e is JobQueuedEvent), isTrue);
        expect(events.any((e) => e is JobStartedEvent), isTrue);
        expect(events.any((e) => e is JobCompletedEvent), isTrue);
      } finally {
        await subscription.cancel();
      }
    });
    
    test('processor handles queue retry logic', () async {
      final job = createTestJob(id: 'retry-test');
      await repository.save(job);
      
      // Simulate failure and requeue
      await queueManager.enqueue(job);
      final dequeuedJob = await queueManager.dequeue();
      
      // Mark as failed
      await queueManager.markFailed(dequeuedJob!, 'Test failure');
      
      // Requeue
      await queueManager.requeue(dequeuedJob);
      
      // Verify retry count increased
      final requeuedJobs = await queueManager.getPending();
      expect(requeuedJobs.length, equals(1));
      expect(requeuedJobs.first.retryCount, equals(1));
      
      // Process retried job
      final retriedJob = await queueManager.dequeue();
      await processor.processJob(retriedJob!);
      
      await Future.delayed(const Duration(seconds: 3));
      
      // Should complete on retry
      final finalJob = await repository.getById('retry-test');
      expect(finalJob!.status, equals(JobStatus.completed));
    });
    
    test('concurrent processing respects limits', () async {
      // Create more jobs than concurrent limit
      final jobs = List.generate(
        6,
        (i) => createTestJob(id: 'concurrent-$i'),
      );
      
      // Enqueue all jobs
      for (final job in jobs) {
        await queueManager.enqueue(job);
      }
      
      // Dequeue up to limit
      final processingJobs = <AnalysisJob>[];
      for (int i = 0; i < 3; i++) {
        final job = await queueManager.dequeue();
        if (job != null) {
          processingJobs.add(job);
        }
      }
      
      expect(processingJobs.length, equals(3));
      
      // Process them
      final processFutures = processingJobs.map((job) => processor.processJob(job)).toList();
      
      // Check processor stats
      final procStats = processor.getStats();
      expect(procStats.processingJobs, equals(3));
      
      // Wait for completion
      await Future.wait(processFutures);
      
      // Process remaining jobs
      final remainingJobs = <AnalysisJob>[];
      for (int i = 0; i < 3; i++) {
        final job = await queueManager.dequeue();
        if (job != null) {
          remainingJobs.add(job);
        }
      }
      
      await processor.processJobs(remainingJobs);
      
      // All should be completed
      for (int i = 0; i < 6; i++) {
        final job = await repository.getById('concurrent-$i');
        expect(job!.status, equals(JobStatus.completed));
      }
    });
    
    test('processor statistics reflect actual state', () async {
      // Initial state
      var stats = processor.getStats();
      expect(stats.processingJobs, equals(0));
      expect(stats.isolateStats.busyIsolates, equals(0));
      
      // Start processing jobs
      final jobs = List.generate(
        3,
        (i) => createTestJob(id: 'stats-$i'),
      );
      
      for (final job in jobs) {
        await repository.save(job);
      }
      
      // Process jobs without waiting
      final futures = jobs.map((job) => processor.processJob(job)).toList();
      
      // Check stats during processing
      await Future.delayed(const Duration(milliseconds: 100));
      stats = processor.getStats();
      expect(stats.processingJobs, equals(3));
      expect(stats.isolateStats.busyIsolates, greaterThan(0));
      
      // Wait for completion
      await Future.wait(futures);
      
      // Final stats
      stats = processor.getStats();
      expect(stats.processingJobs, equals(0));
    });
  });
}