import 'dart:async';
import 'package:trading_dummy/services/langgraph_service.dart';
import 'package:trading_dummy/models/final_report.dart';

/// Mock implementation of ILangGraphService for testing
class MockLangGraphService implements ILangGraphService {
  bool shouldFail = false;
  String failureMessage = 'Mock analysis failed';
  
  @override
  Future<FinalReport> analyzeTicker(String ticker, String tradeDate) async {
    // Simulate some processing time
    await Future.delayed(const Duration(milliseconds: 100));
    
    if (shouldFail) {
      throw Exception(failureMessage);
    }
    
    // Return a mock report
    return FinalReport(
      ticker: ticker,
      tradeDate: tradeDate,
      content: 'Mock analysis report for $ticker on $tradeDate',
      timestamp: DateTime.now(),
      isError: false,
      rawOutput: {
        'summary': 'Mock analysis summary for $ticker on $tradeDate',
        'details': 'Mock analysis details',
      },
    );
  }
  
  @override
  Future<bool> checkHealth() async {
    // Simulate health check
    await Future.delayed(const Duration(milliseconds: 50));
    return !shouldFail;
  }
  
  @override
  void dispose() {
    // Nothing to dispose in mock
  }
}