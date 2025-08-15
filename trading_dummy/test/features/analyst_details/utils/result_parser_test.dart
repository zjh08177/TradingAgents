import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/features/analyst_details/utils/result_parser.dart';
import 'package:trading_dummy/features/analyst_details/models/trade_decision.dart';

void main() {
  group('ResultParser', () {
    // Sample JSON data for testing
    const completeJson = '''
    {
      "final_decision": "BUY",
      "confidence": 0.85,
      "risk_manager_report": "Low risk, high reward potential",
      "market_report": "Bullish trend observed",
      "fundamentals_report": "Strong earnings growth",
      "sentiment_report": "Positive market sentiment",
      "news_report": "Recent product launch success",
      "debate_manager_report": "Consensus reached on BUY"
    }
    ''';
    
    const alternativeJson = '''
    {
      "trade_decision": "SELL",
      "confidence_level": 75,
      "risk_report": "High risk identified",
      "market_report": "Bearish signals",
      "debate_report": "Mixed opinions"
    }
    ''';
    
    const nestedJson = '''
    {
      "result": {
        "final_decision": "HOLD",
        "confidence": 0.6
      }
    }
    ''';
    
    group('parseDecision', () {
      test('extracts decision from final_decision field', () {
        expect(ResultParser.parseDecision(completeJson), TradeDecision.buy);
      });
      
      test('extracts decision from trade_decision field', () {
        expect(ResultParser.parseDecision(alternativeJson), TradeDecision.sell);
      });
      
      test('extracts decision from nested result field', () {
        expect(ResultParser.parseDecision(nestedJson), TradeDecision.hold);
      });
      
      test('returns null for invalid JSON', () {
        expect(ResultParser.parseDecision('invalid json'), null);
      });
      
      test('returns null for null input', () {
        expect(ResultParser.parseDecision(null), null);
      });
      
      test('returns null for empty string', () {
        expect(ResultParser.parseDecision(''), null);
      });
      
      test('returns null when decision field is missing', () {
        expect(ResultParser.parseDecision('{"other": "data"}'), null);
      });
    });
    
    group('parseConfidence', () {
      test('extracts confidence as decimal (0-1)', () {
        expect(ResultParser.parseConfidence(completeJson), 0.85);
      });
      
      test('converts percentage (0-100) to decimal', () {
        expect(ResultParser.parseConfidence(alternativeJson), 0.75);
      });
      
      test('extracts confidence from nested field', () {
        expect(ResultParser.parseConfidence(nestedJson), 0.6);
      });
      
      test('handles string confidence values', () {
        final json = '{"confidence": "0.95"}';
        expect(ResultParser.parseConfidence(json), 0.95);
      });
      
      test('handles percentage string values', () {
        final json = '{"confidence": "85"}';
        expect(ResultParser.parseConfidence(json), 0.85);
      });
      
      test('returns null for invalid confidence', () {
        final json = '{"confidence": "invalid"}';
        expect(ResultParser.parseConfidence(json), null);
      });
      
      test('returns null for null input', () {
        expect(ResultParser.parseConfidence(null), null);
      });
      
      test('returns null when confidence is missing', () {
        expect(ResultParser.parseConfidence('{"other": "data"}'), null);
      });
    });
    
    group('parseAgentReports', () {
      test('extracts all agent reports from complete JSON', () {
        final reports = ResultParser.parseAgentReports(completeJson);
        
        expect(reports.length, 4);
        expect(reports[0].type, 'market');
        expect(reports[0].content, 'Bullish trend observed');
        expect(reports[1].type, 'fundamentals');
        expect(reports[1].content, 'Strong earnings growth');
        expect(reports[2].type, 'sentiment');
        expect(reports[2].content, 'Positive market sentiment');
        expect(reports[3].type, 'news');
        expect(reports[3].content, 'Recent product launch success');
      });
      
      test('extracts available reports from partial JSON', () {
        final reports = ResultParser.parseAgentReports(alternativeJson);
        
        expect(reports.length, 1);
        expect(reports[0].type, 'market');
        expect(reports[0].content, 'Bearish signals');
      });
      
      test('includes emoji icons in reports', () {
        final reports = ResultParser.parseAgentReports(completeJson);
        
        expect(reports[0].icon, '📊');
        expect(reports[1].icon, '📈');
        expect(reports[2].icon, '🎭');
        expect(reports[3].icon, '📰');
      });
      
      test('returns empty list for JSON without reports', () {
        final reports = ResultParser.parseAgentReports(nestedJson);
        expect(reports, isEmpty);
      });
      
      test('returns empty list for null input', () {
        expect(ResultParser.parseAgentReports(null), isEmpty);
      });
      
      test('returns empty list for invalid JSON', () {
        expect(ResultParser.parseAgentReports('invalid'), isEmpty);
      });
      
      test('skips empty report fields', () {
        final json = '{"market_report": "", "news_report": "News content"}';
        final reports = ResultParser.parseAgentReports(json);
        
        expect(reports.length, 1);
        expect(reports[0].type, 'news');
      });
    });
    
    group('parseRiskReport', () {
      test('extracts risk_manager_report field', () {
        expect(
          ResultParser.parseRiskReport(completeJson),
          'Low risk, high reward potential',
        );
      });
      
      test('extracts risk_report field', () {
        expect(
          ResultParser.parseRiskReport(alternativeJson),
          'High risk identified',
        );
      });
      
      test('returns null when risk report is missing', () {
        expect(ResultParser.parseRiskReport(nestedJson), null);
      });
      
      test('returns null for null input', () {
        expect(ResultParser.parseRiskReport(null), null);
      });
      
      test('returns null for invalid JSON', () {
        expect(ResultParser.parseRiskReport('invalid'), null);
      });
    });
    
    group('parseDebateReport', () {
      test('extracts debate_manager_report field', () {
        expect(
          ResultParser.parseDebateReport(completeJson),
          'Consensus reached on BUY',
        );
      });
      
      test('extracts debate_report field', () {
        expect(
          ResultParser.parseDebateReport(alternativeJson),
          'Mixed opinions',
        );
      });
      
      test('returns null when debate report is missing', () {
        expect(ResultParser.parseDebateReport(nestedJson), null);
      });
      
      test('returns null for null input', () {
        expect(ResultParser.parseDebateReport(null), null);
      });
      
      test('returns null for invalid JSON', () {
        expect(ResultParser.parseDebateReport('invalid'), null);
      });
    });
    
    group('parseAll', () {
      test('parses all fields from complete JSON', () {
        final result = ResultParser.parseAll(completeJson);
        
        expect(result['decision'], TradeDecision.buy);
        expect(result['confidence'], 0.85);
        expect(result['riskReport'], 'Low risk, high reward potential');
        expect(result['agentReports'], isA<List>());
        expect((result['agentReports'] as List).length, 4);
        expect(result['debateReport'], 'Consensus reached on BUY');
      });
      
      test('handles partial JSON correctly', () {
        final result = ResultParser.parseAll(alternativeJson);
        
        expect(result['decision'], TradeDecision.sell);
        expect(result['confidence'], 0.75);
        expect(result['riskReport'], 'High risk identified');
        expect((result['agentReports'] as List).length, 1);
        expect(result['debateReport'], 'Mixed opinions');
      });
      
      test('returns nulls for missing fields', () {
        final result = ResultParser.parseAll('{}');
        
        expect(result['decision'], null);
        expect(result['confidence'], null);
        expect(result['riskReport'], null);
        expect(result['agentReports'], isEmpty);
        expect(result['debateReport'], null);
      });
      
      test('handles null input gracefully', () {
        final result = ResultParser.parseAll(null);
        
        expect(result['decision'], null);
        expect(result['confidence'], null);
        expect(result['riskReport'], null);
        expect(result['agentReports'], isEmpty);
        expect(result['debateReport'], null);
      });
    });
    
    group('Investment Recommendation extraction (BUG FIX)', () {
      test('should correctly extract HOLD from Investment Recommendation in risk_manager_report', () {
        // This test replicates the exact issue from the screenshot
        final jsonResult = jsonEncode({
          'risk_manager_report': '''
# Risk Manager Report

Investment Recommendation: HOLD with Medium Confidence

Given the mixed market indicators, we recommend a HOLD position on Tesla (TSLA) at this time. 
The current market environment presents both opportunities and risks, as outlined below. 
This positions us to benefit from any potential upsides while cautiously monitoring for potential risks.

Some analysts might say BUY based on innovation potential, while others suggest SELL due to valuation concerns.

Position Sizing: 5% of Total Portfolio
''',
          'market_report': 'Technical indicators show bullish momentum with BUY signals',
          'fundamentals_report': 'Strong fundamentals suggest BUY opportunity',
        });

        final decision = ResultParser.parseDecision(jsonResult);

        // The decision should be HOLD, not BUY
        expect(decision, equals(TradeDecision.hold));
      });

      test('should not be confused by mentions of BUY/SELL/HOLD in other text', () {
        final jsonResult = jsonEncode({
          'risk_manager_report': '''
Some analysts recommend BUY due to strong earnings.
Others suggest SELL because of high valuation.
Many prefer to HOLD and wait for clarity.

Investment Recommendation: HOLD with Medium Confidence

After considering all factors, we recommend holding current positions.
''',
        });

        final decision = ResultParser.parseDecision(jsonResult);

        // Should extract HOLD from the explicit recommendation, not BUY from earlier text
        expect(decision, equals(TradeDecision.hold));
      });

      test('should extract BUY when it is the actual Investment Recommendation', () {
        final jsonResult = jsonEncode({
          'risk_manager_report': '''
# Risk Manager Report

Investment Recommendation: BUY with High Confidence

Strong fundamentals and positive market sentiment support a buy recommendation.
''',
        });

        final decision = ResultParser.parseDecision(jsonResult);

        expect(decision, equals(TradeDecision.buy));
      });

      test('should extract SELL when it is the actual Investment Recommendation', () {
        final jsonResult = jsonEncode({
          'risk_manager_report': '''
Investment Recommendation: SELL with Low Confidence

Deteriorating fundamentals suggest exiting positions.
''',
        });

        final decision = ResultParser.parseDecision(jsonResult);

        expect(decision, equals(TradeDecision.sell));
      });

      test('complete real-world scenario with all report types', () {
        final jsonResult = jsonEncode({
          'market_report': 'Technical analysis shows BUY signals',
          'fundamentals_report': 'Fundamentals indicate BUY opportunity',
          'sentiment_report': 'Social sentiment is bullish',
          'news_report': 'News coverage is positive',
          'risk_manager_report': '''
# Risk Manager Report

The analysis presents both bullish and bearish perspectives. Bulls point to innovation and growth potential suggesting BUY positions. 
Bears cite valuation concerns recommending SELL strategies.

Investment Recommendation: HOLD with Medium Confidence

Given the mixed signals, we recommend maintaining current positions while monitoring for clearer signals.
''',
        });

        final decision = ResultParser.parseDecision(jsonResult);

        // Should extract HOLD from Investment Recommendation, not BUY from other mentions
        expect(decision, equals(TradeDecision.hold));
      });
    });
    
    group('edge cases', () {
      test('handles malformed but valid JSON', () {
        const malformed = '{"final_decision":"BUY","confidence":0.85}';
        expect(ResultParser.parseDecision(malformed), TradeDecision.buy);
        expect(ResultParser.parseConfidence(malformed), 0.85);
      });
      
      test('handles Unicode in reports', () {
        const unicode = '{"market_report": "📈 Büllish trénd 🚀"}';
        final reports = ResultParser.parseAgentReports(unicode);
        expect(reports[0].content, '📈 Büllish trénd 🚀');
      });
      
      test('handles very large confidence values', () {
        const large = '{"confidence": 999}';
        expect(ResultParser.parseConfidence(large), 9.99);
      });
      
      test('handles negative confidence values', () {
        const negative = '{"confidence": -0.5}';
        expect(ResultParser.parseConfidence(negative), -0.5);
      });
    });
  });
}