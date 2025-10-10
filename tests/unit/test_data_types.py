"""Unit tests for data type validation and functionality."""

import pytest
from datetime import datetime
from src.utils.data_types import (
    Question, Answer, AgentStep, DocumentationLink, ProcessingResult,
    AgentType, ValidationStatus, StepStatus, ProcessingStatus
)


class TestQuestion:
    """Test Question data validation."""
    
    def test_valid_question_creation(self):
        """Test creating a valid question."""
        question = Question(
            text="What is Azure AI?",
            context="Microsoft Azure AI",
            char_limit=2000,
            max_retries=10
        )
        
        assert question.text == "What is Azure AI?"
        assert question.context == "Microsoft Azure AI"
        assert question.char_limit == 2000
        assert question.max_retries == 10
        assert question.id is None
    
    def test_question_with_id(self):
        """Test creating a question with ID."""
        question = Question(
            text="How does Azure OpenAI work?",
            id="Q001"
        )
        
        assert question.id == "Q001"
        assert question.context == "Microsoft Azure AI"  # Default value
    
    def test_question_text_too_short(self):
        """Test validation fails for short question text."""
        with pytest.raises(ValueError, match="Question text must be at least 5 characters"):
            Question(text="Hi?")
    
    def test_question_empty_text(self):
        """Test validation fails for empty question text."""
        with pytest.raises(ValueError, match="Question text must be at least 5 characters"):
            Question(text="")
    
    def test_question_whitespace_only_text(self):
        """Test validation fails for whitespace-only text."""
        with pytest.raises(ValueError, match="Question text must be at least 5 characters"):
            Question(text="   ")
    
    def test_char_limit_too_low(self):
        """Test validation fails for char limit below minimum."""
        with pytest.raises(ValueError, match="Character limit must be between 100 and 10000"):
            Question(text="Valid question text", char_limit=50)
    
    def test_char_limit_too_high(self):
        """Test validation fails for char limit above maximum."""
        with pytest.raises(ValueError, match="Character limit must be between 100 and 10000"):
            Question(text="Valid question text", char_limit=15000)
    
    def test_max_retries_too_low(self):
        """Test validation fails for max retries below minimum."""
        with pytest.raises(ValueError, match="Max retries must be between 1 and 25"):
            Question(text="Valid question text", max_retries=0)
    
    def test_max_retries_too_high(self):
        """Test validation fails for max retries above maximum."""
        with pytest.raises(ValueError, match="Max retries must be between 1 and 25"):
            Question(text="Valid question text", max_retries=30)


class TestAgentStep:
    """Test AgentStep data validation."""
    
    def test_valid_agent_step(self):
        """Test creating a valid agent step."""
        step = AgentStep(
            agent_name=AgentType.QUESTION_ANSWERER,
            input_data="What is Azure AI?",
            output_data="Azure AI is Microsoft's artificial intelligence platform...",
            execution_time=2.5,
            status=StepStatus.SUCCESS
        )
        
        assert step.agent_name == AgentType.QUESTION_ANSWERER
        assert step.execution_time == 2.5
        assert step.status == StepStatus.SUCCESS
        assert step.error_message is None
        assert isinstance(step.timestamp, datetime)
    
    def test_agent_step_with_error(self):
        """Test creating an agent step with error."""
        step = AgentStep(
            agent_name=AgentType.ANSWER_CHECKER,
            input_data="Test input",
            output_data="",
            execution_time=1.0,
            status=StepStatus.FAILURE,
            error_message="Network timeout occurred"
        )
        
        assert step.status == StepStatus.FAILURE
        assert step.error_message == "Network timeout occurred"
    
    def test_negative_execution_time(self):
        """Test validation fails for negative execution time."""
        with pytest.raises(ValueError, match="Execution time must be positive"):
            AgentStep(
                agent_name=AgentType.LINK_CHECKER,
                input_data="Test",
                output_data="Test",
                execution_time=-1.0,
                status=StepStatus.SUCCESS
            )
    
    def test_failure_status_without_error_message(self):
        """Test validation fails for failure status without error message."""
        with pytest.raises(ValueError, match="Error message required when status is FAILURE"):
            AgentStep(
                agent_name=AgentType.QUESTION_ANSWERER,
                input_data="Test",
                output_data="Test",
                execution_time=1.0,
                status=StepStatus.FAILURE
            )


class TestDocumentationLink:
    """Test DocumentationLink validation."""
    
    def test_valid_http_link(self):
        """Test creating a valid HTTP link."""
        link = DocumentationLink(
            url="http://docs.microsoft.com/azure/ai",
            title="Azure AI Documentation",
            is_reachable=True,
            is_relevant=True,
            http_status=200
        )
        
        assert link.url.startswith("http://")
        assert link.is_valid is True
    
    def test_valid_https_link(self):
        """Test creating a valid HTTPS link."""
        link = DocumentationLink(
            url="https://docs.microsoft.com/azure/ai",
            title="Azure AI Documentation",
            is_reachable=True,
            is_relevant=True,
            http_status=200
        )
        
        assert link.url.startswith("https://")
        assert link.is_valid is True
    
    def test_invalid_url_format(self):
        """Test validation fails for invalid URL format."""
        with pytest.raises(ValueError, match="URL must be a valid HTTP/HTTPS format"):
            DocumentationLink(url="ftp://example.com/doc")
    
    def test_link_not_reachable(self):
        """Test link marked as invalid when not reachable."""
        link = DocumentationLink(
            url="https://broken-link.example.com",
            is_reachable=False,
            is_relevant=True
        )
        
        assert link.is_valid is False
    
    def test_link_not_relevant(self):
        """Test link marked as invalid when not relevant."""
        link = DocumentationLink(
            url="https://docs.microsoft.com/unrelated",
            is_reachable=True,
            is_relevant=False
        )
        
        assert link.is_valid is False


class TestAnswer:
    """Test Answer data validation and functionality."""
    
    def test_answer_creation(self):
        """Test creating an answer."""
        answer = Answer(
            content="Azure AI is Microsoft's comprehensive artificial intelligence platform.",
            sources=["https://docs.microsoft.com/azure/ai"],
            validation_status=ValidationStatus.APPROVED,
            retry_count=1
        )
        
        assert len(answer.content) == answer.char_count
        assert answer.is_approved is True
        assert len(answer.sources) == 1
    
    def test_answer_not_approved(self):
        """Test answer not approved when status is pending."""
        answer = Answer(
            content="Test content",
            validation_status=ValidationStatus.PENDING
        )
        
        assert answer.is_approved is False
    
    def test_valid_links_filtering(self):
        """Test filtering of valid documentation links."""
        valid_link = DocumentationLink(
            url="https://docs.microsoft.com/valid",
            is_reachable=True,
            is_relevant=True
        )
        invalid_link = DocumentationLink(
            url="https://broken.example.com",
            is_reachable=False,
            is_relevant=True
        )
        
        answer = Answer(
            content="Test content",
            documentation_links=[valid_link, invalid_link]
        )
        
        assert len(answer.valid_links) == 1
        assert answer.valid_links[0] == valid_link


class TestProcessingResult:
    """Test ProcessingResult validation."""
    
    def test_successful_processing_result(self):
        """Test creating a successful processing result."""
        answer = Answer(content="Test answer", validation_status=ValidationStatus.APPROVED)
        result = ProcessingResult(
            success=True,
            answer=answer,
            processing_time=5.2,
            questions_processed=1,
            questions_failed=0
        )
        
        assert result.success is True
        assert result.answer is not None
        assert result.processing_time == 5.2
    
    def test_failed_processing_result(self):
        """Test creating a failed processing result."""
        result = ProcessingResult(
            success=False,
            error_message="Azure service unavailable",
            processing_time=1.5,
            questions_processed=0,
            questions_failed=1
        )
        
        assert result.success is False
        assert result.error_message == "Azure service unavailable"
        assert result.answer is None
    
    def test_success_without_answer(self):
        """Test validation fails for success without answer."""
        with pytest.raises(ValueError, match="Answer required when success is True"):
            ProcessingResult(success=True, processing_time=1.0)
    
    def test_failure_without_error_message(self):
        """Test validation fails for failure without error message."""
        with pytest.raises(ValueError, match="Error message required when success is False"):
            ProcessingResult(success=False, processing_time=1.0)
    
    def test_negative_processing_time(self):
        """Test validation fails for negative processing time."""
        with pytest.raises(ValueError, match="Processing time must be positive"):
            ProcessingResult(
                success=False,
                error_message="Test error",
                processing_time=-1.0
            )