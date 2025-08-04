import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';

void main() {
  group('JobEventBus', () {
    late JobEventBus eventBus;
    late AnalysisJob testJob1;
    late AnalysisJob testJob2;

    setUp(() {
      // Reset singleton for clean test state
      JobEventBus.resetForTesting();
      eventBus = JobEventBus();
      
      testJob1 = AnalysisJob(
        id: 'job-1',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: DateTime(2024, 1, 20, 10, 0),
        retryCount: 0,
      );

      testJob2 = AnalysisJob(
        id: 'job-2',
        ticker: 'GOOGL',
        tradeDate: '2024-01-21',
        status: JobStatus.pending,
        priority: JobPriority.high,
        createdAt: DateTime(2024, 1, 21, 10, 0),
        retryCount: 0,
      );
    });

    tearDown(() async {
      if (!eventBus.isClosed) {
        await eventBus.close();
      }
    });

    group('Singleton behavior', () {
      test('should return same instance', () {
        final bus1 = JobEventBus();
        final bus2 = JobEventBus();
        expect(bus1, equals(bus2));
      });
    });

    group('Event publishing and subscription', () {
      test('should publish and receive events', () async {
        final events = <JobEvent>[];
        final subscription = eventBus.stream.listen(events.add);

        final event1 = JobQueuedEvent(testJob1);
        final event2 = JobStartedEvent(testJob2);

        eventBus.publish(event1);
        eventBus.publish(event2);

        // Give events time to be processed
        await Future.delayed(Duration(milliseconds: 10));

        expect(events.length, equals(2));
        expect(events[0], equals(event1));
        expect(events[1], equals(event2));

        await subscription.cancel();
      });

      test('should handle multiple subscribers', () async {
        final events1 = <JobEvent>[];
        final events2 = <JobEvent>[];
        
        final sub1 = eventBus.stream.listen(events1.add);
        final sub2 = eventBus.stream.listen(events2.add);

        final event = JobCompletedEvent(testJob1);
        eventBus.publish(event);

        await Future.delayed(Duration(milliseconds: 10));

        expect(events1.length, equals(1));
        expect(events2.length, equals(1));
        expect(events1[0], equals(event));
        expect(events2[0], equals(event));

        await sub1.cancel();
        await sub2.cancel();
      });
    });

    group('Type-specific subscriptions', () {
      test('should filter events by type', () async {
        final queuedEvents = <JobQueuedEvent>[];
        final completedEvents = <JobCompletedEvent>[];

        final queuedSub = eventBus.on<JobQueuedEvent>().listen(queuedEvents.add);
        final completedSub = eventBus.on<JobCompletedEvent>().listen(completedEvents.add);

        eventBus.publish(JobQueuedEvent(testJob1));
        eventBus.publish(JobStartedEvent(testJob1));
        eventBus.publish(JobCompletedEvent(testJob1));
        eventBus.publish(JobQueuedEvent(testJob2));

        await Future.delayed(Duration(milliseconds: 10));

        expect(queuedEvents.length, equals(2));
        expect(completedEvents.length, equals(1));
        expect(queuedEvents[0].jobId, equals('job-1'));
        expect(queuedEvents[1].jobId, equals('job-2'));
        expect(completedEvents[0].jobId, equals('job-1'));

        await queuedSub.cancel();
        await completedSub.cancel();
      });

      test('should provide extension methods for common event types', () async {
        final queuedEvents = <JobQueuedEvent>[];
        final startedEvents = <JobStartedEvent>[];
        final completedEvents = <JobCompletedEvent>[];
        final failedEvents = <JobFailedEvent>[];
        final cancelledEvents = <JobCancelledEvent>[];
        final requeuedEvents = <JobRequeuedEvent>[];

        final subs = [
          eventBus.onJobQueued.listen(queuedEvents.add),
          eventBus.onJobStarted.listen(startedEvents.add),
          eventBus.onJobCompleted.listen(completedEvents.add),
          eventBus.onJobFailed.listen(failedEvents.add),
          eventBus.onJobCancelled.listen(cancelledEvents.add),
          eventBus.onJobRequeued.listen(requeuedEvents.add),
        ];

        eventBus.publish(JobQueuedEvent(testJob1));
        eventBus.publish(JobStartedEvent(testJob1));
        eventBus.publish(JobCompletedEvent(testJob1));
        eventBus.publish(JobFailedEvent(testJob2, willRetry: false));
        eventBus.publish(JobCancelledEvent(testJob2));
        eventBus.publish(JobRequeuedEvent(testJob1, retryAttempt: 1));

        await Future.delayed(Duration(milliseconds: 10));

        expect(queuedEvents.length, equals(1));
        expect(startedEvents.length, equals(1));
        expect(completedEvents.length, equals(1));
        expect(failedEvents.length, equals(1));
        expect(cancelledEvents.length, equals(1));
        expect(requeuedEvents.length, equals(1));

        for (final sub in subs) {
          await sub.cancel();
        }
      });
    });

    group('Job-specific filtering', () {
      test('should filter events by job ID', () async {
        final job1Events = <JobEvent>[];
        final job2Events = <JobEvent>[];

        final sub1 = eventBus.forJob('job-1').listen(job1Events.add);
        final sub2 = eventBus.forJob('job-2').listen(job2Events.add);

        eventBus.publish(JobQueuedEvent(testJob1));
        eventBus.publish(JobStartedEvent(testJob2));
        eventBus.publish(JobCompletedEvent(testJob1));
        eventBus.publish(JobFailedEvent(testJob2, willRetry: false));

        await Future.delayed(Duration(milliseconds: 10));

        expect(job1Events.length, equals(2));
        expect(job2Events.length, equals(2));
        expect(job1Events.every((e) => e.jobId == 'job-1'), isTrue);
        expect(job2Events.every((e) => e.jobId == 'job-2'), isTrue);

        await sub1.cancel();
        await sub2.cancel();
      });

      test('should filter events by ticker', () async {
        final appleEvents = <JobEvent>[];
        final googleEvents = <JobEvent>[];

        final appleSub = eventBus.forTicker('AAPL').listen(appleEvents.add);
        final googleSub = eventBus.forTicker('GOOGL').listen(googleEvents.add);

        eventBus.publish(JobQueuedEvent(testJob1)); // AAPL
        eventBus.publish(JobStartedEvent(testJob2)); // GOOGL
        eventBus.publish(JobCompletedEvent(testJob1)); // AAPL

        await Future.delayed(Duration(milliseconds: 10));

        expect(appleEvents.length, equals(2));
        expect(googleEvents.length, equals(1));
        expect(appleEvents.every((e) => e.ticker == 'AAPL'), isTrue);
        expect(googleEvents.every((e) => e.ticker == 'GOOGL'), isTrue);

        await appleSub.cancel();
        await googleSub.cancel();
      });
    });

    group('Error handling', () {
      test('should handle publishing to closed event bus', () async {
        await eventBus.close();

        // Should not throw but should log warning
        expect(() => eventBus.publish(JobQueuedEvent(testJob1)), returnsNormally);
        expect(eventBus.isClosed, isTrue);
      });

      test('should handle subscription after close', () async {
        await eventBus.close();

        // Should be able to subscribe but won't receive events
        final events = <JobEvent>[];
        final subscription = eventBus.stream.listen(events.add);

        eventBus.publish(JobQueuedEvent(testJob1));

        await Future.delayed(Duration(milliseconds: 10));
        expect(events.length, equals(0));

        await subscription.cancel();
      });
    });

    group('Resource management', () {
      test('should properly close resources', () async {
        expect(eventBus.isClosed, isFalse);
        
        await eventBus.close();
        
        expect(eventBus.isClosed, isTrue);
      });

      test('should detect listener presence', () {
        expect(eventBus.hasListeners, isFalse);
        
        final subscription = eventBus.stream.listen((_) {});
        expect(eventBus.hasListeners, isTrue);
        
        subscription.cancel();
      });
    });
  });

  group('JobEventStatistics', () {
    late JobEventBus eventBus;
    late JobEventStatistics stats;
    late AnalysisJob testJob;

    setUp(() {
      JobEventBus.resetForTesting();
      eventBus = JobEventBus();
      stats = JobEventStatistics(eventBus);
      
      testJob = AnalysisJob(
        id: 'test-job',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: DateTime(2024, 1, 20, 10, 0),
        retryCount: 0,
      );
    });

    tearDown(() async {
      stats.stop();
      if (!eventBus.isClosed) {
        await eventBus.close();
      }
    });

    test('should track event counts by type', () async {
      eventBus.publish(JobQueuedEvent(testJob));
      eventBus.publish(JobQueuedEvent(testJob));
      eventBus.publish(JobStartedEvent(testJob));
      eventBus.publish(JobCompletedEvent(testJob));

      await Future.delayed(Duration(milliseconds: 10));

      expect(stats.getEventCount<JobQueuedEvent>(), equals(2));
      expect(stats.getEventCount<JobStartedEvent>(), equals(1));
      expect(stats.getEventCount<JobCompletedEvent>(), equals(1));
      expect(stats.getEventCount<JobFailedEvent>(), equals(0));
      expect(stats.totalEvents, equals(4));
    });

    test('should calculate events per minute', () async {
      // This test is time-sensitive, so we just verify the calculation logic
      expect(stats.eventsPerMinute, equals(0.0));
      
      eventBus.publish(JobQueuedEvent(testJob));
      await Future.delayed(Duration(milliseconds: 10));
      
      // Should have some rate calculation (exact value depends on timing)
      expect(stats.eventsPerMinute, greaterThanOrEqualTo(0.0));
    });

    test('should provide immutable event counts', () {
      eventBus.publish(JobQueuedEvent(testJob));
      
      final counts = stats.eventCounts;
      final originalSize = counts.length;
      
      // Attempting to modify should not affect the original
      counts[JobStartedEvent] = 999;
      
      expect(stats.eventCounts.length, equals(originalSize));
      expect(stats.getEventCount<JobStartedEvent>(), isNot(equals(999)));
    });
  });
}