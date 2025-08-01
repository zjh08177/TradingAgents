#!/bin/bash

# Claude Code command implementation for /eric:cleanup
# Cleanup stale files and optimize disk usage

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
MODE="interactive"
DRY_RUN=""
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --auto)
            MODE="auto"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --verbose)
            VERBOSE="true"
            shift
            ;;
        --help)
            echo "Usage: /eric:cleanup [options]"
            echo ""
            echo "Options:"
            echo "  --auto      Run in automatic mode (no prompts)"
            echo "  --dry-run   Show what would be cleaned without removing files"
            echo "  --verbose   Show detailed output"
            echo "  --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  /eric:cleanup                  # Interactive cleanup"
            echo "  /eric:cleanup --dry-run        # Preview what would be removed"
            echo "  /eric:cleanup --auto           # Automatic cleanup"
            echo "  /eric:cleanup --auto --verbose # Automatic with details"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Header
echo -e "${BLUE}🧹 Eric's Cleanup Command${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "📍 Project: ${PROJECT_ROOT}"
echo -e "🔧 Mode: ${MODE}$([ -n "$DRY_RUN" ] && echo " (dry-run)")"
echo ""

# Check if cleanup script exists
CLEANUP_SCRIPT="${PROJECT_ROOT}/scripts/cleanup_stale_files.sh"
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo -e "${RED}❌ Error: Cleanup script not found at:${NC}"
    echo "   $CLEANUP_SCRIPT"
    echo ""
    echo "Creating cleanup script..."
    
    # Create the cleanup script if it doesn't exist
    cat > "$CLEANUP_SCRIPT" << 'EOF'
#!/bin/bash
# Auto-generated cleanup script
echo "Cleanup script placeholder - please implement actual cleanup logic"
EOF
    chmod +x "$CLEANUP_SCRIPT"
    echo -e "${GREEN}✅ Created placeholder cleanup script${NC}"
    exit 1
fi

# Run pre-cleanup analysis
echo -e "${YELLOW}📊 Analyzing disk usage...${NC}"
echo ""

# Show current disk usage
echo "Current disk usage by directory:"
echo "--------------------------------"
for dir in "debug_logs" "scripts/trace_analysis_reports" "dataflows/data_cache" ".langgraph_api"; do
    if [ -d "${PROJECT_ROOT}/${dir}" ]; then
        size=$(du -sh "${PROJECT_ROOT}/${dir}" 2>/dev/null | cut -f1 || echo "N/A")
        count=$(find "${PROJECT_ROOT}/${dir}" -type f 2>/dev/null | wc -l | tr -d ' ')
        printf "  %-30s %8s (%s files)\n" "$dir:" "$size" "$count"
    fi
done
echo ""

# Build cleanup command
CLEANUP_CMD="$CLEANUP_SCRIPT"
if [ "$MODE" = "auto" ]; then
    CLEANUP_CMD="$CLEANUP_CMD --auto"
fi
if [ -n "$DRY_RUN" ]; then
    CLEANUP_CMD="$CLEANUP_CMD --dry-run"
fi

# Show what will be run
if [ "$VERBOSE" = "true" ]; then
    echo -e "${BLUE}Running command:${NC} $CLEANUP_CMD"
    echo ""
fi

# Execute cleanup
echo -e "${YELLOW}🚀 Starting cleanup process...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the cleanup script and capture the exit code
if $CLEANUP_CMD; then
    EXIT_CODE=0
else
    EXIT_CODE=$?
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Post-cleanup summary
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Cleanup completed successfully!${NC}"
    
    # Show updated disk usage if not in dry-run mode
    if [ -z "$DRY_RUN" ]; then
        echo ""
        echo "Updated disk usage:"
        echo "------------------"
        for dir in "debug_logs" "scripts/trace_analysis_reports" "dataflows/data_cache" ".langgraph_api"; do
            if [ -d "${PROJECT_ROOT}/${dir}" ]; then
                size=$(du -sh "${PROJECT_ROOT}/${dir}" 2>/dev/null | cut -f1 || echo "N/A")
                count=$(find "${PROJECT_ROOT}/${dir}" -type f 2>/dev/null | wc -l | tr -d ' ')
                printf "  %-30s %8s (%s files)\n" "$dir:" "$size" "$count"
            fi
        done
    fi
else
    echo -e "${RED}❌ Cleanup failed with exit code: $EXIT_CODE${NC}"
fi

# Helpful tips
echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo "  • Use --dry-run first to preview changes"
echo "  • Run weekly to maintain optimal disk usage"
echo "  • Add to cron for automatic cleanup: 0 0 * * 0 /eric:cleanup --auto"
echo "  • Check cleanup logs in: ${PROJECT_ROOT}/debug_logs/"

exit $EXIT_CODE