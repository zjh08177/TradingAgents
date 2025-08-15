import 'dart:async';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:trading_dummy/jobs/infrastructure/services/smart_polling_service.dart';
import 'package:trading_dummy/jobs/infrastructure/services/langgraph_api_service.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_database.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_record.dart';
import 'package:trading_dummy/jobs/infrastructure/services/app_lifecycle_service.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';

// Mock classes
class MockLangGraphApiService extends Mock implements LangGraphApiService {}
class MockAnalysisDatabase extends Mock implements AnalysisDatabase {}
class MockAppLifecycleService extends Mock implements AppLifecycleService {}
class MockJobEventBus extends Mock implements JobEventBus {}
class FakeAnalysisJob extends Fake implements AnalysisJob {}
class FakeJobEvent extends Fake implements JobEvent {}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  
  late SmartPollingService pollingService;
  late MockLangGraphApiService mockApiService;
  late MockAnalysisDatabase mockDatabase;
  late MockAppLifecycleService mockLifecycleService;
  late MockJobEventBus mockEventBus;
  late StreamController<AppLifecycleState> lifecycleController;

  setUpAll(() {
    registerFallbackValue(FakeAnalysisJob());
    registerFallbackValue(FakeJobEvent());
  });

  setUp(() {
    mockApiService = MockLangGraphApiService();
    mockDatabase = MockAnalysisDatabase();
    mockLifecycleService = MockAppLifecycleService();
    mockEventBus = MockJobEventBus();
    lifecycleController = StreamController<AppLifecycleState>.broadcast();

    // Set up default mock responses
    when(() => mockLifecycleService.isInForeground).thenReturn(true);
    when(() => mockLifecycleService.lifecycleState).thenAnswer((_) => lifecycleController.stream);
    when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 0);
    when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => []);
    when(() => mockDatabase.getAnalysisByRunId(any())).thenAnswer((_) async => null);
    when(() => mockDatabase.updateStatus(
      any(),
      status: any(named: 'status'),
      result: any(named: 'result'),
      error: any(named: 'error'),
      completedAt: any(named: 'completedAt'),
    )).thenAnswer((_) async {});
    when(() => mockEventBus.publish(any())).thenReturn(null);

    pollingService = SmartPollingService(
      apiService: mockApiService,
      database: mockDatabase,
      lifecycleService: mockLifecycleService,
      eventBus: mockEventBus,
    );
  });

  tearDown(() {
    pollingService.dispose();
    lifecycleController.close();
  });

  group('Phase 2: Simplified Polling Service', () {
    group('Initialization', () {
      test('should check polling needed on initialization when in foreground', () async {
        // Arrange
        when(() => mockLifecycleService.isInForeground).thenReturn(true);
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 0);

        // Act
        pollingService.initialize();
        await Future.delayed(Duration(milliseconds: 100));

        // Assert
        verify(() => mockDatabase.getRunningCount()).called(greaterThanOrEqualTo(1));
      });

      test('should not check polling when app is in background', () async {
        // Arrange
        when(() => mockLifecycleService.isInForeground).thenReturn(false);

        // Act
        pollingService.initialize();
        await Future.delayed(Duration(milliseconds: 100));

        // Assert
        verifyNever(() => mockDatabase.getRunningCount());
      });
    });

    group('Polling Decision Logic', () {
      test('should NOT start polling with 0 running tasks', () async {
        // Arrange
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 0);

        // Act
        await pollingService.checkPollingNeeded();

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['isPolling'], false);
        verify(() => mockDatabase.getRunningCount()).called(1);
        verifyNever(() => mockDatabase.getRunningAnalyses());
      });

      test('should START polling with 1 running task', () async {
        // Arrange
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 1);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => [
          _createRunningRecord('run1', 'thread1'),
        ]);

        // Act
        await pollingService.checkPollingNeeded();
        await Future.delayed(Duration(milliseconds: 100));

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['isPolling'], true);
        expect(status['hasTimer'], true);
      });

      test('should START polling with multiple running tasks', () async {
        // Arrange
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 3);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => [
          _createRunningRecord('run1', 'thread1'),
          _createRunningRecord('run2', 'thread2'),
          _createRunningRecord('run3', 'thread3'),
        ]);

        // Act
        await pollingService.checkPollingNeeded();
        await Future.delayed(Duration(milliseconds: 100));

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['isPolling'], true);
      });

      test('should STOP polling when running count drops to 0', () async {
        // Arrange: Start with running tasks
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 1);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => [
          _createRunningRecord('run1', 'thread1'),
        ]);
        
        await pollingService.checkPollingNeeded();
        expect(pollingService.getPollingStatus()['isPolling'], true);

        // Act: Simulate all tasks completing
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 0);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => []);
        
        await pollingService.checkPollingNeeded();

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['isPolling'], false);
        expect(status['hasTimer'], false);
      });
    });

    group('Task Polling', () {
      test('should poll only running tasks, not pending or completed', () async {
        // Arrange
        final runningTask = _createRunningRecord('run1', 'thread1');
        
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 1);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => [runningTask]);
        when(() => mockApiService.getRunStatusWithThread(
          runId: 'run1',
          threadId: 'thread1',
        )).thenAnswer((_) async => RunStatusResponse(
          runId: 'run1',
          status: 'running',
        ));

        // Act
        await pollingService.checkPollingNeeded();
        await Future.delayed(Duration(milliseconds: 200));

        // Assert
        verify(() => mockApiService.getRunStatusWithThread(
          runId: 'run1',
          threadId: 'thread1',
        )).called(greaterThanOrEqualTo(1));
      });

      test('should handle task completion and stop polling', () async {
        // Arrange
        final runningTask = _createRunningRecord('run1', 'thread1');
        
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 1);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => [runningTask]);
        when(() => mockApiService.getRunStatusWithThread(
          runId: 'run1',
          threadId: 'thread1',
        )).thenAnswer((_) async => RunStatusResponse(
          runId: 'run1',
          status: 'success',
          result: {'decision': 'BUY'},
        ));

        // Act
        await pollingService.checkPollingNeeded();
        await Future.delayed(Duration(milliseconds: 200));

        // Assert
        verify(() => mockDatabase.updateStatus(
          'run1',
          status: 'success',
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThanOrEqualTo(1));
      });

      test('should skip tasks with missing runId or threadId', () async {
        // Arrange
        final invalidTask = AnalysisRecord(
          id: 'invalid1',
          runId: null, // Missing runId
          threadId: 'thread1',
          ticker: 'AAPL',
          tradeDate: '2024-01-20',
          status: 'running',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 1);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => [invalidTask]);

        // Act
        await pollingService.checkPollingNeeded();
        await Future.delayed(Duration(milliseconds: 200));

        // Assert
        verifyNever(() => mockApiService.getRunStatusWithThread(
          runId: any(named: 'runId'),
          threadId: any(named: 'threadId'),
        ));
      });
    });

    group('Lifecycle Management', () {
      test('should pause polling when app goes to background', () async {
        // Arrange: Start polling
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 2);
        pollingService.initialize();
        await pollingService.checkPollingNeeded();
        expect(pollingService.getPollingStatus()['isPolling'], true);

        // Act: Simulate background
        lifecycleController.add(AppLifecycleState.paused);
        await Future.delayed(Duration(milliseconds: 100));

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['isPolling'], false);
      });

      test('should resume polling when app returns to foreground', () async {
        // Arrange: Background with running tasks
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 1);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => [
          _createRunningRecord('run1', 'thread1'),
        ]);
        when(() => mockLifecycleService.isInForeground).thenReturn(false);
        
        pollingService.initialize();

        // Act: Simulate foreground
        when(() => mockLifecycleService.isInForeground).thenReturn(true);
        lifecycleController.add(AppLifecycleState.resumed);
        await Future.delayed(Duration(milliseconds: 200));

        // Assert
        verify(() => mockDatabase.getRunningCount()).called(greaterThanOrEqualTo(1));
      });
    });

    group('onAnalysisSubmitted', () {
      test('should trigger polling check when new analysis is submitted', () async {
        // Arrange
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 1);

        // Act
        await pollingService.onAnalysisSubmitted('new-run', 'new-thread');

        // Assert
        verify(() => mockDatabase.getRunningCount()).called(1);
      });
    });

    group('Error Handling', () {
      test('should continue polling despite API errors', () async {
        // Arrange
        final task = _createRunningRecord('run1', 'thread1');
        
        when(() => mockDatabase.getRunningCount()).thenAnswer((_) async => 1);
        when(() => mockDatabase.getRunningAnalyses()).thenAnswer((_) async => [task]);
        when(() => mockApiService.getRunStatusWithThread(
          runId: any(named: 'runId'),
          threadId: any(named: 'threadId'),
        )).thenThrow(Exception('API Error'));

        // Act
        await pollingService.checkPollingNeeded();
        await Future.delayed(Duration(milliseconds: 200));

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['isPolling'], true); // Should still be polling
      });

      test('should handle database errors gracefully', () async {
        // Arrange
        when(() => mockDatabase.getRunningCount()).thenThrow(Exception('DB Error'));

        // Act & Assert (should not throw)
        await pollingService.checkPollingNeeded();
        
        final status = pollingService.getPollingStatus();
        expect(status['isPolling'], false);
      });
    });
  });
}

// Helper function to create test records
AnalysisRecord _createRunningRecord(String runId, String threadId) {
  return AnalysisRecord(
    id: 'id-$runId',
    runId: runId,
    threadId: threadId,
    ticker: 'AAPL',
    tradeDate: '2024-01-20',
    status: 'running',
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );
}

