import 'package:trading_dummy/history/domain/repositories/i_history_repository.dart';
import 'package:trading_dummy/history/domain/entities/history_entry.dart';

class MockHistoryRepository implements IHistoryRepository {
  List<HistoryEntry> _entries = [];
  bool _isLoading = false;
  String? _errorMessage;
  bool refreshCalled = false;

  void setEntries(List<HistoryEntry> entries) {
    _entries = entries;
    _isLoading = false;
    _errorMessage = null;
  }

  void setLoading(bool loading) {
    _isLoading = loading;
    if (loading) {
      _errorMessage = null;
    }
  }

  void setError(String error) {
    _errorMessage = error;
    _isLoading = false;
  }

  @override
  Future<List<HistoryEntry>> getAll() async {
    refreshCalled = true;
    
    if (_isLoading) {
      await Future.delayed(const Duration(milliseconds: 100));
      return [];
    }
    
    if (_errorMessage != null) {
      throw Exception(_errorMessage);
    }
    
    return _entries;
  }

  @override
  Future<HistoryEntry?> getById(String id) async {
    if (_errorMessage != null) {
      throw Exception(_errorMessage);
    }
    
    try {
      return _entries.firstWhere((entry) => entry.id == id);
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> save(HistoryEntry entry) async {
    if (_errorMessage != null) {
      throw Exception(_errorMessage);
    }
    
    final existingIndex = _entries.indexWhere((e) => e.id == entry.id);
    if (existingIndex >= 0) {
      _entries[existingIndex] = entry;
    } else {
      _entries.add(entry);
    }
  }

  @override
  Future<void> delete(String id) async {
    if (_errorMessage != null) {
      throw Exception(_errorMessage);
    }
    
    _entries.removeWhere((entry) => entry.id == id);
  }

  @override
  Future<void> clear() async {
    if (_errorMessage != null) {
      throw Exception(_errorMessage);
    }
    
    _entries.clear();
  }

  @override
  Future<List<HistoryEntry>> getByTicker(String ticker) async {
    if (_errorMessage != null) {
      throw Exception(_errorMessage);
    }
    
    return _entries.where((entry) => entry.ticker == ticker).toList();
  }

  @override
  Future<void> clear() async {
    if (_errorMessage != null) {
      throw Exception(_errorMessage);
    }
    
    _entries.clear();
  }
}