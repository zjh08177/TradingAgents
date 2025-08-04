import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/services/job_retry_policy.dart';

void main() {
  group('JobRetryPolicy', () {
    late JobRetryPolicy policy;
    late AnalysisJob sampleJob;
    
    setUp(() {
      policy = const JobRetryPolicy();
      sampleJob = AnalysisJob(
        id: 'test-job-1',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.failed,
        priority: JobPriority.normal,
        createdAt: DateTime(2024, 1, 20, 10, 0),
        completedAt: DateTime(2024, 1, 20, 10, 5),
        retryCount: 1,
        maxRetries: 3,
        errorMessage: 'Network timeout',
      );
    });
    
    group('shouldRetry', () {
      test('returns true for retryable failed job', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          retryCount: 1,
          errorMessage: () => 'Network timeout',
        );
        
        expect(policy.shouldRetry(job), isTrue);
      });
      
      test('returns false when retry count exceeds max retries', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          retryCount: 3,
          maxRetries: 3,
        );
        
        expect(policy.shouldRetry(job), isFalse);
      });
      
      test('returns false for non-failed jobs', () {
        final job = sampleJob.copyWith(status: JobStatus.completed);
        
        expect(policy.shouldRetry(job), isFalse);
      });
      
      test('returns false for non-retryable errors', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          errorMessage: () => 'Unauthorized access',
        );
        
        expect(policy.shouldRetry(job), isFalse);
      });
      
      test('returns false for authentication errors', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          errorMessage: () => 'Authentication failed',
        );
        
        expect(policy.shouldRetry(job), isFalse);
      });
      
      test('returns false for invalid input errors', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          errorMessage: () => 'Invalid ticker symbol',
        );
        
        expect(policy.shouldRetry(job), isFalse);
      });
      
      test('returns true for unknown errors', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          errorMessage: () => null,
        );
        
        expect(policy.shouldRetry(job), isTrue);
      });
      
      test('returns true for retryable network errors', () {
        final retryableErrors = [
          'Connection timeout',
          'Server error 500',
          'Service temporarily unavailable',
          'Network unreachable',
        ];
        
        for (final error in retryableErrors) {
          final job = sampleJob.copyWith(
            status: JobStatus.failed,
            errorMessage: () => error,
          );
          
          expect(policy.shouldRetry(job), isTrue, reason: 'Error: $error');
        }
      });
    });
    
    group('getRetryDelay', () {
      test('calculates exponential backoff correctly', () {
        const policy = JobRetryPolicy(
          baseDelay: Duration(seconds: 30),
          backoffMultiplier: 2.0,
          jitterFactor: 0.0, // No jitter for predictable tests
        );
        
        // First retry (attempt 0)
        expect(policy.getRetryDelay(0), equals(const Duration(seconds: 30)));
        
        // Second retry (attempt 1)
        expect(policy.getRetryDelay(1), equals(const Duration(seconds: 60)));
        
        // Third retry (attempt 2)
        expect(policy.getRetryDelay(2), equals(const Duration(seconds: 120)));
      });
      
      test('respects maximum delay cap', () {
        const policy = JobRetryPolicy(
          baseDelay: Duration(seconds: 30),
          maxDelay: Duration(minutes: 5),
          backoffMultiplier: 10.0,
          jitterFactor: 0.0,
        );
        
        final delay = policy.getRetryDelay(5);
        expect(delay, lessThanOrEqualTo(const Duration(minutes: 5)));
      });
      
      test('throws error for negative attempt number', () {
        expect(
          () => policy.getRetryDelay(-1),
          throwsArgumentError,
        );
      });
      
      test('handles zero attempt number', () {
        expect(
          () => policy.getRetryDelay(0),
          returnsNormally,
        );
      });
      
      test('adds jitter when configured', () {
        const policy = JobRetryPolicy(
          baseDelay: Duration(seconds: 30),
          backoffMultiplier: 2.0,
          jitterFactor: 0.2,
        );
        
        final delays = List.generate(10, (_) => policy.getRetryDelay(1));
        
        // Delays should vary due to jitter
        final uniqueDelays = delays.toSet();
        expect(uniqueDelays.length, greaterThan(1), reason: 'Jitter should create variation');
        
        // All delays should be within reasonable range
        for (final delay in delays) {
          expect(delay.inMilliseconds, greaterThan(48000)); // 60s - 20%
          expect(delay.inMilliseconds, lessThan(72000)); // 60s + 20%
        }
      });
    });
    
    group('getNextRetryTime', () {
      test('returns correct next retry time for retryable job', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          retryCount: 1,
          completedAt: () => DateTime(2024, 1, 20, 10, 5),
        );
        
        const policy = JobRetryPolicy(
          baseDelay: Duration(minutes: 1),
          backoffMultiplier: 2.0,
          jitterFactor: 0.0,
        );
        
        final nextRetryTime = policy.getNextRetryTime(job);
        expect(nextRetryTime, isNotNull);
        
        // Should be 2 minutes after completion time (attempt 1 with 2x multiplier)
        final expectedTime = DateTime(2024, 1, 20, 10, 7);
        expect(nextRetryTime, equals(expectedTime));
      });
      
      test('returns null for non-retryable job', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          retryCount: 3,
          maxRetries: 3,
        );
        
        final nextRetryTime = policy.getNextRetryTime(job);
        expect(nextRetryTime, isNull);
      });
      
      test('uses current time when completedAt is null', () {
        final now = DateTime.now();
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          retryCount: 0,
          completedAt: () => null,
        );
        
        const policy = JobRetryPolicy(
          baseDelay: Duration(minutes: 1),
          jitterFactor: 0.0,
        );
        
        final nextRetryTime = policy.getNextRetryTime(job);
        expect(nextRetryTime, isNotNull);
        
        // Should be approximately 1 minute from now
        final timeDiff = nextRetryTime!.difference(now);
        expect(timeDiff.inSeconds, closeTo(60, 5)); // Allow 5 second tolerance
      });
    });
    
    group('Factory constructors', () {
      test('highPriority creates policy with faster retries', () {
        final policy = JobRetryPolicy.highPriority();
        
        expect(policy.maxRetries, equals(5));
        expect(policy.baseDelay, equals(const Duration(seconds: 15)));
        expect(policy.maxDelay, equals(const Duration(minutes: 15)));
        expect(policy.backoffMultiplier, equals(1.5));
        expect(policy.jitterFactor, equals(0.1));
      });
      
      test('lowPriority creates policy with slower retries', () {
        final policy = JobRetryPolicy.lowPriority();
        
        expect(policy.maxRetries, equals(2));
        expect(policy.baseDelay, equals(const Duration(minutes: 2)));
        expect(policy.maxDelay, equals(const Duration(hours: 1)));
        expect(policy.backoffMultiplier, equals(3.0));
        expect(policy.jitterFactor, equals(0.3));
      });
      
      test('testing creates policy with very short delays', () {
        final policy = JobRetryPolicy.testing();
        
        expect(policy.maxRetries, equals(3));
        expect(policy.baseDelay, equals(const Duration(milliseconds: 100)));
        expect(policy.maxDelay, equals(const Duration(seconds: 10)));
        expect(policy.backoffMultiplier, equals(2.0));
        expect(policy.jitterFactor, equals(0.0));
      });
    });
    
    group('Edge cases', () {
      test('handles very high attempt numbers', () {
        const policy = JobRetryPolicy(
          baseDelay: Duration(seconds: 1),
          maxDelay: Duration(minutes: 10),
          jitterFactor: 0.0,
        );
        
        final delay = policy.getRetryDelay(100);
        expect(delay, lessThanOrEqualTo(const Duration(minutes: 10)));
      });
      
      test('handles empty error message', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          errorMessage: () => '',
        );
        
        expect(policy.shouldRetry(job), isTrue);
      });
      
      test('error patterns are case insensitive', () {
        final job = sampleJob.copyWith(
          status: JobStatus.failed,
          errorMessage: () => 'UNAUTHORIZED ACCESS',
        );
        
        expect(policy.shouldRetry(job), isFalse);
      });
    });
  });
}