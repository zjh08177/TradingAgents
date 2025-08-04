# Task 1: Database Setup - In-App Verification Guide

## 🧪 HOW TO TEST DATABASE FUNCTIONALITY

### 1. Launch the App
```bash
flutter run
```

### 2. Login
- Use any authentication method (Google/Apple)

### 3. Access Database Test Screen
- On the Home screen, scroll down to "Development Testing" section
- Click the red button: **"🧪 Database Test (DELETE AFTER FEATURE)"**

### 4. Test Database Operations

#### Button Functions:
- **Test DB**: Runs a complete test sequence:
  1. Creates a new analysis record with pending status
  2. Retrieves the record to verify save
  3. Updates with a simulated runId
  4. Updates status to success with result
  5. Queries pending analyses count
  6. Gets status counts

- **Refresh**: Reloads all records from database

- **Clear All**: Deletes all analysis records (use with caution)

#### What to Verify:

1. **Save Operation**:
   - Click "Test DB"
   - Check logs show "✅ Saved: test-[timestamp]"
   - Record appears in the list above

2. **Update Operations**:
   - Logs show "✅ Updated with runId"
   - Logs show "✅ Updated status to success"
   - Record in list updates from "pending" to "success"

3. **Query Operations**:
   - Logs show pending count
   - Logs show status counts (e.g., {pending: 1, success: 2})

4. **Persistence**:
   - Create some records
   - Kill the app completely
   - Relaunch and check records are still there

5. **Error Handling**:
   - Database operations should not crash
   - Errors appear in logs with "❌" prefix

### 5. Visual Indicators

- **Pending**: Orange clock icon
- **Running**: Circular progress indicator
- **Success**: Green checkmark
- **Error**: Red error icon

### 6. Expected Database Path

The database is stored at:
- **iOS**: `~/Library/Developer/CoreSimulator/.../Documents/analysis.db`
- **Android**: `/data/data/com.example.trading_dummy/app_flutter/analysis.db`

### 7. Cleanup

**IMPORTANT**: This test screen is marked with TODO and should be deleted after the polling feature is complete. The button is intentionally styled in red to indicate it's temporary.

## Common Test Scenarios

### Test 1: Basic CRUD
1. Tap "Test DB" - creates and updates a record
2. Tap "Refresh" - verifies read operation
3. Check the record appears with correct status

### Test 2: Multiple Records
1. Tap "Test DB" multiple times
2. Each tap creates a new record with unique ID
3. Verify all records appear in the list

### Test 3: Status Updates
1. Create a record (Test DB)
2. Note the transition: pending → running → success
3. Verify timestamps update correctly

### Test 4: Database Persistence
1. Create several records
2. Force quit the app
3. Reopen and tap "Refresh"
4. All records should still be present

### Test 5: Clear Function
1. Create some records
2. Tap "Clear All"
3. List should be empty
4. Logs show "✅ Cleared all analyses"

## Notes

- The database uses SQLite with proper indexes for performance
- Singleton pattern ensures only one database instance
- Path provider ensures correct platform-specific storage
- Test mode support allows unit tests to use temporary paths