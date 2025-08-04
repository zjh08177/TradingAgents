import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';

void main() {
  group('HiveJobRepository', () {
    late HiveJobRepository repository;
    late Directory tempDir;
    
    setUpAll(() async {
      // Initialize Hive with temporary directory
      tempDir = await Directory.systemTemp.createTemp('hive_job_test_');
      Hive.init(tempDir.path);
      
      // Register adapter
      if (!Hive.isAdapterRegistered(20)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      repository = HiveJobRepository();
      await repository.init();
    });
    
    tearDown(() async {
      await repository.close();
      await Hive.deleteBoxFromDisk('analysis_jobs');
    });
    
    tearDownAll(() async {
      await tempDir.delete(recursive: true);
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
    
    test('save and getById work correctly', () async {
      final job = createTestJob(id: 'test-123');
      
      await repository.save(job);
      final retrieved = await repository.getById('test-123');
      
      expect(retrieved, isNotNull);
      expect(retrieved!.id, equals(job.id));
      expect(retrieved.ticker, equals(job.ticker));
      expect(retrieved.status, equals(job.status));
      expect(retrieved.priority, equals(job.priority));
    });
    
    test('getById returns null for non-existent job', () async {
      final retrieved = await repository.getById('non-existent');
      expect(retrieved, isNull);
    });
    
    test('getAll returns all jobs sorted by creation date', () async {
      final now = DateTime.now();
      final job1 = createTestJob(
        id: 'job-1',
        createdAt: now.subtract(const Duration(hours: 2)),
      );
      final job2 = createTestJob(
        id: 'job-2',
        createdAt: now.subtract(const Duration(hours: 1)),
      );
      final job3 = createTestJob(
        id: 'job-3',
        createdAt: now,
      );
      
      await repository.save(job1);
      await repository.save(job2);
      await repository.save(job3);
      
      final jobs = await repository.getAll();
      
      expect(jobs.length, equals(3));
      expect(jobs[0].id, equals('job-3')); // Newest first
      expect(jobs[1].id, equals('job-2'));
      expect(jobs[2].id, equals('job-1'));
    });
    
    test('getByStatus returns only jobs with specified status', () async {
      final pendingJob = createTestJob(id: 'pending-1', status: JobStatus.pending);
      final runningJob = createTestJob(id: 'running-1', status: JobStatus.running);
      final completedJob = createTestJob(id: 'completed-1', status: JobStatus.completed);
      
      await repository.save(pendingJob);
      await repository.save(runningJob);
      await repository.save(completedJob);
      
      final pendingJobs = await repository.getByStatus(JobStatus.pending);
      expect(pendingJobs.length, equals(1));
      expect(pendingJobs.first.id, equals('pending-1'));
      
      final runningJobs = await repository.getByStatus(JobStatus.running);
      expect(runningJobs.length, equals(1));
      expect(runningJobs.first.id, equals('running-1'));
    });
    
    test('getActiveJobs returns all non-terminal jobs sorted correctly', () async {
      final now = DateTime.now();
      
      // Create jobs with different priorities and timestamps
      final criticalJob = createTestJob(
        id: 'critical-1',
        status: JobStatus.pending,
        priority: JobPriority.critical,
        createdAt: now,
      );
      final highJob = createTestJob(
        id: 'high-1',
        status: JobStatus.queued,
        priority: JobPriority.high,
        createdAt: now.subtract(const Duration(minutes: 5)),
      );
      final normalOld = createTestJob(
        id: 'normal-old',
        status: JobStatus.running,
        priority: JobPriority.normal,
        createdAt: now.subtract(const Duration(minutes: 10)),
      );
      final normalNew = createTestJob(
        id: 'normal-new',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: now.subtract(const Duration(minutes: 2)),
      );
      final completedJob = createTestJob(
        id: 'completed-1',
        status: JobStatus.completed,
        priority: JobPriority.critical,
      );
      
      await repository.save(criticalJob);
      await repository.save(highJob);
      await repository.save(normalOld);
      await repository.save(normalNew);
      await repository.save(completedJob);
      
      final activeJobs = await repository.getActiveJobs();
      
      expect(activeJobs.length, equals(4)); // All except completed
      
      // Check order: critical first, then high, then normal (oldest first)
      expect(activeJobs[0].id, equals('critical-1'));
      expect(activeJobs[1].id, equals('high-1'));
      expect(activeJobs[2].id, equals('normal-old')); // Older normal job first
      expect(activeJobs[3].id, equals('normal-new'));
    });
    
    test('getByTicker returns jobs for specific ticker', () async {
      final aaplJob1 = createTestJob(id: 'aapl-1', ticker: 'AAPL');
      final aaplJob2 = createTestJob(id: 'aapl-2', ticker: 'AAPL');
      final googlJob = createTestJob(id: 'googl-1', ticker: 'GOOGL');
      
      await repository.save(aaplJob1);
      await repository.save(aaplJob2);
      await repository.save(googlJob);
      
      final aaplJobs = await repository.getByTicker('AAPL');
      expect(aaplJobs.length, equals(2));
      expect(aaplJobs.every((job) => job.ticker == 'AAPL'), isTrue);
      
      final googlJobs = await repository.getByTicker('GOOGL');
      expect(googlJobs.length, equals(1));
      expect(googlJobs.first.ticker, equals('GOOGL'));
    });
    
    test('update modifies existing job', () async {
      final job = createTestJob(id: 'update-test');
      await repository.save(job);
      
      final updated = job.copyWith(
        status: JobStatus.running,
        startedAt: () => DateTime.now(),
      );
      await repository.update(updated);
      
      final retrieved = await repository.getById('update-test');
      expect(retrieved!.status, equals(JobStatus.running));
      expect(retrieved.startedAt, isNotNull);
    });
    
    test('delete removes job', () async {
      final job = createTestJob(id: 'delete-test');
      await repository.save(job);
      
      // Verify it exists
      var retrieved = await repository.getById('delete-test');
      expect(retrieved, isNotNull);
      
      // Delete it
      await repository.delete('delete-test');
      
      // Verify it's gone
      retrieved = await repository.getById('delete-test');
      expect(retrieved, isNull);
    });
    
    test('deleteCompletedBefore removes old completed jobs', () async {
      final now = DateTime.now();
      final cutoffDate = now.subtract(const Duration(days: 7));
      
      // Create jobs with different completion dates
      final oldCompleted = createTestJob(
        id: 'old-completed',
        status: JobStatus.completed,
      ).copyWith(
        completedAt: () => cutoffDate.subtract(const Duration(days: 1)),
      );
      
      final recentCompleted = createTestJob(
        id: 'recent-completed',
        status: JobStatus.completed,
      ).copyWith(
        completedAt: () => now.subtract(const Duration(days: 1)),
      );
      
      final pendingJob = createTestJob(
        id: 'pending-old',
        status: JobStatus.pending,
        createdAt: cutoffDate.subtract(const Duration(days: 10)),
      );
      
      await repository.save(oldCompleted);
      await repository.save(recentCompleted);
      await repository.save(pendingJob);
      
      final deletedCount = await repository.deleteCompletedBefore(cutoffDate);
      
      expect(deletedCount, equals(1));
      
      // Verify correct jobs remain
      expect(await repository.getById('old-completed'), isNull);
      expect(await repository.getById('recent-completed'), isNotNull);
      expect(await repository.getById('pending-old'), isNotNull);
    });
    
    test('getNextPendingJob returns highest priority oldest job', () async {
      final now = DateTime.now();
      
      // Create multiple pending jobs
      final normalOld = createTestJob(
        id: 'normal-old',
        priority: JobPriority.normal,
        createdAt: now.subtract(const Duration(minutes: 10)),
      );
      final normalNew = createTestJob(
        id: 'normal-new',
        priority: JobPriority.normal,
        createdAt: now,
      );
      final highJob = createTestJob(
        id: 'high-1',
        priority: JobPriority.high,
        createdAt: now.subtract(const Duration(minutes: 5)),
      );
      final runningJob = createTestJob(
        id: 'running-1',
        status: JobStatus.running,
        priority: JobPriority.critical,
      );
      
      await repository.save(normalOld);
      await repository.save(normalNew);
      await repository.save(highJob);
      await repository.save(runningJob);
      
      final nextJob = await repository.getNextPendingJob();
      
      expect(nextJob, isNotNull);
      expect(nextJob!.id, equals('high-1')); // High priority wins
    });
    
    test('getNextPendingJob returns null when no pending jobs', () async {
      final runningJob = createTestJob(status: JobStatus.running);
      final completedJob = createTestJob(status: JobStatus.completed);
      
      await repository.save(runningJob);
      await repository.save(completedJob);
      
      final nextJob = await repository.getNextPendingJob();
      expect(nextJob, isNull);
    });
    
    test('countByStatus returns correct counts', () async {
      // Create jobs with various statuses - need unique IDs
      await repository.save(createTestJob(id: 'pending-1', status: JobStatus.pending));
      await repository.save(createTestJob(id: 'pending-2', status: JobStatus.pending));
      await repository.save(createTestJob(id: 'queued-1', status: JobStatus.queued));
      await repository.save(createTestJob(id: 'running-1', status: JobStatus.running));
      await repository.save(createTestJob(id: 'completed-1', status: JobStatus.completed));
      await repository.save(createTestJob(id: 'completed-2', status: JobStatus.completed));
      await repository.save(createTestJob(id: 'completed-3', status: JobStatus.completed));
      
      final counts = await repository.countByStatus();
      
      expect(counts[JobStatus.pending], equals(2));
      expect(counts[JobStatus.queued], equals(1));
      expect(counts[JobStatus.running], equals(1));
      expect(counts[JobStatus.completed], equals(3));
      expect(counts[JobStatus.failed], equals(0));
      expect(counts[JobStatus.cancelled], equals(0));
    });
    
    test('existsSimilarActiveJob detects duplicate active jobs', () async {
      final activeJob = createTestJob(
        id: 'active-aapl',
        ticker: 'AAPL',
        status: JobStatus.pending,
      );
      final completedJob = createTestJob(
        id: 'completed-aapl',
        ticker: 'AAPL',
        status: JobStatus.completed,
      );
      final differentTickerJob = createTestJob(
        id: 'active-googl',
        ticker: 'GOOGL',
        status: JobStatus.pending,
      );
      
      await repository.save(activeJob);
      await repository.save(completedJob);
      await repository.save(differentTickerJob);
      
      // Should find active AAPL job with same trade date
      expect(
        await repository.existsSimilarActiveJob('AAPL', '2024-01-20'),
        isTrue,
      );
      
      // Should not find active GOOGL job with different trade date
      expect(
        await repository.existsSimilarActiveJob('GOOGL', '2024-01-21'),
        isFalse,
      );
      
      // Should find active GOOGL job with same trade date
      expect(
        await repository.existsSimilarActiveJob('GOOGL', '2024-01-20'),
        isTrue,
      );
      
      // Should not find active job for different date
      expect(
        await repository.existsSimilarActiveJob('AAPL', '2024-01-21'),
        isFalse,
      );
    });
  });
}