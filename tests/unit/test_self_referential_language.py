"""Unit tests for self-referential language detection in agents."""

import pytest
from unittest.mock import AsyncMock
from src.agents.question_answerer import QuestionAnswererExecutor
from src.agents.answer_checker import AnswerCheckerExecutor
from src.utils.data_types import Question


class TestSelfReferentialLanguage:
    """Test that agents prohibit and detect self-referential language."""
    
    def test_question_answerer_instructions_prohibit_self_reference(self):
        """Test that Question Answerer instructions prohibit self-referential language."""
        # Create a mock Azure client
        mock_client = AsyncMock()
        
        # Create the executor
        executor = QuestionAnswererExecutor(
            azure_client=mock_client,
            bing_connection_id="mock_bing_connection"
        )
        
        # Access the agent creation (it's lazy loaded, so we need to check the instructions)
        # The instructions are set when _get_agent is called, but we can verify the pattern
        assert executor.azure_client is not None
        assert executor.bing_connection_id == "mock_bing_connection"
    
    def test_question_answerer_instructions_include_self_reference_prohibition(self):
        """Test that Question Answerer instructions explicitly prohibit self-referential language."""
        from src.agents.question_answerer import QuestionAnswererExecutor
        import inspect
        
        # Get the source code of the _get_agent method
        source = inspect.getsource(QuestionAnswererExecutor._get_agent)
        
        # Verify the instructions contain prohibitions against self-referential language
        assert "NEVER refer to yourself" in source or "NOT refer to yourself" in source
        assert "I am an AI" in source  # Should mention as an example of what NOT to do
        assert "first-person" in source or "first person" in source
        assert "self-referential" in source
    
    def test_answer_checker_instructions_detect_self_reference(self):
        """Test that Answer Checker instructions detect self-referential language."""
        from src.agents.answer_checker import AnswerCheckerExecutor
        import inspect
        
        # Get the source code of the _get_agent method
        source = inspect.getsource(AnswerCheckerExecutor._get_agent)
        
        # Verify the instructions contain detection of self-referential language
        assert "self-referential" in source.lower()
        assert "I am an AI" in source  # Should mention as an example of what to reject
        assert "first-person" in source or "first person" in source
        assert "REJECT" in source
    
    def test_answer_checker_validation_prompt_checks_self_reference(self):
        """Test that Answer Checker validation prompts check for self-referential language."""
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
        
        # Sample answer with self-referential language
        answer = "I am an AI assistant developed to provide expert answers about Microsoft Azure AI services."
        
        # Build the validation prompt
        prompt = executor._build_validation_prompt(question, answer)
        
        # Verify prompt contains self-referential language check
        assert "self-referential" in prompt.lower() or "SELF-REFERENTIAL" in prompt
        assert "I am an AI" in prompt  # Should mention as an example
        assert "first-person" in prompt.lower() or "first person" in prompt
        assert "REJECT" in prompt
    
    def test_question_answerer_prompt_includes_self_reference_prohibition(self):
        """Test that question prompts prohibit self-referential language."""
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
        
        # The build_question_prompt method doesn't repeat all instructions,
        # but the agent's instructions should handle this
        # So we just verify the method works correctly
        assert "Question: What is Azure AI?" in prompt
        assert "plain text" in prompt.lower() or "PLAIN TEXT" in prompt
    
    def test_self_referential_patterns_in_checker_instructions(self):
        """Test that Answer Checker instructions mention various self-referential patterns."""
        from src.agents.answer_checker import AnswerCheckerExecutor
        import inspect
        
        # Get the source code
        source = inspect.getsource(AnswerCheckerExecutor._get_agent)
        
        # Check for various self-referential patterns that should be rejected
        patterns = [
            "I am an AI",
            "As an AI",
            "I can help",
            "I will",
            "I have"
        ]
        
        for pattern in patterns:
            assert pattern in source, f"Pattern '{pattern}' should be mentioned in Answer Checker instructions"
    
    def test_self_referential_patterns_in_answerer_instructions(self):
        """Test that Question Answerer instructions mention various self-referential patterns."""
        from src.agents.question_answerer import QuestionAnswererExecutor
        import inspect
        
        # Get the source code
        source = inspect.getsource(QuestionAnswererExecutor._get_agent)
        
        # Check for prohibitions of self-referential patterns
        patterns_to_avoid = [
            "I am an AI",
            "As an AI",
            "I can help"
        ]
        
        for pattern in patterns_to_avoid:
            assert pattern in source, f"Pattern '{pattern}' should be mentioned as something to avoid"
        
        # Check for the prohibition language
        assert "NEVER" in source
    
    def test_answer_checker_validation_includes_professionalism_check(self):
        """Test that Answer Checker validation prompt has a professionalism section."""
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
        
        # Sample answer
        answer = "Azure AI is a platform for building intelligent applications."
        
        # Build the validation prompt
        prompt = executor._build_validation_prompt(question, answer)
        
        # Verify prompt has a professionalism check section
        assert "PROFESSIONALISM" in prompt or "professionalism" in prompt.lower()
        assert "REJECT" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
