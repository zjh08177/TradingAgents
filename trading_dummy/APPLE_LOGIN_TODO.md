# Apple Login Implementation - TODO List

## Current State Analysis

### ✅ Completed Components
1. **Core Service Implementation** (`lib/auth/services/apple_auth_service.dart`)
   - Basic Apple Sign-In flow implemented
   - Nonce generation for security
   - User model creation from Apple credentials
   - Error handling for authorization exceptions
   - Credential state checking

2. **UI Integration** (`lib/auth/screens/login_screen.dart`)
   - Apple Sign-In button implemented (iOS/macOS only)
   - Platform detection to show button conditionally
   - Loading states and error display

3. **ViewModel Integration** (`lib/auth/view_models/auth_view_model.dart`)
   - `signInWithApple()` method implemented
   - Platform checking (iOS/macOS only)
   - User storage after successful auth
   - Navigation to home screen post-authentication

4. **Package Integration**
   - `sign_in_with_apple` package added to dependencies
   - iOS pods configured and installed

5. **Basic iOS Configuration**
   - Entitlements file exists with Sign In with Apple capability
   - Bundle ID configured: `com.tradingDummy.zjh`

## 🚧 Missing/Incomplete Components

### 1. iOS Configuration Issues
- [ ] **CODE_SIGN_ENTITLEMENTS not linked in Xcode project**
  - The entitlements file exists but isn't referenced in project.pbxproj
  - Need to add CODE_SIGN_ENTITLEMENTS build setting

### 2. Apple Developer Portal Setup
- [ ] **App ID Configuration**
  - Enable Sign In with Apple capability in Apple Developer Portal
  - Configure Sign In with Apple for the App ID
- [ ] **Service ID Creation (for web/Android support)**
  - Create Service ID for non-Apple platforms
  - Configure return URLs and domains
- [ ] **Key Generation**
  - Generate Sign In with Apple private key
  - Download and secure the .p8 key file

### 3. Backend Integration
- [ ] **Token Validation**
  - Implement server-side validation of Apple ID tokens
  - Verify JWT signatures using Apple's public keys
- [ ] **User Account Linking**
  - Handle first-time vs returning users
  - Link Apple ID with existing user accounts
- [ ] **Refresh Token Management**
  - Store and manage Apple refresh tokens
  - Implement token refresh logic

### 4. Testing
- [ ] **Unit Tests**
  - Create MockAppleAuthService for testing
  - Add tests for AppleAuthService methods
  - Test error scenarios and edge cases
- [ ] **Integration Tests**
  - Test full authentication flow
  - Verify token storage and retrieval
  - Test session restoration

### 5. Session Management
- [ ] **Silent Sign-In Implementation**
  - Currently returns null - needs proper implementation
  - Store and validate credentials locally
  - Check token expiry and refresh as needed
- [ ] **Sign-In Status Check**
  - `isSignedIn()` currently always returns false
  - Implement proper credential validation
  - Check stored tokens and expiry

### 6. Security Enhancements
- [ ] **Nonce Storage and Validation**
  - Store nonce before authentication
  - Validate nonce in response
  - Implement SHA256 hashing for nonce
- [ ] **Keychain Integration**
  - Securely store tokens in iOS Keychain
  - Implement secure token retrieval

### 7. Android Support (Optional)
- [ ] **Web-based Apple Sign-In**
  - Configure Service ID for Android
  - Implement web OAuth flow
  - Handle deep linking for return

### 8. Error Handling & UX
- [ ] **Better Error Messages**
  - Map Apple error codes to user-friendly messages
  - Handle network errors gracefully
  - Implement retry mechanisms
- [ ] **Loading States**
  - Add proper loading indicators during auth
  - Handle timeout scenarios

### 9. Documentation
- [ ] **Integration Guide**
  - Document Apple Developer Portal setup
  - Provide step-by-step configuration guide
  - Include troubleshooting section
- [ ] **API Documentation**
  - Document all public methods
  - Include usage examples
  - Document error codes and handling

## Priority Implementation Steps

### Phase 1: iOS Configuration (Critical)
1. Link entitlements file in Xcode project
2. Configure App ID in Apple Developer Portal
3. Test on physical iOS device

### Phase 2: Testing (High Priority)
1. Create mock service for unit tests
2. Write comprehensive test suite
3. Test edge cases and error scenarios

### Phase 3: Session Management (High Priority)
1. Implement proper credential storage
2. Add silent sign-in functionality
3. Implement sign-in status checking

### Phase 4: Backend Integration (Medium Priority)
1. Set up token validation endpoint
2. Implement user account management
3. Handle token refresh

### Phase 5: Polish (Low Priority)
1. Improve error messages
2. Add analytics tracking
3. Enhance documentation

## Configuration Checklist

### Apple Developer Portal
- [ ] App ID with Sign In with Apple enabled
- [ ] Service ID created (for web/Android)
- [ ] Private key generated and downloaded
- [ ] Team ID noted
- [ ] Key ID noted

### Xcode Project
- [ ] Entitlements file linked in build settings
- [ ] Signing & Capabilities updated
- [ ] Bundle ID matches Apple Developer Portal
- [ ] Minimum iOS version set (13.0+)

### Environment Variables Needed
```env
APPLE_TEAM_ID=<your_team_id>
APPLE_KEY_ID=<your_key_id>
APPLE_PRIVATE_KEY=<path_to_p8_file>
APPLE_SERVICE_ID=<service_id_for_web>
```

## Testing Checklist
- [ ] Test on real iOS device
- [ ] Test cancel flow
- [ ] Test error scenarios
- [ ] Test token expiry
- [ ] Test app reinstall scenario
- [ ] Test network failure
- [ ] Test with different Apple IDs
- [ ] Test email hiding option

## Known Issues
1. Silent sign-in not implemented - always returns null
2. Sign-in status check not implemented - always returns false
3. No backend validation - relies on client-side only
4. No token refresh mechanism
5. Android support not implemented

## Resources
- [Apple Developer Documentation](https://developer.apple.com/sign-in-with-apple/)
- [sign_in_with_apple Package](https://pub.dev/packages/sign_in_with_apple)
- [JWT Validation Guide](https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_rest_api/verifying_a_user)
- [Flutter Integration Guide](https://pub.dev/packages/sign_in_with_apple#integration)