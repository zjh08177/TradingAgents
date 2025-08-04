import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'dart:convert';
import 'package:trading_dummy/jobs/infrastructure/services/langgraph_api_service.dart';

void main() {
  group('LangGraphApiService Authentication', () {
    late MockClient mockClient;
    
    setUp(() {
      // Reset singleton for testing
      LangGraphApiService.reset();
    });
    
    tearDown(() {
      LangGraphApiService.reset();
    });
    
    test('should handle 403 error when API key is missing or invalid', () async {
      // Mock a 403 response for missing auth
      mockClient = MockClient((request) async {
        // Check if API key is empty or missing
        final apiKey = request.headers['X-Api-Key'] ?? '';
        
        if (apiKey.isEmpty) {
          return http.Response(
            jsonEncode({
              'error': 'Missing auth headers',
              'detail': 'Authentication required',
            }),
            403,
          );
        }
        
        // For this test, even with a key, return 403 to simulate invalid key
        return http.Response(
          jsonEncode({
            'error': 'Invalid API key',
            'detail': 'The provided API key is not valid',
          }),
          403,
        );
      });
      
      // Create service with empty API key (simulating missing env var)
      final service = LangGraphApiService(
        baseUrl: 'https://api.test.com',
        apiKey: '', // Empty API key
        assistantId: 'test-assistant',
        httpClient: mockClient,
      );
      
      // Test should throw AnalysisException with 403 error
      expect(
        () => service.startAnalysis(ticker: 'AAPL', tradeDate: '2024-01-15'),
        throwsA(
          isA<AnalysisException>()
            .having((e) => e.message, 'message', contains('403'))
            .having((e) => e.message, 'message', contains('Missing auth headers')),
        ),
      );
    });
    
    test('should handle 403 error on health check with missing auth', () async {
      mockClient = MockClient((request) async {
        // Check for missing API key on health check endpoint
        final apiKey = request.headers['X-Api-Key'] ?? '';
        
        if (apiKey.isEmpty || request.url.path.contains('/assistants')) {
          return http.Response(
            jsonEncode({
              'error': 'Authentication required',
              'detail': 'Valid API key must be provided',
            }),
            403,
          );
        }
        
        return http.Response('', 404);
      });
      
      final service = LangGraphApiService(
        baseUrl: 'https://api.test.com',
        apiKey: '', // Empty API key
        assistantId: 'test-assistant',
        httpClient: mockClient,
      );
      
      // Health check should return false on 403
      final isHealthy = await service.checkHealth();
      expect(isHealthy, false);
    });
    
    test('should include proper auth headers when API key is provided', () async {
      const testApiKey = 'test-valid-api-key';
      bool headerChecked = false;
      
      mockClient = MockClient((request) async {
        // Verify API key is included in headers
        expect(request.headers['X-Api-Key'], testApiKey);
        headerChecked = true;
        
        if (request.url.path == '/threads') {
          return http.Response(
            jsonEncode({'thread_id': 'thread-123'}),
            200,
          );
        } else if (request.url.path.contains('/runs')) {
          return http.Response(
            jsonEncode({
              'run_id': 'run-456',
              'status': 'pending',
            }),
            200,
          );
        }
        
        return http.Response('', 404);
      });
      
      final service = LangGraphApiService(
        baseUrl: 'https://api.test.com',
        apiKey: testApiKey,
        assistantId: 'test-assistant',
        httpClient: mockClient,
      );
      
      // This should succeed with proper auth
      final response = await service.startAnalysis(
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
      );
      
      expect(response.runId, 'run-456');
      expect(headerChecked, true, reason: 'Headers should have been checked');
    });
    
    test('should show helpful error message for 403 authentication errors', () async {
      mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'error': 'Forbidden',
            'message': 'Invalid or missing API key',
            'code': 'AUTH_FAILED',
          }),
          403,
        );
      });
      
      final service = LangGraphApiService(
        baseUrl: 'https://api.test.com',
        apiKey: 'invalid-key',
        assistantId: 'test-assistant',
        httpClient: mockClient,
      );
      
      try {
        await service.startAnalysis(ticker: 'AAPL', tradeDate: '2024-01-15');
        fail('Should have thrown AnalysisException');
      } catch (e) {
        expect(e, isA<AnalysisException>());
        final error = e as AnalysisException;
        expect(error.message, contains('403'));
        expect(error.message, contains('Forbidden'));
        
        // The error message should be helpful for debugging
        // Example: "Failed to create thread: 403 {\"error\":\"Forbidden\",\"message\":\"Invalid or missing API key\",\"code\":\"AUTH_FAILED\"}"
      }
    });
  });
}