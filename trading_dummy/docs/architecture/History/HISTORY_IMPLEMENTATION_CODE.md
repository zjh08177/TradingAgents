# History Feature - Implementation Code & Examples

## 🔧 Complete Code Implementations

### 1. Domain Layer

#### history_entry.dart
```dart
import 'package:hive/hive.dart';
import 'package:uuid/uuid.dart';
import 'analysis_details.dart';

part 'history_entry.g.dart';

@HiveType(typeId: 0)
class HistoryEntry extends HiveObject {
  @HiveField(0)
  final String id;
  
  @HiveField(1)
  final String ticker;
  
  @HiveField(2)
  final String tradeDate;
  
  @HiveField(3)
  final DateTime timestamp;
  
  @HiveField(4)
  final String finalDecision;
  
  @HiveField(5)
  final double? confidence;
  
  @HiveField(6)
  final String summary;
  
  @HiveField(7)
  final AnalysisDetails details;
  
  @HiveField(8)
  final bool isError;
  
  @HiveField(9)
  final String? errorMessage;

  HistoryEntry({
    String? id,
    required this.ticker,
    required this.tradeDate,
    required this.timestamp,
    required this.finalDecision,
    this.confidence,
    required this.summary,
    required this.details,
    this.isError = false,
    this.errorMessage,
  }) : id = id ?? const Uuid().v4();
}
```

#### analysis_details.dart
```dart
import 'package:hive/hive.dart';

part 'analysis_details.g.dart';

@HiveType(typeId: 1)
class AnalysisDetails {
  @HiveField(0)
  final String? marketAnalysis;
  
  @HiveField(1)
  final String? fundamentals;
  
  @HiveField(2)
  final String? sentiment;
  
  @HiveField(3)
  final String? newsAnalysis;
  
  @HiveField(4)
  final String? bullArgument;
  
  @HiveField(5)
  final String? bearArgument;
  
  @HiveField(6)
  final String? investmentPlan;
  
  @HiveField(7)
  final Map<String, dynamic>? rawData;

  const AnalysisDetails({
    this.marketAnalysis,
    this.fundamentals,
    this.sentiment,
    this.newsAnalysis,
    this.bullArgument,
    this.bearArgument,
    this.investmentPlan,
    this.rawData,
  });

  bool get hasMeaningfulContent {
    return marketAnalysis != null ||
        fundamentals != null ||
        sentiment != null ||
        newsAnalysis != null ||
        bullArgument != null ||
        bearArgument != null ||
        investmentPlan != null;
  }
}
```

#### i_history_repository.dart
```dart
import '../entities/history_entry.dart';

abstract class IHistoryRepository {
  Future<void> save(HistoryEntry entry);
  Future<List<HistoryEntry>> getAll();
  Future<HistoryEntry?> getById(String id);
  Future<List<HistoryEntry>> getByTicker(String ticker);
  Future<void> delete(String id);
  Future<void> clear();
}
```

### 2. Infrastructure Layer

#### report_mapper.dart
```dart
import 'package:trading_dummy/models/final_report.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';
import 'package:trading_dummy/history/domain/value_objects/analysis_details.dart';

class ReportMapper {
  HistoryEntry map(FinalReport report) {
    if (report.isError) {
      return HistoryEntry(
        ticker: report.ticker,
        tradeDate: report.tradeDate,
        timestamp: report.timestamp,
        finalDecision: 'ERROR',
        summary: 'Analysis failed',
        details: AnalysisDetails(),
        isError: true,
        errorMessage: report.content,
      );
    }

    final decision = _extractDecision(report.content);
    final confidence = _extractConfidence(report.content);
    final summary = _generateSummary(report.content, decision);
    final details = _extractDetails(report);

    return HistoryEntry(
      ticker: report.ticker,
      tradeDate: report.tradeDate,
      timestamp: report.timestamp,
      finalDecision: decision,
      confidence: confidence,
      summary: summary,
      details: details,
      isError: false,
    );
  }

  String _extractDecision(String content) {
    final patterns = [
      RegExp(r'(?:final|trading)?\s*decision[:\s]+(\w+)', caseSensitive: false),
      RegExp(r'\b(BUY|SELL|HOLD)\b', caseSensitive: false),
    ];

    for (final pattern in patterns) {
      final match = pattern.firstMatch(content);
      if (match != null) {
        final decision = match.group(1)?.toUpperCase() ?? '';
        if (['BUY', 'SELL', 'HOLD'].contains(decision)) {
          return decision;
        }
      }
    }

    // Sentiment analysis fallback
    final buyCount = RegExp(r'\bbuy\b', caseSensitive: false).allMatches(content).length;
    final sellCount = RegExp(r'\bsell\b', caseSensitive: false).allMatches(content).length;
    
    if (buyCount > sellCount * 1.5) return 'BUY';
    if (sellCount > buyCount * 1.5) return 'SELL';
    return 'HOLD';
  }

  double? _extractConfidence(String content) {
    final pattern = RegExp(r'confidence[:\s]+(\d+(?:\.\d+)?)\s*%?', caseSensitive: false);
    final match = pattern.firstMatch(content);
    
    if (match != null) {
      final value = double.tryParse(match.group(1) ?? '');
      return value != null && value > 1 ? value / 100 : value;
    }
    
    return null;
  }

  String _generateSummary(String content, String decision) {
    final lines = content.split('\n').where((line) => line.trim().isNotEmpty);
    
    for (final line in lines) {
      if (line.toLowerCase().contains(decision.toLowerCase())) {
        final cleaned = line.replaceAll(RegExp(r'[#*]+'), '').trim();
        return cleaned.length > 150 ? '${cleaned.substring(0, 147)}...' : cleaned;
      }
    }
    
    return '$decision recommendation for ${content.contains('strong') ? 'strong' : 'moderate'} reasons';
  }

  AnalysisDetails _extractDetails(FinalReport report) {
    final content = report.content;
    final rawOutput = report.rawOutput;

    return AnalysisDetails(
      marketAnalysis: _extractSection(content, 'market') ?? 
                     rawOutput?['market_report']?.toString(),
      fundamentals: _extractSection(content, 'fundamentals') ?? 
                   rawOutput?['fundamentals_report']?.toString(),
      sentiment: _extractSection(content, 'sentiment') ?? 
                rawOutput?['sentiment_report']?.toString(),
      newsAnalysis: _extractSection(content, 'news') ?? 
                   rawOutput?['news_report']?.toString(),
      bullArgument: _extractSection(content, 'bull'),
      bearArgument: _extractSection(content, 'bear'),
      investmentPlan: _extractSection(content, 'investment plan') ?? 
                     rawOutput?['trader_investment_plan']?.toString(),
      rawData: rawOutput,
    );
  }

  String? _extractSection(String content, String sectionName) {
    final pattern = RegExp(
      '##\\s*[^#]*$sectionName[^#]*\\n+([^#]+)(?=##|\\Z)',
      caseSensitive: false,
      multiLine: true,
    );

    final match = pattern.firstMatch(content);
    return match?.group(1)?.trim();
  }
}
```

#### hive_history_repository.dart
```dart
import 'package:hive/hive.dart';
import '../../domain/repositories/i_history_repository.dart';
import '../../domain/entities/history_entry.dart';

class HiveHistoryRepository implements IHistoryRepository {
  static const String _boxName = 'history';
  late Box<HistoryEntry> _box;

  HiveHistoryRepository() {
    _box = Hive.box<HistoryEntry>(_boxName);
  }

  @override
  Future<void> save(HistoryEntry entry) async {
    try {
      await _box.put(entry.id, entry);
    } catch (e) {
      throw Exception('Failed to save history entry: $e');
    }
  }

  @override
  Future<List<HistoryEntry>> getAll() async {
    try {
      return _box.values.toList()
        ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
    } catch (e) {
      throw Exception('Failed to get history entries: $e');
    }
  }

  @override
  Future<HistoryEntry?> getById(String id) async {
    try {
      return _box.get(id);
    } catch (e) {
      throw Exception('Failed to get history entry: $e');
    }
  }

  @override
  Future<List<HistoryEntry>> getByTicker(String ticker) async {
    try {
      return _box.values
          .where((entry) => entry.ticker == ticker)
          .toList()
        ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
    } catch (e) {
      throw Exception('Failed to get history by ticker: $e');
    }
  }

  @override
  Future<void> delete(String id) async {
    try {
      await _box.delete(id);
    } catch (e) {
      throw Exception('Failed to delete history entry: $e');
    }
  }

  @override
  Future<void> clear() async {
    try {
      await _box.clear();
    } catch (e) {
      throw Exception('Failed to clear history: $e');
    }
  }
}
```

### 3. Application Layer

#### save_history_use_case.dart
```dart
import '../../domain/repositories/i_history_repository.dart';
import '../../infrastructure/mappers/report_mapper.dart';
import '../../../models/final_report.dart';

class SaveHistoryUseCase {
  final IHistoryRepository _repository;
  final ReportMapper _mapper;

  SaveHistoryUseCase(this._repository, this._mapper);

  Future<void> execute(FinalReport report) async {
    try {
      final entry = _mapper.map(report);
      await _repository.save(entry);
    } catch (e) {
      throw Exception('Failed to save history: $e');
    }
  }
}
```

### 4. Presentation Layer

#### history_view_model.dart
```dart
import 'package:flutter/foundation.dart';
import '../../domain/entities/history_entry.dart';
import '../../domain/repositories/i_history_repository.dart';

class HistoryViewModel extends ChangeNotifier {
  final IHistoryRepository _repository;
  
  List<HistoryEntry> _entries = [];
  bool _isLoading = false;
  String? _errorMessage;
  String _filterTicker = '';

  HistoryViewModel(this._repository) {
    loadHistory();
  }

  List<HistoryEntry> get entries => _filterTicker.isEmpty
      ? _entries
      : _entries.where((e) => e.ticker.contains(_filterTicker.toUpperCase())).toList();
  
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String get filterTicker => _filterTicker;
  int get totalCount => _entries.length;

  List<String> get uniqueTickers {
    final tickers = _entries.map((e) => e.ticker).toSet().toList();
    tickers.sort();
    return tickers;
  }

  Future<void> loadHistory() async {
    _setLoading(true);
    _clearError();

    try {
      _entries = await _repository.getAll();
      notifyListeners();
    } catch (e) {
      _setError('Failed to load history: $e');
    } finally {
      _setLoading(false);
    }
  }

  Future<void> deleteEntry(String id) async {
    try {
      await _repository.delete(id);
      _entries.removeWhere((e) => e.id == id);
      notifyListeners();
    } catch (e) {
      _setError('Failed to delete entry: $e');
    }
  }

  Future<void> clearAll() async {
    _setLoading(true);
    try {
      await _repository.clear();
      _entries.clear();
      notifyListeners();
    } catch (e) {
      _setError('Failed to clear history: $e');
    } finally {
      _setLoading(false);
    }
  }

  void setFilter(String ticker) {
    _filterTicker = ticker;
    notifyListeners();
  }

  void clearFilter() {
    _filterTicker = '';
    notifyListeners();
  }

  Future<void> refresh() => loadHistory();

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  void _setError(String message) {
    _errorMessage = message;
    notifyListeners();
  }

  void _clearError() {
    _errorMessage = null;
  }
}
```

#### history_list_item.dart
```dart
import 'package:flutter/material.dart';
import '../../domain/entities/history_entry.dart';

class HistoryListItem extends StatelessWidget {
  final HistoryEntry entry;
  final VoidCallback onTap;
  
  const HistoryListItem({
    super.key,
    required this.entry,
    required this.onTap,
  });
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ListTile(
        leading: _buildDecisionIcon(),
        title: Text(
          entry.ticker,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        subtitle: Text(entry.tradeDate),
        trailing: _buildConfidenceIndicator(),
        onTap: onTap,
      ),
    );
  }
  
  Widget _buildDecisionIcon() {
    final color = switch (entry.finalDecision) {
      'BUY' => Colors.green,
      'SELL' => Colors.red,
      _ => Colors.orange,
    };
    
    return CircleAvatar(
      backgroundColor: color.withOpacity(0.2),
      child: Text(
        entry.finalDecision[0],
        style: TextStyle(color: color, fontWeight: FontWeight.bold),
      ),
    );
  }
  
  Widget _buildConfidenceIndicator() {
    if (entry.confidence == null) return const SizedBox.shrink();
    
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          '${(entry.confidence! * 100).toStringAsFixed(0)}%',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        const Text(
          'confidence',
          style: TextStyle(fontSize: 10),
        ),
      ],
    );
  }
}
```

### 5. Integration Code

#### Updated main.dart
```dart
// Add to imports
import 'package:hive_flutter/hive_flutter.dart';
import 'history/domain/entities/history_entry.dart';
import 'history/domain/value_objects/analysis_details.dart';

// Add to main() after WidgetsFlutterBinding.ensureInitialized()
// Initialize Hive
AppLogger.info('main', '💾 Initializing Hive database...');
await Hive.initFlutter();

// Register Hive adapters
Hive.registerAdapter(HistoryEntryAdapter());
Hive.registerAdapter(AnalysisDetailsAdapter());

// Open Hive boxes
await Hive.openBox<HistoryEntry>('history');
AppLogger.info('main', '✅ Hive database initialized');
```

#### Updated ServiceProvider
```dart
import 'history/domain/repositories/i_history_repository.dart';
import 'history/infrastructure/repositories/hive_history_repository.dart';

class ServiceProvider extends InheritedWidget {
  final SimpleLangGraphService langGraphService;
  final AutoTestController autoTest;
  final IHistoryRepository historyRepository;
  
  ServiceProvider({
    super.key,
    required this.langGraphService,
    required this.autoTest,
    required super.child,
  }) : historyRepository = HiveHistoryRepository();

  static IHistoryRepository historyRepositoryOf(BuildContext context) {
    final provider = context.dependOnInheritedWidgetOfExactType<ServiceProvider>();
    assert(provider != null, 'No ServiceProvider found in context');
    return provider!.historyRepository;
  }
}
```

#### Analysis Integration
```dart
// In analysis_page_wrapper.dart, after receiving final report:
import 'package:trading_dummy/history/application/use_cases/save_history_use_case.dart';
import 'package:trading_dummy/history/infrastructure/mappers/report_mapper.dart';

void _handleAnalysisComplete(FinalReport report) async {
  try {
    final repository = ServiceProvider.historyRepositoryOf(context);
    final saveUseCase = SaveHistoryUseCase(repository, ReportMapper());
    
    await saveUseCase.execute(report);
    AppLogger.info('analysis_page', 'Analysis saved to history');
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Analysis saved to history'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  } catch (e) {
    AppLogger.error('analysis_page', 'Failed to save to history', e);
  }
}
```

## 🧪 Testing Examples

### Unit Test - Report Mapper
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/models/final_report.dart';
import 'package:trading_dummy/history/infrastructure/mappers/report_mapper.dart';

void main() {
  group('ReportMapper', () {
    final mapper = ReportMapper();
    
    test('extracts BUY decision correctly', () {
      final report = FinalReport(
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        content: 'Final trading decision: BUY with 85% confidence',
        timestamp: DateTime.now(),
      );
      
      final entry = mapper.map(report);
      
      expect(entry.finalDecision, equals('BUY'));
      expect(entry.confidence, equals(0.85));
    });
    
    test('handles error reports', () {
      final report = FinalReport(
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        content: 'Network error',
        timestamp: DateTime.now(),
        isError: true,
      );
      
      final entry = mapper.map(report);
      
      expect(entry.isError, isTrue);
      expect(entry.finalDecision, equals('ERROR'));
    });
  });
}
```

### Integration Test - Hive Repository
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:trading_dummy/history/infrastructure/repositories/hive_history_repository.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';

void main() {
  setUpAll(() async {
    await Hive.initFlutter();
    Hive.registerAdapter(HistoryEntryAdapter());
    Hive.registerAdapter(AnalysisDetailsAdapter());
  });

  test('HiveRepository persists data', () async {
    final box = await Hive.openBox<HistoryEntry>('test_history');
    final repo = HiveHistoryRepository();
    
    final entry = HistoryEntry(
      ticker: 'AAPL',
      tradeDate: '2024-01-15',
      timestamp: DateTime.now(),
      finalDecision: 'BUY',
      summary: 'Test',
      details: AnalysisDetails(),
    );
    
    await repo.save(entry);
    final retrieved = await repo.getById(entry.id);
    
    expect(retrieved?.ticker, equals('AAPL'));
    
    await box.clear();
    await box.close();
  });
}
```