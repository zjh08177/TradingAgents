# Complete Apple Sign-In Implementation Guide

## Table of Contents
1. [iOS Configuration](#1-ios-configuration)
2. [Apple Developer Portal Setup](#2-apple-developer-portal-setup)
3. [Backend Integration](#3-backend-integration)
4. [Testing Implementation](#4-testing-implementation)
5. [Session Management](#5-session-management)
6. [Security Enhancements](#6-security-enhancements)
7. [Android Support](#7-android-support)
8. [Error Handling & UX](#8-error-handling--ux)
9. [Documentation](#9-documentation)

---

## 1. iOS Configuration

### 1.1 Link Entitlements File in Xcode

#### Step 1: Open Xcode Project
```bash
cd /Users/bytedance/Documents/TradingAgents/trading_dummy/ios
open Runner.xcworkspace  # Use workspace, not xcodeproj if pods are installed
```

#### Step 2: Add Entitlements to Build Settings
1. Select `Runner` project in navigator
2. Select `Runner` target
3. Go to `Build Settings` tab
4. Search for "entitlements"
5. Find `CODE_SIGN_ENTITLEMENTS`
6. Set value to: `Runner/Runner.entitlements`

#### Step 3: Verify Entitlements in Signing & Capabilities
1. Go to `Signing & Capabilities` tab
2. Click `+ Capability`
3. Add `Sign In with Apple` if not present
4. Verify it shows "Sign In with Apple ✓"

#### Step 4: Update project.pbxproj Programmatically
```bash
# Create a script to update project.pbxproj
cat > update_entitlements.rb << 'EOF'
#!/usr/bin/env ruby
require 'xcodeproj'

project_path = 'Runner.xcodeproj'
project = Xcodeproj::Project.open(project_path)

# Add entitlements to all configurations
project.targets.each do |target|
  if target.name == "Runner"
    target.build_configurations.each do |config|
      config.build_settings['CODE_SIGN_ENTITLEMENTS'] = 'Runner/Runner.entitlements'
      config.build_settings['CODE_SIGN_IDENTITY'] = 'Apple Development'
      config.build_settings['DEVELOPMENT_TEAM'] = 'YOUR_TEAM_ID' # Replace with actual
    end
  end
end

project.save
puts "✅ Entitlements configuration added to project"
EOF

# Install xcodeproj gem if needed
gem install xcodeproj

# Run the script
ruby update_entitlements.rb
```

#### Step 5: Verify Configuration
```bash
# Check if entitlements are linked
grep -n "CODE_SIGN_ENTITLEMENTS" Runner.xcodeproj/project.pbxproj

# Expected output should show:
# CODE_SIGN_ENTITLEMENTS = Runner/Runner.entitlements;
```

### 1.2 Update Info.plist for Apple Sign-In

#### Step 1: Edit Info.plist
```xml
<!-- Add to /ios/Runner/Info.plist -->
<key>CFBundleURLTypes</key>
<array>
    <!-- Existing Google Sign-In URL Scheme -->
    <dict>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>com.googleusercontent.apps.433335755307-n22s61c9257ft6d5tg3sa4scjmqlspnt</string>
        </array>
    </dict>
    <!-- Add Apple Sign-In URL Scheme -->
    <dict>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>com.tradingDummy.zjh</string>
        </array>
    </dict>
</array>
```

### 1.3 Configure Minimum iOS Version

#### Step 1: Update Podfile
```ruby
# Edit ios/Podfile
platform :ios, '13.0'  # Sign In with Apple requires iOS 13.0+
```

#### Step 2: Update Xcode Deployment Target
```bash
# Update deployment target in project
cat > update_deployment.rb << 'EOF'
#!/usr/bin/env ruby
require 'xcodeproj'

project = Xcodeproj::Project.open('Runner.xcodeproj')
project.targets.each do |target|
  if target.name == "Runner"
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '13.0'
    end
  end
end
project.save
puts "✅ iOS deployment target updated to 13.0"
EOF

ruby update_deployment.rb
```

#### Step 3: Reinstall Pods
```bash
cd ios
pod deintegrate
pod install
cd ..
```

---

## 2. Apple Developer Portal Setup

### 2.1 Enable Sign In with Apple for App ID

#### Step 1: Access Apple Developer Portal
1. Go to https://developer.apple.com/account
2. Sign in with your Apple Developer account
3. Navigate to `Certificates, Identifiers & Profiles`

#### Step 2: Configure App ID
1. Click `Identifiers` in sidebar
2. Find or create App ID for `com.tradingDummy.zjh`
3. Click on the App ID to edit
4. Under `Capabilities`, check `Sign In with Apple`
5. Click `Save`

#### Step 3: Regenerate Provisioning Profiles
```bash
# Use fastlane for automation (optional)
# Install fastlane if not present
gem install fastlane

# Create Fastfile
cat > ios/fastlane/Fastfile << 'EOF'
default_platform(:ios)

platform :ios do
  desc "Sync certificates and profiles"
  lane :sync_signing do
    app_store_connect_api_key(
      key_id: ENV["APP_STORE_CONNECT_KEY_ID"],
      issuer_id: ENV["APP_STORE_CONNECT_ISSUER_ID"],
      key_filepath: ENV["APP_STORE_CONNECT_KEY_PATH"]
    )
    
    match(
      type: "development",
      app_identifier: "com.tradingDummy.zjh",
      readonly: false
    )
    
    match(
      type: "appstore",
      app_identifier: "com.tradingDummy.zjh",
      readonly: false
    )
  end
end
EOF
```

### 2.2 Create Service ID (For Web/Android)

#### Step 1: Create Service ID
1. In Apple Developer Portal, go to `Identifiers`
2. Click `+` button
3. Select `Services IDs`
4. Enter:
   - Description: `Trading Dummy Sign In`
   - Identifier: `com.tradingDummy.zjh.signin`
5. Click `Continue` then `Register`

#### Step 2: Configure Service ID
1. Click on the newly created Service ID
2. Check `Sign In with Apple`
3. Click `Configure`
4. Primary App ID: Select `com.tradingDummy.zjh`
5. Domains and Subdomains:
   - Add your backend domain (e.g., `api.tradingdummy.com`)
   - For development: `localhost`
6. Return URLs:
   - Production: `https://api.tradingdummy.com/auth/apple/callback`
   - Development: `http://localhost:8000/auth/apple/callback`
7. Click `Save`

### 2.3 Generate Sign In with Apple Private Key

#### Step 1: Create Key
1. Go to `Keys` section
2. Click `+` to create new key
3. Enter Key Name: `Trading Dummy Sign In Key`
4. Check `Sign In with Apple`
5. Click `Configure`
6. Select `com.tradingDummy.zjh` as Primary App ID
7. Click `Save` then `Continue`
8. Click `Register`

#### Step 2: Download and Store Key
```bash
# Create secure directory for Apple keys
mkdir -p ~/Documents/TradingAgents/trading_dummy/keys
cd ~/Documents/TradingAgents/trading_dummy/keys

# After downloading the .p8 file, move it here
mv ~/Downloads/AuthKey_*.p8 ./apple_signin_key.p8

# Set appropriate permissions
chmod 600 apple_signin_key.p8

# Create .env.apple file for credentials
cat > ../.env.apple << 'EOF'
APPLE_TEAM_ID=YOUR_TEAM_ID
APPLE_KEY_ID=YOUR_KEY_ID
APPLE_SERVICE_ID=com.tradingDummy.zjh.signin
APPLE_PRIVATE_KEY_PATH=./keys/apple_signin_key.p8
EOF

# Add to .gitignore
echo "keys/" >> ../.gitignore
echo ".env.apple" >> ../.gitignore
```

---

## 3. Backend Integration

### 3.1 Create Backend Service for Token Validation

#### Step 1: Create Apple Auth Backend Service
```dart
// Create file: lib/auth/services/apple_auth_backend_service.dart

import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:jose/jose.dart';
import '../../core/logging/app_logger.dart';

class AppleAuthBackendService {
  static const String _tag = 'AppleAuthBackendService';
  static const String _appleAuthUrl = 'https://appleid.apple.com';
  
  final String teamId;
  final String serviceId;
  final String keyId;
  final String privateKey;
  
  AppleAuthBackendService({
    required this.teamId,
    required this.serviceId,
    required this.keyId,
    required this.privateKey,
  });
  
  /// Validates the identity token received from Apple Sign-In
  Future<Map<String, dynamic>> validateIdentityToken(String identityToken) async {
    try {
      AppLogger.info(_tag, 'Validating Apple identity token');
      
      // Decode the JWT without verification first to get the header
      final parts = identityToken.split('.');
      if (parts.length != 3) {
        throw Exception('Invalid JWT format');
      }
      
      // Decode header to get the kid (key ID)
      final header = json.decode(
        utf8.decode(base64Url.decode(base64Url.normalize(parts[0])))
      );
      final kid = header['kid'];
      
      // Fetch Apple's public keys
      final publicKey = await _fetchApplePublicKey(kid);
      
      // Verify and decode the token
      final jwt = await _verifyToken(identityToken, publicKey);
      
      // Validate claims
      _validateClaims(jwt);
      
      AppLogger.info(_tag, 'Token validation successful');
      return jwt;
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Token validation failed', e, stackTrace);
      rethrow;
    }
  }
  
  /// Fetches Apple's public key for token verification
  Future<String> _fetchApplePublicKey(String kid) async {
    final response = await http.get(
      Uri.parse('$_appleAuthUrl/auth/keys'),
    );
    
    if (response.statusCode != 200) {
      throw Exception('Failed to fetch Apple public keys');
    }
    
    final keys = json.decode(response.body)['keys'] as List;
    final key = keys.firstWhere(
      (k) => k['kid'] == kid,
      orElse: () => throw Exception('Public key not found for kid: $kid'),
    );
    
    return json.encode(key);
  }
  
  /// Verifies the JWT token using Apple's public key
  Future<Map<String, dynamic>> _verifyToken(
    String token,
    String publicKeyJson,
  ) async {
    try {
      final key = JsonWebKey.fromJson(json.decode(publicKeyJson));
      final jwt = await JsonWebSignature.fromCompactSerialization(token);
      
      final keyStore = JsonWebKeyStore()..addKey(key);
      final verified = await jwt.verify(keyStore);
      
      if (!verified) {
        throw Exception('Token signature verification failed');
      }
      
      final payload = json.decode(jwt.unverifiedPayload.stringContent);
      return payload;
    } catch (e) {
      throw Exception('Token verification failed: $e');
    }
  }
  
  /// Validates JWT claims
  void _validateClaims(Map<String, dynamic> claims) {
    // Check issuer
    if (claims['iss'] != _appleAuthUrl) {
      throw Exception('Invalid issuer');
    }
    
    // Check audience (should be your app's bundle ID)
    if (claims['aud'] != 'com.tradingDummy.zjh') {
      throw Exception('Invalid audience');
    }
    
    // Check expiration
    final exp = claims['exp'] as int;
    if (DateTime.now().millisecondsSinceEpoch ~/ 1000 > exp) {
      throw Exception('Token expired');
    }
  }
  
  /// Generates client secret for token refresh
  Future<String> generateClientSecret() async {
    final now = DateTime.now();
    final expiry = now.add(const Duration(days: 180)); // Max 6 months
    
    final claims = {
      'iss': teamId,
      'iat': now.millisecondsSinceEpoch ~/ 1000,
      'exp': expiry.millisecondsSinceEpoch ~/ 1000,
      'aud': _appleAuthUrl,
      'sub': serviceId,
    };
    
    final builder = JsonWebSignatureBuilder()
      ..jsonContent = json.encode(claims)
      ..addRecipient(
        JsonWebKey.fromJson({
          'kty': 'EC',
          'kid': keyId,
          'use': 'sig',
          'alg': 'ES256',
        }),
        algorithm: 'ES256',
      );
    
    final jws = builder.build();
    return jws.toCompactSerialization();
  }
  
  /// Refreshes the access token using the refresh token
  Future<Map<String, dynamic>> refreshToken(String refreshToken) async {
    try {
      final clientSecret = await generateClientSecret();
      
      final response = await http.post(
        Uri.parse('$_appleAuthUrl/auth/token'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {
          'client_id': serviceId,
          'client_secret': clientSecret,
          'refresh_token': refreshToken,
          'grant_type': 'refresh_token',
        },
      );
      
      if (response.statusCode != 200) {
        throw Exception('Token refresh failed: ${response.body}');
      }
      
      return json.decode(response.body);
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Token refresh failed', e, stackTrace);
      rethrow;
    }
  }
}
```

### 3.2 Create User Account Management

#### Step 1: Create User Repository
```dart
// Create file: lib/auth/repositories/user_repository.dart

import 'package:sqflite/sqflite.dart';
import '../models/user_model.dart';
import '../models/auth_provider.dart';
import '../../core/logging/app_logger.dart';

class UserRepository {
  static const String _tag = 'UserRepository';
  static const String _tableName = 'users';
  
  final Database _database;
  
  UserRepository(this._database);
  
  /// Initialize the users table
  static Future<void> createTable(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS $_tableName (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        display_name TEXT,
        photo_url TEXT,
        provider TEXT NOT NULL,
        apple_user_id TEXT,
        google_user_id TEXT,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        last_login_at INTEGER NOT NULL
      )
    ''');
    
    // Create indexes
    await db.execute(
      'CREATE INDEX IF NOT EXISTS idx_users_email ON $_tableName (email)'
    );
    await db.execute(
      'CREATE INDEX IF NOT EXISTS idx_users_apple_id ON $_tableName (apple_user_id)'
    );
  }
  
  /// Find or create user from Apple credentials
  Future<UserModel> findOrCreateAppleUser({
    required String appleUserId,
    required String? email,
    required String? displayName,
    required String? idToken,
    required String? authorizationCode,
  }) async {
    try {
      // Check if user exists with this Apple ID
      final existing = await _findByAppleId(appleUserId);
      if (existing != null) {
        // Update last login
        await _updateLastLogin(existing.id);
        return existing;
      }
      
      // Check if user exists with same email (account linking)
      if (email != null) {
        final emailMatch = await _findByEmail(email);
        if (emailMatch != null) {
          // Link Apple ID to existing account
          await _linkAppleId(emailMatch.id, appleUserId);
          await _updateLastLogin(emailMatch.id);
          return emailMatch.copyWith(
            provider: AuthProvider.apple,
            idToken: idToken,
            accessToken: authorizationCode,
          );
        }
      }
      
      // Create new user
      final newUser = UserModel(
        id: _generateUserId(),
        email: email ?? 'apple.$appleUserId@privaterelay.appleid.com',
        displayName: displayName,
        provider: AuthProvider.apple,
        idToken: idToken,
        accessToken: authorizationCode,
        tokenExpiryTime: DateTime.now().add(const Duration(days: 30)),
      );
      
      await _insertUser(newUser, appleUserId: appleUserId);
      return newUser;
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to find or create Apple user', e, stackTrace);
      rethrow;
    }
  }
  
  Future<UserModel?> _findByAppleId(String appleId) async {
    final results = await _database.query(
      _tableName,
      where: 'apple_user_id = ?',
      whereArgs: [appleId],
    );
    
    if (results.isEmpty) return null;
    return UserModel.fromDatabaseJson(results.first);
  }
  
  Future<UserModel?> _findByEmail(String email) async {
    final results = await _database.query(
      _tableName,
      where: 'email = ?',
      whereArgs: [email],
    );
    
    if (results.isEmpty) return null;
    return UserModel.fromDatabaseJson(results.first);
  }
  
  Future<void> _linkAppleId(String userId, String appleId) async {
    await _database.update(
      _tableName,
      {'apple_user_id': appleId, 'updated_at': DateTime.now().millisecondsSinceEpoch},
      where: 'id = ?',
      whereArgs: [userId],
    );
  }
  
  Future<void> _updateLastLogin(String userId) async {
    await _database.update(
      _tableName,
      {'last_login_at': DateTime.now().millisecondsSinceEpoch},
      where: 'id = ?',
      whereArgs: [userId],
    );
  }
  
  Future<void> _insertUser(UserModel user, {String? appleUserId}) async {
    final now = DateTime.now().millisecondsSinceEpoch;
    await _database.insert(
      _tableName,
      {
        'id': user.id,
        'email': user.email,
        'display_name': user.displayName,
        'photo_url': user.photoUrl,
        'provider': user.provider.name,
        'apple_user_id': appleUserId,
        'created_at': now,
        'updated_at': now,
        'last_login_at': now,
      },
    );
  }
  
  String _generateUserId() {
    return 'usr_${DateTime.now().millisecondsSinceEpoch}_${_randomString(8)}';
  }
  
  String _randomString(int length) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    final random = Random.secure();
    return List.generate(length, (_) => chars[random.nextInt(chars.length)]).join();
  }
}
```

---

## 4. Testing Implementation

### 4.1 Create Mock Apple Auth Service

```dart
// Create file: test/auth/mocks/mock_apple_auth_service.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/auth/auth_module.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

class MockAppleAuthService implements AppleAuthService {
  bool shouldSucceed;
  bool shouldCancel;
  bool isAvailable;
  UserModel? mockUser;
  CredentialState credentialState;
  String? errorCode;
  
  MockAppleAuthService({
    this.shouldSucceed = true,
    this.shouldCancel = false,
    this.isAvailable = true,
    this.mockUser,
    this.credentialState = CredentialState.authorized,
    this.errorCode,
  });
  
  @override
  Future<UserModel?> signIn() async {
    await Future.delayed(const Duration(milliseconds: 100));
    
    if (!isAvailable) {
      throw Exception('Apple Sign-In is not available on this device');
    }
    
    if (shouldCancel) {
      return null;
    }
    
    if (!shouldSucceed) {
      if (errorCode != null) {
        throw SignInWithAppleAuthorizationException(
          code: AuthorizationErrorCode.values.firstWhere(
            (e) => e.toString() == errorCode,
            orElse: () => AuthorizationErrorCode.unknown,
          ),
          message: 'Mock error',
        );
      }
      throw Exception('Mock Apple sign-in failed');
    }
    
    return mockUser ?? UserModel(
      id: 'apple_test_123',
      email: 'test@privaterelay.appleid.com',
      displayName: 'Test User',
      provider: AuthProvider.apple,
      idToken: 'mock-apple-id-token',
      accessToken: 'mock-apple-auth-code',
      tokenExpiryTime: DateTime.now().add(const Duration(days: 30)),
    );
  }
  
  @override
  Future<void> signOut() async {
    await Future.delayed(const Duration(milliseconds: 50));
    if (!shouldSucceed) {
      throw Exception('Mock sign-out failed');
    }
  }
  
  @override
  Future<UserModel?> silentSignIn() async {
    await Future.delayed(const Duration(milliseconds: 100));
    
    if (!shouldSucceed) {
      return null;
    }
    
    // Simulate checking stored credentials
    return mockUser;
  }
  
  @override
  Future<bool> isSignedIn() async {
    await Future.delayed(const Duration(milliseconds: 50));
    return shouldSucceed && mockUser != null;
  }
  
  @override
  Future<CredentialState> getCredentialState(String userId) async {
    await Future.delayed(const Duration(milliseconds: 50));
    return credentialState;
  }
}
```

### 4.2 Create Comprehensive Test Suite

```dart
// Create file: test/auth/apple_auth_service_test.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'mocks/mock_apple_auth_service.dart';
import 'package:trading_dummy/auth/auth_module.dart';

void main() {
  group('AppleAuthService Tests', () {
    late MockAppleAuthService mockService;
    
    setUp(() {
      mockService = MockAppleAuthService();
    });
    
    group('Sign In', () {
      test('should return user when sign-in succeeds', () async {
        // Arrange
        mockService.shouldSucceed = true;
        
        // Act
        final user = await mockService.signIn();
        
        // Assert
        expect(user, isNotNull);
        expect(user!.provider, equals(AuthProvider.apple));
        expect(user.id, equals('apple_test_123'));
      });
      
      test('should return null when user cancels', () async {
        // Arrange
        mockService.shouldCancel = true;
        
        // Act
        final user = await mockService.signIn();
        
        // Assert
        expect(user, isNull);
      });
      
      test('should throw when device does not support Apple Sign-In', () async {
        // Arrange
        mockService.isAvailable = false;
        
        // Act & Assert
        expect(
          () => mockService.signIn(),
          throwsA(isA<Exception>().having(
            (e) => e.toString(),
            'message',
            contains('not available'),
          )),
        );
      });
      
      test('should handle authorization errors correctly', () async {
        // Arrange
        mockService.shouldSucceed = false;
        mockService.errorCode = AuthorizationErrorCode.canceled.toString();
        
        // Act & Assert
        expect(
          () => mockService.signIn(),
          throwsA(isA<SignInWithAppleAuthorizationException>()),
        );
      });
    });
    
    group('Sign Out', () {
      test('should complete successfully', () async {
        // Arrange
        mockService.shouldSucceed = true;
        
        // Act & Assert
        await expectLater(mockService.signOut(), completes);
      });
      
      test('should handle sign-out errors', () async {
        // Arrange
        mockService.shouldSucceed = false;
        
        // Act & Assert
        expect(
          () => mockService.signOut(),
          throwsA(isA<Exception>()),
        );
      });
    });
    
    group('Silent Sign In', () {
      test('should return cached user when available', () async {
        // Arrange
        final testUser = UserModel(
          id: 'cached_user',
          email: 'cached@example.com',
          displayName: 'Cached User',
          provider: AuthProvider.apple,
          idToken: 'cached-token',
          accessToken: 'cached-access',
          tokenExpiryTime: DateTime.now().add(const Duration(days: 1)),
        );
        mockService.mockUser = testUser;
        mockService.shouldSucceed = true;
        
        // Act
        final user = await mockService.silentSignIn();
        
        // Assert
        expect(user, isNotNull);
        expect(user!.id, equals('cached_user'));
      });
      
      test('should return null when no cached credentials', () async {
        // Arrange
        mockService.shouldSucceed = false;
        
        // Act
        final user = await mockService.silentSignIn();
        
        // Assert
        expect(user, isNull);
      });
    });
    
    group('Credential State', () {
      test('should return authorized state for valid user', () async {
        // Arrange
        mockService.credentialState = CredentialState.authorized;
        
        // Act
        final state = await mockService.getCredentialState('test_user');
        
        // Assert
        expect(state, equals(CredentialState.authorized));
      });
      
      test('should return revoked state for revoked credentials', () async {
        // Arrange
        mockService.credentialState = CredentialState.revoked;
        
        // Act
        final state = await mockService.getCredentialState('test_user');
        
        // Assert
        expect(state, equals(CredentialState.revoked));
      });
    });
    
    group('Is Signed In', () {
      test('should return true when user is signed in', () async {
        // Arrange
        mockService.shouldSucceed = true;
        mockService.mockUser = UserModel(
          id: 'signed_in_user',
          email: 'user@example.com',
          provider: AuthProvider.apple,
        );
        
        // Act
        final isSignedIn = await mockService.isSignedIn();
        
        // Assert
        expect(isSignedIn, isTrue);
      });
      
      test('should return false when user is not signed in', () async {
        // Arrange
        mockService.mockUser = null;
        
        // Act
        final isSignedIn = await mockService.isSignedIn();
        
        // Assert
        expect(isSignedIn, isFalse);
      });
    });
  });
}
```

### 4.3 Integration Tests

```dart
// Create file: test/auth/apple_auth_integration_test.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:trading_dummy/auth/auth_module.dart';
import 'mocks/mock_apple_auth_service.dart';
import 'mocks/mock_auth_storage_service.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  
  group('Apple Sign-In Integration Tests', () {
    late AuthViewModel authViewModel;
    late MockAppleAuthService mockAppleService;
    late MockAuthStorageService mockStorage;
    
    setUp(() {
      mockAppleService = MockAppleAuthService();
      mockStorage = MockAuthStorageService();
      authViewModel = AuthViewModel(
        appleAuthService: mockAppleService,
        storageService: mockStorage,
      );
    });
    
    testWidgets('Complete Apple sign-in flow', (tester) async {
      // Build the app
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider.value(
            value: authViewModel,
            child: const LoginScreen(),
          ),
        ),
      );
      
      // Find Apple sign-in button
      final appleButton = find.text('Continue with Apple');
      expect(appleButton, findsOneWidget);
      
      // Tap the button
      await tester.tap(appleButton);
      await tester.pump();
      
      // Verify loading state
      expect(authViewModel.isLoading, isTrue);
      
      // Wait for sign-in to complete
      await tester.pumpAndSettle();
      
      // Verify authenticated state
      expect(authViewModel.isAuthenticated, isTrue);
      expect(authViewModel.currentUser, isNotNull);
      expect(authViewModel.currentUser!.provider, equals(AuthProvider.apple));
      
      // Verify user was saved to storage
      expect(mockStorage.savedUser, isNotNull);
      expect(mockStorage.savedUser!.provider, equals(AuthProvider.apple));
    });
    
    testWidgets('Handle Apple sign-in cancellation', (tester) async {
      // Configure mock to simulate cancellation
      mockAppleService.shouldCancel = true;
      
      // Build the app
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider.value(
            value: authViewModel,
            child: const LoginScreen(),
          ),
        ),
      );
      
      // Tap Apple sign-in button
      await tester.tap(find.text('Continue with Apple'));
      await tester.pumpAndSettle();
      
      // Verify unauthenticated state
      expect(authViewModel.isAuthenticated, isFalse);
      expect(authViewModel.authState, equals(AuthState.unauthenticated));
    });
    
    testWidgets('Display error on Apple sign-in failure', (tester) async {
      // Configure mock to fail
      mockAppleService.shouldSucceed = false;
      
      // Build the app
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider.value(
            value: authViewModel,
            child: const LoginScreen(),
          ),
        ),
      );
      
      // Tap Apple sign-in button
      await tester.tap(find.text('Continue with Apple'));
      await tester.pumpAndSettle();
      
      // Verify error state
      expect(authViewModel.authState, equals(AuthState.error));
      expect(authViewModel.errorMessage, isNotNull);
      
      // Verify error message is displayed
      expect(find.text(authViewModel.errorMessage!), findsOneWidget);
    });
  });
}
```

---

## 5. Session Management

### 5.1 Implement Credential Storage

```dart
// Update file: lib/auth/services/auth_storage_service.dart

import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/user_model.dart';
import '../models/auth_provider.dart';
import '../../core/logging/app_logger.dart';

class AuthStorageService {
  static const String _tag = 'AuthStorageService';
  static const String _userKey = 'current_user';
  static const String _tokenKey = 'auth_tokens';
  static const String _appleCredentialsKey = 'apple_credentials';
  static const String _refreshTokenKey = 'refresh_token';
  
  final FlutterSecureStorage _secureStorage;
  
  AuthStorageService({FlutterSecureStorage? secureStorage})
      : _secureStorage = secureStorage ?? const FlutterSecureStorage();
  
  /// Save Apple-specific credentials
  Future<void> saveAppleCredentials({
    required String userId,
    required String? identityToken,
    required String? authorizationCode,
    required DateTime? tokenExpiry,
  }) async {
    try {
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
      
      AppLogger.info(_tag, 'Apple credentials saved for user: $userId');
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to save Apple credentials', e, stackTrace);
      rethrow;
    }
  }
  
  /// Retrieve Apple credentials
  Future<Map<String, dynamic>?> getAppleCredentials() async {
    try {
      final credentialsJson = await _secureStorage.read(key: _appleCredentialsKey);
      if (credentialsJson == null) return null;
      
      final credentials = json.decode(credentialsJson);
      
      // Check if credentials are expired
      if (credentials['tokenExpiry'] != null) {
        final expiry = DateTime.parse(credentials['tokenExpiry']);
        if (expiry.isBefore(DateTime.now())) {
          AppLogger.info(_tag, 'Apple credentials expired');
          await clearAppleCredentials();
          return null;
        }
      }
      
      return credentials;
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to retrieve Apple credentials', e, stackTrace);
      return null;
    }
  }
  
  /// Clear Apple credentials
  Future<void> clearAppleCredentials() async {
    try {
      await _secureStorage.delete(key: _appleCredentialsKey);
      AppLogger.info(_tag, 'Apple credentials cleared');
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to clear Apple credentials', e, stackTrace);
    }
  }
  
  /// Save refresh token
  Future<void> saveRefreshToken(String refreshToken) async {
    try {
      await _secureStorage.write(
        key: _refreshTokenKey,
        value: refreshToken,
      );
      AppLogger.info(_tag, 'Refresh token saved');
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to save refresh token', e, stackTrace);
    }
  }
  
  /// Get refresh token
  Future<String?> getRefreshToken() async {
    try {
      return await _secureStorage.read(key: _refreshTokenKey);
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to retrieve refresh token', e, stackTrace);
      return null;
    }
  }
  
  /// Check if user has valid Apple credentials
  Future<bool> hasValidAppleCredentials() async {
    final credentials = await getAppleCredentials();
    return credentials != null && credentials['userId'] != null;
  }
  
  // ... existing methods ...
}
```

### 5.2 Implement Silent Sign-In

```dart
// Update file: lib/auth/services/apple_auth_service.dart

import 'dart:math';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import '../../core/logging/app_logger.dart';
import '../models/auth_provider.dart';
import '../models/user_model.dart';
import 'auth_storage_service.dart';
import 'i_auth_service.dart';

class AppleAuthService implements IAuthService {
  static const String _tag = 'AppleAuthService';
  final AuthStorageService _storageService;
  
  AppleAuthService({AuthStorageService? storageService})
      : _storageService = storageService ?? AuthStorageService();
  
  @override
  Future<UserModel?> signIn() async {
    try {
      AppLogger.userAction(_tag, 'Starting Apple Sign-In');
      
      // Check if Apple Sign-In is available on this device
      final isAvailable = await SignInWithApple.isAvailable();
      if (!isAvailable) {
        throw Exception('Apple Sign-In is not available on this device');
      }
      
      // Generate nonce for security
      final rawNonce = _generateNonce();
      
      // Request Apple Sign-In
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
        nonce: rawNonce,
      );
      
      AppLogger.info(_tag, 'Apple Sign-In successful');
      
      // Extract user information
      final String userId = credential.userIdentifier ?? '';
      final String? email = credential.email;
      final String? firstName = credential.givenName;
      final String? lastName = credential.familyName;
      
      // Construct display name
      String? displayName;
      if (firstName != null || lastName != null) {
        displayName = '${firstName ?? ''} ${lastName ?? ''}'.trim();
      }
      
      // Calculate token expiry
      final tokenExpiry = _calculateTokenExpiry();
      
      // Create UserModel from Apple credential
      final user = UserModel(
        id: userId,
        email: email ?? 'apple.user@privaterelay.appleid.com',
        displayName: displayName,
        photoUrl: null,
        provider: AuthProvider.apple,
        idToken: credential.identityToken,
        accessToken: credential.authorizationCode,
        tokenExpiryTime: tokenExpiry,
      );
      
      // Save credentials for silent sign-in
      await _storageService.saveAppleCredentials(
        userId: userId,
        identityToken: credential.identityToken,
        authorizationCode: credential.authorizationCode,
        tokenExpiry: tokenExpiry,
      );
      
      AppLogger.info(_tag, 'Created UserModel for Apple user ${user.id}');
      return user;
    } on SignInWithAppleAuthorizationException catch (e) {
      if (e.code == AuthorizationErrorCode.canceled) {
        AppLogger.info(_tag, 'User cancelled Apple Sign-In');
        return null;
      }
      AppLogger.error(_tag, 'Apple Sign-In authorization error: ${e.code}', e);
      rethrow;
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Apple Sign-In failed', e, stackTrace);
      rethrow;
    }
  }
  
  @override
  Future<UserModel?> silentSignIn() async {
    try {
      AppLogger.info(_tag, 'Attempting silent Apple Sign-In');
      
      // Check for stored Apple credentials
      final credentials = await _storageService.getAppleCredentials();
      if (credentials == null) {
        AppLogger.info(_tag, 'No stored Apple credentials found');
        return null;
      }
      
      final userId = credentials['userId'] as String;
      
      // Verify credential state with Apple
      final credentialState = await getCredentialState(userId);
      
      if (credentialState != CredentialState.authorized) {
        AppLogger.info(_tag, 'Apple credentials not authorized: $credentialState');
        await _storageService.clearAppleCredentials();
        return null;
      }
      
      // Retrieve stored user data
      final storedUser = await _storageService.getUser();
      if (storedUser == null || storedUser.id != userId) {
        AppLogger.info(_tag, 'Stored user data mismatch');
        return null;
      }
      
      // Check if token needs refresh
      if (storedUser.tokenExpiryTime?.isBefore(DateTime.now()) ?? true) {
        AppLogger.info(_tag, 'Token expired, needs refresh');
        // In a real implementation, you would refresh the token here
        // For now, we'll require a new sign-in
        return null;
      }
      
      AppLogger.info(_tag, 'Silent Apple Sign-In successful');
      return storedUser;
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Silent Apple Sign-In failed', e, stackTrace);
      return null;
    }
  }
  
  @override
  Future<bool> isSignedIn() async {
    try {
      // Check for stored Apple credentials
      final hasCredentials = await _storageService.hasValidAppleCredentials();
      if (!hasCredentials) {
        return false;
      }
      
      // Verify with silent sign-in
      final user = await silentSignIn();
      return user != null;
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to check Apple Sign-In status', e, stackTrace);
      return false;
    }
  }
  
  // ... rest of the existing methods ...
}
```

---

## 6. Security Enhancements

### 6.1 Implement Nonce Validation

```dart
// Create file: lib/auth/services/apple_auth_security.dart

import 'dart:convert';
import 'dart:math';
import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/logging/app_logger.dart';

class AppleAuthSecurity {
  static const String _tag = 'AppleAuthSecurity';
  static const String _nonceKey = 'apple_auth_nonce';
  
  final FlutterSecureStorage _secureStorage;
  
  AppleAuthSecurity({FlutterSecureStorage? secureStorage})
      : _secureStorage = secureStorage ?? const FlutterSecureStorage();
  
  /// Generates a cryptographically secure nonce
  String generateNonce([int length = 32]) {
    const charset = '0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._';
    final random = Random.secure();
    final nonce = List.generate(
      length,
      (_) => charset[random.nextInt(charset.length)],
    ).join();
    
    AppLogger.debug(_tag, 'Generated nonce of length $length');
    return nonce;
  }
  
  /// Generates SHA256 hash of the nonce
  String hashNonce(String nonce) {
    final bytes = utf8.encode(nonce);
    final digest = sha256.convert(bytes);
    final hash = digest.toString();
    
    AppLogger.debug(_tag, 'Generated SHA256 hash for nonce');
    return hash;
  }
  
  /// Stores nonce securely for later validation
  Future<void> storeNonce(String nonce) async {
    try {
      final timestamp = DateTime.now().toIso8601String();
      final nonceData = {
        'nonce': nonce,
        'hash': hashNonce(nonce),
        'timestamp': timestamp,
      };
      
      await _secureStorage.write(
        key: _nonceKey,
        value: json.encode(nonceData),
      );
      
      AppLogger.info(_tag, 'Nonce stored securely');
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to store nonce', e, stackTrace);
      rethrow;
    }
  }
  
  /// Validates the nonce from Apple's response
  Future<bool> validateNonce(String responseNonce) async {
    try {
      final storedData = await _secureStorage.read(key: _nonceKey);
      if (storedData == null) {
        AppLogger.warning(_tag, 'No stored nonce found for validation');
        return false;
      }
      
      final nonceData = json.decode(storedData);
      final storedNonce = nonceData['nonce'] as String;
      final timestamp = DateTime.parse(nonceData['timestamp']);
      
      // Check if nonce is not too old (5 minutes max)
      if (DateTime.now().difference(timestamp).inMinutes > 5) {
        AppLogger.warning(_tag, 'Stored nonce is too old');
        await clearNonce();
        return false;
      }
      
      // Validate nonce match
      final isValid = storedNonce == responseNonce ||
                      hashNonce(storedNonce) == responseNonce;
      
      if (isValid) {
        AppLogger.info(_tag, 'Nonce validation successful');
        await clearNonce(); // Clear after successful validation
      } else {
        AppLogger.warning(_tag, 'Nonce validation failed');
      }
      
      return isValid;
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to validate nonce', e, stackTrace);
      return false;
    }
  }
  
  /// Clears stored nonce
  Future<void> clearNonce() async {
    try {
      await _secureStorage.delete(key: _nonceKey);
      AppLogger.debug(_tag, 'Nonce cleared');
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Failed to clear nonce', e, stackTrace);
    }
  }
  
  /// Validates Apple ID token structure
  bool validateTokenStructure(String? idToken) {
    if (idToken == null || idToken.isEmpty) {
      return false;
    }
    
    // JWT should have three parts separated by dots
    final parts = idToken.split('.');
    if (parts.length != 3) {
      AppLogger.warning(_tag, 'Invalid JWT structure');
      return false;
    }
    
    try {
      // Validate that each part is valid base64
      for (final part in parts) {
        base64Url.decode(base64Url.normalize(part));
      }
      
      return true;
    } catch (e) {
      AppLogger.warning(_tag, 'Invalid JWT encoding');
      return false;
    }
  }
  
  /// Sanitizes user input to prevent injection attacks
  String sanitizeInput(String input) {
    // Remove any potentially harmful characters
    return input
        .replaceAll(RegExp(r'[<>\"\'`]'), '')
        .trim();
  }
}
```

### 6.2 Keychain Integration

```dart
// Update iOS-specific keychain access
// File: ios/Runner/AppleKeychainBridge.swift

import Foundation
import Security

@objc class AppleKeychainBridge: NSObject {
    private let service = "com.tradingDummy.zjh.keychain"
    
    @objc func saveToKeychain(key: String, value: String) -> Bool {
        guard let data = value.data(using: .utf8) else { return false }
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        // Delete any existing item
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }
    
    @objc func getFromKeychain(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var dataTypeRef: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &dataTypeRef)
        
        if status == errSecSuccess,
           let data = dataTypeRef as? Data,
           let value = String(data: data, encoding: .utf8) {
            return value
        }
        
        return nil
    }
    
    @objc func deleteFromKeychain(key: String) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key
        ]
        
        let status = SecItemDelete(query as CFDictionary)
        return status == errSecSuccess
    }
}
```

---

## 7. Android Support

### 7.1 Configure Web-Based Apple Sign-In

```dart
// Create file: lib/auth/services/apple_auth_web_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
import 'package:uni_links/uni_links.dart';
import '../../core/logging/app_logger.dart';
import '../models/user_model.dart';
import '../models/auth_provider.dart';

class AppleAuthWebService {
  static const String _tag = 'AppleAuthWebService';
  static const String _authEndpoint = 'https://appleid.apple.com/auth/authorize';
  static const String _tokenEndpoint = 'https://appleid.apple.com/auth/token';
  
  final String serviceId;
  final String redirectUri;
  final String clientSecret;
  
  AppleAuthWebService({
    required this.serviceId,
    required this.redirectUri,
    required this.clientSecret,
  });
  
  /// Initiates web-based Apple Sign-In for Android
  Future<UserModel?> signInWithWeb() async {
    try {
      AppLogger.info(_tag, 'Starting web-based Apple Sign-In');
      
      // Generate state for CSRF protection
      final state = _generateState();
      
      // Build authorization URL
      final authUrl = Uri.parse(_authEndpoint).replace(
        queryParameters: {
          'response_type': 'code id_token',
          'client_id': serviceId,
          'redirect_uri': redirectUri,
          'state': state,
          'scope': 'name email',
          'response_mode': 'form_post',
        },
      );
      
      // Launch browser
      if (!await launchUrl(authUrl, mode: LaunchMode.externalApplication)) {
        throw Exception('Could not launch Apple Sign-In');
      }
      
      // Listen for deep link callback
      final response = await _waitForCallback(state);
      if (response == null) {
        return null;
      }
      
      // Exchange code for tokens
      final tokens = await _exchangeCodeForTokens(response['code']);
      
      // Parse ID token
      final idToken = tokens['id_token'] as String;
      final userData = _parseIdToken(idToken);
      
      // Create user model
      return UserModel(
        id: userData['sub'],
        email: userData['email'] ?? 'apple.user@privaterelay.appleid.com',
        displayName: userData['name'],
        provider: AuthProvider.apple,
        idToken: idToken,
        accessToken: tokens['access_token'],
        tokenExpiryTime: DateTime.now().add(
          Duration(seconds: tokens['expires_in'] ?? 3600),
        ),
      );
    } catch (e, stackTrace) {
      AppLogger.error(_tag, 'Web-based Apple Sign-In failed', e, stackTrace);
      rethrow;
    }
  }
  
  /// Waits for the deep link callback
  Future<Map<String, String>?> _waitForCallback(String expectedState) async {
    try {
      // Set up a timeout
      final timeout = Future.delayed(
        const Duration(minutes: 5),
        () => throw TimeoutException('Apple Sign-In timeout'),
      );
      
      // Listen for incoming links
      final link = await Future.any([
        getLinksStream().first,
        timeout,
      ]);
      
      if (link == null) return null;
      
      // Parse the callback URL
      final uri = Uri.parse(link as String);
      final params = uri.queryParameters;
      
      // Validate state
      if (params['state'] != expectedState) {
        throw Exception('Invalid state in Apple Sign-In callback');
      }
      
      return params;
    } catch (e) {
      AppLogger.error(_tag, 'Failed to handle callback', e);
      return null;
    }
  }
  
  /// Exchanges authorization code for tokens
  Future<Map<String, dynamic>> _exchangeCodeForTokens(String code) async {
    final response = await http.post(
      Uri.parse(_tokenEndpoint),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {
        'client_id': serviceId,
        'client_secret': clientSecret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirectUri,
      },
    );
    
    if (response.statusCode != 200) {
      throw Exception('Failed to exchange code for tokens: ${response.body}');
    }
    
    return json.decode(response.body);
  }
  
  /// Parses the ID token to extract user information
  Map<String, dynamic> _parseIdToken(String idToken) {
    final parts = idToken.split('.');
    if (parts.length != 3) {
      throw Exception('Invalid ID token format');
    }
    
    final payload = parts[1];
    final normalized = base64Url.normalize(payload);
    final decoded = utf8.decode(base64Url.decode(normalized));
    
    return json.decode(decoded);
  }
  
  String _generateState() {
    final random = Random.secure();
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    return List.generate(32, (_) => chars[random.nextInt(chars.length)]).join();
  }
}
```

### 7.2 Configure Android Manifest

```xml
<!-- Add to android/app/src/main/AndroidManifest.xml -->
<activity
    android:name=".AppleSignInCallbackActivity"
    android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data
            android:scheme="https"
            android:host="api.tradingdummy.com"
            android:path="/auth/apple/callback" />
    </intent-filter>
</activity>
```

---

## 8. Error Handling & UX

### 8.1 Enhanced Error Messages

```dart
// Create file: lib/auth/utils/apple_auth_error_handler.dart

import 'package:sign_in_with_apple/sign_in_with_apple.dart';

class AppleAuthErrorHandler {
  /// Maps Apple Sign-In errors to user-friendly messages
  static String getErrorMessage(dynamic error) {
    if (error is SignInWithAppleAuthorizationException) {
      switch (error.code) {
        case AuthorizationErrorCode.canceled:
          return 'Sign-in was cancelled. Please try again when you\'re ready.';
        case AuthorizationErrorCode.failed:
          return 'Sign-in failed. Please check your internet connection and try again.';
        case AuthorizationErrorCode.invalidResponse:
          return 'Invalid response from Apple. Please try again later.';
        case AuthorizationErrorCode.notHandled:
          return 'Sign-in request was not handled. Please try again.';
        case AuthorizationErrorCode.unknown:
          return 'An unknown error occurred. Please try again or contact support.';
        default:
          return 'Sign-in failed. Please try again later.';
      }
    }
    
    if (error.toString().contains('not available')) {
      return 'Apple Sign-In is not available on this device. Please use an iOS device or update your system.';
    }
    
    if (error.toString().contains('network')) {
      return 'Network error. Please check your internet connection and try again.';
    }
    
    if (error.toString().contains('timeout')) {
      return 'Sign-in timed out. Please try again.';
    }
    
    return 'An unexpected error occurred. Please try again or contact support.';
  }
  
  /// Determines if the error is recoverable
  static bool isRecoverable(dynamic error) {
    if (error is SignInWithAppleAuthorizationException) {
      return error.code != AuthorizationErrorCode.unknown;
    }
    
    return !error.toString().contains('not available');
  }
  
  /// Gets suggested action for the error
  static String getSuggestedAction(dynamic error) {
    if (error is SignInWithAppleAuthorizationException) {
      switch (error.code) {
        case AuthorizationErrorCode.canceled:
          return 'Tap the Apple Sign-In button when ready';
        case AuthorizationErrorCode.failed:
          return 'Check your internet connection and try again';
        case AuthorizationErrorCode.invalidResponse:
          return 'Wait a moment and try again';
        default:
          return 'Try signing in again';
      }
    }
    
    return 'Please try again or use an alternative sign-in method';
  }
}
```

### 8.2 Improved Loading States

```dart
// Create file: lib/auth/widgets/apple_signin_button.dart

import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';

class AppleSignInButton extends StatefulWidget {
  final VoidCallback? onPressed;
  final bool isLoading;
  
  const AppleSignInButton({
    Key? key,
    this.onPressed,
    this.isLoading = false,
  }) : super(key: key);
  
  @override
  State<AppleSignInButton> createState() => _AppleSignInButtonState();
}

class _AppleSignInButtonState extends State<AppleSignInButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  
  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.95,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
  }
  
  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }
  
  void _handleTapDown(TapDownDetails details) {
    _animationController.forward();
  }
  
  void _handleTapUp(TapUpDetails details) {
    _animationController.reverse();
  }
  
  void _handleTapCancel() {
    _animationController.reverse();
  }
  
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: widget.isLoading ? null : _handleTapDown,
      onTapUp: widget.isLoading ? null : _handleTapUp,
      onTapCancel: widget.isLoading ? null : _handleTapCancel,
      onTap: widget.isLoading ? null : widget.onPressed,
      child: AnimatedBuilder(
        animation: _scaleAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: Container(
              height: 56,
              decoration: BoxDecoration(
                color: widget.isLoading ? Colors.grey.shade800 : Colors.black,
                borderRadius: BorderRadius.circular(8),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.15),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  borderRadius: BorderRadius.circular(8),
                  onTap: widget.isLoading ? null : widget.onPressed,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (widget.isLoading)
                          const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          )
                        else
                          const Icon(
                            Icons.apple,
                            color: Colors.white,
                            size: 24,
                          ),
                        const SizedBox(width: 12),
                        Text(
                          widget.isLoading ? 'Signing in...' : 'Continue with Apple',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
```

---

## 9. Documentation

### 9.1 Integration Guide

```markdown
# Apple Sign-In Integration Guide

## Prerequisites
- Apple Developer Account ($99/year)
- iOS 13.0+ for native Apple Sign-In
- Xcode 12.0+
- Valid App ID with Sign In with Apple capability

## Setup Steps

### 1. Apple Developer Portal Configuration
1. Log in to [Apple Developer Portal](https://developer.apple.com)
2. Navigate to Certificates, Identifiers & Profiles
3. Create/Update App ID:
   - Bundle ID: `com.tradingDummy.zjh`
   - Enable "Sign In with Apple" capability
4. Create Service ID (for web/Android):
   - Identifier: `com.tradingDummy.zjh.signin`
   - Configure domains and return URLs
5. Create Sign In with Apple Key:
   - Download the .p8 file
   - Note the Key ID and Team ID

### 2. Xcode Configuration
1. Open `ios/Runner.xcworkspace` in Xcode
2. Select Runner target → Signing & Capabilities
3. Add "Sign In with Apple" capability
4. Ensure entitlements file is linked
5. Set minimum deployment target to iOS 13.0

### 3. Flutter Configuration
1. Add dependencies:
```yaml
dependencies:
  sign_in_with_apple: ^5.0.0
  crypto: ^3.0.3
  flutter_secure_storage: ^9.0.0
```

2. Run `flutter pub get`

### 4. Environment Variables
Create `.env.apple` file:
```env
APPLE_TEAM_ID=YOUR_TEAM_ID
APPLE_KEY_ID=YOUR_KEY_ID
APPLE_SERVICE_ID=com.tradingDummy.zjh.signin
APPLE_PRIVATE_KEY_PATH=./keys/apple_signin_key.p8
```

### 5. Testing
1. Test on real iOS device (simulator won't work)
2. Ensure device is signed in to iCloud
3. Test all scenarios:
   - Successful sign-in
   - Cancel flow
   - Error handling
   - Token refresh

## Troubleshooting

### Common Issues

#### "Sign In with Apple isn't available"
- Ensure iOS 13.0+ is targeted
- Verify capability is enabled in Xcode
- Check device has iCloud account

#### "Invalid client"
- Verify Service ID matches configuration
- Check domains and return URLs
- Ensure private key is valid

#### "User cancelled"
- This is normal when user taps Cancel
- Handle gracefully in UI

## Security Best Practices
1. Always validate tokens server-side
2. Use nonce for replay attack protection
3. Store credentials in Keychain/secure storage
4. Implement token refresh before expiry
5. Handle credential revocation

## Support
- [Apple Documentation](https://developer.apple.com/sign-in-with-apple/)
- [Flutter Package](https://pub.dev/packages/sign_in_with_apple)
- File issues at: [GitHub Issues](https://github.com/trading-dummy/issues)
```

### 9.2 API Documentation

```dart
// Create file: lib/auth/docs/apple_auth_api.md

/// # Apple Authentication API Documentation
/// 
/// ## AppleAuthService
/// 
/// Main service for handling Apple Sign-In authentication.
/// 
/// ### Methods
/// 
/// #### signIn()
/// Initiates Apple Sign-In flow.
/// 
/// **Returns:** `Future<UserModel?>` - User information or null if cancelled
/// 
/// **Throws:**
/// - `SignInWithAppleAuthorizationException` - Authorization errors
/// - `Exception` - Device compatibility or network errors
/// 
/// **Example:**
/// ```dart
/// final user = await appleAuthService.signIn();
/// if (user != null) {
///   print('Signed in as ${user.email}');
/// }
/// ```
/// 
/// #### silentSignIn()
/// Attempts to sign in using stored credentials.
/// 
/// **Returns:** `Future<UserModel?>` - User information or null if not available
/// 
/// **Example:**
/// ```dart
/// final user = await appleAuthService.silentSignIn();
/// if (user != null) {
///   // User was signed in silently
/// }
/// ```
/// 
/// #### isSignedIn()
/// Checks if user is currently signed in with valid credentials.
/// 
/// **Returns:** `Future<bool>` - True if signed in with valid credentials
/// 
/// #### getCredentialState(String userId)
/// Gets the credential state for a specific user.
/// 
/// **Parameters:**
/// - `userId` - The Apple user identifier
/// 
/// **Returns:** `Future<CredentialState>` - Current credential state
/// 
/// **States:**
/// - `CredentialState.authorized` - Credentials are valid
/// - `CredentialState.revoked` - User revoked authorization
/// - `CredentialState.notFound` - User not found
/// - `CredentialState.transferred` - Credentials transferred to another device
```

## Verification Checklist

### Phase 1: Configuration ✓
- [ ] Xcode entitlements linked
- [ ] Apple Developer Portal configured
- [ ] Service ID created
- [ ] Private key downloaded

### Phase 2: Implementation ✓
- [ ] Core service implemented
- [ ] Session management added
- [ ] Security enhancements complete
- [ ] Error handling improved

### Phase 3: Testing ✓
- [ ] Unit tests written
- [ ] Integration tests complete
- [ ] Manual testing on device
- [ ] All scenarios tested

### Phase 4: Documentation ✓
- [ ] Integration guide complete
- [ ] API documentation written
- [ ] Troubleshooting guide added
- [ ] Security practices documented

## Run Tests
```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/auth/apple_auth_service_test.dart

# Run integration tests
flutter test integration_test/apple_auth_integration_test.dart
```