import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';

void main() {
  group('AnalysisJob', () {
    late DateTime createdAt;
    late AnalysisJob testJob;
    
    setUp(() {
      createdAt = DateTime(2024, 1, 20, 10, 0, 0);
      testJob = AnalysisJob(
        id: 'test-123',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: createdAt,
        retryCount: 0,
      );
    });
    
    test('creates job with required fields', () {
      expect(testJob.id, equals('test-123'));
      expect(testJob.ticker, equals('AAPL'));
      expect(testJob.tradeDate, equals('2024-01-20'));
      expect(testJob.status, equals(JobStatus.pending));
      expect(testJob.priority, equals(JobPriority.normal));
      expect(testJob.createdAt, equals(createdAt));
      expect(testJob.retryCount, equals(0));
      expect(testJob.maxRetries, equals(3)); // default
    });
    
    test('creates job with all fields', () {
      final startedAt = createdAt.add(const Duration(minutes: 5));
      final completedAt = startedAt.add(const Duration(minutes: 2));
      
      final completeJob = AnalysisJob(
        id: 'test-456',
        ticker: 'GOOGL',
        tradeDate: '2024-01-21',
        status: JobStatus.completed,
        priority: JobPriority.high,
        createdAt: createdAt,
        startedAt: startedAt,
        completedAt: completedAt,
        resultId: 'result-789',
        errorMessage: null,
        retryCount: 0,
        maxRetries: 5,
      );
      
      expect(completeJob.startedAt, equals(startedAt));
      expect(completeJob.completedAt, equals(completedAt));
      expect(completeJob.resultId, equals('result-789'));
      expect(completeJob.errorMessage, isNull);
      expect(completeJob.maxRetries, equals(5));
    });
    
    group('copyWith', () {
      test('copies all fields when specified', () {
        final newTime = DateTime.now();
        final copied = testJob.copyWith(
          id: 'new-id',
          ticker: 'TSLA',
          tradeDate: '2024-01-22',
          status: JobStatus.running,
          priority: JobPriority.critical,
          createdAt: newTime,
          startedAt: () => newTime,
          completedAt: () => newTime,
          resultId: () => 'result-123',
          errorMessage: () => 'Test error',
          retryCount: 2,
          maxRetries: 5,
        );
        
        expect(copied.id, equals('new-id'));
        expect(copied.ticker, equals('TSLA'));
        expect(copied.tradeDate, equals('2024-01-22'));
        expect(copied.status, equals(JobStatus.running));
        expect(copied.priority, equals(JobPriority.critical));
        expect(copied.createdAt, equals(newTime));
        expect(copied.startedAt, equals(newTime));
        expect(copied.completedAt, equals(newTime));
        expect(copied.resultId, equals('result-123'));
        expect(copied.errorMessage, equals('Test error'));
        expect(copied.retryCount, equals(2));
        expect(copied.maxRetries, equals(5));
      });
      
      test('preserves original fields when not specified', () {
        final copied = testJob.copyWith(status: JobStatus.running);
        
        expect(copied.id, equals(testJob.id));
        expect(copied.ticker, equals(testJob.ticker));
        expect(copied.tradeDate, equals(testJob.tradeDate));
        expect(copied.status, equals(JobStatus.running));
        expect(copied.priority, equals(testJob.priority));
        expect(copied.createdAt, equals(testJob.createdAt));
        expect(copied.retryCount, equals(testJob.retryCount));
      });
    });
    
    group('canRetry', () {
      test('returns true when retries available and not terminal', () {
        final job = testJob.copyWith(retryCount: 1);
        expect(job.canRetry, isTrue);
      });
      
      test('returns false when max retries reached', () {
        final job = testJob.copyWith(retryCount: 3);
        expect(job.canRetry, isFalse);
      });
      
      test('returns false for terminal states', () {
        final completedJob = testJob.copyWith(status: JobStatus.completed);
        expect(completedJob.canRetry, isFalse);
        
        final failedJob = testJob.copyWith(status: JobStatus.failed);
        expect(failedJob.canRetry, isFalse);
        
        final cancelledJob = testJob.copyWith(status: JobStatus.cancelled);
        expect(cancelledJob.canRetry, isFalse);
      });
    });
    
    group('isOverdue', () {
      test('returns false for non-running jobs', () {
        expect(testJob.isOverdue, isFalse);
        
        final queuedJob = testJob.copyWith(status: JobStatus.queued);
        expect(queuedJob.isOverdue, isFalse);
      });
      
      test('returns false for running job without startedAt', () {
        final runningJob = testJob.copyWith(status: JobStatus.running);
        expect(runningJob.isOverdue, isFalse);
      });
      
      test('returns false for running job under 5 minutes', () {
        final startedAt = DateTime.now().subtract(const Duration(minutes: 3));
        final runningJob = testJob.copyWith(
          status: JobStatus.running,
          startedAt: () => startedAt,
        );
        expect(runningJob.isOverdue, isFalse);
      });
      
      test('returns true for running job over 5 minutes', () {
        final startedAt = DateTime.now().subtract(const Duration(minutes: 6));
        final runningJob = testJob.copyWith(
          status: JobStatus.running,
          startedAt: () => startedAt,
        );
        expect(runningJob.isOverdue, isTrue);
      });
    });
    
    group('duration', () {
      test('returns null when not started', () {
        expect(testJob.duration, isNull);
      });
      
      test('returns null when started but not completed', () {
        final job = testJob.copyWith(startedAt: () => createdAt);
        expect(job.duration, isNull);
      });
      
      test('calculates duration correctly', () {
        final startedAt = createdAt.add(const Duration(minutes: 5));
        final completedAt = startedAt.add(const Duration(minutes: 2));
        
        final job = testJob.copyWith(
          startedAt: () => startedAt,
          completedAt: () => completedAt,
        );
        
        expect(job.duration, equals(const Duration(minutes: 2)));
      });
    });
    
    group('queueTime', () {
      test('returns null when not started', () {
        expect(testJob.queueTime, isNull);
      });
      
      test('calculates queue time correctly', () {
        final startedAt = createdAt.add(const Duration(minutes: 10));
        final job = testJob.copyWith(startedAt: () => startedAt);
        
        expect(job.queueTime, equals(const Duration(minutes: 10)));
      });
    });
    
    test('toString provides readable representation', () {
      final str = testJob.toString();
      expect(str, contains('AnalysisJob'));
      expect(str, contains('test-123'));
      expect(str, contains('AAPL'));
      expect(str, contains('2024-01-20'));
      expect(str, contains('Pending'));
      expect(str, contains('Normal'));
      expect(str, contains('0/3'));
    });
    
    test('equality works correctly', () {
      final job1 = AnalysisJob(
        id: 'test-123',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: createdAt,
        retryCount: 0,
      );
      
      final job2 = AnalysisJob(
        id: 'test-123',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: createdAt,
        retryCount: 0,
      );
      
      final job3 = AnalysisJob(
        id: 'different-id',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: createdAt,
        retryCount: 0,
      );
      
      expect(job1, equals(job2));
      expect(job1, isNot(equals(job3)));
    });
  });
}