# SQLite Migration Verification Guide

## Quick Start Verification

### 1. Run the App with SQLite
```bash
# Force SQLite usage for testing
flutter run --dart-define=USE_SQLITE=true
```

### 2. Access Migration Controls
1. Launch app and login
2. Go to Home Screen
3. Tap **"Migration Control"** tile (indigo color with admin icon)

## Complete Verification Checklist

### 📱 In-App Verification Screens

#### A. Migration Control Screen (`/migration-control`)
**Access**: Home → Migration Control

**What to Verify**:
- [ ] **Status Card**
  - Shows current migration status (Not Started → Completed)
  - Displays current database (Hive → SQLite)
  - Shows migration version number

- [ ] **Migration Actions**
  - "Start Migration" button works
  - Progress indicator appears during migration
  - Success/failure message displays
  - Validate button available after completion
  - Rollback button works (reverts to Hive)

- [ ] **Rollout Controls**
  - Slider adjusts from 0-100%
  - Percentage updates correctly
  - Current rollout percentage displays

- [ ] **Database Toggle**
  - Switch between Hive and SQLite
  - Immediate effect on data operations
  - Status updates accordingly

- [ ] **Statistics**
  - Accurate counts and metrics
  - Timestamp updates
  - Version tracking works

#### B. SQLite Migration Test Screen (`/sqlite-migration-test`)
**Access**: Home → SQLite Migration

**What to Verify**:
- [ ] **Side-by-Side Comparison**
  - Both repositories return same data
  - CRUD operations work identically
  - No data inconsistencies

- [ ] **Performance Tests**
  - SQLite performs equal or better than Hive
  - Bulk operations complete successfully
  - Query performance acceptable

- [ ] **Migration Test**
  - Data transfers completely
  - No data loss
  - Validation passes

- [ ] **Test Results**
  - All tests show green checkmarks
  - Performance metrics display
  - Can copy results to clipboard

### 🔬 Test Scenarios

#### Scenario 1: Fresh Install
```bash
# Clear app data first
flutter clean
flutter pub get
flutter run
```

**Verify**:
1. App starts without errors
2. Migration status shows "Not Started"
3. Using Hive by default
4. Can manually trigger migration

#### Scenario 2: Automatic Migration
```bash
# Run with fresh data
flutter run
```

**Verify**:
1. Check logs for "Starting automatic database migration"
2. Migration completes without intervention
3. Status changes to "Completed"
4. Data accessible through SQLite

#### Scenario 3: Manual Migration
1. Open Migration Control Screen
2. Tap "Start Migration"
3. Wait for completion

**Verify**:
- Progress indicator shows
- Success message appears
- Statistics update
- Can validate migration

#### Scenario 4: Gradual Rollout
1. Set rollout to 50%
2. Clear app data
3. Run app multiple times

**Verify**:
- Some launches use SQLite
- Some launches use Hive
- Consistent assignment per device

#### Scenario 5: Rollback
1. Complete migration
2. Use SQLite for a while
3. Tap "Rollback" in Migration Control

**Verify**:
- Status changes to "Rolled Back"
- Database switches to Hive
- All data still accessible
- Can re-migrate if needed

### 🧪 Development Testing

#### Test with SQLite Only
```bash
flutter run --dart-define=USE_SQLITE=true
```

**What to Test**:
- [ ] App launches successfully
- [ ] Can create new analysis
- [ ] History saves and loads
- [ ] Jobs queue works
- [ ] No Hive-related errors

#### Test with Hive Only
```bash
flutter run --dart-define=USE_SQLITE=false
```

**What to Test**:
- [ ] Existing Hive data loads
- [ ] Can still use Hive repositories
- [ ] Migration tools available
- [ ] No SQLite forced usage

#### Run All Tests
```bash
# Unit tests
flutter test

# Specific migration tests
flutter test test/migration/
flutter test test/history/infrastructure/repositories/sqlite_*
flutter test test/jobs/infrastructure/repositories/sqlite_*
```

**Expected Results**:
- All tests pass
- No deprecation warnings for SQLite
- Migration tests validate correctly

### 📊 Performance Verification

#### In Migration Test Screen:
1. Tap "Performance Tests"
2. Review the metrics table

**Expected Performance**:
| Operation | Hive | SQLite | Expected |
|-----------|------|--------|----------|
| Single Insert | ~5ms | ~3ms | SQLite faster ✅ |
| Bulk Insert (100) | ~500ms | ~300ms | SQLite faster ✅ |
| Query All | ~10ms | ~8ms | Similar ✅ |
| Query Filtered | ~5ms | ~3ms | SQLite faster ✅ |
| Delete | ~3ms | ~2ms | SQLite faster ✅ |

### 🔍 Data Integrity Verification

#### Check Data Consistency:
1. In Migration Test Screen
2. Run "History Tests" → Note counts
3. Run "Migration Test"
4. Verify counts match

**What to Verify**:
- [ ] All history entries migrated
- [ ] All jobs migrated
- [ ] Metadata preserved (priority, retry count)
- [ ] Timestamps accurate
- [ ] No null or corrupted data

### 📱 User Experience Verification

#### For End Users:
- [ ] No visible disruption during migration
- [ ] App performance same or better
- [ ] All features continue working
- [ ] No data loss
- [ ] No increase in crashes

#### For Developers:
- [ ] Clear migration status visibility
- [ ] Easy rollback if needed
- [ ] Detailed logs available
- [ ] Performance metrics accessible
- [ ] Test tools comprehensive

### 🚨 Common Issues & Solutions

#### Issue: Migration Fails
**Solution**:
1. Check logs in console
2. Verify both repositories initialized
3. Ensure sufficient storage
4. Try "Reset" then retry

#### Issue: Performance Degradation
**Solution**:
1. Run performance tests
2. Check for missing indexes
3. Verify batch sizes
4. Review query patterns

#### Issue: Data Not Showing
**Solution**:
1. Check migration status
2. Verify correct database selected
3. Run validation in Migration Control
4. Check for errors in logs

#### Issue: Can't Toggle Database
**Solution**:
1. Ensure migration completed
2. Check SharedPreferences permissions
3. Restart app after toggle
4. Clear app data if persistent

### ✅ Final Verification Checklist

Before considering migration complete:

- [ ] **Migration Testing**
  - [ ] All unit tests pass
  - [ ] Integration tests pass
  - [ ] Manual testing completed
  - [ ] Performance acceptable

- [ ] **Data Integrity**
  - [ ] All data migrated
  - [ ] No data corruption
  - [ ] Counts match exactly
  - [ ] Relationships preserved

- [ ] **User Experience**
  - [ ] No visible disruption
  - [ ] Performance maintained
  - [ ] All features work
  - [ ] Rollback tested

- [ ] **Production Readiness**
  - [ ] Gradual rollout tested
  - [ ] Monitoring in place
  - [ ] Rollback plan ready
  - [ ] Documentation complete

## Monitoring Commands

### Check Migration Status Programmatically
```dart
// Add this to any screen for debugging
final manager = await MigrationManager.create();
final stats = manager.getStatistics();
print('Status: ${stats.status}');
print('Using SQLite: ${stats.isUsingSQLite}');
print('Rollout: ${stats.rolloutPercentage}%');
```

### Force Migration State (Testing Only)
```dart
// In debug mode only
final manager = await MigrationManager.create();
await manager.clearMigrationData(); // Reset
await manager.performMigration(); // Force migration
await manager.rollback(); // Force rollback
```

## Production Deployment Steps

1. **Deploy with 0% rollout**
   - Monitor for any issues
   - Verify migration works for test users

2. **Increase to 5%**
   - Monitor performance metrics
   - Check error rates
   - Gather user feedback

3. **Increase to 25%**
   - Broader testing
   - Performance comparison
   - Stability verification

4. **Increase to 50%**
   - A/B testing complete
   - Performance validated
   - Ready for full rollout

5. **Increase to 100%**
   - All users on SQLite
   - Continue monitoring
   - Prepare for Hive cleanup

## Success Criteria

Migration is considered successful when:

1. ✅ 100% of users successfully migrated
2. ✅ Zero data loss reported
3. ✅ Performance metrics stable or improved
4. ✅ No increase in crash rate
5. ✅ No increase in error rate
6. ✅ User satisfaction maintained
7. ✅ All features functioning correctly
8. ✅ Rollback tested and working
9. ✅ 30 days stable operation
10. ✅ Ready for Hive removal