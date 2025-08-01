#!/bin/bash

# Cleanup script for removing stale files in the trading-graph-server project
# Usage: ./cleanup_stale_files.sh [--auto] [--dry-run]

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
AUTO_MODE=false
DRY_RUN=false
DAYS_OLD_LOGS=7
DAYS_OLD_TRACES=3
DAYS_OLD_CHECKPOINTS=1
DAYS_OLD_CACHE=14

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--auto] [--dry-run]"
            echo "  --auto     Run without prompting for confirmation"
            echo "  --dry-run  Show what would be removed without actually removing"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🧹 Trading Graph Server Cleanup Tool${NC}"
echo "============================================================"
echo -e "📍 Root directory: ${ROOT_DIR}"
echo ""

# Initialize counters
TOTAL_FILES_REMOVED=0
TOTAL_SIZE_FREED=0

# Function to convert bytes to human readable format
human_readable() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes}B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$((bytes / 1024))KB"
    elif [ $bytes -lt 1073741824 ]; then
        echo "$((bytes / 1048576))MB"
    else
        echo "$((bytes / 1073741824))GB"
    fi
}

# Function to get file size in bytes
get_file_size() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        stat -f%z "$1" 2>/dev/null || echo 0
    else
        stat -c%s "$1" 2>/dev/null || echo 0
    fi
}

# Function to remove files with logging
remove_file() {
    local file=$1
    local size=$(get_file_size "$file")
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}[DRY RUN]${NC} Would remove: $(basename "$file") ($(human_readable $size))"
    else
        if rm -f "$file" 2>/dev/null; then
            echo -e "  ${GREEN}Removed:${NC} $(basename "$file") ($(human_readable $size))"
            TOTAL_FILES_REMOVED=$((TOTAL_FILES_REMOVED + 1))
            TOTAL_SIZE_FREED=$((TOTAL_SIZE_FREED + size))
            return 0
        else
            echo -e "  ${RED}Error removing:${NC} $(basename "$file")"
            return 1
        fi
    fi
}

# Clean up LangGraph checkpoints
echo -e "\n${YELLOW}🗄️  Cleaning LangGraph checkpoints...${NC}"
CHECKPOINT_DIR="${ROOT_DIR}/.langgraph_api"
CHECKPOINT_COUNT=0
CHECKPOINT_SIZE=0

if [ -d "$CHECKPOINT_DIR" ]; then
    while IFS= read -r -d '' file; do
        size=$(get_file_size "$file")
        CHECKPOINT_SIZE=$((CHECKPOINT_SIZE + size))
        remove_file "$file"
        CHECKPOINT_COUNT=$((CHECKPOINT_COUNT + 1))
    done < <(find "$CHECKPOINT_DIR" -name "*.pckl" -type f -print0 2>/dev/null)
    
    echo -e "  ${GREEN}Processed${NC} $CHECKPOINT_COUNT checkpoint files ($(human_readable $CHECKPOINT_SIZE))"
else
    echo "  No checkpoint directory found"
fi

# Clean up duplicate trace files
echo -e "\n${YELLOW}📋 Cleaning duplicate trace files...${NC}"
TRACE_COUNT=0
TRACE_SIZE=0

# Find all trace analysis files and keep only the latest per trace ID
# First, collect all trace files
temp_file=$(mktemp)
find "$ROOT_DIR" -name "trace_analysis_*.json" -type f -print0 2>/dev/null | while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    # Extract trace ID from filename (handle both formats)
    trace_id=""
    if [[ $filename =~ trace_analysis_optimized_([a-f0-9-]+)_ ]]; then
        trace_id="${BASH_REMATCH[1]}"
    elif [[ $filename =~ trace_analysis_([a-f0-9-]+)_ ]]; then
        trace_id="${BASH_REMATCH[1]}"
    fi
    
    if [ -n "$trace_id" ]; then
        # Get modification time in seconds since epoch
        if [[ "$OSTYPE" == "darwin"* ]]; then
            mtime=$(stat -f%m "$file")
        else
            mtime=$(stat -c%Y "$file")
        fi
        echo "$trace_id|$mtime|$file" >> "$temp_file"
    fi
done

# Process duplicates
if [ -f "$temp_file" ] && [ -s "$temp_file" ]; then
    # Sort by trace_id and modification time (newest first)
    sort -t'|' -k1,1 -k2,2nr "$temp_file" | while IFS='|' read -r trace_id mtime file; do
        # Check if we've seen this trace_id before
        if grep -q "^${trace_id}_KEEP$" "$temp_file.processed" 2>/dev/null; then
            # This is a duplicate (older version), remove it
            size=$(get_file_size "$file")
            TRACE_SIZE=$((TRACE_SIZE + size))
            remove_file "$file"
            TRACE_COUNT=$((TRACE_COUNT + 1))
        else
            # Mark this trace_id as processed (keep the first/newest)
            echo "${trace_id}_KEEP" >> "$temp_file.processed"
        fi
    done
fi

# Cleanup temp files
rm -f "$temp_file" "$temp_file.processed" 2>/dev/null

echo -e "  ${GREEN}Removed${NC} $TRACE_COUNT duplicate files ($(human_readable $TRACE_SIZE))"

# Find and remove stale debug logs
echo -e "\n${YELLOW}📁 Cleaning stale debug logs...${NC}"
LOG_COUNT=0
LOG_SIZE=0

while IFS= read -r -d '' file; do
    size=$(get_file_size "$file")
    LOG_SIZE=$((LOG_SIZE + size))
    remove_file "$file"
    LOG_COUNT=$((LOG_COUNT + 1))
done < <(find "${ROOT_DIR}/debug_logs" -name "debug_session_*.log" -type f -mtime +${DAYS_OLD_LOGS} -print0 2>/dev/null)

echo -e "  ${GREEN}Processed${NC} $LOG_COUNT log files older than $DAYS_OLD_LOGS days ($(human_readable $LOG_SIZE))"

# Find and remove old trace analysis files
echo -e "\n${YELLOW}📊 Cleaning old trace analysis files...${NC}"
OLD_TRACE_COUNT=0
OLD_TRACE_SIZE=0

while IFS= read -r -d '' file; do
    size=$(get_file_size "$file")
    OLD_TRACE_SIZE=$((OLD_TRACE_SIZE + size))
    remove_file "$file"
    OLD_TRACE_COUNT=$((OLD_TRACE_COUNT + 1))
done < <(find "$ROOT_DIR" -name "trace_analysis_*.json" -type f -mtime +${DAYS_OLD_TRACES} -print0 2>/dev/null)

echo -e "  ${GREEN}Processed${NC} $OLD_TRACE_COUNT trace files older than $DAYS_OLD_TRACES days ($(human_readable $OLD_TRACE_SIZE))"

# Summary
echo -e "\n${GREEN}✅ Cleanup Summary:${NC}"
echo "============================================================"

if [ "$DRY_RUN" = true ]; then
    TOTAL_SIZE=$((CHECKPOINT_SIZE + TRACE_SIZE + LOG_SIZE + OLD_TRACE_SIZE))
    TOTAL_FILES=$((CHECKPOINT_COUNT + TRACE_COUNT + LOG_COUNT + OLD_TRACE_COUNT))
    echo -e "  ${YELLOW}[DRY RUN MODE]${NC} No files were actually removed"
    echo -e "  Would remove: ${TOTAL_FILES} files"
    echo -e "  Would free: $(human_readable $TOTAL_SIZE)"
else
    echo -e "  Total files removed: ${TOTAL_FILES_REMOVED}"
    echo -e "  Total space freed: $(human_readable $TOTAL_SIZE_FREED)"
fi

# Recommendations
echo -e "\n${BLUE}💡 Recommendations:${NC}"
echo "  1. Run this cleanup script weekly to maintain disk space"
echo "  2. Use --dry-run first to preview what will be removed"
echo "  3. Archive important trace analyses before cleanup"
echo "  4. Add cleanup to CI/CD pipeline"

# Show current disk usage
echo -e "\n${BLUE}📊 Current Disk Usage:${NC}"
echo -n "  Debug logs: "
du -sh "${ROOT_DIR}/debug_logs" 2>/dev/null | cut -f1 || echo "N/A"
echo -n "  Trace reports: "
du -sh "${ROOT_DIR}/scripts/trace_analysis_reports" 2>/dev/null | cut -f1 || echo "N/A"
echo -n "  Data cache: "
du -sh "${ROOT_DIR}/dataflows/data_cache" 2>/dev/null | cut -f1 || echo "N/A"

# Ask for confirmation if not in auto mode and not dry run
if [ "$AUTO_MODE" = false ] && [ "$DRY_RUN" = false ] && [ $TOTAL_FILES_REMOVED -eq 0 ]; then
    echo -e "\n${YELLOW}No files have been removed yet.${NC}"
    read -p "Run cleanup now? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Cleanup cancelled${NC}"
        exit 0
    fi
fi