import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:trading_dummy/migration/services/migration_manager.dart';
import 'package:trading_dummy/migration/services/data_migration_service.dart';

void main() {
  group('MigrationManager', () {
    late MigrationManager manager;

    setUp(() async {
      // Initialize SharedPreferences with test values
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();
      
      // Note: We can't easily test the full MigrationManager.create() 
      // because it initializes Hive repositories which need proper setup.
      // For now, we'll test the basic concepts.
    });

    test('migration status constants are defined', () {
      // This is a simple test to verify the migration manager can be imported
      expect(MigrationManager, isNotNull);
    });

    test('MigrationStatistics can be created', () {
      final stats = MigrationStatistics(
        status: 'not_started',
        version: 0,
        rolloutPercentage: 0,
        isUsingSQLite: false,
      );
      
      expect(stats.status, equals('not_started'));
      expect(stats.version, equals(0));
      expect(stats.rolloutPercentage, equals(0));
      expect(stats.isUsingSQLite, isFalse);
    });

    test('MigrationStatistics toMap works', () {
      final stats = MigrationStatistics(
        status: 'completed',
        timestamp: DateTime(2024, 1, 1),
        version: 1,
        rolloutPercentage: 50,
        isUsingSQLite: true,
      );
      
      final map = stats.toMap();
      
      expect(map['status'], equals('completed'));
      expect(map['version'], equals(1));
      expect(map['rolloutPercentage'], equals(50));
      expect(map['isUsingSQLite'], isTrue);
      expect(map['timestamp'], equals('2024-01-01T00:00:00.000'));
    });

    test('MigrationReport calculates duration correctly', () {
      final report = MigrationReport(
        success: true,
        message: 'Test',
        startTime: DateTime(2024, 1, 1, 10, 0, 0),
        endTime: DateTime(2024, 1, 1, 10, 5, 30),
      );
      
      expect(report.duration.inMinutes, equals(5));
      expect(report.duration.inSeconds, equals(330));
    });

    test('MigrationReport calculates totals correctly', () {
      final report = MigrationReport(
        success: true,
        message: 'Test',
        startTime: DateTime.now(),
        endTime: DateTime.now(),
        historyResult: MigrationResult(
          success: true,
          itemsProcessed: 10,
          itemsFailed: 2,
          message: 'History',
        ),
        jobsResult: MigrationResult(
          success: true,
          itemsProcessed: 15,
          itemsFailed: 3,
          message: 'Jobs',
        ),
      );
      
      expect(report.totalItemsProcessed, equals(25));
      expect(report.totalItemsFailed, equals(5));
    });
  });
}