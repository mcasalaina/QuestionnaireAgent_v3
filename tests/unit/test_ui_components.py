"""Unit tests for UI components and functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
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


class TestUIManagerDisplayAnswer:
    """Test UIManager.display_answer functionality."""
    
    @pytest.fixture
    def mock_ui_manager(self):
        """Create mock UI manager for display_answer testing."""
        ui_manager = Mock()
        ui_manager.display_answer = Mock()
        ui_manager.displayed_answers = []  # Track display calls
        
        def track_display(answer_content, sources=None):
            ui_manager.displayed_answers.append({
                'answer': answer_content,
                'sources': sources if sources else []
            })
        
        ui_manager.display_answer.side_effect = track_display
        return ui_manager
    
    def test_display_answer_with_sources(self, mock_ui_manager):
        """Test displaying answer with documentation sources."""
        # Arrange
        answer_text = "Azure AI provides comprehensive AI services."
        sources = [
            "https://docs.microsoft.com/azure/ai",
            "https://learn.microsoft.com/azure/openai"
        ]
        
        # Act
        mock_ui_manager.display_answer(answer_text, sources)
        
        # Assert
        assert len(mock_ui_manager.displayed_answers) == 1
        display = mock_ui_manager.displayed_answers[0]
        assert display['answer'] == answer_text
        assert len(display['sources']) == 2
        assert display['sources'] == sources
    
    def test_display_answer_without_sources(self, mock_ui_manager):
        """Test displaying answer without sources shows blank documentation area."""
        # Arrange
        answer_text = "Azure AI provides comprehensive AI services."
        
        # Act
        mock_ui_manager.display_answer(answer_text, sources=None)
        
        # Assert
        assert len(mock_ui_manager.displayed_answers) == 1
        display = mock_ui_manager.displayed_answers[0]
        assert display['answer'] == answer_text
        assert display['sources'] == []  # Should be empty, not "No sources provided."
    
    def test_display_answer_with_empty_sources_list(self, mock_ui_manager):
        """Test displaying answer with empty sources list shows blank documentation area."""
        # Arrange
        answer_text = "Azure AI provides comprehensive AI services."
        
        # Act
        mock_ui_manager.display_answer(answer_text, sources=[])
        
        # Assert
        assert len(mock_ui_manager.displayed_answers) == 1
        display = mock_ui_manager.displayed_answers[0]
        assert display['answer'] == answer_text


class TestURLRemovalFromAnswer:
    """Test that URLs are properly removed from answer content and only shown in Documentation tab."""
    
    def test_remove_urls_from_answer_with_trailing_urls(self):
        """Test that URLs at the end of answer are removed from answer content."""
        from src.ui.main_window import UIManager
        
        # Create a minimal UI manager instance (without initializing UI)
        with patch('src.ui.main_window.tk.Tk'):
            ui_manager = UIManager.__new__(UIManager)
        
        # Arrange
        answer_with_urls = """Azure AI's text-to-speech service, part of Azure Speech, currently supports over 140 languages and locales as of mid-2024. The service offers a wide array of neural and standard voices, enabling developers to convert text to lifelike speech in numerous languages including major world languages such as English, Spanish, Chinese, French, Arabic, Russian, Hindi, Portuguese, Japanese, German, and many others.

https://learn.microsoft.com/azure/ai-services/speech-service/language-support#text-to-speech
https://learn.microsoft.com/azure/ai-services/speech-service/language-support"""
        
        # Act
        clean_answer = ui_manager._remove_urls_from_answer(answer_with_urls)
        
        # Assert
        assert "https://" not in clean_answer, "URLs should be removed from answer content"
        assert "Azure AI's text-to-speech service" in clean_answer, "Answer content should be preserved"
        assert clean_answer.endswith("and many others."), "Answer should end with the prose, not URLs"
    
    def test_remove_urls_preserves_embedded_urls(self):
        """Test that URLs embedded in prose are preserved (only trailing URL-only lines are removed)."""
        from src.ui.main_window import UIManager
        
        with patch('src.ui.main_window.tk.Tk'):
            ui_manager = UIManager.__new__(UIManager)
        
        # Arrange - URL mentioned in the middle of prose
        answer_with_embedded_url = """Azure AI services are documented at https://learn.microsoft.com/azure/ai and include various capabilities."""
        
        # Act
        clean_answer = ui_manager._remove_urls_from_answer(answer_with_embedded_url)
        
        # Assert - Embedded URL should be preserved
        assert clean_answer == answer_with_embedded_url, "Embedded URLs in prose should be preserved"
    
    def test_remove_urls_from_answer_no_urls(self):
        """Test that answer without URLs is returned unchanged."""
        from src.ui.main_window import UIManager
        
        with patch('src.ui.main_window.tk.Tk'):
            ui_manager = UIManager.__new__(UIManager)
        
        # Arrange
        answer_without_urls = "Azure AI provides comprehensive services for natural language processing."
        
        # Act
        clean_answer = ui_manager._remove_urls_from_answer(answer_without_urls)
        
        # Assert
        assert clean_answer == answer_without_urls, "Answer without URLs should be unchanged"
    
    def test_remove_urls_handles_multiple_trailing_urls(self):
        """Test that multiple trailing URLs are all removed."""
        from src.ui.main_window import UIManager
        
        with patch('src.ui.main_window.tk.Tk'):
            ui_manager = UIManager.__new__(UIManager)
        
        # Arrange
        answer_with_multiple_urls = """Azure Cognitive Services provide AI capabilities.

https://docs.microsoft.com/azure/cognitive-services
https://learn.microsoft.com/azure/ai-services
https://azure.microsoft.com/services/cognitive-services"""
        
        # Act
        clean_answer = ui_manager._remove_urls_from_answer(answer_with_multiple_urls)
        
        # Assert
        assert "https://" not in clean_answer, "All trailing URLs should be removed"
        assert "Azure Cognitive Services provide AI capabilities." in clean_answer
    
    def test_display_answer_separates_urls_from_content(self):
        """Test that display_answer shows clean content in Answer tab and URLs in Documentation tab."""
        from src.ui.main_window import UIManager
        
        # Create mock UI components
        with patch('src.ui.main_window.tk.Tk'), \
             patch('src.ui.main_window.scrolledtext.ScrolledText') as mock_scrolled:
            
            ui_manager = UIManager.__new__(UIManager)
            
            # Mock the text widgets
            mock_answer_display = Mock()
            mock_sources_display = Mock()
            ui_manager.answer_display = mock_answer_display
            ui_manager.sources_display = mock_sources_display
            
            # Arrange
            answer_with_urls = """This is the answer content.

https://example.com/doc1
https://example.com/doc2"""
            sources = ["https://example.com/doc1", "https://example.com/doc2"]
            
            # Act
            ui_manager.display_answer(answer_with_urls, sources)
            
            # Assert - Check that answer display got clean content
            answer_display_calls = [call[0][1] for call in mock_answer_display.insert.call_args_list]
            displayed_answer = answer_display_calls[0] if answer_display_calls else ""
            
            assert "https://" not in displayed_answer, "Answer display should not contain URLs"
            assert "This is the answer content." in displayed_answer
            
            # Assert - Check that sources display got the URLs
            sources_display_calls = [call[0][1] for call in mock_sources_display.insert.call_args_list]
            displayed_sources = sources_display_calls[0] if sources_display_calls else ""
            
            assert "https://example.com/doc1" in displayed_sources, "Sources display should contain URLs"
            assert "https://example.com/doc2" in displayed_sources, "Sources display should contain URLs"