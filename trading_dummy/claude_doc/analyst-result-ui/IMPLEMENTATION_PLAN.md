# Implementation Plan - Analyst Result UI Display

## Executive Summary

This plan provides atomic, self-testable subtasks for implementing the analyst result UI display feature. Each task is designed to be completed independently, tested in isolation, and integrated incrementally. The implementation extends the existing `AnalysisRecord` infrastructure without breaking changes.

## Project Timeline

**Total Duration**: 8-10 days
**Team Size**: 1-2 developers
**Daily Velocity**: 2-3 tasks per developer

## Task Breakdown by Phase

### Phase 1: Data Foundation (Day 1-2)
**Goal**: Establish data parsing and modeling layer

#### Task 1.1: Create TradeDecision Enum
**Duration**: 30 minutes
**Dependencies**: None
**Input**: String values ('BUY', 'SELL', 'HOLD')
**Output**: Enum with display properties
**Test Command**: `flutter test test/features/analyst_details/models/trade_decision_test.dart`

```dart
// Implementation file: lib/features/analyst_details/models/trade_decision.dart
enum TradeDecision {
  buy('BUY', Colors.green, Icons.trending_up),
  sell('SELL', Colors.red, Icons.trending_down),
  hold('HOLD', Colors.orange, Icons.pause_circle_outline);
  
  final String displayName;
  final Color color;
  final IconData icon;
  
  const TradeDecision(this.displayName, this.color, this.icon);
  
  static TradeDecision? fromString(String? value) {
    if (value == null) return null;
    switch (value.toUpperCase()) {
      case 'BUY': return buy;
      case 'SELL': return sell;
      case 'HOLD': return hold;
      default: return null;
    }
  }
}

// Test file: test/features/analyst_details/models/trade_decision_test.dart
void main() {
  test('TradeDecision.fromString parses correctly', () {
    expect(TradeDecision.fromString('BUY'), TradeDecision.buy);
    expect(TradeDecision.fromString('sell'), TradeDecision.sell);
    expect(TradeDecision.fromString('HOLD'), TradeDecision.hold);
    expect(TradeDecision.fromString('invalid'), null);
    expect(TradeDecision.fromString(null), null);
  });
  
  test('TradeDecision has correct display properties', () {
    expect(TradeDecision.buy.displayName, 'BUY');
    expect(TradeDecision.buy.color, Colors.green);
    expect(TradeDecision.buy.icon, Icons.trending_up);
  });
}
```

#### Task 1.2: Create AgentReport Model
**Duration**: 30 minutes
**Dependencies**: None
**Input**: JSON data with report content
**Output**: Structured report model
**Test Command**: `flutter test test/features/analyst_details/models/agent_report_test.dart`

```dart
// Implementation: lib/features/analyst_details/models/agent_report.dart
class AgentReport {
  final String type;
  final String title;
  final String content;
  final String? icon;
  
  const AgentReport({
    required this.type,
    required this.title,
    required this.content,
    this.icon,
  });
  
  bool get hasContent => content.isNotEmpty;
  
  factory AgentReport.empty(String type, String title) {
    return AgentReport(type: type, title: title, content: '');
  }
}

// Test: test/features/analyst_details/models/agent_report_test.dart
void main() {
  test('AgentReport hasContent works correctly', () {
    final report1 = AgentReport(type: 'market', title: 'Market', content: 'Data');
    final report2 = AgentReport.empty('market', 'Market');
    
    expect(report1.hasContent, true);
    expect(report2.hasContent, false);
  });
}
```

#### Task 1.3: Create ResultParser Utility
**Duration**: 2 hours
**Dependencies**: Task 1.1, Task 1.2
**Input**: JSON string from AnalysisRecord.result
**Output**: Parsed components
**Test Command**: `flutter test test/features/analyst_details/utils/result_parser_test.dart`

```dart
// Implementation: lib/features/analyst_details/utils/result_parser.dart
class ResultParser {
  static TradeDecision? parseDecision(String? jsonString) {
    if (jsonString == null) return null;
    
    try {
      final json = jsonDecode(jsonString);
      final decision = json['final_decision'] ?? 
                      json['trade_decision'] ?? 
                      json['result']?['final_decision'];
      return TradeDecision.fromString(decision?.toString());
    } catch (e) {
      return null;
    }
  }
  
  static double? parseConfidence(String? jsonString) {
    if (jsonString == null) return null;
    
    try {
      final json = jsonDecode(jsonString);
      final confidence = json['confidence'] ?? 
                        json['confidence_level'] ?? 
                        json['result']?['confidence'];
      if (confidence == null) return null;
      
      // Handle both 0-1 and 0-100 ranges
      final value = confidence.toDouble();
      return value > 1 ? value / 100 : value;
    } catch (e) {
      return null;
    }
  }
  
  static List<AgentReport> parseAgentReports(String? jsonString) {
    if (jsonString == null) return [];
    
    try {
      final json = jsonDecode(jsonString);
      final reports = <AgentReport>[];
      
      final reportMappings = {
        'market_report': ('market', '📊 Market Analysis'),
        'fundamentals_report': ('fundamentals', '📈 Fundamentals'),
        'sentiment_report': ('sentiment', '🎭 Sentiment Analysis'),
        'news_report': ('news', '📰 News Analysis'),
      };
      
      reportMappings.forEach((key, value) {
        if (json[key] != null) {
          reports.add(AgentReport(
            type: value.$1,
            title: value.$2,
            content: json[key].toString(),
          ));
        }
      });
      
      return reports;
    } catch (e) {
      return [];
    }
  }
  
  static String? parseRiskReport(String? jsonString) {
    if (jsonString == null) return null;
    
    try {
      final json = jsonDecode(jsonString);
      return json['risk_manager_report']?.toString();
    } catch (e) {
      return null;
    }
  }
  
  static String? parseDebateReport(String? jsonString) {
    if (jsonString == null) return null;
    
    try {
      final json = jsonDecode(jsonString);
      return json['debate_manager_report']?.toString();
    } catch (e) {
      return null;
    }
  }
}

// Test: test/features/analyst_details/utils/result_parser_test.dart
void main() {
  group('ResultParser', () {
    const sampleJson = '''
    {
      "final_decision": "BUY",
      "confidence": 0.85,
      "risk_manager_report": "Low risk, high reward",
      "market_report": "Bullish trend",
      "fundamentals_report": "Strong earnings",
      "debate_manager_report": "Consensus reached"
    }
    ''';
    
    test('parseDecision extracts correctly', () {
      expect(ResultParser.parseDecision(sampleJson), TradeDecision.buy);
      expect(ResultParser.parseDecision(null), null);
      expect(ResultParser.parseDecision('invalid'), null);
    });
    
    test('parseConfidence handles different formats', () {
      expect(ResultParser.parseConfidence(sampleJson), 0.85);
      expect(ResultParser.parseConfidence('{"confidence": 85}'), 0.85);
      expect(ResultParser.parseConfidence('{"confidence_level": 0.75}'), 0.75);
    });
    
    test('parseAgentReports extracts all reports', () {
      final reports = ResultParser.parseAgentReports(sampleJson);
      expect(reports.length, 2);
      expect(reports[0].type, 'market');
      expect(reports[0].content, 'Bullish trend');
    });
  });
}
```

#### Task 1.4: Create ParsedAnalysis Model
**Duration**: 1 hour
**Dependencies**: Tasks 1.1, 1.2, 1.3
**Input**: AnalysisRecord
**Output**: ParsedAnalysis with all extracted data
**Test Command**: `flutter test test/features/analyst_details/models/parsed_analysis_test.dart`

```dart
// Implementation: lib/features/analyst_details/models/parsed_analysis.dart
class ParsedAnalysis {
  final AnalysisRecord record;
  final TradeDecision? decision;
  final double? confidence;
  final String? riskReport;
  final List<AgentReport> agentReports;
  final String? debateReport;
  
  ParsedAnalysis({
    required this.record,
    this.decision,
    this.confidence,
    this.riskReport,
    this.agentReports = const [],
    this.debateReport,
  });
  
  factory ParsedAnalysis.fromRecord(AnalysisRecord record) {
    return ParsedAnalysis(
      record: record,
      decision: ResultParser.parseDecision(record.result),
      confidence: ResultParser.parseConfidence(record.result),
      riskReport: ResultParser.parseRiskReport(record.result),
      agentReports: ResultParser.parseAgentReports(record.result),
      debateReport: ResultParser.parseDebateReport(record.result),
    );
  }
  
  bool get hasDecision => decision != null;
  bool get hasRiskReport => riskReport != null && riskReport!.isNotEmpty;
  bool get hasAgentReports => agentReports.isNotEmpty;
  String get displayConfidence => confidence != null 
    ? '${(confidence! * 100).round()}%' 
    : '';
}
```

### Phase 2: Widget Components (Day 3-4)
**Goal**: Build reusable UI components

#### Task 2.1: Create DecisionHeader Widget
**Duration**: 1 hour
**Dependencies**: Task 1.1
**Input**: Ticker, datetime, decision, confidence
**Output**: Formatted header UI
**Test Command**: `flutter test test/features/analyst_details/widgets/decision_header_test.dart`

```dart
// Implementation: lib/features/analyst_details/widgets/decision_header.dart
class DecisionHeader extends StatelessWidget {
  final String ticker;
  final DateTime analyzeTime;
  final TradeDecision? decision;
  final double? confidence;
  
  const DecisionHeader({
    Key? key,
    required this.ticker,
    required this.analyzeTime,
    this.decision,
    this.confidence,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            ticker,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Analyzed: ${_formatDateTime(analyzeTime)}',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 16),
          if (decision != null) _buildDecisionBadge(context),
        ],
      ),
    );
  }
  
  Widget _buildDecisionBadge(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: decision!.color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: decision!.color, width: 2),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(decision!.icon, color: decision!.color, size: 20),
          const SizedBox(width: 8),
          Text(
            decision!.displayName,
            style: TextStyle(
              color: decision!.color,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          if (confidence != null) ...[
            const SizedBox(width: 8),
            Text(
              '${(confidence! * 100).round()}% Confidence',
              style: TextStyle(
                color: decision!.color.withOpacity(0.8),
                fontSize: 14,
              ),
            ),
          ],
        ],
      ),
    );
  }
  
  String _formatDateTime(DateTime dt) {
    return '${dt.month}/${dt.day}/${dt.year} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
  }
}
```

#### Task 2.2: Create RiskReportView Widget
**Duration**: 45 minutes
**Dependencies**: None
**Input**: Risk report text
**Output**: Scrollable formatted view
**Test Command**: `flutter test test/features/analyst_details/widgets/risk_report_view_test.dart`

```dart
// Implementation: lib/features/analyst_details/widgets/risk_report_view.dart
class RiskReportView extends StatelessWidget {
  final String? report;
  
  const RiskReportView({
    Key? key,
    this.report,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Risk Manager Final Decision',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
                ),
              ),
              child: SingleChildScrollView(
                child: Text(
                  report ?? 'Risk assessment report will appear here once the analysis is complete.',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
```

#### Task 2.3: Create AgentReportButton Widget
**Duration**: 45 minutes
**Dependencies**: None
**Input**: Title, hasContent flag, onTap callback
**Output**: Styled button
**Test Command**: `flutter test test/features/analyst_details/widgets/agent_report_button_test.dart`

```dart
// Implementation: lib/features/analyst_details/widgets/agent_report_button.dart
class AgentReportButton extends StatelessWidget {
  final String title;
  final bool hasContent;
  final VoidCallback? onTap;
  
  const AgentReportButton({
    Key? key,
    required this.title,
    required this.hasContent,
    this.onTap,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    final isEnabled = hasContent && onTap != null;
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Material(
        color: isEnabled 
          ? Theme.of(context).colorScheme.surface
          : Theme.of(context).colorScheme.surface.withOpacity(0.5),
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: isEnabled ? onTap : null,
          borderRadius: BorderRadius.circular(8),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              border: Border.all(
                color: isEnabled
                  ? Theme.of(context).colorScheme.outline.withOpacity(0.3)
                  : Theme.of(context).colorScheme.outline.withOpacity(0.1),
              ),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w500,
                      color: isEnabled 
                        ? Theme.of(context).colorScheme.onSurface
                        : Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
                    ),
                  ),
                ),
                Icon(
                  Icons.chevron_right,
                  color: isEnabled
                    ? Theme.of(context).colorScheme.onSurfaceVariant
                    : Theme.of(context).colorScheme.onSurfaceVariant.withOpacity(0.3),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

#### Task 2.4: Create ReportModal Widget
**Duration**: 1 hour
**Dependencies**: None
**Input**: Title, content
**Output**: Full-screen modal
**Test Command**: `flutter test test/features/analyst_details/widgets/report_modal_test.dart`

```dart
// Implementation: lib/features/analyst_details/widgets/report_modal.dart
class ReportModal extends StatelessWidget {
  final String title;
  final String content;
  
  const ReportModal({
    Key? key,
    required this.title,
    required this.content,
  }) : super(key: key);
  
  static Future<void> show({
    required BuildContext context,
    required String title,
    required String content,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => ReportModal(
        title: title,
        content: content,
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.9,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Handle bar
              Container(
                margin: const EdgeInsets.only(top: 12),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.outline.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              // Header
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              // Content
              Expanded(
                child: SingleChildScrollView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    content,
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
```

### Phase 3: Page Integration (Day 5-6)
**Goal**: Integrate components into pages

#### Task 3.1: Create AnalysisDetailPage
**Duration**: 2 hours
**Dependencies**: All Phase 1 & 2 tasks
**Input**: AnalysisRecord
**Output**: Complete detail page
**Test Command**: `flutter test test/features/analyst_details/pages/analysis_detail_page_test.dart`

```dart
// Implementation: lib/features/analyst_details/pages/analysis_detail_page.dart
class AnalysisDetailPage extends StatefulWidget {
  final AnalysisRecord record;
  
  const AnalysisDetailPage({
    Key? key,
    required this.record,
  }) : super(key: key);
  
  @override
  State<AnalysisDetailPage> createState() => _AnalysisDetailPageState();
}

class _AnalysisDetailPageState extends State<AnalysisDetailPage> {
  late ParsedAnalysis parsed;
  
  @override
  void initState() {
    super.initState();
    parsed = ParsedAnalysis.fromRecord(widget.record);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.record.ticker} Analysis'),
        backgroundColor: Theme.of(context).colorScheme.surface,
        elevation: 1,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: Column(
        children: [
          // Header Section (25%)
          Expanded(
            flex: 1,
            child: DecisionHeader(
              ticker: widget.record.ticker,
              analyzeTime: widget.record.completedAt ?? widget.record.createdAt,
              decision: parsed.decision,
              confidence: parsed.confidence,
            ),
          ),
          
          // Risk Report Section (50%)
          Expanded(
            flex: 2,
            child: RiskReportView(
              report: parsed.riskReport,
            ),
          ),
          
          // Agent Reports Section (25%)
          Expanded(
            flex: 1,
            child: _buildAgentReports(),
          ),
        ],
      ),
    );
  }
  
  Widget _buildAgentReports() {
    final reportButtons = [
      _createReportButton('📊 Market Analysis', 'market'),
      _createReportButton('📈 Fundamentals Report', 'fundamentals'),
      _createReportButton('🎭 Sentiment Analysis', 'sentiment'),
      _createReportButton('📰 News Analysis', 'news'),
      _createDebateButton(),
    ];
    
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: reportButtons.map((button) => Expanded(child: button)).toList(),
      ),
    );
  }
  
  Widget _createReportButton(String title, String type) {
    final report = parsed.agentReports.firstWhere(
      (r) => r.type == type,
      orElse: () => AgentReport.empty(type, title),
    );
    
    return AgentReportButton(
      title: title,
      hasContent: report.hasContent,
      onTap: report.hasContent 
        ? () => _showReport(title, report.content)
        : null,
    );
  }
  
  Widget _createDebateButton() {
    return AgentReportButton(
      title: '⚖️ Debate Manager Summary',
      hasContent: parsed.debateReport != null,
      onTap: parsed.debateReport != null
        ? () => _showReport('Debate Manager Summary', parsed.debateReport!)
        : null,
    );
  }
  
  void _showReport(String title, String content) {
    ReportModal.show(
      context: context,
      title: title,
      content: content,
    );
  }
}
```

#### Task 3.2: Enhance SimpleAnalysisPage List Item
**Duration**: 1 hour
**Dependencies**: Task 1.1, 1.4
**Input**: Existing list item code
**Output**: Enhanced with decision icons
**Test Command**: `flutter test test/pages/simple_analysis_page_test.dart`

```dart
// Modification: lib/pages/simple_analysis_page.dart
// Add import at top
import '../features/analyst_details/models/parsed_analysis.dart';
import '../features/analyst_details/pages/analysis_detail_page.dart';

// Modify _buildAnalysisCard method
Widget _buildAnalysisCard(AnalysisRecord analysis) {
  final parsed = ParsedAnalysis.fromRecord(analysis);
  final statusColor = _getAnalysisStatusColor(analysis.status);
  final isComplete = analysis.status.toLowerCase() == 'success' || 
                     analysis.status.toLowerCase() == 'completed';
  
  // Decision display logic
  final decisionColor = isComplete && parsed.hasDecision 
    ? parsed.decision!.color 
    : statusColor;
  final decisionIcon = isComplete && parsed.hasDecision
    ? parsed.decision!.icon
    : _getAnalysisStatusIcon(analysis.status);
  
  return Dismissible(
    key: Key(analysis.id),
    direction: DismissDirection.endToStart,
    // ... existing dismissible configuration ...
    child: Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: decisionColor.withOpacity(0.2),
          child: Icon(
            decisionIcon,
            color: decisionColor,
            size: 20,
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                analysis.ticker,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ),
            if (isComplete && parsed.hasDecision)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: decisionColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: decisionColor.withOpacity(0.3)),
                ),
                child: Text(
                  parsed.decision!.displayName,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: decisionColor,
                  ),
                ),
              ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Trade Date: ${analysis.tradeDate}'),
            if (!isComplete)
              Text(
                'Status: ${analysis.status}',
                style: TextStyle(color: statusColor),
              ),
            if (isComplete && parsed.displayConfidence.isNotEmpty)
              Text(
                'Confidence: ${parsed.displayConfidence}',
                style: TextStyle(color: Colors.grey[600]),
              ),
          ],
        ),
        trailing: // ... existing trailing widget ...
        onTap: isComplete ? () => _navigateToDetail(analysis) : null,
      ),
    ),
  );
}

// Add navigation method
void _navigateToDetail(AnalysisRecord analysis) {
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => AnalysisDetailPage(record: analysis),
    ),
  );
}
```

### Phase 4: Testing & Polish (Day 7-8)
**Goal**: Comprehensive testing and refinement

#### Task 4.1: Unit Test Suite
**Duration**: 2 hours
**Dependencies**: All previous tasks
**Input**: All components
**Output**: Complete unit test coverage
**Test Command**: `flutter test test/features/analyst_details/`

#### Task 4.2: Widget Test Suite
**Duration**: 2 hours
**Dependencies**: All widget tasks
**Input**: All widgets
**Output**: Widget interaction tests
**Test Command**: `flutter test test/features/analyst_details/widgets/`

#### Task 4.3: Integration Test
**Duration**: 2 hours
**Dependencies**: All tasks
**Input**: Complete flow
**Output**: End-to-end test
**Test Command**: `flutter test integration_test/analyst_details_test.dart`

```dart
// Integration test: integration_test/analyst_details_test.dart
void main() {
  testWidgets('Complete analyst details flow', (tester) async {
    // Setup mock data
    final mockRecord = AnalysisRecord(
      id: 'test-1',
      ticker: 'AAPL',
      tradeDate: '2024-01-01',
      status: 'success',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
      completedAt: DateTime.now(),
      result: '''
      {
        "final_decision": "BUY",
        "confidence": 0.85,
        "risk_manager_report": "Low risk profile with strong fundamentals",
        "market_report": "Bullish trend confirmed",
        "fundamentals_report": "Excellent earnings growth",
        "sentiment_report": "Positive market sentiment",
        "news_report": "Recent product launch success",
        "debate_manager_report": "Strong consensus for BUY"
      }
      ''',
    );
    
    // Test list item display
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: _buildAnalysisCard(mockRecord),
        ),
      ),
    );
    
    expect(find.text('AAPL'), findsOneWidget);
    expect(find.text('BUY'), findsOneWidget);
    expect(find.byIcon(Icons.trending_up), findsOneWidget);
    
    // Test navigation to detail
    await tester.tap(find.byType(ListTile));
    await tester.pumpAndSettle();
    
    expect(find.text('AAPL Analysis'), findsOneWidget);
    expect(find.text('85% Confidence'), findsOneWidget);
    expect(find.text('Risk Manager Final Decision'), findsOneWidget);
    
    // Test report modal
    await tester.tap(find.text('📊 Market Analysis'));
    await tester.pumpAndSettle();
    
    expect(find.text('Bullish trend confirmed'), findsOneWidget);
    
    // Test modal close
    await tester.tap(find.byIcon(Icons.close));
    await tester.pumpAndSettle();
    
    expect(find.text('Bullish trend confirmed'), findsNothing);
  });
}
```

#### Task 4.4: Performance Optimization
**Duration**: 1 hour
**Dependencies**: All tasks
**Input**: Complete implementation
**Output**: Optimized performance
**Metrics**: <200ms page load, smooth animations

#### Task 4.5: Documentation
**Duration**: 1 hour
**Dependencies**: All tasks
**Input**: Complete implementation
**Output**: Developer documentation
**Deliverable**: README.md with setup and usage instructions

## Quality Gates

### Code Quality Checklist
- [ ] All tests passing (unit, widget, integration)
- [ ] No linting warnings
- [ ] Code coverage > 80%
- [ ] Performance metrics met
- [ ] Documentation complete

### User Experience Checklist
- [ ] BUY/SELL/HOLD icons clearly visible
- [ ] Navigation smooth and intuitive
- [ ] All reports accessible
- [ ] Error states handled gracefully
- [ ] Loading states properly displayed

### Technical Checklist
- [ ] No breaking changes to existing code
- [ ] Existing AnalysisRecord structure unchanged
- [ ] All parsing handles null/malformed data
- [ ] Memory leaks checked
- [ ] No console errors or warnings

## Risk Mitigation

### Potential Risks and Mitigations

1. **Risk**: JSON structure varies between analyses
   **Mitigation**: Defensive parsing with fallbacks and null checks

2. **Risk**: Large report content causes performance issues
   **Mitigation**: Implement lazy loading and pagination if needed

3. **Risk**: Navigation conflicts with existing routes
   **Mitigation**: Use unique route names and test navigation stack

4. **Risk**: Theme compatibility issues
   **Mitigation**: Use Theme.of(context) for all colors and styles

5. **Risk**: Database migration needed
   **Mitigation**: None required - using existing structure

## Success Criteria

### Functional Requirements Met
- ✅ Pending analyses show loading icon
- ✅ Completed analyses show BUY/SELL/HOLD icon
- ✅ Tap navigates to detail page
- ✅ Back button returns to list
- ✅ Header shows ticker, time, decision, confidence
- ✅ Risk report displayed in scrollable view
- ✅ Five report buttons displayed
- ✅ Modal overlays show full reports

### Non-Functional Requirements Met
- ✅ Zero breaking changes
- ✅ <200ms page load time
- ✅ Smooth animations
- ✅ >80% test coverage
- ✅ Fully compatible with existing code

This implementation plan provides a clear, testable path to implementing the analyst result UI display feature while maintaining full compatibility with the existing codebase.