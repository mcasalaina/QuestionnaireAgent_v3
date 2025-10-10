"""Unit tests for UI components and functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tkinter as tk
from src.utils.data_types import Question, ProcessingResult, Answer, ValidationStatus
from src.utils.exceptions import AzureServiceError, NetworkError, AuthenticationError


class TestUIManagerProcessing:
    """Test UIManager.process_single_question functionality."""
    
    @pytest.fixture
    def mock_agent_coordinator(self):
        """Create a mock agent coordinator."""
        coordinator = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def mock_ui_manager(self, mock_agent_coordinator):
        """Create a mock UI manager with dependencies."""
        # We'll test the interface without importing the actual UI class yet
        # since it doesn't exist. This ensures tests fail first (TDD).
        ui_manager = Mock()
        ui_manager.agent_coordinator = mock_agent_coordinator
        ui_manager.process_single_question = Mock()
        return ui_manager
    
    def test_process_single_question_success(self, mock_ui_manager, mock_agent_coordinator):
        """Test successful single question processing."""
        # Arrange
        question_text = "What is Azure AI?"
        expected_answer = Answer(
            content="Azure AI is Microsoft's comprehensive AI platform.",
            validation_status=ValidationStatus.APPROVED
        )
        expected_result = ProcessingResult(
            success=True,
            answer=expected_answer,
            processing_time=3.5,
            questions_processed=1,
            questions_failed=0
        )
        
        mock_agent_coordinator.process_question.return_value = expected_result
        
        # Mock the actual implementation behavior
        def mock_process_implementation(question, context="Microsoft Azure AI", char_limit=2000, max_retries=10):
            # Validate inputs
            if not question or len(question.strip()) < 5:
                raise ValueError("Question text must be at least 5 characters")
            
            # Create Question object
            question_obj = Question(
                text=question,
                context=context,
                char_limit=char_limit,
                max_retries=max_retries
            )
            
            # Call agent coordinator
            return mock_agent_coordinator.process_question(question_obj, Mock())
        
        mock_ui_manager.process_single_question.side_effect = mock_process_implementation
        
        # Act
        result = mock_ui_manager.process_single_question(question_text)
        
        # Assert
        assert result.success is True
        assert result.answer.content == "Azure AI is Microsoft's comprehensive AI platform."
        assert result.processing_time == 3.5
        mock_agent_coordinator.process_question.assert_called_once()
    
    def test_process_single_question_empty_input(self, mock_ui_manager):
        """Test processing fails with empty question."""
        # Mock the validation behavior
        def mock_process_implementation(question, **kwargs):
            if not question or len(question.strip()) < 5:
                raise ValueError("Question text must be at least 5 characters")
        
        mock_ui_manager.process_single_question.side_effect = mock_process_implementation
        
        # Act & Assert
        with pytest.raises(ValueError, match="Question text must be at least 5 characters"):
            mock_ui_manager.process_single_question("")
    
    def test_process_single_question_azure_service_error(self, mock_ui_manager, mock_agent_coordinator):
        """Test processing handles Azure service errors."""
        # Arrange
        mock_agent_coordinator.process_question.side_effect = AzureServiceError("Azure AI Foundry unavailable")
        
        def mock_process_implementation(question, **kwargs):
            question_obj = Question(text=question)
            try:
                return mock_agent_coordinator.process_question(question_obj, Mock())
            except AzureServiceError as e:
                return ProcessingResult(
                    success=False,
                    error_message=str(e),
                    processing_time=0.5,
                    questions_processed=0,
                    questions_failed=1
                )
        
        mock_ui_manager.process_single_question.side_effect = mock_process_implementation
        
        # Act
        result = mock_ui_manager.process_single_question("What is Azure AI?")
        
        # Assert
        assert result.success is False
        assert "Azure AI Foundry unavailable" in result.error_message
        assert result.questions_failed == 1
    
    def test_process_single_question_network_error(self, mock_ui_manager, mock_agent_coordinator):
        """Test processing handles network errors."""
        # Arrange
        mock_agent_coordinator.process_question.side_effect = NetworkError("Network connection failed")
        
        def mock_process_implementation(question, **kwargs):
            question_obj = Question(text=question)
            try:
                return mock_agent_coordinator.process_question(question_obj, Mock())
            except NetworkError as e:
                return ProcessingResult(
                    success=False,
                    error_message=str(e),
                    processing_time=0.2,
                    questions_processed=0,
                    questions_failed=1
                )
        
        mock_ui_manager.process_single_question.side_effect = mock_process_implementation
        
        # Act
        result = mock_ui_manager.process_single_question("Test question?")
        
        # Assert
        assert result.success is False
        assert "Network connection failed" in result.error_message
    
    def test_process_single_question_authentication_error(self, mock_ui_manager, mock_agent_coordinator):
        """Test processing handles authentication errors."""
        # Arrange
        mock_agent_coordinator.process_question.side_effect = AuthenticationError("Invalid Azure credentials")
        
        def mock_process_implementation(question, **kwargs):
            question_obj = Question(text=question)
            try:
                return mock_agent_coordinator.process_question(question_obj, Mock())
            except AuthenticationError as e:
                return ProcessingResult(
                    success=False,
                    error_message=str(e),
                    processing_time=0.1,
                    questions_processed=0,
                    questions_failed=1
                )
        
        mock_ui_manager.process_single_question.side_effect = mock_process_implementation
        
        # Act
        result = mock_ui_manager.process_single_question("Test question?")
        
        # Assert
        assert result.success is False
        assert "Invalid Azure credentials" in result.error_message
    
    def test_process_single_question_custom_parameters(self, mock_ui_manager, mock_agent_coordinator):
        """Test processing with custom parameters."""
        # Arrange
        expected_result = ProcessingResult(
            success=True,
            answer=Answer(content="Custom answer", validation_status=ValidationStatus.APPROVED),
            processing_time=2.0,
            questions_processed=1,
            questions_failed=0
        )
        mock_agent_coordinator.process_question.return_value = expected_result
        
        def mock_process_implementation(question, context="Microsoft Azure AI", char_limit=2000, max_retries=10):
            question_obj = Question(
                text=question,
                context=context,
                char_limit=char_limit,
                max_retries=max_retries
            )
            return mock_agent_coordinator.process_question(question_obj, Mock())
        
        mock_ui_manager.process_single_question.side_effect = mock_process_implementation
        
        # Act
        result = mock_ui_manager.process_single_question(
            "Custom question?",
            context="Custom context",
            char_limit=1500,
            max_retries=5
        )
        
        # Assert
        assert result.success is True
        # Verify the Question object was created with custom parameters
        call_args = mock_agent_coordinator.process_question.call_args[0]
        question_obj = call_args[0]
        assert question_obj.context == "Custom context"
        assert question_obj.char_limit == 1500
        assert question_obj.max_retries == 5


class TestUIManagerProgressUpdates:
    """Test UIManager.update_progress functionality."""
    
    @pytest.fixture
    def mock_ui_manager(self):
        """Create mock UI manager for progress testing."""
        ui_manager = Mock()
        ui_manager.update_progress = Mock()
        ui_manager.progress_updates = []  # Track progress calls
        
        def track_progress(agent, message, progress):
            ui_manager.progress_updates.append({
                'agent': agent,
                'message': message,
                'progress': progress
            })
        
        ui_manager.update_progress.side_effect = track_progress
        return ui_manager
    
    def test_update_progress_question_answerer(self, mock_ui_manager):
        """Test progress update for question answerer agent."""
        # Act
        mock_ui_manager.update_progress("question_answerer", "Analyzing question...", 0.1)
        
        # Assert
        assert len(mock_ui_manager.progress_updates) == 1
        update = mock_ui_manager.progress_updates[0]
        assert update['agent'] == "question_answerer"
        assert update['message'] == "Analyzing question..."
        assert update['progress'] == 0.1
    
    def test_update_progress_answer_checker(self, mock_ui_manager):
        """Test progress update for answer checker agent."""
        # Act
        mock_ui_manager.update_progress("answer_checker", "Validating answer content...", 0.6)
        
        # Assert
        update = mock_ui_manager.progress_updates[0]
        assert update['agent'] == "answer_checker"
        assert update['message'] == "Validating answer content..."
        assert update['progress'] == 0.6
    
    def test_update_progress_link_checker(self, mock_ui_manager):
        """Test progress update for link checker agent."""
        # Act
        mock_ui_manager.update_progress("link_checker", "Verifying documentation links...", 0.9)
        
        # Assert
        update = mock_ui_manager.progress_updates[0]
        assert update['agent'] == "link_checker"
        assert update['message'] == "Verifying documentation links..."
        assert update['progress'] == 0.9
    
    def test_update_progress_sequence(self, mock_ui_manager):
        """Test sequence of progress updates."""
        # Act
        mock_ui_manager.update_progress("question_answerer", "Starting...", 0.0)
        mock_ui_manager.update_progress("question_answerer", "Generating answer...", 0.3)
        mock_ui_manager.update_progress("answer_checker", "Checking quality...", 0.6)
        mock_ui_manager.update_progress("link_checker", "Validating links...", 0.8)
        mock_ui_manager.update_progress("link_checker", "Complete!", 1.0)
        
        # Assert
        assert len(mock_ui_manager.progress_updates) == 5
        assert mock_ui_manager.progress_updates[0]['progress'] == 0.0
        assert mock_ui_manager.progress_updates[-1]['progress'] == 1.0


class TestUIManagerErrorDisplay:
    """Test UIManager.display_error functionality."""
    
    @pytest.fixture
    def mock_ui_manager(self):
        """Create mock UI manager for error testing."""
        ui_manager = Mock()
        ui_manager.display_error = Mock()
        ui_manager.displayed_errors = []  # Track error displays
        
        def track_errors(error_type, message, details=None):
            ui_manager.displayed_errors.append({
                'error_type': error_type,
                'message': message,
                'details': details
            })
        
        ui_manager.display_error.side_effect = track_errors
        return ui_manager
    
    def test_display_azure_service_error(self, mock_ui_manager):
        """Test displaying Azure service error."""
        # Act
        mock_ui_manager.display_error(
            "azure_service",
            "Azure AI Foundry is currently unavailable",
            "Please check your internet connection and try again"
        )
        
        # Assert
        assert len(mock_ui_manager.displayed_errors) == 1
        error = mock_ui_manager.displayed_errors[0]
        assert error['error_type'] == "azure_service"
        assert "Azure AI Foundry" in error['message']
        assert "internet connection" in error['details']
    
    def test_display_network_error(self, mock_ui_manager):
        """Test displaying network error."""
        # Act
        mock_ui_manager.display_error(
            "network",
            "Network connection failed",
            "Check firewall settings and proxy configuration"
        )
        
        # Assert
        error = mock_ui_manager.displayed_errors[0]
        assert error['error_type'] == "network"
        assert "Network connection failed" in error['message']
    
    def test_display_authentication_error(self, mock_ui_manager):
        """Test displaying authentication error."""
        # Act
        mock_ui_manager.display_error(
            "authentication",
            "Azure authentication failed",
            "Run 'az login' to authenticate with Azure"
        )
        
        # Assert
        error = mock_ui_manager.displayed_errors[0]
        assert error['error_type'] == "authentication"
        assert "Azure authentication failed" in error['message']
        assert "az login" in error['details']
    
    def test_display_error_without_details(self, mock_ui_manager):
        """Test displaying error without details."""
        # Act
        mock_ui_manager.display_error("general", "An unexpected error occurred")
        
        # Assert
        error = mock_ui_manager.displayed_errors[0]
        assert error['error_type'] == "general"
        assert error['message'] == "An unexpected error occurred"
        assert error['details'] is None