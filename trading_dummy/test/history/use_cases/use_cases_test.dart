import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/models/final_report.dart';
import 'package:trading_dummy/history/application/use_cases/save_history_use_case.dart';
import 'package:trading_dummy/history/application/use_cases/get_history_use_case.dart';
import 'package:trading_dummy/history/application/use_cases/delete_history_use_case.dart';
import 'package:trading_dummy/history/infrastructure/repositories/mock_history_repository.dart';
import 'package:trading_dummy/history/infrastructure/mappers/report_mapper.dart';

void main() {
  group('SaveHistoryUseCase Tests', () {
    late SaveHistoryUseCase saveUseCase;
    late MockHistoryRepository repository;
    late ReportMapper mapper;

    setUp(() {
      repository = MockHistoryRepository();
      mapper = ReportMapper();
      saveUseCase = SaveHistoryUseCase(
        repository: repository,
        mapper: mapper,
      );
    });

    test('execute saves a report successfully', () async {
      final report = FinalReport(
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        content: 'Trading decision: BUY with 80% confidence',
        timestamp: DateTime.now(),
      );

      final entry = await saveUseCase.execute(report);

      expect(entry.ticker, equals('AAPL'));
      expect(entry.finalDecision, equals('BUY'));
      expect(entry.confidence, equals(0.8));
      expect(entry.isError, isFalse);

      // Verify it was saved
      final saved = await repository.getById(entry.id);
      expect(saved, isNotNull);
      expect(saved!.id, equals(entry.id));
    });

    test('execute handles error reports', () async {
      final errorReport = FinalReport(
        ticker: 'ERROR',
        tradeDate: '2024-01-20',
        content: 'Network error',
        timestamp: DateTime.now(),
        isError: true,
      );

      final entry = await saveUseCase.execute(errorReport);

      expect(entry.isError, isTrue);
      expect(entry.finalDecision, equals('ERROR'));
    });

    test('executeBatch saves multiple reports', () async {
      final reports = [
        FinalReport(
          ticker: 'AAPL',
          tradeDate: '2024-01-20',
          content: 'BUY recommendation',
          timestamp: DateTime.now(),
        ),
        FinalReport(
          ticker: 'GOOGL',
          tradeDate: '2024-01-20',
          content: 'SELL recommendation',
          timestamp: DateTime.now(),
        ),
      ];

      final entries = await saveUseCase.executeBatch(reports);

      expect(entries.length, equals(2));
      expect(entries[0].ticker, equals('AAPL'));
      expect(entries[1].ticker, equals('GOOGL'));
    });
  });

  group('GetHistoryUseCase Tests', () {
    late GetHistoryUseCase getUseCase;
    late MockHistoryRepository repository;

    setUp(() {
      repository = MockHistoryRepository();
      getUseCase = GetHistoryUseCase(repository: repository);
    });

    test('getAll returns all entries sorted by newest first', () async {
      final entries = await getUseCase.getAll();

      expect(entries.isNotEmpty, isTrue);
      expect(entries.length, greaterThanOrEqualTo(3)); // Mock data has 3 entries

      // Check sorting
      for (int i = 0; i < entries.length - 1; i++) {
        expect(
          entries[i].timestamp.isAfter(entries[i + 1].timestamp),
          isTrue,
        );
      }
    });

    test('getById returns specific entry', () async {
      final entry = await getUseCase.getById('mock-1');

      expect(entry, isNotNull);
      expect(entry!.ticker, equals('AAPL'));
    });

    test('getById returns null for non-existent entry', () async {
      final entry = await getUseCase.getById('non-existent');

      expect(entry, isNull);
    });

    test('getByTicker returns entries for specific ticker', () async {
      final entries = await getUseCase.getByTicker('AAPL');

      expect(entries.isNotEmpty, isTrue);
      expect(entries.every((e) => e.ticker == 'AAPL'), isTrue);
    });

    test('getMostRecentForTicker returns latest entry', () async {
      final entry = await getUseCase.getMostRecentForTicker('AAPL');

      expect(entry, isNotNull);
      expect(entry!.ticker, equals('AAPL'));
    });

    test('getRecent returns limited entries', () async {
      final entries = await getUseCase.getRecent(limit: 2);

      expect(entries.length, lessThanOrEqualTo(2));
    });

    test('getUniqueTickers returns sorted ticker list', () async {
      final tickers = await getUseCase.getUniqueTickers();

      expect(tickers.isNotEmpty, isTrue);
      expect(tickers, contains('AAPL'));
      expect(tickers, contains('GOOGL'));
      expect(tickers, contains('MSFT'));

      // Check sorting
      final sorted = List.from(tickers)..sort();
      expect(tickers, equals(sorted));
    });

    test('getStatistics returns correct counts', () async {
      final stats = await getUseCase.getStatistics();

      expect(stats.totalEntries, greaterThanOrEqualTo(3));
      expect(stats.buyDecisions, greaterThanOrEqualTo(2)); // AAPL and MSFT
      expect(stats.holdDecisions, greaterThanOrEqualTo(1)); // GOOGL
      expect(stats.uniqueTickers, greaterThanOrEqualTo(3));
    });

    test('getByDateRange filters correctly', () async {
      final now = DateTime.now();
      final entries = await getUseCase.getByDateRange(
        startDate: now.subtract(const Duration(days: 5)),
        endDate: now,
      );

      expect(entries.isNotEmpty, isTrue);
    });

    test('throws exception for invalid date range', () async {
      final now = DateTime.now();
      
      expect(
        () => getUseCase.getByDateRange(
          startDate: now,
          endDate: now.subtract(const Duration(days: 1)),
        ),
        throwsA(isA<GetHistoryException>()),
      );
    });
  });

  group('DeleteHistoryUseCase Tests', () {
    late DeleteHistoryUseCase deleteUseCase;
    late MockHistoryRepository repository;
    late SaveHistoryUseCase saveUseCase;

    setUp(() {
      repository = MockHistoryRepository();
      deleteUseCase = DeleteHistoryUseCase(repository: repository);
      saveUseCase = SaveHistoryUseCase(
        repository: repository,
        mapper: ReportMapper(),
      );
    });

    test('deleteById removes existing entry', () async {
      // Add a new entry
      final report = FinalReport(
        ticker: 'TEST',
        tradeDate: '2024-01-20',
        content: 'Test entry for deletion',
        timestamp: DateTime.now(),
      );
      final saved = await saveUseCase.execute(report);

      // Delete it
      final result = await deleteUseCase.deleteById(saved.id);

      expect(result, isTrue);

      // Verify it's gone
      final deleted = await repository.getById(saved.id);
      expect(deleted, isNull);
    });

    test('deleteById returns false for non-existent entry', () async {
      final result = await deleteUseCase.deleteById('non-existent');

      expect(result, isFalse);
    });

    test('deleteMultiple handles mixed results', () async {
      // Add test entries
      final report = FinalReport(
        ticker: 'DELETE_TEST',
        tradeDate: '2024-01-20',
        content: 'Test',
        timestamp: DateTime.now(),
      );
      final saved = await saveUseCase.execute(report);

      final result = await deleteUseCase.deleteMultiple([
        saved.id,
        'non-existent-1',
        'non-existent-2',
      ]);

      expect(result.deleted, equals(1));
      expect(result.notFound, equals(2));
      expect(result.failed, equals(0));
    });

    test('deleteByTicker removes all entries for ticker', () async {
      // Add multiple entries for same ticker
      final ticker = 'DELETE_TICKER';
      for (int i = 0; i < 3; i++) {
        await saveUseCase.execute(FinalReport(
          ticker: ticker,
          tradeDate: '2024-01-2$i',
          content: 'Test $i',
          timestamp: DateTime.now().subtract(Duration(days: i)),
        ));
      }

      // Delete all
      final count = await deleteUseCase.deleteByTicker(ticker);

      expect(count, equals(3));

      // Verify they're gone
      final remaining = await repository.getByTicker(ticker);
      expect(remaining.isEmpty, isTrue);
    });

    test('clearAll removes all entries', () async {
      // Get initial count
      final before = await repository.getAll();
      expect(before.isNotEmpty, isTrue);

      // Clear all
      await deleteUseCase.clearAll();

      // Verify empty
      final after = await repository.getAll();
      expect(after.isEmpty, isTrue);
    });

    test('deleteOlderThan removes old entries only', () async {
      // Add an old entry
      final oldReport = FinalReport(
        ticker: 'OLD',
        tradeDate: '2023-01-01',
        content: 'Old entry',
        timestamp: DateTime(2023, 1, 1),
      );
      await saveUseCase.execute(oldReport);

      // Delete entries older than 1 year
      final cutoff = DateTime.now().subtract(const Duration(days: 365));
      final count = await deleteUseCase.deleteOlderThan(cutoff);

      expect(count, greaterThan(0));
    });

    test('deleteErrors removes error entries only', () async {
      // Add an error entry
      final errorReport = FinalReport(
        ticker: 'ERROR_TEST',
        tradeDate: '2024-01-20',
        content: 'Error',
        timestamp: DateTime.now(),
        isError: true,
      );
      await saveUseCase.execute(errorReport);

      // Count errors before
      final allBefore = await repository.getAll();
      final errorsBefore = allBefore.where((e) => e.isError).length;

      // Delete errors
      final count = await deleteUseCase.deleteErrors();

      expect(count, equals(errorsBefore));

      // Verify no errors remain
      final allAfter = await repository.getAll();
      final errorsAfter = allAfter.where((e) => e.isError).length;
      expect(errorsAfter, equals(0));
    });

    test('previewDelete returns entry details', () async {
      final preview = await deleteUseCase.previewDelete('mock-1');

      expect(preview, isNotNull);
      expect(preview!.ticker, equals('AAPL'));
    });
  });
}