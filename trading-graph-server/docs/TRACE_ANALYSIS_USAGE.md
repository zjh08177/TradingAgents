# LangSmith Trace Analysis Usage Guide

## Overview
The trace analysis tool is available both as a Claude Code slash command and as a command-line utility for analyzing LangSmith traces.

## Location
The trace analyzer is located at:
```
trading-graph-server/scripts/analyze_trace_production.sh
```

## Usage

### Claude Code Slash Command (NEW!)

The trace analyzer is now available as a Claude Code slash command:

```
/trace:analyze [trace_id] [--project project_name] [--format summary|json|both] [--verbose]
```

#### Examples:
- List recent traces: `/trace:analyze`
- Analyze specific trace: `/trace:analyze 1f06e57b-ff55-6312-ab60-8724837bd9be`
- Analyze with project: `/trace:analyze abc123 --project my-project`
- Get JSON output: `/trace:analyze abc123 --format json`

### Command-Line Usage

1. **Check environment setup:**
   ```bash
   cd trading-graph-server/scripts
   ./analyze_trace_production.sh --env-check
   ```

2. **List recent traces:**
   ```bash
   ./analyze_trace_production.sh --list-recent
   ```

3. **Analyze a specific trace:**
   ```bash
   ./analyze_trace_production.sh <TRACE_ID>
   ```

4. **Analyze with summary output only:**
   ```bash
   ./analyze_trace_production.sh <TRACE_ID> -f summary
   ```

5. **Analyze with JSON output:**
   ```bash
   ./analyze_trace_production.sh <TRACE_ID> -f json
   ```

### Advanced Options

- `-p, --project`: Specify LangSmith project name (default: trading-agent-graph)
- `-o, --output`: Custom output file path
- `-f, --format`: Output format: summary, json, both (default: both)
- `-v, --verbose`: Enable verbose logging
- `-s, --max-size`: Maximum file size in KB (default: 2048)

### Examples

```bash
# Analyze the default trace
./analyze_trace_production.sh

# Analyze a specific trace from a different project
./analyze_trace_production.sh abc123 -p my-project

# Save analysis to custom location
./analyze_trace_production.sh abc123 -o /tmp/analysis.json -f json

# Analyze with 1MB file size limit
./analyze_trace_production.sh abc123 --max-size 1024
```

## Features

- Enhanced analysis with 7 comprehensive categories
- Size-optimized reports (under 2MB by default)
- Performance regression detection
- Priority-based recommendations
- Quality grading system (A+ to D)
- Token usage analysis
- Error categorization
- Tool performance metrics
- Timing bottleneck detection

## Requirements

- Python 3.x
- LangSmith API key (set as LANGSMITH_API_KEY environment variable)
- langsmith Python package (auto-installed if missing)

## Output

The analyzer produces:
- Executive summary with quality grade
- Performance metrics vs targets
- Tool usage analysis
- Error analysis (if any)
- Timing bottlenecks
- Prioritized recommendations
- Overall assessment

Reports are saved to `trace_analysis_reports/` directory by default.