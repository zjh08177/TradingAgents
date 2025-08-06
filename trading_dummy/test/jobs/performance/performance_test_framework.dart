import 'dart:async';
import 'dart:io';
import 'dart:math';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job_adapter.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';
import 'package:trading_dummy/jobs/infrastructure/services/retry_scheduler.dart';
import 'package:trading_dummy/jobs/domain/services/job_retry_policy.dart';

/// Performance testing framework for the async job system
/// 
/// This framework provides comprehensive performance benchmarks
/// and load testing capabilities for all job system components.
class PerformanceTestFramework {
  late Directory _tempDir;
  late HiveJobRepository _repository;
  late JobQueueManager _queueManager;
  late RetryScheduler _retryScheduler;
  
  /// Initialize the performance test environment
  Future<void> initialize() async {
    _tempDir = await Directory.systemTemp.createTemp('perf_test_');
    Hive.init(_tempDir.path);
    
    if (!Hive.isAdapterRegistered(HiveAnalysisJobAdapter().typeId)) {
      Hive.registerAdapter(HiveAnalysisJobAdapter());
    }
    
    _repository = HiveJobRepository();
    await _repository.init();
    
    _queueManager = JobQueueManager(repository: _repository);
    await _queueManager.initialize();
    
    _retryScheduler = RetryScheduler(
      repository: _repository,
      queueManager: _queueManager,
      retryPolicy: JobRetryPolicy.testing(),
    );
    await _retryScheduler.initialize();
  }
  
  /// Clean up test environment
  Future<void> dispose() async {
    await _retryScheduler.dispose();
    _queueManager.dispose();
    
    try {
      if (Hive.isBoxOpen('analysis_jobs')) {
        await Hive.box('analysis_jobs').clear();
        await Hive.box('analysis_jobs').close();
      }
    } catch (e) {
      // Ignore cleanup errors
    }
    
    if (_tempDir.existsSync()) {
      _tempDir.deleteSync(recursive: true);
    }
  }
  
  /// Run a comprehensive performance benchmark suite
  Future<PerformanceBenchmarkResults> runBenchmarkSuite() async {
    final results = PerformanceBenchmarkResults();
    
    // Repository performance tests
    results.repositoryResults = await _benchmarkRepository();
    
    // Queue manager performance tests
    results.queueResults = await _benchmarkQueueManager();
    
    // Retry scheduler performance tests
    results.retryResults = await _benchmarkRetryScheduler();
    
    // Load testing
    results.loadTestResults = await _benchmarkLoadTesting();
    
    // Memory usage analysis
    results.memoryResults = await _benchmarkMemoryUsage();
    
    return results;
  }
  
  /// Benchmark repository operations
  Future<RepositoryBenchmarkResults> _benchmarkRepository() async {
    final results = RepositoryBenchmarkResults();
    
    // Test single job save performance
    final singleSaveStopwatch = Stopwatch()..start();
    final testJob = _createTestJob('single-save-test');
    await _repository.save(testJob);
    singleSaveStopwatch.stop();
    results.singleSaveTime = singleSaveStopwatch.elapsedMicroseconds;
    
    // Test batch save performance
    final batchJobs = List.generate(100, (i) => _createTestJob('batch-$i'));
    final batchSaveStopwatch = Stopwatch()..start();
    for (final job in batchJobs) {
      await _repository.save(job);
    }
    batchSaveStopwatch.stop();
    results.batchSaveTime = batchSaveStopwatch.elapsedMicroseconds;
    results.avgSaveTimePerJob = results.batchSaveTime / batchJobs.length;
    
    // Test retrieval performance
    final retrievalStopwatch = Stopwatch()..start();
    final retrievedJobs = await _repository.getAll();
    retrievalStopwatch.stop();
    results.retrievalTime = retrievalStopwatch.elapsedMicroseconds;
    results.jobsRetrieved = retrievedJobs.length;
    
    // Test query by status performance
    final queryStopwatch = Stopwatch()..start();
    final pendingJobs = await _repository.getByStatus(JobStatus.pending);
    queryStopwatch.stop();
    results.queryTime = queryStopwatch.elapsedMicroseconds;
    results.jobsQueried = pendingJobs.length;
    
    // Test update performance
    final updateJob = retrievedJobs.first.copyWith(status: JobStatus.running);
    final updateStopwatch = Stopwatch()..start();
    await _repository.update(updateJob);
    updateStopwatch.stop();
    results.updateTime = updateStopwatch.elapsedMicroseconds;
    
    return results;
  }
  
  /// Benchmark queue manager operations
  Future<QueueBenchmarkResults> _benchmarkQueueManager() async {
    final results = QueueBenchmarkResults();
    
    // Test enqueue performance
    final enqueueJobs = List.generate(50, (i) => _createTestJob('enqueue-$i'));
    final enqueueStopwatch = Stopwatch()..start();
    for (final job in enqueueJobs) {
      await _queueManager.enqueue(job);
    }
    enqueueStopwatch.stop();
    results.enqueueTime = enqueueStopwatch.elapsedMicroseconds;
    results.avgEnqueueTime = results.enqueueTime / enqueueJobs.length;
    
    // Test dequeue performance
    final dequeueStopwatch = Stopwatch()..start();
    final dequeuedJobs = <AnalysisJob>[];
    AnalysisJob? job;
    do {
      job = await _queueManager.dequeue();
      if (job != null) {
        dequeuedJobs.add(job);
      }
    } while (job != null);
    dequeueStopwatch.stop();
    results.dequeueTime = dequeueStopwatch.elapsedMicroseconds;
    results.jobsDequeued = dequeuedJobs.length;
    results.avgDequeueTime = dequeuedJobs.isNotEmpty 
        ? results.dequeueTime / dequeuedJobs.length 
        : 0;
    
    // Test priority ordering performance
    final priorityJobs = [
      _createTestJob('low', priority: JobPriority.low),
      _createTestJob('critical', priority: JobPriority.critical),
      _createTestJob('normal', priority: JobPriority.normal),
      _createTestJob('high', priority: JobPriority.high),
    ];
    
    final priorityStopwatch = Stopwatch()..start();
    for (final job in priorityJobs) {
      await _queueManager.enqueue(job);
    }
    
    final orderedJobs = <AnalysisJob>[];
    AnalysisJob? priorityJob;
    do {
      priorityJob = await _queueManager.dequeue();
      if (priorityJob != null) {
        orderedJobs.add(priorityJob);
      }
    } while (priorityJob != null);
    priorityStopwatch.stop();
    
    results.priorityOrderingTime = priorityStopwatch.elapsedMicroseconds;
    results.priorityOrderCorrect = orderedJobs.isNotEmpty && 
        orderedJobs.first.priority == JobPriority.critical;
    
    return results;
  }
  
  /// Benchmark retry scheduler operations
  Future<RetryBenchmarkResults> _benchmarkRetryScheduler() async {
    final results = RetryBenchmarkResults();
    
    // Create failed jobs for retry testing
    final failedJobs = List.generate(20, (i) => AnalysisJob(
      id: 'retry-$i',
      ticker: 'RETRY$i',
      tradeDate: '2024-01-20',
      status: JobStatus.failed,
      priority: JobPriority.normal,
      createdAt: DateTime.now(),
      completedAt: DateTime.now(),
      retryCount: 1,
      maxRetries: 3,
      errorMessage: 'Test failure',
    ));
    
    // Save failed jobs
    for (final job in failedJobs) {
      await _repository.save(job);
    }
    
    // Test retry scheduling performance
    final scheduleStopwatch = Stopwatch()..start();
    for (final job in failedJobs) {
      await _retryScheduler.scheduleRetry(job);
    }
    scheduleStopwatch.stop();
    
    results.scheduleTime = scheduleStopwatch.elapsedMicroseconds;
    results.avgScheduleTime = results.scheduleTime / failedJobs.length;
    results.scheduledCount = _retryScheduler.scheduledRetryCount;
    
    // Test retry cancellation performance
    final cancelStopwatch = Stopwatch()..start();
    for (final job in failedJobs.take(10)) {
      await _retryScheduler.cancelRetry(job.id);
    }
    cancelStopwatch.stop();
    
    results.cancelTime = cancelStopwatch.elapsedMicroseconds;
    results.avgCancelTime = results.cancelTime / 10;
    results.remainingScheduled = _retryScheduler.scheduledRetryCount;
    
    return results;
  }
  
  /// Benchmark load testing scenarios
  Future<LoadTestResults> _benchmarkLoadTesting() async {
    final results = LoadTestResults();
    
    // High volume job creation
    final heavyLoadStopwatch = Stopwatch()..start();
    final heavyLoadJobs = List.generate(500, (i) => _createTestJob('heavy-$i'));
    
    // Simulate burst load
    final futures = <Future>[];
    for (final job in heavyLoadJobs) {
      futures.add(_queueManager.enqueue(job));
    }
    await Future.wait(futures);
    
    heavyLoadStopwatch.stop();
    results.heavyLoadTime = heavyLoadStopwatch.elapsedMicroseconds;
    results.heavyLoadJobCount = heavyLoadJobs.length;
    results.avgJobThroughput = heavyLoadJobs.length / 
        (heavyLoadStopwatch.elapsedMicroseconds / 1000000);
    
    // Concurrent operations stress test
    final stressStopwatch = Stopwatch()..start();
    final stressFutures = <Future>[];
    
    // Concurrent enqueues
    for (int i = 0; i < 50; i++) {
      stressFutures.add(_queueManager.enqueue(_createTestJob('stress-enqueue-$i')));
    }
    
    // Concurrent dequeues
    for (int i = 0; i < 25; i++) {
      stressFutures.add(_queueManager.dequeue());
    }
    
    // Concurrent status checks
    for (int i = 0; i < 25; i++) {
      stressFutures.add(_queueManager.getStatistics());
    }
    
    await Future.wait(stressFutures);
    stressStopwatch.stop();
    
    results.stressTestTime = stressStopwatch.elapsedMicroseconds;
    results.concurrentOperations = stressFutures.length;
    
    return results;
  }
  
  /// Benchmark memory usage patterns
  Future<MemoryBenchmarkResults> _benchmarkMemoryUsage() async {
    final results = MemoryBenchmarkResults();
    
    // Measure baseline memory
    final baselineInfo = ProcessInfo.currentRss;
    results.baselineMemory = baselineInfo;
    
    // Create large number of jobs and measure memory growth
    final memoryJobs = List.generate(1000, (i) => _createTestJob('memory-$i'));
    
    final beforeCreation = ProcessInfo.currentRss;
    
    for (final job in memoryJobs) {
      await _repository.save(job);
      await _queueManager.enqueue(job);
    }
    
    final afterCreation = ProcessInfo.currentRss;
    results.peakMemory = afterCreation;
    results.memoryGrowth = afterCreation - beforeCreation;
    results.avgMemoryPerJob = results.memoryGrowth / memoryJobs.length;
    
    // Test memory cleanup
    await _repository.clearAll();
    
    // Force garbage collection (platform dependent)
    for (int i = 0; i < 5; i++) {
      await Future.delayed(const Duration(milliseconds: 100));
    }
    
    final afterCleanup = ProcessInfo.currentRss;
    results.memoryAfterCleanup = afterCleanup;
    results.memoryReclaimed = afterCreation - afterCleanup;
    
    return results;
  }
  
  /// Create a test job with optional parameters
  AnalysisJob _createTestJob(String id, {JobPriority? priority}) {
    return AnalysisJob(
      id: id,
      ticker: 'TEST${Random().nextInt(1000)}',
      tradeDate: '2024-01-20',
      status: JobStatus.pending,
      priority: priority ?? JobPriority.normal,
      createdAt: DateTime.now(),
      retryCount: 0,
    );
  }
}

/// Comprehensive benchmark results container
class PerformanceBenchmarkResults {
  late RepositoryBenchmarkResults repositoryResults;
  late QueueBenchmarkResults queueResults;
  late RetryBenchmarkResults retryResults;
  late LoadTestResults loadTestResults;
  late MemoryBenchmarkResults memoryResults;
  
  /// Generate a comprehensive report
  String generateReport() {
    final buffer = StringBuffer();
    buffer.writeln('=== PERFORMANCE BENCHMARK RESULTS ===\n');
    
    buffer.writeln('Repository Performance:');
    buffer.writeln(repositoryResults.toString());
    buffer.writeln();
    
    buffer.writeln('Queue Manager Performance:');
    buffer.writeln(queueResults.toString());
    buffer.writeln();
    
    buffer.writeln('Retry Scheduler Performance:');
    buffer.writeln(retryResults.toString());
    buffer.writeln();
    
    buffer.writeln('Load Testing Results:');
    buffer.writeln(loadTestResults.toString());
    buffer.writeln();
    
    buffer.writeln('Memory Usage Analysis:');
    buffer.writeln(memoryResults.toString());
    buffer.writeln();
    
    buffer.writeln('=== PERFORMANCE SUMMARY ===');
    buffer.writeln('Overall Performance: ${_getOverallRating()}');
    buffer.writeln('Key Recommendations: ${_getRecommendations()}');
    
    return buffer.toString();
  }
  
  String _getOverallRating() {
    final scores = <String, double>{
      'Repository': repositoryResults.getPerformanceScore(),
      'Queue': queueResults.getPerformanceScore(),
      'Retry': retryResults.getPerformanceScore(),
      'Load': loadTestResults.getPerformanceScore(),
      'Memory': memoryResults.getPerformanceScore(),
    };
    
    final avgScore = scores.values.reduce((a, b) => a + b) / scores.length;
    
    if (avgScore >= 90) return 'EXCELLENT';
    if (avgScore >= 80) return 'GOOD';
    if (avgScore >= 70) return 'ACCEPTABLE';
    if (avgScore >= 60) return 'NEEDS IMPROVEMENT';
    return 'POOR';
  }
  
  List<String> _getRecommendations() {
    final recommendations = <String>[];
    
    if (repositoryResults.avgSaveTimePerJob > 1000) {
      recommendations.add('Consider batch operations for repository saves');
    }
    
    if (queueResults.avgEnqueueTime > 500) {
      recommendations.add('Optimize queue enqueue operations');
    }
    
    if (memoryResults.avgMemoryPerJob > 1024) {
      recommendations.add('Review job object memory footprint');
    }
    
    if (loadTestResults.avgJobThroughput < 100) {
      recommendations.add('Improve overall system throughput');
    }
    
    if (recommendations.isEmpty) {
      recommendations.add('Performance is within acceptable limits');
    }
    
    return recommendations;
  }
}

/// Repository-specific benchmark results
class RepositoryBenchmarkResults {
  late int singleSaveTime;
  late int batchSaveTime;
  late double avgSaveTimePerJob;
  late int retrievalTime;
  late int jobsRetrieved;
  late int queryTime;
  late int jobsQueried;
  late int updateTime;
  
  double getPerformanceScore() {
    double score = 100.0;
    
    // Penalize slow operations
    if (avgSaveTimePerJob > 1000) score -= 20;
    if (retrievalTime > 10000) score -= 15;
    if (queryTime > 5000) score -= 15;
    if (updateTime > 1000) score -= 10;
    
    return score.clamp(0.0, 100.0);
  }
  
  @override
  String toString() {
    return '''
  Single Save Time: ${singleSaveTime}μs
  Batch Save Time: ${batchSaveTime}μs (${jobsRetrieved} jobs)
  Avg Save Time per Job: ${avgSaveTimePerJob.toStringAsFixed(2)}μs
  Retrieval Time: ${retrievalTime}μs (${jobsRetrieved} jobs)
  Query Time: ${queryTime}μs (${jobsQueried} jobs)
  Update Time: ${updateTime}μs
  Performance Score: ${getPerformanceScore().toStringAsFixed(1)}/100''';
  }
}

/// Queue manager benchmark results
class QueueBenchmarkResults {
  late int enqueueTime;
  late double avgEnqueueTime;
  late int dequeueTime;
  late int jobsDequeued;
  late double avgDequeueTime;
  late int priorityOrderingTime;
  late bool priorityOrderCorrect;
  
  double getPerformanceScore() {
    double score = 100.0;
    
    if (avgEnqueueTime > 500) score -= 25;
    if (avgDequeueTime > 300) score -= 25;
    if (!priorityOrderCorrect) score -= 30;
    if (priorityOrderingTime > 5000) score -= 20;
    
    return score.clamp(0.0, 100.0);
  }
  
  @override
  String toString() {
    return '''
  Enqueue Time: ${enqueueTime}μs
  Avg Enqueue Time: ${avgEnqueueTime.toStringAsFixed(2)}μs
  Dequeue Time: ${dequeueTime}μs (${jobsDequeued} jobs)
  Avg Dequeue Time: ${avgDequeueTime.toStringAsFixed(2)}μs
  Priority Ordering Time: ${priorityOrderingTime}μs
  Priority Order Correct: $priorityOrderCorrect
  Performance Score: ${getPerformanceScore().toStringAsFixed(1)}/100''';
  }
}

/// Retry scheduler benchmark results
class RetryBenchmarkResults {
  late int scheduleTime;
  late double avgScheduleTime;
  late int scheduledCount;
  late int cancelTime;
  late double avgCancelTime;
  late int remainingScheduled;
  
  double getPerformanceScore() {
    double score = 100.0;
    
    if (avgScheduleTime > 1000) score -= 30;
    if (avgCancelTime > 500) score -= 20;
    if (scheduledCount == 0) score -= 50;
    
    return score.clamp(0.0, 100.0);
  }
  
  @override
  String toString() {
    return '''
  Schedule Time: ${scheduleTime}μs (${scheduledCount} jobs)
  Avg Schedule Time: ${avgScheduleTime.toStringAsFixed(2)}μs
  Cancel Time: ${cancelTime}μs
  Avg Cancel Time: ${avgCancelTime.toStringAsFixed(2)}μs
  Remaining Scheduled: $remainingScheduled
  Performance Score: ${getPerformanceScore().toStringAsFixed(1)}/100''';
  }
}

/// Load testing results
class LoadTestResults {
  late int heavyLoadTime;
  late int heavyLoadJobCount;
  late double avgJobThroughput;
  late int stressTestTime;
  late int concurrentOperations;
  
  double getPerformanceScore() {
    double score = 100.0;
    
    if (avgJobThroughput < 50) score -= 40;
    if (heavyLoadTime > 1000000) score -= 30; // 1 second
    if (stressTestTime > 500000) score -= 30; // 0.5 seconds
    
    return score.clamp(0.0, 100.0);
  }
  
  @override
  String toString() {
    return '''
  Heavy Load Time: ${heavyLoadTime}μs (${heavyLoadJobCount} jobs)
  Avg Job Throughput: ${avgJobThroughput.toStringAsFixed(2)} jobs/sec
  Stress Test Time: ${stressTestTime}μs (${concurrentOperations} operations)
  Performance Score: ${getPerformanceScore().toStringAsFixed(1)}/100''';
  }
}

/// Memory usage benchmark results
class MemoryBenchmarkResults {
  late int baselineMemory;
  late int peakMemory;
  late int memoryGrowth;
  late double avgMemoryPerJob;
  late int memoryAfterCleanup;
  late int memoryReclaimed;
  
  double getPerformanceScore() {
    double score = 100.0;
    
    if (avgMemoryPerJob > 2048) score -= 30; // 2KB per job
    if (memoryReclaimed < (memoryGrowth * 0.8)) score -= 40; // Should reclaim 80%
    
    return score.clamp(0.0, 100.0);
  }
  
  @override
  String toString() {
    return '''
  Baseline Memory: ${(baselineMemory / 1024).toStringAsFixed(2)}KB
  Peak Memory: ${(peakMemory / 1024).toStringAsFixed(2)}KB
  Memory Growth: ${(memoryGrowth / 1024).toStringAsFixed(2)}KB
  Avg Memory per Job: ${avgMemoryPerJob.toStringAsFixed(2)} bytes
  Memory After Cleanup: ${(memoryAfterCleanup / 1024).toStringAsFixed(2)}KB
  Memory Reclaimed: ${(memoryReclaimed / 1024).toStringAsFixed(2)}KB
  Performance Score: ${getPerformanceScore().toStringAsFixed(1)}/100''';
  }
}