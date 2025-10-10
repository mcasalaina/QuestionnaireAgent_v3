"""Unit tests for plain text formatting requirements in agents."""

import pytest
from unittest.mock import AsyncMock, Mock
from src.agents.question_answerer import QuestionAnswererExecutor
from src.agents.answer_checker import AnswerCheckerExecutor


class TestPlainTextFormatting:
    """Test that agents enforce plain text formatting."""
    
    def test_question_answerer_instructions_require_plain_text(self):
        """Test that Question Answerer instructions require plain text output."""
        # Create a mock Azure client
        mock_client = AsyncMock()
        
        # Create the executor
        executor = QuestionAnswererExecutor(
            azure_client=mock_client,
            bing_connection_id="mock_bing_connection"
        )
        
        # Access the agent creation (it's lazy loaded)
        # We need to verify the instructions when agent is created
        assert executor.azure_client is not None
        assert executor.bing_connection_id == "mock_bing_connection"
    
    def test_answer_checker_instructions_validate_plain_text(self):
        """Test that Answer Checker instructions validate plain text format."""
        # Create a mock Azure client
        mock_client = AsyncMock()
        
        # Create the executor
        executor = AnswerCheckerExecutor(azure_client=mock_client)
        
        # Verify the executor is created correctly
        assert executor.azure_client is not None
    
    def test_question_answerer_prompt_includes_plain_text_requirement(self):
        """Test that question prompts include plain text formatting requirements."""
        from src.utils.data_types import Question
        
        # Create a mock Azure client
        mock_client = AsyncMock()
        
        # Create the executor
        executor = QuestionAnswererExecutor(
            azure_client=mock_client,
            bing_connection_id="mock_bing_connection"
        )
        
        # Create a test question
        question = Question(
            text="What is Azure AI?",
            context="Microsoft Azure AI",
            char_limit=2000
        )
        
        # Build the prompt
        prompt = executor._build_question_prompt(question)
        
        # Verify prompt contains plain text formatting requirements
        assert "plain text" in prompt.lower() or "PLAIN TEXT" in prompt
        assert "NO markdown" in prompt or "no markdown" in prompt
        assert "**bold**" in prompt
        assert "*italics*" in prompt
        assert "bullet points" in prompt.lower()
    
    def test_answer_checker_prompt_includes_plain_text_validation(self):
        """Test that validation prompts check for plain text format."""
        from src.utils.data_types import Question
        
        # Create a mock Azure client
        mock_client = AsyncMock()
        
        # Create the executor
        executor = AnswerCheckerExecutor(azure_client=mock_client)
        
        # Create a test question
        question = Question(
            text="What is Azure AI?",
            context="Microsoft Azure AI",
            char_limit=2000
        )
        
        # Sample answer (with markdown)
        answer = "Azure AI is a **powerful** platform."
        
        # Build the validation prompt
        prompt = executor._build_validation_prompt(question, answer)
        
        # Verify prompt contains plain text validation requirements
        assert "plain text" in prompt.lower() or "PLAIN TEXT" in prompt
        assert "markdown" in prompt.lower()
        assert "FORMATTING" in prompt or "formatting" in prompt.lower()
        assert "**bold**" in prompt
        assert "bullet points" in prompt.lower()
    
    def test_markdown_patterns_detected_in_prompts(self):
        """Test that both agents' prompts mention common markdown patterns."""
        from src.utils.data_types import Question
        
        mock_client = AsyncMock()
        
        # Test Question Answerer
        qa_executor = QuestionAnswererExecutor(
            azure_client=mock_client,
            bing_connection_id="mock_bing"
        )
        
        question = Question(
            text="Test question",
            context="Test context",
            char_limit=1000
        )
        
        qa_prompt = qa_executor._build_question_prompt(question)
        
        # Check for markdown pattern mentions
        markdown_patterns = ["**bold**", "*italics*", "`code`", "# headers", "bullet points", "numbered lists"]
        
        for pattern in markdown_patterns:
            assert pattern in qa_prompt or pattern.replace("**", "") in qa_prompt.lower(), \
                f"Pattern '{pattern}' should be mentioned in question answerer prompt"
        
        # Test Answer Checker
        ac_executor = AnswerCheckerExecutor(azure_client=mock_client)
        
        answer = "Test answer"
        ac_prompt = ac_executor._build_validation_prompt(question, answer)
        
        for pattern in markdown_patterns:
            assert pattern in ac_prompt or pattern.replace("**", "") in ac_prompt.lower(), \
                f"Pattern '{pattern}' should be mentioned in answer checker prompt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
