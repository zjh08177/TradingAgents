import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:trading_dummy/jobs/application/use_cases/get_job_status_use_case.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';

void main() {
  group('GetJobStatusUseCase', () {
    late GetJobStatusUseCase useCase;
    late HiveJobRepository repository;
    late Directory tempDir;
    
    setUpAll(() async {
      tempDir = await Directory.systemTemp.createTemp('status_use_case_test_');
      Hive.init(tempDir.path);
      
      if (!Hive.isAdapterRegistered(20)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      repository = HiveJobRepository();
      await repository.init();
      useCase = GetJobStatusUseCase(repository: repository);
      
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
    
    final testJob = AnalysisJob(
      id: 'test-id',
      ticker: 'AAPL',
      tradeDate: '2024-01-20',
      status: JobStatus.running,
      priority: JobPriority.normal,
      createdAt: DateTime(2024, 1, 20, 10, 0),
      retryCount: 0,
    );
    
    group('execute', () {
      test('should return job when found', () async {
        // Arrange
        await repository.save(testJob);
        
        // Act
        final result = await useCase.execute('test-id');
        
        // Assert
        expect(result, isNotNull);
        expect(result!.id, equals('test-id'));
        expect(result.ticker, equals('AAPL'));
        expect(result.status, equals(JobStatus.running));
      });
      
      test('should return null when job not found', () async {
        // Act
        final result = await useCase.execute('non-existent-id');
        
        // Assert
        expect(result, isNull);
      });
      
      test('should throw ArgumentError for empty job ID', () async {
        // Act & Assert
        expect(
          () => useCase.execute(''),
          throwsA(isA<ArgumentError>()
            .having((e) => e.message, 'message', 'Job ID cannot be empty')),
        );
      });
    });
    
    group('executeBatch', () {
      final testJobs = [
        testJob,
        testJob.copyWith(
          id: 'test-id-2',
          ticker: 'GOOGL',
          status: JobStatus.completed,
        ),
        testJob.copyWith(
          id: 'test-id-3',
          ticker: 'MSFT',
          status: JobStatus.pending,
        ),
      ];
      
      test('should return all found jobs', () async {
        // Arrange
        for (final job in testJobs) {
          await repository.save(job);
        }
        
        // Act
        final result = await useCase.executeBatch([
          'test-id',
          'test-id-2',
          'test-id-3',
        ]);
        
        // Assert
        expect(result.length, equals(3));
        expect(result.map((j) => j.id), containsAll(['test-id', 'test-id-2', 'test-id-3']));
      });
      
      test('should handle empty list', () async {
        // Act
        final result = await useCase.executeBatch([]);
        
        // Assert
        expect(result, isEmpty);
      });
      
      test('should filter out not found jobs', () async {
        // Arrange
        await repository.save(testJobs[0]);
        await repository.save(testJobs[2]);
        
        // Act
        final result = await useCase.executeBatch([
          'test-id',
          'test-id-2', // Not saved
          'test-id-3',
        ]);
        
        // Assert
        expect(result.length, equals(2));
        expect(result.map((j) => j.id), containsAll(['test-id', 'test-id-3']));
        expect(result.map((j) => j.id), isNot(contains('test-id-2')));
      });
      
      test('should remove duplicates and empty strings', () async {
        // Arrange
        await repository.save(testJobs[0]);
        
        // Act
        final result = await useCase.executeBatch([
          'test-id',
          'test-id',
          '',
          'test-id',
        ]);
        
        // Assert
        expect(result.length, equals(1));
        expect(result[0].id, equals('test-id'));
      });
    });
    
    group('getAll', () {
      final allJobs = [
        testJob.copyWith(
          id: 'job-1',
          status: JobStatus.pending,
          priority: JobPriority.high,
          createdAt: DateTime(2024, 1, 20, 10, 0),
        ),
        testJob.copyWith(
          id: 'job-2',
          status: JobStatus.running,
          priority: JobPriority.normal,
          ticker: 'GOOGL',
          createdAt: DateTime(2024, 1, 20, 11, 0),
        ),
        testJob.copyWith(
          id: 'job-3',
          status: JobStatus.completed,
          priority: JobPriority.low,
          createdAt: DateTime(2024, 1, 20, 12, 0),
        ),
        testJob.copyWith(
          id: 'job-4',
          status: JobStatus.failed,
          priority: JobPriority.high,
          ticker: 'MSFT',
          createdAt: DateTime(2024, 1, 20, 13, 0),
        ),
      ];
      
      setUp(() async {
        for (final job in allJobs) {
          await repository.save(job);
        }
      });
      
      test('should return all jobs when no filters', () async {
        // Act
        final result = await useCase.getAll();
        
        // Assert
        expect(result.length, equals(4));
        expect(result[0].id, equals('job-4')); // Newest first
        expect(result[3].id, equals('job-1')); // Oldest last
      });
      
      test('should filter by status', () async {
        // Act
        final result = await useCase.getAll(status: JobStatus.running);
        
        // Assert
        expect(result.length, equals(1));
        expect(result[0].id, equals('job-2'));
      });
      
      test('should filter by priority', () async {
        // Act
        final result = await useCase.getAll(priority: JobPriority.high);
        
        // Assert
        expect(result.length, equals(2));
        expect(result.map((j) => j.id), containsAll(['job-1', 'job-4']));
      });
      
      test('should filter by ticker (case-insensitive)', () async {
        // Act
        final result = await useCase.getAll(ticker: 'googl');
        
        // Assert
        expect(result.length, equals(1));
        expect(result[0].ticker, equals('GOOGL'));
      });
      
      test('should filter by date range', () async {
        // Act
        final result = await useCase.getAll(
          startDate: DateTime(2024, 1, 20, 11, 0),
          endDate: DateTime(2024, 1, 20, 12, 0),
        );
        
        // Assert
        expect(result.length, equals(2));
        expect(result.map((j) => j.id), containsAll(['job-2', 'job-3']));
      });
      
      test('should apply limit', () async {
        // Act
        final result = await useCase.getAll(limit: 2);
        
        // Assert
        expect(result.length, equals(2));
        expect(result[0].id, equals('job-4')); // Newest
        expect(result[1].id, equals('job-3'));
      });
      
      test('should apply multiple filters', () async {
        // Act
        final result = await useCase.getAll(
          status: JobStatus.failed,
          priority: JobPriority.high,
          ticker: 'MSFT',
        );
        
        // Assert
        expect(result.length, equals(1));
        expect(result[0].id, equals('job-4'));
      });
      
      test('should handle empty results', () async {
        // Act
        final result = await useCase.getAll(status: JobStatus.cancelled);
        
        // Assert
        expect(result, isEmpty);
      });
    });
    
    group('getStatistics', () {
      test('should calculate statistics correctly', () async {
        // Arrange
        final jobs = [
          testJob.copyWith(id: '1', status: JobStatus.pending),
          testJob.copyWith(id: '2', status: JobStatus.pending),
          testJob.copyWith(id: '3', status: JobStatus.queued),
          testJob.copyWith(id: '4', status: JobStatus.running),
          testJob.copyWith(id: '5', status: JobStatus.completed),
          testJob.copyWith(id: '6', status: JobStatus.completed),
          testJob.copyWith(id: '7', status: JobStatus.completed),
          testJob.copyWith(id: '8', status: JobStatus.failed),
          testJob.copyWith(id: '9', status: JobStatus.cancelled),
        ];
        
        for (final job in jobs) {
          await repository.save(job);
        }
        
        // Act
        final stats = await useCase.getStatistics();
        
        // Assert
        expect(stats.total, equals(9));
        expect(stats.pending, equals(2));
        expect(stats.queued, equals(1));
        expect(stats.running, equals(1));
        expect(stats.completed, equals(3));
        expect(stats.failed, equals(1));
        expect(stats.cancelled, equals(1));
        expect(stats.active, equals(4)); // pending + queued + running
        expect(stats.terminal, equals(5)); // completed + failed + cancelled
        expect(stats.successRate, equals(0.75)); // 3 completed / (3 + 1 failed)
      });
      
      test('should handle empty job list', () async {
        // Act
        final stats = await useCase.getStatistics();
        
        // Assert
        expect(stats.total, equals(0));
        expect(stats.pending, equals(0));
        expect(stats.queued, equals(0));
        expect(stats.running, equals(0));
        expect(stats.completed, equals(0));
        expect(stats.failed, equals(0));
        expect(stats.cancelled, equals(0));
        expect(stats.active, equals(0));
        expect(stats.terminal, equals(0));
        expect(stats.successRate, equals(0.0));
      });
      
      test('should calculate 0% success rate when no completed/failed', () async {
        // Arrange
        final jobs = [
          testJob.copyWith(id: '1', status: JobStatus.pending),
          testJob.copyWith(id: '2', status: JobStatus.running),
        ];
        
        for (final job in jobs) {
          await repository.save(job);
        }
        
        // Act
        final stats = await useCase.getStatistics();
        
        // Assert
        expect(stats.successRate, equals(0.0));
      });
    });
    
    group('JobStatistics', () {
      test('should have correct equality', () {
        // Arrange
        final stats1 = const JobStatistics(
          total: 10,
          pending: 2,
          queued: 1,
          running: 1,
          completed: 4,
          failed: 1,
          cancelled: 1,
        );
        
        final stats2 = const JobStatistics(
          total: 10,
          pending: 2,
          queued: 1,
          running: 1,
          completed: 4,
          failed: 1,
          cancelled: 1,
        );
        
        final stats3 = const JobStatistics(
          total: 10,
          pending: 3, // Different
          queued: 1,
          running: 1,
          completed: 4,
          failed: 1,
          cancelled: 0,
        );
        
        // Assert
        expect(stats1, equals(stats2));
        expect(stats1.hashCode, equals(stats2.hashCode));
        expect(stats1, isNot(equals(stats3)));
      });
      
      test('should have meaningful toString', () {
        // Arrange
        final stats = const JobStatistics(
          total: 10,
          pending: 2,
          queued: 1,
          running: 1,
          completed: 4,
          failed: 1,
          cancelled: 1,
        );
        
        // Act
        final str = stats.toString();
        
        // Assert
        expect(str, contains('total: 10'));
        expect(str, contains('active: 4'));
        expect(str, contains('completed: 4'));
        expect(str, contains('failed: 1'));
      });
    });
  });
}