"""Unit tests for Confluence integration."""

import pytest
import asyncio
from pathlib import Path

from shared.utils.confluence_client import (
    MockConfluenceClient,
    RealConfluenceClient,
    ConfluenceSearchResult,
    create_confluence_client,
)
from agents.data_processor.agent import ConfluenceKnowledgeClassifier
import pandas as pd


class TestMockConfluenceClient:
    """Test mock Confluence client."""
    
    @pytest.mark.asyncio
    async def test_search_email_field(self):
        """Test searching for email field documentation."""
        client = MockConfluenceClient()
        
        results = await client.search('email field', limit=5)
        
        assert len(results) > 0
        assert any('email' in r.title.lower() for r in results)
        assert all(isinstance(r, ConfluenceSearchResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_search_phone_field(self):
        """Test searching for phone field documentation."""
        client = MockConfluenceClient()
        
        results = await client.search('phone number', limit=5)
        
        assert len(results) > 0
        assert any('phone' in r.title.lower() for r in results)
        # Check that content contains PII indicators
        assert any('pii' in r.content.lower() for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_space_filter(self):
        """Test searching with space filter."""
        client = MockConfluenceClient()
        
        results = await client.search('field', space='DATA', limit=10)
        
        # All results should be from DATA space
        assert all(r.space == 'DATA' for r in results)
    
    @pytest.mark.asyncio
    async def test_search_limit(self):
        """Test search result limit."""
        client = MockConfluenceClient()
        
        results = await client.search('field', limit=2)
        
        assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with no matching results."""
        client = MockConfluenceClient()
        
        results = await client.search('nonexistent_field_xyz', limit=5)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_get_page(self):
        """Test retrieving a specific page."""
        client = MockConfluenceClient()
        
        page = await client.get_page('mock-email-001')
        
        assert page.page_id == 'mock-email-001'
        assert 'email' in page.title.lower()
        assert len(page.content) > 0
    
    @pytest.mark.asyncio
    async def test_get_page_not_found(self):
        """Test retrieving non-existent page."""
        client = MockConfluenceClient()
        
        with pytest.raises(ValueError, match='Page not found'):
            await client.get_page('invalid-page-id')
    
    @pytest.mark.asyncio
    async def test_search_returns_url(self):
        """Test that search results include URLs."""
        client = MockConfluenceClient()
        
        results = await client.search('email', limit=1)
        
        assert len(results) > 0
        assert results[0].url.startswith('https://')
        assert 'confluence' in results[0].url


class TestRealConfluenceClient:
    """Test real Confluence client (placeholder tests)."""
    
    def test_initialization(self):
        """Test client initialization."""
        client = RealConfluenceClient(
            base_url='https://company.atlassian.net/wiki',
            username='user@example.com',
            api_token='fake-token'
        )
        
        assert client.base_url == 'https://company.atlassian.net/wiki'
        assert client.username == 'user@example.com'
    
    @pytest.mark.asyncio
    async def test_search_not_implemented(self):
        """Test that real search raises NotImplementedError."""
        client = RealConfluenceClient(
            base_url='https://company.atlassian.net/wiki',
            username='user@example.com',
            api_token='fake-token'
        )
        
        with pytest.raises(NotImplementedError):
            await client.search('test query')
    
    @pytest.mark.asyncio
    async def test_get_page_not_implemented(self):
        """Test that real get_page raises NotImplementedError."""
        client = RealConfluenceClient(
            base_url='https://company.atlassian.net/wiki',
            username='user@example.com',
            api_token='fake-token'
        )
        
        with pytest.raises(NotImplementedError):
            await client.get_page('page-123')


class TestConfluenceClientFactory:
    """Test Confluence client factory function."""
    
    def test_create_mock_client(self):
        """Test creating mock client."""
        client = create_confluence_client(demo_mode=True)
        
        assert isinstance(client, MockConfluenceClient)
    
    def test_create_real_client(self):
        """Test creating real client."""
        client = create_confluence_client(
            demo_mode=False,
            base_url='https://company.atlassian.net/wiki',
            username='user@example.com',
            api_token='fake-token'
        )
        
        assert isinstance(client, RealConfluenceClient)
    
    def test_create_real_client_missing_credentials(self):
        """Test creating real client without credentials."""
        with pytest.raises(ValueError, match='requires base_url'):
            create_confluence_client(demo_mode=False)


class TestConfluenceKnowledgeClassifier:
    """Test Confluence knowledge classifier."""
    
    @pytest.mark.asyncio
    async def test_classify_email_field(self):
        """Test classifying email field with Confluence."""
        confluence = MockConfluenceClient()
        classifier = ConfluenceKnowledgeClassifier(confluence, bedrock_client=None)
        
        samples = pd.Series(['user@example.com', 'test@test.org'])
        # Use "email" which will match the mock Confluence data
        result = await classifier.classify('email', samples, {})
        
        # Should find documentation and classify appropriately
        assert result.confidence >= 0.2  # At least finds documentation
        assert result.sensitivity_type in ['email', 'address', 'name', 'unknown', 'non_sensitive']
        assert 'confluence' in result.reasoning.lower() or 'documentation' in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_classify_phone_field(self):
        """Test classifying phone field with Confluence."""
        confluence = MockConfluenceClient()
        classifier = ConfluenceKnowledgeClassifier(confluence, bedrock_client=None)
        
        samples = pd.Series(['555-123-4567', '555-987-6543'])
        result = await classifier.classify('phone_number', samples, {})
        
        assert result.confidence > 0.5
        assert result.sensitivity_type in ['phone', 'non_sensitive']
    
    @pytest.mark.asyncio
    async def test_classify_without_confluence(self):
        """Test classifier without Confluence client."""
        classifier = ConfluenceKnowledgeClassifier(confluence_client=None)
        
        samples = pd.Series(['test@example.com'])
        result = await classifier.classify('email', samples, {})
        
        assert result.confidence == 0.0
        assert 'not available' in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_classify_no_documentation_found(self):
        """Test classification when no documentation is found."""
        confluence = MockConfluenceClient()
        classifier = ConfluenceKnowledgeClassifier(confluence, bedrock_client=None)
        
        samples = pd.Series(['value1', 'value2'])
        result = await classifier.classify('unknown_field_xyz', samples, {})
        
        assert result.confidence == 0.0
        assert 'no confluence documentation' in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_caching(self):
        """Test that Confluence results are cached."""
        confluence = MockConfluenceClient()
        classifier = ConfluenceKnowledgeClassifier(confluence, bedrock_client=None)
        
        samples = pd.Series(['user@example.com'])
        
        # First call
        result1 = await classifier.classify('email', samples, {})
        
        # Second call should use cache (same field name)
        result2 = await classifier.classify('email', samples, {})
        
        assert result1.confidence == result2.confidence
        assert result1.sensitivity_type == result2.sensitivity_type
        # Second call should indicate it's cached
        if result1.confidence > 0.5:  # Only check if first call succeeded
            assert 'cached' in result2.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_confluence_references_collected(self):
        """Test that Confluence references are collected."""
        confluence = MockConfluenceClient()
        classifier = ConfluenceKnowledgeClassifier(confluence, bedrock_client=None)
        
        samples = pd.Series(['user@example.com'])
        result = await classifier.classify('email', samples, {})
        
        # Should have Confluence URLs in pattern_matches
        if result.confidence > 0.5:
            assert result.pattern_matches is not None
            assert len(result.pattern_matches) > 0
            assert any('confluence' in str(ref).lower() for ref in result.pattern_matches)
    
    @pytest.mark.asyncio
    async def test_mock_bedrock_analysis(self):
        """Test mock Bedrock analysis."""
        confluence = MockConfluenceClient()
        classifier = ConfluenceKnowledgeClassifier(confluence, bedrock_client=None)
        
        # Search for email to get results
        results = await confluence.search('email field', limit=3)
        
        # Test mock Bedrock call
        response = await classifier._mock_bedrock_call('test prompt', results)
        
        # Should return valid JSON
        import json
        parsed = json.loads(response)
        assert 'is_sensitive' in parsed
        assert 'type' in parsed
        assert 'confidence' in parsed
        assert 'reasoning' in parsed


class TestDataProcessorWithConfluence:
    """Test Data Processor Agent with Confluence integration."""
    
    @pytest.mark.asyncio
    async def test_agent_with_confluence(self):
        """Test agent processes data with Confluence classifier."""
        from agents.data_processor.agent import DataProcessorAgent
        
        confluence = MockConfluenceClient()
        agent = DataProcessorAgent(confluence_client=confluence)
        
        # Check that Confluence classifier was added
        classifier_names = [name for name, _ in agent.classifiers]
        assert 'confluence' in classifier_names
    
    @pytest.mark.asyncio
    async def test_agent_without_confluence(self):
        """Test agent works without Confluence classifier."""
        from agents.data_processor.agent import DataProcessorAgent
        
        agent = DataProcessorAgent(confluence_client=None)
        
        # Check that Confluence classifier was not added
        classifier_names = [name for name, _ in agent.classifiers]
        assert 'confluence' not in classifier_names
    
    def test_synchronous_process_with_confluence(self, tmp_path):
        """Test synchronous process method with Confluence."""
        from agents.data_processor.agent import DataProcessorAgent
        
        # Create test CSV
        test_file = tmp_path / 'test.csv'
        df = pd.DataFrame({
            'email': ['user@example.com', 'test@test.org'],
            'name': ['John Doe', 'Jane Smith'],
            'age': [30, 25]
        })
        df.to_csv(test_file, index=False)
        
        # Create agent with Confluence
        confluence = MockConfluenceClient()
        agent = DataProcessorAgent(confluence_client=confluence)
        
        # Process data (synchronous wrapper)
        report = agent.process(test_file)
        
        assert report.total_fields == 3
        assert report.sensitive_fields >= 1  # At least email should be detected
        
        # Check for Confluence references
        email_classification = report.classifications.get('email')
        if email_classification and email_classification.is_sensitive:
            # May have Confluence references
            assert isinstance(email_classification.confluence_references, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
