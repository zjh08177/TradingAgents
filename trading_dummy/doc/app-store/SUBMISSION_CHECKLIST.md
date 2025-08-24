# Minimal App Store Requirements - Trading Dummy

## ✅ COMPLETED (Already Done)
1. ~~**Privacy Policy** - Created in `/legal/PRIVACY_POLICY.md`~~
2. ~~**Terms of Service** - Created in `/legal/TERMS_OF_SERVICE.md`~~
3. ~~**Info.plist Configuration** - Privacy URL and security settings added~~
4. ~~**Financial Disclaimer** - Visible on analysis page~~
5. ~~**Apple/Google Sign-In** - Working authentication~~
6. ~~**NSAppTransportSecurity** - Configured for secure connections~~
7. ~~**Age Rating Config** - Set to 17+ in Info.plist~~

## 🔴 MANUAL STEPS REQUIRED

### Step 1: Host Legal Documents (15-20 minutes)

#### Option A: GitHub Pages (Recommended - FREE)
1. **Create a new GitHub repository**
   ```bash
   # Repository name: tradingdummy-legal
   # Make it public
   ```

2. **Upload legal documents**
   ```bash
   # Clone the repo
   git clone https://github.com/YOUR_USERNAME/tradingdummy-legal.git
   cd tradingdummy-legal
   
   # Copy legal documents
   cp /Users/bytedance/Documents/TradingAgents/trading_dummy/legal/PRIVACY_POLICY.md privacy.md
   cp /Users/bytedance/Documents/TradingAgents/trading_dummy/legal/TERMS_OF_SERVICE.md terms.md
   
   # Create index.html for better presentation
   echo '<!DOCTYPE html>
   <html>
   <head><title>Trading Dummy Legal</title></head>
   <body>
   <h1>Trading Dummy Legal Documents</h1>
   <ul>
   <li><a href="privacy.html">Privacy Policy</a></li>
   <li><a href="terms.html">Terms of Service</a></li>
   </ul>
   </body>
   </html>' > index.html
   
   # Commit and push
   git add .
   git commit -m "Add legal documents"
   git push
   ```

3. **Enable GitHub Pages**
   - Go to Settings → Pages
   - Source: Deploy from branch
   - Branch: main, folder: / (root)
   - Click Save
   - Wait 2-3 minutes for deployment
   - Your URLs will be:
     - `https://YOUR_USERNAME.github.io/tradingdummy-legal/privacy`
     - `https://YOUR_USERNAME.github.io/tradingdummy-legal/terms`

4. **Update Info.plist with real URL**
   ```bash
   # Open Xcode
   open /Users/bytedance/Documents/TradingAgents/trading_dummy/ios/Runner.xcworkspace
   
   # In Xcode:
   # 1. Click Runner in left sidebar
   # 2. Click Info tab
   # 3. Find NSPrivacyPolicyURL
   # 4. Change value to: https://YOUR_USERNAME.github.io/tradingdummy-legal/privacy
   ```

### Step 2: Create App Icon (20 minutes)

1. **Create a simple icon** (if you don't have one)
   ```bash
   # Option 1: Use SF Symbols (Quick)
   # Open SF Symbols app on Mac
   # Search for "chart.line.uptrend.xyaxis"
   # Export as 1024x1024 PNG
   
   # Option 2: Use Preview app
   # - Create new from clipboard (1024x1024)
   # - Add text "TD" with large font
   # - Add background color
   # - Save as PNG (no transparency)
   ```

2. **Generate all required sizes**
   - Go to https://www.appicon.co/
   - Upload your 1024x1024 icon
   - Download iOS icons
   - Unzip the file

3. **Add to Xcode**
   ```bash
   # In Xcode (already open from Step 1):
   # 1. Click Runner → Assets.xcassets → AppIcon
   # 2. Drag each icon size to its slot
   # 3. Make sure 1024x1024 "App Store" slot is filled
   ```

### Step 3: Take Screenshots (15 minutes)

1. **Open iOS Simulator**
   ```bash
   # In Xcode:
   # 1. Select iPhone 15 Pro Max (6.7") simulator
   # 2. Press Cmd+R to run
   ```

2. **Take required screenshots**
   ```bash
   # In Simulator, navigate to each screen and press Cmd+S
   
   # Screenshot 1: Sign-In Screen
   # - Shows Apple/Google sign-in buttons
   # - Professional looking auth screen
   
   # Screenshot 2: Analysis Input
   # - Show ticker input field with "AAPL" typed
   # - Shows the financial disclaimer warning
   
   # Screenshot 3: Analysis Results  
   # - Show a completed analysis
   # - Demonstrates the AI output
   
   # Screenshots saved to Desktop by default
   ```

3. **Optional: Take iPad screenshots**
   ```bash
   # Switch to iPad Pro 12.9" simulator
   # Repeat the 3 screenshots
   # Apple prefers both iPhone and iPad shots
   ```

### Step 4: Prepare App Store Connect Info (10 minutes)

1. **Write App Description** (copy this or modify):
   ```
   Trading Dummy - AI-Powered Stock Analysis
   
   Get instant AI-generated analysis for any stock ticker using advanced language models. Simply enter a ticker symbol and receive comprehensive trading insights.
   
   Features:
   • AI-powered analysis using OpenAI or Google AI
   • Secure API key storage on device
   • Sign in with Apple or Google
   • Clean, simple interface
   • Historical analysis tracking
   
   Note: You provide your own API keys. This app provides educational analysis only, not financial advice.
   ```

2. **Prepare Keywords**:
   ```
   stock, trading, analysis, AI, market, finance, investment, OpenAI, GPT
   ```

3. **Prepare Support URL**:
   ```
   Use: https://github.com/YOUR_USERNAME/tradingdummy-support
   (Create empty repo for support/issues)
   ```

### Step 5: Build for Release (20 minutes)

1. **Clean and prepare**
   ```bash
   cd /Users/bytedance/Documents/TradingAgents/trading_dummy
   
   # Clean everything
   flutter clean
   rm -rf ios/Pods
   rm ios/Podfile.lock
   
   # Get dependencies
   flutter pub get
   
   # iOS specific
   cd ios
   pod install
   cd ..
   ```

2. **Build release version**
   ```bash
   # Build for iOS
   flutter build ios --release --no-codesign
   ```

3. **Open in Xcode for archive**
   ```bash
   open ios/Runner.xcworkspace
   ```

4. **Configure signing in Xcode**
   ```
   1. Select Runner target
   2. Signing & Capabilities tab
   3. Team: Select your Apple Developer team
   4. Bundle ID: com.tradingDummy.zjh (already set)
   5. ✅ Automatically manage signing
   ```

### Step 6: Archive and Upload (30 minutes)

1. **Create Archive**
   ```
   In Xcode:
   1. Select "Any iOS Device (arm64)" as target
   2. Menu: Product → Clean Build Folder (Cmd+Shift+K)
   3. Menu: Product → Archive
   4. Wait for archive to complete (3-5 minutes)
   ```

2. **Upload to App Store Connect**
   ```
   In Organizer window (opens automatically):
   1. Select your archive
   2. Click "Distribute App"
   3. Select "App Store Connect"
   4. Select "Upload"
   5. Keep all defaults, click Next
   6. Review, click Upload
   7. Wait for upload (2-5 minutes)
   ```

### Step 7: Submit in App Store Connect (20 minutes)

1. **Login to App Store Connect**
   ```
   https://appstoreconnect.apple.com
   ```

2. **Create New App**
   ```
   My Apps → "+" → New App
   Platform: iOS
   Name: Trading Dummy
   Primary Language: English (U.S.)
   Bundle ID: Select com.tradingDummy.zjh
   SKU: trading-dummy-v1
   ```

3. **Fill Required Information**
   ```
   Version Information:
   - Screenshots: Upload the 3 you took
   - Description: Paste from Step 4
   - Keywords: Paste from Step 4
   - Support URL: Your GitHub repo
   - Category: Finance
   
   General App Information:
   - App Icon: Will auto-populate from build
   - Rating: 17+ (Frequent/Intense Simulated Gambling)
   - Copyright: © 2024 Your Name
   
   App Privacy:
   - Start questionnaire
   - Data not collected (we don't send data to servers)
   - Publish on App Store
   ```

4. **Submit for Review**
   ```
   1. Select build from TestFlight builds
   2. Add release notes: "Initial release"
   3. Click "Submit for Review"
   ```

## ⏱ Total Time Breakdown
- Step 1: Host docs - 20 min
- Step 2: App icon - 20 min  
- Step 3: Screenshots - 15 min
- Step 4: Prepare info - 10 min
- Step 5: Build - 20 min
- Step 6: Archive/Upload - 30 min
- Step 7: Submit - 20 min
- **TOTAL: ~2 hours 15 minutes**

## 🎯 Success Criteria
- ✅ Legal docs hosted and accessible
- ✅ App icon in all sizes
- ✅ 3+ screenshots per device type
- ✅ Clean build with no warnings
- ✅ Successful upload to App Store Connect
- ✅ All required fields completed
- ✅ Submitted for review

## Common Issues & Solutions

**Issue**: Archive button grayed out
**Fix**: Select "Any iOS Device" not simulator

**Issue**: Signing errors
**Fix**: Ensure Apple Developer account is active ($99/year)

**Issue**: Upload fails
**Fix**: Update Xcode to latest version

**Issue**: Missing icon
**Fix**: Ensure 1024x1024 icon has NO transparency

## After Submission
- Review typically takes 24-48 hours
- Watch email for any requests from Apple
- Be ready to respond to reviewer questions
- Once approved, app goes live immediately