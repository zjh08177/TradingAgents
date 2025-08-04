import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:trading_dummy/jobs/application/use_cases/queue_analysis_use_case.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';

void main() {
  group('QueueAnalysisUseCase', () {
    late QueueAnalysisUseCase useCase;
    late HiveJobRepository repository;
    late JobQueueManager queueManager;
    late Directory tempDir;
    
    setUpAll(() async {
      tempDir = await Directory.systemTemp.createTemp('queue_use_case_test_');
      Hive.init(tempDir.path);
      
      if (!Hive.isAdapterRegistered(20)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      repository = HiveJobRepository();
      await repository.init();
      queueManager = JobQueueManager(repository: repository);
      
      useCase = QueueAnalysisUseCase(
        repository: repository,
        queueManager: queueManager,
      );
      
      // Clear any existing jobs
      final allJobs = await repository.getAll();
      for (final job in allJobs) {
        await repository.delete(job.id);
      }
    });
    
    tearDown(() async {
      await repository.close();
    });
    
    tearDownAll(() async {
      await tempDir.delete(recursive: true);
    });
    
    group('execute', () {
      const testTicker = 'AAPL';
      const testTradeDate = '2024-01-20';
      
      test('should create and queue a job successfully', () async {
        // Act
        final result = await useCase.execute(testTicker, testTradeDate);
        
        // Assert
        expect(result.ticker, equals(testTicker));
        expect(result.tradeDate, equals(testTradeDate));
        expect(result.status, equals(JobStatus.pending));
        expect(result.priority, equals(JobPriority.normal));
        expect(result.retryCount, equals(0));
        
        // Verify job was saved
        final savedJob = await repository.getById(result.id);
        expect(savedJob, isNotNull);
        expect(savedJob!.id, equals(result.id));
        
        // Verify job was queued
        final queuedJobs = await repository.getByStatus(JobStatus.queued);
        expect(queuedJobs.length, equals(1));
        expect(queuedJobs.first.id, equals(result.id));
      });
      
      test('should create job with custom priority', () async {
        // Act
        final result = await useCase.execute(
          testTicker,
          testTradeDate,
          priority: JobPriority.high,
        );
        
        // Assert
        expect(result.priority, equals(JobPriority.high));
      });
      
      test('should convert ticker to uppercase', () async {
        // Act
        final result = await useCase.execute('aapl', testTradeDate);
        
        // Assert
        expect(result.ticker, equals('AAPL'));
      });
      
      group('input validation', () {
        test('should throw ArgumentError for empty ticker', () async {
          // Act & Assert
          expect(
            () => useCase.execute('', testTradeDate),
            throwsA(isA<ArgumentError>()
              .having((e) => e.message, 'message', 'Ticker cannot be empty')),
          );
        });
        
        test('should throw ArgumentError for long ticker', () async {
          // Act & Assert
          expect(
            () => useCase.execute('VERYLONGTICKER', testTradeDate),
            throwsA(isA<ArgumentError>()
              .having((e) => e.message, 'message', 'Ticker cannot be longer than 10 characters')),
          );
        });
        
        test('should throw ArgumentError for non-alphanumeric ticker', () async {
          // Act & Assert
          expect(
            () => useCase.execute('AAPL.X', testTradeDate),
            throwsA(isA<ArgumentError>()
              .having((e) => e.message, 'message', 'Ticker must be alphanumeric')),
          );
        });
        
        test('should throw ArgumentError for invalid date format', () async {
          // Act & Assert
          expect(
            () => useCase.execute(testTicker, '2024/01/20'),
            throwsA(isA<ArgumentError>()
              .having((e) => e.message, 'message', 'Trade date must be in YYYY-MM-DD format')),
          );
        });
        
        test('should throw ArgumentError for future date', () async {
          // Arrange
          final futureDate = DateTime.now().add(const Duration(days: 1));
          final futureDateStr = '${futureDate.year}-${futureDate.month.toString().padLeft(2, '0')}-${futureDate.day.toString().padLeft(2, '0')}';
          
          // Act & Assert
          expect(
            () => useCase.execute(testTicker, futureDateStr),
            throwsA(isA<ArgumentError>()
              .having((e) => e.message, 'message', 'Trade date cannot be in the future')),
          );
        });
        
        test('should throw ArgumentError for date before 2000', () async {
          // Act & Assert
          expect(
            () => useCase.execute(testTicker, '1999-12-31'),
            throwsA(isA<ArgumentError>()
              .having((e) => e.message, 'message', 'Trade date cannot be before year 2000')),
          );
        });
        
        test('should throw ArgumentError for invalid date values', () async {
          // Act & Assert
          expect(
            () => useCase.execute(testTicker, '2024-13-01'),
            throwsA(isA<ArgumentError>()
              .having((e) => e.message, 'message', contains('Invalid trade date'))),
          );
        });
      });
      
      group('duplicate detection', () {
        test('should throw DuplicateJobException for queued duplicate', () async {
          // Arrange - create a job (immediately becomes queued)
          await useCase.execute(testTicker, testTradeDate);
          
          // Act & Assert
          expect(
            () => useCase.execute(testTicker, testTradeDate),
            throwsA(isA<DuplicateJobException>()
              .having((e) => e.message, 'message', contains('already Queued'))),
          );
        });
        
        
        test('should throw DuplicateJobException for running duplicate', () async {
          // Arrange - Create a job directly in the repository with running status
          final runningJob = AnalysisJob(
            id: 'running-job',
            ticker: testTicker,
            tradeDate: testTradeDate,
            status: JobStatus.running,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            startedAt: DateTime.now(),
            retryCount: 0,
          );
          await repository.save(runningJob);
          
          // Act & Assert
          expect(
            () => useCase.execute(testTicker, testTradeDate),
            throwsA(isA<DuplicateJobException>()
              .having((e) => e.message, 'message', contains('already Running'))),
          );
        });
        
        test('should allow duplicate if existing job is completed', () async {
          // Arrange - Create a completed job directly in the repository
          final completedJob = AnalysisJob(
            id: 'completed-job',
            ticker: testTicker,
            tradeDate: testTradeDate,
            status: JobStatus.completed,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            completedAt: DateTime.now(),
            retryCount: 0,
          );
          await repository.save(completedJob);
          
          // Act - should allow creating new job
          final newJob = await useCase.execute(testTicker, testTradeDate);
          
          // Assert
          expect(newJob.id, isNot(equals(completedJob.id)));
          expect(newJob.status, equals(JobStatus.pending)); // Job is created as pending
          
          // Verify it was queued in repository
          final queuedJob = await repository.getById(newJob.id);
          expect(queuedJob!.status, equals(JobStatus.queued)); // But immediately queued
        });
        
        test('should be case-insensitive for ticker comparison', () async {
          // Arrange - create a job with lowercase ticker
          final job = AnalysisJob(
            id: 'test-id',
            ticker: 'aapl',
            tradeDate: testTradeDate,
            status: JobStatus.queued, // Should be queued, not pending
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            retryCount: 0,
          );
          await repository.save(job);
          
          // Act & Assert
          expect(
            () => useCase.execute('AAPL', testTradeDate),
            throwsA(isA<DuplicateJobException>()),
          );
        });
      });
      
      group('error handling', () {
        test('should handle queue manager initialization', () async {
          // This test verifies the queue manager is properly initialized
          // and can handle jobs
          
          // Act
          final job1 = await useCase.execute('AAPL', '2024-01-20');
          final job2 = await useCase.execute('GOOGL', '2024-01-20');
          final job3 = await useCase.execute('MSFT', '2024-01-20');
          
          // Assert - all jobs should be queued
          final queuedJobs = await repository.getByStatus(JobStatus.queued);
          expect(queuedJobs.length, equals(3));
        });
      });
    });
  });
}