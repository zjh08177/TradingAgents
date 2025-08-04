import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';

void main() {
  group('JobPriority', () {
    group('value', () {
      test('returns correct numeric values', () {
        expect(JobPriority.low.value, equals(0));
        expect(JobPriority.normal.value, equals(1));
        expect(JobPriority.high.value, equals(2));
        expect(JobPriority.critical.value, equals(3));
      });
    });
    
    group('displayName', () {
      test('returns correct display names', () {
        expect(JobPriority.low.displayName, equals('Low'));
        expect(JobPriority.normal.displayName, equals('Normal'));
        expect(JobPriority.high.displayName, equals('High'));
        expect(JobPriority.critical.displayName, equals('Critical'));
      });
    });
    
    group('compareTo', () {
      test('sorts higher priority first', () {
        expect(JobPriority.critical.compareTo(JobPriority.high), lessThan(0));
        expect(JobPriority.high.compareTo(JobPriority.normal), lessThan(0));
        expect(JobPriority.normal.compareTo(JobPriority.low), lessThan(0));
      });
      
      test('returns zero for same priority', () {
        expect(JobPriority.normal.compareTo(JobPriority.normal), equals(0));
        expect(JobPriority.high.compareTo(JobPriority.high), equals(0));
      });
      
      test('sorts lower priority last', () {
        expect(JobPriority.low.compareTo(JobPriority.normal), greaterThan(0));
        expect(JobPriority.normal.compareTo(JobPriority.high), greaterThan(0));
        expect(JobPriority.high.compareTo(JobPriority.critical), greaterThan(0));
      });
    });
    
    test('enum values are in correct order', () {
      expect(JobPriority.values.length, equals(4));
      expect(JobPriority.values[0], equals(JobPriority.low));
      expect(JobPriority.values[1], equals(JobPriority.normal));
      expect(JobPriority.values[2], equals(JobPriority.high));
      expect(JobPriority.values[3], equals(JobPriority.critical));
    });
    
    test('priority list sorts correctly', () {
      final priorities = [
        JobPriority.low,
        JobPriority.critical,
        JobPriority.normal,
        JobPriority.high,
      ];
      
      priorities.sort((a, b) => a.compareTo(b));
      
      expect(priorities, equals([
        JobPriority.critical,
        JobPriority.high,
        JobPriority.normal,
        JobPriority.low,
      ]));
    });
  });
}