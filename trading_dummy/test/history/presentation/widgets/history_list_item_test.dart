import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';
import 'package:trading_dummy/history/domain/value_objects/analysis_details.dart';
import 'package:trading_dummy/history/presentation/widgets/history_list_item.dart';

void main() {
  group('HistoryListItem', () {
    late HistoryEntry testEntry;
    late HistoryEntry errorEntry;
    bool tapped = false;

    setUp(() {
      tapped = false;
      testEntry = HistoryEntry(
        id: 'test-id',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        timestamp: DateTime(2024, 1, 15, 10, 30),
        finalDecision: 'BUY',
        confidence: 0.85,
        summary: 'Strong buy signal based on positive market indicators',
        details: const AnalysisDetails(),
      );

      errorEntry = HistoryEntry(
        id: 'error-id',
        ticker: 'GOOGL',
        tradeDate: '2024-01-14',
        timestamp: DateTime(2024, 1, 14, 15, 45),
        finalDecision: 'ERROR',
        summary: 'Analysis failed',
        details: const AnalysisDetails(),
        isError: true,
        errorMessage: 'Network timeout',
      );
    });

    Widget createWidgetUnderTest(HistoryEntry entry) {
      return MaterialApp(
        home: Scaffold(
          body: HistoryListItem(
            entry: entry,
            onTap: () => tapped = true,
          ),
        ),
      );
    }

    testWidgets('displays ticker correctly', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      
      expect(find.text('AAPL'), findsOneWidget);
    });

    testWidgets('displays trade date correctly', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      
      expect(find.text('2024-01-15'), findsOneWidget);
    });

    testWidgets('displays summary correctly', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      
      expect(find.text('Strong buy signal based on positive market indicators'), findsOneWidget);
    });

    testWidgets('displays BUY decision with green icon', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      
      final iconFinder = find.byIcon(Icons.trending_up);
      expect(iconFinder, findsOneWidget);
      
      final icon = tester.widget<Icon>(iconFinder);
      expect(icon.color, equals(Colors.green));
    });

    testWidgets('displays SELL decision with red icon', (WidgetTester tester) async {
      final sellEntry = HistoryEntry(
        id: 'sell-id',
        ticker: 'TSLA',
        tradeDate: '2024-01-16',
        timestamp: DateTime.now(),
        finalDecision: 'SELL',
        confidence: 0.72,
        summary: 'Sell recommendation',
        details: const AnalysisDetails(),
      );
      
      await tester.pumpWidget(createWidgetUnderTest(sellEntry));
      
      final iconFinder = find.byIcon(Icons.trending_down);
      expect(iconFinder, findsOneWidget);
      
      final icon = tester.widget<Icon>(iconFinder);
      expect(icon.color, equals(Colors.red));
    });

    testWidgets('displays HOLD decision with orange icon', (WidgetTester tester) async {
      final holdEntry = HistoryEntry(
        id: 'hold-id',
        ticker: 'MSFT',
        tradeDate: '2024-01-17',
        timestamp: DateTime.now(),
        finalDecision: 'HOLD',
        confidence: 0.60,
        summary: 'Hold recommendation',
        details: const AnalysisDetails(),
      );
      
      await tester.pumpWidget(createWidgetUnderTest(holdEntry));
      
      final iconFinder = find.byIcon(Icons.swap_horiz);
      expect(iconFinder, findsOneWidget);
      
      final icon = tester.widget<Icon>(iconFinder);
      expect(icon.color, equals(Colors.orange));
    });

    testWidgets('displays confidence percentage', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      
      expect(find.text('85%'), findsOneWidget);
      expect(find.text('confidence'), findsOneWidget);
    });

    testWidgets('shows circular progress indicator for confidence', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      
      final progressFinder = find.byType(CircularProgressIndicator);
      expect(progressFinder, findsOneWidget);
      
      final progress = tester.widget<CircularProgressIndicator>(progressFinder);
      expect(progress.value, equals(0.85));
    });

    testWidgets('hides confidence for error entries', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(errorEntry));
      
      expect(find.text('confidence'), findsNothing);
      expect(find.byType(CircularProgressIndicator), findsNothing);
    });

    testWidgets('displays ERROR badge for error entries', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(errorEntry));
      
      expect(find.text('ERROR'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('handles tap correctly', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      
      expect(tapped, isFalse);
      
      await tester.tap(find.byType(InkWell));
      await tester.pump();
      
      expect(tapped, isTrue);
    });

    testWidgets('truncates long summary with ellipsis', (WidgetTester tester) async {
      final longSummaryEntry = HistoryEntry(
        id: 'long-id',
        ticker: 'AMZN',
        tradeDate: '2024-01-18',
        timestamp: DateTime.now(),
        finalDecision: 'BUY',
        summary: 'This is a very long summary that should be truncated with ellipsis because it exceeds the maximum number of lines allowed in the widget which is set to 2 lines to maintain a clean and consistent layout across all history items',
        details: const AnalysisDetails(),
      );
      
      await tester.pumpWidget(createWidgetUnderTest(longSummaryEntry));
      
      final textWidget = tester.widget<Text>(
        find.text(longSummaryEntry.summary)
      );
      expect(textWidget.maxLines, equals(2));
      expect(textWidget.overflow, equals(TextOverflow.ellipsis));
    });

    testWidgets('applies correct styling to card', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      
      final cardFinder = find.byType(Card);
      expect(cardFinder, findsOneWidget);
      
      final card = tester.widget<Card>(cardFinder);
      expect(card.elevation, equals(2));
      expect(card.margin, equals(const EdgeInsets.symmetric(horizontal: 16, vertical: 8)));
    });

    testWidgets('confidence color changes based on value', (WidgetTester tester) async {
      // High confidence (>= 70%) - Green
      await tester.pumpWidget(createWidgetUnderTest(testEntry));
      var progress = tester.widget<CircularProgressIndicator>(
        find.byType(CircularProgressIndicator)
      );
      expect((progress.valueColor as AlwaysStoppedAnimation).value, equals(Colors.green));

      // Medium confidence (50-69%) - Orange
      final mediumEntry = HistoryEntry(
        id: 'medium-id',
        ticker: 'FB',
        tradeDate: '2024-01-19',
        timestamp: DateTime.now(),
        finalDecision: 'HOLD',
        confidence: 0.60,
        summary: 'Medium confidence',
        details: const AnalysisDetails(),
      );
      await tester.pumpWidget(createWidgetUnderTest(mediumEntry));
      progress = tester.widget<CircularProgressIndicator>(
        find.byType(CircularProgressIndicator)
      );
      expect((progress.valueColor as AlwaysStoppedAnimation).value, equals(Colors.orange));

      // Low confidence (< 50%) - Red
      final lowEntry = HistoryEntry(
        id: 'low-id',
        ticker: 'NFLX',
        tradeDate: '2024-01-20',
        timestamp: DateTime.now(),
        finalDecision: 'SELL',
        confidence: 0.35,
        summary: 'Low confidence',
        details: const AnalysisDetails(),
      );
      await tester.pumpWidget(createWidgetUnderTest(lowEntry));
      progress = tester.widget<CircularProgressIndicator>(
        find.byType(CircularProgressIndicator)
      );
      expect((progress.valueColor as AlwaysStoppedAnimation).value, equals(Colors.red));
    });
  });
}