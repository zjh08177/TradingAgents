import 'dart:async';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';

void main() {
  group('Job Event Integration Tests', () {
    late Directory tempDir;
    late HiveJobRepository repository;
    late JobEventBus eventBus;
    late JobQueueManager queueManager;
    late List<JobEvent> capturedEvents;
    late StreamSubscription<JobEvent> eventSubscription;

    setUpAll(() async {
      tempDir = await Directory.systemTemp.createTemp('hive_event_test_');
      Hive.init(tempDir.path);
      Hive.registerAdapter(HiveAnalysisJobAdapter());
    });

    setUp(() async {
      // Reset singleton for clean test state
      JobEventBus.resetForTesting();
      
      repository = HiveJobRepository();
      await repository.init();
      
      eventBus = JobEventBus();
      queueManager = JobQueueManager(
        repository: repository,
        eventBus: eventBus,
        maxConcurrentJobs: 3,
      );
      
      await queueManager.initialize();
      
      capturedEvents = [];
      eventSubscription = eventBus.stream.listen(capturedEvents.add);
    });

    tearDown(() async {
      await eventSubscription.cancel();
      await repository.close();
      if (!eventBus.isClosed) {
        await eventBus.close();
      }
      queueManager.dispose();
    });

    tearDownAll(() async {
      await Hive.close();
      if (tempDir.existsSync()) {
        tempDir.deleteSync(recursive: true);
      }
    });

    group('Queue Manager Event Integration', () {
      test('should emit JobQueuedEvent when job is enqueued', () async {
        final job = AnalysisJob(
          id: 'test-job-1',
          ticker: 'AAPL',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        await queueManager.enqueue(job);
        await Future.delayed(Duration(milliseconds: 10));

        expect(capturedEvents.length, equals(1));
        expect(capturedEvents[0], isA<JobQueuedEvent>());
        expect(capturedEvents[0].jobId, equals('test-job-1'));
        expect(capturedEvents[0].ticker, equals('AAPL'));
      });

      test('should emit JobStartedEvent when job is dequeued', () async {
        final job = AnalysisJob(
          id: 'test-job-2',
          ticker: 'GOOGL',
          tradeDate: '2024-01-21',
          status: JobStatus.pending,
          priority: JobPriority.high,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        await queueManager.enqueue(job);
        final dequeuedJob = await queueManager.dequeue();
        await Future.delayed(Duration(milliseconds: 10));

        expect(capturedEvents.length, equals(2));
        expect(capturedEvents[0], isA<JobQueuedEvent>());
        expect(capturedEvents[1], isA<JobStartedEvent>());
        expect(capturedEvents[1].jobId, equals('test-job-2'));
        expect(dequeuedJob?.status, equals(JobStatus.running));
      });

      test('should emit JobCompletedEvent when job is marked complete', () async {
        final job = AnalysisJob(
          id: 'test-job-3',
          ticker: 'MSFT',
          tradeDate: '2024-01-22',
          status: JobStatus.running,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          startedAt: DateTime.now(),
          retryCount: 0,
        );

        await repository.save(job);
        await queueManager.markCompleted(job, 'result-123');
        await Future.delayed(Duration(milliseconds: 10));

        expect(capturedEvents.length, equals(1));
        expect(capturedEvents[0], isA<JobCompletedEvent>());
        final completedEvent = capturedEvents[0] as JobCompletedEvent;
        expect(completedEvent.jobId, equals('test-job-3'));
        expect(completedEvent.resultId, equals('result-123'));
      });

      test('should emit JobFailedEvent when job is marked failed', () async {
        final job = AnalysisJob(
          id: 'test-job-4',
          ticker: 'TSLA',
          tradeDate: '2024-01-23',
          status: JobStatus.running,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          startedAt: DateTime.now(),
          retryCount: 0,
        );

        await repository.save(job);
        await queueManager.markFailed(job, 'Network timeout');
        await Future.delayed(Duration(milliseconds: 10));

        expect(capturedEvents.length, equals(1));
        expect(capturedEvents[0], isA<JobFailedEvent>());
        final failedEvent = capturedEvents[0] as JobFailedEvent;
        expect(failedEvent.jobId, equals('test-job-4'));
        expect(failedEvent.errorMessage, equals('Network timeout'));
        expect(failedEvent.willRetry, isTrue); // Can retry since retryCount is 0
      });

      test('should emit JobCancelledEvent when job is cancelled', () async {
        final job = AnalysisJob(
          id: 'test-job-5',
          ticker: 'AMZN',
          tradeDate: '2024-01-24',
          status: JobStatus.pending,
          priority: JobPriority.low,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        await queueManager.enqueue(job);
        capturedEvents.clear(); // Clear the queued event
        
        final cancelled = await queueManager.cancel('test-job-5');
        await Future.delayed(Duration(milliseconds: 10));

        expect(cancelled, isTrue);
        expect(capturedEvents.length, equals(1));
        expect(capturedEvents[0], isA<JobCancelledEvent>());
        final cancelledEvent = capturedEvents[0] as JobCancelledEvent;
        expect(cancelledEvent.jobId, equals('test-job-5'));
        expect(cancelledEvent.reason, equals('Cancelled by user'));
      });

      test('should emit JobRequeuedEvent when job is requeued', () async {
        final job = AnalysisJob(
          id: 'test-job-6',
          ticker: 'NFLX',
          tradeDate: '2024-01-25',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 1,
        );

        await repository.save(job);
        await queueManager.requeue(job);
        await Future.delayed(Duration(milliseconds: 10));

        expect(capturedEvents.length, equals(1));
        expect(capturedEvents[0], isA<JobRequeuedEvent>());
        final requeuedEvent = capturedEvents[0] as JobRequeuedEvent;
        expect(requeuedEvent.jobId, equals('test-job-6'));
        expect(requeuedEvent.retryAttempt, equals(2)); // retryCount + 1
      });
    });

    group('Event Flow Integration', () {
      test('should emit events in correct order for full job lifecycle', () async {
        final job = AnalysisJob(
          id: 'lifecycle-job',
          ticker: 'AAPL',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        // Enqueue job
        await queueManager.enqueue(job);
        
        // Start job
        final runningJob = await queueManager.dequeue();
        
        // Complete job
        await queueManager.markCompleted(runningJob!, 'final-result');
        
        await Future.delayed(Duration(milliseconds: 10));

        expect(capturedEvents.length, equals(3));
        expect(capturedEvents[0], isA<JobQueuedEvent>());
        expect(capturedEvents[1], isA<JobStartedEvent>());
        expect(capturedEvents[2], isA<JobCompletedEvent>());
        
        // All events should be for the same job
        expect(capturedEvents.every((e) => e.jobId == 'lifecycle-job'), isTrue);
      });

      test('should emit events for failure and retry cycle', () async {
        final job = AnalysisJob(
          id: 'retry-job',
          ticker: 'MSFT',
          tradeDate: '2024-01-21',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        // Enqueue and start job
        await queueManager.enqueue(job);
        final runningJob = await queueManager.dequeue();
        
        // Fail the job
        await queueManager.markFailed(runningJob!, 'Temporary failure');
        
        // Requeue for retry
        final failedJob = await repository.getById('retry-job');
        await queueManager.requeue(failedJob!);
        
        await Future.delayed(Duration(milliseconds: 10));

        expect(capturedEvents.length, equals(4));
        expect(capturedEvents[0], isA<JobQueuedEvent>());
        expect(capturedEvents[1], isA<JobStartedEvent>());
        expect(capturedEvents[2], isA<JobFailedEvent>());
        expect(capturedEvents[3], isA<JobRequeuedEvent>());
        
        final failedEvent = capturedEvents[2] as JobFailedEvent;
        expect(failedEvent.willRetry, isTrue);
        
        final requeuedEvent = capturedEvents[3] as JobRequeuedEvent;
        expect(requeuedEvent.retryAttempt, equals(1));
      });
    });

    group('Event Filtering and Subscription', () {
      test('should filter events by job ID across lifecycle', () async {
        final job1 = AnalysisJob(
          id: 'filter-job-1',
          ticker: 'AAPL',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        final job2 = AnalysisJob(
          id: 'filter-job-2',
          ticker: 'GOOGL',
          tradeDate: '2024-01-21',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        final job1Events = <JobEvent>[];
        final job1Subscription = eventBus.forJob('filter-job-1').listen(job1Events.add);

        // Small delay to ensure subscription is active
        await Future.delayed(Duration(milliseconds: 5));

        // Process both jobs
        await queueManager.enqueue(job1);
        await queueManager.enqueue(job2);
        
        final runningJob1 = await queueManager.dequeue();
        final runningJob2 = await queueManager.dequeue();
        
        await queueManager.markCompleted(runningJob1!, 'result-1');
        await queueManager.markCompleted(runningJob2!, 'result-2');
        
        await Future.delayed(Duration(milliseconds: 10));

        // Job1-specific subscription should only receive job1 events
        expect(job1Events.length, equals(3));
        expect(job1Events.every((e) => e.jobId == 'filter-job-1'), isTrue);
        expect(job1Events[0], isA<JobQueuedEvent>());
        expect(job1Events[1], isA<JobStartedEvent>());
        expect(job1Events[2], isA<JobCompletedEvent>());

        await job1Subscription.cancel();
      });

      test('should filter events by ticker symbol', () async {
        final appleJob = AnalysisJob(
          id: 'apple-job',
          ticker: 'AAPL',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        final googleJob = AnalysisJob(
          id: 'google-job',
          ticker: 'GOOGL',
          tradeDate: '2024-01-21',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        final appleEvents = <JobEvent>[];
        final appleSubscription = eventBus.forTicker('AAPL').listen(appleEvents.add);

        // Small delay to ensure subscription is active
        await Future.delayed(Duration(milliseconds: 5));

        await queueManager.enqueue(appleJob);
        await queueManager.enqueue(googleJob);
        
        await Future.delayed(Duration(milliseconds: 10));

        expect(appleEvents.length, equals(1));
        expect(appleEvents[0].ticker, equals('AAPL'));
        expect(appleEvents[0].jobId, equals('apple-job'));

        await appleSubscription.cancel();
      });
    });

    group('Concurrent Event Handling', () {
      test('should handle multiple simultaneous events correctly', () async {
        final jobs = List.generate(5, (i) => AnalysisJob(
          id: 'concurrent-job-$i',
          ticker: 'STOCK$i',
          tradeDate: '2024-01-2${i + 1}',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        ));

        // Enqueue all jobs simultaneously
        await Future.wait(jobs.map((job) => queueManager.enqueue(job)));
        
        await Future.delayed(Duration(milliseconds: 10));

        expect(capturedEvents.length, equals(5));
        expect(capturedEvents.every((e) => e is JobQueuedEvent), isTrue);
        
        final jobIds = capturedEvents.map((e) => e.jobId).toSet();
        expect(jobIds.length, equals(5)); // All unique job IDs
      });
    });
  });
}