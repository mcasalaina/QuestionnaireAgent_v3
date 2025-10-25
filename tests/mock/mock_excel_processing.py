"""Mock Azure services for ExcelProcessor testing."""

import asyncio
from typing import Optional, Dict, Any
from unittest.mock import AsyncMock, MagicMock
from ...src.utils.data_types import Question, ProcessingResult, Answer, AgentStep, StepStatus, AgentType
from ...src.agents.workflow_manager import AgentCoordinator
import logging

logger = logging.getLogger(__name__)


class MockAgentCoordinator:
    """Mock AgentCoordinator for testing Excel processing without Azure services."""
    
    def __init__(self, 
                 success_rate: float = 1.0,
                 processing_delay: float = 0.1,
                 mock_answers: Optional[Dict[str, str]] = None):
        """Initialize mock coordinator.
        
        Args:
            success_rate: Fraction of questions that succeed (0.0 to 1.0)
            processing_delay: Simulated processing time in seconds
            mock_answers: Dictionary mapping question text to mock answers
        """
        self.success_rate = success_rate
        self.processing_delay = processing_delay
        self.mock_answers = mock_answers or {}
        self.call_count = 0
        self.processed_questions = []
    
    async def process_question(self, question: Question, progress_callback=None) -> ProcessingResult:
        """Mock question processing with configurable success rate.
        
        Args:
            question: Question to process
            progress_callback: Progress update callback (ignored in mock)
            
        Returns:
            ProcessingResult with mock answer or error
        """
        self.call_count += 1
        self.processed_questions.append(question.text)
        
        # Simulate processing delay
        await asyncio.sleep(self.processing_delay)
        
        # Call progress callback if provided
        if progress_callback:
            progress_callback(AgentType.QUESTION_ANSWERER, "Processing question...", 0.5)
            await asyncio.sleep(self.processing_delay / 2)
            progress_callback(AgentType.ANSWER_CHECKER, "Validating answer...", 0.8)
        
        # Determine success based on success rate and call count
        should_succeed = (self.call_count % int(1.0 / self.success_rate)) != 0 if self.success_rate < 1.0 else True
        
        if should_succeed:
            # Generate mock answer
            mock_answer_text = self.mock_answers.get(
                question.text,
                f"Mock answer for: {question.text[:50]}..."
            )
            
            answer = Answer(
                content=mock_answer_text,
                sources=["https://docs.microsoft.com/mock-source"],
                agent_reasoning=[
                    AgentStep(
                        agent_name=AgentType.QUESTION_ANSWERER,
                        input_data=question.text,
                        output_data=mock_answer_text,
                        execution_time=self.processing_delay,
                        status=StepStatus.SUCCESS
                    )
                ]
            )
            
            return ProcessingResult(
                success=True,
                answer=answer,
                processing_time=self.processing_delay
            )
        else:
            # Simulate failure
            return ProcessingResult(
                success=False,
                error_message="Mock processing failure",
                processing_time=self.processing_delay
            )
    
    async def cleanup_agents(self):
        """Mock cleanup method."""
        logger.info("Mock: Cleaned up agents")
    
    def reset_stats(self):
        """Reset call statistics."""
        self.call_count = 0
        self.processed_questions.clear()


class MockExcelProcessingService:
    """Service class for managing mock Excel processing scenarios."""
    
    @staticmethod
    def create_success_coordinator() -> MockAgentCoordinator:
        """Create coordinator that always succeeds."""
        return MockAgentCoordinator(
            success_rate=1.0,
            processing_delay=0.05,  # Fast for tests
            mock_answers={
                "What is artificial intelligence?": "AI is the simulation of human intelligence in machines.",
                "How does machine learning work?": "ML uses algorithms to learn patterns from data.",
                "What are the benefits of cloud computing?": "Cloud computing offers scalability and cost efficiency."
            }
        )
    
    @staticmethod
    def create_partial_failure_coordinator() -> MockAgentCoordinator:
        """Create coordinator with 80% success rate."""
        return MockAgentCoordinator(
            success_rate=0.8,
            processing_delay=0.05
        )
    
    @staticmethod
    def create_slow_coordinator() -> MockAgentCoordinator:
        """Create coordinator with realistic processing times."""
        return MockAgentCoordinator(
            success_rate=1.0,
            processing_delay=0.5,  # Slower for realistic testing
            mock_answers={
                "What is Azure AI?": "Azure AI provides comprehensive artificial intelligence services.",
                "How to use Azure OpenAI?": "Azure OpenAI offers access to OpenAI's powerful language models.",
                "What is Cognitive Services?": "Azure Cognitive Services are pre-built AI capabilities."
            }
        )
    
    @staticmethod
    def create_failure_coordinator() -> MockAgentCoordinator:
        """Create coordinator that always fails."""
        return MockAgentCoordinator(success_rate=0.0)


def patch_agent_coordinator(test_case, coordinator_type: str = "success") -> MockAgentCoordinator:
    """Patch AgentCoordinator for testing.
    
    Args:
        test_case: Test case instance (unittest.TestCase)
        coordinator_type: Type of mock coordinator ("success", "partial", "slow", "failure")
        
    Returns:
        MockAgentCoordinator instance
    """
    if coordinator_type == "success":
        mock_coordinator = MockExcelProcessingService.create_success_coordinator()
    elif coordinator_type == "partial":
        mock_coordinator = MockExcelProcessingService.create_partial_failure_coordinator()
    elif coordinator_type == "slow":
        mock_coordinator = MockExcelProcessingService.create_slow_coordinator()
    elif coordinator_type == "failure":
        mock_coordinator = MockExcelProcessingService.create_failure_coordinator()
    else:
        raise ValueError(f"Unknown coordinator type: {coordinator_type}")
    
    # Patch the AgentCoordinator class
    patcher = test_case.patch('src.agents.workflow_manager.AgentCoordinator')
    patcher.return_value = mock_coordinator
    
    return mock_coordinator


# Convenience functions for common test scenarios

async def process_mock_excel_questions(questions: list[str], 
                                     coordinator_type: str = "success") -> list[ProcessingResult]:
    """Process a list of questions with mock coordinator.
    
    Args:
        questions: List of question strings
        coordinator_type: Type of mock coordinator to use
        
    Returns:
        List of ProcessingResult objects
    """
    if coordinator_type == "success":
        coordinator = MockExcelProcessingService.create_success_coordinator()
    elif coordinator_type == "partial":
        coordinator = MockExcelProcessingService.create_partial_failure_coordinator()
    elif coordinator_type == "slow":
        coordinator = MockExcelProcessingService.create_slow_coordinator()
    elif coordinator_type == "failure":
        coordinator = MockExcelProcessingService.create_failure_coordinator()
    else:
        raise ValueError(f"Unknown coordinator type: {coordinator_type}")
    
    results = []
    for question_text in questions:
        question = Question(text=question_text)
        result = await coordinator.process_question(question)
        results.append(result)
    
    return results


def create_mock_workbook_data():
    """Create sample WorkbookData for testing."""
    from ...src.utils.data_types import WorkbookData, SheetData, CellState
    
    # Sheet 1: AI Basics
    sheet1 = SheetData(
        sheet_name="AI Basics",
        sheet_index=0,
        questions=[
            "What is artificial intelligence?",
            "How does machine learning work?",
            "What is deep learning?"
        ],
        answers=[None, None, None],
        cell_states=[CellState.PENDING, CellState.PENDING, CellState.PENDING]
    )
    
    # Sheet 2: Azure Services
    sheet2 = SheetData(
        sheet_name="Azure Services",
        sheet_index=1,
        questions=[
            "What is Azure AI?",
            "How to use Azure OpenAI?"
        ],
        answers=[None, None],
        cell_states=[CellState.PENDING, CellState.PENDING]
    )
    
    return WorkbookData(
        file_path="tests/fixtures/excel/test_workbook.xlsx",
        sheets=[sheet1, sheet2]
    )


# Test utilities

class ExcelProcessingTestUtils:
    """Utility functions for Excel processing tests."""
    
    @staticmethod
    def assert_processing_result(result: ProcessingResult, expected_success: bool):
        """Assert ProcessingResult properties."""
        assert result.success == expected_success
        if expected_success:
            assert result.answer is not None
            assert result.answer.content
            assert result.error_message is None
        else:
            assert result.answer is None
            assert result.error_message is not None
    
    @staticmethod
    def assert_sheet_progress(sheet_data, expected_completed: int):
        """Assert sheet completion progress."""
        from ...src.utils.data_types import CellState
        completed = sum(1 for state in sheet_data.cell_states if state == CellState.COMPLETED)
        assert completed == expected_completed
    
    @staticmethod
    def count_processing_events(events: list, event_type: str) -> int:
        """Count events of specific type."""
        return sum(1 for event in events if event.event_type == event_type)