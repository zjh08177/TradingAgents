# Eric Cleanup Command - Quick Start Guide

## Installation
The `/eric:cleanup` command has been successfully installed in your Claude Code environment.

## Usage

### Basic Usage
```bash
# Interactive cleanup (asks for confirmation)
/eric:cleanup

# Preview what would be cleaned (dry run)
/eric:cleanup --dry-run

# Automatic cleanup (no prompts)
/eric:cleanup --auto

# Verbose output
/eric:cleanup --auto --verbose
```

### What It Does

1. **Removes LangGraph Checkpoints** - Temporary state files that accumulate
2. **Cleans Debug Logs** - Removes logs older than 7 days
3. **Deduplicates Trace Files** - Keeps only the latest trace analysis per ID
4. **Optimizes Disk Space** - Can free up 100+ MB of space

### Example Output
```
🧹 Eric's Cleanup Command
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Project: /path/to/trading-graph-server
🔧 Mode: auto

📊 Analyzing disk usage...

Current disk usage by directory:
--------------------------------
  debug_logs:                    9.6M (88 files)
  scripts/trace_analysis_reports: 6.6M (23 files)
  dataflows/data_cache:          8.5M (35 files)
  .langgraph_api:               288K (7 files)

🚀 Starting cleanup process...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Cleanup completed successfully!
  Total files removed: 95
  Total space freed: 100.3 MB
```

### Automation

Add to your crontab for weekly automatic cleanup:
```bash
# Run every Sunday at midnight
0 0 * * 0 cd /path/to/project && /eric:cleanup --auto
```

### Safety Features

- **Dry Run Mode**: Always preview changes before deletion
- **Retention Policies**: Keeps recent files based on type
- **No Critical Files**: Never touches source code or config
- **Detailed Logging**: Shows exactly what was removed

### Integration with Other Commands

Works alongside:
- `/trace:analyze` - Cleans up old trace analysis files
- Debug logging system - Manages log rotation
- LangGraph - Removes temporary checkpoints

## Troubleshooting

If the command doesn't work:
1. Check that you're in the project root directory
2. Verify the scripts exist: `ls -la scripts/cleanup_stale_files.sh`
3. Check permissions: `chmod +x scripts/cleanup_stale_files.sh`

## File Locations

- Command script: `.claude/commands/eric/cleanup.sh`
- Cleanup logic: `scripts/cleanup_stale_files.sh`
- Documentation: `.claude/commands/eric/cleanup.md`