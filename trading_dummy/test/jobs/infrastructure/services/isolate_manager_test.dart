import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/infrastructure/services/isolate_manager.dart';

// Test task that returns a simple result
class TestTask extends IsolateTask<String> {
  final String input;
  final Duration? delay;
  final bool shouldFail;
  
  TestTask(this.input, {this.delay, this.shouldFail = false});
  
  @override
  Future<String> execute() async {
    if (delay != null) {
      await Future.delayed(delay!);
    }
    
    if (shouldFail) {
      throw Exception('Task failed: $input');
    }
    
    return 'Processed: $input';
  }
}

// Task that performs computation
class ComputationTask extends IsolateTask<int> {
  final int n;
  
  ComputationTask(this.n);
  
  @override
  Future<int> execute() async {
    // Compute factorial
    int result = 1;
    for (int i = 1; i <= n; i++) {
      result *= i;
    }
    return result;
  }
}

void main() {
  group('IsolateManager', () {
    late IsolateManager manager;
    
    setUp(() async {
      manager = IsolateManager(maxIsolates: 2);
      await manager.initialize();
    });
    
    tearDown(() {
      manager.dispose();
    });
    
    test('initialize creates correct number of isolates', () async {
      final stats = manager.getStats();
      expect(stats.totalIsolates, equals(2));
      expect(stats.availableIsolates, equals(2));
      expect(stats.busyIsolates, equals(0));
      expect(stats.pendingTasks, equals(0));
    });
    
    test('execute runs task and returns result', () async {
      final task = TestTask('Hello');
      final result = await manager.execute(task);
      
      expect(result, equals('Processed: Hello'));
    });
    
    test('execute runs multiple tasks concurrently', () async {
      final tasks = [
        TestTask('Task1', delay: const Duration(milliseconds: 100)),
        TestTask('Task2', delay: const Duration(milliseconds: 100)),
      ];
      
      final stopwatch = Stopwatch()..start();
      
      final results = await Future.wait([
        manager.execute(tasks[0]),
        manager.execute(tasks[1]),
      ]);
      
      stopwatch.stop();
      
      expect(results[0], equals('Processed: Task1'));
      expect(results[1], equals('Processed: Task2'));
      
      // Should run concurrently, so time should be ~100ms, not 200ms
      expect(stopwatch.elapsedMilliseconds, lessThan(150));
    });
    
    test('execute queues tasks when all isolates are busy', () async {
      // Create 3 tasks but only have 2 isolates
      final tasks = [
        TestTask('Task1', delay: const Duration(milliseconds: 200)),
        TestTask('Task2', delay: const Duration(milliseconds: 200)),
        TestTask('Task3', delay: const Duration(milliseconds: 100)),
      ];
      
      // Start all tasks
      final futures = tasks.map((task) => manager.execute(task)).toList();
      
      // Check stats after a brief delay to allow setup
      await Future.delayed(const Duration(milliseconds: 100));
      final stats = manager.getStats();
      expect(stats.busyIsolates, greaterThanOrEqualTo(1)); // At least 1 should be busy
      expect(stats.pendingTasks, greaterThanOrEqualTo(1)); // At least 1 should be pending
      
      // Wait for all to complete
      final results = await Future.wait(futures);
      
      expect(results[0], equals('Processed: Task1'));
      expect(results[1], equals('Processed: Task2'));
      expect(results[2], equals('Processed: Task3'));
    });
    
    test('execute handles task errors correctly', () async {
      final task = TestTask('Error', shouldFail: true);
      
      expect(
        () => manager.execute(task),
        throwsA(isA<Exception>().having(
          (e) => e.toString(),
          'message',
          contains('Task failed: Error'),
        )),
      );
    });
    
    test('execute handles multiple task types', () async {
      final stringTask = TestTask('Hello');
      final computeTask = ComputationTask(5);
      
      final results = await Future.wait([
        manager.execute(stringTask),
        manager.execute(computeTask),
      ]);
      
      expect(results[0], equals('Processed: Hello'));
      expect(results[1], equals(120)); // 5! = 120
    });
    
    test('getStats returns correct statistics', () async {
      // Initial state
      var stats = manager.getStats();
      expect(stats.utilization, equals(0.0));
      expect(stats.totalIsolates, equals(2));
      
      // Start some tasks with longer duration
      final task1 = manager.execute(TestTask('Task1', delay: const Duration(milliseconds: 500)));
      final task2 = manager.execute(TestTask('Task2', delay: const Duration(milliseconds: 500)));
      final task3 = manager.execute(TestTask('Task3', delay: const Duration(milliseconds: 500)));
      
      // Wait a bit longer to ensure tasks have started
      await Future.delayed(const Duration(milliseconds: 100));
      stats = manager.getStats();
      
      // Should have 2 busy isolates and 1 pending task
      expect(stats.totalIsolates, equals(2));
      expect(stats.busyIsolates, greaterThanOrEqualTo(1)); // At least 1 should be busy
      expect(stats.busyIsolates, lessThanOrEqualTo(2)); // At most 2 can be busy
      expect(stats.pendingTasks, greaterThanOrEqualTo(1)); // At least 1 should be pending
      expect(stats.utilization, greaterThan(0.0)); // Should be utilizing some capacity
      
      // Wait for completion
      await Future.wait([task1, task2, task3]);
      
      // Check final stats - should be back to idle
      stats = manager.getStats();
      expect(stats.busyIsolates, equals(0));
      expect(stats.availableIsolates, equals(2));
      expect(stats.pendingTasks, equals(0));
      expect(stats.utilization, equals(0.0));
    });
    
    test('dispose cleans up resources', () async {
      // Create a separate manager for this test to avoid tearDown conflicts
      final testManager = IsolateManager(maxIsolates: 2);
      await testManager.initialize();
      
      // Verify initial state
      var stats = testManager.getStats();
      expect(stats.totalIsolates, equals(2));
      expect(stats.availableIsolates, equals(2));
      
      // Dispose manager
      testManager.dispose();
      
      // Should not be able to execute tasks after dispose
      expect(
        () => testManager.execute(TestTask('Test')),
        throwsStateError,
      );
    });
    
    test('execute throws after dispose', () async {
      manager.dispose();
      
      expect(
        () => manager.execute(TestTask('Test')),
        throwsStateError,
      );
    });
    
    test('isolate pool handles high load', () async {
      // Create many tasks
      final tasks = List.generate(
        20,
        (i) => TestTask('Task$i', delay: const Duration(milliseconds: 50)),
      );
      
      // Execute all tasks
      final futures = tasks.map((task) => manager.execute(task)).toList();
      
      // All should complete successfully
      final results = await Future.wait(futures);
      
      expect(results.length, equals(20));
      for (int i = 0; i < 20; i++) {
        expect(results[i], equals('Processed: Task$i'));
      }
    });
  });
}