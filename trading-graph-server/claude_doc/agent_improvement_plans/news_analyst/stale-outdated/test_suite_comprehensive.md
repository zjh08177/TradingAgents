# Comprehensive Test Suite for News Analyst Pure Data Collection

## Test Strategy Overview

### Test Pyramid
```
         E2E Tests (10%)
        /           \
    Integration (30%)
   /                 \
Unit Tests (60%)
```

### Coverage Goals
- **Line Coverage**: >95%
- **Branch Coverage**: >90%
- **Integration Coverage**: All API combinations
- **Error Scenarios**: All failure modes

## 1. Unit Tests

### Test File: `tests/unit/test_news_data_structure.py`

```python
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

class TestDataStructure:
    """Test data structure consistency"""
    
    def test_serper_article_structure(self):
        """Test Serper article has required fields"""
        article = {
            "title": "Test Article",
            "source": "Reuters",
            "date": "2024-01-14",
            "link": "https://example.com",
            "snippet": "Full content here"
        }
        
        # Transform to internal structure
        result = transform_serper_article(article, index=1)
        
        assert result["index"] == 1
        assert result["api_source"] == "serper"
        assert result["title"] == "Test Article"
        assert result["source"] == "Reuters"
        assert result["full_content"] == "Full content here"
        assert "metadata" in result
        
    def test_finnhub_article_structure(self):
        """Test Finnhub article transformation"""
        article = {
            "headline": "Financial News",
            "summary": "Complete summary text",
            "source": "Bloomberg",
            "datetime": 1705248000,  # Unix timestamp
            "url": "https://bloomberg.com/1"
        }
        
        result = transform_finnhub_article(article, index=1)
        
        assert result["index"] == 1
        assert result["api_source"] == "finnhub"
        assert result["title"] == "Financial News"
        assert result["full_content"] == "Complete summary text"
        assert result["date"] == "2024-01-14"  # Converted from timestamp
        
    def test_no_content_truncation(self):
        """Verify content is never truncated"""
        long_content = "A" * 10000  # 10K characters
        
        article = {
            "title": "Test",
            "snippet": long_content
        }
        
        result = transform_serper_article(article, index=1)
        
        assert len(result["full_content"]) == 10000
        assert result["full_content"] == long_content
        
    def test_missing_fields_handling(self):
        """Test handling of missing fields"""
        article = {"title": "Only Title"}
        
        result = transform_serper_article(article, index=1)
        
        assert result["title"] == "Only Title"
        assert result["source"] == ""
        assert result["date"] == ""
        assert result["url"] == ""
        assert result["full_content"] == ""
```

### Test File: `tests/unit/test_source_classification.py`

```python
class TestSourceClassification:
    """Test news source tier classification"""
    
    @pytest.mark.parametrize("source,expected_tier", [
        ("Reuters", "tier1"),
        ("reuters.com", "tier1"),
        ("Bloomberg", "tier1"),
        ("Wall Street Journal", "tier1"),
        ("WSJ", "tier1"),
        ("Financial Times", "tier1"),
        ("CNBC", "tier2"),
        ("MarketWatch", "tier2"),
        ("Forbes", "tier2"),
        ("Yahoo Finance", "tier2"),
        ("Barron's", "tier2"),
        ("Seeking Alpha", "tier3"),
        ("Motley Fool", "tier3"),
        ("InvestorPlace", "tier3"),
        ("Unknown Blog", "tier4"),
        ("", "tier4"),
    ])
    def test_source_tier_classification(self, source, expected_tier):
        """Test correct tier assignment"""
        assert classify_source_tier(source) == expected_tier
        
    def test_case_insensitive_classification(self):
        """Test classification is case-insensitive"""
        assert classify_source_tier("REUTERS") == "tier1"
        assert classify_source_tier("cnbc") == "tier2"
        assert classify_source_tier("SeEkInG aLpHa") == "tier3"
```

### Test File: `tests/unit/test_report_generation.py`

```python
class TestReportGeneration:
    """Test pure data report generation"""
    
    def test_report_has_no_analysis(self):
        """Verify report contains no analysis"""
        news_data = {
            "serper_articles": [{"title": "Article 1"}],
            "finnhub_articles": [],
            "data_fetch_time": 1.5
        }
        
        report = generate_news_report("AAPL", news_data, "2024-01-14")
        
        # Should NOT contain
        assert "TLDR" not in report
        assert "Sentiment" not in report
        assert "Impact" not in report
        assert "Keywords" not in report
        assert "Trading Signal" not in report
        assert "Recommendation" not in report
        
        # Should contain
        assert "NEWS DATA COLLECTION" in report
        assert "STRUCTURED DATA" in report
        assert "```json" in report
        
    def test_all_articles_included(self):
        """Test all articles appear in report"""
        serper = [{"title": f"S{i}"} for i in range(45)]
        finnhub = [{"headline": f"F{i}"} for i in range(7)]
        
        news_data = {
            "serper_articles": serper,
            "finnhub_articles": finnhub,
            "data_fetch_time": 2.0
        }
        
        report = generate_news_report("AAPL", news_data, "2024-01-14")
        
        # Check counts
        assert "Total Articles: 52" in report
        assert "Serper: 45 articles" in report
        assert "Finnhub: 7 articles" in report
        
        # Check all titles present
        for i in range(45):
            assert f"S{i}" in report
        for i in range(7):
            assert f"F{i}" in report
            
    def test_valid_json_structure(self):
        """Test JSON structure is valid and complete"""
        news_data = {
            "serper_articles": [
                {"title": "Test", "snippet": "Content"}
            ],
            "finnhub_articles": [],
            "data_fetch_time": 1.0
        }
        
        report = generate_news_report("AAPL", news_data, "2024-01-14")
        
        # Extract JSON
        json_match = re.search(r'```json\n(.*?)\n```', report, re.DOTALL)
        assert json_match
        
        data = json.loads(json_match.group(1))
        
        # Verify structure
        assert data["company"] == "AAPL"
        assert data["date"] == "2024-01-14"
        assert data["total"] == 1
        assert len(data["articles"]) == 1
        
        article = data["articles"][0]
        assert article["index"] == 1
        assert article["api_source"] == "serper"
        assert article["title"] == "Test"
        assert article["full_content"] == "Content"
```

## 2. Integration Tests

### Test File: `tests/integration/test_api_integration.py`

```python
class TestAPIIntegration:
    """Test API integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_serper_pagination(self):
        """Test Serper API pagination"""
        mock_responses = [
            [{"title": f"Page{p}Article{i}"} for i in range(10)]
            for p in range(5)
        ]
        
        with patch('getNewsDataSerperAPIWithPagination') as mock_serper:
            mock_serper.return_value = sum(mock_responses, [])
            
            news_data = await gather_news_data("AAPL", toolkit, time.time())
            
            assert len(news_data["serper_articles"]) == 50
            mock_serper.assert_called_with(
                query_or_company="AAPL",
                max_pages=5,
                config=ANY
            )
    
    @pytest.mark.asyncio
    async def test_finnhub_parsing(self):
        """Test Finnhub response parsing"""
        finnhub_response = """
        Title: Breaking News
        Summary: Important financial update
        Source: Reuters
        Date: 2024-01-14
        URL: https://reuters.com/1
        
        Title: Market Update
        Summary: Stock market analysis
        Source: CNBC
        Date: 2024-01-14
        URL: https://cnbc.com/2
        """
        
        toolkit = Mock()
        toolkit.get_finnhub_news.invoke.return_value = finnhub_response
        
        news_data = await gather_news_data("AAPL", toolkit, time.time())
        
        assert len(news_data["finnhub_articles"]) == 2
        assert news_data["finnhub_articles"][0]["headline"] == "Breaking News"
        
    @pytest.mark.asyncio
    async def test_parallel_api_calls(self):
        """Test APIs called in parallel for performance"""
        async def mock_serper_delay(*args, **kwargs):
            await asyncio.sleep(1)
            return [{"title": "Serper"}] * 10
            
        async def mock_finnhub_delay(*args, **kwargs):
            await asyncio.sleep(1)
            return "Title: Finnhub\nSummary: Test"
        
        with patch('getNewsDataSerperAPIWithPagination', mock_serper_delay):
            with patch.object(toolkit, 'get_finnhub_news.invoke', mock_finnhub_delay):
                start = time.time()
                news_data = await gather_news_data("AAPL", toolkit, start)
                duration = time.time() - start
                
                # Should take ~1s if parallel, ~2s if serial
                assert duration < 1.5, "APIs not called in parallel"
```

### Test File: `tests/integration/test_error_handling.py`

```python
class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_serper_failure_fallback(self):
        """Test fallback when Serper fails"""
        with patch('getNewsDataSerperAPIWithPagination', side_effect=Exception("API Error")):
            toolkit = Mock()
            toolkit.get_finnhub_news.invoke.return_value = "Title: Backup\nSummary: Data"
            
            news_data = await gather_news_data("AAPL", toolkit, time.time())
            
            assert len(news_data["serper_articles"]) == 0
            assert len(news_data["finnhub_articles"]) > 0
            assert news_data["sources_successful"] == 1
            assert news_data["sources_attempted"] == 2
    
    @pytest.mark.asyncio
    async def test_both_apis_fail(self):
        """Test handling when both APIs fail"""
        with patch('getNewsDataSerperAPIWithPagination', side_effect=Exception("Serper Error")):
            toolkit = Mock()
            toolkit.get_finnhub_news.invoke.side_effect = Exception("Finnhub Error")
            
            news_data = await gather_news_data("AAPL", toolkit, time.time())
            
            assert news_data["total_articles"] == 0
            assert news_data["sources_successful"] == 0
            assert news_data["sources_attempted"] == 2
            
    @pytest.mark.asyncio
    async def test_partial_serper_failure(self):
        """Test handling partial page failures"""
        page_responses = [
            [{"title": f"Article{i}"} for i in range(10)],  # Page 1 OK
            Exception("Page 2 Error"),  # Page 2 fails
            [{"title": f"Article{i}"} for i in range(20, 30)],  # Page 3 OK
        ]
        
        call_count = 0
        def mock_serper(*args, **kwargs):
            nonlocal call_count
            response = page_responses[min(call_count, len(page_responses)-1)]
            call_count += 1
            if isinstance(response, Exception):
                raise response
            return response
        
        with patch('getNewsDataSerperAPIWithPagination', side_effect=mock_serper):
            news_data = await gather_news_data("AAPL", toolkit, time.time())
            
            # Should have data from successful pages
            assert 10 <= len(news_data["serper_articles"]) <= 20
```

## 3. End-to-End Tests

### Test File: `tests/e2e/test_complete_flow.py`

```python
class TestCompleteFlow:
    """Test complete news analyst flow"""
    
    @pytest.mark.asyncio
    async def test_full_collection_and_report(self):
        """Test complete flow from API to report"""
        
        # Setup
        toolkit = create_mock_toolkit()
        analyst = create_news_analyst_ultra_fast(None, toolkit)
        
        state = {
            "company_of_interest": "AAPL",
            "trade_date": "2024-01-14"
        }
        
        # Execute
        result = await analyst(state)
        
        # Verify state update
        assert "news_report" in result
        assert "news_messages" in result
        assert result["sender"] == "News Analyst (Ultra-Fast)"
        
        # Verify report
        report = result["news_report"]
        assert len(report) > 10000  # Substantial report
        
        # Extract and verify JSON
        json_match = re.search(r'```json\n(.*?)\n```', report, re.DOTALL)
        assert json_match
        
        data = json.loads(json_match.group(1))
        assert data["company"] == "AAPL"
        assert data["total"] >= 50
        
        # Verify no analysis
        assert "TLDR" not in report
        assert "Sentiment" not in report
        
    @pytest.mark.asyncio
    async def test_performance_requirements(self):
        """Test performance meets requirements"""
        
        toolkit = create_mock_toolkit()
        analyst = create_news_analyst_ultra_fast(None, toolkit)
        
        state = {
            "company_of_interest": "TSLA",
            "trade_date": "2024-01-14"
        }
        
        # Measure performance
        start = time.time()
        result = await analyst(state)
        duration = time.time() - start
        
        # Performance assertions
        assert duration < 6.0, f"Too slow: {duration:.3f}s"
        
        # Data volume assertions
        report = result["news_report"]
        assert "Total Articles: " in report
        
        # Extract count
        match = re.search(r'Total Articles: (\d+)', report)
        assert match
        total = int(match.group(1))
        assert total >= 50, f"Not enough articles: {total}"
```

### Test File: `tests/e2e/test_downstream_compatibility.py`

```python
class TestDownstreamCompatibility:
    """Test compatibility with downstream agents"""
    
    @pytest.mark.asyncio
    async def test_aggregator_can_process_output(self):
        """Test aggregator can process news output"""
        
        # Generate news report
        analyst = create_news_analyst_ultra_fast(None, toolkit)
        result = await analyst(state)
        
        # Simulate aggregator processing
        report = result["news_report"]
        json_match = re.search(r'```json\n(.*?)\n```', report, re.DOTALL)
        assert json_match
        
        data = json.loads(json_match.group(1))
        
        # Verify aggregator can access all needed fields
        for article in data["articles"]:
            assert "title" in article
            assert "source" in article
            assert "full_content" in article
            assert "date" in article
            assert "url" in article
            
            # Content should be complete
            assert len(article["full_content"]) > 0
            
    @pytest.mark.asyncio
    async def test_llm_can_summarize_output(self):
        """Test LLM can process raw data for summarization"""
        
        # Generate report
        result = await analyst(state)
        
        # Extract articles
        json_data = extract_json_from_report(result["news_report"])
        articles = json_data["articles"]
        
        # Simulate LLM summarization prompt
        prompt = f"""
        Summarize these news articles:
        {json.dumps(articles[:5])}
        """
        
        # Verify prompt is reasonable size
        assert len(prompt) < 50000  # Within context window
        
        # Verify articles have content to summarize
        for article in articles[:5]:
            assert len(article["full_content"]) > 50
```

## 4. Performance Tests

### Test File: `tests/performance/test_load.py`

```python
class TestLoadPerformance:
    """Test performance under load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        
        async def run_analyst(company):
            analyst = create_news_analyst_ultra_fast(None, toolkit)
            state = {
                "company_of_interest": company,
                "trade_date": "2024-01-14"
            }
            return await analyst(state)
        
        # Run 5 concurrent analyses
        companies = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        
        start = time.time()
        results = await asyncio.gather(*[run_analyst(c) for c in companies])
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 15.0  # 5 requests in 15s
        
        # All should succeed
        for result in results:
            assert "news_report" in result
            
    @pytest.mark.asyncio
    async def test_large_response_handling(self):
        """Test handling very large API responses"""
        
        # Mock 100 articles
        large_response = [
            {
                "title": f"Article {i}",
                "snippet": "A" * 1000  # 1KB per article
            }
            for i in range(100)
        ]
        
        with patch('getNewsDataSerperAPIWithPagination', return_value=large_response):
            result = await analyst(state)
            
            report = result["news_report"]
            
            # Should handle large data
            assert "Total Articles: 100" in report
            
            # Report should be substantial but not excessive
            assert 50000 < len(report) < 200000
```

## 5. Regression Tests

### Test File: `tests/regression/test_no_analysis.py`

```python
class TestNoAnalysisRegression:
    """Ensure analysis functions don't creep back in"""
    
    def test_no_sentiment_analysis_function(self):
        """Verify sentiment analysis is removed"""
        import news_analyst_ultra_fast
        
        assert not hasattr(news_analyst_ultra_fast, 'analyze_news_sentiment')
        assert not hasattr(news_analyst_ultra_fast, 'analyze_single_article_sentiment')
        
    def test_no_tldr_generation_function(self):
        """Verify TLDR generation is removed"""
        import news_analyst_ultra_fast
        
        assert not hasattr(news_analyst_ultra_fast, 'generate_article_tldr')
        assert not hasattr(news_analyst_ultra_fast, 'generate_tldr')
        
    def test_no_priority_calculation(self):
        """Verify priority calculation is removed"""
        import news_analyst_ultra_fast
        
        assert not hasattr(news_analyst_ultra_fast, 'calculate_headline_priority')
        assert not hasattr(news_analyst_ultra_fast, 'calculate_article_impact')
```

## Test Execution Plan

### Local Development
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src.agent.analysts.news_analyst_ultra_fast --cov-report=html

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

### CI/CD Pipeline
```yaml
name: News Analyst Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Unit Tests
        run: pytest tests/unit/ -v
        
      - name: Integration Tests
        run: pytest tests/integration/ -v
        
      - name: E2E Tests
        run: pytest tests/e2e/ -v
        
      - name: Performance Tests
        run: pytest tests/performance/ -v
        
      - name: Coverage Report
        run: pytest tests/ --cov=src.agent.analysts.news_analyst_ultra_fast --cov-fail-under=95
```

## Test Data Fixtures

### File: `tests/fixtures/mock_data.py`

```python
@pytest.fixture
def mock_serper_articles():
    """Mock Serper API response"""
    return [
        {
            "title": f"Apple Stock Rises on Strong Earnings",
            "source": "Reuters",
            "date": "2024-01-14",
            "link": "https://reuters.com/1",
            "snippet": "Apple Inc reported better than expected quarterly earnings...",
            "position": 1
        },
        # ... more articles
    ]

@pytest.fixture
def mock_finnhub_response():
    """Mock Finnhub API response"""
    return """
    Title: Tech Stocks Rally
    Summary: Technology stocks led market gains...
    Source: Bloomberg
    Date: 2024-01-14
    URL: https://bloomberg.com/1
    """

@pytest.fixture
def mock_toolkit():
    """Mock toolkit with API methods"""
    toolkit = Mock()
    toolkit.config = {"serper_key": "test_key"}
    toolkit.get_finnhub_news = Mock()
    return toolkit
```

## Success Criteria

### All Tests Pass
- ✅ 100% of unit tests pass
- ✅ 100% of integration tests pass
- ✅ 100% of E2E tests pass
- ✅ Performance requirements met

### Coverage Targets
- ✅ Line coverage >95%
- ✅ Branch coverage >90%
- ✅ No uncovered error paths

### Quality Gates
- ✅ No hardcoded analysis
- ✅ Complete data preservation
- ✅ Valid JSON output
- ✅ <6s performance

## Conclusion

This comprehensive test suite ensures:
1. **Pure data collection** without analysis
2. **Complete data preservation** without truncation
3. **Robust error handling** for all failure modes
4. **Performance requirements** are met
5. **Downstream compatibility** is maintained

Total test count: **45+ test cases** across 5 categories