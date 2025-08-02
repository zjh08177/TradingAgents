# Wave 5 App Verification Guide

## 🔍 How to Verify Wave 5 (Hive Implementation) in the App

Since Wave 5 is the persistence layer and Wave 6 (Screens) hasn't been implemented yet, you'll need to verify through debugging or temporary test code.

## Method 1: Debug Verification (Recommended)

### 1. Add Debug Code to Analysis Integration
Temporarily add logging to verify Hive is working when an analysis completes.

In `analysis_page_wrapper.dart`, after the analysis completes:
```dart
// Temporary debug code
void _handleAnalysisComplete(FinalReport report) async {
  try {
    final repository = ServiceProvider.historyRepositoryOf(context);
    final saveUseCase = SaveHistoryUseCase(repository, ReportMapper());
    
    // Save to history
    await saveUseCase.execute(report);
    AppLogger.info('analysis_page', '✅ Analysis saved to history');
    
    // DEBUG: Verify it was saved
    final allEntries = await repository.getAll();
    AppLogger.info('DEBUG', '📊 Total history entries: ${allEntries.length}');
    AppLogger.info('DEBUG', '🎯 Latest entry: ${allEntries.firstOrNull?.ticker} - ${allEntries.firstOrNull?.finalDecision}');
    
    // Show snackbar...
  } catch (e) {
    AppLogger.error('analysis_page', 'Failed to save to history', e);
  }
}
```

### 2. Run the App and Test
```bash
flutter run
```

1. Login to the app
2. Navigate to Analysis page
3. Enter a ticker (e.g., "AAPL") and date
4. Click "Get Analysis Report"
5. Watch the console logs for:
   - "✅ Analysis saved to history"
   - "📊 Total history entries: 1"
   - "🎯 Latest entry: AAPL - BUY"

### 3. Verify Persistence
1. Kill the app completely
2. Run it again
3. Add the following debug code to check persistence:

In `main.dart` after Hive initialization:
```dart
// DEBUG: Check persisted data
final testRepo = HiveHistoryRepository();
final entries = await testRepo.getAll();
AppLogger.info('DEBUG', '🔍 Persisted entries on startup: ${entries.length}');
for (final entry in entries) {
  AppLogger.info('DEBUG', '  - ${entry.ticker}: ${entry.finalDecision} (${entry.tradeDate})');
}
```

## Method 2: Unit Test Verification

Run the comprehensive test suite:
```bash
# Run all history tests
flutter test test/history/

# Run specific Hive repository test
flutter test test/history/infrastructure/repositories/hive_history_repository_test.dart
```

Expected output:
```
00:01 +8: All tests passed!
```

## Method 3: Flutter Inspector

1. Run the app with Flutter Inspector
2. Use the console to execute:
```dart
// In debug console
final repo = HiveHistoryRepository();
await repo.getAll().then((entries) => print('Entries: ${entries.length}'));
```

## Method 4: Temporary Test Screen

Create a temporary test file `lib/test_history.dart`:
```dart
import 'package:flutter/material.dart';
import 'history/infrastructure/repositories/hive_history_repository.dart';
import 'history/domain/entities/history_entry.dart';
import 'history/domain/value_objects/analysis_details.dart';

class TestHistoryScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Test History')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () async {
                final repo = HiveHistoryRepository();
                
                // Add test entry
                final testEntry = HistoryEntry(
                  ticker: 'TEST',
                  tradeDate: '2024-01-15',
                  timestamp: DateTime.now(),
                  finalDecision: 'BUY',
                  confidence: 0.85,
                  summary: 'Test entry',
                  details: AnalysisDetails(),
                );
                
                await repo.save(testEntry);
                print('✅ Saved test entry');
                
                // Read all
                final all = await repo.getAll();
                print('📊 Total entries: ${all.length}');
                for (final entry in all) {
                  print('  - ${entry.ticker}: ${entry.finalDecision}');
                }
              },
              child: Text('Test Hive'),
            ),
          ],
        ),
      ),
    );
  }
}
```

Then temporarily add a button in the app to navigate to this screen.

## Expected Behaviors

### ✅ Working Correctly If:
1. Console shows "✅ Hive database initialized" on app start
2. Analysis results are saved without errors
3. Entry count increases after each analysis
4. Data persists after app restart
5. All repository tests pass

### ❌ Issues to Watch For:
1. `MissingPluginException` - Hive not initialized properly
2. `HiveError: Box not found` - Box not opened
3. Type errors - Adapter registration issues
4. Empty results after restart - Persistence not working

## Verification Checklist

- [ ] App starts without Hive initialization errors
- [ ] Analysis results save without exceptions
- [ ] Repository methods work (save, getAll, getById, etc.)
- [ ] Data persists between app sessions
- [ ] All unit tests pass
- [ ] No analyzer warnings related to Hive

## Next Steps

Once Wave 5 is verified working:
1. Remove all debug code
2. Proceed to Wave 6 (History & Detail Screens)
3. The screens will use the HistoryViewModel which uses the HiveHistoryRepository
4. Full end-to-end testing will be possible with UI