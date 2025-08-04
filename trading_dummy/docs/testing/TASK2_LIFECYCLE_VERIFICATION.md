# Task 2: App Lifecycle Service - In-App Verification Guide

## 🧪 HOW TO TEST APP LIFECYCLE FUNCTIONALITY

### 1. Launch the App
```bash
flutter run
```

### 2. Login
- Use any authentication method (Google/Apple)

### 3. Access Lifecycle Test Screen
- On the Home screen, scroll down to "Development Testing" section
- Click the orange button: **"🔄 Lifecycle Test (DELETE AFTER FEATURE)"**

### 4. Test App Lifecycle Transitions

#### What the Screen Shows:
- **Service Status**: Current initialization state and foreground/background status
- **Event Logs**: Real-time log of all lifecycle state changes
- **How to Test Instructions**: Built-in guide for testing

#### Testing Steps:

1. **Test Background/Foreground**:
   - Press the Home button (iOS) or Recent Apps button (Android)
   - App should log: "State changed to: Paused (Background)"
   - Return to the app
   - App should log: "State changed to: Resumed (Foreground)"

2. **Test App Switching**:
   - Switch to another app
   - Should see state transition logs
   - Return to the app
   - Should see "Resumed" state

3. **Test Screen Lock**:
   - Lock your device screen
   - Unlock and return to app
   - Check logs for state transitions

4. **Test Rapid Changes**:
   - Quickly switch between apps multiple times
   - All state changes should be logged

### 5. Button Functions

- **Check State**: Manually check and log current lifecycle state
- **Clear Logs**: Clear the event log history

### 6. Expected States

- **Resumed (Foreground)**: App is active and visible
- **Paused (Background)**: App is in background
- **Inactive**: App is transitioning (iOS specific)
- **Detached**: App is being terminated
- **Hidden**: App window is hidden

### 7. Visual Indicators

- **Green checkmark**: When app is in foreground
- **Red X**: When app is in background
- **Timestamps**: Each log entry shows exact time

### 8. Service Features to Verify

1. **Singleton Pattern**: 
   - Service maintains state across the app
   - Only one instance exists

2. **Stream Broadcasting**:
   - Real-time state change notifications
   - Multiple listeners supported

3. **Foreground Detection**:
   - `isInForeground` correctly reflects app state
   - Updates immediately on state changes

### 9. Common Test Scenarios

#### Test 1: Basic State Transitions
1. Open lifecycle test screen
2. Minimize app → See "Paused" log
3. Resume app → See "Resumed" log
4. Verify "Is Foreground" shows correct state

#### Test 2: Multiple Transitions
1. Switch apps rapidly 5 times
2. Each transition should be logged
3. Final state should match app's actual state

#### Test 3: Lock Screen
1. Lock device while app is open
2. Should see "Paused" state
3. Unlock and return → Should see "Resumed"

#### Test 4: Memory Management
1. Create many state changes (20+)
2. Logs should be limited to last 50 entries
3. No memory issues or crashes

### 10. Unit Test Verification

Run the comprehensive test suite:
```bash
flutter test test/jobs/infrastructure/services/app_lifecycle_service_test.dart
```

Expected output:
- 17 tests should pass
- Tests cover all lifecycle scenarios
- Including edge cases and rapid state changes

## Notes

- The lifecycle service uses Flutter's `WidgetsBindingObserver`
- Works consistently across iOS and Android
- Critical for the polling service to pause/resume based on app state
- This debug screen will be removed after polling feature completion