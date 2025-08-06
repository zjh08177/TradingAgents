#!/bin/bash

# Flutter Build Performance Measurement Script
# This script measures and reports Flutter build times

echo "🚀 Flutter Build Performance Measurement"
echo "========================================"
echo ""

# Clean build artifacts for accurate measurement
echo "🧹 Cleaning build artifacts..."
flutter clean > /dev/null 2>&1

# Remove iOS pods for clean measurement
if [ -d "ios" ]; then
    echo "🧹 Cleaning iOS pods..."
    rm -rf ios/Pods ios/.symlinks ios/Podfile.lock > /dev/null 2>&1
fi

# Remove Dart tool and build directories
rm -rf .dart_tool build > /dev/null 2>&1

echo "✅ Clean complete"
echo ""

# Measure pub get time
echo "📦 Measuring dependency resolution time..."
PUB_START=$(date +%s)
flutter pub get
PUB_END=$(date +%s)
PUB_TIME=$((PUB_END - PUB_START))
echo "✅ Dependency resolution: ${PUB_TIME}s"
echo ""

# Measure iOS pod install time (if on macOS)
if [ -d "ios" ] && [ "$(uname)" = "Darwin" ]; then
    echo "🍎 Measuring iOS pod installation time..."
    POD_START=$(date +%s)
    cd ios && pod install && cd ..
    POD_END=$(date +%s)
    POD_TIME=$((POD_END - POD_START))
    echo "✅ Pod installation: ${POD_TIME}s"
    echo ""
fi

# Measure first build time (cold build)
echo "🔨 Measuring cold build time..."
echo "This may take a while..."
BUILD_START=$(date +%s)

# Run build based on platform
if [ "$(uname)" = "Darwin" ]; then
    # macOS - build for iOS simulator
    flutter build ios --simulator --debug
else
    # Linux/Windows - build for Android
    flutter build apk --debug
fi

BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))
echo "✅ Cold build time: ${BUILD_TIME}s"
echo ""

# Calculate total time
TOTAL_TIME=$((PUB_TIME + ${POD_TIME:-0} + BUILD_TIME))

# Generate report
echo "📊 Build Performance Report"
echo "=========================="
echo "Dependency resolution: ${PUB_TIME}s"
if [ -n "$POD_TIME" ]; then
    echo "iOS pod installation: ${POD_TIME}s"
fi
echo "Cold build time: ${BUILD_TIME}s"
echo "--------------------------"
echo "Total time: ${TOTAL_TIME}s ($(printf '%d:%02d' $((TOTAL_TIME/60)) $((TOTAL_TIME%60))))"
echo ""

# Compare with target
TARGET=60  # 1 minute target
if [ $TOTAL_TIME -le $TARGET ]; then
    echo "✅ Build time is within target (<1 minute)!"
else
    OVERHEAD=$((TOTAL_TIME - TARGET))
    echo "⚠️  Build time exceeds target by ${OVERHEAD}s"
fi

# Save results
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "" >> build_performance_log.txt
echo "[$TIMESTAMP] Total: ${TOTAL_TIME}s | Deps: ${PUB_TIME}s | Pods: ${POD_TIME:-N/A}s | Build: ${BUILD_TIME}s" >> build_performance_log.txt

echo ""
echo "💾 Results saved to build_performance_log.txt"