# Claude Commands for Trading Agent

This directory contains custom Claude commands for the Trading Agent project.

## Available Commands

### `/trace:analyze`

Analyzes LangGraph traces following the trace analysis guide and improvement workflow.

**Usage:**
```bash
# Basic usage - analyze a trace
/trace:analyze 1f06e434-b0a5-6f70-8758-d8b558bf7a46

# With custom size limit
/trace:analyze 1f06e434-b0a5-6f70-8758-d8b558bf7a46 --max-size 1024

# With verbose output
/trace:analyze 1f06e434-b0a5-6f70-8758-d8b558bf7a46 --verbose

# Skip workflow updates (just analyze)
/trace:analyze 1f06e434-b0a5-6f70-8758-d8b558bf7a46 --skip-workflow
```

**Features:**
- Uses the optimized trace analyzer (guaranteed <2MB reports)
- Follows the improvement workflow procedure automatically
- Updates `trace_analysis_report.md` with findings
- Generates priority-based recommendations
- Provides verification commands for testing

**Options:**
- `trace_id`: The LangSmith trace ID to analyze (required)
- `--max-size`: Maximum report size in KB (default: 2048)
- `--verbose`: Enable verbose output
- `--skip-workflow`: Skip workflow document updates

**Output:**
1. Runs optimized trace analysis
2. Updates `claude_doc/trace_analysis_report.md`
3. Identifies performance issues and regressions
4. Provides actionable recommendations
5. Includes verification commands

**Example Output:**
```
🚀 Claude Command: /trace:analyze
==================================================
🔍 Analyzing trace: 1f06e434-b0a5-6f70-8758-d8b558bf7a46
📏 Max report size: 2048KB

✅ Trace analysis completed successfully!

📝 Updating workflow documents...
   Updating trace_analysis_report.md...
   - Trace ID: 1f06e434-b0a5-6f70-8758-d8b558bf7a46
   - Runtime: 130.79s (target: <120s)
   - Tokens: 48,726 (target: <40K)
   - Success Rate: 100.0%
   - Quality Grade: A+
   ✅ Updated claude_doc/trace_analysis_report.md
✅ Workflow documents updated!

💡 Recommendations:
   1. Review performance metrics against targets
   2. Check for regressions compared to previous traces
   3. Identify bottlenecks and optimization opportunities
   4. Update implementation plan with new atomic tasks
   5. Verify improvements with debug_local.sh

✅ Trace analysis completed successfully!

📄 View the report at: claude_doc/trace_analysis_report.md
```

## Implementation Details

The commands are implemented as Python scripts with shell wrappers for easy invocation. Each command:

1. Validates the environment and required files
2. Executes the main functionality
3. Updates relevant documentation
4. Provides actionable output

## Adding New Commands

To add a new Claude command:

1. Create a Python script in this directory (e.g., `my_command.py`)
2. Create a shell wrapper (e.g., `my_command.sh`)
3. Make the shell script executable: `chmod +x my_command.sh`
4. Update this README with documentation

## Integration with Workflow

These commands are designed to integrate with the Trading Agent improvement workflow:

- `trace_analysis_report.md`: Updated with latest trace findings
- `unified_atomic_implementation_plan_v2.md`: Source of truth for improvements
- `IMPROVEMENT_WORKFLOW.md`: Defines the continuous improvement process

The commands follow the established two-document system and workflow procedures.