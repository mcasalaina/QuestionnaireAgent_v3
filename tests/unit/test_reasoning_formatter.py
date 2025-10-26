"""Unit tests for reasoning formatter."""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, src_path)

import pytest
from utils.data_types import AgentStep, AgentType, StepStatus
from utils.reasoning_formatter import ReasoningFormatter


def test_format_question_answerer_step():
    """Test formatting of Question Answerer step."""
    step = AgentStep(
        agent_name=AgentType.QUESTION_ANSWERER,
        input_data="How many languages does your text-to-speech service support?",
        output_data="Microsoft Azure's text-to-speech service supports over 70 languages.",
        execution_time=5.2,
        status=StepStatus.SUCCESS
    )
    
    formatted = ReasoningFormatter.format_agent_steps([step])
    
    assert len(formatted) == 1
    agent_name, content, color = formatted[0]
    
    assert agent_name == "Question Answerer"
    assert "Microsoft Azure's text-to-speech service supports over 70 languages" in content
    assert color == "black"


def test_format_answer_checker_approve():
    """Test formatting of Answer Checker APPROVE step."""
    step = AgentStep(
        agent_name=AgentType.ANSWER_CHECKER,
        input_data="Question: ...\nAnswer: ...",
        output_data="APPROVED: The answer is accurate and complete.",
        execution_time=2.1,
        status=StepStatus.SUCCESS
    )
    
    formatted = ReasoningFormatter.format_agent_steps([step])
    
    assert len(formatted) == 1
    agent_name, content, color = formatted[0]
    
    assert agent_name == "Answer Checker"
    assert content == "APPROVE."
    assert color == "green"


def test_format_answer_checker_reject():
    """Test formatting of Answer Checker REJECT step."""
    step = AgentStep(
        agent_name=AgentType.ANSWER_CHECKER,
        input_data="Question: ...\nAnswer: ...",
        output_data="REJECTED: Answer fails to mention OpenAI text-to-speech voices.",
        execution_time=1.8,
        status=StepStatus.SUCCESS
    )
    
    formatted = ReasoningFormatter.format_agent_steps([step])
    
    assert len(formatted) == 1
    agent_name, content, color = formatted[0]
    
    assert agent_name == "Answer Checker"
    assert "REJECT" in content
    assert "Answer fails to mention OpenAI text-to-speech voices" in content
    assert color == "green"


def test_format_link_checker_step():
    """Test formatting of Link Checker step."""
    step = AgentStep(
        agent_name=AgentType.LINK_CHECKER,
        input_data="Links to check: ['https://example.com']",
        output_data="LINKS_VALID: All links are accessible and relevant.",
        execution_time=3.5,
        status=StepStatus.SUCCESS
    )
    
    formatted = ReasoningFormatter.format_agent_steps([step])
    
    assert len(formatted) == 1
    agent_name, content, color = formatted[0]
    
    assert agent_name == "Link Checker"
    assert "LINKS_VALID" in content
    assert color == "blue"


def test_format_multiple_steps():
    """Test formatting of multiple agent steps in conversation."""
    steps = [
        AgentStep(
            agent_name=AgentType.QUESTION_ANSWERER,
            input_data="How many languages?",
            output_data="Over 70 languages are supported.",
            execution_time=5.0,
            status=StepStatus.SUCCESS
        ),
        AgentStep(
            agent_name=AgentType.ANSWER_CHECKER,
            input_data="Question: ...\nAnswer: ...",
            output_data="REJECTED: Missing information about OpenAI voices.",
            execution_time=2.0,
            status=StepStatus.SUCCESS
        ),
        AgentStep(
            agent_name=AgentType.QUESTION_ANSWERER,
            input_data="How many languages?",
            output_data="Over 70 languages and 400 voices from Azure and 12 from OpenAI.",
            execution_time=5.5,
            status=StepStatus.SUCCESS
        ),
        AgentStep(
            agent_name=AgentType.ANSWER_CHECKER,
            input_data="Question: ...\nAnswer: ...",
            output_data="APPROVED: Answer is now complete.",
            execution_time=1.9,
            status=StepStatus.SUCCESS
        )
    ]
    
    formatted = ReasoningFormatter.format_agent_steps(steps)
    
    assert len(formatted) == 4
    
    # Check first step (Question Answerer)
    assert formatted[0][0] == "Question Answerer"
    assert formatted[0][2] == "black"
    
    # Check second step (Answer Checker REJECT)
    assert formatted[1][0] == "Answer Checker"
    assert "REJECT" in formatted[1][1]
    assert formatted[1][2] == "green"
    
    # Check third step (Question Answerer retry)
    assert formatted[2][0] == "Question Answerer"
    assert formatted[2][2] == "black"
    
    # Check fourth step (Answer Checker APPROVE)
    assert formatted[3][0] == "Answer Checker"
    assert formatted[3][1] == "APPROVE."
    assert formatted[3][2] == "green"


def test_empty_steps():
    """Test formatting with empty steps list."""
    formatted = ReasoningFormatter.format_agent_steps([])
    assert formatted == []


def test_step_with_empty_output():
    """Test formatting step with empty output data."""
    step = AgentStep(
        agent_name=AgentType.QUESTION_ANSWERER,
        input_data="Test question",
        output_data="",
        execution_time=1.0,
        status=StepStatus.SUCCESS
    )
    
    formatted = ReasoningFormatter.format_agent_steps([step])
    assert len(formatted) == 0  # Empty output should be skipped
