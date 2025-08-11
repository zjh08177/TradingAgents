import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/features/analyst_details/models/agent_report.dart';

void main() {
  group('AgentReport', () {
    group('constructor', () {
      test('creates report with all required fields', () {
        const report = AgentReport(
          type: 'market',
          title: 'Market Analysis',
          content: 'Test content',
        );
        
        expect(report.type, 'market');
        expect(report.title, 'Market Analysis');
        expect(report.content, 'Test content');
        expect(report.icon, null);
      });
      
      test('creates report with optional icon', () {
        const report = AgentReport(
          type: 'market',
          title: 'Market Analysis',
          content: 'Test content',
          icon: '📊',
        );
        
        expect(report.icon, '📊');
      });
    });
    
    group('hasContent', () {
      test('returns true when content is not empty', () {
        const report = AgentReport(
          type: 'market',
          title: 'Market',
          content: 'Some content',
        );
        
        expect(report.hasContent, true);
      });
      
      test('returns false when content is empty', () {
        const report = AgentReport(
          type: 'market',
          title: 'Market',
          content: '',
        );
        
        expect(report.hasContent, false);
      });
    });
    
    group('empty factory', () {
      test('creates report with empty content', () {
        final report = AgentReport.empty('market', 'Market Analysis');
        
        expect(report.type, 'market');
        expect(report.title, 'Market Analysis');
        expect(report.content, '');
        expect(report.hasContent, false);
        expect(report.icon, null);
      });
    });
    
    group('fromJson', () {
      test('parses complete JSON correctly', () {
        final json = {
          'type': 'fundamentals',
          'title': 'Fundamentals Report',
          'content': 'Strong earnings growth',
          'icon': '📈',
        };
        
        final report = AgentReport.fromJson(json);
        
        expect(report.type, 'fundamentals');
        expect(report.title, 'Fundamentals Report');
        expect(report.content, 'Strong earnings growth');
        expect(report.icon, '📈');
      });
      
      test('handles missing optional fields', () {
        final json = {
          'type': 'news',
          'title': 'News Analysis',
          'content': 'Recent news summary',
        };
        
        final report = AgentReport.fromJson(json);
        
        expect(report.type, 'news');
        expect(report.title, 'News Analysis');
        expect(report.content, 'Recent news summary');
        expect(report.icon, null);
      });
      
      test('handles null values with defaults', () {
        final json = <String, dynamic>{
          'type': null,
          'title': null,
          'content': null,
        };
        
        final report = AgentReport.fromJson(json);
        
        expect(report.type, '');
        expect(report.title, '');
        expect(report.content, '');
        expect(report.icon, null);
      });
      
      test('handles empty JSON', () {
        final report = AgentReport.fromJson({});
        
        expect(report.type, '');
        expect(report.title, '');
        expect(report.content, '');
        expect(report.icon, null);
      });
    });
    
    group('toJson', () {
      test('exports complete report to JSON', () {
        const report = AgentReport(
          type: 'sentiment',
          title: 'Sentiment Analysis',
          content: 'Positive sentiment',
          icon: '🎭',
        );
        
        final json = report.toJson();
        
        expect(json['type'], 'sentiment');
        expect(json['title'], 'Sentiment Analysis');
        expect(json['content'], 'Positive sentiment');
        expect(json['icon'], '🎭');
      });
      
      test('excludes null icon from JSON', () {
        const report = AgentReport(
          type: 'market',
          title: 'Market',
          content: 'Content',
        );
        
        final json = report.toJson();
        
        expect(json.containsKey('icon'), false);
        expect(json.length, 3);
      });
    });
    
    group('equality', () {
      test('reports with same values are equal', () {
        const report1 = AgentReport(
          type: 'market',
          title: 'Market',
          content: 'Content',
        );
        
        const report2 = AgentReport(
          type: 'market',
          title: 'Market',
          content: 'Content',
        );
        
        expect(report1, report2);
        expect(report1.hashCode, report2.hashCode);
      });
      
      test('reports with different values are not equal', () {
        const report1 = AgentReport(
          type: 'market',
          title: 'Market',
          content: 'Content1',
        );
        
        const report2 = AgentReport(
          type: 'market',
          title: 'Market',
          content: 'Content2',
        );
        
        expect(report1, isNot(report2));
      });
      
      test('reports with same values including icon are equal', () {
        const report1 = AgentReport(
          type: 'market',
          title: 'Market',
          content: 'Content',
          icon: '📊',
        );
        
        const report2 = AgentReport(
          type: 'market',
          title: 'Market',
          content: 'Content',
          icon: '📊',
        );
        
        expect(report1, report2);
        expect(report1.hashCode, report2.hashCode);
      });
    });
    
    group('toString', () {
      test('provides readable string representation', () {
        const report = AgentReport(
          type: 'market',
          title: 'Market Analysis',
          content: 'Some content',
        );
        
        final str = report.toString();
        
        expect(str, contains('AgentReport'));
        expect(str, contains('type: market'));
        expect(str, contains('title: Market Analysis'));
        expect(str, contains('hasContent: true'));
      });
      
      test('shows hasContent false for empty report', () {
        final report = AgentReport.empty('market', 'Market');
        
        final str = report.toString();
        
        expect(str, contains('hasContent: false'));
      });
    });
  });
}