# /eric:cleanup - Disk Space Cleanup Tool

## Purpose
Clean up stale files, remove old logs, and optimize disk usage in the trading-graph-server project.

## Usage
```
/eric:cleanup [options]
```

## Options
- `--auto` - Run in automatic mode without prompts
- `--dry-run` - Preview what would be removed without actually deleting
- `--verbose` - Show detailed output during cleanup
- `--help` - Display help information

## Examples
```bash
# Interactive cleanup (default)
/eric:cleanup

# Preview what would be cleaned
/eric:cleanup --dry-run

# Automatic cleanup (no prompts)
/eric:cleanup --auto

# Automatic cleanup with details
/eric:cleanup --auto --verbose
```

## What It Cleans

### 1. Debug Logs
- Removes logs older than 7 days
- Location: `debug_logs/`
- Pattern: `debug_session_*.log`

### 2. Trace Analysis Files
- Removes duplicate trace files (keeps latest)
- Removes traces older than 3 days
- Location: `trace_analysis_reports/` and root
- Pattern: `trace_analysis_*.json`

### 3. LangGraph Checkpoints
- Removes all checkpoint files
- Location: `.langgraph_api/`
- Pattern: `*.pckl`

### 4. Temporary Files
- Various temporary and cache files
- Preserves active session data

## Retention Policies

| File Type | Retention Period | Reason |
|-----------|-----------------|---------|
| Debug Logs | 7 days | Recent logs needed for troubleshooting |
| Trace Analysis | 3 days | Performance data analysis |
| Checkpoints | 1 day | Temporary state files |
| Data Cache | 14 days | Market data for testing |

## Features

- **Safe Operation**: Always preserves recent and important files
- **Dry Run Mode**: Preview changes before execution
- **Duplicate Detection**: Removes duplicate trace files automatically
- **Space Reports**: Shows before/after disk usage
- **Color Output**: Easy-to-read status indicators

## Integration

This command integrates with:
- `/trace:analyze` - Cleans up old trace analysis files
- Debug logging system - Manages debug log rotation
- LangGraph checkpoints - Removes temporary state files

## Best Practices

1. **Preview First**: Always run with `--dry-run` before actual cleanup
2. **Regular Schedule**: Run weekly to prevent accumulation
3. **Archive Important**: Save important traces before cleanup
4. **Monitor Usage**: Check disk usage trends over time

## Automation

Add to cron for weekly automatic cleanup:
```bash
0 0 * * 0 cd /path/to/project && /eric:cleanup --auto
```

## Implementation Details

The command executes `scripts/cleanup_stale_files.sh` which:
1. Identifies files based on age and type
2. Calculates space to be freed
3. Removes files safely with logging
4. Provides detailed summary report

## Error Handling

- Validates script existence
- Handles permission errors gracefully
- Provides clear error messages
- Returns appropriate exit codes

## Performance Impact

- Minimal CPU usage
- Fast execution (typically < 5 seconds)
- No impact on running services
- Safe to run during active development