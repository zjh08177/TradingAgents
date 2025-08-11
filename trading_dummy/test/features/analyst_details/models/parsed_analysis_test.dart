import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/features/analyst_details/models/parsed_analysis.dart';
import 'package:trading_dummy/features/analyst_details/models/trade_decision.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_record.dart';

void main() {
  group('ParsedAnalysis', () {
    // Helper function to create test AnalysisRecord
    AnalysisRecord createTestRecord({
      String? result,
      String status = 'success',
      String? error,
    }) {
      return AnalysisRecord(
        id: 'test-1',
        runId: 'run-1',
        threadId: 'thread-1',
        ticker: 'AAPL',
        tradeDate: '2024-01-01',
        status: status,
        createdAt: DateTime(2024, 1, 1, 10, 0),
        updatedAt: DateTime(2024, 1, 1, 10, 30),
        completedAt: status == 'success' ? DateTime(2024, 1, 1, 10, 30) : null,
        result: result,
        error: error,
      );
    }
    
    const completeResultJson = '''
    {
      "final_decision": "BUY",
      "confidence": 0.85,
      "risk_manager_report": "Low risk with high reward potential",
      "market_report": "Strong bullish trend",
      "fundamentals_report": "Excellent earnings",
      "sentiment_report": "Positive sentiment",
      "news_report": "Good news coverage",
      "debate_manager_report": "Unanimous BUY recommendation"
    }
    ''';
    
    const partialResultJson = '''
    {
      "final_decision": "SELL",
      "confidence": 0.65,
      "risk_manager_report": "High risk identified"
    }
    ''';
    
    group('fromRecord factory', () {
      test('creates ParsedAnalysis from complete result', () {
        final record = createTestRecord(result: completeResultJson);
        final parsed = ParsedAnalysis.fromRecord(record);
        
        expect(parsed.record, record);
        expect(parsed.decision, TradeDecision.buy);
        expect(parsed.confidence, 0.85);
        expect(parsed.riskReport, 'Low risk with high reward potential');
        expect(parsed.agentReports.length, 4);
        expect(parsed.debateReport, 'Unanimous BUY recommendation');
      });
      
      test('creates ParsedAnalysis from partial result', () {
        final record = createTestRecord(result: partialResultJson);
        final parsed = ParsedAnalysis.fromRecord(record);
        
        expect(parsed.record, record);
        expect(parsed.decision, TradeDecision.sell);
        expect(parsed.confidence, 0.65);
        expect(parsed.riskReport, 'High risk identified');
        expect(parsed.agentReports, isEmpty);
        expect(parsed.debateReport, null);
      });
      
      test('handles null result gracefully', () {
        final record = createTestRecord(result: null);
        final parsed = ParsedAnalysis.fromRecord(record);
        
        expect(parsed.record, record);
        expect(parsed.decision, null);
        expect(parsed.confidence, null);
        expect(parsed.riskReport, null);
        expect(parsed.agentReports, isEmpty);
        expect(parsed.debateReport, null);
      });
      
      test('handles invalid JSON gracefully', () {
        final record = createTestRecord(result: 'invalid json');
        final parsed = ParsedAnalysis.fromRecord(record);
        
        expect(parsed.record, record);
        expect(parsed.decision, null);
        expect(parsed.confidence, null);
        expect(parsed.riskReport, null);
        expect(parsed.agentReports, isEmpty);
        expect(parsed.debateReport, null);
      });
    });
    
    group('boolean getters', () {
      test('hasDecision returns correct values', () {
        final withDecision = ParsedAnalysis.fromRecord(
          createTestRecord(result: completeResultJson),
        );
        final withoutDecision = ParsedAnalysis.fromRecord(
          createTestRecord(result: '{}'),
        );
        
        expect(withDecision.hasDecision, true);
        expect(withoutDecision.hasDecision, false);
      });
      
      test('hasRiskReport returns correct values', () {
        final withRisk = ParsedAnalysis.fromRecord(
          createTestRecord(result: completeResultJson),
        );
        final withoutRisk = ParsedAnalysis.fromRecord(
          createTestRecord(result: '{"final_decision": "BUY"}'),
        );
        
        expect(withRisk.hasRiskReport, true);
        expect(withoutRisk.hasRiskReport, false);
      });
      
      test('hasAgentReports returns correct values', () {
        final withReports = ParsedAnalysis.fromRecord(
          createTestRecord(result: completeResultJson),
        );
        final withoutReports = ParsedAnalysis.fromRecord(
          createTestRecord(result: partialResultJson),
        );
        
        expect(withReports.hasAgentReports, true);
        expect(withoutReports.hasAgentReports, false);
      });
      
      test('hasDebateReport returns correct values', () {
        final withDebate = ParsedAnalysis.fromRecord(
          createTestRecord(result: completeResultJson),
        );
        final withoutDebate = ParsedAnalysis.fromRecord(
          createTestRecord(result: partialResultJson),
        );
        
        expect(withDebate.hasDebateReport, true);
        expect(withoutDebate.hasDebateReport, false);
      });
    });
    
    group('display getters', () {
      test('displayConfidence formats percentage correctly', () {
        final high = ParsedAnalysis.fromRecord(
          createTestRecord(result: '{"confidence": 0.85}'),
        );
        final low = ParsedAnalysis.fromRecord(
          createTestRecord(result: '{"confidence": 0.333}'),
        );
        final none = ParsedAnalysis.fromRecord(
          createTestRecord(result: '{}'),
        );
        
        expect(high.displayConfidence, '85%');
        expect(low.displayConfidence, '33%');
        expect(none.displayConfidence, '');
      });
    });
    
    group('delegated getters from AnalysisRecord', () {
      test('ticker returns record ticker', () {
        final record = createTestRecord();
        final parsed = ParsedAnalysis.fromRecord(record);
        
        expect(parsed.ticker, 'AAPL');
      });
      
      test('tradeDate returns record tradeDate', () {
        final record = createTestRecord();
        final parsed = ParsedAnalysis.fromRecord(record);
        
        expect(parsed.tradeDate, '2024-01-01');
      });
      
      test('status returns record status', () {
        final record = createTestRecord(status: 'running');
        final parsed = ParsedAnalysis.fromRecord(record);
        
        expect(parsed.status, 'running');
      });
      
      test('date getters return record dates', () {
        final record = createTestRecord();
        final parsed = ParsedAnalysis.fromRecord(record);
        
        expect(parsed.createdAt, DateTime(2024, 1, 1, 10, 0));
        expect(parsed.completedAt, DateTime(2024, 1, 1, 10, 30));
      });
      
      test('status booleans delegate to record', () {
        final complete = ParsedAnalysis.fromRecord(
          createTestRecord(status: 'success'),
        );
        final running = ParsedAnalysis.fromRecord(
          createTestRecord(status: 'running'),
        );
        final pending = ParsedAnalysis.fromRecord(
          createTestRecord(status: 'pending'),
        );
        final error = ParsedAnalysis.fromRecord(
          createTestRecord(status: 'error', error: 'Test error'),
        );
        
        expect(complete.isComplete, true);
        expect(complete.isRunning, false);
        expect(running.isRunning, true);
        expect(pending.isPending, true);
        expect(error.hasError, true);
        expect(error.errorMessage, 'Test error');
      });
    });
    
    group('report getters', () {
      test('getReportByType returns correct report', () {
        final parsed = ParsedAnalysis.fromRecord(
          createTestRecord(result: completeResultJson),
        );
        
        final market = parsed.getReportByType('market');
        expect(market?.content, 'Strong bullish trend');
        
        final fundamentals = parsed.getReportByType('fundamentals');
        expect(fundamentals?.content, 'Excellent earnings');
      });
      
      test('getReportByType returns null for missing report', () {
        final parsed = ParsedAnalysis.fromRecord(
          createTestRecord(result: completeResultJson),
        );
        
        expect(parsed.getReportByType('nonexistent'), null);
      });
      
      test('convenience report getters work correctly', () {
        final parsed = ParsedAnalysis.fromRecord(
          createTestRecord(result: completeResultJson),
        );
        
        expect(parsed.marketReport?.content, 'Strong bullish trend');
        expect(parsed.fundamentalsReport?.content, 'Excellent earnings');
        expect(parsed.sentimentReport?.content, 'Positive sentiment');
        expect(parsed.newsReport?.content, 'Good news coverage');
      });
      
      test('convenience report getters return null when missing', () {
        final parsed = ParsedAnalysis.fromRecord(
          createTestRecord(result: partialResultJson),
        );
        
        expect(parsed.marketReport, null);
        expect(parsed.fundamentalsReport, null);
        expect(parsed.sentimentReport, null);
        expect(parsed.newsReport, null);
      });
    });
    
    group('equality and hashCode', () {
      test('identical ParsedAnalysis objects are equal', () {
        final record = createTestRecord(result: completeResultJson);
        final parsed1 = ParsedAnalysis.fromRecord(record);
        final parsed2 = ParsedAnalysis.fromRecord(record);
        
        expect(parsed1, parsed2);
        expect(parsed1.hashCode, parsed2.hashCode);
      });
      
      test('ParsedAnalysis with different records are not equal', () {
        final record1 = createTestRecord(result: completeResultJson);
        final record2 = createTestRecord(result: partialResultJson);
        final parsed1 = ParsedAnalysis.fromRecord(record1);
        final parsed2 = ParsedAnalysis.fromRecord(record2);
        
        expect(parsed1, isNot(parsed2));
      });
    });
    
    group('toString', () {
      test('provides readable string representation', () {
        final parsed = ParsedAnalysis.fromRecord(
          createTestRecord(result: completeResultJson),
        );
        
        final str = parsed.toString();
        
        expect(str, contains('ParsedAnalysis'));
        expect(str, contains('ticker: AAPL'));
        expect(str, contains('status: success'));
        expect(str, contains('decision: TradeDecision.buy'));
        expect(str, contains('confidence: 85%'));
      });
      
      test('handles null values in toString', () {
        final parsed = ParsedAnalysis.fromRecord(
          createTestRecord(result: null),
        );
        
        final str = parsed.toString();
        
        expect(str, contains('decision: null'));
        expect(str, contains('confidence: '));
      });
    });
  });
}