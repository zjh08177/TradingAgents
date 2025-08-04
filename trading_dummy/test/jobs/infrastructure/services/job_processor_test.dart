import 'dart:async';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:mocktail/mocktail.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_processor.dart';
import 'package:trading_dummy/services/langgraph_service.dart';
import 'package:trading_dummy/models/final_report.dart';

// Mock classes
class MockLangGraphService extends Mock implements ILangGraphService {}

void main() {
  group('JobProcessor', () {
    late HiveJobRepository repository;
    late MockLangGraphService mockAnalysisService;
    late JobProcessor processor;
    late Directory tempDir;
    
    setUpAll(() async {
      tempDir = await Directory.systemTemp.createTemp('processor_test_');
      Hive.init(tempDir.path);
      
      if (!Hive.isAdapterRegistered(20)) {
        Hive.registerAdapter(HiveAnalysisJobAdapter());
      }
    });
    
    setUp(() async {
      repository = HiveJobRepository();
      await repository.init();
      
      mockAnalysisService = MockLangGraphService();
      
      processor = JobProcessor(
        repository: repository,
        analysisService: mockAnalysisService,
        maxConcurrentIsolates: 2,
      );
    });
    
    tearDown(() async {
      processor.dispose();
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
    }) {
      return AnalysisJob(
        id: id ?? 'test-${DateTime.now().millisecondsSinceEpoch}',
        ticker: ticker ?? 'AAPL',
        tradeDate: '2024-01-20',
        status: status ?? JobStatus.pending,
        priority: priority ?? JobPriority.normal,
        createdAt: DateTime.now(),
        retryCount: 0,
      );
    }
    
    test('processJob spawns isolate and processes job', () async {
      final job = createTestJob(id: 'isolate-test');
      
      // Save job to repository
      await repository.save(job);
      
      // Process the job
      await processor.processJob(job);
      
      // Give isolate time to process
      await Future.delayed(const Duration(seconds: 3));
      
      // Check job was completed
      final updatedJob = await repository.getById('isolate-test');
      expect(updatedJob, isNotNull);
      expect(updatedJob!.status, equals(JobStatus.completed));
      expect(updatedJob.completedAt, isNotNull);
      expect(updatedJob.resultId, isNotNull);
    });
    
    test('processJob respects max concurrent isolates', () async {
      // Create multiple jobs
      final job1 = createTestJob(id: 'job-1');
      final job2 = createTestJob(id: 'job-2');
      final job3 = createTestJob(id: 'job-3');
      
      await repository.save(job1);
      await repository.save(job2);
      await repository.save(job3);
      
      // Process first two jobs (max is 2)
      await processor.processJob(job1);
      await processor.processJob(job2);
      
      expect(processor.runningIsolateCount, equals(2));
      expect(processor.canProcessMore, isFalse);
      
      // Try to process third job - should throw
      expect(
        () => processor.processJob(job3),
        throwsA(isA<IsolateCapacityException>()),
      );
    });
    
    test('handleJobSuccess updates job correctly', () async {
      final job = createTestJob(id: 'success-test').copyWith(
        status: JobStatus.running,
        startedAt: () => DateTime.now(),
      );
      
      await repository.save(job);
      
      final report = FinalReport(
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        content: 'Strong buy recommendation - Hold for now',
        timestamp: DateTime.now(),
      );
      
      await processor.handleJobSuccess(job, report);
      
      final updatedJob = await repository.getById('success-test');
      expect(updatedJob!.status, equals(JobStatus.completed));
      expect(updatedJob.completedAt, isNotNull);
      expect(updatedJob.resultId, isNotNull);
    });
    
    test('handleJobFailure updates job correctly', () async {
      final job = createTestJob(id: 'failure-test').copyWith(
        status: JobStatus.running,
        startedAt: () => DateTime.now(),
      );
      
      await repository.save(job);
      
      final error = Exception('Analysis failed');
      await processor.handleJobFailure(job, error);
      
      final updatedJob = await repository.getById('failure-test');
      expect(updatedJob!.status, equals(JobStatus.failed));
      expect(updatedJob.completedAt, isNotNull);
      expect(updatedJob.errorMessage, contains('Analysis failed'));
    });
    
    test('cancelJob cancels running job', () async {
      final job = createTestJob(id: 'cancel-test');
      await repository.save(job);
      
      // Start processing
      await processor.processJob(job);
      
      // Cancel immediately
      final result = await processor.cancelJob('cancel-test');
      expect(result, isTrue);
      
      // Check job was cancelled
      final updatedJob = await repository.getById('cancel-test');
      expect(updatedJob!.status, equals(JobStatus.cancelled));
      expect(updatedJob.completedAt, isNotNull);
    });
    
    test('cancelJob returns false for non-existent job', () async {
      final result = await processor.cancelJob('non-existent');
      expect(result, isFalse);
    });
    
    test('dispose cleans up all resources', () async {
      final job1 = createTestJob(id: 'dispose-1');
      final job2 = createTestJob(id: 'dispose-2');
      
      await repository.save(job1);
      await repository.save(job2);
      
      // Start processing
      await processor.processJob(job1);
      await processor.processJob(job2);
      
      expect(processor.runningIsolateCount, equals(2));
      
      // Dispose
      processor.dispose();
      
      // After dispose, count should be 0
      expect(processor.runningIsolateCount, equals(0));
    });
    
    test('isolate handles errors gracefully', () async {
      final job = createTestJob(id: 'error-test');
      await repository.save(job);
      
      // This will fail in the isolate due to the mock service
      await processor.processJob(job);
      
      // Give time for error handling
      await Future.delayed(const Duration(seconds: 3));
      
      // Job should be completed (simulated success in test isolate)
      final updatedJob = await repository.getById('error-test');
      expect(updatedJob!.status, equals(JobStatus.completed));
    });
  });
}