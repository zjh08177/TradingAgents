import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:trading_dummy/history/presentation/screens/history_screen.dart';
import 'package:trading_dummy/history/presentation/widgets/history_list_item.dart';
import 'package:trading_dummy/history/presentation/widgets/history_empty_state.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';
import 'package:trading_dummy/history/domain/value_objects/analysis_details.dart';
import 'package:trading_dummy/services/service_provider.dart';
import 'package:trading_dummy/services/langgraph_service.dart';
import 'package:trading_dummy/services/auto_test.dart';
import '../../../mocks/mock_history_repository.dart';

void main() {
  group('HistoryScreen', () {
    late MockHistoryRepository mockRepository;
    late ServiceProvider serviceProvider;

    setUp(() {
      mockRepository = MockHistoryRepository();
      serviceProvider = ServiceProvider(
        langGraphService: SimpleLangGraphService(
          url: 'http://test.com',
          apiKey: 'test-key',
          assistantId: 'test-assistant',
        ),
        autoTest: AutoTestController(),
        historyRepository: mockRepository,
        child: const SizedBox(),
      );
    });

    Widget createTestWidget(Widget child) {
      return MaterialApp(
        home: ServiceProvider(
          langGraphService: serviceProvider.langGraphService,
          autoTest: serviceProvider.autoTest,
          historyRepository: mockRepository,
          child: child,
        ),
      );
    }

    testWidgets('shows loading indicator while loading', (tester) async {
      mockRepository.setLoading(true);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pump(); // Start loading

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows empty state when no entries', (tester) async {
      mockRepository.setEntries([]);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.byType(HistoryEmptyState), findsOneWidget);
      expect(find.text('No Analysis History'), findsOneWidget);
    });

    testWidgets('shows error state when error occurs', (tester) async {
      mockRepository.setError('Test error message');

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.text('Error loading history'), findsOneWidget);
      expect(find.text('Test error message'), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('shows list of history entries', (tester) async {
      final entries = [
        HistoryEntry(
          id: '1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          timestamp: DateTime.now(),
          finalDecision: 'BUY',
          confidence: 0.85,
          summary: 'Strong buy signal',
          details: AnalysisDetails(),
        ),
        HistoryEntry(
          id: '2',
          ticker: 'GOOGL',
          tradeDate: '2024-01-14',
          timestamp: DateTime.now().subtract(const Duration(days: 1)),
          finalDecision: 'SELL',
          confidence: 0.72,
          summary: 'Sell recommendation',
          details: AnalysisDetails(),
        ),
      ];

      mockRepository.setEntries(entries);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.byType(HistoryListItem), findsNWidgets(2));
      expect(find.text('AAPL'), findsOneWidget);
      expect(find.text('GOOGL'), findsOneWidget);
    });

    testWidgets('shows filter chips for unique tickers', (tester) async {
      final entries = [
        HistoryEntry(
          id: '1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          timestamp: DateTime.now(),
          finalDecision: 'BUY',
          confidence: 0.85,
          summary: 'Strong buy signal',
          details: AnalysisDetails(),
        ),
        HistoryEntry(
          id: '2',
          ticker: 'AAPL',
          tradeDate: '2024-01-14',
          timestamp: DateTime.now().subtract(const Duration(days: 1)),
          finalDecision: 'HOLD',
          confidence: 0.60,
          summary: 'Hold position',
          details: AnalysisDetails(),
        ),
        HistoryEntry(
          id: '3',
          ticker: 'GOOGL',
          tradeDate: '2024-01-13',
          timestamp: DateTime.now().subtract(const Duration(days: 2)),
          finalDecision: 'SELL',
          confidence: 0.72,
          summary: 'Sell recommendation',
          details: AnalysisDetails(),
        ),
      ];

      mockRepository.setEntries(entries);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.text('All'), findsOneWidget);
      expect(find.text('AAPL (2)'), findsOneWidget);
      expect(find.text('GOOGL (1)'), findsOneWidget);
    });

    testWidgets('filters entries when ticker chip is selected', (tester) async {
      final entries = [
        HistoryEntry(
          id: '1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          timestamp: DateTime.now(),
          finalDecision: 'BUY',
          confidence: 0.85,
          summary: 'Strong buy signal',
          details: AnalysisDetails(),
        ),
        HistoryEntry(
          id: '2',
          ticker: 'GOOGL',
          tradeDate: '2024-01-14',
          timestamp: DateTime.now().subtract(const Duration(days: 1)),
          finalDecision: 'SELL',
          confidence: 0.72,
          summary: 'Sell recommendation',
          details: AnalysisDetails(),
        ),
      ];

      mockRepository.setEntries(entries);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      // Initially shows both entries
      expect(find.byType(HistoryListItem), findsNWidgets(2));

      // Tap on AAPL filter
      await tester.tap(find.text('AAPL (1)'));
      await tester.pumpAndSettle();

      // Should show only AAPL entry
      expect(find.byType(HistoryListItem), findsOneWidget);
      expect(find.text('AAPL'), findsOneWidget);
      expect(find.text('GOOGL'), findsNothing);
    });

    testWidgets('shows delete confirmation dialog on swipe', (tester) async {
      final entries = [
        HistoryEntry(
          id: '1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          timestamp: DateTime.now(),
          finalDecision: 'BUY',
          confidence: 0.85,
          summary: 'Strong buy signal',
          details: AnalysisDetails(),
        ),
      ];

      mockRepository.setEntries(entries);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      // Start swipe gesture
      await tester.drag(find.byType(HistoryListItem), const Offset(-300, 0));
      await tester.pumpAndSettle();

      // Confirmation dialog should appear
      expect(find.text('Delete Analysis'), findsOneWidget);
      expect(find.text('Delete AAPL analysis from 2024-01-15?'), findsOneWidget);
      expect(find.text('Cancel'), findsOneWidget);
      expect(find.text('Delete'), findsOneWidget);
    });

    testWidgets('shows more menu with options when entries exist', (tester) async {
      final entries = [
        HistoryEntry(
          id: '1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          timestamp: DateTime.now(),
          finalDecision: 'BUY',
          confidence: 0.85,
          summary: 'Strong buy signal',
          details: AnalysisDetails(),
        ),
      ];

      mockRepository.setEntries(entries);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      // Tap more menu
      await tester.tap(find.byIcon(Icons.more_vert));
      await tester.pumpAndSettle();

      expect(find.text('Clear Filter'), findsOneWidget);
      expect(find.text('Clear All'), findsOneWidget);
    });

    testWidgets('shows clear all confirmation dialog', (tester) async {
      final entries = [
        HistoryEntry(
          id: '1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          timestamp: DateTime.now(),
          finalDecision: 'BUY',
          confidence: 0.85,
          summary: 'Strong buy signal',
          details: AnalysisDetails(),
        ),
      ];

      mockRepository.setEntries(entries);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      // Open menu
      await tester.tap(find.byIcon(Icons.more_vert));
      await tester.pumpAndSettle();

      // Tap Clear All
      await tester.tap(find.text('Clear All'));
      await tester.pumpAndSettle();

      // Confirmation dialog should appear
      expect(find.text('Clear All History'), findsOneWidget);
      expect(find.text('This will permanently delete all analysis history. Are you sure?'), findsOneWidget);
    });

    testWidgets('refresh indicator triggers data reload', (tester) async {
      final entries = [
        HistoryEntry(
          id: '1',
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
          timestamp: DateTime.now(),
          finalDecision: 'BUY',
          confidence: 0.85,
          summary: 'Strong buy signal',
          details: AnalysisDetails(),
        ),
      ];

      mockRepository.setEntries(entries);

      await tester.pumpWidget(createTestWidget(const HistoryScreen()));
      await tester.pumpAndSettle();

      // Pull to refresh
      await tester.fling(find.byType(HistoryListItem), const Offset(0, 300), 1000);
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Verify refresh was called
      expect(mockRepository.refreshCalled, isTrue);
    });
  });
}