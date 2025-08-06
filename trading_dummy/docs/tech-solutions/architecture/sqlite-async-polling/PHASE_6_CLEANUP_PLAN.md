# Phase 6: Hive Cleanup Plan

## Overview
Phase 6 involves removing Hive dependencies after successful migration. However, this should be done **conditionally** based on migration completion and confidence.

## Current Hive Usage

### Hive Files Still in Codebase:
1. **Models** (8 files):
   - `lib/history/infrastructure/models/hive_*.dart`
   - `lib/jobs/infrastructure/models/hive_*.dart`

2. **Repositories** (2 files):
   - `lib/history/infrastructure/repositories/hive_history_repository.dart`
   - `lib/jobs/infrastructure/repositories/hive_job_repository.dart`

3. **Files Using Hive** (9 locations):
   - `lib/main.dart` - Initialization and fallback
   - `lib/services/service_provider.dart` - Fallback repository creation
   - `lib/migration/services/*.dart` - Source for migration
   - `lib/debug/screens/sqlite_migration_test_screen.dart` - Comparison testing
   - `lib/jobs/test_utils/queue_test_widget.dart` - Test utilities

## Cleanup Strategy

### Option 1: Full Cleanup (Not Recommended Yet)
Remove all Hive code immediately. This is risky as:
- No fallback if SQLite has issues
- Cannot rollback migration
- Cannot compare implementations

### Option 2: Conditional Cleanup (Recommended)
Keep Hive code but make it conditionally compiled/loaded:

```dart
// Add a compile-time flag
const bool ENABLE_HIVE_SUPPORT = bool.fromEnvironment(
  'ENABLE_HIVE_SUPPORT',
  defaultValue: true, // Keep true until confident
);
```

### Option 3: Gradual Deprecation (Best Approach)
1. **Stage 1** (Current): Keep all Hive code for migration and fallback
2. **Stage 2** (After 100% rollout): Mark Hive code as deprecated
3. **Stage 3** (After 30 days stable): Remove Hive imports from main code
4. **Stage 4** (After 60 days): Remove Hive files completely

## Implementation Steps for Gradual Deprecation

### Stage 1: Current State ✅
- All Hive code remains
- Migration system uses Hive as source
- Fallback to Hive when needed

### Stage 2: Mark as Deprecated
```dart
@deprecated('Use SQLite repositories instead. Will be removed in v2.0.0')
class HiveHistoryRepository implements IHistoryRepository {
  // ...
}
```

### Stage 3: Isolate Hive Code
1. Create `lib/legacy/hive/` directory
2. Move all Hive files there
3. Update imports to show legacy status
4. Remove from main initialization flow

### Stage 4: Complete Removal
1. Delete `lib/legacy/hive/` directory
2. Remove Hive from pubspec.yaml
3. Remove Hive initialization from main.dart
4. Simplify ServiceProvider to SQLite only

## Verification Plan for Safe Cleanup

### Pre-Cleanup Checklist:
- [ ] Migration status shows "completed" for all users
- [ ] 100% rollout percentage achieved
- [ ] No rollbacks in last 30 days
- [ ] Performance metrics stable or improved
- [ ] No Hive-related errors in logs
- [ ] All data successfully migrated
- [ ] Backup of Hive data exists

### In-App Verification Steps:

#### 1. Check Migration Status
```dart
// In Migration Control Screen
- Status: "Completed"
- Rollout: 100%
- Database: SQLite
- No errors reported
```

#### 2. Verify Data Integrity
```dart
// In SQLite Migration Test Screen
- Run "Migration Test"
- Verify counts match
- Run performance tests
- All tests pass
```

#### 3. Test Without Hive
```bash
# Run app with Hive disabled
flutter run --dart-define=ENABLE_HIVE_SUPPORT=false

# Verify:
- App starts normally
- All features work
- No errors in console
```

#### 4. Production Monitoring
- Monitor crash reports for 30 days
- Check performance metrics
- Verify no data loss reports
- Confirm user satisfaction

## Code Changes for Conditional Hive

### 1. Update main.dart
```dart
// Conditional Hive initialization
if (const bool.fromEnvironment('ENABLE_HIVE_SUPPORT', defaultValue: true)) {
  await Hive.initFlutter();
  Hive.registerAdapter(HiveHistoryEntryAdapter());
  // ... other adapters
}
```

### 2. Update ServiceProvider
```dart
static IHistoryRepository _createHistoryRepository(MigrationManager? manager) {
  // Check if Hive is disabled
  if (!const bool.fromEnvironment('ENABLE_HIVE_SUPPORT', defaultValue: true)) {
    return SQLiteHistoryRepository();
  }
  
  // Existing logic for migration-based selection
  // ...
}
```

### 3. Update Migration Services
```dart
// Make migration services handle missing Hive gracefully
if (!ENABLE_HIVE_SUPPORT) {
  return MigrationResult(
    success: true,
    message: 'Hive support disabled, using SQLite only',
  );
}
```

## Testing the Cleanup

### Test Scenarios:

1. **Test with Hive Enabled** (Current)
   ```bash
   flutter test
   ```

2. **Test with Hive Disabled**
   ```bash
   flutter test --dart-define=ENABLE_HIVE_SUPPORT=false
   ```

3. **Test Migration Path**
   - Start with Hive enabled
   - Perform migration
   - Disable Hive
   - Verify app still works

4. **Test Fresh Install**
   - Clear all app data
   - Run with Hive disabled
   - Verify SQLite-only path works

## Monitoring Dashboard

Create a monitoring view in Migration Control Screen:

### Metrics to Track:
- Current database in use (Hive vs SQLite)
- Number of operations per database
- Error rates by database type
- Performance comparison
- User distribution

### Success Criteria for Cleanup:
- 0% users on Hive for 30+ days
- 0 Hive-related errors for 30+ days
- All features working with SQLite
- Performance metrics stable or improved
- Successful rollback test completed

## Rollback Plan

If issues arise after cleanup:

1. **Immediate**: Revert git commit removing Hive
2. **Deploy**: Release update with Hive restored
3. **Enable**: Set ENABLE_HIVE_SUPPORT=true
4. **Investigate**: Analyze what went wrong
5. **Fix**: Address issues before attempting again

## Timeline

### Recommended Schedule:
- **Week 1-2**: 100% SQLite rollout in production
- **Week 3-4**: Monitor metrics, fix any issues
- **Week 5-6**: Mark Hive as deprecated
- **Week 7-8**: Move Hive to legacy directory
- **Week 9-12**: Continue monitoring
- **Week 13**: Complete removal if stable

## Conclusion

Phase 6 cleanup should be approached cautiously. The recommended approach is gradual deprecation with careful monitoring at each stage. Only proceed with complete removal after extended stable operation on SQLite-only configuration.