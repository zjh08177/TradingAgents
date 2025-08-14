# News Analyst Pure Data Collection - Atomic Implementation Plan

## Design Review

### Core Architecture Principles
1. **Single Responsibility**: News analyst ONLY collects data
2. **Data Completeness**: Preserve 100% of API response data
3. **No Processing**: Zero analysis, summarization, or filtering
4. **Structured Output**: Consistent JSON format for agent consumption
5. **Performance**: Fast collection with parallel API calls where possible

### Data Flow
```
API Sources → Raw Collection → Structured JSON → Agent Processing
   ↓              ↓                ↓                    ↓
Serper API    No filtering    Consistent format    LLM Analysis
Finnhub API   No truncation   Complete metadata    Intelligent Summary
```

## Atomic Subtasks Breakdown

### Phase 1: Data Collection Enhancement (Day 1)

#### Task 1.1: Update Serper Pagination
**File**: `src/agent/analysts/news_analyst_ultra_fast.py`
**Lines**: 154-158

**Changes**:
```python
# FROM:
max_pages=2  # Line 156

# TO:
max_pages=5  # Comprehensive coverage
```

**Test Plan**:
```python
def test_serper_pagination():
    """Test that Serper fetches 5 pages"""
    # Mock serper API responses
    # Verify 5 API calls made
    # Assert 50 articles returned
    # Check no duplicates
```

---

#### Task 1.2: Fix Data Structure Keys
**File**: `src/agent/analysts/news_analyst_ultra_fast.py`
**Lines**: 162, 225

**Changes**:
```python
# FROM:
news_data["serper_news"] = serper_articles  # Line 162
serper_count = len(news_data["serper_news"])  # Line 225

# TO:
news_data["serper_articles"] = serper_articles
serper_count = len(news_data.get("serper_articles", []))
```

**Test Plan**:
```python
def test_data_structure_keys():
    """Test correct key names in data structure"""
    # Call gather_news_data
    # Assert "serper_articles" key exists
    # Assert "finnhub_articles" key exists (not finnhub_news)
    # Verify data structure matches schema
```

---

#### Task 1.3: Rename Finnhub Key
**File**: `src/agent/analysts/news_analyst_ultra_fast.py`
**Lines**: 198, 226

**Changes**:
```python
# FROM:
news_data["finnhub_news"] = finnhub_articles  # Line 198
finnhub_count = len(news_data["finnhub_news"])  # Line 226

# TO:
news_data["finnhub_articles"] = finnhub_articles
finnhub_count = len(news_data.get("finnhub_articles", []))
```

**Test Plan**:
```python
def test_finnhub_data_structure():
    """Test Finnhub data structure consistency"""
    # Mock finnhub response
    # Verify key is "finnhub_articles"
    # Check article format
```

### Phase 2: Remove Analysis Functions (Day 1)

#### Task 2.1: Delete Sentiment Analysis
**File**: `src/agent/analysts/news_analyst_ultra_fast.py`
**Lines**: 440-515

**Action**: DELETE entire `analyze_news_sentiment()` function

**Test Plan**:
```python
def test_no_sentiment_analysis():
    """Verify sentiment analysis removed"""
    # Import module
    # Assert no analyze_news_sentiment function
    # Verify report has no sentiment section
```

---

#### Task 2.2: Delete Headline Extraction
**File**: `src/agent/analysts/news_analyst_ultra_fast.py`
**Lines**: 306-338

**Action**: DELETE entire `extract_key_headlines()` function

**Test Plan**:
```python
def test_no_headline_extraction():
    """Verify headline extraction removed"""
    # Assert function doesn't exist
    # Check report includes ALL headlines
```

---

#### Task 2.3: Delete Priority Calculation
**File**: `src/agent/analysts/news_analyst_ultra_fast.py`
**Lines**: 341-377

**Action**: DELETE entire `calculate_headline_priority()` function

**Test Plan**:
```python
def test_no_priority_calculation():
    """Verify no priority scoring"""
    # Assert function removed
    # Check articles appear in API order
```

### Phase 3: Implement Pure Data Report (Day 2)

#### Task 3.1: Create New Report Structure
**File**: `src/agent/analysts/news_analyst_ultra_fast.py`
**Lines**: 221-303

**Replace entire `generate_news_report()` with**:
```python
def generate_news_report(company: str, news_data: Dict[str, Any], current_date: str) -> str:
    """Generate pure data collection report"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare structured data
    all_articles = []
    
    # Add Serper articles
    for idx, article in enumerate(news_data.get("serper_articles", [])):
        all_articles.append({
            "index": idx + 1,
            "api_source": "serper",
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "date": article.get("date", ""),
            "url": article.get("link", ""),
            "full_content": article.get("snippet", ""),
            "metadata": {
                "position": article.get("position", 0),
                "image_url": article.get("imageUrl", "")
            }
        })
    
    # Add Finnhub articles
    base_idx = len(news_data.get("serper_articles", []))
    for idx, article in enumerate(news_data.get("finnhub_articles", [])):
        all_articles.append({
            "index": base_idx + idx + 1,
            "api_source": "finnhub",
            "title": article.get("headline", ""),
            "source": article.get("source", "Finnhub"),
            "date": article.get("date", ""),
            "url": article.get("url", ""),
            "full_content": article.get("summary", ""),
            "metadata": {
                "category": article.get("category", ""),
                "id": article.get("id", "")
            }
        })
    
    # Build data-only report
    report = f"""# NEWS DATA COLLECTION - {company}

Generated: {timestamp}
Trade Date: {current_date}

## COLLECTION METRICS
- Total Articles: {len(all_articles)}
- Serper: {len(news_data.get('serper_articles', []))} articles
- Finnhub: {len(news_data.get('finnhub_articles', []))} articles
- Collection Time: {news_data.get('data_fetch_time', 0):.3f}s

## RAW ARTICLE DATA

"""
    
    # Add all articles without processing
    for article in all_articles:
        report += f"""### Article {article['index']}
Title: {article['title']}
Source: {article['source']}
Date: {article['date']}
URL: {article['url']}
Content: {article['full_content']}

"""
    
    # Add JSON for agents
    report += f"""## STRUCTURED DATA

```json
{json.dumps({
    "company": company,
    "date": current_date,
    "total": len(all_articles),
    "articles": all_articles
}, indent=2, default=str)}
```
"""
    
    return report
```

**Test Plan**:
```python
def test_pure_data_report():
    """Test report contains only raw data"""
    # Generate report
    # Assert NO "TLDR" in report
    # Assert NO "Sentiment" in report
    # Assert NO "Impact" in report
    # Assert NO "Keywords" in report
    # Assert HAS "STRUCTURED DATA"
    # Assert HAS valid JSON
    # Verify all articles present
```

---

#### Task 3.2: Add Source Classification
**File**: `src/agent/analysts/news_analyst_ultra_fast.py`
**Add after line 515**:

```python
def classify_source_tier(source: str) -> str:
    """Factual classification of source authority"""
    source_lower = source.lower()
    
    tier_map = {
        "tier1": ["reuters", "bloomberg", "wsj", "wall street journal", "financial times"],
        "tier2": ["cnbc", "marketwatch", "forbes", "yahoo finance", "barron"],
        "tier3": ["seeking alpha", "motley fool", "investorplace"],
    }
    
    for tier, sources in tier_map.items():
        if any(s in source_lower for s in sources):
            return tier
    
    return "tier4"
```

**Test Plan**:
```python
def test_source_classification():
    """Test source tier classification"""
    assert classify_source_tier("Reuters") == "tier1"
    assert classify_source_tier("CNBC") == "tier2"
    assert classify_source_tier("Unknown Blog") == "tier4"
```

### Phase 4: Integration Testing (Day 2)

#### Task 4.1: End-to-End Data Collection Test
**Create**: `tests/test_news_data_collection.py`

```python
import asyncio
import json
from unittest.mock import Mock, patch

async def test_complete_data_collection():
    """Test complete data collection flow"""
    
    # Mock toolkit
    toolkit = Mock()
    toolkit.config = {"serper_key": "test_key"}
    
    # Mock Serper response (50 articles)
    serper_articles = [
        {
            "title": f"Article {i}",
            "source": "Reuters" if i < 10 else "CNBC",
            "date": "2024-01-14",
            "link": f"https://example.com/{i}",
            "snippet": f"Full content of article {i} " * 20  # Long content
        }
        for i in range(50)
    ]
    
    # Mock Finnhub response (10 articles)
    finnhub_response = """
    Title: Finnhub Article 1
    Summary: Complete summary text here
    Source: Financial Times
    Date: 2024-01-14
    URL: https://ft.com/1
    
    Title: Finnhub Article 2
    Summary: Another complete summary
    Source: Bloomberg
    Date: 2024-01-14
    URL: https://bloomberg.com/2
    """
    
    with patch('getNewsDataSerperAPIWithPagination', return_value=serper_articles):
        with patch.object(toolkit, 'get_finnhub_news', return_value=finnhub_response):
            
            # Run collection
            from news_analyst_ultra_fast import create_news_analyst_ultra_fast
            analyst = create_news_analyst_ultra_fast(None, toolkit)
            
            state = {
                "company_of_interest": "AAPL",
                "trade_date": "2024-01-14"
            }
            
            result = await analyst(state)
            
            # Verify report structure
            report = result["news_report"]
            
            # Check metrics
            assert "Total Articles: 60" in report  # 50 + 10
            assert "Serper: 50 articles" in report
            assert "Finnhub: 10 articles" in report
            
            # Check no analysis
            assert "TLDR" not in report
            assert "Sentiment" not in report
            assert "Impact Score" not in report
            
            # Check JSON structure
            json_match = re.search(r'```json\n(.*?)\n```', report, re.DOTALL)
            assert json_match
            
            data = json.loads(json_match.group(1))
            assert data["company"] == "AAPL"
            assert data["total"] == 60
            assert len(data["articles"]) == 60
            
            # Verify article structure
            article = data["articles"][0]
            assert "title" in article
            assert "source" in article
            assert "full_content" in article
            assert len(article["full_content"]) > 100  # Not truncated
            
            print("✅ Complete data collection test passed")

if __name__ == "__main__":
    asyncio.run(test_complete_data_collection())
```

---

#### Task 4.2: Performance Test
**Create**: `tests/test_news_performance.py`

```python
async def test_collection_performance():
    """Test data collection performance"""
    
    start_time = time.time()
    
    # Run collection
    result = await analyst(state)
    
    execution_time = time.time() - start_time
    
    # Performance assertions
    assert execution_time < 6.0, f"Too slow: {execution_time}s"
    
    # Data volume assertions
    report = result["news_report"]
    assert len(report) > 10000, "Report too small"
    
    # Parse JSON
    json_data = extract_json(report)
    assert json_data["total"] >= 50, "Not enough articles"
    
    print(f"✅ Performance test passed: {execution_time:.3f}s for {json_data['total']} articles")
```

---

#### Task 4.3: Error Handling Test
**Create**: `tests/test_news_error_handling.py`

```python
async def test_api_failure_handling():
    """Test handling of API failures"""
    
    # Test Serper failure
    with patch('getNewsDataSerperAPIWithPagination', side_effect=Exception("API Error")):
        result = await analyst(state)
        report = result["news_report"]
        assert "Finnhub" in report  # Should still have Finnhub data
    
    # Test both APIs fail
    with patch('getNewsDataSerperAPIWithPagination', side_effect=Exception("API Error")):
        with patch.object(toolkit, 'get_finnhub_news', side_effect=Exception("API Error")):
            result = await analyst(state)
            report = result["news_report"]
            assert "Total Articles: 0" in report
            assert "NO NEWS DATA AVAILABLE" in report or "Total Articles: 0" in report
```

### Phase 5: Validation & Documentation (Day 3)

#### Task 5.1: Create Integration Guide
**File**: `claude_doc/agent_improvement_plans/news_analyst/integration_guide.md`

Content:
- How downstream agents consume the data
- JSON schema documentation
- Example processing code

---

#### Task 5.2: Create Migration Script
**File**: `scripts/migrate_news_analyst.py`

```python
#!/usr/bin/env python3
"""Migration script to update news analyst to pure data collection"""

import os
import shutil
from datetime import datetime

def backup_original():
    """Backup original file"""
    original = "src/agent/analysts/news_analyst_ultra_fast.py"
    backup = f"{original}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(original, backup)
    print(f"✅ Backed up to {backup}")

def apply_changes():
    """Apply all changes"""
    # Implementation of automated changes
    pass

def run_tests():
    """Run validation tests"""
    os.system("python -m pytest tests/test_news_*.py -v")

if __name__ == "__main__":
    backup_original()
    apply_changes()
    run_tests()
```

---

#### Task 5.3: Create Validation Checklist
**File**: `claude_doc/agent_improvement_plans/news_analyst/validation_checklist.md`

```markdown
# Validation Checklist

## Code Changes
- [ ] Serper pagination increased to 5
- [ ] Data keys renamed (serper_articles, finnhub_articles)
- [ ] Analysis functions removed
- [ ] New report structure implemented
- [ ] Source classification added

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Performance <6s for 50+ articles
- [ ] Error handling works
- [ ] JSON structure valid

## Data Quality
- [ ] 50+ articles collected
- [ ] No content truncation
- [ ] All metadata preserved
- [ ] Consistent structure

## Documentation
- [ ] Integration guide complete
- [ ] Migration script works
- [ ] Examples provided
```

## Success Metrics

### Quantitative
- **Article Count**: ≥50 per analysis
- **Data Completeness**: 100% of API fields preserved
- **Performance**: <6s collection time
- **Report Size**: >10KB (vs current 2KB)
- **Test Coverage**: 100% of new functions

### Qualitative
- **No Analysis**: Zero hardcoded processing
- **Pure Data**: Complete content preservation
- **Clean Structure**: Consistent JSON format
- **Agent Ready**: Easy for LLMs to process

## Risk Mitigation

### Risk 1: Large Report Size
**Mitigation**: Implement streaming if >100 articles

### Risk 2: API Rate Limits
**Mitigation**: Add exponential backoff, use caching

### Risk 3: Breaking Changes
**Mitigation**: Keep backup, gradual rollout

## Timeline

### Day 1 (4 hours)
- Tasks 1.1-1.3: Data collection updates (1 hour)
- Tasks 2.1-2.3: Remove analysis functions (1 hour)
- Task 3.1: New report structure (2 hours)

### Day 2 (4 hours)
- Task 3.2: Source classification (30 min)
- Tasks 4.1-4.3: Integration testing (3.5 hours)

### Day 3 (2 hours)
- Tasks 5.1-5.3: Documentation & validation (2 hours)

## Conclusion

This atomic plan transforms the news analyst into a pure data collector through:
1. **10 atomic tasks** with clear scope
2. **Comprehensive testing** at each step
3. **Zero analysis logic** in final implementation
4. **Complete data preservation** for agent processing

The result is a simpler, more maintainable, and more effective news data collection system.