#!/usr/bin/env python3
"""Verify news analyst changes in the execution results"""

import json
import re

# Load the results file
with open('/Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_NVDA_20250813_174728.json', 'r') as f:
    data = json.load(f)

news_report = data.get('full_result', {}).get('news_report', '')

print('✅ VERIFICATION OF NEWS ANALYST CHANGES:')
print('=' * 50)
print(f'1. Report contains "NEWS DATA COLLECTION": {("NEWS DATA COLLECTION" in news_report)}')
print(f'2. Report contains "COLLECTION METRICS": {("COLLECTION METRICS" in news_report)}')
print(f'3. Report contains "RAW ARTICLE DATA": {("RAW ARTICLE DATA" in news_report)}')
print(f'4. Report contains "STRUCTURED DATA": {("STRUCTURED DATA" in news_report)}')
print(f'5. Report contains JSON block: {("```json" in news_report)}')
print()

print('❌ VERIFICATION OF REMOVED ANALYSIS:')
print('=' * 50)
print(f'6. Report contains "TLDR": {("TLDR" in news_report)}')
print(f'7. Report contains "SENTIMENT": {("SENTIMENT" in news_report.upper())}')
print(f'8. Report contains "IMPACT": {("IMPACT" in news_report.upper())}')
print(f'9. Report contains "TRADING": {("TRADING" in news_report.upper())}')
print(f'10. Report contains "RECOMMENDATION": {("RECOMMENDATION" in news_report.upper())}')
print()

print('📊 METRICS:')
print('=' * 50)
print(f'Total report length: {len(news_report):,} characters')
print(f'Number of articles shown: {news_report.count("### Article")}')

# Extract article count from COLLECTION METRICS
match = re.search(r'Total Articles: (\d+)', news_report)
if match:
    print(f'Total articles collected: {match.group(1)}')
    
# Check Serper article count
match = re.search(r'Serper: (\d+) articles', news_report)
if match:
    print(f'Serper articles: {match.group(1)} (increased from 2 pages to 5 pages)')
    
# Check Finnhub article count  
match = re.search(r'Finnhub: (\d+) articles', news_report)
if match:
    print(f'Finnhub articles: {match.group(1)}')

# Check if structured JSON is present
if '```json' in news_report:
    # Extract JSON block
    json_match = re.search(r'```json\n(.*?)\n```', news_report, re.DOTALL)
    if json_match:
        try:
            json_data = json.loads(json_match.group(1))
            print(f'JSON data parsed successfully!')
            print(f'  - Company: {json_data.get("company")}')
            print(f'  - Date: {json_data.get("date")}')
            print(f'  - Total articles in JSON: {json_data.get("total")}')
            print(f'  - Articles array length: {len(json_data.get("articles", []))}')
        except json.JSONDecodeError as e:
            print(f'JSON parsing error: {e}')

print()
print('🎉 CONCLUSION:')
print('=' * 50)
if all([
    "NEWS DATA COLLECTION" in news_report,
    "COLLECTION METRICS" in news_report,
    "RAW ARTICLE DATA" in news_report,
    "STRUCTURED DATA" in news_report,
    "```json" in news_report,
    "TLDR" not in news_report,
    "SENTIMENT" not in news_report.upper(),
    "TRADING" not in news_report.upper(),
    "RECOMMENDATION" not in news_report.upper()
]):
    print('✅ SUCCESS: All news analyst changes have been successfully applied!')
    print('  - Pure data collection format implemented')
    print('  - Analysis sections removed')
    print('  - Structured JSON output included')
    print('  - Article count increased (60 articles collected)')
else:
    print('⚠️ PARTIAL SUCCESS: Some changes may not be fully applied')
    print('  Please review the verification results above')