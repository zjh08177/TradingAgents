import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';
import 'package:trading_dummy/history/domain/value_objects/analysis_details.dart';
import 'package:trading_dummy/history/presentation/view_models/history_view_model.dart';
import 'package:trading_dummy/history/infrastructure/repositories/mock_history_repository.dart';

void main() {
  group('HistoryViewModel', () {
    late MockHistoryRepository repository;
    late HistoryViewModel viewModel;
    final viewModels = <HistoryViewModel>[];

    setUp(() {
      repository = MockHistoryRepository();
      viewModel = HistoryViewModel(repository);
      viewModels.add(viewModel);
    });

    tearDown(() {
      // Dispose all created view models
      for (final vm in viewModels) {
        vm.dispose();
      }
      viewModels.clear();
    });

    test('initializes and loads history on creation', () async {
      // Give time for initial load
      await Future.delayed(const Duration(milliseconds: 100));
      
      expect(viewModel.entries, isNotEmpty);
      expect(viewModel.isLoading, isFalse);
      expect(viewModel.errorMessage, isNull);
    });

    test('filters entries by ticker', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      final initialCount = viewModel.entries.length;
      expect(initialCount, greaterThan(0));
      
      viewModel.setFilter('AAPL');
      final filteredEntries = viewModel.entries;
      
      expect(filteredEntries.every((e) => e.ticker.contains('AAPL')), isTrue);
      expect(viewModel.filterTicker, equals('AAPL'));
      expect(viewModel.hasFilter, isTrue);
    });

    test('clears filter correctly', () {
      viewModel.setFilter('AAPL');
      expect(viewModel.hasFilter, isTrue);
      
      viewModel.clearFilter();
      expect(viewModel.filterTicker, isEmpty);
      expect(viewModel.hasFilter, isFalse);
    });

    test('deletes entry successfully', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      final initialEntries = List<HistoryEntry>.from(viewModel.entries);
      expect(initialEntries, isNotEmpty);
      
      final entryToDelete = initialEntries.first;
      await viewModel.deleteEntry(entryToDelete.id);
      
      expect(viewModel.entries.any((e) => e.id == entryToDelete.id), isFalse);
      expect(viewModel.entries.length, equals(initialEntries.length - 1));
    });

    test('handles delete error gracefully', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      // Try to delete non-existent entry
      await viewModel.deleteEntry('non-existent-id');
      
      expect(viewModel.errorMessage, contains('Failed to delete'));
    });

    test('gets unique tickers sorted', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      final tickers = viewModel.uniqueTickers;
      
      expect(tickers, isNotEmpty);
      expect(tickers, equals(tickers.toSet().toList())); // No duplicates
      expect(tickers, equals(List<String>.from(tickers)..sort())); // Sorted
    });

    test('calculates ticker counts correctly', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      final counts = viewModel.tickerCounts;
      
      expect(counts, isNotEmpty);
      expect(counts.values.every((count) => count > 0), isTrue);
      
      // Verify counts match actual entries
      for (final ticker in counts.keys) {
        final actualCount = viewModel.entries.where((e) => e.ticker == ticker).length;
        expect(counts[ticker], equals(actualCount));
      }
    });

    test('groups entries by date correctly', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      final grouped = viewModel.groupByDate();
      
      expect(grouped, isNotEmpty);
      
      // Verify each group contains entries from the same day
      for (final entries in grouped.values) {
        expect(entries, isNotEmpty);
        
        if (entries.length > 1) {
          final firstDate = entries.first.timestamp;
          final sameDayDates = entries.skip(1).map((e) => e.timestamp).every((date) =>
            date.year == firstDate.year &&
            date.month == firstDate.month &&
            date.day == firstDate.day
          );
          expect(sameDayDates, isTrue);
        }
      }
    });

    test('refreshes data successfully', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      final initialCount = viewModel.entries.length;
      
      // Add a new entry to repository
      await repository.save(HistoryEntry(
        ticker: 'NEW',
        tradeDate: '2024-01-20',
        timestamp: DateTime.now(),
        finalDecision: 'BUY',
        summary: 'New entry',
        details: const AnalysisDetails(),
      ));
      
      await viewModel.refresh();
      
      expect(viewModel.entries.length, equals(initialCount + 1));
      expect(viewModel.entries.any((e) => e.ticker == 'NEW'), isTrue);
    });

    test('clears all entries', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      expect(viewModel.entries, isNotEmpty);
      
      await viewModel.clearAll();
      
      expect(viewModel.entries, isEmpty);
      expect(viewModel.hasEntries, isFalse);
      expect(viewModel.filterTicker, isEmpty);
    });

    test('loading state changes correctly', () async {
      expect(viewModel.isLoading, isTrue); // Initial load
      
      await Future.delayed(const Duration(milliseconds: 100));
      expect(viewModel.isLoading, isFalse);
      
      // Trigger another load
      final future = viewModel.refresh();
      expect(viewModel.isLoading, isTrue);
      
      await future;
      expect(viewModel.isLoading, isFalse);
    });

    test('gets recent entries limited correctly', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      final recent5 = viewModel.getRecentEntries(limit: 5);
      expect(recent5.length, lessThanOrEqualTo(5));
      
      // Verify sorted by most recent first
      for (int i = 1; i < recent5.length; i++) {
        expect(recent5[i-1].timestamp.isAfter(recent5[i].timestamp), isTrue);
      }
    });

    test('error message auto-clears after delay', () async {
      await Future.delayed(const Duration(milliseconds: 100));
      
      // Trigger an error
      await viewModel.deleteEntry('non-existent-id');
      expect(viewModel.errorMessage, contains('Failed to delete'));
      
      // Wait for auto-clear
      await Future.delayed(const Duration(seconds: 6));
      expect(viewModel.errorMessage, isNull);
    });
  });
}