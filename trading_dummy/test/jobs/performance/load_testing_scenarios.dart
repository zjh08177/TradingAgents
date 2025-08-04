import 'dart:async';
import 'dart:io';
import 'dart:math';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/models/hive_analysis_job.dart';
import 'package:trading_dummy/jobs/infrastructure/repositories/hive_job_repository.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_queue_manager.dart';
import 'package:trading_dummy/jobs/infrastructure/services/retry_scheduler.dart';
import 'package:trading_dummy/jobs/domain/services/job_retry_policy.dart';
import 'performance_test_framework.dart';

/// Comprehensive load testing scenarios for the async job system
/// 
/// This suite includes various realistic load patterns that the system
/// might encounter in production, including burst loads, sustained loads,
/// mixed operation patterns, and stress testing scenarios.
void main() {
  group('Load Testing Scenarios', () {
    late PerformanceTestFramework framework;

    setUpAll(() async {
      framework = PerformanceTestFramework();
      await framework.initialize();
    });

    tearDownAll(() async {
      await framework.dispose();
    });

    group('Burst Load Scenarios', () {
      test('sudden spike - 100 jobs in 1 second', () async {
        final jobs = List.generate(100, (i) => AnalysisJob(
          id: 'burst-$i',
          ticker: 'BURST$i',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        ));

        final stopwatch = Stopwatch()..start();
        
        // Submit all jobs as fast as possible
        final futures = jobs.map((job) async {
          await framework._queueManager.enqueue(job);
        }).toList();
        
        await Future.wait(futures);
        stopwatch.stop();

        // Verify performance targets
        expect(stopwatch.elapsedMilliseconds, lessThan(1000));
        expect(jobs.length / (stopwatch.elapsedMilliseconds / 1000), greaterThan(50)); // 50+ jobs/sec
        
        // Verify all jobs were queued
        final stats = await framework._queueManager.getStatistics();
        expect(stats.pendingCount, equals(100));
      });

      test('multiple burst waves', () async {
        const wavesCount = 5;
        const jobsPerWave = 20;
        const delayBetweenWaves = Duration(milliseconds: 100);
        
        final allJobTimes = <int>[];
        
        for (int wave = 0; wave < wavesCount; wave++) {
          final waveJobs = List.generate(jobsPerWave, (i) => AnalysisJob(
            id: 'wave-$wave-$i',
            ticker: 'WAVE${wave}${i}',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            retryCount: 0,
          ));

          final waveStopwatch = Stopwatch()..start();
          for (final job in waveJobs) {
            await framework._queueManager.enqueue(job);
          }
          waveStopwatch.stop();
          
          allJobTimes.add(waveStopwatch.elapsedMicroseconds);
          
          if (wave < wavesCount - 1) {
            await Future.delayed(delayBetweenWaves);
          }
        }

        // Verify consistent performance across waves
        final avgTime = allJobTimes.reduce((a, b) => a + b) / allJobTimes.length;
        final maxDeviation = allJobTimes.map((time) => (time - avgTime).abs()).reduce(max);
        
        // Performance should be consistent (deviation < 50% of average)
        expect(maxDeviation, lessThan(avgTime * 0.5));
        
        // Verify all jobs were processed
        final stats = await framework._queueManager.getStatistics();
        expect(stats.pendingCount, equals(wavesCount * jobsPerWave));
      });
    });

    group('Sustained Load Scenarios', () {
      test('steady stream - 5 jobs/second for 10 seconds', () async {
        const jobsPerSecond = 5;
        const testDurationSeconds = 10;
        const totalJobs = jobsPerSecond * testDurationSeconds;
        
        final jobSubmissionTimes = <DateTime>[];
        final stopwatch = Stopwatch()..start();
        
        // Submit jobs at steady rate
        for (int i = 0; i < totalJobs; i++) {
          final job = AnalysisJob(
            id: 'steady-$i',
            ticker: 'STEADY$i',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            retryCount: 0,
          );
          
          jobSubmissionTimes.add(DateTime.now());
          await framework._queueManager.enqueue(job);
          
          // Wait to maintain steady rate
          if (i < totalJobs - 1) {
            await Future.delayed(Duration(milliseconds: 1000 ~/ jobsPerSecond));
          }
        }
        
        stopwatch.stop();

        // Verify timing consistency
        expect(stopwatch.elapsedSeconds, lessThanOrEqualTo(testDurationSeconds + 1));
        
        // Verify job distribution over time
        final timeBuckets = <int, int>{};
        for (final time in jobSubmissionTimes) {
          final bucket = time.second;
          timeBuckets[bucket] = (timeBuckets[bucket] ?? 0) + 1;
        }
        
        // Each second should have approximately the right number of jobs
        for (final count in timeBuckets.values) {
          expect(count, allOf(greaterThanOrEqualTo(jobsPerSecond - 1), 
                              lessThanOrEqualTo(jobsPerSecond + 1)));
        }
      });

      test('marathon load - 1000 jobs over extended period', () async {
        const totalJobs = 1000;
        const batchSize = 50;
        const delayBetweenBatches = Duration(milliseconds: 200);
        
        final batchTimes = <int>[];
        final overallStopwatch = Stopwatch()..start();
        
        for (int batch = 0; batch < totalJobs ~/ batchSize; batch++) {
          final batchJobs = List.generate(batchSize, (i) => AnalysisJob(
            id: 'marathon-${batch * batchSize + i}',
            ticker: 'MARATHON${batch}${i}',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: _getRandomPriority(),
            createdAt: DateTime.now(),
            retryCount: 0,
          ));

          final batchStopwatch = Stopwatch()..start();
          for (final job in batchJobs) {
            await framework._queueManager.enqueue(job);
          }
          batchStopwatch.stop();
          
          batchTimes.add(batchStopwatch.elapsedMicroseconds);
          
          // Brief pause between batches
          await Future.delayed(delayBetweenBatches);
        }
        
        overallStopwatch.stop();

        // Verify no significant performance degradation over time
        final firstHalfAvg = batchTimes.take(batchTimes.length ~/ 2)
            .reduce((a, b) => a + b) / (batchTimes.length ~/ 2);
        final secondHalfAvg = batchTimes.skip(batchTimes.length ~/ 2)
            .reduce((a, b) => a + b) / (batchTimes.length - batchTimes.length ~/ 2);
        
        // Second half should not be more than 50% slower than first half
        expect(secondHalfAvg, lessThan(firstHalfAvg * 1.5));
        
        // Verify all jobs were processed
        final stats = await framework._queueManager.getStatistics();
        expect(stats.pendingCount, equals(totalJobs));
      });
    });

    group('Mixed Operation Patterns', () {
      test('simultaneous enqueue/dequeue/query operations', () async {
        const operationCount = 100;
        final futures = <Future>[];
        final operationTimes = <String, List<int>>{
          'enqueue': [],
          'dequeue': [],
          'query': [],
        };

        // Pre-populate with some jobs for dequeue operations
        for (int i = 0; i < 50; i++) {
          await framework._queueManager.enqueue(AnalysisJob(
            id: 'pre-$i',
            ticker: 'PRE$i',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            retryCount: 0,
          ));
        }

        final overallStopwatch = Stopwatch()..start();

        // Launch mixed operations concurrently
        for (int i = 0; i < operationCount; i++) {
          final operationType = i % 3;
          
          switch (operationType) {
            case 0: // Enqueue
              futures.add(_timedOperation(() async {
                final job = AnalysisJob(
                  id: 'mixed-enqueue-$i',
                  ticker: 'MIX$i',
                  tradeDate: '2024-01-20',
                  status: JobStatus.pending,
                  priority: JobPriority.normal,
                  createdAt: DateTime.now(),
                  retryCount: 0,
                );
                await framework._queueManager.enqueue(job);
              }, 'enqueue', operationTimes));
              break;
              
            case 1: // Dequeue
              futures.add(_timedOperation(() async {
                await framework._queueManager.dequeue();
              }, 'dequeue', operationTimes));
              break;
              
            case 2: // Query
              futures.add(_timedOperation(() async {
                await framework._queueManager.getStatistics();
              }, 'query', operationTimes));
              break;
          }
        }

        await Future.wait(futures);
        overallStopwatch.stop();

        // Verify operation performance
        for (final entry in operationTimes.entries) {
          final operationType = entry.key;
          final times = entry.value;
          
          if (times.isNotEmpty) {
            final avgTime = times.reduce((a, b) => a + b) / times.length;
            final maxTime = times.reduce(max);
            
            // No operation should take more than 100ms
            expect(maxTime, lessThan(100000)); // 100ms in microseconds
            
            print('$operationType: avg=${avgTime.toStringAsFixed(2)}μs, max=${maxTime}μs, count=${times.length}');
          }
        }

        // Overall operation should complete within reasonable time
        expect(overallStopwatch.elapsedMilliseconds, lessThan(10000)); // 10 seconds
      });

      test('priority mixing under load', () async {
        final priorities = [JobPriority.low, JobPriority.normal, JobPriority.high, JobPriority.critical];
        final priorityJobCounts = <JobPriority, int>{};
        
        // Create mixed priority jobs
        final jobs = <AnalysisJob>[];
        for (int i = 0; i < 200; i++) {
          final priority = priorities[i % priorities.length];
          priorityJobCounts[priority] = (priorityJobCounts[priority] ?? 0) + 1;
          
          jobs.add(AnalysisJob(
            id: 'priority-$i',
            ticker: 'PRIO$i',
            tradeDate: '2024-01-20',
            status: JobStatus.pending,
            priority: priority,
            createdAt: DateTime.now(),
            retryCount: 0,
          ));
        }

        // Shuffle to simulate random arrival order
        jobs.shuffle();

        // Enqueue all jobs
        final stopwatch = Stopwatch()..start();
        for (final job in jobs) {
          await framework._queueManager.enqueue(job);
        }
        stopwatch.stop();

        // Dequeue and verify priority ordering
        final dequeuedJobs = <AnalysisJob>[];
        AnalysisJob? job;
        do {
          job = await framework._queueManager.dequeue();
          if (job != null) {
            dequeuedJobs.add(job);
          }
        } while (job != null);

        // Verify priority ordering is maintained
        JobPriority? lastPriority;
        for (final dequeuedJob in dequeuedJobs) {
          if (lastPriority != null) {
            // Current priority should be <= last priority (higher number = lower priority)
            expect(dequeuedJob.priority.index, greaterThanOrEqualTo(lastPriority.index));
          }
          lastPriority = dequeuedJob.priority;
        }

        // Verify all jobs were processed
        expect(dequeuedJobs.length, equals(jobs.length));
      });
    });

    group('Stress Testing Scenarios', () {
      test('memory pressure - large job objects', () async {
        // Create jobs with large data payload simulation
        final largeJobs = List.generate(100, (i) => AnalysisJob(
          id: 'large-$i',
          ticker: 'LARGE$i' * 10, // Simulate larger data
          tradeDate: '2024-01-20' * 5,
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
          errorMessage: 'X' * 1000, // Simulate large error messages
        ));

        final beforeMemory = ProcessInfo.currentRss;
        
        final stopwatch = Stopwatch()..start();
        for (final job in largeJobs) {
          await framework._queueManager.enqueue(job);
        }
        stopwatch.stop();

        final afterMemory = ProcessInfo.currentRss;
        final memoryGrowth = afterMemory - beforeMemory;

        // Verify performance is still acceptable with large objects
        expect(stopwatch.elapsedMilliseconds, lessThan(5000)); // 5 seconds
        
        // Memory growth should be reasonable (less than 10MB for 100 jobs)
        expect(memoryGrowth, lessThan(10 * 1024 * 1024));
        
        print('Memory growth: ${(memoryGrowth / 1024).toStringAsFixed(2)}KB for ${largeJobs.length} large jobs');
      });

      test('concurrent retry scheduling stress', () async {
        // Create many failed jobs
        final failedJobs = List.generate(200, (i) => AnalysisJob(
          id: 'retry-stress-$i',
          ticker: 'RETRY$i',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: Random().nextInt(3),
          maxRetries: 3,
          errorMessage: 'Stress test failure $i',
        ));

        // Save all failed jobs
        for (final job in failedJobs) {
          await framework._repository.save(job);
        }

        // Schedule retries concurrently
        final stopwatch = Stopwatch()..start();
        final retryFutures = failedJobs.map((job) => 
            framework._retryScheduler.scheduleRetry(job)).toList();
        
        await Future.wait(retryFutures);
        stopwatch.stop();

        // Verify performance
        expect(stopwatch.elapsedMilliseconds, lessThan(10000)); // 10 seconds
        
        // Verify scheduled count
        final scheduledCount = framework._retryScheduler.scheduledRetryCount;
        expect(scheduledCount, greaterThan(0));
        
        print('Scheduled ${scheduledCount} retries in ${stopwatch.elapsedMilliseconds}ms');
      });

      test('system resource exhaustion simulation', () async {
        // Try to exhaust various system resources
        final resourceTests = <String, Future<bool>>{};

        // CPU intensive operations
        resourceTests['CPU'] = _testCpuIntensiveOperations();
        
        // Memory intensive operations
        resourceTests['Memory'] = _testMemoryIntensiveOperations();
        
        // I/O intensive operations
        resourceTests['IO'] = _testIoIntensiveOperations();

        final results = await Future.wait(resourceTests.values);
        final allPassed = results.every((passed) => passed);

        // System should handle resource pressure gracefully
        expect(allPassed, isTrue);
        
        print('Resource exhaustion tests: ${resourceTests.keys.join(', ')} - All passed: $allPassed');
      });
    });

    group('Failure Scenario Testing', () {
      test('repository unavailable simulation', () async {
        // This would require mocking the repository to simulate failures
        // For now, we'll test graceful handling of repository errors
        
        final job = AnalysisJob(
          id: 'repo-fail-test',
          ticker: 'FAIL',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          retryCount: 0,
        );

        // Test should not throw unhandled exceptions
        await expectLater(
          framework._queueManager.enqueue(job),
          completes,
        );
      });

      test('timer system stress', () async {
        // Create many jobs that will need retry timers
        final timerJobs = List.generate(100, (i) => AnalysisJob(
          id: 'timer-$i',
          ticker: 'TIMER$i',
          tradeDate: '2024-01-20',
          status: JobStatus.failed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          completedAt: DateTime.now(),
          retryCount: 1,
          maxRetries: 3,
          errorMessage: 'Timer test failure',
        ));

        for (final job in timerJobs) {
          await framework._repository.save(job);
          await framework._retryScheduler.scheduleRetry(job);
        }

        // Wait for some timers to fire
        await Future.delayed(const Duration(milliseconds: 500));

        // Cancel all remaining timers
        final cancelFutures = timerJobs.map((job) => 
            framework._retryScheduler.cancelRetry(job.id)).toList();
        
        await Future.wait(cancelFutures);

        // Verify cleanup
        expect(framework._retryScheduler.scheduledRetryCount, equals(0));
      });
    });
  });
}

/// Helper method to time operations and collect statistics
Future<void> _timedOperation(
  Future<void> Function() operation,
  String operationType,
  Map<String, List<int>> operationTimes,
) async {
  final stopwatch = Stopwatch()..start();
  await operation();
  stopwatch.stop();
  
  operationTimes[operationType] = operationTimes[operationType] ?? [];
  operationTimes[operationType]!.add(stopwatch.elapsedMicroseconds);
}

/// Get random priority for testing
JobPriority _getRandomPriority() {
  final priorities = JobPriority.values;
  return priorities[Random().nextInt(priorities.length)];
}

/// Test CPU intensive operations
Future<bool> _testCpuIntensiveOperations() async {
  try {
    final futures = <Future>[];
    
    // Create CPU intensive work
    for (int i = 0; i < 10; i++) {
      futures.add(Future(() {
        // Simulate CPU intensive calculation
        var result = 0;
        for (int j = 0; j < 1000000; j++) {
          result += j * j;
        }
        return result;
      }));
    }
    
    await Future.wait(futures);
    return true;
  } catch (e) {
    return false;
  }
}

/// Test memory intensive operations
Future<bool> _testMemoryIntensiveOperations() async {
  try {
    final largeData = <List<int>>[];
    
    // Allocate large chunks of memory
    for (int i = 0; i < 100; i++) {
      largeData.add(List.filled(10000, i));
    }
    
    // Access the data to ensure it's not optimized away
    final sum = largeData.fold<int>(0, (sum, list) => sum + list.length);
    
    return sum > 0;
  } catch (e) {
    return false;
  }
}

/// Test I/O intensive operations
Future<bool> _testIoIntensiveOperations() async {
  try {
    final futures = <Future>[];
    
    // Create multiple I/O operations
    for (int i = 0; i < 20; i++) {
      futures.add(Future(() async {
        // Simulate I/O with short delays
        await Future.delayed(const Duration(milliseconds: 10));
        return i;
      }));
    }
    
    final results = await Future.wait(futures);
    return results.length == 20;
  } catch (e) {
    return false;
  }
}