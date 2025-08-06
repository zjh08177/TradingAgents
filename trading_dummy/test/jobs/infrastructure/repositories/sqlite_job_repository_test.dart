import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/sqlite_job_repository.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_database.dart';
import 'dart:io';
import 'package:path/path.dart' as path;

void main() {
  late SQLiteJobRepository repository;
  late AnalysisDatabase database;
  late String testDbPath;

  setUpAll(() {
    // Initialize sqflite_ffi for testing
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  setUp(() async {
    // Create a temporary test database
    final tempDir = await Directory.systemTemp.createTemp('sqlite_job_test_');
    testDbPath = path.join(tempDir.path, 'test.db');
    
    // Initialize database with test path
    database = AnalysisDatabase();
    database.setTestPath(testDbPath);
    
    // Create repository
    repository = SQLiteJobRepository();
    await repository.init();
  });

  tearDown(() async {
    // Close database and clean up
    await database.close();
    
    // Delete test database file
    if (await File(testDbPath).exists()) {
      await File(testDbPath).delete();
    }
  });

  group('SQLiteJobRepository', () {
    test('should save and retrieve a job', () async {
      // Arrange
      final job = _createTestJob('AAPL', JobStatus.pending);
      
      // Act
      await repository.save(job);
      final retrieved = await repository.getById(job.id);
      
      // Assert
      expect(retrieved, isNotNull);
      expect(retrieved!.id, equals(job.id));
      expect(retrieved.ticker, equals(job.ticker));
      expect(retrieved.tradeDate, equals(job.tradeDate));
      expect(retrieved.status, equals(job.status));
      expect(retrieved.priority, equals(job.priority));
    });

    test('should retrieve all jobs', () async {
      // Arrange
      final job1 = _createTestJob('AAPL', JobStatus.pending, id: 'job1');
      final job2 = _createTestJob('GOOGL', JobStatus.running, id: 'job2');
      final job3 = _createTestJob('MSFT', JobStatus.completed, id: 'job3');
      
      // Act
      await repository.save(job1);
      await repository.save(job2);
      await repository.save(job3);
      final allJobs = await repository.getAll();
      
      // Assert
      expect(allJobs.length, equals(3));
      expect(allJobs.map((j) => j.id).toSet(), equals({'job1', 'job2', 'job3'}));
    });

    test('should retrieve jobs by status', () async {
      // Arrange
      final pendingJob1 = _createTestJob('AAPL', JobStatus.pending, id: 'p1');
      final pendingJob2 = _createTestJob('GOOGL', JobStatus.pending, id: 'p2');
      final runningJob = _createTestJob('MSFT', JobStatus.running, id: 'r1');
      final completedJob = _createTestJob('TSLA', JobStatus.completed, id: 'c1');
      
      // Act
      await repository.save(pendingJob1);
      await repository.save(pendingJob2);
      await repository.save(runningJob);
      await repository.save(completedJob);
      
      final pendingJobs = await repository.getByStatus(JobStatus.pending);
      final runningJobs = await repository.getByStatus(JobStatus.running);
      
      // Assert
      expect(pendingJobs.length, equals(2));
      expect(pendingJobs.every((j) => j.status == JobStatus.pending), isTrue);
      expect(runningJobs.length, equals(1));
      expect(runningJobs.first.status, equals(JobStatus.running));
    });

    test('should retrieve active jobs', () async {
      // Arrange
      final pendingJob = _createTestJob('AAPL', JobStatus.pending, id: 'p1');
      final runningJob = _createTestJob('GOOGL', JobStatus.running, id: 'r1');
      final completedJob = _createTestJob('MSFT', JobStatus.completed, id: 'c1');
      final failedJob = _createTestJob('TSLA', JobStatus.failed, id: 'f1');
      
      // Act
      await repository.save(pendingJob);
      await repository.save(runningJob);
      await repository.save(completedJob);
      await repository.save(failedJob);
      
      final activeJobs = await repository.getActiveJobs();
      
      // Assert
      expect(activeJobs.length, equals(2));
      expect(activeJobs.map((j) => j.id).toSet(), equals({'p1', 'r1'}));
    });

    test('should retrieve jobs by ticker', () async {
      // Arrange
      final appleJob1 = _createTestJob('AAPL', JobStatus.pending, id: 'a1');
      final appleJob2 = _createTestJob('AAPL', JobStatus.completed, id: 'a2');
      final googleJob = _createTestJob('GOOGL', JobStatus.pending, id: 'g1');
      
      // Act
      await repository.save(appleJob1);
      await repository.save(appleJob2);
      await repository.save(googleJob);
      
      final appleJobs = await repository.getByTicker('AAPL');
      
      // Assert
      expect(appleJobs.length, equals(2));
      expect(appleJobs.every((j) => j.ticker == 'AAPL'), isTrue);
    });

    test('should update an existing job', () async {
      // Arrange
      final job = _createTestJob('AAPL', JobStatus.pending);
      await repository.save(job);
      
      // Update job status and other fields
      final updatedJob = AnalysisJob(
        id: job.id,
        ticker: job.ticker,
        tradeDate: job.tradeDate,
        status: JobStatus.running,
        priority: JobPriority.high,
        createdAt: job.createdAt,
        startedAt: DateTime.now(),
        retryCount: job.retryCount,
        maxRetries: job.maxRetries,
      );
      
      // Act
      await repository.update(updatedJob);
      final retrieved = await repository.getById(job.id);
      
      // Assert
      expect(retrieved!.status, equals(JobStatus.running));
      expect(retrieved.priority, equals(JobPriority.high));
      expect(retrieved.startedAt, isNotNull);
    });

    test('should delete a job', () async {
      // Arrange
      final job = _createTestJob('AAPL', JobStatus.pending);
      await repository.save(job);
      
      // Act
      await repository.delete(job.id);
      final retrieved = await repository.getById(job.id);
      
      // Assert
      expect(retrieved, isNull);
    });

    test('should delete completed jobs before date', () async {
      // Arrange
      final now = DateTime.now();
      final oldCompleted = _createTestJob('AAPL', JobStatus.completed, id: 'old1',
        completedAt: now.subtract(const Duration(days: 10)));
      final recentCompleted = _createTestJob('GOOGL', JobStatus.completed, id: 'recent1',
        completedAt: now.subtract(const Duration(days: 2)));
      final oldFailed = _createTestJob('MSFT', JobStatus.failed, id: 'old2',
        completedAt: now.subtract(const Duration(days: 10)));
      final pendingJob = _createTestJob('TSLA', JobStatus.pending, id: 'pending1');
      
      await repository.save(oldCompleted);
      await repository.save(recentCompleted);
      await repository.save(oldFailed);
      await repository.save(pendingJob);
      
      // Act
      final deletedCount = await repository.deleteCompletedBefore(
        now.subtract(const Duration(days: 5))
      );
      
      final remainingJobs = await repository.getAll();
      
      // Assert
      expect(deletedCount, equals(2)); // old completed and old failed
      expect(remainingJobs.length, equals(2));
      expect(remainingJobs.map((j) => j.id).toSet(), equals({'recent1', 'pending1'}));
    });

    test('should get next pending job with priority ordering', () async {
      // Arrange
      final lowPriorityOld = _createTestJob('AAPL', JobStatus.pending, 
        id: 'low-old',
        priority: JobPriority.low,
        createdAt: DateTime.now().subtract(const Duration(hours: 2)));
      
      final highPriorityNew = _createTestJob('GOOGL', JobStatus.pending,
        id: 'high-new', 
        priority: JobPriority.high,
        createdAt: DateTime.now());
      
      final normalPriorityMid = _createTestJob('MSFT', JobStatus.pending,
        id: 'normal-mid',
        priority: JobPriority.normal,
        createdAt: DateTime.now().subtract(const Duration(hours: 1)));
      
      // Act
      await repository.save(lowPriorityOld);
      await repository.save(highPriorityNew);
      await repository.save(normalPriorityMid);
      
      final nextJob = await repository.getNextPendingJob();
      
      // Assert
      expect(nextJob, isNotNull);
      expect(nextJob!.id, equals('high-new')); // High priority wins
    });

    test('should count jobs by status', () async {
      // Arrange
      await repository.save(_createTestJob('AAPL', JobStatus.pending, id: 'p1'));
      await repository.save(_createTestJob('GOOGL', JobStatus.pending, id: 'p2'));
      await repository.save(_createTestJob('MSFT', JobStatus.running, id: 'r1'));
      await repository.save(_createTestJob('TSLA', JobStatus.completed, id: 'c1'));
      await repository.save(_createTestJob('META', JobStatus.failed, id: 'f1'));
      
      // Act
      final counts = await repository.countByStatus();
      
      // Assert
      expect(counts[JobStatus.pending], equals(2));
      expect(counts[JobStatus.running], equals(1));
      expect(counts[JobStatus.completed], equals(1));
      expect(counts[JobStatus.failed], equals(1));
      expect(counts[JobStatus.cancelled] ?? 0, equals(0));
    });

    test('should check for similar active job', () async {
      // Arrange
      final activeJob = _createTestJob('AAPL', JobStatus.pending, 
        id: 'active-job', tradeDate: '2024-01-15');
      final completedJob = _createTestJob('AAPL', JobStatus.completed, 
        id: 'completed-job', tradeDate: '2024-01-14');
      
      await repository.save(activeJob);
      await repository.save(completedJob);
      
      // Act
      final existsSimilar1 = await repository.existsSimilarActiveJob('AAPL', '2024-01-15');
      final existsSimilar2 = await repository.existsSimilarActiveJob('AAPL', '2024-01-14');
      final existsSimilar3 = await repository.existsSimilarActiveJob('GOOGL', '2024-01-15');
      
      // Assert
      expect(existsSimilar1, isTrue); // Active job exists
      expect(existsSimilar2, isFalse); // Job is completed, not active
      expect(existsSimilar3, isFalse); // Different ticker
    });

    test('should handle job with error message', () async {
      // Arrange
      final failedJob = AnalysisJob(
        id: 'failed-job',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        status: JobStatus.failed,
        priority: JobPriority.normal,
        createdAt: DateTime.now(),
        errorMessage: 'Network timeout',
        retryCount: 2,
        maxRetries: 3,
      );
      
      // Act
      await repository.save(failedJob);
      final retrieved = await repository.getById(failedJob.id);
      
      // Assert
      expect(retrieved!.status, equals(JobStatus.failed));
      expect(retrieved.errorMessage, equals('Network timeout'));
      expect(retrieved.retryCount, equals(2));
    });

    test('should return null for non-existent job', () async {
      // Act
      final result = await repository.getById('non-existent-id');
      
      // Assert
      expect(result, isNull);
    });

    test('should return null when no pending jobs', () async {
      // Arrange
      await repository.save(_createTestJob('AAPL', JobStatus.completed));
      
      // Act
      final nextJob = await repository.getNextPendingJob();
      
      // Assert
      expect(nextJob, isNull);
    });
  });
}

// Helper function to create test jobs
AnalysisJob _createTestJob(
  String ticker,
  JobStatus status, {
  String? id,
  String? tradeDate,
  JobPriority? priority,
  DateTime? createdAt,
  DateTime? completedAt,
}) {
  return AnalysisJob(
    id: id ?? 'test-${DateTime.now().millisecondsSinceEpoch}',
    ticker: ticker,
    tradeDate: tradeDate ?? '2024-01-15',
    status: status,
    priority: priority ?? JobPriority.normal,
    createdAt: createdAt ?? DateTime.now(),
    completedAt: completedAt,
    retryCount: 0,
    maxRetries: 3,
  );
}