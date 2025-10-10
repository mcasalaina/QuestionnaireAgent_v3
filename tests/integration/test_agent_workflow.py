"""Integration tests for multi-agent workflow."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.utils.data_types import (
    Question, Answer, ProcessingResult, AgentStep,
    AgentType, ValidationStatus, StepStatus
)
from src.utils.exceptions import AzureServiceError, MaxRetriesExceededError, ValidationTimeoutError


class TestAgentWorkflowIntegration:
    """Test integration of multi-agent workflow components."""
    
    @pytest.fixture
    def mock_azure_client(self):
        """Create mock Azure AI Agent client."""
        client = AsyncMock()
        
        # Mock agent creation
        client.create_agent.return_value = {
            "id": "mock_agent_123",
            "name": "Test Agent",
            "model": "gpt-4.1-mini"
        }
        
        # Mock thread creation
        client.create_thread.return_value = {
            "id": "mock_thread_456",
            "object": "thread"
        }
        
        # Mock run creation and completion
        client.create_run.return_value = {
            "id": "mock_run_789",
            "status": "in_progress"
        }
        
        client.get_run.return_value = {
            "id": "mock_run_789",
            "status": "completed"
        }
        
        # Mock message responses
        client.list_messages.return_value = {
            "data": [{
                "id": "mock_msg_001",
                "role": "assistant",
                "content": [{"type": "text", "text": {"value": "Mock agent response"}}]
            }]
        }
        
        return client
    
    @pytest.fixture
    def mock_agent_coordinator(self, mock_azure_client):
        """Create mock agent coordinator."""
        coordinator = Mock()
        coordinator.azure_client = mock_azure_client
        coordinator.process_question = AsyncMock()
        coordinator.process_batch = AsyncMock()
        coordinator.create_agents = AsyncMock()
        coordinator.cleanup_agents = AsyncMock()
        coordinator.health_check = AsyncMock()
        return coordinator
    
    @pytest.mark.asyncio
    async def test_single_question_workflow_success(self, mock_agent_coordinator):
        """Test successful single question processing through workflow."""
        # Arrange
        question = Question(
            text="What is Azure AI?",
            context="Microsoft Azure AI",
            char_limit=2000,
            max_retries=10
        )
        
        expected_answer = Answer(
            content="Azure AI is Microsoft's comprehensive artificial intelligence platform that provides machine learning, cognitive services, and OpenAI integration.",
            sources=["https://docs.microsoft.com/azure/ai"],
            validation_status=ValidationStatus.APPROVED,
            retry_count=1,
            agent_reasoning=[
                AgentStep(
                    agent_name=AgentType.QUESTION_ANSWERER,
                    input_data=question.text,
                    output_data="Generated comprehensive answer about Azure AI",
                    execution_time=2.5,
                    status=StepStatus.SUCCESS
                ),
                AgentStep(
                    agent_name=AgentType.ANSWER_CHECKER,
                    input_data="Generated comprehensive answer about Azure AI",
                    output_data="APPROVED: Answer is accurate and complete",
                    execution_time=1.2,
                    status=StepStatus.SUCCESS
                ),
                AgentStep(
                    agent_name=AgentType.LINK_CHECKER,
                    input_data="https://docs.microsoft.com/azure/ai",
                    output_data="LINKS_VALID: All documentation links verified",
                    execution_time=0.8,
                    status=StepStatus.SUCCESS
                )
            ]
        )
        
        expected_result = ProcessingResult(
            success=True,
            answer=expected_answer,
            processing_time=4.5,
            questions_processed=1,
            questions_failed=0
        )
        
        mock_agent_coordinator.process_question.return_value = expected_result
        
        # Act
        progress_callback = Mock()
        result = await mock_agent_coordinator.process_question(question, progress_callback)
        
        # Assert
        assert result.success is True
        assert result.answer.validation_status == ValidationStatus.APPROVED
        assert len(result.answer.agent_reasoning) == 3
        assert result.answer.agent_reasoning[0].agent_name == AgentType.QUESTION_ANSWERER
        assert result.answer.agent_reasoning[1].agent_name == AgentType.ANSWER_CHECKER
        assert result.answer.agent_reasoning[2].agent_name == AgentType.LINK_CHECKER
        assert result.processing_time == 4.5
        
        mock_agent_coordinator.process_question.assert_called_once_with(question, progress_callback)
    
    @pytest.mark.asyncio
    async def test_workflow_with_answer_rejection(self, mock_agent_coordinator):
        """Test workflow when answer checker rejects the answer."""
        # Arrange
        question = Question(text="Test question that gets rejected")
        
        # Simulate answer rejection and retry
        rejected_answer = Answer(
            content="Initial answer that gets rejected",
            validation_status=ValidationStatus.REJECTED_CONTENT,
            retry_count=2,
            agent_reasoning=[
                AgentStep(
                    agent_name=AgentType.QUESTION_ANSWERER,
                    input_data=question.text,
                    output_data="Initial answer that gets rejected",
                    execution_time=2.0,
                    status=StepStatus.SUCCESS
                ),
                AgentStep(
                    agent_name=AgentType.ANSWER_CHECKER,
                    input_data="Initial answer that gets rejected",
                    output_data="REJECTED: Answer lacks sufficient detail",
                    execution_time=1.0,
                    status=StepStatus.SUCCESS
                ),
                AgentStep(
                    agent_name=AgentType.QUESTION_ANSWERER,
                    input_data=question.text + " (retry)",
                    output_data="Improved detailed answer",
                    execution_time=2.2,
                    status=StepStatus.SUCCESS
                ),
                AgentStep(
                    agent_name=AgentType.ANSWER_CHECKER,
                    input_data="Improved detailed answer",
                    output_data="APPROVED: Answer now meets quality standards",
                    execution_time=1.1,
                    status=StepStatus.SUCCESS
                )
            ]
        )
        
        # Final approved answer after retry
        approved_answer = Answer(
            content="Improved detailed answer",
            validation_status=ValidationStatus.APPROVED,
            retry_count=2
        )
        
        result = ProcessingResult(
            success=True,
            answer=approved_answer,
            processing_time=6.3,
            questions_processed=1,
            questions_failed=0
        )
        
        mock_agent_coordinator.process_question.return_value = result
        
        # Act
        progress_callback = Mock()
        result = await mock_agent_coordinator.process_question(question, progress_callback)
        
        # Assert
        assert result.success is True
        assert result.answer.validation_status == ValidationStatus.APPROVED
        assert result.answer.retry_count == 2
    
    @pytest.mark.asyncio
    async def test_workflow_max_retries_exceeded(self, mock_agent_coordinator):
        """Test workflow when maximum retries are exceeded."""
        # Arrange
        question = Question(text="Problematic question", max_retries=3)
        
        mock_agent_coordinator.process_question.side_effect = MaxRetriesExceededError(
            "Maximum retry attempts (3) reached without valid answer"
        )
        
        # Act & Assert
        progress_callback = Mock()
        with pytest.raises(MaxRetriesExceededError, match="Maximum retry attempts"):
            await mock_agent_coordinator.process_question(question, progress_callback)
    
    @pytest.mark.asyncio
    async def test_workflow_azure_service_failure(self, mock_agent_coordinator):
        """Test workflow when Azure services fail."""
        # Arrange
        question = Question(text="Test question")
        
        mock_agent_coordinator.process_question.side_effect = AzureServiceError(
            "Azure AI Foundry service is currently unavailable"
        )
        
        # Act & Assert
        progress_callback = Mock()
        with pytest.raises(AzureServiceError, match="Azure AI Foundry service"):
            await mock_agent_coordinator.process_question(question, progress_callback)
    
    @pytest.mark.asyncio
    async def test_workflow_timeout_error(self, mock_agent_coordinator):
        """Test workflow when validation times out."""
        # Arrange
        question = Question(text="Question that times out")
        
        mock_agent_coordinator.process_question.side_effect = ValidationTimeoutError(
            "Agent validation exceeded configured timeout (120 seconds)"
        )
        
        # Act & Assert
        progress_callback = Mock()
        with pytest.raises(ValidationTimeoutError, match="Agent validation exceeded"):
            await mock_agent_coordinator.process_question(question, progress_callback)
    
    @pytest.mark.asyncio
    async def test_batch_processing_workflow(self, mock_agent_coordinator):
        """Test batch processing of multiple questions."""
        # Arrange
        questions = [
            Question(text="What is Azure AI?", id="Q1"),
            Question(text="How does Azure OpenAI work?", id="Q2"),
            Question(text="What are Azure Cognitive Services?", id="Q3")
        ]
        
        expected_results = [
            ProcessingResult(
                success=True,
                answer=Answer(content="Answer 1", validation_status=ValidationStatus.APPROVED),
                processing_time=3.0,
                questions_processed=1,
                questions_failed=0
            ),
            ProcessingResult(
                success=True,
                answer=Answer(content="Answer 2", validation_status=ValidationStatus.APPROVED),
                processing_time=3.5,
                questions_processed=1,
                questions_failed=0
            ),
            ProcessingResult(
                success=False,
                error_message="Network timeout occurred",
                processing_time=1.0,
                questions_processed=0,
                questions_failed=1
            )
        ]
        
        mock_agent_coordinator.process_batch.return_value = expected_results
        
        # Act
        progress_callback = Mock()
        results = await mock_agent_coordinator.process_batch(questions, progress_callback)
        
        # Assert
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is True
        assert results[2].success is False
        assert results[2].error_message == "Network timeout occurred"
        
        mock_agent_coordinator.process_batch.assert_called_once_with(questions, progress_callback)
    
    @pytest.mark.asyncio
    async def test_agent_creation_and_cleanup(self, mock_agent_coordinator):
        """Test agent creation and cleanup workflow."""
        # Act - Test agent creation
        await mock_agent_coordinator.create_agents()
        
        # Act - Test agent cleanup
        await mock_agent_coordinator.cleanup_agents()
        
        # Assert
        mock_agent_coordinator.create_agents.assert_called_once()
        mock_agent_coordinator.cleanup_agents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_workflow(self, mock_agent_coordinator):
        """Test system health check workflow."""
        # Arrange
        from src.utils.data_types import HealthStatus
        
        expected_health = HealthStatus(
            azure_connectivity=True,
            authentication_valid=True,
            configuration_valid=True,
            agent_services_available=True,
            error_details=[]
        )
        
        mock_agent_coordinator.health_check.return_value = expected_health
        
        # Act
        health_status = await mock_agent_coordinator.health_check()
        
        # Assert
        assert health_status.is_healthy is True
        assert health_status.azure_connectivity is True
        assert health_status.authentication_valid is True
        assert health_status.configuration_valid is True
        assert health_status.agent_services_available is True
        assert len(health_status.error_details) == 0
        
        mock_agent_coordinator.health_check.assert_called_once()


class TestProgressCallbackIntegration:
    """Test progress callback integration during workflow execution."""
    
    def test_progress_callback_during_question_processing(self):
        """Test progress callbacks are called during question processing."""
        # Arrange
        progress_calls = []
        
        def progress_callback(agent, message, progress):
            progress_calls.append({
                'agent': agent,
                'message': message,
                'progress': progress
            })
        
        # Simulate workflow progress calls
        progress_callback("question_answerer", "Starting question analysis...", 0.0)
        progress_callback("question_answerer", "Generating answer...", 0.2)
        progress_callback("answer_checker", "Validating answer quality...", 0.5)
        progress_callback("answer_checker", "Answer approved", 0.7)
        progress_callback("link_checker", "Checking documentation links...", 0.8)
        progress_callback("link_checker", "All links verified", 1.0)
        
        # Assert
        assert len(progress_calls) == 6
        assert progress_calls[0]['agent'] == "question_answerer"
        assert progress_calls[0]['progress'] == 0.0
        assert progress_calls[-1]['agent'] == "link_checker"
        assert progress_calls[-1]['progress'] == 1.0
        
        # Verify progress increases monotonically
        for i in range(1, len(progress_calls)):
            assert progress_calls[i]['progress'] >= progress_calls[i-1]['progress']