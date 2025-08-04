import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';

void main() {
  group('JobEvent', () {
    late AnalysisJob testJob;

    setUp(() {
      testJob = AnalysisJob(
        id: 'test-job-1',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: DateTime(2024, 1, 20, 10, 0),
        retryCount: 0,
      );
    });

    group('JobQueuedEvent', () {
      test('should create event with job details', () {
        final event = JobQueuedEvent(testJob);

        expect(event.job, equals(testJob));
        expect(event.jobId, equals('test-job-1'));
        expect(event.ticker, equals('AAPL'));
        expect(event.tradeDate, equals('2024-01-20'));
        expect(event.timestamp, isA<DateTime>());
      });

      test('should generate proper string representation', () {
        final event = JobQueuedEvent(testJob);
        final eventString = event.toString();

        expect(eventString, contains('JobQueuedEvent'));
        expect(eventString, contains('test-job-1'));
        expect(eventString, contains('AAPL'));
      });
    });

    group('JobStartedEvent', () {
      test('should create event with job details', () {
        final runningJob = testJob.copyWith(status: JobStatus.running);
        final event = JobStartedEvent(runningJob);

        expect(event.job, equals(runningJob));
        expect(event.jobId, equals('test-job-1'));
        expect(event.ticker, equals('AAPL'));
        expect(event.tradeDate, equals('2024-01-20'));
      });
    });

    group('JobCompletedEvent', () {
      test('should create event with result ID', () {
        final completedJob = testJob.copyWith(status: JobStatus.completed);
        const resultId = 'result-123';
        final event = JobCompletedEvent(completedJob, resultId: resultId);

        expect(event.job, equals(completedJob));
        expect(event.resultId, equals(resultId));
        expect(event.jobId, equals('test-job-1'));
      });

      test('should create event without result ID', () {
        final completedJob = testJob.copyWith(status: JobStatus.completed);
        final event = JobCompletedEvent(completedJob);

        expect(event.job, equals(completedJob));
        expect(event.resultId, isNull);
      });

      test('should generate proper string representation with result ID', () {
        final completedJob = testJob.copyWith(status: JobStatus.completed);
        const resultId = 'result-123';
        final event = JobCompletedEvent(completedJob, resultId: resultId);
        final eventString = event.toString();

        expect(eventString, contains('JobCompletedEvent'));
        expect(eventString, contains('test-job-1'));
        expect(eventString, contains('result-123'));
      });
    });

    group('JobFailedEvent', () {
      test('should create event with error message and retry flag', () {
        final failedJob = testJob.copyWith(status: JobStatus.failed);
        const errorMessage = 'Network timeout';
        final event = JobFailedEvent(failedJob, errorMessage: errorMessage, willRetry: true);

        expect(event.job, equals(failedJob));
        expect(event.errorMessage, equals(errorMessage));
        expect(event.willRetry, isTrue);
        expect(event.jobId, equals('test-job-1'));
      });

      test('should create event without error message', () {
        final failedJob = testJob.copyWith(status: JobStatus.failed);
        final event = JobFailedEvent(failedJob, willRetry: false);

        expect(event.job, equals(failedJob));
        expect(event.errorMessage, isNull);
        expect(event.willRetry, isFalse);
      });

      test('should generate proper string representation', () {
        final failedJob = testJob.copyWith(status: JobStatus.failed);
        const errorMessage = 'Connection failed';
        final event = JobFailedEvent(failedJob, errorMessage: errorMessage, willRetry: true);
        final eventString = event.toString();

        expect(eventString, contains('JobFailedEvent'));
        expect(eventString, contains('test-job-1'));
        expect(eventString, contains('Connection failed'));
        expect(eventString, contains('willRetry: true'));
      });
    });

    group('JobCancelledEvent', () {
      test('should create event with cancellation reason', () {
        final cancelledJob = testJob.copyWith(status: JobStatus.cancelled);
        const reason = 'User requested cancellation';
        final event = JobCancelledEvent(cancelledJob, reason: reason);

        expect(event.job, equals(cancelledJob));
        expect(event.reason, equals(reason));
        expect(event.jobId, equals('test-job-1'));
      });

      test('should create event without reason', () {
        final cancelledJob = testJob.copyWith(status: JobStatus.cancelled);
        final event = JobCancelledEvent(cancelledJob);

        expect(event.job, equals(cancelledJob));
        expect(event.reason, isNull);
      });

      test('should generate proper string representation', () {
        final cancelledJob = testJob.copyWith(status: JobStatus.cancelled);
        const reason = 'Timeout';
        final event = JobCancelledEvent(cancelledJob, reason: reason);
        final eventString = event.toString();

        expect(eventString, contains('JobCancelledEvent'));
        expect(eventString, contains('test-job-1'));
        expect(eventString, contains('Timeout'));
      });
    });

    group('JobRequeuedEvent', () {
      test('should create event with retry attempt and delay', () {
        final requeuedJob = testJob.copyWith(retryCount: 1);
        const retryAttempt = 1;
        const retryDelay = Duration(seconds: 30);
        final event = JobRequeuedEvent(requeuedJob, retryAttempt: retryAttempt, retryDelay: retryDelay);

        expect(event.job, equals(requeuedJob));
        expect(event.retryAttempt, equals(retryAttempt));
        expect(event.retryDelay, equals(retryDelay));
        expect(event.jobId, equals('test-job-1'));
      });

      test('should create event without delay', () {
        final requeuedJob = testJob.copyWith(retryCount: 2);
        const retryAttempt = 2;
        final event = JobRequeuedEvent(requeuedJob, retryAttempt: retryAttempt);

        expect(event.job, equals(requeuedJob));
        expect(event.retryAttempt, equals(retryAttempt));
        expect(event.retryDelay, isNull);
      });

      test('should generate proper string representation', () {
        final requeuedJob = testJob.copyWith(retryCount: 1);
        const retryAttempt = 1;
        const retryDelay = Duration(minutes: 1);
        final event = JobRequeuedEvent(requeuedJob, retryAttempt: retryAttempt, retryDelay: retryDelay);
        final eventString = event.toString();

        expect(eventString, contains('JobRequeuedEvent'));
        expect(eventString, contains('test-job-1'));
        expect(eventString, contains('attempt: 1'));
        expect(eventString, contains('0:01:00'));
      });
    });

    group('Base JobEvent', () {
      test('should have consistent timestamp behavior', () {
        final event1 = JobQueuedEvent(testJob);
        final event2 = JobStartedEvent(testJob);

        // Timestamps should be close but not necessarily identical
        final timeDiff = event2.timestamp.difference(event1.timestamp).abs();
        expect(timeDiff.inMilliseconds, lessThan(100));
      });

      test('should provide convenient access to job properties', () {
        final event = JobCompletedEvent(testJob);

        expect(event.jobId, equals(testJob.id));
        expect(event.ticker, equals(testJob.ticker));
        expect(event.tradeDate, equals(testJob.tradeDate));
      });
    });
  });
}