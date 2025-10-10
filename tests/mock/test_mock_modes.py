"""Mock mode tests for GUI question processing without Azure dependencies."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from tests.mock.mock_azure_services import (
    MockAzureAIAgentClient, MockDefaultAzureCredential,
    create_mock_azure_client, create_mock_credential
)
from src.utils.data_types import Question, ProcessingResult, Answer, ValidationStatus


class TestMockModeGUIProcessing:
    """Test GUI question processing in mock mode without Azure dependencies."""
    
    @pytest.fixture
    def mock_azure_setup(self):
        """Set up mock Azure services for testing."""
        mock_client = create_mock_azure_client()
        mock_credential = create_mock_credential()
        
        return {
            'client': mock_client,
            'credential': mock_credential
        }
    
    @pytest.fixture
    def mock_gui_application(self, mock_azure_setup):
        """Create mock GUI application with mock Azure services."""
        app = Mock()
        app.azure_client = mock_azure_setup['client']
        app.credential = mock_azure_setup['credential']
        app.mock_mode = True
        
        # Mock UI components
        app.question_entry = Mock()
        app.ask_button = Mock()
        app.answer_display = Mock()
        app.progress_bar = Mock()
        app.status_label = Mock()
        
        # Mock processing methods
        app.process_question = AsyncMock()
        app.update_progress = Mock()
        app.display_answer = Mock()
        app.show_error = Mock()
        
        return app
    
    @pytest.mark.asyncio
    async def test_mock_question_processing_success(self, mock_gui_application, mock_azure_setup):
        """Test successful question processing in mock mode."""
        # Arrange
        question_text = "What is Azure AI?"
        mock_client = mock_azure_setup['client']
        
        # Set up mock agent responses
        await mock_client.create_agent(name="Question Answerer", model="gpt-4.1-mini")
        await mock_client.create_agent(name="Answer Checker", model="gpt-4.1-mini")
        await mock_client.create_agent(name="Link Checker", model="gpt-4.1-mini")
        
        # Mock the processing workflow
        async def mock_process_question(question_text):
            question = Question(text=question_text)
            
            # Simulate agent workflow
            thread = await mock_client.create_thread()
            await mock_client.create_message(thread['id'], 'user', question_text)
            
            # Get mock responses from each agent
            qa_response = await mock_client.list_messages(thread['id'], agent_type="question_answerer")
            ac_response = await mock_client.list_messages(thread['id'], agent_type="answer_checker")
            lc_response = await mock_client.list_messages(thread['id'], agent_type="link_checker")
            
            # Create mock answer
            answer = Answer(
                content=qa_response['data'][0]['content'][0]['text']['value'],
                validation_status=ValidationStatus.APPROVED,
                sources=["https://docs.microsoft.com/azure/ai"]
            )
            
            return ProcessingResult(
                success=True,
                answer=answer,
                processing_time=2.5,
                questions_processed=1,
                questions_failed=0
            )
        
        mock_gui_application.process_question.side_effect = mock_process_question
        
        # Act
        result = await mock_gui_application.process_question(question_text)
        
        # Assert
        assert result.success is True
        assert result.answer is not None
        assert result.answer.validation_status == ValidationStatus.APPROVED
        assert "Azure AI" in result.answer.content or "Azure" in result.answer.content
        assert result.processing_time > 0
        
        # Verify mock client was used
        assert len(mock_client.agents) == 3  # Three agents created
        assert len(mock_client.threads) >= 1  # At least one thread created
    
    @pytest.mark.asyncio
    async def test_mock_question_processing_with_progress_updates(self, mock_gui_application):
        """Test question processing with progress updates in mock mode."""
        # Arrange
        progress_updates = []
        
        def track_progress(agent, message, progress):
            progress_updates.append({
                'agent': agent,
                'message': message,
                'progress': progress
            })
        
        mock_gui_application.update_progress.side_effect = track_progress
        
        # Simulate workflow with progress updates
        async def mock_process_with_progress(question_text):
            mock_gui_application.update_progress("question_answerer", "Analyzing question...", 0.1)
            mock_gui_application.update_progress("question_answerer", "Generating answer...", 0.3)
            mock_gui_application.update_progress("answer_checker", "Validating content...", 0.6)
            mock_gui_application.update_progress("link_checker", "Checking links...", 0.8)
            mock_gui_application.update_progress("link_checker", "Complete!", 1.0)
            
            return ProcessingResult(
                success=True,
                answer=Answer(content="Mock answer", validation_status=ValidationStatus.APPROVED),
                processing_time=3.0,
                questions_processed=1,
                questions_failed=0
            )
        
        mock_gui_application.process_question.side_effect = mock_process_with_progress
        
        # Act
        result = await mock_gui_application.process_question("Test question?")
        
        # Assert
        assert result.success is True
        assert len(progress_updates) == 5
        assert progress_updates[0]['agent'] == "question_answerer"
        assert progress_updates[0]['progress'] == 0.1
        assert progress_updates[-1]['agent'] == "link_checker"
        assert progress_updates[-1]['progress'] == 1.0
    
    def test_mock_error_handling_azure_service_failure(self, mock_gui_application):
        """Test error handling when mock Azure service fails."""
        # Arrange
        error_displays = []
        
        def track_errors(error_type, message, details=None):
            error_displays.append({
                'error_type': error_type,
                'message': message,
                'details': details
            })
        
        mock_gui_application.show_error.side_effect = track_errors
        
        # Simulate Azure service failure
        async def mock_process_with_error(question_text):
            mock_gui_application.show_error(
                "azure_service",
                "Mock Azure service unavailable",
                "This is a simulated error for testing purposes"
            )
            return ProcessingResult(
                success=False,
                error_message="Mock Azure service unavailable",
                processing_time=0.5,
                questions_processed=0,
                questions_failed=1
            )
        
        mock_gui_application.process_question.side_effect = mock_process_with_error
        
        # Act
        # This would be called by the GUI button click handler
        import asyncio
        result = asyncio.run(mock_gui_application.process_question("Test question?"))
        
        # Assert
        assert result.success is False
        assert len(error_displays) == 1
        assert error_displays[0]['error_type'] == "azure_service"
        assert "Mock Azure service unavailable" in error_displays[0]['message']
    
    def test_mock_gui_components_interaction(self, mock_gui_application):
        """Test mock GUI components interact correctly."""
        # Arrange - Simulate user input
        question_text = "How does Azure OpenAI work?"
        mock_gui_application.question_entry.get.return_value = question_text
        
        # Mock answer display
        def mock_display_answer(answer_content, sources=None):
            mock_gui_application.last_displayed_answer = answer_content
            mock_gui_application.last_displayed_sources = sources or []
        
        mock_gui_application.display_answer.side_effect = mock_display_answer
        
        # Act - Simulate button click processing
        user_input = mock_gui_application.question_entry.get()
        
        # Simulate successful processing
        mock_answer = "Azure OpenAI provides access to OpenAI's language models through Azure's secure, enterprise-ready platform."
        mock_sources = ["https://docs.microsoft.com/azure/openai"]
        
        mock_gui_application.display_answer(mock_answer, mock_sources)
        
        # Assert
        assert user_input == question_text
        assert mock_gui_application.last_displayed_answer == mock_answer
        assert mock_gui_application.last_displayed_sources == mock_sources
        mock_gui_application.question_entry.get.assert_called_once()
        mock_gui_application.display_answer.assert_called_once()
    
    def test_mock_progress_bar_updates(self, mock_gui_application):
        """Test progress bar updates during mock processing."""
        # Arrange
        progress_values = []
        
        def track_progress_bar(value):
            progress_values.append(value)
        
        # Mock progress bar behavior
        def mock_update_progress(agent, message, progress):
            progress_percentage = int(progress * 100)
            track_progress_bar(progress_percentage)
            mock_gui_application.progress_bar.set(progress_percentage)
            mock_gui_application.status_label.set(f"{agent}: {message}")
        
        mock_gui_application.update_progress.side_effect = mock_update_progress
        
        # Act - Simulate progress updates
        mock_gui_application.update_progress("question_answerer", "Starting...", 0.0)
        mock_gui_application.update_progress("question_answerer", "Processing...", 0.4)
        mock_gui_application.update_progress("answer_checker", "Validating...", 0.7)
        mock_gui_application.update_progress("link_checker", "Complete!", 1.0)
        
        # Assert
        assert progress_values == [0, 40, 70, 100]
        assert mock_gui_application.progress_bar.set.call_count == 4
        assert mock_gui_application.status_label.set.call_count == 4
    
    @pytest.mark.asyncio
    async def test_mock_agent_responses_variety(self, mock_azure_setup):
        """Test variety in mock agent responses."""
        # Arrange
        mock_client = mock_azure_setup['client']
        questions = [
            "What is Azure AI?",
            "How do I use Azure OpenAI?",
            "What are Azure Cognitive Services?",
            "How does Azure Machine Learning work?"
        ]
        
        responses = []
        
        # Act - Get responses for different questions
        for question in questions:
            thread = await mock_client.create_thread()
            await mock_client.create_message(thread['id'], 'user', question)
            response = await mock_client.list_messages(thread['id'], agent_type="question_answerer")
            responses.append(response['data'][0]['content'][0]['text']['value'])
        
        # Assert - Verify we get different responses
        assert len(responses) == 4
        assert len(set(responses)) >= 2  # At least some variety in responses
        
        # Verify all responses contain relevant content
        for response in responses:
            assert len(response) > 50  # Reasonable length
            assert any(keyword in response.lower() for keyword in ['azure', 'ai', 'microsoft', 'service'])


class TestMockModeValidation:
    """Test validation behavior in mock mode."""
    
    @pytest.mark.asyncio
    async def test_mock_answer_checker_approval(self, mock_azure_setup):
        """Test mock answer checker approval behavior."""
        # Arrange
        mock_client = mock_azure_setup['client']
        
        # Act
        thread = await mock_client.create_thread()
        response = await mock_client.list_messages(thread['id'], agent_type="answer_checker")
        validation_result = response['data'][0]['content'][0]['text']['value']
        
        # Assert
        assert "APPROVED" in validation_result or "REJECTED" in validation_result
        if "APPROVED" in validation_result:
            assert "accurate" in validation_result.lower() or "correct" in validation_result.lower()
    
    @pytest.mark.asyncio
    async def test_mock_link_checker_validation(self, mock_azure_setup):
        """Test mock link checker validation behavior."""
        # Arrange
        mock_client = mock_azure_setup['client']
        
        # Act
        thread = await mock_client.create_thread()
        response = await mock_client.list_messages(thread['id'], agent_type="link_checker")
        link_check_result = response['data'][0]['content'][0]['text']['value']
        
        # Assert
        assert "LINKS_VALID" in link_check_result or "LINKS_INVALID" in link_check_result
        if "LINKS_VALID" in link_check_result:
            assert "verified" in link_check_result.lower() or "accessible" in link_check_result.lower()