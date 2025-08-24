# Apple Sign-In Quick Start Guide

## 🚨 Critical Path to Working Implementation

### Day 1: Apple Developer Setup (2-3 hours)
```bash
# 1. Apple Developer Portal
- [ ] Log in to developer.apple.com
- [ ] Enable Sign In with Apple for App ID: com.tradingDummy.zjh
- [ ] Create Service ID: com.tradingDummy.zjh.signin
- [ ] Generate Sign In with Apple Key (.p8 file)
- [ ] Note: TEAM_ID, KEY_ID, SERVICE_ID

# 2. Store credentials securely
mkdir -p ~/Documents/TradingAgents/trading_dummy/keys
mv ~/Downloads/AuthKey_*.p8 ./keys/apple_signin_key.p8
chmod 600 ./keys/apple_signin_key.p8

# 3. Create environment file
cat > .env.apple << EOF
APPLE_TEAM_ID=YOUR_TEAM_ID_HERE
APPLE_KEY_ID=YOUR_KEY_ID_HERE
APPLE_SERVICE_ID=com.tradingDummy.zjh.signin
APPLE_PRIVATE_KEY_PATH=./keys/apple_signin_key.p8
EOF
```

### Day 2: iOS Project Configuration (1-2 hours)
```bash
# 1. Open Xcode
cd ios
open Runner.xcworkspace

# 2. In Xcode:
# - Select Runner target
# - Go to Signing & Capabilities
# - Add "Sign In with Apple" capability
# - Ensure CODE_SIGN_ENTITLEMENTS = Runner/Runner.entitlements

# 3. Update minimum iOS version
# Edit ios/Podfile: platform :ios, '13.0'

# 4. Reinstall pods
pod deintegrate
pod install
cd ..
```

### Day 3: Code Implementation (3-4 hours)

#### Fix 1: Update AppleAuthService with Session Management
```dart
// lib/auth/services/apple_auth_service.dart
// Add these key changes:

class AppleAuthService implements IAuthService {
  final AuthStorageService _storageService;
  
  AppleAuthService({AuthStorageService? storageService})
      : _storageService = storageService ?? AuthStorageService();
  
  @override
  Future<UserModel?> signIn() async {
    // ... existing code ...
    
    // ADD: Save credentials after successful sign-in
    await _storageService.saveAppleCredentials(
      userId: userId,
      identityToken: credential.identityToken,
      authorizationCode: credential.authorizationCode,
      tokenExpiry: tokenExpiry,
    );
    
    return user;
  }
  
  @override
  Future<UserModel?> silentSignIn() async {
    // REPLACE the stub with:
    final credentials = await _storageService.getAppleCredentials();
    if (credentials == null) return null;
    
    final userId = credentials['userId'] as String;
    final credentialState = await getCredentialState(userId);
    
    if (credentialState != CredentialState.authorized) {
      await _storageService.clearAppleCredentials();
      return null;
    }
    
    final storedUser = await _storageService.getUser();
    return storedUser;
  }
  
  @override
  Future<bool> isSignedIn() async {
    // REPLACE the stub with:
    final hasCredentials = await _storageService.hasValidAppleCredentials();
    if (!hasCredentials) return false;
    
    final user = await silentSignIn();
    return user != null;
  }
}
```

#### Fix 2: Add Apple Credential Storage
```dart
// lib/auth/services/auth_storage_service.dart
// Add these methods:

static const String _appleCredentialsKey = 'apple_credentials';

Future<void> saveAppleCredentials({
  required String userId,
  required String? identityToken,
  required String? authorizationCode,
  required DateTime? tokenExpiry,
}) async {
  final credentials = {
    'userId': userId,
    'identityToken': identityToken,
    'authorizationCode': authorizationCode,
    'tokenExpiry': tokenExpiry?.toIso8601String(),
    'savedAt': DateTime.now().toIso8601String(),
  };
  
  await _secureStorage.write(
    key: _appleCredentialsKey,
    value: json.encode(credentials),
  );
}

Future<Map<String, dynamic>?> getAppleCredentials() async {
  final credentialsJson = await _secureStorage.read(key: _appleCredentialsKey);
  if (credentialsJson == null) return null;
  
  final credentials = json.decode(credentialsJson);
  
  // Check expiry
  if (credentials['tokenExpiry'] != null) {
    final expiry = DateTime.parse(credentials['tokenExpiry']);
    if (expiry.isBefore(DateTime.now())) {
      await clearAppleCredentials();
      return null;
    }
  }
  
  return credentials;
}

Future<bool> hasValidAppleCredentials() async {
  final credentials = await getAppleCredentials();
  return credentials != null && credentials['userId'] != null;
}
```

### Day 4: Testing (2-3 hours)

#### Create Mock Service for Testing
```dart
// test/auth/mocks/mock_apple_auth_service.dart
class MockAppleAuthService implements AppleAuthService {
  bool shouldSucceed = true;
  bool shouldCancel = false;
  
  @override
  Future<UserModel?> signIn() async {
    if (shouldCancel) return null;
    if (!shouldSucceed) throw Exception('Mock error');
    
    return UserModel(
      id: 'apple_test_123',
      email: 'test@privaterelay.appleid.com',
      displayName: 'Test User',
      provider: AuthProvider.apple,
      idToken: 'mock-token',
      accessToken: 'mock-access',
      tokenExpiryTime: DateTime.now().add(const Duration(days: 30)),
    );
  }
}
```

#### Run Tests
```bash
# Create test file
flutter test test/auth/apple_auth_service_test.dart

# Test on real device (REQUIRED - won't work on simulator)
flutter run --release
```

## ⚡ Rapid Implementation Checklist

### Essential Files to Modify (In Order)
1. ✅ `.env.apple` - Store your Apple credentials
2. ✅ `ios/Runner.xcodeproj/project.pbxproj` - Add CODE_SIGN_ENTITLEMENTS
3. ✅ `ios/Podfile` - Set platform :ios, '13.0'
4. ✅ `lib/auth/services/apple_auth_service.dart` - Fix silentSignIn() and isSignedIn()
5. ✅ `lib/auth/services/auth_storage_service.dart` - Add Apple credential methods
6. ✅ `test/auth/mocks/mock_apple_auth_service.dart` - Create mock for testing

### Commands to Run (In Order)
```bash
# 1. Install dependencies
flutter pub add sign_in_with_apple crypto flutter_secure_storage

# 2. iOS setup
cd ios
pod deintegrate
pod install
cd ..

# 3. Run tests
flutter test

# 4. Test on device
flutter run --release
```

## 🔥 Common Issues & Quick Fixes

### Issue: "Sign In with Apple isn't available"
```bash
# Fix: Update iOS deployment target
sed -i '' "s/IPHONEOS_DEPLOYMENT_TARGET = .*/IPHONEOS_DEPLOYMENT_TARGET = 13.0;/g" ios/Runner.xcodeproj/project.pbxproj
```

### Issue: Entitlements not found
```bash
# Fix: Link entitlements in Xcode or run:
ruby -e "
require 'xcodeproj'
project = Xcodeproj::Project.open('ios/Runner.xcodeproj')
project.targets.first.build_configurations.each do |config|
  config.build_settings['CODE_SIGN_ENTITLEMENTS'] = 'Runner/Runner.entitlements'
end
project.save
"
```

### Issue: Silent sign-in always returns null
```dart
// Fix: Ensure you're saving credentials on sign-in
// In apple_auth_service.dart signIn() method, add:
await _storageService.saveAppleCredentials(
  userId: userId,
  identityToken: credential.identityToken,
  authorizationCode: credential.authorizationCode,
  tokenExpiry: DateTime.now().add(const Duration(days: 30)),
);
```

## 📱 Testing on Physical Device

### Requirements
- Physical iPhone/iPad (iOS 13.0+)
- Device signed into iCloud
- Valid provisioning profile

### Test Scenarios
```dart
// 1. Test successful sign-in
await appleAuthService.signIn();
// Expected: Returns UserModel with Apple credentials

// 2. Test cancel
// User taps Cancel in Apple dialog
// Expected: Returns null, no error

// 3. Test silent sign-in
await appleAuthService.silentSignIn();
// Expected: Returns cached user if valid

// 4. Test sign-in status
await appleAuthService.isSignedIn();
// Expected: Returns true if valid credentials exist
```

## 🎯 Success Criteria

### Minimum Viable Implementation
- [ ] Apple Sign-In button visible on iOS devices
- [ ] User can sign in with Apple ID
- [ ] App receives user ID and email (if shared)
- [ ] User stays signed in across app restarts
- [ ] Sign out clears Apple credentials

### Production Ready
- [ ] Token validation on backend
- [ ] Refresh token handling
- [ ] Account linking with email
- [ ] Android web-based sign-in
- [ ] Comprehensive error handling
- [ ] Analytics tracking
- [ ] Accessibility compliance

## 📊 Time Estimate

### Minimum Implementation: 2-3 days
- Day 1: Apple Developer setup (2-3 hours)
- Day 2: iOS configuration (1-2 hours)
- Day 3: Code fixes (3-4 hours)
- Testing: 2-3 hours

### Full Implementation: 1-2 weeks
- Backend integration: 2-3 days
- Android support: 1-2 days
- Testing & QA: 2-3 days
- Documentation: 1 day

## 🆘 Get Help

### Resources
- [Apple Sign-In Documentation](https://developer.apple.com/sign-in-with-apple/)
- [Flutter Package Docs](https://pub.dev/packages/sign_in_with_apple)
- [Stack Overflow Tag](https://stackoverflow.com/questions/tagged/sign-in-with-apple)

### Common Search Terms
- "Sign In with Apple Flutter"
- "CODE_SIGN_ENTITLEMENTS Xcode"
- "Apple Sign-In not available iOS"
- "Silent sign in Apple Flutter"

### Debug Commands
```bash
# Check if entitlements are linked
grep -n "CODE_SIGN_ENTITLEMENTS" ios/Runner.xcodeproj/project.pbxproj

# Verify package is installed
flutter pub deps | grep sign_in_with_apple

# Check iOS deployment target
grep -n "IPHONEOS_DEPLOYMENT_TARGET" ios/Runner.xcodeproj/project.pbxproj

# Test on device with verbose logging
flutter run --verbose --release
```