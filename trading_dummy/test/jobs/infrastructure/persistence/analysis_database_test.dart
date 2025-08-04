import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_database.dart' as app_db;
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_record.dart';

void main() {
  late app_db.AnalysisDatabase database;
  late Directory tempDir;

  setUpAll(() async {
    // Initialize sqflite for testing
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  setUp(() async {
    // Create temporary directory for each test
    tempDir = await Directory.systemTemp.createTemp('analysis_db_test_');
    
    // Override database path for testing
    database = app_db.AnalysisDatabase();
    final testDbPath = '${tempDir.path}/test_analysis.db';
    database.setTestPath(testDbPath);
    
    // Ensure database is initialized and clean
    await database.isInitialized();
    await database.clearAllAnalyses();
  });

  tearDown(() async {
    // Clean up after each test
    await database.close();
    if (tempDir.existsSync()) {
      tempDir.deleteSync(recursive: true);
    }
  });

  group('AnalysisDatabase Setup', () {
    test('should initialize database successfully', () async {
      final isInitialized = await database.isInitialized();
      expect(isInitialized, isTrue);
    });

    test('should create database with correct schema', () async {
      // Verify table exists by attempting to query it
      final analyses = await database.getAllAnalyses();
      expect(analyses, isEmpty);
    });

    test('should get database path', () async {
      final path = await database.getDatabasePath();
      expect(path, isNotEmpty);
      expect(path, contains('analysis.db'));
    });
  });

  group('AnalysisRecord CRUD Operations', () {
    late AnalysisRecord testRecord;

    setUp(() {
      testRecord = AnalysisRecord(
        id: 'test-id-123',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        status: 'pending',
        createdAt: DateTime(2024, 1, 15, 10, 30),
        updatedAt: DateTime(2024, 1, 15, 10, 30),
      );
    });

    test('should save analysis record', () async {
      await database.saveAnalysis(testRecord);
      
      final retrieved = await database.getAnalysisById(testRecord.id);
      expect(retrieved, isNotNull);
      expect(retrieved!.id, equals(testRecord.id));
      expect(retrieved.ticker, equals(testRecord.ticker));
      expect(retrieved.tradeDate, equals(testRecord.tradeDate));
      expect(retrieved.status, equals(testRecord.status));
    });

    test('should handle REPLACE conflict when saving duplicate ID', () async {
      // Save original record
      await database.saveAnalysis(testRecord);
      
      // Save updated record with same ID
      final updatedRecord = testRecord.copyWith(
        ticker: 'GOOGL',
        updatedAt: DateTime(2024, 1, 15, 11, 30),
      );
      await database.saveAnalysis(updatedRecord);
      
      // Verify the record was replaced
      final retrieved = await database.getAnalysisById(testRecord.id);
      expect(retrieved!.ticker, equals('GOOGL'));
      expect(retrieved.updatedAt, equals(updatedRecord.updatedAt));
    });

    test('should retrieve analysis by ID', () async {
      await database.saveAnalysis(testRecord);
      
      final retrieved = await database.getAnalysisById(testRecord.id);
      expect(retrieved, equals(testRecord));
    });

    test('should return null for non-existent ID', () async {
      final retrieved = await database.getAnalysisById('non-existent');
      expect(retrieved, isNull);
    });

    test('should delete analysis record', () async {
      await database.saveAnalysis(testRecord);
      
      // Verify record exists
      var retrieved = await database.getAnalysisById(testRecord.id);
      expect(retrieved, isNotNull);
      
      // Delete record
      await database.deleteAnalysis(testRecord.id);
      
      // Verify record is deleted
      retrieved = await database.getAnalysisById(testRecord.id);
      expect(retrieved, isNull);
    });

    test('should throw exception when deleting non-existent record', () async {
      expect(
        () => database.deleteAnalysis('non-existent'),
        throwsA(isA<app_db.DatabaseException>()),
      );
    });
  });

  group('Status Update Operations', () {
    late AnalysisRecord testRecord;

    setUp(() async {
      testRecord = AnalysisRecord(
        id: 'test-id-456',
        runId: 'run-123',
        ticker: 'TSLA',
        tradeDate: '2024-01-16',
        status: 'pending',
        createdAt: DateTime(2024, 1, 16, 9, 0),
        updatedAt: DateTime(2024, 1, 16, 9, 0),
      );
      await database.saveAnalysis(testRecord);
    });

    test('should update status successfully', () async {
      final completedAt = DateTime(2024, 1, 16, 10, 0);
      
      await database.updateStatus(
        testRecord.runId!,
        status: 'success',
        result: '{"decision": "BUY", "confidence": 0.85}',
        completedAt: completedAt,
      );
      
      final updated = await database.getAnalysisByRunId(testRecord.runId!);
      expect(updated!.status, equals('success'));
      expect(updated.result, equals('{"decision": "BUY", "confidence": 0.85}'));
      expect(updated.completedAt, equals(completedAt));
      expect(updated.updatedAt.isAfter(testRecord.updatedAt), isTrue);
    });

    test('should update status with error', () async {
      const errorMessage = 'API request failed';
      
      await database.updateStatus(
        testRecord.runId!,
        status: 'error',
        error: errorMessage,
      );
      
      final updated = await database.getAnalysisByRunId(testRecord.runId!);
      expect(updated!.status, equals('error'));
      expect(updated.error, equals(errorMessage));
    });

    test('should throw exception when updating non-existent runId', () async {
      expect(
        () => database.updateStatus('non-existent-run', status: 'success'),
        throwsA(isA<app_db.DatabaseException>()),
      );
    });
  });

  group('Query Operations', () {
    late List<AnalysisRecord> testRecords;

    setUp(() async {
      testRecords = [
        AnalysisRecord(
          id: 'pending-1',
          runId: 'run-pending-1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          status: 'pending',
          createdAt: DateTime(2024, 1, 15, 9, 0),
          updatedAt: DateTime(2024, 1, 15, 9, 0),
        ),
        AnalysisRecord(
          id: 'running-1',
          runId: 'run-running-1',
          ticker: 'GOOGL',
          tradeDate: '2024-01-16',
          status: 'running',
          createdAt: DateTime(2024, 1, 16, 10, 0),
          updatedAt: DateTime(2024, 1, 16, 10, 0),
        ),
        AnalysisRecord(
          id: 'success-1',
          runId: 'run-success-1',
          ticker: 'TSLA',
          tradeDate: '2024-01-17',
          status: 'success',
          createdAt: DateTime(2024, 1, 17, 11, 0),
          updatedAt: DateTime(2024, 1, 17, 11, 0),
          completedAt: DateTime(2024, 1, 17, 11, 30),
          result: '{"decision": "SELL"}',
        ),
        AnalysisRecord(
          id: 'error-1',
          runId: 'run-error-1',
          ticker: 'AAPL',
          tradeDate: '2024-01-18',
          status: 'error',
          createdAt: DateTime(2024, 1, 18, 12, 0),
          updatedAt: DateTime(2024, 1, 18, 12, 0),
          error: 'Network timeout',
        ),
      ];

      for (final record in testRecords) {
        await database.saveAnalysis(record);
      }
    });

    test('should get all analyses ordered by creation date DESC', () async {
      final analyses = await database.getAllAnalyses();
      
      expect(analyses.length, equals(4));
      // Should be ordered by createdAt DESC (newest first)
      expect(analyses[0].id, equals('error-1'));
      expect(analyses[1].id, equals('success-1'));
      expect(analyses[2].id, equals('running-1'));
      expect(analyses[3].id, equals('pending-1'));
    });

    test('should get pending analyses only', () async {
      final pendingAnalyses = await database.getPendingAnalyses();
      
      expect(pendingAnalyses.length, equals(2));
      expect(pendingAnalyses.any((a) => a.status == 'pending'), isTrue);
      expect(pendingAnalyses.any((a) => a.status == 'running'), isTrue);
      expect(pendingAnalyses.any((a) => a.status == 'success'), isFalse);
      expect(pendingAnalyses.any((a) => a.status == 'error'), isFalse);
    });

    test('should get analyses by ticker', () async {
      final appleAnalyses = await database.getAnalysesByTicker('AAPL');
      
      expect(appleAnalyses.length, equals(2));
      expect(appleAnalyses.every((a) => a.ticker == 'AAPL'), isTrue);
    });

    test('should get analyses by status', () async {
      final successAnalyses = await database.getAnalysesByStatus('success');
      
      expect(successAnalyses.length, equals(1));
      expect(successAnalyses.first.status, equals('success'));
      expect(successAnalyses.first.result, isNotNull);
    });

    test('should get analysis by runId', () async {
      final analysis = await database.getAnalysisByRunId('run-success-1');
      
      expect(analysis, isNotNull);
      expect(analysis!.id, equals('success-1'));
      expect(analysis.status, equals('success'));
    });

    test('should return null for non-existent runId', () async {
      final analysis = await database.getAnalysisByRunId('non-existent');
      expect(analysis, isNull);
    });
  });

  group('Analytics and Maintenance Operations', () {
    setUp(() async {
      final testRecords = [
        AnalysisRecord(
          id: 'pending-1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          status: 'pending',
          createdAt: DateTime(2024, 1, 15),
          updatedAt: DateTime(2024, 1, 15),
        ),
        AnalysisRecord(
          id: 'running-1',
          ticker: 'GOOGL',
          tradeDate: '2024-01-16',
          status: 'running',
          createdAt: DateTime(2024, 1, 16),
          updatedAt: DateTime(2024, 1, 16),
        ),
        AnalysisRecord(
          id: 'success-1',
          ticker: 'TSLA',
          tradeDate: '2024-01-17',
          status: 'success',
          createdAt: DateTime(2024, 1, 17),
          updatedAt: DateTime(2024, 1, 17),
          completedAt: DateTime(2024, 1, 5), // Old completion date before cutoff
        ),
        AnalysisRecord(
          id: 'success-2',
          ticker: 'MSFT',
          tradeDate: '2024-01-18',
          status: 'success',
          createdAt: DateTime(2024, 1, 18),
          updatedAt: DateTime(2024, 1, 18),
          completedAt: DateTime(2024, 1, 20), // Recent completion date
        ),
      ];

      for (final record in testRecords) {
        await database.saveAnalysis(record);
      }
    });

    test('should get analysis count by status', () async {
      final counts = await database.getAnalysisCountByStatus();
      
      expect(counts['pending'], equals(1));
      expect(counts['running'], equals(1));
      expect(counts['success'], equals(2));
      expect(counts['error'], isNull); // No error records
    });

    test('should delete old completed analyses', () async {
      final cutoffDate = DateTime(2024, 1, 10);
      final deletedCount = await database.deleteCompletedAnalysesBefore(cutoffDate);
      
      expect(deletedCount, equals(1)); // Only success-1 should be deleted (completed before cutoff)
      
      final remaining = await database.getAllAnalyses();
      expect(remaining.length, equals(3));
      expect(remaining.any((a) => a.id == 'success-1'), isFalse);
      expect(remaining.any((a) => a.id == 'success-2'), isTrue);
    });

    test('should clear all analyses', () async {
      await database.clearAllAnalyses();
      
      final analyses = await database.getAllAnalyses();
      expect(analyses, isEmpty);
    });
  });

  group('Error Handling', () {
    test('should handle database exceptions gracefully', () async {
      // Test that database can recover from closed state
      await database.close();
      
      // Database should be able to reinitialize and save successfully
      await database.saveAnalysis(AnalysisRecord(
        id: 'test-recovery',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        status: 'pending',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      ));
      
      // Verify the record was saved successfully
      final retrieved = await database.getAnalysisById('test-recovery');
      expect(retrieved, isNotNull);
      expect(retrieved!.ticker, equals('AAPL'));
    });

    test('DatabaseException should have meaningful message', () {
      final exception = app_db.DatabaseException('Test error message');
      expect(exception.toString(), contains('Test error message'));
    });
  });

  group('AnalysisRecord Model Tests', () {
    late AnalysisRecord testRecord;

    setUp(() {
      testRecord = AnalysisRecord(
        id: 'model-test',
        runId: 'run-model-test',
        threadId: 'thread-123',
        ticker: 'NVDA',
        tradeDate: '2024-01-20',
        status: 'success',
        createdAt: DateTime(2024, 1, 20, 9, 0),
        updatedAt: DateTime(2024, 1, 20, 10, 0),
        completedAt: DateTime(2024, 1, 20, 10, 30),
        result: '{"decision": "HOLD", "confidence": 0.75}',
      );
    });

    test('should convert to and from map correctly', () {
      final map = testRecord.toMap();
      final reconstructed = AnalysisRecord.fromMap(map);
      
      expect(reconstructed, equals(testRecord));
    });

    test('should handle null values in fromMap', () {
      final mapWithNulls = {
        'id': 'test-nulls',
        'runId': null,
        'threadId': null,
        'ticker': 'AAPL',
        'tradeDate': '2024-01-15',
        'status': 'pending',
        'createdAt': DateTime(2024, 1, 15).millisecondsSinceEpoch,
        'updatedAt': DateTime(2024, 1, 15).millisecondsSinceEpoch,
        'completedAt': null,
        'result': null,
        'error': null,
      };

      final record = AnalysisRecord.fromMap(mapWithNulls);
      expect(record.runId, isNull);
      expect(record.threadId, isNull);
      expect(record.completedAt, isNull);
      expect(record.result, isNull);
      expect(record.error, isNull);
    });

    test('should create copy with updated fields', () {
      final updated = testRecord.copyWith(
        status: 'error',
        error: 'Test error',
        completedAt: DateTime(2024, 1, 20, 11, 0),
      );

      expect(updated.id, equals(testRecord.id)); // Unchanged
      expect(updated.ticker, equals(testRecord.ticker)); // Unchanged
      expect(updated.status, equals('error')); // Changed
      expect(updated.error, equals('Test error')); // Changed
      expect(updated.completedAt, equals(DateTime(2024, 1, 20, 11, 0))); // Changed
    });

    test('should correctly identify record states', () {
      expect(testRecord.isComplete, isTrue);
      expect(testRecord.isRunning, isFalse);
      expect(testRecord.isPending, isFalse);
      expect(testRecord.hasError, isFalse);

      final pendingRecord = testRecord.copyWith(status: 'pending');
      expect(pendingRecord.isPending, isTrue);
      expect(pendingRecord.isComplete, isFalse);

      final runningRecord = testRecord.copyWith(status: 'running');
      expect(runningRecord.isRunning, isTrue);
      expect(runningRecord.isComplete, isFalse);

      final errorRecord = testRecord.copyWith(status: 'error');
      expect(errorRecord.hasError, isTrue);
      expect(errorRecord.isComplete, isTrue);
    });

    test('should have proper toString representation', () {
      final string = testRecord.toString();
      expect(string, contains('NVDA'));
      expect(string, contains('2024-01-20'));
      expect(string, contains('success'));
    });

    test('should implement Equatable correctly', () {
      final identical = AnalysisRecord(
        id: testRecord.id,
        runId: testRecord.runId,
        threadId: testRecord.threadId,
        ticker: testRecord.ticker,
        tradeDate: testRecord.tradeDate,
        status: testRecord.status,
        createdAt: testRecord.createdAt,
        updatedAt: testRecord.updatedAt,
        completedAt: testRecord.completedAt,
        result: testRecord.result,
        error: testRecord.error,
      );

      final different = testRecord.copyWith(ticker: 'DIFFERENT');

      expect(testRecord, equals(identical));
      expect(testRecord, isNot(equals(different)));
    });
  });
}