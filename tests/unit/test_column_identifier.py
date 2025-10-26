"""Unit tests for column identification functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from excel.column_identifier import ColumnIdentifier


class TestColumnIdentifierHeuristics:
    """Test heuristic-based column identification (no Azure AI)."""
    
    def test_identify_standard_columns(self):
        """Test identification of standard Question/Response/Documentation columns."""
        identifier = ColumnIdentifier(azure_client=None)
        headers = ['Status', 'Owner', 'Q#', 'Question', 'Response', 'Documentation']
        
        result = identifier._identify_with_heuristics(headers)
        
        assert result['question'] == 3, "Question column should be at index 3"
        assert result['response'] == 4, "Response column should be at index 4"
        assert result['documentation'] == 5, "Documentation column should be at index 5"
    
    def test_identify_case_insensitive(self):
        """Test that identification is case-insensitive."""
        identifier = ColumnIdentifier(azure_client=None)
        headers = ['status', 'QUESTION', 'answer', 'DOCUMENTATION']
        
        result = identifier._identify_with_heuristics(headers)
        
        assert result['question'] == 1, "Question column should be found case-insensitively"
        assert result['response'] == 2, "Response column should be found (answer is a keyword)"
        assert result['documentation'] == 3, "Documentation column should be found case-insensitively"
    
    def test_identify_abbreviated_columns(self):
        """Test identification of abbreviated column names."""
        identifier = ColumnIdentifier(azure_client=None)
        headers = ['Q', 'A', 'Docs']
        
        result = identifier._identify_with_heuristics(headers)
        
        assert result['question'] == 0, "Q should be identified as question"
        # Note: 'A' alone won't match as we need longer keywords
        assert result['documentation'] == 2, "Docs should be identified as documentation"
    
    def test_identify_missing_columns(self):
        """Test handling when some columns are missing."""
        identifier = ColumnIdentifier(azure_client=None)
        headers = ['Question', 'Response']
        
        result = identifier._identify_with_heuristics(headers)
        
        assert result['question'] == 0
        assert result['response'] == 1
        assert result['documentation'] is None, "Documentation should be None when not found"
    
    def test_identify_no_question_column(self):
        """Test handling when no question column is found."""
        identifier = ColumnIdentifier(azure_client=None)
        headers = ['Status', 'Owner', 'Value']
        
        result = identifier._identify_with_heuristics(headers)
        
        assert result['question'] is None, "Question should be None when not found"
    
    def test_identify_empty_headers(self):
        """Test handling of empty or None headers."""
        identifier = ColumnIdentifier(azure_client=None)
        headers = ['', None, 'Question', 'Response', '']
        
        result = identifier._identify_with_heuristics(headers)
        
        assert result['question'] == 2, "Should handle empty/None headers"
        assert result['response'] == 3


class TestColumnIdentifierValidation:
    """Test column mapping validation."""
    
    def test_validate_valid_mapping(self):
        """Test validation of a valid column mapping."""
        identifier = ColumnIdentifier(azure_client=None)
        mapping = {'question': 3, 'response': 4, 'documentation': 5}
        
        assert identifier._validate_column_mapping(mapping, 6) is True
    
    def test_validate_missing_question(self):
        """Test validation fails when question column is missing."""
        identifier = ColumnIdentifier(azure_client=None)
        mapping = {'question': None, 'response': 4, 'documentation': 5}
        
        assert identifier._validate_column_mapping(mapping, 6) is False
    
    def test_validate_out_of_range(self):
        """Test validation fails when column index is out of range."""
        identifier = ColumnIdentifier(azure_client=None)
        mapping = {'question': 10, 'response': 4, 'documentation': 5}
        
        assert identifier._validate_column_mapping(mapping, 6) is False
    
    def test_validate_negative_index(self):
        """Test validation fails for negative column indices."""
        identifier = ColumnIdentifier(azure_client=None)
        mapping = {'question': -1, 'response': 4, 'documentation': 5}
        
        assert identifier._validate_column_mapping(mapping, 6) is False
    
    def test_validate_duplicate_columns(self):
        """Test validation fails when question and response are the same column."""
        identifier = ColumnIdentifier(azure_client=None)
        mapping = {'question': 3, 'response': 3, 'documentation': 5}
        
        assert identifier._validate_column_mapping(mapping, 6) is False
    
    def test_validate_with_none_documentation(self):
        """Test validation succeeds with None documentation column."""
        identifier = ColumnIdentifier(azure_client=None)
        mapping = {'question': 3, 'response': 4, 'documentation': None}
        
        assert identifier._validate_column_mapping(mapping, 6) is True


class TestColumnIdentifierAI:
    """Test AI-based column identification with mocking."""
    
    @pytest.mark.skip(reason="Requires agent_framework module which may not be installed")
    @pytest.mark.asyncio
    async def test_identify_with_ai_success(self):
        """Test successful AI-based column identification."""
        # Mock Azure client and agent
        mock_client = Mock()
        mock_response = Mock()
        mock_response.messages = [
            Mock(content='{"question": 3, "response": 4, "documentation": 5}')
        ]
        
        # Create mocks for the agent framework imports
        mock_agent = Mock()
        mock_agent.invoke = AsyncMock(return_value=mock_response)
        
        # Patch the imports where they are used (inside the method)
        with patch('agent_framework.ChatAgent', return_value=mock_agent):
            with patch('agent_framework.ChatMessage'):
                with patch('agent_framework.Role'):
                    identifier = ColumnIdentifier(azure_client=mock_client)
                    headers = ['Status', 'Owner', 'Q#', 'Question', 'Response', 'Documentation']
                    
                    result = await identifier._identify_with_ai(headers)
                    
                    assert result['question'] == 3
                    assert result['response'] == 4
                    assert result['documentation'] == 5
    
    @pytest.mark.skip(reason="Requires agent_framework module which may not be installed")
    @pytest.mark.asyncio
    async def test_identify_with_ai_invalid_json(self):
        """Test fallback when AI returns invalid JSON."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.messages = [Mock(content='This is not JSON')]
        
        mock_agent = Mock()
        mock_agent.invoke = AsyncMock(return_value=mock_response)
        
        with patch('agent_framework.ChatAgent', return_value=mock_agent):
            with patch('agent_framework.ChatMessage'):
                with patch('agent_framework.Role'):
                    identifier = ColumnIdentifier(azure_client=mock_client)
                    headers = ['Status', 'Question', 'Response']
                    
                    # Should fall back to heuristics
                    result = await identifier.identify_columns(headers)
                    
                    # Heuristic result should be returned
                    assert result['question'] == 1
                    assert result['response'] == 2
    
    @pytest.mark.asyncio
    async def test_identify_without_ai_client(self):
        """Test that identify_columns works without AI client."""
        identifier = ColumnIdentifier(azure_client=None)
        headers = ['Status', 'Owner', 'Q#', 'Question', 'Response', 'Documentation']
        
        result = await identifier.identify_columns(headers)
        
        # Should use heuristics
        assert result['question'] == 3
        assert result['response'] == 4
        assert result['documentation'] == 5


class TestColumnIdentifierParsing:
    """Test AI response parsing."""
    
    def test_parse_clean_json(self):
        """Test parsing clean JSON response."""
        identifier = ColumnIdentifier(azure_client=None)
        response = '{"question": 3, "response": 4, "documentation": 5}'
        
        result = identifier._parse_ai_response(response)
        
        assert result['question'] == 3
        assert result['response'] == 4
        assert result['documentation'] == 5
    
    def test_parse_json_with_text(self):
        """Test parsing JSON embedded in text."""
        identifier = ColumnIdentifier(azure_client=None)
        response = 'Based on the headers, here is the mapping: {"question": 3, "response": 4, "documentation": null}'
        
        result = identifier._parse_ai_response(response)
        
        assert result['question'] == 3
        assert result['response'] == 4
        assert result['documentation'] is None
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns default."""
        identifier = ColumnIdentifier(azure_client=None)
        response = 'This is not JSON at all'
        
        result = identifier._parse_ai_response(response)
        
        assert result['question'] is None
        assert result['response'] is None
        assert result['documentation'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
