"""Unit tests for Question Answerer agent functionality."""

import pytest
from src.agents.question_answerer import QuestionAnswererExecutor


class TestQuestionAnswererURLSeparation:
    """Test URL separation at the agent level."""
    
    def test_remove_urls_from_answer_with_trailing_urls(self):
        """Test that URLs at the end of answer are removed by the agent."""
        # Create executor (no Azure client needed for this unit test)
        executor = QuestionAnswererExecutor.__new__(QuestionAnswererExecutor)
        
        # Arrange
        answer_with_urls = """Azure AI's text-to-speech service, part of Azure Speech, currently supports over 140 languages and locales as of mid-2024. The service offers a wide array of neural and standard voices, enabling developers to convert text to lifelike speech in numerous languages including major world languages such as English, Spanish, Chinese, French, Arabic, Russian, Hindi, Portuguese, Japanese, German, and many others.

https://learn.microsoft.com/azure/ai-services/speech-service/language-support#text-to-speech
https://learn.microsoft.com/azure/ai-services/speech-service/language-support"""
        
        # Act
        clean_answer = executor._remove_urls_from_answer(answer_with_urls)
        
        # Assert
        assert "https://" not in clean_answer, "URLs should be removed from answer content"
        assert "Azure AI's text-to-speech service" in clean_answer, "Answer content should be preserved"
        assert clean_answer.endswith("and many others."), "Answer should end with the prose, not URLs"
    
    def test_remove_urls_preserves_embedded_urls(self):
        """Test that URLs embedded in prose are preserved (only trailing URL-only lines are removed)."""
        # Create executor
        executor = QuestionAnswererExecutor.__new__(QuestionAnswererExecutor)
        
        # Arrange - URL mentioned in the middle of prose
        answer_with_embedded_url = """Azure AI services are documented at https://learn.microsoft.com/azure/ai and include various capabilities."""
        
        # Act
        clean_answer = executor._remove_urls_from_answer(answer_with_embedded_url)
        
        # Assert - Embedded URL should be preserved
        assert clean_answer == answer_with_embedded_url, "Embedded URLs in prose should be preserved"
    
    def test_remove_urls_from_answer_no_urls(self):
        """Test that answer without URLs is returned unchanged."""
        # Create executor
        executor = QuestionAnswererExecutor.__new__(QuestionAnswererExecutor)
        
        # Arrange
        answer_without_urls = "Azure AI provides comprehensive services for natural language processing."
        
        # Act
        clean_answer = executor._remove_urls_from_answer(answer_without_urls)
        
        # Assert
        assert clean_answer == answer_without_urls, "Answer without URLs should be unchanged"
    
    def test_remove_urls_handles_multiple_trailing_urls(self):
        """Test that multiple trailing URLs are all removed."""
        # Create executor
        executor = QuestionAnswererExecutor.__new__(QuestionAnswererExecutor)
        
        # Arrange
        answer_with_multiple_urls = """Azure Cognitive Services provide AI capabilities.

https://docs.microsoft.com/azure/cognitive-services
https://learn.microsoft.com/azure/ai-services
https://azure.microsoft.com/services/cognitive-services"""
        
        # Act
        clean_answer = executor._remove_urls_from_answer(answer_with_multiple_urls)
        
        # Assert
        assert "https://" not in clean_answer, "All trailing URLs should be removed"
        assert "Azure Cognitive Services provide AI capabilities." in clean_answer
        assert clean_answer.strip().endswith("capabilities."), "Answer should end with prose"
    
    def test_extract_sources_from_answer(self):
        """Test that URLs are correctly extracted from answer content."""
        # Create executor
        executor = QuestionAnswererExecutor.__new__(QuestionAnswererExecutor)
        
        # Arrange
        answer_with_urls = """Azure AI provides services.

https://learn.microsoft.com/azure/ai-services/speech-service/language-support#text-to-speech
https://learn.microsoft.com/azure/ai-services/speech-service/language-support"""
        
        # Act
        sources = executor._extract_sources(answer_with_urls)
        
        # Assert
        assert len(sources) == 2, "Should extract 2 URLs"
        assert "https://learn.microsoft.com/azure/ai-services/speech-service/language-support#text-to-speech" in sources
        assert "https://learn.microsoft.com/azure/ai-services/speech-service/language-support" in sources
    
    def test_url_separation_integration(self):
        """Test that URL extraction and removal work together correctly."""
        # Create executor
        executor = QuestionAnswererExecutor.__new__(QuestionAnswererExecutor)
        
        # Arrange - Full answer with URLs at the end
        full_answer = """Azure AI's text-to-speech service supports over 140 languages.

https://example.com/doc1
https://example.com/doc2"""
        
        # Act
        sources = executor._extract_sources(full_answer)
        clean_answer = executor._remove_urls_from_answer(full_answer)
        
        # Assert
        assert len(sources) == 2, "Should extract 2 sources"
        assert "https://" not in clean_answer, "Clean answer should not contain URLs"
        assert clean_answer.strip().endswith("languages."), "Clean answer should end with prose"
        assert all("example.com" in source for source in sources), "All sources should be extracted"
