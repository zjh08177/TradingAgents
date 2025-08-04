import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:mocktail/mocktail.dart';

import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/presentation/view_models/job_queue_view_model.dart';
import 'package:trading_dummy/jobs/presentation/widgets/job_submission_widget.dart';

// Mock classes
class MockJobQueueViewModel extends Mock implements JobQueueViewModel {}

void main() {
  group('JobSubmissionWidget', () {
    late MockJobQueueViewModel mockViewModel;

    setUpAll(() {
      registerFallbackValue(JobPriority.normal);
    });

    setUp(() {
      mockViewModel = MockJobQueueViewModel();
      // Set up default mock behavior
      when(() => mockViewModel.isLoading).thenReturn(false);
      when(() => mockViewModel.errorMessage).thenReturn(null);
      when(() => mockViewModel.submitAnalysis(any(), any(), priority: any(named: 'priority')))
          .thenAnswer((_) async {});
      when(() => mockViewModel.clearError()).thenReturn(null);
    });

    Widget createTestWidget() {
      return MaterialApp(
        home: Scaffold(
          body: ChangeNotifierProvider<JobQueueViewModel>.value(
            value: mockViewModel,
            child: const JobSubmissionWidget(),
          ),
        ),
      );
    }

    testWidgets('should display all form fields and submit button', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Verify form fields are present
      expect(find.text('Submit Analysis Job'), findsOneWidget);
      expect(find.byType(TextFormField), findsNWidgets(2)); // Ticker and Trade Date
      expect(find.byType(DropdownButtonFormField<JobPriority>), findsOneWidget);
      expect(find.byType(ElevatedButton), findsOneWidget);
      expect(find.text('Submit Analysis'), findsOneWidget);
    });

    testWidgets('should validate ticker field correctly', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Find the ticker field
      final tickerField = find.widgetWithText(TextFormField, 'Stock Ticker').first;
      
      // Test empty ticker validation
      await tester.enterText(tickerField, '');
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();
      
      expect(find.text('Please enter a stock ticker'), findsOneWidget);

      // Test ticker too long
      await tester.enterText(tickerField, 'VERYLONGTICKER');
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();
      
      expect(find.text('Ticker must be 1-10 characters'), findsOneWidget);

      // Test invalid characters
      await tester.enterText(tickerField, 'A@PL');
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();
      
      expect(find.text('Ticker must contain only letters and numbers'), findsOneWidget);
    });

    testWidgets('should auto-uppercase ticker input', (tester) async {
      await tester.pumpWidget(createTestWidget());

      final tickerField = find.widgetWithText(TextFormField, 'Stock Ticker').first;
      
      // Enter lowercase ticker
      await tester.enterText(tickerField, 'aapl');
      await tester.pump();
      
      // Verify it was converted to uppercase
      final textField = tester.widget<TextFormField>(tickerField);
      expect(textField.controller?.text, equals('AAPL'));
    });

    testWidgets('should validate trade date field', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Find the trade date field
      final tradeDateField = find.widgetWithText(TextFormField, 'Trade Date').first;
      
      // Clear the default date and try to submit
      final textField = tester.widget<TextFormField>(tradeDateField);
      textField.controller?.clear();
      
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();
      
      expect(find.text('Please select a trade date'), findsOneWidget);
    });

    testWidgets('should open date picker when trade date field is tapped', (tester) async {
      await tester.pumpWidget(createTestWidget());

      final tradeDateField = find.widgetWithText(TextFormField, 'Trade Date').first;
      
      await tester.tap(tradeDateField);
      await tester.pumpAndSettle();
      
      // Verify date picker is shown
      expect(find.byType(DatePickerDialog), findsOneWidget);
    });

    testWidgets('should allow priority selection', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Find and tap the priority dropdown
      final priorityDropdown = find.byType(DropdownButtonFormField<JobPriority>);
      await tester.tap(priorityDropdown);
      await tester.pumpAndSettle();

      // Verify all priority options are available
      expect(find.text('Low'), findsOneWidget);
      expect(find.text('Normal'), findsOneWidget);
      expect(find.text('High'), findsOneWidget);
      expect(find.text('Critical'), findsOneWidget);

      // Select High priority
      await tester.tap(find.text('High'));
      await tester.pumpAndSettle();

      // Verify selection was made
      expect(find.text('High'), findsOneWidget);
    });

    testWidgets('should submit job with valid input', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Fill in valid form data
      final tickerField = find.widgetWithText(TextFormField, 'Stock Ticker').first;
      await tester.enterText(tickerField, 'AAPL');
      
      // Trade date field already has default value
      
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();

      // Verify submitAnalysis was called
      verify(() => mockViewModel.submitAnalysis(
        'AAPL',
        any(),
        priority: JobPriority.normal,
      )).called(1);
    });

    testWidgets('should clear form after successful submission', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Fill in form data
      final tickerField = find.widgetWithText(TextFormField, 'Stock Ticker').first;
      await tester.enterText(tickerField, 'AAPL');
      
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();

      // Verify ticker field was cleared
      final textField = tester.widget<TextFormField>(tickerField);
      expect(textField.controller?.text, isEmpty);
    });

    testWidgets('should show loading state during submission', (tester) async {
      when(() => mockViewModel.isLoading).thenReturn(true);

      await tester.pumpWidget(createTestWidget());

      // Verify loading indicator and disabled button
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Submitting...'), findsOneWidget);
      
      final submitButton = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
      expect(submitButton.onPressed, isNull);
    });

    testWidgets('should display error message when present', (tester) async {
      const errorMessage = 'Test error message';
      when(() => mockViewModel.errorMessage).thenReturn(errorMessage);

      await tester.pumpWidget(createTestWidget());

      // Verify error message is displayed
      expect(find.text(errorMessage), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
      expect(find.byIcon(Icons.close), findsOneWidget);
    });

    testWidgets('should clear error when close button is tapped', (tester) async {
      const errorMessage = 'Test error message';
      when(() => mockViewModel.errorMessage).thenReturn(errorMessage);

      await tester.pumpWidget(createTestWidget());

      // Tap the close button
      await tester.tap(find.byIcon(Icons.close));
      await tester.pump();

      // Verify clearError was called
      verify(() => mockViewModel.clearError()).called(1);
    });

    testWidgets('should show success snackbar after submission', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Fill in valid form data
      final tickerField = find.widgetWithText(TextFormField, 'Stock Ticker').first;
      await tester.enterText(tickerField, 'AAPL');
      
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // Verify success snackbar is shown
      expect(find.byType(SnackBar), findsOneWidget);
      expect(find.text('Analysis job submitted for AAPL'), findsOneWidget);
    });

    testWidgets('should handle submission errors gracefully', (tester) async {
      when(() => mockViewModel.submitAnalysis(any(), any(), priority: any(named: 'priority')))
          .thenThrow(Exception('Test error'));

      await tester.pumpWidget(createTestWidget());

      // Fill in valid form data
      final tickerField = find.widgetWithText(TextFormField, 'Stock Ticker').first;
      await tester.enterText(tickerField, 'AAPL');
      
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();

      // Verify submission was attempted
      verify(() => mockViewModel.submitAnalysis(
        'AAPL',
        any(),
        priority: JobPriority.normal,
      )).called(1);
    });

    testWidgets('should prevent submission with invalid form', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Try to submit with empty ticker
      await tester.tap(find.text('Submit Analysis'));
      await tester.pump();

      // Verify submitAnalysis was not called
      verifyNever(() => mockViewModel.submitAnalysis(any(), any(), priority: any(named: 'priority')));
    });

    group('Priority Icons and Labels', () {
      testWidgets('should display correct priority icons', (tester) async {
        await tester.pumpWidget(createTestWidget());

        // Open priority dropdown
        await tester.tap(find.byType(DropdownButtonFormField<JobPriority>));
        await tester.pumpAndSettle();

        // Verify priority icons are present
        expect(find.byIcon(Icons.low_priority), findsOneWidget); // Low
        expect(find.byIcon(Icons.remove), findsOneWidget); // Normal
        expect(find.byIcon(Icons.priority_high), findsOneWidget); // High
        expect(find.byIcon(Icons.warning), findsOneWidget); // Critical
      });
    });
  });
}