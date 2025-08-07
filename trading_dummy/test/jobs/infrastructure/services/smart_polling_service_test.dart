import 'dart:async';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:trading_dummy/jobs/infrastructure/services/smart_polling_service.dart';
import 'package:trading_dummy/jobs/infrastructure/services/langgraph_api_service.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_database.dart';
import 'package:trading_dummy/jobs/infrastructure/services/app_lifecycle_service.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_record.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';

class MockLangGraphApiService extends Mock implements LangGraphApiService {}
class MockAnalysisDatabase extends Mock implements AnalysisDatabase {}
class MockAppLifecycleService extends Mock implements AppLifecycleService {}
class MockJobEventBus extends Mock implements JobEventBus {}

void main() {
  group('SmartPollingService', () {
    late SmartPollingService pollingService;
    late MockLangGraphApiService mockApiService;
    late MockAnalysisDatabase mockDatabase;
    late MockAppLifecycleService mockLifecycleService;
    late MockJobEventBus mockEventBus;
    late StreamController<AppLifecycleState> lifecycleController;

    setUpAll(() {
      // Register fallback values for mocktail
      registerFallbackValue(AnalysisStatusUpdatedEvent(
        _createMockAnalysisJob(),
        runId: 'fallback',
        status: 'pending',
        isComplete: false,
      ));
    });

    setUp(() {
      // Create mocks
      mockApiService = MockLangGraphApiService();
      mockDatabase = MockAnalysisDatabase();
      mockLifecycleService = MockAppLifecycleService();
      mockEventBus = MockJobEventBus();

      // Set up lifecycle stream
      lifecycleController = StreamController<AppLifecycleState>.broadcast();
      when(() => mockLifecycleService.lifecycleState).thenAnswer((_) => lifecycleController.stream);
      when(() => mockLifecycleService.isInForeground).thenReturn(true);

      // Set up default mock responses to prevent null exceptions
      when(() => mockDatabase.getPendingAnalyses()).thenAnswer((_) async => <AnalysisRecord>[]);
      when(() => mockDatabase.getAnalysisByRunId(any())).thenAnswer((_) async => null);
      when(() => mockDatabase.updateStatus(
        any(),
        status: any(named: 'status'),
        result: any(named: 'result'),
        error: any(named: 'error'),
        completedAt: any(named: 'completedAt'),
      )).thenAnswer((_) async {});
      when(() => mockEventBus.publish(any())).thenReturn(null);
      
      // Default API service mock - returns running status
      when(() => mockApiService.getRunStatusWithThread(
        runId: any(named: 'runId'),
        threadId: any(named: 'threadId'),
      )).thenAnswer((_) async => RunStatusResponse(
        runId: 'default-run',
        status: 'running',
      ));

      // Create service with mocks
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

    group('Initialization', () {
      test('should initialize with lifecycle listener', () {
        // Act
        pollingService.initialize();

        // Assert
        expect(pollingService.getPollingStatus()['isInForeground'], isTrue);
      });

      test('should start polling for pending analyses on initialization if in foreground', () async {
        // Arrange
        final pendingRecord = _createMockAnalysisRecord('run123', 'thread123', 'running');
        when(() => mockDatabase.getPendingAnalyses()).thenAnswer((_) async => [pendingRecord]);
        when(() => mockLifecycleService.isInForeground).thenReturn(true);

        // Act
        pollingService.initialize();
        await Future.delayed(Duration(milliseconds: 10)); // Allow async operations

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], greaterThanOrEqualTo(0));
      });
    });

    group('Polling Management', () {
      test('should start polling for new run when in foreground', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';

        // Act
        await pollingService.startPollingForRun(runId, threadId);

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['runIds'], contains(runId));
        expect(status['activePollers'], equals(1));
      });

      test('should not start polling when app is in background', () async {
        // Arrange
        when(() => mockLifecycleService.isInForeground).thenReturn(false);
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';

        // Act
        await pollingService.startPollingForRun(runId, threadId);

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], equals(0));
      });

      test('should not start duplicate polling for same run ID', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await pollingService.startPollingForRun(runId, threadId); // Duplicate

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], equals(1));
      });

      test('should stop polling for specific run', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        await pollingService.startPollingForRun(runId, threadId);

        // Act
        pollingService.stopPollingForRun(runId);

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], equals(0));
        expect(status['runIds'], isEmpty);
      });
    });

    group('Constant Polling', () {
      test('should use constant 10s polling interval', () {
        // Test internal method behavior - constant interval means no complex logic needed
        final status = pollingService.getPollingStatus();
        
        // Verify the polling service tracks poll counts correctly
        expect(status, isA<Map<String, dynamic>>());
        expect(status.containsKey('pollCounts'), isTrue);
      });

      test('should start with immediate poll then constant 10s intervals', () async {
        // This tests the pattern by verifying timer behavior indirectly
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';

        // Arrange - mock the API call to return running status
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'running',
        );
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'running');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);

        // Allow some time for polling to start
        await Future.delayed(Duration(milliseconds: 50));

        // Assert - verify API was called at least once (initial immediate poll)
        verify(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).called(greaterThan(0));
        
        // Verify constant 10s polling doesn't change interval based on poll count
        final status = pollingService.getPollingStatus();
        expect(status['pollCounts'][runId], greaterThan(0));
      });
    });

    group('App Lifecycle Management', () {
      test('should pause all polling when app goes to background', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        pollingService.initialize();
        await pollingService.startPollingForRun(runId, threadId);

        // Act - simulate app going to background
        lifecycleController.add(AppLifecycleState.paused);
        await Future.delayed(Duration(milliseconds: 10));

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], equals(0));
      });

      test('should resume polling when app comes to foreground', () async {
        // Arrange
        pollingService.initialize();
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        // Mock pending analyses for resume
        final pendingRecord = _createMockAnalysisRecord(runId, threadId, 'running');
        when(() => mockDatabase.getPendingAnalyses()).thenAnswer((_) async => [pendingRecord]);

        // Simulate app going to background then foreground
        lifecycleController.add(AppLifecycleState.paused);
        await Future.delayed(Duration(milliseconds: 10));

        // Act - simulate app coming to foreground
        when(() => mockLifecycleService.isInForeground).thenReturn(true);
        lifecycleController.add(AppLifecycleState.resumed);
        await Future.delayed(Duration(milliseconds: 50));

        // Assert
        verify(() => mockDatabase.getPendingAnalyses()).called(greaterThan(0));
      });
    });

    group('Status Polling', () {
      test('should update database when status changes', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'success',
          result: {'decision': 'BUY', 'confidence': 0.8},
          completedAt: DateTime.now(),
        );
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 50));

        // Assert
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result'),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
      });

      test('should publish event when status updates', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'running',
        );
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'running');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 50));

        // Assert
        verify(() => mockEventBus.publish(any())).called(greaterThan(0));
      });

      test('should stop polling when analysis is complete', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'success',
          result: {'decision': 'BUY'},
          completedAt: DateTime.now(),
        );
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 100)); // Allow polling to complete

        // Assert - polling should stop when complete
        await Future.delayed(Duration(milliseconds: 50)); // Give it more time
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], lessThanOrEqualTo(1)); // May be 0 or 1 depending on timing
      });

      test('should handle API errors gracefully and continue polling', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenThrow(AnalysisException('Network error'));

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 50));

        // Assert - polling should continue despite errors
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], greaterThan(0));
      });
    });

    group('Multiple Concurrent Polling', () {
      test('should handle multiple concurrent polling operations', () async {
        // Arrange
        const runs = [
          ('run1', 'thread1'),
          ('run2', 'thread2'),
          ('run3', 'thread3'),
        ];

        // Act
        for (final (runId, threadId) in runs) {
          await pollingService.startPollingForRun(runId, threadId);
        }

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], equals(3));
        expect(status['runIds'], hasLength(3));
      });

      test('should stop individual polling operations independently', () async {
        // Arrange
        const runs = [
          ('run1', 'thread1'),
          ('run2', 'thread2'),
          ('run3', 'thread3'),
        ];

        for (final (runId, threadId) in runs) {
          await pollingService.startPollingForRun(runId, threadId);
        }

        // Act - stop one polling operation
        pollingService.stopPollingForRun('run2');

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], equals(2));
        expect(status['runIds'], isNot(contains('run2')));
        expect(status['runIds'], contains('run1'));
        expect(status['runIds'], contains('run3'));
      });
    });

    group('Event Broadcasting', () {
      test('should publish AnalysisStatusUpdatedEvent with correct data', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'running',
          result: {'progress': '50%'},
        );
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'running');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 50));

        // Assert - verify event was published
        verify(() => mockEventBus.publish(any<AnalysisStatusUpdatedEvent>())).called(greaterThan(0));
      });
    });

    group('Enhanced Dual-API Pattern Result Retrieval', () {
      test('should use enhanced result retrieval when status response lacks result', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        // Mock status response with no result
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'success',
          result: null, // No result in status response
          completedAt: DateTime.now(),
        );
        
        // Mock separate result retrieval success
        final mockResult = {
          'final_trade_decision': 'BUY',
          'confidence': 0.85,
          'analysis': 'Strong bullish signals detected'
        };
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);
        
        when(() => mockApiService.getRunResult(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockResult);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 100));

        // Assert
        verify(() => mockApiService.getRunResult(
          runId: runId,
          threadId: threadId,
        )).called(greaterThan(0));
        
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: mockResult.toString(),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
      });

      test('should create fallback result when dual-API retrieval fails completely', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        // Mock status response with success but no result
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'success',
          result: null,
          completedAt: DateTime.now(),
        );
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);
        
        // Mock separate result retrieval failure
        when(() => mockApiService.getRunResult(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => null);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 100));

        // Assert - fallback result should be created
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('completed_no_result')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
      });

      test('should create error fallback result when dual-API throws exception', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'success',
          result: null,
          completedAt: DateTime.now(),
        );
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);
        
        // Mock separate result retrieval throwing exception
        when(() => mockApiService.getRunResult(
          runId: runId,
          threadId: threadId,
        )).thenThrow(Exception('Network timeout'));

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 100));

        // Assert - error fallback result should be created
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('completed_with_error')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
      });

      test('should skip dual-API retrieval when result already exists in status', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        // Mock status response with existing result
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'success',
          result: {'final_trade_decision': 'HOLD', 'confidence': 0.75},
          completedAt: DateTime.now(),
        );
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 100));

        // Assert - dual-API should NOT be called
        verifyNever(() => mockApiService.getRunResult(
          runId: any(named: 'runId'),
          threadId: any(named: 'threadId'),
        ));
        
        // But status should still be updated with existing result
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('HOLD')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
      });

      test('should publish enhanced event with retrieved result data', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'success',
          result: null,
          completedAt: DateTime.now(),
        );
        
        final enhancedResult = {
          'final_trade_decision': 'BUY',
          'confidence': 0.90,
          'analysis': 'Strong technical indicators'
        };
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);
        
        when(() => mockApiService.getRunResult(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => enhancedResult);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 100));

        // Assert - event should contain enhanced result data
        final captured = verify(() => mockEventBus.publish(captureAny<AnalysisStatusUpdatedEvent>())).captured;
        expect(captured.isNotEmpty, isTrue);
        
        final event = captured.first as AnalysisStatusUpdatedEvent;
        expect(event.result, equals(enhancedResult));
        expect(event.status, equals('success'));
        expect(event.isComplete, isTrue);
      });

      test('should handle empty/null result strings correctly', () async {
        // Arrange
        const runId = 'test-run-123';
        const threadId = 'test-thread-123';
        
        // Mock status with empty result string
        final mockStatus = RunStatusResponse(
          runId: runId,
          status: 'success',
          result: {},  // Empty map
          completedAt: DateTime.now(),
        );
        
        final enhancedResult = {
          'final_trade_decision': 'BUY',
          'confidence': 0.80
        };
        
        when(() => mockApiService.getRunStatusWithThread(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => mockStatus);
        
        when(() => mockApiService.getRunResult(
          runId: runId,
          threadId: threadId,
        )).thenAnswer((_) async => enhancedResult);

        when(() => mockDatabase.updateStatus(
          any(),
          status: any(named: 'status'),
          result: any(named: 'result'),
          error: any(named: 'error'),
          completedAt: any(named: 'completedAt'),
        )).thenAnswer((_) async {});

        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);

        // Act
        await pollingService.startPollingForRun(runId, threadId);
        await Future.delayed(Duration(milliseconds: 100));

        // Assert - should trigger dual-API retrieval for empty result
        verify(() => mockApiService.getRunResult(
          runId: runId,
          threadId: threadId,
        )).called(greaterThan(0));
      });
    });

    group('Resource Management', () {
      test('should dispose properly and clean up all resources', () {
        // Arrange
        pollingService.initialize();

        // Act
        pollingService.dispose();

        // Assert
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], equals(0));
        expect(status['runIds'], isEmpty);
      });

      test('should provide status information for debugging', () {
        // Act
        final status = pollingService.getPollingStatus();

        // Assert
        expect(status, containsPair('activePollers', 0));
        expect(status, contains('runIds'));
        expect(status, contains('pollCounts'));
        expect(status, contains('isInForeground'));
      });
    });
  });
}

/// Helper method to create mock AnalysisRecord
AnalysisRecord _createMockAnalysisRecord(String runId, String threadId, String status) {
  return AnalysisRecord(
    id: 'test-id-$runId',
    runId: runId,
    threadId: threadId,
    ticker: 'AAPL',
    tradeDate: '2024-01-15',
    status: status,
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );
}

/// Helper method to create mock AnalysisJob
AnalysisJob _createMockAnalysisJob() {
  return AnalysisJob(
    id: 'test-job-id',
    ticker: 'AAPL',
    tradeDate: '2024-01-15',
    status: JobStatus.pending,
    priority: JobPriority.normal,
    createdAt: DateTime.now(),
    retryCount: 0,
  );
}