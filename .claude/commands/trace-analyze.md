# Analyze LangSmith Trace

Analyze a LangSmith trace for performance insights and optimization opportunities.

## Instructions

You are a trace analysis specialist. Follow these steps to analyze the LangSmith trace:

1. **Setup Environment**
   - Change to the scripts directory: `cd trading-graph-server/scripts`
   - Verify the analyzer script exists: `ls -la analyze_trace_production.sh`

2. **Parse Arguments**
   - Extract trace ID from: $ARGUMENTS
   - Look for additional flags: --project, --format, --verbose

3. **Execute Analysis**
   - If no trace ID provided: Run `./analyze_trace_production.sh --list-recent`
   - If trace ID provided: Run `./analyze_trace_production.sh [TRACE_ID] [FLAGS]`

4. **Analysis Tasks**
   - Check environment setup (Python, LangSmith API key)
   - Fetch and analyze the specified trace
   - Generate comprehensive performance report
   - Provide prioritized recommendations

5. **Output Format**
   - Quality grading (A+ to D)
   - Token usage analysis vs targets
   - Performance bottleneck detection
   - Error categorization
   - Tool usage metrics
   - Timing analysis

## Examples of Usage
- `/trace:analyze` - List recent traces
- `/trace:analyze 1f06e57b-ff55-6312-ab60-8724837bd9be` - Analyze specific trace
- `/trace:analyze abc123 --project my-project` - Analyze with custom project
- `/trace:analyze abc123 --format json` - Get JSON output

Use the arguments provided as: $ARGUMENTS