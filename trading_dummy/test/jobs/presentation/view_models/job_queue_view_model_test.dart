import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/application/use_cases/queue_analysis_use_case.dart';
import 'package:trading_dummy/jobs/application/use_cases/get_job_status_use_case.dart';
import 'package:trading_dummy/jobs/application/use_cases/cancel_job_use_case.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';
import 'package:trading_dummy/jobs/presentation/view_models/job_queue_view_model.dart';

// Mock classes
class MockQueueAnalysisUseCase extends Mock implements QueueAnalysisUseCase {}
class MockGetJobStatusUseCase extends Mock implements GetJobStatusUseCase {}
class MockCancelJobUseCase extends Mock implements CancelJobUseCase {}

void main() {
  group('JobQueueViewModel', () {
    late MockQueueAnalysisUseCase mockQueueAnalysis;
    late MockGetJobStatusUseCase mockGetJobStatus;
    late MockCancelJobUseCase mockCancelJob;
    late JobEventBus eventBus;
    late JobQueueViewModel viewModel;
    
    setUpAll(() async {
      // No Hive initialization needed
      
      // Register fallback values for mocktail
      registerFallbackValue(JobPriority.normal);
    });
    
    setUp(() async {
      JobEventBus.resetForTesting();
      
      mockQueueAnalysis = MockQueueAnalysisUseCase();
      mockGetJobStatus = MockGetJobStatusUseCase();
      mockCancelJob = MockCancelJobUseCase();
      eventBus = JobEventBus();
      
      viewModel = JobQueueViewModel(
        queueAnalysis: mockQueueAnalysis,
        getJobStatus: mockGetJobStatus,
        cancelJob: mockCancelJob,
        eventBus: eventBus,
      );
    });
    
    tearDown(() {
      try {
        viewModel.dispose();
      } catch (e) {
        // Already disposed
      }
    });
    
    tearDownAll(() async {
      // Cleanup if needed
    });
    
    AnalysisJob createTestJob({
      String? id,
      String? ticker,
      JobStatus? status,
      JobPriority? priority,
      DateTime? createdAt,
    }) {
      return AnalysisJob(
        id: id ?? 'test-${DateTime.now().millisecondsSinceEpoch}',
        ticker: ticker ?? 'AAPL',
        tradeDate: '2024-01-20',
        status: status ?? JobStatus.pending,
        priority: priority ?? JobPriority.normal,
        createdAt: createdAt ?? DateTime.now(),
        retryCount: 0,
      );
    }
    
    group('initialization', () {
      test('should initialize with empty job lists', () {
        expect(viewModel.activeJobs, isEmpty);
        expect(viewModel.completedJobs, isEmpty);
        expect(viewModel.failedJobs, isEmpty);
        expect(viewModel.isLoading, isFalse);
        expect(viewModel.errorMessage, isNull);
      });
      
      test('should initialize counters correctly', () {
        expect(viewModel.totalJobs, equals(0));
        expect(viewModel.activeJobsCount, equals(0));
        expect(viewModel.completedJobsCount, equals(0));
        expect(viewModel.failedJobsCount, equals(0));
        expect(viewModel.hasActiveJobs, isFalse);
        expect(viewModel.hasCompletedJobs, isFalse);
        expect(viewModel.hasFailedJobs, isFalse);
      });
    });
    
    group('submitAnalysis', () {
      test('should submit analysis job successfully', () async {
        final job = createTestJob(id: 'submit-test');
        
        when(() => mockQueueAnalysis.execute(
          'AAPL', 
          '2024-01-20', 
          priority: JobPriority.normal
        )).thenAnswer((_) async => job);
        
        bool notified = false;
        viewModel.addListener(() => notified = true);
        
        await viewModel.submitAnalysis('AAPL', '2024-01-20');
        
        expect(notified, isTrue);
        expect(viewModel.activeJobs.length, equals(1));
        expect(viewModel.activeJobs.first.id, equals('submit-test'));
        expect(viewModel.isLoading, isFalse);
        expect(viewModel.errorMessage, isNull);
        
        verify(() => mockQueueAnalysis.execute(
          'AAPL', 
          '2024-01-20', 
          priority: JobPriority.normal
        )).called(1);
      });
      
      test('should submit analysis job with custom priority', () async {
        final job = createTestJob(id: 'priority-test', priority: JobPriority.high);
        
        when(() => mockQueueAnalysis.execute(
          'AAPL', 
          '2024-01-20', 
          priority: JobPriority.high
        )).thenAnswer((_) async => job);
        
        await viewModel.submitAnalysis('AAPL', '2024-01-20', priority: JobPriority.high);
        
        expect(viewModel.activeJobs.first.priority, equals(JobPriority.high));
        
        verify(() => mockQueueAnalysis.execute(
          'AAPL', 
          '2024-01-20', 
          priority: JobPriority.high
        )).called(1);
      });
      
      test('should handle submission error', () async {
        when(() => mockQueueAnalysis.execute(
          any(), 
          any(), 
          priority: any(named: 'priority')
        )).thenThrow(Exception('Submission failed'));
        
        bool notified = false;
        viewModel.addListener(() => notified = true);
        
        await viewModel.submitAnalysis('AAPL', '2024-01-20');
        
        expect(notified, isTrue);
        expect(viewModel.activeJobs, isEmpty);
        expect(viewModel.isLoading, isFalse);
        expect(viewModel.errorMessage, contains('Failed to submit analysis'));
      });
      
      test('should set loading state during submission', () async {
        final job = createTestJob();
        final completer = Completer<AnalysisJob>();
        
        when(() => mockQueueAnalysis.execute(
          any(), 
          any(), 
          priority: any(named: 'priority')
        )).thenAnswer((_) => completer.future);
        
        bool loadingStateChanged = false;
        viewModel.addListener(() {
          if (viewModel.isLoading) loadingStateChanged = true;
        });
        
        final submitFuture = viewModel.submitAnalysis('AAPL', '2024-01-20');
        
        // Should be loading now
        expect(viewModel.isLoading, isTrue);
        expect(loadingStateChanged, isTrue);
        
        // Complete the submission
        completer.complete(job);
        await submitFuture;
        
        expect(viewModel.isLoading, isFalse);
      });
    });
    
    group('cancelAnalysis', () {
      test('should cancel job successfully', () async {
        final job = createTestJob(id: 'cancel-test');
        
        // Add job to active list first
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        when(() => mockCancelJob.execute('cancel-test')).thenAnswer((_) async => true);
        
        final result = await viewModel.cancelAnalysis('cancel-test');
        
        expect(result, isTrue);
        expect(viewModel.activeJobs.any((j) => j.id == 'cancel-test'), isFalse);
        
        verify(() => mockCancelJob.execute('cancel-test')).called(1);
      });
      
      test('should handle cancellation failure', () async {
        when(() => mockCancelJob.execute('fail-test')).thenAnswer((_) async => false);
        
        final result = await viewModel.cancelAnalysis('fail-test');
        
        expect(result, isFalse);
        verify(() => mockCancelJob.execute('fail-test')).called(1);
      });
      
      test('should handle cancellation error', () async {
        when(() => mockCancelJob.execute('error-test')).thenThrow(Exception('Cancel failed'));
        
        bool notified = false;
        viewModel.addListener(() => notified = true);
        
        final result = await viewModel.cancelAnalysis('error-test');
        
        expect(result, isFalse);
        expect(notified, isTrue);
        expect(viewModel.errorMessage, contains('Failed to cancel job'));
      });
    });
    
    group('event handling', () {
      test('should handle JobQueuedEvent', () async {
        final job = createTestJob(id: 'queued-event', status: JobStatus.queued);
        
        bool notified = false;
        viewModel.addListener(() => notified = true);
        
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(notified, isTrue);
        expect(viewModel.activeJobs.length, equals(1));
        expect(viewModel.activeJobs.first.id, equals('queued-event'));
        expect(viewModel.activeJobsCount, equals(1));
      });
      
      test('should handle JobStartedEvent', () async {
        final queuedJob = createTestJob(id: 'started-event', status: JobStatus.queued);
        final runningJob = queuedJob.copyWith(
          status: JobStatus.running,
          startedAt: () => DateTime.now(),
        );
        
        // First queue the job
        eventBus.publish(JobQueuedEvent(queuedJob));
        await Future.delayed(const Duration(milliseconds: 10));
        
        bool notified = false;
        viewModel.addListener(() => notified = true);
        
        // Then start it
        eventBus.publish(JobStartedEvent(runningJob));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(notified, isTrue);
        expect(viewModel.activeJobs.length, equals(1));
        expect(viewModel.activeJobs.first.status, equals(JobStatus.running));
        expect(viewModel.activeJobs.first.startedAt, isNotNull);
      });
      
      test('should handle JobCompletedEvent', () async {
        final job = createTestJob(id: 'completed-event', status: JobStatus.queued);
        final completedJob = job.copyWith(
          status: JobStatus.completed,
          completedAt: () => DateTime.now(),
          resultId: () => 'result-123',
        );
        
        // First queue the job
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.activeJobs.length, equals(1));
        expect(viewModel.completedJobs.length, equals(0));
        
        // Then complete it
        eventBus.publish(JobCompletedEvent(completedJob, resultId: 'result-123'));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.activeJobs.length, equals(0));
        expect(viewModel.completedJobs.length, equals(1));
        expect(viewModel.completedJobs.first.status, equals(JobStatus.completed));
        expect(viewModel.completedJobsCount, equals(1));
      });
      
      test('should handle JobFailedEvent without retry', () async {
        final job = createTestJob(id: 'failed-event', status: JobStatus.running);
        final failedJob = job.copyWith(
          status: JobStatus.failed,
          completedAt: () => DateTime.now(),
          errorMessage: () => 'Test failure',
        );
        
        // First queue the job
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.activeJobs.length, equals(1));
        expect(viewModel.failedJobs.length, equals(0));
        
        // Then fail it (no retry)
        eventBus.publish(JobFailedEvent(failedJob, errorMessage: 'Test failure', willRetry: false));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.activeJobs.length, equals(0));
        expect(viewModel.failedJobs.length, equals(1));
        expect(viewModel.failedJobs.first.status, equals(JobStatus.failed));
        expect(viewModel.failedJobs.first.errorMessage, equals('Test failure'));
        expect(viewModel.failedJobsCount, equals(1));
      });
      
      test('should handle JobFailedEvent with retry', () async {
        final job = createTestJob(id: 'retry-event', status: JobStatus.running);
        final failedJob = job.copyWith(
          status: JobStatus.failed,
          completedAt: () => DateTime.now(),
          errorMessage: () => 'Test failure',
        );
        
        // First queue the job
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.activeJobs.length, equals(1));
        
        // Then fail it (with retry - should stay in active)
        eventBus.publish(JobFailedEvent(failedJob, errorMessage: 'Test failure', willRetry: true));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.activeJobs.length, equals(1));
        expect(viewModel.failedJobs.length, equals(0));
      });
      
      test('should handle JobCancelledEvent', () async {
        final job = createTestJob(id: 'cancelled-event', status: JobStatus.queued);
        final cancelledJob = job.copyWith(
          status: JobStatus.cancelled,
          completedAt: () => DateTime.now(),
        );
        
        // First queue the job
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.activeJobs.length, equals(1));
        
        // Then cancel it
        eventBus.publish(JobCancelledEvent(cancelledJob, reason: 'User cancelled'));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.activeJobs.length, equals(0));
        expect(viewModel.completedJobs.length, equals(0));
        expect(viewModel.failedJobs.length, equals(0));
      });
      
      test('should handle JobRequeuedEvent', () async {
        final failedJob = createTestJob(id: 'requeued-event', status: JobStatus.failed);
        final requeuedJob = failedJob.copyWith(
          status: JobStatus.queued,
          retryCount: 1,
          startedAt: () => null,
          completedAt: () => null,
          errorMessage: () => null,
        );
        
        // First add to failed jobs
        eventBus.publish(JobFailedEvent(failedJob, errorMessage: 'Test failure', willRetry: false));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.failedJobs.length, equals(1));
        expect(viewModel.activeJobs.length, equals(0));
        
        // Then requeue it
        eventBus.publish(JobRequeuedEvent(requeuedJob, retryAttempt: 1));
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(viewModel.failedJobs.length, equals(0));
        expect(viewModel.activeJobs.length, equals(1));
        expect(viewModel.activeJobs.first.retryCount, equals(1));
      });
    });
    
    group('job sorting', () {
      test('should sort active jobs by priority and creation time', () async {
        final now = DateTime.now();
        
        final normalJob = createTestJob(
          id: 'normal',
          priority: JobPriority.normal,
          createdAt: now.subtract(const Duration(minutes: 1)),
        );
        final highJob = createTestJob(
          id: 'high',
          priority: JobPriority.high,
          createdAt: now.subtract(const Duration(minutes: 2)),
        );
        final criticalJob = createTestJob(
          id: 'critical',
          priority: JobPriority.critical,
          createdAt: now.subtract(const Duration(minutes: 3)),
        );
        
        // Add jobs in random order
        eventBus.publish(JobQueuedEvent(normalJob));
        eventBus.publish(JobQueuedEvent(highJob));
        eventBus.publish(JobQueuedEvent(criticalJob));
        await Future.delayed(const Duration(milliseconds: 10));
        
        // Should be sorted by priority (critical > high > normal)
        expect(viewModel.activeJobs.length, equals(3));
        expect(viewModel.activeJobs[0].id, equals('critical'));
        expect(viewModel.activeJobs[1].id, equals('high'));
        expect(viewModel.activeJobs[2].id, equals('normal'));
      });
    });
    
    group('utility methods', () {
      test('getJobById should find job correctly', () async {
        final job = createTestJob(id: 'find-test');
        
        eventBus.publish(JobQueuedEvent(job));
        await Future.delayed(const Duration(milliseconds: 10));
        
        final foundJob = viewModel.getJobById('find-test');
        expect(foundJob, isNotNull);
        expect(foundJob!.id, equals('find-test'));
        
        final notFoundJob = viewModel.getJobById('not-found');
        expect(notFoundJob, isNull);
      });
      
      test('clearError should clear error message', () {
        when(() => mockQueueAnalysis.execute(
          any(), 
          any(), 
          priority: any(named: 'priority')
        )).thenThrow(Exception('Test error'));
        
        viewModel.submitAnalysis('AAPL', '2024-01-20');
        
        expect(viewModel.errorMessage, isNotNull);
        
        viewModel.clearError();
        
        expect(viewModel.errorMessage, isNull);
      });
      
      test('refreshJobs should trigger notification', () async {
        bool notified = false;
        viewModel.addListener(() => notified = true);
        
        await viewModel.refreshJobs();
        
        expect(notified, isTrue);
      });
    });
    
    group('change notification', () {
      test('should notify listeners on state changes', () async {
        int notificationCount = 0;
        viewModel.addListener(() => notificationCount++);
        
        final job = createTestJob();
        when(() => mockQueueAnalysis.execute(
          any(), 
          any(), 
          priority: any(named: 'priority')
        )).thenAnswer((_) async => job);
        
        await viewModel.submitAnalysis('AAPL', '2024-01-20');
        
        // Should notify: loading true, loading false, job added
        expect(notificationCount, greaterThan(0));
      });
    });
    
    group('disposal', () {
      test('should dispose cleanly', () {
        expect(() => viewModel.dispose(), returnsNormally);
      });
    });
  });
}