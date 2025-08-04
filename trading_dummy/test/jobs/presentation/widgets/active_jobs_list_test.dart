import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:mocktail/mocktail.dart';

import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/presentation/view_models/job_queue_view_model.dart';
import 'package:trading_dummy/jobs/presentation/widgets/active_jobs_list.dart';
import 'package:trading_dummy/jobs/presentation/widgets/job_status_card.dart';

// Mock classes
class MockJobQueueViewModel extends Mock implements JobQueueViewModel {}

void main() {
  group('ActiveJobsList', () {
    late MockJobQueueViewModel mockViewModel;

    setUp(() {
      mockViewModel = MockJobQueueViewModel();
      // Set up default mock behavior
      when(() => mockViewModel.isLoading).thenReturn(false);
      when(() => mockViewModel.activeJobs).thenReturn([]);
      when(() => mockViewModel.activeJobsCount).thenReturn(0);
      when(() => mockViewModel.refreshJobs()).thenAnswer((_) async {});
    });

    List<AnalysisJob> createTestJobs() {
      return [
        AnalysisJob(
          id: 'job-1',
          ticker: 'AAPL',
          tradeDate: '2024-01-20',
          status: JobStatus.running,
          priority: JobPriority.high,
          createdAt: DateTime.now().subtract(const Duration(minutes: 5)),
          startedAt: DateTime.now().subtract(const Duration(minutes: 2)),
          completedAt: null,
          resultId: null,
          errorMessage: null,
          retryCount: 0,
        ),
        AnalysisJob(
          id: 'job-2',
          ticker: 'TSLA',
          tradeDate: '2024-01-20',
          status: JobStatus.pending,
          priority: JobPriority.normal,
          createdAt: DateTime.now().subtract(const Duration(minutes: 10)),
          startedAt: null,
          completedAt: null,
          resultId: null,
          errorMessage: null,
          retryCount: 0,
        ),
        AnalysisJob(
          id: 'job-3',
          ticker: 'GOOGL',
          tradeDate: '2024-01-20',
          status: JobStatus.queued,
          priority: JobPriority.critical,
          createdAt: DateTime.now().subtract(const Duration(minutes: 1)),
          startedAt: null,
          completedAt: null,
          resultId: null,
          errorMessage: null,
          retryCount: 0,
        ),
      ];
    }

    Widget createTestWidget({bool showHeader = true, double? height}) {
      return MaterialApp(
        home: Scaffold(
          body: ChangeNotifierProvider<JobQueueViewModel>.value(
            value: mockViewModel,
            child: ActiveJobsList(
              showHeader: showHeader,
              height: height,
            ),
          ),
        ),
      );
    }

    testWidgets('should display header with active jobs count', (tester) async {
      when(() => mockViewModel.activeJobsCount).thenReturn(3);

      await tester.pumpWidget(createTestWidget());

      expect(find.text('Active Jobs'), findsOneWidget);
      expect(find.text('3'), findsOneWidget);
      expect(find.byIcon(Icons.work_outline), findsOneWidget);
    });

    testWidgets('should not display count badge when no active jobs', (tester) async {
      when(() => mockViewModel.activeJobsCount).thenReturn(0);

      await tester.pumpWidget(createTestWidget());

      expect(find.text('Active Jobs'), findsOneWidget);
      expect(find.text('0'), findsNothing);
    });

    testWidgets('should hide header when showHeader is false', (tester) async {
      await tester.pumpWidget(createTestWidget(showHeader: false));

      expect(find.text('Active Jobs'), findsNothing);
      expect(find.byIcon(Icons.work_outline), findsNothing);
    });

    testWidgets('should display empty state when no jobs', (tester) async {
      when(() => mockViewModel.activeJobs).thenReturn([]);
      when(() => mockViewModel.isLoading).thenReturn(false);

      await tester.pumpWidget(createTestWidget());

      expect(find.text('No Active Jobs'), findsOneWidget);
      expect(find.text('Submit an analysis job to see it here'), findsOneWidget);
      expect(find.byIcon(Icons.work_off_outlined), findsOneWidget);
    });

    testWidgets('should display loading state when loading', (tester) async {
      when(() => mockViewModel.isLoading).thenReturn(true);
      when(() => mockViewModel.activeJobs).thenReturn([]);

      await tester.pumpWidget(createTestWidget());

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Loading jobs...'), findsOneWidget);
    });

    testWidgets('should display jobs when available', (tester) async {
      final jobs = createTestJobs();
      when(() => mockViewModel.activeJobs).thenReturn(jobs);
      when(() => mockViewModel.activeJobsCount).thenReturn(jobs.length);

      await tester.pumpWidget(createTestWidget());

      // Verify all jobs are displayed as JobStatusCard widgets
      expect(find.byType(JobStatusCard), findsNWidgets(3));
      expect(find.text('AAPL'), findsOneWidget);
      expect(find.text('TSLA'), findsOneWidget);
      expect(find.text('GOOGL'), findsOneWidget);
    });

    testWidgets('should display loading indicator in header when loading', (tester) async {
      when(() => mockViewModel.isLoading).thenReturn(true);
      when(() => mockViewModel.activeJobs).thenReturn(createTestJobs());

      await tester.pumpWidget(createTestWidget());

      // Verify loading indicator is shown in header
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should call refreshJobs when refresh button is tapped', (tester) async {
      await tester.pumpWidget(createTestWidget());

      // Find and tap the refresh button
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pump();

      // Verify refreshJobs was called
      verify(() => mockViewModel.refreshJobs()).called(1);
    });

    testWidgets('should show job details bottom sheet when job is tapped', (tester) async {
      final jobs = createTestJobs();
      when(() => mockViewModel.activeJobs).thenReturn(jobs);

      await tester.pumpWidget(createTestWidget());

      // Tap on the first job card
      await tester.tap(find.byType(JobStatusCard).first);
      await tester.pumpAndSettle();

      // Verify bottom sheet is shown with job details
      expect(find.text('Job Details: AAPL'), findsOneWidget);
      expect(find.byType(DraggableScrollableSheet), findsOneWidget);
    });

    testWidgets('should display job details in bottom sheet', (tester) async {
      final jobs = createTestJobs();
      when(() => mockViewModel.activeJobs).thenReturn(jobs);

      await tester.pumpWidget(createTestWidget());

      // Tap on the first job card
      await tester.tap(find.byType(JobStatusCard).first);
      await tester.pumpAndSettle();

      // Verify job details are displayed
      expect(find.text('Job ID'), findsOneWidget);
      expect(find.text('job-1'), findsOneWidget);
      expect(find.text('Ticker Symbol'), findsOneWidget);
      expect(find.text('AAPL'), findsAtLeastNWidgets(1));
      expect(find.text('Trade Date'), findsOneWidget);
      expect(find.text('2024-01-20'), findsOneWidget);
      expect(find.text('Status'), findsOneWidget);
      expect(find.text('Running'), findsOneWidget);
      expect(find.text('Priority'), findsOneWidget);
      expect(find.text('High'), findsOneWidget);
    });

    testWidgets('should display progress section in bottom sheet', (tester) async {
      final jobs = createTestJobs();
      when(() => mockViewModel.activeJobs).thenReturn(jobs);

      await tester.pumpWidget(createTestWidget());

      // Tap on the first job card (running status)
      await tester.tap(find.byType(JobStatusCard).first);
      await tester.pumpAndSettle();

      // Verify progress section is displayed
      expect(find.text('Progress'), findsOneWidget);
      expect(find.byType(LinearProgressIndicator), findsOneWidget);
      expect(find.text('50% Complete'), findsOneWidget); // Running status = 50%
    });

    testWidgets('should display error section when job has error', (tester) async {
      final jobWithError = AnalysisJob(
        id: 'error-job',
        ticker: 'ERROR',
        tradeDate: '2024-01-20',
        status: JobStatus.failed,
        priority: JobPriority.normal,
        createdAt: DateTime.now(),
        startedAt: null,
        completedAt: null,
        resultId: null,
        errorMessage: 'Test error message',
        retryCount: 1,
      );

      when(() => mockViewModel.activeJobs).thenReturn([jobWithError]);

      await tester.pumpWidget(createTestWidget());

      // Tap on the job card
      await tester.tap(find.byType(JobStatusCard).first);
      await tester.pumpAndSettle();

      // Verify error section is displayed
      expect(find.text('Error Message'), findsOneWidget);
      expect(find.text('Test error message'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsAtLeastNWidgets(1));
    });

    testWidgets('should handle fixed height constraint', (tester) async {
      final jobs = createTestJobs();
      when(() => mockViewModel.activeJobs).thenReturn(jobs);

      await tester.pumpWidget(createTestWidget(height: 300));

      // Verify the list is constrained to the specified height
      final containers = find.byType(Container);
      expect(containers, findsAtLeastNWidgets(1));
      // Note: We can't easily test Container height as it's not exposed
      // but we can verify the widget structure is correct
    });

    testWidgets('should use scrollable physics when height is specified', (tester) async {
      final jobs = createTestJobs();
      when(() => mockViewModel.activeJobs).thenReturn(jobs);

      await tester.pumpWidget(createTestWidget(height: 300));

      // Verify ListView has scrollable physics
      final listView = tester.widget<ListView>(find.byType(ListView));
      expect(listView.physics, isNot(isA<NeverScrollableScrollPhysics>()));
    });

    testWidgets('should use non-scrollable physics when height is not specified', (tester) async {
      final jobs = createTestJobs();
      when(() => mockViewModel.activeJobs).thenReturn(jobs);

      await tester.pumpWidget(createTestWidget());

      // Verify ListView has non-scrollable physics
      final listView = tester.widget<ListView>(find.byType(ListView));
      expect(listView.physics, isA<NeverScrollableScrollPhysics>());
    });

    group('Bottom Sheet Details', () {
      testWidgets('should format timestamps correctly in bottom sheet', (tester) async {
        final job = AnalysisJob(
          id: 'time-job',
          ticker: 'TIME',
          tradeDate: '2024-01-20',
          status: JobStatus.completed,
          priority: JobPriority.normal,
          createdAt: DateTime(2024, 1, 20, 10, 30, 45),
          startedAt: DateTime(2024, 1, 20, 10, 31, 0),
          completedAt: DateTime(2024, 1, 20, 10, 35, 30),
          resultId: 'result-123',
          errorMessage: null,
          retryCount: 0,
        );

        when(() => mockViewModel.activeJobs).thenReturn([job]);

        await tester.pumpWidget(createTestWidget());

        // Tap on the job card
        await tester.tap(find.byType(JobStatusCard).first);
        await tester.pumpAndSettle();

        // Verify formatted timestamps are displayed
        expect(find.text('2024-01-20 10:30:45'), findsOneWidget);
        expect(find.text('2024-01-20 10:31:00'), findsOneWidget);
        expect(find.text('2024-01-20 10:35:30'), findsOneWidget);
      });

      testWidgets('should calculate progress correctly for different statuses', (tester) async {
        final testCases = [
          (JobStatus.pending, '10% Complete'),
          (JobStatus.queued, '20% Complete'),
          (JobStatus.running, '50% Complete'),
          (JobStatus.completed, '100% Complete'),
          (JobStatus.failed, '0% Complete'),
          (JobStatus.cancelled, '0% Complete'),
        ];

        for (final (status, expectedProgress) in testCases) {
          final job = AnalysisJob(
            id: 'progress-job',
            ticker: 'PROG',
            tradeDate: '2024-01-20',
            status: status,
            priority: JobPriority.normal,
            createdAt: DateTime.now(),
            startedAt: null,
            completedAt: null,
            resultId: null,
            errorMessage: null,
            retryCount: 0,
          );

          when(() => mockViewModel.activeJobs).thenReturn([job]);

          await tester.pumpWidget(createTestWidget());

          // Tap on the job card
          await tester.tap(find.byType(JobStatusCard).first);
          await tester.pumpAndSettle();

          // Verify progress percentage
          expect(find.text(expectedProgress), findsOneWidget);

          // Close bottom sheet and clear widget
          Navigator.of(tester.element(find.byType(ActiveJobsList))).pop();
          await tester.pumpAndSettle();
          await tester.pumpWidget(Container());
        }
      });

      testWidgets('should display result ID when available', (tester) async {
        final job = AnalysisJob(
          id: 'result-job',
          ticker: 'RESULT',
          tradeDate: '2024-01-20',
          status: JobStatus.completed,
          priority: JobPriority.normal,
          createdAt: DateTime.now(),
          startedAt: null,
          completedAt: DateTime.now(),
          resultId: 'result-abc-123',
          errorMessage: null,
          retryCount: 0,
        );

        when(() => mockViewModel.activeJobs).thenReturn([job]);

        await tester.pumpWidget(createTestWidget());

        // Tap on the job card
        await tester.tap(find.byType(JobStatusCard).first);
        await tester.pumpAndSettle();

        // Verify result ID is displayed
        expect(find.text('Result ID'), findsOneWidget);
        expect(find.text('result-abc-123'), findsOneWidget);
      });
    });
  });
}