import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'dart:convert';
import 'package:trading_dummy/jobs/infrastructure/services/langgraph_api_service.dart';

void main() {
  group('LangGraphApiService', () {
    late LangGraphApiService service;
    late MockClient mockClient;
    
    const testBaseUrl = 'https://api.test.com';
    const testApiKey = 'test-api-key';
    const testAssistantId = 'test-assistant';
    
    setUp(() {
      // Reset singleton for testing
      LangGraphApiService.reset();
      mockClient = MockClient((request) async {
        return http.Response('', 404);
      });
    });
    
    tearDown(() {
      LangGraphApiService.reset();
    });
    
    group('startAnalysis', () {
      test('should successfully start analysis', () async {
        final threadId = 'thread-123';
        final runId = 'run-456';
        
        int callCount = 0;
        mockClient = MockClient((request) async {
          callCount++;
          
          // First call: create thread
          if (callCount == 1) {
            expect(request.url.toString(), '$testBaseUrl/threads');
            expect(request.method, 'POST');
            expect(request.headers['X-Api-Key'], testApiKey);
            
            return http.Response(
              jsonEncode({'thread_id': threadId}),
              200,
            );
          }
          
          // Second call: create run
          if (callCount == 2) {
            expect(request.url.toString(), '$testBaseUrl/threads/$threadId/runs');
            expect(request.method, 'POST');
            expect(request.headers['X-Api-Key'], testApiKey);
            
            final body = jsonDecode(request.body);
            expect(body['assistant_id'], testAssistantId);
            expect(body['input']['company_of_interest'], 'AAPL');
            expect(body['input']['trade_date'], '2024-01-15');
            
            return http.Response(
              jsonEncode({
                'run_id': runId,
                'status': 'pending',
              }),
              200,
            );
          }
          
          return http.Response('', 404);
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final response = await service.startAnalysis(
          ticker: 'AAPL',
          tradeDate: '2024-01-15',
        );
        
        expect(response.runId, runId);
        expect(response.threadId, threadId);
        expect(response.status, 'pending');
        expect(response.createdAt, isA<DateTime>());
        expect(callCount, 2);
      });
      
      test('should handle thread creation failure', () async {
        mockClient = MockClient((request) async {
          return http.Response(
            jsonEncode({'error': 'API key invalid'}),
            401,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        expect(
          () => service.startAnalysis(ticker: 'AAPL', tradeDate: '2024-01-15'),
          throwsA(isA<AnalysisException>()
            .having((e) => e.message, 'message', contains('Failed to start analysis'))),
        );
      });
      
      test('should handle run creation failure', () async {
        int callCount = 0;
        mockClient = MockClient((request) async {
          callCount++;
          
          // First call: create thread successfully
          if (callCount == 1) {
            return http.Response(
              jsonEncode({'thread_id': 'thread-123'}),
              200,
            );
          }
          
          // Second call: fail to create run
          return http.Response(
            jsonEncode({'error': 'Invalid parameters'}),
            400,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        expect(
          () => service.startAnalysis(ticker: 'AAPL', tradeDate: '2024-01-15'),
          throwsA(isA<AnalysisException>()),
        );
      });
    });
    
    group('getRunStatusWithThread', () {
      test('should get status for pending run', () async {
        mockClient = MockClient((request) async {
          expect(request.url.toString(), '$testBaseUrl/threads/thread-123/runs/run-456');
          expect(request.method, 'GET');
          expect(request.headers['X-Api-Key'], testApiKey);
          
          return http.Response(
            jsonEncode({
              'run_id': 'run-456',
              'status': 'pending',
            }),
            200,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final response = await service.getRunStatusWithThread(
          runId: 'run-456',
          threadId: 'thread-123',
        );
        
        expect(response.runId, 'run-456');
        expect(response.status, 'pending');
        expect(response.isComplete, false);
        expect(response.result, isNull);
        expect(response.error, isNull);
        expect(response.completedAt, isNull);
      });
      
      test('should get status for running run', () async {
        mockClient = MockClient((request) async {
          return http.Response(
            jsonEncode({
              'run_id': 'run-456',
              'status': 'running',
            }),
            200,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final response = await service.getRunStatusWithThread(
          runId: 'run-456',
          threadId: 'thread-123',
        );
        
        expect(response.status, 'running');
        expect(response.isComplete, false);
      });
      
      test('should get status for successful run', () async {
        mockClient = MockClient((request) async {
          return http.Response(
            jsonEncode({
              'run_id': 'run-456',
              'status': 'success',
              'output': {
                'final_trade_decision': 'BUY',
                'confidence': 0.85,
              },
            }),
            200,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final response = await service.getRunStatusWithThread(
          runId: 'run-456',
          threadId: 'thread-123',
        );
        
        expect(response.status, 'success');
        expect(response.isComplete, true);
        expect(response.result, isNotNull);
        expect(response.result!['final_trade_decision'], 'BUY');
        expect(response.result!['confidence'], 0.85);
        expect(response.completedAt, isA<DateTime>());
      });
      
      test('should get status for failed run', () async {
        mockClient = MockClient((request) async {
          return http.Response(
            jsonEncode({
              'run_id': 'run-456',
              'status': 'error',
              'error': 'Analysis failed: Invalid ticker',
            }),
            200,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final response = await service.getRunStatusWithThread(
          runId: 'run-456',
          threadId: 'thread-123',
        );
        
        expect(response.status, 'error');
        expect(response.isComplete, true);
        expect(response.error, 'Analysis failed: Invalid ticker');
        expect(response.completedAt, isA<DateTime>());
      });
      
      test('should handle API errors', () async {
        mockClient = MockClient((request) async {
          return http.Response(
            jsonEncode({'error': 'Run not found'}),
            404,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        expect(
          () => service.getRunStatusWithThread(
            runId: 'run-456',
            threadId: 'thread-123',
          ),
          throwsA(isA<AnalysisException>()
            .having((e) => e.message, 'message', contains('Failed to get run status'))),
        );
      });
    });
    
    group('checkHealth', () {
      test('should return true when service is healthy', () async {
        mockClient = MockClient((request) async {
          expect(request.url.toString(), '$testBaseUrl/assistants');
          expect(request.method, 'GET');
          expect(request.headers['X-Api-Key'], testApiKey);
          
          return http.Response(
            jsonEncode([
              {'assistant_id': 'other-assistant'},
              {'assistant_id': testAssistantId},
            ]),
            200,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final isHealthy = await service.checkHealth();
        expect(isHealthy, true);
      });
      
      test('should return false when assistant not found', () async {
        mockClient = MockClient((request) async {
          return http.Response(
            jsonEncode([
              {'assistant_id': 'other-assistant'},
            ]),
            200,
          );
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final isHealthy = await service.checkHealth();
        expect(isHealthy, false);
      });
      
      test('should return false on API error', () async {
        mockClient = MockClient((request) async {
          return http.Response('Unauthorized', 401);
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final isHealthy = await service.checkHealth();
        expect(isHealthy, false);
      });
      
      test('should return false on network error', () async {
        mockClient = MockClient((request) async {
          throw Exception('Network error');
        });
        
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final isHealthy = await service.checkHealth();
        expect(isHealthy, false);
      });
    });
    
    group('singleton behavior', () {
      test('should return same instance', () {
        final instance1 = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        final instance2 = LangGraphApiService();
        
        expect(identical(instance1, instance2), true);
      });
      
      test('should use environment config when not provided', () {
        // Skip this test as it requires dotenv to be initialized
        // In a real app, dotenv would be initialized in main()
      }, skip: 'Requires dotenv initialization');
    });
    
    group('deprecated getRunStatus', () {
      test('should throw UnimplementedError', () {
        service = LangGraphApiService(
          baseUrl: testBaseUrl,
          apiKey: testApiKey,
          assistantId: testAssistantId,
          httpClient: mockClient,
        );
        
        expect(
          () => service.getRunStatus('run-123'),
          throwsUnimplementedError,
        );
      });
    });
  });
}