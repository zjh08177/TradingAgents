# Troubleshooting the Cleanup Command in Claude Code

## Issue: Command Not Showing in Claude Code

If the `/cleanup` or `/eric:cleanup` command is not showing up in Claude Code, here are several solutions:

## Solution 1: Direct Execution

The command files have been created and are executable. You can run them directly:

```bash
# From project root
.claude/commands/cleanup --help
.claude/commands/cleanup --dry-run
.claude/commands/cleanup --auto
```

## Solution 2: Check Claude Code Version

Some versions of Claude Code may have different command discovery mechanisms. Try:

1. **Restart Claude Code** completely (not just reload)
2. **Clear Claude Code cache** if available in settings
3. **Check if `/trace:analyze` works** - if it doesn't, project commands may be disabled

## Solution 3: Manual Command Invocation

Even if the command doesn't show in autocomplete, try typing it anyway:
- Type `/cleanup` and press Enter
- Type `/eric:cleanup` and press Enter

## Solution 4: Alternative Execution Methods

### Direct Script Execution:
```bash
# Run the cleanup script directly
./scripts/cleanup_stale_files.sh --help
./scripts/cleanup_stale_files.sh --dry-run
./scripts/cleanup_stale_files.sh --auto
```

### Python Script:
```bash
# Run via Python
python3 .claude/commands/cleanup.py --help
python3 .claude/commands/cleanup.py --dry-run
```

## Files Created

All necessary files have been created:
```
.claude/
├── commands/
│   ├── cleanup           # Shell wrapper (no extension)
│   ├── cleanup.sh        # Shell wrapper with extension
│   ├── cleanup.py        # Python implementation
│   ├── cleanup.md        # Documentation
│   ├── eric_cleanup.sh   # Alternative name
│   └── eric_cleanup.md   # Alternative documentation
├── settings.json         # Command registration
└── commands.json         # Command manifest
```

## Testing the Implementation

### Test 1: Shell Script
```bash
# Should show usage
.claude/commands/cleanup.sh --help

# Should show what would be removed
.claude/commands/cleanup.sh --dry-run
```

### Test 2: Python Script
```bash
# Should show usage
python3 .claude/commands/cleanup.py --help

# Should show cleanup output
python3 .claude/commands/cleanup.py --dry-run
```

### Test 3: Direct Script
```bash
# Should work from anywhere in project
./scripts/cleanup_stale_files.sh --dry-run
```

## Expected Output

When the command runs successfully, you should see:
```
🧹 Trading Graph Server Cleanup Tool
============================================================
📍 Root directory: /path/to/trading-graph-server

🗄️  Cleaning LangGraph checkpoints...
📋 Cleaning duplicate trace files...
📁 Cleaning stale debug logs...
📊 Cleaning old trace analysis files...

✅ Cleanup Summary:
  Total files removed: X
  Total space freed: X MB
```

## Common Issues

1. **Permission Denied**: Make sure scripts are executable
   ```bash
   chmod +x .claude/commands/cleanup*
   chmod +x scripts/cleanup_stale_files.sh
   ```

2. **Command Not Found**: Check you're in the project root
   ```bash
   pwd  # Should show .../trading-graph-server
   ```

3. **Python Not Found**: Use python3 explicitly
   ```bash
   python3 .claude/commands/cleanup.py --help
   ```

## Next Steps

1. The command infrastructure is fully set up
2. All files are created and executable
3. Multiple execution methods are available
4. Even if Claude Code doesn't recognize the command, the scripts work independently

The cleanup functionality is ready to use via any of the methods above!