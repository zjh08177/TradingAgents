import 'dart:async';
import 'dart:convert';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
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

class MockAnalysisDatabase extends Mock implements AnalysisDatabase {}
class MockAppLifecycleService extends Mock implements AppLifecycleService {}
class MockJobEventBus extends Mock implements JobEventBus {}

/// Integration test for the complete dual-API pattern implementation
/// Tests the full flow: polling → dual-API result retrieval → database save → UI events
void main() {
  group('LangGraph Dual-API Pattern Integration Tests', () {
    late SmartPollingService pollingService;
    late LangGraphApiService apiService;
    late MockClient mockHttpClient;
    late MockAnalysisDatabase mockDatabase;
    late MockAppLifecycleService mockLifecycleService;
    late MockJobEventBus mockEventBus;
    late StreamController<AppLifecycleState> lifecycleController;

    const testBaseUrl = 'https://api.test.com';
    const testApiKey = 'test-api-key';
    const testAssistantId = 'test-assistant';

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
      // Reset singleton for testing
      LangGraphApiService.reset();
      
      // Create mocks
      mockDatabase = MockAnalysisDatabase();
      mockLifecycleService = MockAppLifecycleService();
      mockEventBus = MockJobEventBus();
      
      // Set up lifecycle stream
      lifecycleController = StreamController<AppLifecycleState>.broadcast();
      when(() => mockLifecycleService.lifecycleState).thenAnswer((_) => lifecycleController.stream);
      when(() => mockLifecycleService.isInForeground).thenReturn(true);
      
      // Set up default mock responses
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
    });

    tearDown(() {
      pollingService.dispose();
      LangGraphApiService.reset();
      lifecycleController.close();
    });

    group('Strategy 1: Direct Run Output Success', () {
      test('should complete full flow with direct run output', () async {
        // Arrange: Mock HTTP responses for successful direct result retrieval
        const runId = 'run-123';
        const threadId = 'thread-456';
        
        int httpCallCount = 0;
        mockHttpClient = MockClient((request) async {
          httpCallCount++;
          
          // Status polling call - success with result
          if (request.url.toString().contains('/runs/$runId') && !request.url.toString().contains('/events')) {
            return http.Response(
              jsonEncode({
                'run_id': runId,
                'status': 'success',
                'output': {
                  'final_trade_decision': 'BUY',
                  'confidence': 0.85,
                  'analysis': 'Strong bullish momentum detected',
                }
              }),
              200,
            );
          }
          
          return http.Response('Not found', 404);
        });
        
        // Create services
        apiService = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockHttpClient,
        );
        
        pollingService = SmartPollingService(
          apiService: apiService,
          database: mockDatabase,
          lifecycleService: mockLifecycleService,
          eventBus: mockEventBus,
        );
        
        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);
        
        // Act: Start polling
        await pollingService.onAnalysisSubmitted(runId, threadId);
        await Future.delayed(Duration(milliseconds: 200));
        
        // Assert: Verify complete flow
        expect(httpCallCount, greaterThan(0));
        
        // Verify database was updated with result
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('BUY')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
        
        // Verify event was published with result data
        final captured = verify(() => mockEventBus.publish(captureAny<AnalysisStatusUpdatedEvent>())).captured;
        expect(captured.isNotEmpty, isTrue);
        
        final event = captured.first as AnalysisStatusUpdatedEvent;
        expect(event.status, equals('success'));
        expect(event.isComplete, isTrue);
        expect(event.result, isNotNull);
        expect(event.result.toString(), contains('BUY'));
        
        // Verify polling stopped (since analysis is complete)
        final status = pollingService.getPollingStatus();
        expect(status['activePollers'], lessThanOrEqualTo(1));
      });
    });

    group('Strategy 2: Thread State Fallback Success', () {
      test('should succeed with thread state when run output fails', () async {
        // Arrange: Mock HTTP responses
        const runId = 'run-123';
        const threadId = 'thread-456';
        
        int httpCallCount = 0;
        mockHttpClient = MockClient((request) async {
          httpCallCount++;
          
          // Status polling call - success but no output
          if (request.url.toString().contains('/runs/$runId') && !request.url.toString().contains('/state') && !request.url.toString().contains('/events')) {
            return http.Response(
              jsonEncode({
                'run_id': runId,
                'status': 'success',
                // No output field
              }),
              200,
            );
          }
          
          // Strategy 1: Same as status call above (no result)
          if (request.url.toString().contains('/runs/$runId') && !request.url.toString().contains('/state') && !request.url.toString().contains('/events')) {
            return http.Response(
              jsonEncode({'run_id': runId, 'status': 'success'}),
              200,
            );
          }
          
          // Strategy 2: Thread state - success
          if (request.url.toString().contains('/state')) {
            return http.Response(
              jsonEncode({
                'values': {
                  'final_trade_decision': 'SELL',
                  'confidence': 0.75,
                  'risk_assessment': 'Moderate bearish trend',
                }
              }),
              200,
            );
          }
          
          return http.Response('Not found', 404);
        });
        
        // Create services
        apiService = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockHttpClient,
        );
        
        pollingService = SmartPollingService(
          apiService: apiService,
          database: mockDatabase,
          lifecycleService: mockLifecycleService,
          eventBus: mockEventBus,
        );
        
        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);
        
        // Act: Start polling
        await pollingService.onAnalysisSubmitted(runId, threadId);
        await Future.delayed(Duration(milliseconds: 300));
        
        // Assert: Verify fallback strategy worked
        expect(httpCallCount, greaterThan(1)); // Multiple API calls for fallback
        
        // Verify database was updated with thread state result
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('SELL')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
        
        // Verify event contains thread state data
        final captured = verify(() => mockEventBus.publish(captureAny<AnalysisStatusUpdatedEvent>())).captured;
        expect(captured.isNotEmpty, isTrue);
        
        final event = captured.first as AnalysisStatusUpdatedEvent;
        expect(event.result.toString(), contains('SELL'));
        expect(event.result.toString(), contains('bearish'));
      });
    });

    group('Strategy 3: Thread Messages Fallback Success', () {
      test('should succeed with thread messages when state fails', () async {
        // Arrange: Mock HTTP responses
        const runId = 'run-123';
        const threadId = 'thread-456';
        
        int httpCallCount = 0;
        mockHttpClient = MockClient((request) async {
          httpCallCount++;
          
          // Status polling call - success but no output
          if (request.url.toString().contains('/runs/$runId') && 
              !request.url.toString().contains('/state') && 
              !request.url.toString().contains('/events') &&
              !request.url.toString().contains('/messages')) {
            return http.Response(
              jsonEncode({'run_id': runId, 'status': 'success'}),
              200,
            );
          }
          
          // Strategy 1 & 2: Fail
          if (request.url.toString().contains('/state')) {
            return http.Response('State not found', 404);
          }
          
          // Strategy 3: Thread messages - success with JSON content
          if (request.url.toString().contains('/messages')) {
            return http.Response(
              jsonEncode([
                {
                  'role': 'user',
                  'content': 'Analyze AAPL for 2024-01-15'
                },
                {
                  'role': 'assistant',
                  'content': [
                    {
                      'type': 'text',
                      'text': '{"final_trade_decision": "HOLD", "confidence": 0.65, "reasoning": "Mixed signals in technical indicators"}'
                    }
                  ]
                }
              ]),
              200,
            );
          }
          
          return http.Response('Not found', 404);
        });
        
        // Create services
        apiService = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockHttpClient,
        );
        
        pollingService = SmartPollingService(
          apiService: apiService,
          database: mockDatabase,
          lifecycleService: mockLifecycleService,
          eventBus: mockEventBus,
        );
        
        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);
        
        // Act: Start polling
        await pollingService.onAnalysisSubmitted(runId, threadId);
        await Future.delayed(Duration(milliseconds: 400));
        
        // Assert: Verify messages strategy worked
        expect(httpCallCount, greaterThan(2)); // Multiple fallback attempts
        
        // Verify database was updated with messages result
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('HOLD')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
        
        // Verify event contains parsed JSON from messages
        final captured = verify(() => mockEventBus.publish(captureAny<AnalysisStatusUpdatedEvent>())).captured;
        expect(captured.isNotEmpty, isTrue);
        
        final event = captured.first as AnalysisStatusUpdatedEvent;
        expect(event.result.toString(), contains('HOLD'));
        expect(event.result.toString(), contains('Mixed signals'));
      });
    });

    group('Strategy 4: Run History/Events Success', () {
      test('should succeed with run events when messages fail', () async {
        // Arrange: Mock HTTP responses
        const runId = 'run-123';
        const threadId = 'thread-456';
        
        int httpCallCount = 0;
        mockHttpClient = MockClient((request) async {
          httpCallCount++;
          
          // Status polling call - success but no output
          if (request.url.toString().contains('/runs/$runId') && 
              !request.url.toString().contains('/state') && 
              !request.url.toString().contains('/events') &&
              !request.url.toString().contains('/messages')) {
            return http.Response(
              jsonEncode({'run_id': runId, 'status': 'success'}),
              200,
            );
          }
          
          // Strategies 1-3: All fail
          if (request.url.toString().contains('/state') || 
              request.url.toString().contains('/messages')) {
            return http.Response('Not found', 404);
          }
          
          // Strategy 4: Run events - success
          if (request.url.toString().contains('/events')) {
            return http.Response(
              jsonEncode([
                {
                  'event': 'on_run_start',
                  'data': {'status': 'starting'}
                },
                {
                  'event': 'on_agent_action',
                  'data': {'step': 'analysis'}
                },
                {
                  'event': 'on_run_end',
                  'data': {
                    'output': {
                      'final_trade_decision': 'BUY_STRONG',
                      'confidence': 0.95,
                      'urgency': 'high',
                      'target_price': 180.5
                    }
                  }
                }
              ]),
              200,
            );
          }
          
          return http.Response('Not found', 404);
        });
        
        // Create services
        apiService = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockHttpClient,
        );
        
        pollingService = SmartPollingService(
          apiService: apiService,
          database: mockDatabase,
          lifecycleService: mockLifecycleService,
          eventBus: mockEventBus,
        );
        
        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);
        
        // Act: Start polling
        await pollingService.onAnalysisSubmitted(runId, threadId);
        await Future.delayed(Duration(milliseconds: 500));
        
        // Assert: Verify events strategy worked
        expect(httpCallCount, greaterThan(3)); // All fallback attempts
        
        // Verify database was updated with events result
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('BUY_STRONG')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
        
        // Verify event contains run events data
        final captured = verify(() => mockEventBus.publish(captureAny<AnalysisStatusUpdatedEvent>())).captured;
        expect(captured.isNotEmpty, isTrue);
        
        final event = captured.first as AnalysisStatusUpdatedEvent;
        expect(event.result.toString(), contains('BUY_STRONG'));
        expect(event.result.toString(), contains('180.5'));
      });
    });

    group('Fallback Result Creation', () {
      test('should create fallback result when all strategies fail', () async {
        // Arrange: Mock all HTTP calls to fail
        const runId = 'run-123';
        const threadId = 'thread-456';
        
        mockHttpClient = MockClient((request) async {
          // Status polling - success but no result
          if (request.url.toString().contains('/runs/$runId') && 
              !request.url.toString().contains('/state') && 
              !request.url.toString().contains('/events') &&
              !request.url.toString().contains('/messages')) {
            return http.Response(
              jsonEncode({'run_id': runId, 'status': 'success'}),
              200,
            );
          }
          
          // All other strategies fail
          return http.Response('Not found', 404);
        });
        
        // Create services
        apiService = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockHttpClient,
        );
        
        pollingService = SmartPollingService(
          apiService: apiService,
          database: mockDatabase,
          lifecycleService: mockLifecycleService,
          eventBus: mockEventBus,
        );
        
        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);
        
        // Act: Start polling
        await pollingService.onAnalysisSubmitted(runId, threadId);
        await Future.delayed(Duration(milliseconds: 600));
        
        // Assert: Verify fallback result was created
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('completed_no_result')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
        
        // Verify event indicates fallback scenario
        final captured = verify(() => mockEventBus.publish(captureAny<AnalysisStatusUpdatedEvent>())).captured;
        expect(captured.isNotEmpty, isTrue);
        
        final event = captured.first as AnalysisStatusUpdatedEvent;
        expect(event.result.toString(), contains('completed_no_result'));
        expect(event.result.toString(), contains('could not be retrieved'));
      });

      test('should create error fallback when dual-API throws exceptions', () async {
        // Arrange: Mock HTTP calls to throw exceptions
        const runId = 'run-123';
        const threadId = 'thread-456';
        
        mockHttpClient = MockClient((request) async {
          // Status polling - success but no result
          if (request.url.toString().contains('/runs/$runId') && 
              !request.url.toString().contains('/state') && 
              !request.url.toString().contains('/events') &&
              !request.url.toString().contains('/messages')) {
            return http.Response(
              jsonEncode({'run_id': runId, 'status': 'success'}),
              200,
            );
          }
          
          // All result retrieval strategies throw exceptions
          throw Exception('Network timeout during result retrieval');
        });
        
        // Create services
        apiService = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockHttpClient,
        );
        
        pollingService = SmartPollingService(
          apiService: apiService,
          database: mockDatabase,
          lifecycleService: mockLifecycleService,
          eventBus: mockEventBus,
        );
        
        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);
        
        // Act: Start polling
        await pollingService.onAnalysisSubmitted(runId, threadId);
        await Future.delayed(Duration(milliseconds: 600));
        
        // Assert: Verify error fallback result was created
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: contains('completed_with_error')),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
        
        // Verify event indicates error scenario
        final captured = verify(() => mockEventBus.publish(captureAny<AnalysisStatusUpdatedEvent>())).captured;
        expect(captured.isNotEmpty, isTrue);
        
        final event = captured.first as AnalysisStatusUpdatedEvent;
        expect(event.result.toString(), contains('completed_with_error'));
        expect(event.result.toString(), contains('Network timeout'));
      });
    });

    group('Real-World Scenario Testing', () {
      test('should handle realistic LangGraph API responses with run ID from logs', () async {
        // Arrange: Use real run ID from logs for testing
        const runId = '1f073d12-1030-6677-9a30-d739d108e227';
        const threadId = 'e8e9d596-25f6-4d72-af3d-ff13c901aa8f';
        
        int httpCallCount = 0;
        mockHttpClient = MockClient((request) async {
          httpCallCount++;
          
          // Simulate realistic LangGraph responses
          if (request.url.toString().contains('/runs/$runId')) {
            return http.Response(
              jsonEncode({
                'run_id': runId,
                'thread_id': threadId,
                'status': 'success',
                'created_at': '2024-08-07T14:32:29Z',
                'updated_at': '2024-08-07T14:35:45Z',
                'metadata': {
                  'assistant_id': 'trade-team-v1',
                  'user_id': 'test-user'
                },
                // No output field initially
              }),
              200,
            );
          }
          
          // Thread state retrieval
          if (request.url.toString().contains('/state')) {
            return http.Response(
              jsonEncode({
                'values': {
                  'market_report': {
                    'sector_analysis': 'Healthcare showing strength',
                    'market_sentiment': 'Bullish'
                  },
                  'technical_analysis': {
                    'rsi': 68.5,
                    'moving_averages': 'Golden cross pattern'
                  },
                  'final_trade_decision': 'BUY',
                  'confidence': 0.82,
                  'target_price': 175.0,
                  'stop_loss': 165.0,
                  'position_size': '2% of portfolio'
                }
              }),
              200,
            );
          }
          
          return http.Response('Not found', 404);
        });
        
        // Create services
        apiService = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockHttpClient,
        );
        
        pollingService = SmartPollingService(
          apiService: apiService,
          database: mockDatabase,
          lifecycleService: mockLifecycleService,
          eventBus: mockEventBus,
        );
        
        final mockRecord = _createMockAnalysisRecord(runId, threadId, 'success');
        when(() => mockDatabase.getAnalysisByRunId(runId)).thenAnswer((_) async => mockRecord);
        
        // Act: Start polling
        await pollingService.onAnalysisSubmitted(runId, threadId);
        await Future.delayed(Duration(milliseconds: 400));
        
        // Assert: Verify realistic scenario worked
        expect(httpCallCount, greaterThan(1));
        
        // Verify comprehensive result was saved
        verify(() => mockDatabase.updateStatus(
          runId,
          status: 'success',
          result: any(named: 'result', that: allOf([
            contains('BUY'),
            contains('175.0'),
            contains('Healthcare'),
            contains('Golden cross'),
          ])),
          completedAt: any(named: 'completedAt'),
        )).called(greaterThan(0));
        
        // Verify event contains comprehensive analysis data
        final captured = verify(() => mockEventBus.publish(captureAny<AnalysisStatusUpdatedEvent>())).captured;
        expect(captured.isNotEmpty, isTrue);
        
        final event = captured.first as AnalysisStatusUpdatedEvent;
        expect(event.result.toString(), contains('market_report'));
        expect(event.result.toString(), contains('technical_analysis'));
        expect(event.result.toString(), contains('target_price'));
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