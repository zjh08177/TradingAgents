# Eric Cleanup Command - Test & Verification

## Command Setup Complete ✅

The `/eric:cleanup` command has been successfully set up with the following components:

### Files Created:
1. **`.claude/commands/eric_cleanup.sh`** - Main command wrapper
2. **`.claude/commands/eric_cleanup.md`** - Command documentation
3. **`scripts/cleanup_stale_files.sh`** - Core cleanup logic
4. **`.claude/settings.json`** - Updated with command registration
5. **`.claude/commands.json`** - Command manifest for discovery

### Testing the Command

To test if the command is working in Claude Code:

1. **In Claude Code, try typing:**
   ```
   /eric:cleanup --help
   ```

2. **If the command doesn't appear:**
   - Restart Claude Code
   - Check if other custom commands like `/trace:analyze` work
   - Verify you're in the project root directory

3. **Manual Testing (if command doesn't show):**
   ```bash
   # Direct execution
   .claude/commands/eric_cleanup.sh --help
   
   # Dry run test
   .claude/commands/eric_cleanup.sh --dry-run
   
   # Full test (interactive)
   .claude/commands/eric_cleanup.sh
   ```

### Expected Behavior:

When you run `/eric:cleanup`, you should see:
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

### Troubleshooting:

1. **Command not found:**
   - Check: `ls -la .claude/commands/eric_cleanup.sh`
   - Ensure executable: `chmod +x .claude/commands/eric_cleanup.sh`

2. **Script errors:**
   - Check: `bash -n scripts/cleanup_stale_files.sh` (syntax check)
   - Test directly: `./scripts/cleanup_stale_files.sh --dry-run`

3. **Permission issues:**
   - Ensure write permissions in project directories
   - Check script permissions: `ls -la scripts/cleanup_stale_files.sh`

### Command Options:

- `/eric:cleanup` - Interactive mode (asks for confirmation)
- `/eric:cleanup --dry-run` - Preview what would be deleted
- `/eric:cleanup --auto` - Automatic cleanup (no prompts)
- `/eric:cleanup --help` - Show help information

### Integration:

The command integrates with:
- Debug logging system (cleans logs >7 days old)
- LangGraph checkpoints (removes all .pckl files)
- Trace analysis system (deduplicates and removes old traces)

### Next Steps:

1. Test the command in Claude Code
2. Run with `--dry-run` first to preview
3. Use `--auto` for CI/CD integration
4. Schedule weekly cleanup with cron

## Success Criteria:

✅ Command files created
✅ Scripts are executable
✅ Documentation updated
✅ Settings.json configured
✅ Manual testing works

The command should now be available as `/eric:cleanup` in Claude Code!