import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/history/presentation/widgets/history_empty_state.dart';

void main() {
  group('HistoryEmptyState', () {
    bool analyzePressed = false;

    setUp(() {
      analyzePressed = false;
    });

    Widget createWidgetUnderTest({VoidCallback? onAnalyzePressed}) {
      return MaterialApp(
        home: Scaffold(
          body: HistoryEmptyState(
            onAnalyzePressed: onAnalyzePressed,
          ),
        ),
      );
    }

    testWidgets('displays empty state icon', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      
      final iconFinder = find.byIcon(Icons.history);
      expect(iconFinder, findsOneWidget);
      
      final icon = tester.widget<Icon>(iconFinder);
      expect(icon.size, equals(80));
    });

    testWidgets('displays title text', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      
      expect(find.text('No Analysis History'), findsOneWidget);
    });

    testWidgets('displays description text', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      
      expect(
        find.text('Your stock analysis history will appear here.\nStart by analyzing a stock!'),
        findsOneWidget,
      );
    });

    testWidgets('shows analyze button when callback provided', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(
        onAnalyzePressed: () => analyzePressed = true,
      ));
      
      final buttonFinder = find.byType(FilledButton);
      expect(buttonFinder, findsOneWidget);
      
      expect(find.text('Analyze Stock'), findsOneWidget);
      expect(find.byIcon(Icons.analytics), findsOneWidget);
    });

    testWidgets('hides analyze button when no callback provided', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      
      expect(find.byType(FilledButton), findsNothing);
      expect(find.text('Analyze Stock'), findsNothing);
    });

    testWidgets('handles button tap correctly', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(
        onAnalyzePressed: () => analyzePressed = true,
      ));
      
      expect(analyzePressed, isFalse);
      
      await tester.tap(find.byType(FilledButton));
      await tester.pump();
      
      expect(analyzePressed, isTrue);
    });

    testWidgets('centers content properly', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      
      final centerFinder = find.byType(Center);
      expect(centerFinder, findsOneWidget);
      
      final columnFinder = find.descendant(
        of: centerFinder,
        matching: find.byType(Column),
      );
      expect(columnFinder, findsOneWidget);
      
      final column = tester.widget<Column>(columnFinder);
      expect(column.mainAxisAlignment, equals(MainAxisAlignment.center));
    });

    testWidgets('applies correct padding', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      
      final paddingFinder = find.byType(Padding).first;
      final padding = tester.widget<Padding>(paddingFinder);
      expect(padding.padding, equals(const EdgeInsets.all(32.0)));
    });

    testWidgets('text is centered', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      
      final descriptionText = tester.widget<Text>(
        find.text('Your stock analysis history will appear here.\nStart by analyzing a stock!')
      );
      expect(descriptionText.textAlign, equals(TextAlign.center));
    });

    testWidgets('uses correct text styles', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Title should use headlineSmall
      final titleText = tester.widget<Text>(find.text('No Analysis History'));
      expect(titleText.style?.fontWeight, equals(FontWeight.bold));
    });

    testWidgets('button has correct styling', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(
        onAnalyzePressed: () {},
      ));
      
      final button = tester.widget<FilledButton>(find.byType(FilledButton));
      final buttonStyle = button.style as ButtonStyle?;
      
      // Check padding
      final padding = buttonStyle?.padding?.resolve({});
      expect(padding, equals(const EdgeInsets.symmetric(horizontal: 24, vertical: 12)));
    });

    testWidgets('layout spacing is correct', (WidgetTester tester) async {
      await tester.pumpWidget(createWidgetUnderTest(
        onAnalyzePressed: () {},
      ));
      
      // Find all SizedBox widgets used for spacing
      final sizedBoxes = tester.widgetList<SizedBox>(find.byType(SizedBox));
      final heights = sizedBoxes
          .where((box) => box.height != null)
          .map((box) => box.height)
          .toList();
      
      // Should have spacing of 24, 8, and 32
      expect(heights.contains(24), isTrue);
      expect(heights.contains(8), isTrue);
      expect(heights.contains(32), isTrue);
    });
  });
}