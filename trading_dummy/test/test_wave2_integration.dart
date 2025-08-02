import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/models/final_report.dart';
import 'package:trading_dummy/history/infrastructure/mappers/report_mapper.dart';
import 'package:trading_dummy/history/infrastructure/repositories/mock_history_repository.dart';

void main() {
  group('Wave 2 Integration Tests', () {
    late ReportMapper mapper;
    late MockHistoryRepository repository;

    setUp(() {
      mapper = ReportMapper();
      repository = MockHistoryRepository();
    });

    test('ReportMapper extracts BUY decision correctly', () async {
      final report = FinalReport(
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        content: 'Final trading decision: BUY with 85% confidence',
        timestamp: DateTime.now(),
      );
      
      final entry = mapper.map(report);
      
      expect(entry.finalDecision, equals('BUY'));
      expect(entry.confidence, equals(0.85));
      expect(entry.isError, isFalse);
    });

    test('ReportMapper handles error reports', () async {
      final report = FinalReport(
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        content: 'Network error occurred',
        timestamp: DateTime.now(),
        isError: true,
      );
      
      final entry = mapper.map(report);
      
      expect(entry.isError, isTrue);
      expect(entry.finalDecision, equals('ERROR'));
      expect(entry.errorMessage, equals('Network error occurred'));
    });

    test('MockHistoryRepository stores and retrieves entries', () async {
      final report = FinalReport(
        ticker: 'TEST',
        tradeDate: '2024-01-16',
        content: 'Trading decision: SELL',
        timestamp: DateTime.now(),
      );
      
      final entry = mapper.map(report);
      await repository.save(entry);
      
      final retrieved = await repository.getById(entry.id);
      expect(retrieved, isNotNull);
      expect(retrieved!.ticker, equals('TEST'));
      expect(retrieved.finalDecision, equals('SELL'));
    });

    test('MockHistoryRepository returns sorted entries', () async {
      final entries = await repository.getAll();
      
      expect(entries.isNotEmpty, isTrue);
      
      // Check if sorted by timestamp (newest first)
      for (int i = 0; i < entries.length - 1; i++) {
        expect(entries[i].timestamp.isAfter(entries[i + 1].timestamp), isTrue);
      }
    });

    test('ReportMapper extracts confidence variations', () {
      final testCases = [
        ('confidence: 75%', 0.75),
        ('85% confidence', 0.85),
        ('confidence: 0.9', 0.9),
        ('certainty: 60%', 0.6),
      ];

      for (final testCase in testCases) {
        final report = FinalReport(
          ticker: 'TEST',
          tradeDate: '2024-01-16',
          content: 'Decision: BUY with ${testCase.$1}',
          timestamp: DateTime.now(),
        );
        
        final entry = mapper.map(report);
        expect(entry.confidence, equals(testCase.$2), 
          reason: 'Failed to extract confidence from "${testCase.$1}"');
      }
    });

    test('ReportMapper generates appropriate summaries', () {
      final report = FinalReport(
        ticker: 'TSLA',
        tradeDate: '2024-01-16',
        content: '''
Summary: Strong buy signal based on technical breakout and positive momentum
Decision: BUY
''',
        timestamp: DateTime.now(),
      );
      
      final entry = mapper.map(report);
      expect(entry.summary, contains('Strong buy signal'));
      expect(entry.summary.length, lessThanOrEqualTo(150));
    });

    test('MockHistoryRepository filters by ticker correctly', () async {
      // The repository comes pre-populated with mock data
      final appleEntries = await repository.getByTicker('AAPL');
      final googleEntries = await repository.getByTicker('GOOGL');
      final teslaEntries = await repository.getByTicker('TSLA');
      
      expect(appleEntries.length, equals(1));
      expect(googleEntries.length, equals(1));
      expect(teslaEntries.length, equals(0)); // No TSLA in initial mock data
      
      expect(appleEntries.first.ticker, equals('AAPL'));
      expect(googleEntries.first.ticker, equals('GOOGL'));
    });
  });
}