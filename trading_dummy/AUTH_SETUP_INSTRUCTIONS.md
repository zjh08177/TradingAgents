# Authentication Setup Instructions

This guide provides step-by-step instructions to complete the authentication setup for both Apple Sign-In and Google Sign-In.

## Prerequisites

- Apple Developer Account (for Apple Sign-In)
- Firebase/Google Cloud Account (for Google Sign-In)
- Xcode installed (for iOS development)
- Android Studio installed (for Android development)

## What Has Been Implemented

The following configuration changes have been made to fix the authentication issues:

### iOS Configuration
- ✅ Created `Runner.entitlements` with Apple Sign-In capability
- ✅ Updated `Info.plist` with URL schemes placeholders
- ✅ Updated `AppDelegate.swift` for Google Sign-In URL handling
- ✅ Created placeholder for `GoogleService-Info.plist`

### Android Configuration
- ✅ Updated `settings.gradle.kts` to include Google Services plugin
- ✅ Updated `app/build.gradle.kts` to apply Google Services plugin
- ✅ Changed package name from `com.example.trading_dummy` to `com.tradingdummy.app`
- ✅ Created new `MainActivity.kt` with correct package
- ✅ Updated `AndroidManifest.xml` with new MainActivity reference
- ✅ Created placeholder for `google-services.json`

## Required Manual Steps

### 1. Apple Sign-In Setup (iOS Only)

#### In Apple Developer Portal:
1. Sign in to [Apple Developer Portal](https://developer.apple.com)
2. Navigate to **Certificates, Identifiers & Profiles** → **Identifiers**
3. Create a new App ID or select your existing one:
   - **Bundle ID**: `com.tradingdummy.app` (or your custom bundle ID)
   - Enable **Sign In with Apple** capability
   - Save the configuration

#### In Xcode:
1. Open `ios/Runner.xcworkspace` in Xcode
2. Select the **Runner** target
3. Go to **Signing & Capabilities** tab
4. Ensure your team is selected and automatic signing is enabled
5. The **Sign In with Apple** capability should already be present (from the `.entitlements` file)
6. Update the **Bundle Identifier** to match your App ID (e.g., `com.tradingdummy.app`)

### 2. Google Sign-In Setup (iOS & Android)

#### In Firebase Console:
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project or select existing one
3. Add both iOS and Android apps:

##### For iOS:
- **iOS bundle ID**: `com.tradingdummy.app`
- Download `GoogleService-Info.plist`
- Replace the placeholder file:
  ```bash
  rm ios/Runner/GoogleService-Info.plist.PLACEHOLDER
  # Copy downloaded GoogleService-Info.plist to ios/Runner/
  ```
- Add to Xcode project (drag into Runner folder)

##### For Android:
- **Android package name**: `com.tradingdummy.app`
- Add your SHA certificates:
  ```bash
  # Debug certificate
  keytool -list -v \
    -keystore ~/.android/debug.keystore \
    -alias androiddebugkey \
    -storepass android \
    -keypass android
  
  # Copy both SHA-1 and SHA-256 to Firebase
  ```
- Download `google-services.json`
- Replace the placeholder file:
  ```bash
  rm android/app/google-services.json.PLACEHOLDER
  # Copy downloaded google-services.json to android/app/
  ```

### 3. Update iOS Info.plist

After obtaining your `GoogleService-Info.plist`, you need to update the `Info.plist`:

1. Open `GoogleService-Info.plist` and find the `REVERSED_CLIENT_ID`
2. Edit `ios/Runner/Info.plist`
3. Replace `com.googleusercontent.apps.YOUR_REVERSED_CLIENT_ID` with your actual reversed client ID

### 4. Clean and Rebuild

After completing the setup:

```bash
# Clean Flutter build
flutter clean

# Get dependencies
flutter pub get

# For iOS
cd ios && pod install && cd ..

# Run the app
flutter run
```

## Testing Checklist

### iOS Testing
- [ ] Test Apple Sign-In on iOS Simulator (limited functionality)
- [ ] Test Apple Sign-In on physical iOS device (full functionality)
- [ ] Test Google Sign-In on iOS Simulator
- [ ] Test Google Sign-In on physical iOS device

### Android Testing
- [ ] Test Google Sign-In on Android Emulator
- [ ] Test Google Sign-In on physical Android device

## Troubleshooting

### Apple Sign-In Issues
- **Error 1000**: Ensure entitlements file is included in build settings
- **Error 1001**: Check bundle ID matches Apple Developer Portal
- **Not Available**: Apple Sign-In requires iOS 13.0+

### Google Sign-In Issues
- **Crash on start**: Ensure `google-services.json` or `GoogleService-Info.plist` is present
- **SHA mismatch**: Re-add SHA certificates and download new config files
- **Network error**: Check internet connectivity and OAuth consent screen setup

### Common Issues
- **Bundle ID mismatch**: Ensure all bundle IDs are consistent across:
  - Xcode project settings
  - Apple Developer Portal
  - Firebase/Google Cloud Console
  - Info.plist configurations

- **Missing files**: Verify all required files are in place:
  - `ios/Runner/Runner.entitlements`
  - `ios/Runner/GoogleService-Info.plist` (not placeholder)
  - `android/app/google-services.json` (not placeholder)

## Security Notes

1. **Never commit** `GoogleService-Info.plist` or `google-services.json` to public repositories
2. Add these files to `.gitignore`:
   ```
   ios/Runner/GoogleService-Info.plist
   android/app/google-services.json
   ```
3. Use environment-specific configuration files for different build environments
4. Implement proper token refresh mechanisms in production

## Next Steps

1. Complete the manual setup steps above
2. Test authentication on both platforms
3. Implement token refresh logic if not already present
4. Add error handling for edge cases
5. Consider adding biometric authentication as an additional option