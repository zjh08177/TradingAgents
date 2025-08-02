import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/history/presentation/screens/history_detail_screen.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';
import 'package:trading_dummy/history/domain/value_objects/analysis_details.dart';

void main() {
  group('HistoryDetailScreen', () {
    late HistoryEntry testEntry;
    late HistoryEntry errorEntry;
    late HistoryEntry fullEntry;

    setUp(() {
      testEntry = HistoryEntry(
        id: '1',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        timestamp: DateTime(2024, 1, 15, 10, 30),
        finalDecision: 'BUY',
        confidence: 0.85,
        summary: 'Strong buy signal based on positive market momentum',
        details: AnalysisDetails(),
      );

      errorEntry = HistoryEntry(
        id: '2',
        ticker: 'GOOGL',
        tradeDate: '2024-01-14',
        timestamp: DateTime(2024, 1, 14, 14, 45),
        finalDecision: 'ERROR',
        confidence: null,
        summary: 'Analysis failed',
        isError: true,
        errorMessage: 'Network timeout during analysis',
        details: AnalysisDetails(),
      );

      fullEntry = HistoryEntry(
        id: '3',
        ticker: 'MSFT',
        tradeDate: '2024-01-13',
        timestamp: DateTime(2024, 1, 13, 9, 15),
        finalDecision: 'SELL',
        confidence: 0.72,
        summary: 'Sell recommendation due to overvaluation',
        details: AnalysisDetails(
          marketAnalysis: '## Market Overview\nThe market is showing bearish signals...',
          fundamentals: '## Financial Analysis\nP/E ratio is above historical average...',
          sentiment: '## Sentiment Analysis\nNegative sentiment detected in news...',
          newsAnalysis: '## Recent News\n- Regulatory concerns\n- Competition increasing',
          bullArgument: '## Bull Case\nStrong cash position and cloud growth...',
          bearArgument: '## Bear Case\nValuation concerns and slowing growth...',
          investmentPlan: '## Investment Plan\n1. Sell 50% of position\n2. Set stop loss at \$420',
          rawData: {
            'analysis_version': '1.0',
            'confidence_score': 0.72,
            'signals': ['overbought', 'negative_sentiment'],
          },
        ),
      );
    });

    Widget createTestWidget(HistoryEntry entry) {
      return MaterialApp(
        home: HistoryDetailScreen(entry: entry),
      );
    }

    testWidgets('displays basic entry information', (tester) async {
      await tester.pumpWidget(createTestWidget(testEntry));

      expect(find.text('AAPL - 2024-01-15'), findsOneWidget);
      expect(find.text('BUY'), findsOneWidget);
      expect(find.text('85%'), findsOneWidget);
      expect(find.text('Strong buy signal based on positive market momentum'), findsOneWidget);
    });

    testWidgets('displays error state correctly', (tester) async {
      await tester.pumpWidget(createTestWidget(errorEntry));

      expect(find.text('GOOGL - 2024-01-14'), findsOneWidget);
      expect(find.text('ERROR'), findsOneWidget);
      expect(find.text('Network timeout during analysis'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsAtLeastNWidgets(1));
    });

    testWidgets('shows all three tabs', (tester) async {
      await tester.pumpWidget(createTestWidget(fullEntry));

      // Check for tabs specifically
      expect(find.byType(Tab), findsNWidgets(3));
      expect(find.descendant(
        of: find.byType(TabBar),
        matching: find.text('Summary'),
      ), findsOneWidget);
      expect(find.descendant(
        of: find.byType(TabBar),
        matching: find.text('Analysis'),
      ), findsOneWidget);
      expect(find.descendant(
        of: find.byType(TabBar),
        matching: find.text('Raw Data'),
      ), findsOneWidget);
    });

    testWidgets('switches between tabs correctly', (tester) async {
      await tester.pumpWidget(createTestWidget(fullEntry));

      // Initially on Summary tab
      expect(find.text('Trading Decision'), findsOneWidget);
      expect(find.text('Sell recommendation due to overvaluation'), findsOneWidget);

      // Switch to Analysis tab - tap on the tab in TabBar
      await tester.tap(find.descendant(
        of: find.byType(TabBar),
        matching: find.text('Analysis'),
      ));
      await tester.pumpAndSettle();

      // These section titles appear both as card headers and in markdown content
      expect(find.text('Market Analysis'), findsAtLeastNWidgets(1));
      expect(find.text('Fundamentals'), findsAtLeastNWidgets(1));
      expect(find.text('Sentiment Analysis'), findsAtLeastNWidgets(1));

      // Switch to Raw Data tab - tap on the tab in TabBar
      await tester.tap(find.descendant(
        of: find.byType(TabBar),
        matching: find.text('Raw Data'),
      ));
      await tester.pumpAndSettle();

      expect(find.text('Raw JSON Data'), findsOneWidget);
      expect(find.byIcon(Icons.copy), findsOneWidget);
    });

    testWidgets('shows correct decision icon and color', (tester) async {
      await tester.pumpWidget(createTestWidget(testEntry));

      // BUY should show green trending up icon
      expect(find.byIcon(Icons.trending_up), findsOneWidget);
      
      // Test SELL decision
      await tester.pumpWidget(createTestWidget(fullEntry));
      expect(find.byIcon(Icons.trending_down), findsOneWidget);

      // Test ERROR decision
      await tester.pumpWidget(createTestWidget(errorEntry));
      expect(find.byIcon(Icons.error_outline), findsAtLeastNWidgets(1));
    });

    testWidgets('shows confidence indicator correctly', (tester) async {
      await tester.pumpWidget(createTestWidget(testEntry));

      expect(find.text('85%'), findsOneWidget);
      expect(find.text('confidence'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('hides confidence for error entries', (tester) async {
      await tester.pumpWidget(createTestWidget(errorEntry));

      expect(find.text('confidence'), findsNothing);
      expect(find.byType(CircularProgressIndicator), findsNothing);
    });

    testWidgets('displays metadata correctly', (tester) async {
      await tester.pumpWidget(createTestWidget(testEntry));

      expect(find.text('Details'), findsOneWidget);
      expect(find.text('Ticker'), findsOneWidget);
      expect(find.text('AAPL'), findsAtLeastNWidgets(1));
      expect(find.text('Trade Date'), findsOneWidget);
      expect(find.text('2024-01-15'), findsAtLeastNWidgets(1));
      expect(find.text('Analysis Time'), findsOneWidget);
    });

    testWidgets('shows empty analysis tab when no details', (tester) async {
      await tester.pumpWidget(createTestWidget(testEntry));

      // Switch to Analysis tab
      await tester.tap(find.text('Analysis'));
      await tester.pumpAndSettle();

      expect(find.text('No detailed analysis available'), findsOneWidget);
      expect(find.byIcon(Icons.analytics_outlined), findsOneWidget);
    });

    testWidgets('shows all analysis sections when available', (tester) async {
      await tester.pumpWidget(createTestWidget(fullEntry));

      // Switch to Analysis tab - tap on the tab in TabBar
      await tester.tap(find.descendant(
        of: find.byType(TabBar),
        matching: find.text('Analysis'),
      ));
      await tester.pumpAndSettle();

      // These section titles appear both as card headers and in markdown content
      expect(find.text('Market Analysis'), findsAtLeastNWidgets(1));
      expect(find.text('Fundamentals'), findsAtLeastNWidgets(1));
      expect(find.text('Sentiment Analysis'), findsAtLeastNWidgets(1));
      expect(find.text('News Analysis'), findsAtLeastNWidgets(1));
      expect(find.text('Bull Case'), findsAtLeastNWidgets(1));
      expect(find.text('Bear Case'), findsAtLeastNWidgets(1));
      expect(find.text('Investment Plan'), findsAtLeastNWidgets(1));
    });

    testWidgets('shows empty raw data tab when no data', (tester) async {
      await tester.pumpWidget(createTestWidget(testEntry));

      // Switch to Raw Data tab
      await tester.tap(find.text('Raw Data'));
      await tester.pumpAndSettle();

      expect(find.text('No raw data available'), findsOneWidget);
      expect(find.byIcon(Icons.code_off), findsOneWidget);
    });

    testWidgets('shows raw data when available', (tester) async {
      await tester.pumpWidget(createTestWidget(fullEntry));

      // Switch to Raw Data tab - tap on the tab in TabBar
      await tester.tap(find.descendant(
        of: find.byType(TabBar),
        matching: find.text('Raw Data'),
      ));
      await tester.pumpAndSettle();

      expect(find.text('Raw JSON Data'), findsOneWidget);
      // The JSON is formatted and displayed inside a SelectableText widget
      expect(find.byType(SelectableText), findsOneWidget);
      // Check the content contains our expected data
      final selectableText = tester.widget<SelectableText>(find.byType(SelectableText));
      expect(selectableText.data, contains('analysis_version'));
      expect(selectableText.data, contains('confidence_score'));
    });

    testWidgets('share button copies analysis to clipboard', (tester) async {
      // Set up clipboard mock
      final List<Map<String, dynamic>> clipboardData = [];
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, (message) async {
        if (message.method == 'Clipboard.setData') {
          clipboardData.add(message.arguments as Map<String, dynamic>);
          return null;
        }
        return null;
      });

      await tester.pumpWidget(createTestWidget(fullEntry));

      // Tap share button
      await tester.tap(find.byIcon(Icons.share));
      await tester.pumpAndSettle();

      expect(clipboardData.isNotEmpty, isTrue);
      expect(clipboardData.first['text'], contains('MSFT Analysis'));
      expect(clipboardData.first['text'], contains('Decision: SELL'));
      expect(clipboardData.first['text'], contains('Confidence: 72%'));

      // Clean up
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, null);
    });

    testWidgets('copy button in raw data tab works', (tester) async {
      // Set up clipboard mock
      final List<Map<String, dynamic>> clipboardData = [];
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, (message) async {
        if (message.method == 'Clipboard.setData') {
          clipboardData.add(message.arguments as Map<String, dynamic>);
          return null;
        }
        return null;
      });

      await tester.pumpWidget(createTestWidget(fullEntry));

      // Switch to Raw Data tab
      await tester.tap(find.text('Raw Data'));
      await tester.pumpAndSettle();

      // Tap copy button
      await tester.tap(find.byIcon(Icons.copy));
      await tester.pumpAndSettle();

      expect(clipboardData.isNotEmpty, isTrue);
      expect(clipboardData.first['text'], contains('analysis_version'));

      // Clean up
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, null);
    });
  });
}