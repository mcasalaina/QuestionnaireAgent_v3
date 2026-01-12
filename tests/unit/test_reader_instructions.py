"""Unit tests for reader instructions detection in agents."""

import pytest
from unittest.mock import AsyncMock
from src.agents.question_answerer import QuestionAnswererExecutor
from src.agents.answer_checker import AnswerCheckerExecutor
from src.utils.data_types import Question


class TestReaderInstructions:
    """Test that agents prohibit and detect reader instructions/advice."""
    
    def test_question_answerer_instructions_prohibit_reader_instructions(self):
        """Test that Question Answerer instructions prohibit reader instructions."""
        from src.agents.question_answerer import QuestionAnswererExecutor
        import inspect
        
        # Get the source code of the _get_agent method
        source = inspect.getsource(QuestionAnswererExecutor._get_agent)
        
        # Verify the instructions contain prohibitions against reader instructions
        assert "NO READER INSTRUCTIONS" in source
        assert "Always review the latest documentation" in source
        assert "Consult with a sales representative" in source
        assert "factual information" in source.lower()
    
    def test_question_answerer_instructions_prohibit_advice_phrases(self):
        """Test that Question Answerer instructions prohibit advice phrases."""
        from src.agents.question_answerer import QuestionAnswererExecutor
        import inspect
        
        # Get the source code of the _get_agent method
        source = inspect.getsource(QuestionAnswererExecutor._get_agent)
        
        # Verify the instructions mention common advice phrases to avoid
        advice_phrases = [
            "always",
            "be sure to",
            "make sure to",
            "remember to",
            "consider",
            "it is recommended"
        ]
        
        for phrase in advice_phrases:
            assert phrase in source.lower(), f"Phrase '{phrase}' should be mentioned as something to avoid"
    
    def test_answer_checker_instructions_detect_reader_instructions(self):
        """Test that Answer Checker instructions detect reader instructions."""
        from src.agents.answer_checker import AnswerCheckerExecutor
        import inspect
        
        # Get the source code of the _get_agent method
        source = inspect.getsource(AnswerCheckerExecutor._get_agent)
        
        # Verify the instructions contain detection of reader instructions
        assert "NO READER INSTRUCTIONS" in source
        assert "Always review the latest documentation" in source
        assert "Consult with a sales representative" in source
        assert "REJECT" in source
    
    def test_answer_checker_instructions_detect_advice_patterns(self):
        """Test that Answer Checker instructions mention advice patterns to reject."""
        from src.agents.answer_checker import AnswerCheckerExecutor
        import inspect
        
        # Get the source code
        source = inspect.getsource(AnswerCheckerExecutor._get_agent)
        
        # Check for various advice patterns that should be rejected
        patterns = [
            "always",
            "be sure to",
            "make sure to",
            "remember to"
        ]
        
        for pattern in patterns:
            assert pattern in source.lower(), f"Pattern '{pattern}' should be mentioned in Answer Checker instructions"
    
    def test_answer_checker_validation_prompt_checks_reader_instructions(self):
        """Test that Answer Checker validation prompts check for reader instructions."""
        # Create a mock Azure client
        mock_client = AsyncMock()
        
        # Create the executor
        executor = AnswerCheckerExecutor(azure_client=mock_client)
        
        # Create a test question
        question = Question(
            text="What are Azure AI features?",
            context="Microsoft Azure AI",
            char_limit=2000
        )
        
        # Sample answer with reader instructions (the problematic pattern from the issue)
        answer = "Azure AI provides various features. Always review the latest documentation and consult with a sales representative for updates on service SKUs."
        
        # Build the validation prompt
        prompt = executor._build_validation_prompt(question, answer)
        
        # Verify prompt contains reader instructions check
        assert "READER INSTRUCTIONS CHECK" in prompt
        assert "Always review the latest documentation" in prompt
        assert "Consult with a sales representative" in prompt
        assert "REJECT" in prompt
    
    def test_answer_checker_validation_prompt_checks_disclaimer_patterns(self):
        """Test that Answer Checker validation prompts check for disclaimer patterns."""
        # Create a mock Azure client
        mock_client = AsyncMock()
        
        # Create the executor
        executor = AnswerCheckerExecutor(azure_client=mock_client)
        
        # Create a test question
        question = Question(
            text="What are Azure pricing options?",
            context="Microsoft Azure",
            char_limit=2000
        )
        
        # Sample answer
        answer = "Azure offers various pricing tiers."
        
        # Build the validation prompt
        prompt = executor._build_validation_prompt(question, answer)
        
        # Verify prompt checks for disclaimer patterns
        assert "features may change" in prompt or "information changing" in prompt
        assert "additional research" in prompt or "verification" in prompt
    
    def test_answer_checker_validation_prompt_has_factual_only_requirement(self):
        """Test that Answer Checker validation prompts require factual-only content."""
        # Create a mock Azure client
        mock_client = AsyncMock()
        
        # Create the executor
        executor = AnswerCheckerExecutor(azure_client=mock_client)
        
        # Create a test question
        question = Question(
            text="What is Azure?",
            context="Microsoft Azure",
            char_limit=2000
        )
        
        answer = "Azure is a cloud computing platform."
        
        # Build the validation prompt
        prompt = executor._build_validation_prompt(question, answer)
        
        # Verify prompt requires factual-only content
        assert "factual information" in prompt.lower() or "ONLY factual" in prompt
        assert "not advice" in prompt.lower() or "NOT advice" in prompt
    
    def test_answer_checker_instructions_mention_disclaimer_patterns(self):
        """Test that Answer Checker instructions mention disclaimer patterns to reject."""
        from src.agents.answer_checker import AnswerCheckerExecutor
        import inspect
        
        # Get the source code
        source = inspect.getsource(AnswerCheckerExecutor._get_agent)
        
        # Check for disclaimer patterns that should be rejected
        assert "features may change" in source or "information changing" in source
        assert "additional research" in source or "verification" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
