# Implementation Tasks & Test Plans

## Task Breakdown

### 🚀 Task 1: Create API Service Layer

**Description**: Implement direct server API integration service

**Subtasks**:
1. Create `AnalysisApiService` class
2. Implement `submitAnalysis` method
3. Implement `getJobHistory` method  
4. Implement `getJobStatus` method
5. Add Dio configuration
6. Add error handling
7. Add request/response logging

**Files to Create**:
- `lib/analysis/services/analysis_api_service.dart`
- `lib/analysis/services/api_config.dart`
- `test/analysis/services/analysis_api_service_test.dart`

**Test Plan**:
```dart
// Unit Tests
- ✓ submitAnalysis sends correct POST request
- ✓ submitAnalysis handles success response
- ✓ submitAnalysis handles error response
- ✓ getJobHistory sends correct GET request
- ✓ getJobHistory parses array response
- ✓ getJobStatus sends correct GET request
- ✓ Network errors throw meaningful exceptions
- ✓ Timeout handling works correctly

// Integration Tests
- ✓ Real API call to submit job
- ✓ Real API call to get history
- ✓ Error scenarios with mock server
```

---

### 🎯 Task 2: Implement Simplified Models

**Description**: Create simple, server-aligned data models

**Subtasks**:
1. Create `AnalysisRequest` model
2. Create `AnalysisStatus` model
3. Create `JobStatus` enum
4. Add JSON serialization
5. Remove old complex models
6. Update existing code references

**Files to Create**:
- `lib/analysis/models/analysis_request.dart`
- `lib/analysis/models/analysis_status.dart`
- `lib/analysis/models/job_status.dart`
- `test/analysis/models/models_test.dart`

**Test Plan**:
```dart
// Unit Tests
- ✓ AnalysisRequest toJson creates correct map
- ✓ AnalysisStatus fromJson parses all fields
- ✓ AnalysisStatus handles null optional fields
- ✓ JobStatus enum conversion works
- ✓ isComplete getter returns correct value
- ✓ isProcessing getter returns correct value
- ✓ Duration calculation is accurate
```

---

### 🔄 Task 3: Status Polling Service

**Description**: Implement real-time status updates via polling

**Subtasks**:
1. Create `StatusPollingService` class
2. Implement timer-based polling
3. Add stream controller for updates
4. Handle connection errors gracefully
5. Add start/stop polling methods
6. Implement dispose cleanup

**Files to Create**:
- `lib/analysis/services/status_polling_service.dart`
- `test/analysis/services/status_polling_service_test.dart`

**Test Plan**:
```dart
// Unit Tests
- ✓ startPolling initiates timer
- ✓ Polls at correct intervals (5s)
- ✓ stopPolling cancels timer
- ✓ Stream emits job updates
- ✓ Handles API errors without stopping
- ✓ dispose cleans up resources
- ✓ Initial poll happens immediately

// Widget Tests
- ✓ Updates trigger UI rebuilds
- ✓ Error states don't crash app
```

---

### 📱 Task 4: Analysis Submission UI

**Description**: Simple UI for submitting analysis requests

**Subtasks**:
1. Create `AnalysisScreen` widget
2. Add ticker input field
3. Add date picker
4. Add submit button
5. Show loading state
6. Display errors
7. Navigate to history on success

**Files to Create**:
- `lib/analysis/screens/analysis_screen.dart`
- `lib/analysis/view_models/analysis_view_model.dart`
- `test/analysis/screens/analysis_screen_test.dart`

**Test Plan**:
```dart
// Widget Tests
- ✓ Ticker input accepts text
- ✓ Date picker shows calendar
- ✓ Submit button disabled when loading
- ✓ Error message displays correctly
- ✓ Success navigates to history
- ✓ Form validation works

// Integration Tests
- ✓ Full submission flow works
- ✓ API errors show user message
```

---

### 📋 Task 5: History Screen Implementation

**Description**: Display job history with real-time updates

**Subtasks**:
1. Create `HistoryScreen` widget
2. Create `HistoryViewModel`
3. Implement job list display
4. Add pull-to-refresh
5. Show job status indicators
6. Add LangGraph trace links
7. Handle empty states

**Files to Create**:
- `lib/analysis/screens/history_screen.dart`
- `lib/analysis/view_models/history_view_model.dart`
- `lib/analysis/widgets/job_card.dart`
- `test/analysis/screens/history_screen_test.dart`

**Test Plan**:
```dart
// Widget Tests
- ✓ Shows loading indicator initially
- ✓ Displays job list when loaded
- ✓ Pull-to-refresh triggers reload
- ✓ Job cards show all information
- ✓ Status colors are correct
- ✓ Empty state shows message
- ✓ Trace links are tappable

// Integration Tests
- ✓ Real-time updates work
- ✓ New jobs appear automatically
- ✓ Status changes reflect
```

---

### 🔧 Task 6: Fix UI Overflow Issues

**Description**: Fix RenderFlex overflow errors

**Subtasks**:
1. Audit all Row widgets
2. Add Flexible/Expanded wrappers
3. Set text overflow properties
4. Test on small screens
5. Add responsive breakpoints
6. Fix constraint issues

**Files to Update**:
- All widget files with Row/Column layouts
- job_status_card.dart (main culprit)

**Test Plan**:
```dart
// Widget Tests
- ✓ No overflow on 320px width
- ✓ No overflow on 768px width  
- ✓ No overflow on 1024px width
- ✓ Text truncates properly
- ✓ Layout adapts to screen size

// Manual Tests
- ✓ Test on iPhone SE (small)
- ✓ Test on iPhone 14 
- ✓ Test on iPad
- ✓ Test with long ticker names
```

---

### 🗑️ Task 7: Remove Old Architecture

**Description**: Clean up all client-side queue code

**Subtasks**:
1. Remove JobQueueManager
2. Remove JobProcessor
3. Remove IsolateManager
4. Remove retry logic
5. Remove Hive repositories
6. Remove complex use cases
7. Update imports

**Files to Remove**:
- `lib/jobs/` entire directory
- All related test files
- Hive adapter registrations

**Test Plan**:
```dart
// Verification
- ✓ App builds without errors
- ✓ No unused imports
- ✓ No dead code warnings
- ✓ All tests pass
- ✓ No Hive references remain
```

---

### 🧪 Task 8: Comprehensive Testing

**Description**: Full test coverage for new architecture

**Subtasks**:
1. Write unit tests for all services
2. Write widget tests for all screens
3. Write integration tests
4. Add error scenario tests
5. Add performance tests
6. Document test commands

**Test Plan**:
```dart
// Coverage Goals
- Services: 90%+
- Models: 100%
- ViewModels: 85%+
- Widgets: 80%+
- Integration: Key flows

// Performance Tests
- ✓ API response time < 200ms
- ✓ UI updates at 60 FPS
- ✓ Memory usage stable
- ✓ No memory leaks
```

---

## Implementation Schedule

### Day 1: API & Models
- [ ] Task 1: API Service (4h)
- [ ] Task 2: Models (2h)
- [ ] Basic testing (2h)

### Day 2: Services & ViewModels  
- [ ] Task 3: Polling Service (3h)
- [ ] ViewModels (3h)
- [ ] Integration (2h)

### Day 3: UI Implementation
- [ ] Task 4: Analysis Screen (3h)
- [ ] Task 5: History Screen (3h)
- [ ] Task 6: Fix Overflows (2h)

### Day 4: Cleanup & Testing
- [ ] Task 7: Remove Old Code (2h)
- [ ] Task 8: Full Testing (4h)
- [ ] Documentation (2h)

### Day 5: Integration & Polish
- [ ] LangGraph Studio testing
- [ ] Performance optimization
- [ ] Final QA
- [ ] Deployment prep

## Success Metrics

1. **Functionality**
   - ✓ Direct server submission works
   - ✓ Jobs appear in LangGraph Studio
   - ✓ History updates in real-time
   - ✓ No UI overflow errors

2. **Performance**
   - ✓ API calls < 200ms
   - ✓ Polling efficient (low CPU)
   - ✓ Smooth UI (60 FPS)
   - ✓ Low memory footprint

3. **Code Quality**
   - ✓ 85%+ test coverage
   - ✓ No linting errors
   - ✓ Clear documentation
   - ✓ Simple, maintainable code

4. **User Experience**
   - ✓ Intuitive submission flow
   - ✓ Clear status indicators
   - ✓ Responsive design
   - ✓ Helpful error messages