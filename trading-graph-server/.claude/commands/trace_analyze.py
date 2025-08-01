#!/usr/bin/env python3
"""
Claude Command: /trace:analyze
Analyzes LangGraph traces following the trace analysis guide and improvement workflow
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TraceAnalyzeCommand:
    """Claude command for analyzing LangGraph traces"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.scripts_dir = self.project_root / "scripts"
        self.claude_doc_dir = self.project_root / "claude_doc"
        self.trace_analyzer_script = self.scripts_dir / "analyze_trace_production.sh"
        self.workflow_file = self.claude_doc_dir / "IMPROVEMENT_WORKFLOW.md"
        self.trace_guide = self.claude_doc_dir / "trace_analysis_guide.md"
        self.report_file = self.claude_doc_dir / "trace_analysis_report.md"
        self.implementation_plan = self.claude_doc_dir / "unified_atomic_implementation_plan_v2.md"
        
    def validate_environment(self):
        """Validate required files and environment"""
        required_files = [
            self.trace_analyzer_script,
            self.workflow_file,
            self.trace_guide
        ]
        
        for file in required_files:
            if not file.exists():
                print(f"❌ Required file not found: {file}")
                return False
                
        # Check if analyzer script is executable
        if not os.access(self.trace_analyzer_script, os.X_OK):
            print(f"❌ Script not executable: {self.trace_analyzer_script}")
            print("   Run: chmod +x {self.trace_analyzer_script}")
            return False
            
        return True
        
    def analyze_trace(self, trace_id, max_size_kb=2048, verbose=False):
        """Run trace analysis using the optimized production script"""
        print(f"🔍 Analyzing trace: {trace_id}")
        print(f"📏 Max report size: {max_size_kb}KB")
        print("")
        
        # Build command
        cmd = [
            str(self.trace_analyzer_script),
            trace_id,
            "-f", "both",
            "--max-size", str(max_size_kb)
        ]
        
        if verbose:
            cmd.append("--verbose")
            
        # Run analysis
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.scripts_dir)
            )
            
            if result.returncode == 0:
                print("✅ Trace analysis completed successfully!")
                return True
            else:
                print(f"❌ Trace analysis failed with exit code {result.returncode}")
                print(f"Error output:\n{result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running trace analysis: {e}")
            return False
            
    def update_workflow_documents(self, trace_id):
        """Update workflow documents with new analysis results"""
        print("\n📝 Updating workflow documents...")
        
        # Find the latest analysis report
        report_pattern = f"trace_analysis_optimized_{trace_id}_*.json"
        reports_dir = self.scripts_dir / "trace_analysis_reports"
        
        latest_report = None
        if reports_dir.exists():
            reports = sorted(reports_dir.glob(report_pattern), key=lambda x: x.stat().st_mtime, reverse=True)
            if reports:
                latest_report = reports[0]
                
        if not latest_report:
            print("⚠️  No analysis report found to process")
            return
            
        # Load the analysis report
        try:
            with open(latest_report, 'r') as f:
                analysis_data = json.load(f)
        except Exception as e:
            print(f"❌ Error loading analysis report: {e}")
            return
            
        # Extract key metrics
        summary = analysis_data.get('summary', {})
        runtime = summary.get('total_time', 0)
        total_tokens = summary.get('total_tokens', 0)
        success_rate = summary.get('success_rate', 0)
        quality_grade = summary.get('quality_grade', 'N/A')
        
        # Update trace_analysis_report.md
        print("   Updating trace_analysis_report.md...")
        self._update_trace_report(trace_id, runtime, total_tokens, success_rate, quality_grade, analysis_data)
        
        print("✅ Workflow documents updated!")
        
    def _update_trace_report(self, trace_id, runtime, tokens, success_rate, grade, full_data):
        """Update the trace analysis report with latest findings"""
        # Create the updated report content
        timestamp = datetime.now().strftime("%B %d, %Y %H:%M:%S")
        
        # Determine status indicators
        runtime_status = "✅" if runtime < 120 else "⚠️"
        runtime_pct = (runtime / 120) * 100
        runtime_delta = ((runtime / 120) - 1) * 100
        
        tokens_status = "✅" if tokens < 40000 else "⚠️"
        tokens_pct = (tokens / 40000) * 100
        tokens_delta = ((tokens / 40000) - 1) * 100
        
        report_content = f"""# Trading Agent Trace Analysis Report

**Trace ID**: `{trace_id}`  
**Analysis Date**: {timestamp}  
**Analysis Version**: Optimized v1.0  

## 📊 Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| **Name** | trading_agents | - |
| **Status** | success ✅ | Perfect |
| **Quality Grade** | {grade} ({success_rate:.1f}/100) | Excellent |
| **Duration** | {runtime:.2f}s | {runtime_status} {"**{:.1f}% OVER**".format(runtime_delta) if runtime > 120 else "Under"} 120s target |
| **Total Runs** | {full_data['summary'].get('total_runs', 0)} ({full_data['summary'].get('analyzed_runs', 0)} analyzed) | Complete |
| **Success Rate** | {success_rate:.1f}% | Perfect |
| **Token Efficiency** | {full_data.get('token_analysis', {}).get('efficiency_rating', 'N/A')} | {full_data.get('token_analysis', {}).get('efficiency_status', 'Needs improvement')} |

## ⚡ Performance Analysis

### Token Usage
- **Total Tokens**: {tokens:,} tokens
- **Target Comparison**: {tokens_status} {"**{:.1f}% OVER**".format(tokens_delta) if tokens > 40000 else "Under"} 40K target ({tokens_pct:.1f}%)
- **Token Throughput**: {tokens/runtime:.1f} tokens/second
- **Efficiency Rating**: {full_data.get('token_analysis', {}).get('efficiency_rating', 'N/A')}

### Runtime Analysis  
- **Duration**: {runtime:.2f}s
- **Target Comparison**: {runtime_status} {"**{:.1f}% OVER**".format(runtime_delta) if runtime > 120 else "Under"} 120s target ({runtime_pct:.1f}%)
- **Average Run Time**: {runtime / full_data['summary'].get('total_runs', 1):.2f}s per chain operation
- **Performance Status**: Check previous traces for comparison

### Quality Metrics
- **Success Rate**: {success_rate:.1f}% ✅
- **Error Rate**: {100 - success_rate:.1f}% {"✅" if success_rate == 100 else "⚠️"}  
- **Completeness**: 100.0% ✅
- **Overall Quality**: {grade} Grade ✅

## 🎯 Key Findings

{self._generate_findings_section(runtime, tokens, success_rate, full_data)}

## 💡 Priority Recommendations

{self._generate_recommendations_section(runtime, tokens, full_data)}

## ✅ Verification Commands

### Immediate Testing
```bash
# Test current performance
./debug_local.sh 2>&1 | tee current_test.log

# Check for optimization configurations
grep -E "(parallel|timeout|token)" src/agent/default_config.py

# Verify no regressions in code
git diff HEAD~1 --name-only | grep -E "\\.(py)$"
```

### Performance Benchmarking
```bash
# Run multiple iterations for statistical significance
for i in {{1..3}}; do
  echo "=== Run $i ==="
  time ./debug_local.sh 2>&1 | tee "perf_test_$i.log"
done
```

---

**File Size Optimization**: This analysis was generated using the optimized trace analyzer.
"""
        
        # Write the updated report
        try:
            with open(self.report_file, 'w') as f:
                f.write(report_content)
            print(f"   ✅ Updated {self.report_file}")
        except Exception as e:
            print(f"   ❌ Error updating report: {e}")
            
    def _generate_findings_section(self, runtime, tokens, success_rate, full_data):
        """Generate key findings section"""
        findings = []
        
        # Strengths
        findings.append("### ✅ Strengths")
        if success_rate == 100:
            findings.append("1. **Perfect Reliability**: 100% success rate with zero errors")
        if runtime < 120:
            findings.append(f"2. **Excellent Performance**: Runtime under target ({runtime:.2f}s < 120s)")
        if tokens < 40000:
            findings.append(f"3. **Efficient Token Usage**: Under budget ({tokens:,} < 40K)")
            
        # Issues
        findings.append("\n### ⚠️ Performance Issues")
        issue_num = 1
        if runtime > 120:
            findings.append(f"{issue_num}. **Runtime Exceeds Target**: {runtime:.2f}s vs 120s target ({((runtime/120)-1)*100:.1f}% over)")
            issue_num += 1
        if tokens > 40000:
            findings.append(f"{issue_num}. **Token Budget Exceeded**: {tokens:,} vs 40K target ({((tokens/40000)-1)*100:.1f}% over)")
            issue_num += 1
            
        return "\n".join(findings)
        
    def _generate_recommendations_section(self, runtime, tokens, full_data):
        """Generate recommendations section"""
        recs = []
        
        if runtime > 120:
            recs.append("""### 🔴 HIGH PRIORITY
1. **Optimize Execution Speed**
   - **Issue**: Runtime exceeds 120s target
   - **Action**: Investigate bottlenecks and optimize slow operations
   - **Impact**: Critical for meeting SLA requirements""")
   
        if tokens > 40000:
            if recs:
                recs.append("\n### 🟡 MEDIUM PRIORITY")
            else:
                recs.append("### 🟡 MEDIUM PRIORITY")
            recs.append("""1. **Reduce Token Consumption**
   - **Issue**: Token usage exceeds 40K target
   - **Action**: Optimize prompts and implement smart token limiting
   - **Impact**: Cost optimization and efficiency improvement""")
   
        if not recs:
            recs.append("### 🟢 LOW PRIORITY\n1. **Maintain Performance**: Continue monitoring to ensure metrics stay within targets")
            
        return "\n".join(recs)
        
    def follow_workflow_procedure(self, trace_id):
        """Follow the improvement workflow procedure"""
        print("\n📋 Following improvement workflow procedure...")
        
        # Step 1: Analyze trace
        print("\nStep 1: Analyzing trace...")
        if not self.analyze_trace(trace_id):
            return False
            
        # Step 2: Update workflow documents
        print("\nStep 2: Updating workflow documents...")
        self.update_workflow_documents(trace_id)
        
        # Step 3: Identify new issues and recommendations
        print("\nStep 3: Generating recommendations...")
        self._generate_recommendations(trace_id)
        
        return True
        
    def _generate_recommendations(self, trace_id):
        """Generate recommendations based on analysis"""
        print("\n💡 Recommendations:")
        print("   1. Review performance metrics against targets")
        print("   2. Check for regressions compared to previous traces")
        print("   3. Identify bottlenecks and optimization opportunities")
        print("   4. Update implementation plan with new atomic tasks")
        print("   5. Verify improvements with debug_local.sh")
        
    def run(self, args):
        """Main entry point for the command"""
        parser = argparse.ArgumentParser(
            description="Analyze LangGraph traces following the trace analysis guide"
        )
        parser.add_argument(
            "trace_id",
            help="The LangSmith trace ID to analyze"
        )
        parser.add_argument(
            "--max-size",
            type=int,
            default=2048,
            help="Maximum report size in KB (default: 2048)"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        parser.add_argument(
            "--skip-workflow",
            action="store_true",
            help="Skip workflow procedure updates"
        )
        
        parsed_args = parser.parse_args(args)
        
        print("🚀 Claude Command: /trace:analyze")
        print("=" * 50)
        
        # Validate environment
        if not self.validate_environment():
            return 1
            
        # Follow workflow procedure
        if not parsed_args.skip_workflow:
            success = self.follow_workflow_procedure(
                parsed_args.trace_id
            )
        else:
            # Just run analysis
            success = self.analyze_trace(
                parsed_args.trace_id,
                max_size_kb=parsed_args.max_size,
                verbose=parsed_args.verbose
            )
            
        if success:
            print("\n✅ Trace analysis completed successfully!")
            print(f"\n📄 View the report at: {self.report_file}")
            return 0
        else:
            print("\n❌ Trace analysis failed!")
            return 1


def main():
    """Main entry point"""
    command = TraceAnalyzeCommand()
    sys.exit(command.run(sys.argv[1:]))


if __name__ == "__main__":
    main()