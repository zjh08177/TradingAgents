import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';

void main() {
  group('JobStatus', () {
    group('isTerminal', () {
      test('returns true for terminal states', () {
        expect(JobStatus.completed.isTerminal, isTrue);
        expect(JobStatus.failed.isTerminal, isTrue);
        expect(JobStatus.cancelled.isTerminal, isTrue);
      });
      
      test('returns false for non-terminal states', () {
        expect(JobStatus.pending.isTerminal, isFalse);
        expect(JobStatus.queued.isTerminal, isFalse);
        expect(JobStatus.running.isTerminal, isFalse);
      });
    });
    
    group('isActive', () {
      test('returns true for active states', () {
        expect(JobStatus.pending.isActive, isTrue);
        expect(JobStatus.queued.isActive, isTrue);
        expect(JobStatus.running.isActive, isTrue);
      });
      
      test('returns false for inactive states', () {
        expect(JobStatus.completed.isActive, isFalse);
        expect(JobStatus.failed.isActive, isFalse);
        expect(JobStatus.cancelled.isActive, isFalse);
      });
    });
    
    group('displayName', () {
      test('returns correct display names', () {
        expect(JobStatus.pending.displayName, equals('Pending'));
        expect(JobStatus.queued.displayName, equals('Queued'));
        expect(JobStatus.running.displayName, equals('Running'));
        expect(JobStatus.completed.displayName, equals('Completed'));
        expect(JobStatus.failed.displayName, equals('Failed'));
        expect(JobStatus.cancelled.displayName, equals('Cancelled'));
      });
    });
    
    test('enum values are in correct order', () {
      expect(JobStatus.values.length, equals(6));
      expect(JobStatus.values[0], equals(JobStatus.pending));
      expect(JobStatus.values[1], equals(JobStatus.queued));
      expect(JobStatus.values[2], equals(JobStatus.running));
      expect(JobStatus.values[3], equals(JobStatus.completed));
      expect(JobStatus.values[4], equals(JobStatus.failed));
      expect(JobStatus.values[5], equals(JobStatus.cancelled));
    });
  });
}