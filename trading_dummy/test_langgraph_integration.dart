import 'dart:io';
import 'lib/services/langgraph_client.dart';
import 'lib/services/logger_service.dart';

void main() async {
  print('🧪 LangGraph Integration Test');
  print('=' * 50);
  
  // Initialize logger
  LoggerService.setLogLevel(LogLevel.info);
  
  // Create client
  final client = LangGraphClient(
    baseUrl: 'http://localhost:8000',
    timeout: const Duration(seconds: 120),
  );
  
  try {
    // Step 1: Health Check
    print('\n1️⃣ Testing server health check...');
    final isHealthy = await client.checkHealth();
    print('   Result: ${isHealthy ? "✅ HEALTHY" : "❌ UNHEALTHY"}');
    
    if (!isHealthy) {
      print('\n❌ Server is not running or unhealthy');
      print('   Please start the server with:');
      print('   cd backend && python3 -m uvicorn api:app --reload');
      exit(1);
    }
    
    // Step 2: Test Analysis
    print('\n2️⃣ Testing analysis endpoint with TSLA...');
    print('   This may take 30-120 seconds...');
    
    final stopwatch = Stopwatch()..start();
    final result = await client.analyzeTicker('TSLA');
    stopwatch.stop();
    
    print('   ✅ Analysis completed in ${stopwatch.elapsed.inSeconds} seconds');
    
    // Step 3: Verify Results
    print('\n3️⃣ Verifying results:');
    print('   - Ticker: ${result.ticker}');
    print('   - Date: ${result.analysisDate}');
    print('   - Signal: ${result.processedSignal ?? "N/A"}');
    print('   - Has Final Decision: ${result.finalTradeDecision != null ? "✅" : "❌"}');
    print('   - Has Market Report: ${result.marketReport != null ? "✅" : "❌"}');
    print('   - Has News Report: ${result.newsReport != null ? "✅" : "❌"}');
    print('   - Error: ${result.error ?? "None"}');
    
    // Step 4: Check Available Reports
    print('\n4️⃣ Available reports:');
    result.availableReports.forEach((name, _) {
      print('   - $name ✅');
    });
    
    // Step 5: Summary
    print('\n5️⃣ Test Summary:');
    if (result.isSuccessful) {
      print('   ✅ Integration test PASSED');
      print('   ✅ LangGraph client is working correctly');
      print('   ✅ Server communication established');
      print('   ✅ Analysis results received');
    } else {
      print('   ❌ Integration test FAILED');
      print('   Error: ${result.error}');
    }
    
  } catch (e) {
    print('\n❌ Test failed with error:');
    print('   $e');
    exit(1);
  } finally {
    client.dispose();
  }
  
  print('\n' + '=' * 50);
  print('Test completed');
}