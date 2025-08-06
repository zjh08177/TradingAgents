#!/bin/bash

# iOS Build Optimization Script
# Run this before building to ensure optimal performance

echo "🚀 iOS Build Optimization Script"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Clean old DerivedData (keep last 3 days)
echo "🧹 Cleaning old DerivedData..."
find ~/Library/Developer/Xcode/DerivedData -type d -name "trading_dummy-*" -mtime +3 -exec rm -rf {} \; 2>/dev/null || true
echo -e "${GREEN}✓ DerivedData cleaned${NC}"

# 2. Optimize Xcode build settings
echo "⚙️  Setting Xcode build optimizations..."
defaults write com.apple.dt.Xcode ShowBuildOperationDuration YES
defaults write com.apple.dt.Xcode BuildSystemScheduleInherentlyParallelCommandsExclusively YES
defaults write com.apple.dt.Xcode IDEBuildOperationMaxNumberOfConcurrentCompileTasks $(sysctl -n hw.ncpu)
defaults write com.apple.dt.Xcode PBXNumberOfParallelBuildSubtasks $(sysctl -n hw.ncpu)
defaults write com.apple.dt.Xcode IDEIndexDisable 0
echo -e "${GREEN}✓ Xcode settings optimized${NC}"

# 3. Warm up CocoaPods cache
echo "📦 Warming up CocoaPods cache..."
export COCOAPODS_DISABLE_STATS=true
export CP_REPOS_DIR="$HOME/.cocoapods/repos"
if [ ! -d "$CP_REPOS_DIR/trunk" ]; then
    pod repo add-cdn trunk https://cdn.cocoapods.org/ 2>/dev/null || true
fi
echo -e "${GREEN}✓ CocoaPods cache ready${NC}"

# 4. Create build cache directories
echo "📁 Creating cache directories..."
mkdir -p ~/Library/Caches/XcodeBuildCache
mkdir -p ~/Library/Developer/Xcode/DerivedData
mkdir -p ~/Library/Caches/CocoaPods
echo -e "${GREEN}✓ Cache directories created${NC}"

# 5. Set environment variables
echo "🔧 Setting environment variables..."
export XCODE_BUILD_PARALLELIZATION=YES
export XCODE_PARALLEL_BUILD_LIMIT=$(sysctl -n hw.ncpu)
export COCOAPODS_PARALLEL_DOWNLOADS=8
export DERIVED_DATA_PATH="$HOME/Library/Developer/Xcode/DerivedData"
echo -e "${GREEN}✓ Environment configured${NC}"

# 6. Optimize simulator
echo "📱 Optimizing iOS Simulator..."
xcrun simctl shutdown all 2>/dev/null || true
xcrun simctl erase all 2>/dev/null || true
echo -e "${GREEN}✓ Simulator optimized${NC}"

echo ""
echo -e "${GREEN}✅ iOS build optimization complete!${NC}"
echo ""
echo "Tips for faster builds:"
echo "1. Use 'flutter run' instead of Xcode when possible"
echo "2. Keep the simulator open between builds"
echo "3. Use hot reload (r) and hot restart (R)"
echo "4. Run 'pod install' only when dependencies change"
echo ""