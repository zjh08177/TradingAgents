import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:trading_dummy/jobs/application/use_cases/cancel_job_use_case.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_processor.dart';
import '../../../mocks/mock_langgraph_service.dart';

void main() {
  group('CancelJobUseCase', () {
    late CancelJobUseCase useCase;
    late HiveJobRepository repository;
    late JobQueueManager queueManager;
    late JobProcessor jobProcessor;
    late MockLangGraphService analysisService;
    late Directory tempDir;
    
    setUpAll(() async {
      tempDir = await Directory.systemTemp.createTemp('cancel_use_case_test_');
      Hive.init(tempDir.path);
      
      if (!Hive.isAdapterRegistered(20)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      repository = HiveJobRepository();
      await repository.init();
      queueManager = JobQueueManager(repository: repository);
      analysisService = MockLangGraphService();
      jobProcessor = JobProcessor(
        repository: repository,
        analysisService: analysisService,
      );
      
      useCase = CancelJobUseCase(
        repository: repository,
        queueManager: queueManager,
        jobProcessor: jobProcessor,
      );
      
      // Clear any existing jobs
      final allJobs = await repository.getAll();
      for (final job in allJobs) {
        await repository.delete(job.id);
      }
    });
    
    tearDown(() async {
      jobProcessor.dispose();
      await repository.close();
    });
    
    tearDownAll(() async {
      await tempDir.delete(recursive: true);
    });
    
    final testJob = AnalysisJob(
      id: 'test-id',
      ticker: 'AAPL',
      tradeDate: '2024-01-20',
      status: JobStatus.pending,
      priority: JobPriority.normal,
      createdAt: DateTime.now(),
      retryCount: 0,
    );
    
    group('execute', () {
      test('should throw ArgumentError for empty job ID', () async {
        // Act & Assert
        expect(
          () => useCase.execute(''),
          throwsA(isA<ArgumentError>()
            .having((e) => e.message, 'message', 'Job ID cannot be empty')),
        );
      });
      
      test('should throw JobNotFoundException when job not found', () async {
        // Act & Assert
        await expectLater(
          useCase.execute('non-existent-id'),
          throwsA(isA<JobNotFoundException>()
            .having((e) => e.message, 'message', contains('not found'))),
        );
      });
      
      group('pending job cancellation', () {
        test('should cancel pending job successfully', () async {
          // Arrange
          await repository.save(testJob);
          await queueManager.enqueue(testJob);
          
          // Act
          final result = await useCase.execute('test-id');
          
          // Assert
          expect(result, isTrue);
          
          // Verify job status was updated
          final cancelledJob = await repository.getById('test-id');
          expect(cancelledJob!.status, equals(JobStatus.cancelled));
          expect(cancelledJob.completedAt, isNotNull);
        });
      });
      
      group('queued job cancellation', () {
        test('should cancel queued job successfully', () async {
          // Arrange
          await repository.save(testJob);
          await queueManager.enqueue(testJob);
          
          // Wait for job to be queued
          await Future.delayed(const Duration(milliseconds: 100));
          
          // Act
          final result = await useCase.execute('test-id');
          
          // Assert
          expect(result, isTrue);
          
          // Verify job status was updated
          final cancelledJob = await repository.getById('test-id');
          expect(cancelledJob!.status, equals(JobStatus.cancelled));
        });
      });
      
      group('running job cancellation', () {
        test('should cancel running job successfully', () async {
          // Arrange
          final runningJob = testJob.copyWith(
            status: JobStatus.running,
            startedAt: () => DateTime.now(),
          );
          await repository.save(runningJob);
          
          // Start processing the job
          jobProcessor.processJob(runningJob);
          
          // Give it a moment to start
          await Future.delayed(const Duration(milliseconds: 100));
          
          // Act
          final result = await useCase.execute('test-id');
          
          // Assert
          expect(result, isTrue);
          
          // Wait for cancellation to propagate
          await Future.delayed(const Duration(milliseconds: 200));
          
          // Verify job status was updated
          final cancelledJob = await repository.getById('test-id');
          expect(cancelledJob!.status, equals(JobStatus.cancelled));
        });
        
        test('should return false if no job processor available', () async {
          // Arrange
          final runningJob = testJob.copyWith(
            status: JobStatus.running,
            startedAt: () => DateTime.now(),
          );
          await repository.save(runningJob);
          
          final useCaseNoProcessor = CancelJobUseCase(
            repository: repository,
            queueManager: queueManager,
            jobProcessor: null,
          );
          
          // Act
          final result = await useCaseNoProcessor.execute('test-id');
          
          // Assert
          expect(result, isFalse);
        });
      });
      
      group('non-cancellable jobs', () {
        test('should return false for completed job', () async {
          // Arrange
          final completedJob = testJob.copyWith(
            status: JobStatus.completed,
            completedAt: () => DateTime.now(),
          );
          await repository.save(completedJob);
          
          // Act
          final result = await useCase.execute('test-id');
          
          // Assert
          expect(result, isFalse);
          
          // Verify status unchanged
          final job = await repository.getById('test-id');
          expect(job!.status, equals(JobStatus.completed));
        });
        
        test('should return false for failed job', () async {
          // Arrange
          final failedJob = testJob.copyWith(
            status: JobStatus.failed,
            completedAt: () => DateTime.now(),
          );
          await repository.save(failedJob);
          
          // Act
          final result = await useCase.execute('test-id');
          
          // Assert
          expect(result, isFalse);
        });
        
        test('should return false for already cancelled job', () async {
          // Arrange
          final cancelledJob = testJob.copyWith(
            status: JobStatus.cancelled,
            completedAt: () => DateTime.now(),
          );
          await repository.save(cancelledJob);
          
          // Act
          final result = await useCase.execute('test-id');
          
          // Assert
          expect(result, isFalse);
        });
      });
    });
    
    group('executeBatch', () {
      test('should handle empty list', () async {
        // Act
        final result = await useCase.executeBatch([]);
        
        // Assert
        expect(result.requested, equals(0));
        expect(result.succeeded, equals(0));
        expect(result.failed, equals(0));
        expect(result.notFound, equals(0));
        expect(result.notCancellable, equals(0));
      });
      
      test('should remove duplicates', () async {
        // Arrange
        await repository.save(testJob);
        await queueManager.enqueue(testJob);
        
        // Act
        final result = await useCase.executeBatch(['test-id', 'test-id', 'test-id']);
        
        // Assert
        expect(result.requested, equals(1));
        expect(result.succeeded, equals(1));
      });
      
      test('should handle mixed results', () async {
        // Arrange
        final pendingJob = testJob;
        final completedJob = testJob.copyWith(
          id: 'completed-id',
          status: JobStatus.completed,
        );
        
        // Pending job - will succeed
        await repository.save(pendingJob);
        await queueManager.enqueue(pendingJob);
        
        // Completed job - not cancellable
        await repository.save(completedJob);
        
        // Act
        final result = await useCase.executeBatch([
          'test-id',
          'completed-id',
          'not-found-id',
        ]);
        
        // Assert
        expect(result.requested, equals(3));
        expect(result.succeeded, equals(1));
        expect(result.failed, equals(0));
        expect(result.notFound, equals(1));
        expect(result.notCancellable, equals(1));
        expect(result.notCancelled, equals(2));
        expect(result.allSucceeded, isFalse);
        expect(result.anySucceeded, isTrue);
      });
    });
    
    group('CancelBatchResult', () {
      test('should have correct equality', () {
        // Arrange
        final result1 = const CancelBatchResult(
          requested: 5,
          succeeded: 2,
          failed: 1,
          notFound: 1,
          notCancellable: 1,
        );
        
        final result2 = const CancelBatchResult(
          requested: 5,
          succeeded: 2,
          failed: 1,
          notFound: 1,
          notCancellable: 1,
        );
        
        final result3 = const CancelBatchResult(
          requested: 5,
          succeeded: 3, // Different
          failed: 1,
          notFound: 1,
          notCancellable: 0,
        );
        
        // Assert
        expect(result1, equals(result2));
        expect(result1.hashCode, equals(result2.hashCode));
        expect(result1, isNot(equals(result3)));
      });
      
      test('should have meaningful toString', () {
        // Arrange
        final result = const CancelBatchResult(
          requested: 5,
          succeeded: 2,
          failed: 1,
          notFound: 1,
          notCancellable: 1,
        );
        
        // Act
        final str = result.toString();
        
        // Assert
        expect(str, contains('requested: 5'));
        expect(str, contains('succeeded: 2'));
        expect(str, contains('failed: 1'));
        expect(str, contains('notFound: 1'));
        expect(str, contains('notCancellable: 1'));
      });
    });
  });
}