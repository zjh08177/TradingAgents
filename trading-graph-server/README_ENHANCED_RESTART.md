# Enhanced Trading Graph Server Restart Script

## 🎯 Overview

The `restart_server_enhanced.sh` script is an enhanced version of the original `restart_server.sh` that adds automatic ticker execution capabilities. It can start the LangGraph dev server and automatically kick off trading analysis for any specified ticker (e.g., TSLA, NVDA, AAPL).

## 🚀 Features

### Original Features (Preserved)
- ✅ Complete LangGraph process cleanup
- ✅ Editable mode package management
- ✅ Python cache cleanup
- ✅ Environment validation
- ✅ Fix validation (async pandas, error handling)
- ✅ Port 2024 management

### New Enhanced Features
- 🎯 **Ticker Parameter Support**: Specify any stock ticker
- ⚡ **Auto-Execution Mode**: Automatically run analysis after server startup
- 📝 **Dynamic Script Generation**: Creates custom execution scripts
- ⏰ **Configurable Wait Time**: Control delay before auto-execution
- 🔧 **Test Skipping**: Option to skip preliminary tests
- 📱 **Cross-Platform Support**: Works on macOS, Linux, and Windows
- 🎛️ **Flexible Execution**: Multiple execution modes and options

## 📋 Usage

### Basic Usage
```bash
# Start server only (original behavior)
./restart_server_enhanced.sh

# Start server with ticker preparation
./restart_server_enhanced.sh TSLA

# Start server and auto-execute TSLA analysis
./restart_server_enhanced.sh TSLA --auto-execute

# Start server, wait 15 seconds, then auto-execute NVDA
./restart_server_enhanced.sh NVDA --auto-execute --wait 15

# Start server and auto-execute AAPL without tests
./restart_server_enhanced.sh AAPL --auto-execute --skip-tests
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--auto-execute` | `-a` | Automatically execute analysis after startup | `false` |
| `--wait SECONDS` | `-w` | Wait time before auto-execution | `10` |
| `--skip-tests` | | Skip preliminary tests during execution | `false` |
| `--help` | `-h` | Show help message | |

### Example Commands
```bash
# Quick TSLA analysis
./restart_server_enhanced.sh TSLA -a

# Comprehensive NVDA analysis with longer wait
./restart_server_enhanced.sh NVDA --auto-execute --wait 20

# Fast AAPL analysis without tests
./restart_server_enhanced.sh AAPL -a --skip-tests

# Prepare GOOG analysis (manual execution)
./restart_server_enhanced.sh GOOG
```

## 🔧 How It Works

### 1. Server Initialization
The script performs all standard restart operations:
- Terminates existing LangGraph processes
- Validates and installs package in editable mode
- Cleans Python caches
- Validates environment and fixes

### 2. Ticker Script Generation
When a ticker is provided, the script:
- Creates a custom execution script: `execute_[ticker]_analysis.sh`
- Makes the script executable
- Configures appropriate flags based on options

### 3. Auto-Execution (Optional)
If `--auto-execute` is enabled:
- Starts the LangGraph server
- Waits for specified time (default: 10 seconds)
- Launches the analysis in a new terminal/background process
- Continues running the server

### 4. Manual Execution
If auto-execution is disabled:
- Displays the generated execution script path
- Provides quick command for manual execution
- Server runs normally for Studio access

## 📊 Generated Execution Scripts

When you specify a ticker, the script generates a custom execution script:

```bash
# Example: execute_tsla_analysis.sh
#!/bin/bash
# Auto-generated execution script for TSLA analysis

echo "🎯 Executing Trading Graph Analysis for TSLA"
echo "=========================================="

SCRIPT_FLAGS=""
if [[ "false" == "true" ]]; then
    SCRIPT_FLAGS="--skip-tests"
fi

# Execute the analysis
echo "🚀 Running: ./debug_local.sh TSLA $SCRIPT_FLAGS"
./debug_local.sh TSLA $SCRIPT_FLAGS

echo ""
echo "✅ Analysis complete for TSLA"
echo "📂 Check debug_logs/ for detailed results"
```

## 🎛️ Configuration

The script automatically detects and configures:
- Package installation mode (editable vs. regular)
- API key availability (OpenAI, Google)
- System fixes (async pandas, error handling)
- Port availability (2024)

## 📂 Output Files

### Server Outputs
- LangGraph dev server on `http://localhost:2024`
- API documentation at `http://localhost:2024/docs`
- LangSmith Studio integration

### Analysis Outputs
- Execution scripts: `execute_[ticker]_analysis.sh`
- Debug logs: `debug_logs/debug_session_[TICKER]_[timestamp].log`
- Results: `debug_logs/results_[TICKER]_[timestamp].json`
- Reports: `debug_logs/execution_report_[TICKER]_[timestamp].md`

## 🔍 Validation & Error Handling

The enhanced script includes comprehensive validation:

### Environment Validation
- ✅ `.env` file existence
- ✅ API key configuration
- ✅ Port availability
- ✅ Package installation mode

### System Fix Validation
- ✅ Async-compatible pandas integration
- ✅ AttributeError protection
- ✅ Empty response handlers
- ✅ Cache cleanup completion

### Execution Validation
- ✅ Ticker parameter format
- ✅ Execution script creation
- ✅ Script permissions
- ✅ Background process management

## 🎯 Examples

### Example 1: Quick TSLA Analysis
```bash
./restart_server_enhanced.sh TSLA --auto-execute
```

**Output:**
```
🔄 Enhanced Trading Graph Server Restart with Auto-Execution...
🎯 Target Ticker: TSLA
⚡ Auto-execution: ENABLED (wait: 10s)

🛑 Terminating existing LangGraph processes...
✅ All LangGraph processes terminated
📦 Package already in EDITABLE mode
🧹 Performing comprehensive Python module cleanup...
✅ Python module cleanup completed
🔍 Checking port 2024...
🔑 Checking environment variables...
✅ OpenAI API key configured
🔍 Validating system fixes...
✅ Async-compatible pandas market analyst found
📝 Creating execution script: execute_tsla_analysis.sh
✅ Execution script created and made executable

🚀 Starting Enhanced LangGraph Server...
📍 API: http://localhost:2024
🎯 Ticker Analysis Ready:
   • Target: TSLA
   • Auto-execution: ENABLED (10s wait)
   • Script: ./execute_tsla_analysis.sh

⏰ Waiting 10 seconds for server startup...
🎯 Auto-executing analysis for TSLA...
✅ Auto-execution initiated for TSLA
```

### Example 2: Manual NVDA Preparation
```bash
./restart_server_enhanced.sh NVDA
```

**Result:**
- Server starts normally
- Creates `execute_nvda_analysis.sh`
- Displays manual execution command: `./debug_local.sh NVDA`
- Server runs for Studio access

## 🔄 Migration from Original

To migrate from the original `restart_server.sh`:

1. **Backup the original:**
   ```bash
   cp restart_server.sh restart_server_original.sh
   ```

2. **Replace with enhanced version:**
   ```bash
   cp restart_server_enhanced.sh restart_server.sh
   ```

3. **Use new features:**
   ```bash
   # Old way
   ./restart_server.sh
   # Then manually run: ./debug_local.sh TICKER

   # New way
   ./restart_server.sh TICKER --auto-execute
   ```

## 🛠️ Troubleshooting

### Common Issues

**Issue: Port 2024 in use**
```bash
# The script automatically handles this
lsof -ti:2024 | xargs kill -9 2>/dev/null || true
```

**Issue: Package not in editable mode**
```bash
# The script automatically fixes this
pip uninstall agent -y
pip install -e . --quiet
```

**Issue: Auto-execution not working**
- Check if ticker is valid
- Ensure `debug_local.sh` exists
- Verify script permissions: `ls -la execute_*_analysis.sh`

**Issue: Terminal not opening on macOS**
- The script uses `osascript` for macOS
- Falls back to background execution if needed

### Debug Commands
```bash
# Check generated scripts
ls -la execute_*_analysis.sh

# Manual execution
./execute_tsla_analysis.sh

# Check server status
curl http://localhost:2024/docs

# View recent logs
tail -f debug_logs/debug_session_*_$(date +%Y%m%d)*.log
```

## 🎉 Benefits

### Developer Experience
- **One Command**: Start server and analysis with single command
- **No Context Switching**: Automatic execution reduces manual steps
- **Flexible Options**: Multiple execution modes for different needs
- **Clear Feedback**: Comprehensive status and progress information

### Productivity
- **Time Savings**: Eliminates manual execution steps
- **Consistency**: Standardized execution process
- **Automation**: Background execution allows parallel work
- **Integration**: Works seamlessly with existing tools

### Reliability
- **Comprehensive Cleanup**: Ensures clean server restart
- **Validation**: Multiple validation checkpoints
- **Error Handling**: Graceful error handling and recovery
- **Cross-Platform**: Works across different operating systems

## 📈 Performance Impact

The enhanced script adds minimal overhead:
- **Startup Time**: +2-3 seconds for script generation
- **Memory Usage**: Negligible additional memory
- **Background Execution**: Efficient process management
- **Server Performance**: No impact on LangGraph server performance

## 🔮 Future Enhancements

Potential future improvements:
- Multiple ticker support (`TSLA,NVDA,AAPL`)
- Configuration file support
- Integration with CI/CD pipelines
- Real-time progress monitoring
- Results aggregation and comparison
- Scheduled execution support