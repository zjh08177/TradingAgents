# macOS Network Permissions Fix

## Problem
The Flutter macOS app couldn't connect to `localhost:8000` due to App Sandbox restrictions:
```
ClientException with SocketException: Connection failed (OS Error: Operation not permitted, errno = 1)
```

## Root Cause
macOS apps run in a sandbox that restricts network access by default. The entitlements files were missing network client permissions.

## Solution
Added network permissions to both entitlements files:

### 1. DebugProfile.entitlements
```xml
<key>com.apple.security.network.client</key>
<true/>
```

### 2. Release.entitlements  
```xml
<key>com.apple.security.network.client</key>
<true/>
<key>com.apple.security.network.server</key>
<true/>
```

## Files Modified
- `macos/Runner/DebugProfile.entitlements` - Added network client permission
- `macos/Runner/Release.entitlements` - Added both client and server permissions

## Verification
1. **Server Health Check**: `curl http://localhost:8000/health` returns `{"status":"healthy"}`
2. **Flutter Test**: Run `dart test_network_fix.dart` for verification
3. **App Test**: `flutter run -d macos` should now connect successfully

## Additional Fix: Use 127.0.0.1 instead of localhost
Changed server URL from `http://localhost:8000` to `http://127.0.0.1:8000` in Flutter app to avoid DNS resolution timeouts on macOS.

## Expected Result
✅ Flutter app connects to LangGraph server at `http://127.0.0.1:8000`
✅ Health check passes within 5 seconds
✅ Automated TSLA analysis triggers after 2 seconds
✅ Test script: `dart test_network_fix.dart` shows SUCCESS 