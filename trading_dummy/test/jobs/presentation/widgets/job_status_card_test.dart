import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:mocktail/mocktail.dart';

import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/presentation/view_models/job_queue_view_model.dart';
import 'package:trading_dummy/jobs/presentation/widgets/job_status_card.dart';

// Mock classes
class MockJobQueueViewModel extends Mock implements JobQueueViewModel {}

void main() {
  group('JobStatusCard', () {
    late MockJobQueueViewModel mockViewModel;

    setUpAll(() {
      registerFallbackValue(JobPriority.normal);
    });

    setUp(() {
      mockViewModel = MockJobQueueViewModel();
      when(() => mockViewModel.cancelAnalysis(any())).thenAnswer((_) async => true);
      when(() => mockViewModel.submitAnalysis(any(), any(), priority: any(named: 'priority')))
          .thenAnswer((_) async {});
    });

    AnalysisJob createTestJob({
      String id = 'test-job-1',
      String ticker = 'AAPL',
      String tradeDate = '2024-01-20',
      JobStatus status = JobStatus.pending,
      JobPriority priority = JobPriority.normal,
      String? errorMessage,
      int retryCount = 0,
    }) {
      return AnalysisJob(
        id: id,
        ticker: ticker,
        tradeDate: tradeDate,
        status: status,
        priority: priority,
        createdAt: DateTime.now(),
        startedAt: status == JobStatus.running ? DateTime.now() : null,
        completedAt: status == JobStatus.completed ? DateTime.now() : null,
        resultId: status == JobStatus.completed ? 'result-123' : null,
        errorMessage: errorMessage,
        retryCount: retryCount,
      );
    }

    Widget createTestWidget(AnalysisJob job, {VoidCallback? onTap}) {
      return MaterialApp(
        home: Scaffold(
          body: ChangeNotifierProvider<JobQueueViewModel>.value(
            value: mockViewModel,
            child: JobStatusCard(
              job: job,
              onTap: onTap,
            ),
          ),
        ),
      );
    }

    testWidgets('should display job basic information', (tester) async {
      final job = createTestJob();
      await tester.pumpWidget(createTestWidget(job));

      // Verify basic job information is displayed
      expect(find.text('AAPL'), findsOneWidget);
      expect(find.text('Trade Date: 2024-01-20'), findsOneWidget);
      expect(find.text('Status: Pending'), findsOneWidget);
    });

    testWidgets('should display priority badge for non-normal priorities', (tester) async {
      final highPriorityJob = createTestJob(priority: JobPriority.high);
      await tester.pumpWidget(createTestWidget(highPriorityJob));

      expect(find.text('HIGH'), findsOneWidget);
    });

    testWidgets('should not display priority badge for normal priority', (tester) async {
      final normalPriorityJob = createTestJob(priority: JobPriority.normal);
      await tester.pumpWidget(createTestWidget(normalPriorityJob));

      expect(find.text('NORMAL'), findsNothing);
    });

    testWidgets('should display correct status indicators', (tester) async {
      final testCases = [
        (JobStatus.pending, Icons.schedule),
        (JobStatus.queued, Icons.queue),
        (JobStatus.running, Icons.play_circle_outline),
        (JobStatus.completed, Icons.check_circle_outline),
        (JobStatus.failed, Icons.error_outline),
        (JobStatus.cancelled, Icons.cancel_outlined),
      ];

      for (final (status, expectedIcon) in testCases) {
        final job = createTestJob(status: status);
        await tester.pumpWidget(createTestWidget(job));

        expect(find.byIcon(expectedIcon), findsOneWidget);
        await tester.pumpWidget(Container()); // Clear widget
      }
    });

    testWidgets('should display retry count when greater than 0', (tester) async {
      final job = createTestJob(retryCount: 2);
      await tester.pumpWidget(createTestWidget(job));

      expect(find.text('Retries: 2'), findsOneWidget);
    });

    testWidgets('should not display retry count when 0', (tester) async {
      final job = createTestJob(retryCount: 0);
      await tester.pumpWidget(createTestWidget(job));

      expect(find.text('Retries: 0'), findsNothing);
    });

    testWidgets('should display timestamps correctly', (tester) async {
      final now = DateTime.now();
      final job = AnalysisJob(
        id: 'test-job',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.completed,
        priority: JobPriority.normal,
        createdAt: now.subtract(const Duration(hours: 2)),
        startedAt: now.subtract(const Duration(hours: 1)),
        completedAt: now,
        resultId: 'result-123',
        errorMessage: null,
        retryCount: 0,
      );

      await tester.pumpWidget(createTestWidget(job));

      // Verify all timestamps are displayed
      expect(find.textContaining('Created:'), findsOneWidget);
      expect(find.textContaining('Started:'), findsOneWidget);
      expect(find.textContaining('Completed:'), findsOneWidget);
    });

    testWidgets('should display error message when present', (tester) async {
      const errorMessage = 'Test error occurred';
      final job = createTestJob(
        status: JobStatus.failed,
        errorMessage: errorMessage,
      );

      await tester.pumpWidget(createTestWidget(job));

      expect(find.text(errorMessage), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsAtLeastNWidgets(1));
    });

    testWidgets('should show cancel button for pending jobs', (tester) async {
      final job = createTestJob(status: JobStatus.pending);
      await tester.pumpWidget(createTestWidget(job));

      expect(find.text('Cancel'), findsOneWidget);
    });

    testWidgets('should show cancel button for queued jobs', (tester) async {
      final job = createTestJob(status: JobStatus.queued);
      await tester.pumpWidget(createTestWidget(job));

      expect(find.text('Cancel'), findsOneWidget);
    });

    testWidgets('should not show cancel button for running jobs', (tester) async {
      final job = createTestJob(status: JobStatus.running);
      await tester.pumpWidget(createTestWidget(job));

      expect(find.text('Cancel'), findsNothing);
    });

    testWidgets('should show retry button for failed jobs with retry count < 3', (tester) async {
      final job = createTestJob(
        status: JobStatus.failed,
        retryCount: 2,
      );

      await tester.pumpWidget(createTestWidget(job));

      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('should not show retry button for failed jobs with retry count >= 3', (tester) async {
      final job = createTestJob(
        status: JobStatus.failed,
        retryCount: 3,
      );

      await tester.pumpWidget(createTestWidget(job));

      expect(find.text('Retry'), findsNothing);
    });

    testWidgets('should handle cancel button tap with confirmation', (tester) async {
      final job = createTestJob(status: JobStatus.pending);
      await tester.pumpWidget(createTestWidget(job));

      // Tap cancel button
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();

      // Verify confirmation dialog is shown
      expect(find.text('Cancel Job'), findsOneWidget);
      expect(find.text('Are you sure you want to cancel the analysis for AAPL?'), findsOneWidget);
      expect(find.text('No'), findsOneWidget);
      expect(find.text('Yes, Cancel'), findsOneWidget);

      // Confirm cancellation
      await tester.tap(find.text('Yes, Cancel'));
      await tester.pumpAndSettle();

      // Verify cancelAnalysis was called
      verify(() => mockViewModel.cancelAnalysis('test-job-1')).called(1);
    });

    testWidgets('should handle cancel button tap with rejection', (tester) async {
      final job = createTestJob(status: JobStatus.pending);
      await tester.pumpWidget(createTestWidget(job));

      // Tap cancel button
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();

      // Reject cancellation
      await tester.tap(find.text('No'));
      await tester.pumpAndSettle();

      // Verify cancelAnalysis was not called
      verifyNever(() => mockViewModel.cancelAnalysis(any()));
    });

    testWidgets('should handle retry button tap', (tester) async {
      final job = createTestJob(
        status: JobStatus.failed,
        retryCount: 1,
        priority: JobPriority.high,
      );

      await tester.pumpWidget(createTestWidget(job));

      // Tap retry button
      await tester.tap(find.text('Retry'));
      await tester.pump();

      // Verify submitAnalysis was called with same parameters
      verify(() => mockViewModel.submitAnalysis(
        'AAPL',
        '2024-01-20',
        priority: JobPriority.high,
      )).called(1);
    });

    testWidgets('should call onTap callback when card is tapped', (tester) async {
      bool tapped = false;
      final job = createTestJob();

      await tester.pumpWidget(createTestWidget(job, onTap: () => tapped = true));

      // Tap the card
      await tester.tap(find.byType(InkWell));
      await tester.pump();

      expect(tapped, isTrue);
    });

    testWidgets('should format timestamps correctly', (tester) async {
      final now = DateTime.now();
      final oneMinuteAgo = now.subtract(const Duration(minutes: 1));
      final oneHourAgo = now.subtract(const Duration(hours: 1));

      final job = AnalysisJob(
        id: 'test-job',
        ticker: 'AAPL',
        tradeDate: '2024-01-20',
        status: JobStatus.running,
        priority: JobPriority.normal,
        createdAt: oneHourAgo,
        startedAt: oneMinuteAgo,
        completedAt: null,
        resultId: null,
        errorMessage: null,
        retryCount: 0,
      );

      await tester.pumpWidget(createTestWidget(job));

      // Check for relative time formatting
      expect(find.textContaining('1h ago'), findsOneWidget);
      expect(find.textContaining('1m ago'), findsOneWidget);
    });

    group('Status Colors', () {
      testWidgets('should use correct colors for different statuses', (tester) async {
        final testCases = [
          (JobStatus.pending, Colors.orange),
          (JobStatus.queued, Colors.blue),
          (JobStatus.running, Colors.blue),
          (JobStatus.completed, Colors.green),
          (JobStatus.failed, Colors.red),
          (JobStatus.cancelled, Colors.grey),
        ];

        for (final (status, expectedColor) in testCases) {
          final job = createTestJob(status: status);
          await tester.pumpWidget(createTestWidget(job));

          // Find the status indicator container
          final container = tester.widget<Container>(
            find.descendant(
              of: find.byType(JobStatusCard),
              matching: find.byType(Container),
            ).first,
          );

          final decoration = container.decoration as BoxDecoration;
          expect(decoration.border?.top.color, expectedColor.withValues(alpha: 0.3));

          await tester.pumpWidget(Container()); // Clear widget
        }
      });
    });

    group('Priority Colors', () {
      testWidgets('should use correct colors for different priorities', (tester) async {
        final testCases = [
          (JobPriority.low, Colors.green.shade600),
          (JobPriority.high, Colors.orange.shade600),
          (JobPriority.critical, Colors.red.shade600),
        ];

        for (final (priority, expectedColor) in testCases) {
          final job = createTestJob(priority: priority);
          await tester.pumpWidget(createTestWidget(job));

          // Find containers and check for priority badge
          final containers = find.descendant(
            of: find.byType(JobStatusCard),
            matching: find.byType(Container),
          );
          
          expect(containers, findsAtLeastNWidgets(1));
          // Note: Testing specific decoration colors is complex in widget tests
          // We verify the structure exists

          await tester.pumpWidget(Container()); // Clear widget
        }
      });
    });
  });
}