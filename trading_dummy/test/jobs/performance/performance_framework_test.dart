import 'package:flutter_test/flutter_test.dart';
import 'performance_test_framework.dart';

/// Test the performance testing framework itself
void main() {
  group('Performance Test Framework', () {
    late PerformanceTestFramework framework;

    setUp(() async {
      framework = PerformanceTestFramework();
      await framework.initialize();
    });

    tearDown(() async {
      await framework.dispose();
    });

    test('initializes successfully', () async {
      // Framework should initialize without errors
      expect(framework, isNotNull);
    });

    test('runs benchmark suite', () async {
      // Run a basic benchmark to verify framework functionality
      final results = await framework.runBenchmarkSuite();
      
      // Verify results structure
      expect(results, isNotNull);
      expect(results.repositoryResults, isNotNull);
      expect(results.queueResults, isNotNull);
      expect(results.retryResults, isNotNull);
      expect(results.loadTestResults, isNotNull);
      expect(results.memoryResults, isNotNull);
      
      // Generate and verify report
      final report = results.generateReport();
      expect(report, isNotEmpty);
      expect(report, contains('PERFORMANCE BENCHMARK RESULTS'));
    });
  });
}