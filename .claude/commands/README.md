# Claude Code Custom Commands

This directory contains custom slash commands for Claude Code.

## Available Commands

### /trace:analyze
Analyze LangSmith traces for performance insights and optimization opportunities.

**Usage:**
```
/trace:analyze [trace_id] [--project project_name] [--format summary|json|both] [--verbose]
```

**Features:**
- Lists recent traces when no trace ID provided
- Analyzes trace performance against targets (120s runtime, 40K tokens)
- Provides quality grading (A+ to D)
- Identifies performance bottlenecks
- Categorizes errors
- Generates prioritized recommendations

## Command Structure

Each command consists of:
1. **Command File** (`.md` file) - Contains prompt template and instructions
2. **Filename becomes command** - `trace-analyze.md` becomes `/trace-analyze`

## Adding New Commands

To add a new command:

1. Create command file: `.claude/commands/your-command.md`
2. Write prompt template with instructions for Claude
3. Use `$ARGUMENTS` to capture command parameters
4. Add Bash permission to `settings.json` if needed:
   ```json
   "permissions": {
     "allow": [
       "Bash(your-script.sh *)"
     ]
   }
   ```

## How Commands Work

- Claude Code reads `.md` files in `.claude/commands/`
- The filename becomes the slash command name
- `$ARGUMENTS` is replaced with whatever you type after the command
- Claude executes the instructions as a prompt template

## Notes

- Commands are executed relative to the project root
- Environment variables from `.env` are automatically loaded
- Command handlers have access to all Bash permissions defined in settings