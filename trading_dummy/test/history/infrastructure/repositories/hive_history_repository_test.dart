import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';
import 'package:trading_dummy/history/infrastructure/repositories/hive_history_repository.dart';
import 'package:trading_dummy/history/infrastructure/models/hive_history_entry.dart';
import 'package:trading_dummy/history/infrastructure/models/hive_analysis_details.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';
import 'package:trading_dummy/history/domain/value_objects/analysis_details.dart';
import 'dart:io';
import 'package:path/path.dart' as path;

void main() {
  group('HiveHistoryRepository', () {
    late HiveHistoryRepository repository;
    final testEntry = HistoryEntry(
      id: 'test-id-123',
      ticker: 'AAPL',
      tradeDate: '2024-01-15',
      timestamp: DateTime(2024, 1, 15, 10, 30),
      finalDecision: 'BUY',
      confidence: 0.85,
      summary: 'Strong buy signal',
      details: const AnalysisDetails(
        marketAnalysis: 'Positive market trends',
        fundamentals: 'Strong earnings',
        sentiment: 'Bullish sentiment',
      ),
    );

    setUpAll(() async {
      // Initialize Hive for testing with a temporary directory
      final tempDir = await Directory.systemTemp.createTemp('hive_test_');
      Hive.init(tempDir.path);
      
      // Register adapters
      if (!Hive.isAdapterRegistered(0)) {
        Hive.registerAdapter(HiveHistoryEntryAdapter());
      }
      if (!Hive.isAdapterRegistered(1)) {
        Hive.registerAdapter(HiveAnalysisDetailsAdapter());
      }
      
      // Open test box
      await HiveHistoryRepository.openBox();
    });

    setUp(() async {
      repository = HiveHistoryRepository();
      // Clear the box before each test
      await repository.clear();
    });

    tearDownAll(() async {
      await HiveHistoryRepository.closeBox();
      await Hive.close();
    });

    test('save and retrieve entry by id', () async {
      await repository.save(testEntry);
      
      final retrieved = await repository.getById(testEntry.id);
      
      expect(retrieved, isNotNull);
      expect(retrieved!.id, equals(testEntry.id));
      expect(retrieved.ticker, equals(testEntry.ticker));
      expect(retrieved.finalDecision, equals(testEntry.finalDecision));
      expect(retrieved.confidence, equals(testEntry.confidence));
    });

    test('get all entries returns sorted list', () async {
      final entry1 = HistoryEntry(
        id: '1',
        ticker: 'AAPL',
        tradeDate: '2024-01-10',
        timestamp: DateTime(2024, 1, 10),
        finalDecision: 'BUY',
        summary: 'Entry 1',
        details: const AnalysisDetails(),
      );
      
      final entry2 = HistoryEntry(
        id: '2',
        ticker: 'GOOGL',
        tradeDate: '2024-01-15',
        timestamp: DateTime(2024, 1, 15),
        finalDecision: 'SELL',
        summary: 'Entry 2',
        details: const AnalysisDetails(),
      );
      
      final entry3 = HistoryEntry(
        id: '3',
        ticker: 'MSFT',
        tradeDate: '2024-01-12',
        timestamp: DateTime(2024, 1, 12),
        finalDecision: 'HOLD',
        summary: 'Entry 3',
        details: const AnalysisDetails(),
      );
      
      await repository.save(entry1);
      await repository.save(entry2);
      await repository.save(entry3);
      
      final all = await repository.getAll();
      
      expect(all.length, equals(3));
      // Should be sorted by timestamp descending (newest first)
      expect(all[0].id, equals('2'));
      expect(all[1].id, equals('3'));
      expect(all[2].id, equals('1'));
    });

    test('get by ticker returns filtered list', () async {
      final appleEntry1 = HistoryEntry(
        id: '1',
        ticker: 'AAPL',
        tradeDate: '2024-01-10',
        timestamp: DateTime(2024, 1, 10),
        finalDecision: 'BUY',
        summary: 'Apple 1',
        details: const AnalysisDetails(),
      );
      
      final googleEntry = HistoryEntry(
        id: '2',
        ticker: 'GOOGL',
        tradeDate: '2024-01-11',
        timestamp: DateTime(2024, 1, 11),
        finalDecision: 'SELL',
        summary: 'Google',
        details: const AnalysisDetails(),
      );
      
      final appleEntry2 = HistoryEntry(
        id: '3',
        ticker: 'AAPL',
        tradeDate: '2024-01-12',
        timestamp: DateTime(2024, 1, 12),
        finalDecision: 'HOLD',
        summary: 'Apple 2',
        details: const AnalysisDetails(),
      );
      
      await repository.save(appleEntry1);
      await repository.save(googleEntry);
      await repository.save(appleEntry2);
      
      final appleEntries = await repository.getByTicker('AAPL');
      
      expect(appleEntries.length, equals(2));
      expect(appleEntries.every((e) => e.ticker == 'AAPL'), isTrue);
      // Should be sorted by timestamp descending
      expect(appleEntries[0].id, equals('3'));
      expect(appleEntries[1].id, equals('1'));
    });

    test('delete removes entry', () async {
      await repository.save(testEntry);
      
      // Verify it exists
      var retrieved = await repository.getById(testEntry.id);
      expect(retrieved, isNotNull);
      
      // Delete it
      await repository.delete(testEntry.id);
      
      // Verify it's gone
      retrieved = await repository.getById(testEntry.id);
      expect(retrieved, isNull);
    });

    test('clear removes all entries', () async {
      // Add multiple entries
      for (int i = 0; i < 5; i++) {
        await repository.save(HistoryEntry(
          id: 'id-$i',
          ticker: 'TEST$i',
          tradeDate: '2024-01-$i',
          timestamp: DateTime(2024, 1, i + 1),
          finalDecision: 'BUY',
          summary: 'Test $i',
          details: const AnalysisDetails(),
        ));
      }
      
      // Verify they exist
      var all = await repository.getAll();
      expect(all.length, equals(5));
      
      // Clear all
      await repository.clear();
      
      // Verify they're gone
      all = await repository.getAll();
      expect(all, isEmpty);
    });

    test('handles complex analysis details', () async {
      final complexEntry = HistoryEntry(
        id: 'complex-id',
        ticker: 'TSLA',
        tradeDate: '2024-01-20',
        timestamp: DateTime.now(),
        finalDecision: 'BUY',
        confidence: 0.92,
        summary: 'Complex analysis with all details',
        details: const AnalysisDetails(
          marketAnalysis: 'Strong upward trend in the technology sector',
          fundamentals: 'P/E ratio of 25, revenue growth of 15%',
          sentiment: 'Social media sentiment is overwhelmingly positive',
          newsAnalysis: 'Recent product launch receiving positive coverage',
          bullArgument: 'Innovation leader with strong growth potential',
          bearArgument: 'Valuation concerns and increasing competition',
          investmentPlan: 'Long-term hold with 20% portfolio allocation',
          rawData: {
            'price': 150.25,
            'volume': 1000000,
            'indicators': {
              'rsi': 65,
              'macd': 'bullish',
            },
          },
        ),
      );
      
      await repository.save(complexEntry);
      final retrieved = await repository.getById('complex-id');
      
      expect(retrieved, isNotNull);
      expect(retrieved!.details.marketAnalysis, equals(complexEntry.details.marketAnalysis));
      expect(retrieved.details.fundamentals, equals(complexEntry.details.fundamentals));
      expect(retrieved.details.sentiment, equals(complexEntry.details.sentiment));
      expect(retrieved.details.newsAnalysis, equals(complexEntry.details.newsAnalysis));
      expect(retrieved.details.bullArgument, equals(complexEntry.details.bullArgument));
      expect(retrieved.details.bearArgument, equals(complexEntry.details.bearArgument));
      expect(retrieved.details.investmentPlan, equals(complexEntry.details.investmentPlan));
      expect(retrieved.details.rawData, equals(complexEntry.details.rawData));
    });

    test('handles error entries', () async {
      final errorEntry = HistoryEntry(
        id: 'error-id',
        ticker: 'ERROR',
        tradeDate: '2024-01-15',
        timestamp: DateTime.now(),
        finalDecision: 'ERROR',
        summary: 'Analysis failed',
        details: const AnalysisDetails(),
        isError: true,
        errorMessage: 'Network timeout occurred',
      );
      
      await repository.save(errorEntry);
      final retrieved = await repository.getById('error-id');
      
      expect(retrieved, isNotNull);
      expect(retrieved!.isError, isTrue);
      expect(retrieved.errorMessage, equals('Network timeout occurred'));
      expect(retrieved.finalDecision, equals('ERROR'));
    });

    test('box operations are available', () {
      expect(HiveHistoryRepository.isBoxOpen(), isTrue);
    });
  });
}