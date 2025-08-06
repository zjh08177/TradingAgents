import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:trading_dummy/history/infrastructure/repositories/sqlite_history_repository.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';
import 'package:trading_dummy/history/domain/value_objects/analysis_details.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_database.dart';
import 'dart:io';
import 'package:path/path.dart' as path;

void main() {
  late SQLiteHistoryRepository repository;
  late AnalysisDatabase database;
  late String testDbPath;

  setUpAll(() {
    // Initialize sqflite_ffi for testing
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  setUp(() async {
    // Create a temporary test database
    final tempDir = await Directory.systemTemp.createTemp('sqlite_history_test_');
    testDbPath = path.join(tempDir.path, 'test.db');
    
    // Initialize database with test path
    database = AnalysisDatabase();
    database.setTestPath(testDbPath);
    
    // Create repository
    repository = SQLiteHistoryRepository();
  });

  tearDown(() async {
    // Close database and clean up
    await database.close();
    
    // Delete test database file
    if (await File(testDbPath).exists()) {
      await File(testDbPath).delete();
    }
  });

  group('SQLiteHistoryRepository', () {
    test('should save and retrieve a history entry', () async {
      // Arrange
      final entry = _createTestEntry('AAPL', 'BUY');
      
      // Act
      await repository.save(entry);
      final retrieved = await repository.getById(entry.id);
      
      // Assert
      expect(retrieved, isNotNull);
      expect(retrieved!.id, equals(entry.id));
      expect(retrieved.ticker, equals(entry.ticker));
      expect(retrieved.finalDecision, equals(entry.finalDecision));
      expect(retrieved.confidence, equals(entry.confidence));
      expect(retrieved.summary, equals(entry.summary));
      expect(retrieved.details.marketAnalysis, equals(entry.details.marketAnalysis));
    });

    test('should retrieve all history entries sorted by timestamp', () async {
      // Arrange
      final now = DateTime.now();
      final entry1 = _createTestEntry('AAPL', 'BUY', 
        id: 'entry1',
        timestamp: now.subtract(const Duration(hours: 2)));
      final entry2 = _createTestEntry('GOOGL', 'SELL',
        id: 'entry2',
        timestamp: now.subtract(const Duration(hours: 1)));
      final entry3 = _createTestEntry('MSFT', 'HOLD',
        id: 'entry3',
        timestamp: now);
      
      // Act
      await repository.save(entry1);
      await repository.save(entry2);
      await repository.save(entry3);
      final allEntries = await repository.getAll();
      
      // Assert
      expect(allEntries.length, equals(3));
      // Should be sorted by timestamp DESC (newest first)
      expect(allEntries[0].ticker, equals('MSFT'));
      expect(allEntries[1].ticker, equals('GOOGL'));
      expect(allEntries[2].ticker, equals('AAPL'));
    });

    test('should retrieve entries by ticker', () async {
      // Arrange
      final appleEntry1 = _createTestEntry('AAPL', 'BUY', id: 'apple1');
      final appleEntry2 = _createTestEntry('AAPL', 'SELL', id: 'apple2');
      final googleEntry = _createTestEntry('GOOGL', 'HOLD', id: 'google1');
      
      // Act
      await repository.save(appleEntry1);
      await repository.save(appleEntry2);
      await repository.save(googleEntry);
      final appleEntries = await repository.getByTicker('AAPL');
      
      // Assert
      expect(appleEntries.length, equals(2));
      expect(appleEntries.every((e) => e.ticker == 'AAPL'), isTrue);
    });

    test('should update an existing entry', () async {
      // Arrange
      final entry = _createTestEntry('AAPL', 'BUY');
      await repository.save(entry);
      
      // Create updated entry with same ID
      final updatedEntry = HistoryEntry(
        id: entry.id,
        ticker: entry.ticker,
        tradeDate: entry.tradeDate,
        timestamp: entry.timestamp,
        finalDecision: 'SELL', // Changed
        confidence: 0.95, // Changed
        summary: 'Updated summary',
        details: entry.details,
        isError: false,
      );
      
      // Act
      await repository.save(updatedEntry);
      final retrieved = await repository.getById(entry.id);
      
      // Assert
      expect(retrieved!.finalDecision, equals('SELL'));
      expect(retrieved.confidence, equals(0.95));
      expect(retrieved.summary, equals('Updated summary'));
    });

    test('should delete a history entry', () async {
      // Arrange
      final entry = _createTestEntry('AAPL', 'BUY');
      await repository.save(entry);
      
      // Act
      await repository.delete(entry.id);
      final retrieved = await repository.getById(entry.id);
      
      // Assert
      expect(retrieved, isNull);
    });

    test('should clear all history entries', () async {
      // Arrange
      await repository.save(_createTestEntry('AAPL', 'BUY'));
      await repository.save(_createTestEntry('GOOGL', 'SELL'));
      await repository.save(_createTestEntry('MSFT', 'HOLD'));
      
      // Act
      await repository.clear();
      final allEntries = await repository.getAll();
      
      // Assert
      expect(allEntries, isEmpty);
    });

    test('should handle entries with error state', () async {
      // Arrange
      final errorEntry = HistoryEntry(
        id: 'error-entry',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        timestamp: DateTime.now(),
        finalDecision: 'ERROR',
        confidence: null,
        summary: 'Analysis failed',
        details: AnalysisDetails(
          marketAnalysis: '',
          fundamentals: '',
          sentiment: '',
          newsAnalysis: '',
          bullArgument: '',
          bearArgument: '',
          investmentPlan: '',
        ),
        isError: true,
        errorMessage: 'Network timeout',
      );
      
      // Act
      await repository.save(errorEntry);
      final retrieved = await repository.getById(errorEntry.id);
      
      // Assert
      expect(retrieved!.isError, isTrue);
      expect(retrieved.errorMessage, equals('Network timeout'));
    });

    test('should handle entries with raw data', () async {
      // Arrange
      final rawData = {
        'technical_indicators': {
          'RSI': 65.5,
          'MACD': 0.25,
        },
        'volume': 1000000,
      };
      
      final entry = HistoryEntry(
        id: 'raw-data-entry',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        timestamp: DateTime.now(),
        finalDecision: 'BUY',
        confidence: 0.85,
        summary: 'Test with raw data',
        details: AnalysisDetails(
          marketAnalysis: 'Market analysis',
          fundamentals: 'Fundamentals',
          sentiment: 'Sentiment',
          newsAnalysis: 'News',
          bullArgument: 'Bull',
          bearArgument: 'Bear',
          investmentPlan: 'Plan',
          rawData: rawData,
        ),
      );
      
      // Act
      await repository.save(entry);
      final retrieved = await repository.getById(entry.id);
      
      // Assert
      expect(retrieved!.details.rawData, isNotNull);
      expect(retrieved.details.rawData!['technical_indicators']['RSI'], equals(65.5));
      expect(retrieved.details.rawData!['volume'], equals(1000000));
    });

    test('should return null for non-existent entry', () async {
      // Act
      final result = await repository.getById('non-existent-id');
      
      // Assert
      expect(result, isNull);
    });

    test('should return empty list when no entries for ticker', () async {
      // Act
      final result = await repository.getByTicker('UNKNOWN');
      
      // Assert
      expect(result, isEmpty);
    });
  });
}

// Helper function to create test entries
HistoryEntry _createTestEntry(
  String ticker, 
  String decision, {
  String? id,
  DateTime? timestamp,
}) {
  return HistoryEntry(
    id: id ?? 'test-${DateTime.now().millisecondsSinceEpoch}',
    ticker: ticker,
    tradeDate: '2024-01-15',
    timestamp: timestamp ?? DateTime.now(),
    finalDecision: decision,
    confidence: 0.85,
    summary: 'Test analysis for $ticker',
    details: AnalysisDetails(
      marketAnalysis: 'Market is bullish',
      fundamentals: 'Strong fundamentals',
      sentiment: 'Positive sentiment',
      newsAnalysis: 'Good news coverage',
      bullArgument: 'Strong buy signals',
      bearArgument: 'Minor concerns',
      investmentPlan: 'Long-term hold',
    ),
    isError: false,
  );
}