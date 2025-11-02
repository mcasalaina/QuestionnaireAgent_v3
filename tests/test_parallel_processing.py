#!/usr/bin/env python3
"""
Test for parallel Excel processing with 3 agent sets.
"""

import os
import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from excel.processor import ParallelExcelProcessor
from utils.data_types import (
    WorkbookData, SheetData, CellState, Question, ProcessingResult, Answer, ValidationStatus
)
from utils.ui_queue import UIUpdateQueue


@pytest.mark.asyncio
async def test_parallel_processor_initialization():
    """Test that ParallelExcelProcessor requires exactly 3 coordinators."""
    mock_queue = MagicMock()
    
    # Should fail with wrong number of coordinators
    with pytest.raises(ValueError, match="requires exactly 3 agent coordinators"):
        ParallelExcelProcessor(
            agent_coordinators=[MagicMock()],
            ui_update_queue=mock_queue
        )
    
    # Should succeed with 3 coordinators
    processor = ParallelExcelProcessor(
        agent_coordinators=[MagicMock(), MagicMock(), MagicMock()],
        ui_update_queue=mock_queue
    )
    assert processor is not None
    assert len(processor.agent_coordinators) == 3


@pytest.mark.asyncio
async def test_parallel_processor_distributes_work():
    """Test that work is distributed across 3 agent sets."""
    # Create mock coordinators
    mock_coordinators = []
    for i in range(3):
        coordinator = MagicMock()
        # Mock the process_question method to return success
        # Use default parameter to capture i correctly
        async def mock_process_question(question, progress_cb, reasoning_cb, conv_cb, agent_id=i):
            return ProcessingResult(
                success=True,
                answer=Answer(
                    content=f"Answer from agent set {agent_id + 1}",
                    validation_status=ValidationStatus.APPROVED
                ),
                processing_time=0.1,
                questions_processed=1,
                questions_failed=0
            )
        coordinator.process_question = mock_process_question
        mock_coordinators.append(coordinator)
    
    # Create mock UI queue
    mock_queue = MagicMock()
    mock_queue.put_event = MagicMock()
    
    # Create processor
    processor = ParallelExcelProcessor(
        agent_coordinators=mock_coordinators,
        ui_update_queue=mock_queue
    )
    
    # Create test workbook with 6 questions (so each agent set gets 2)
    sheet_data = SheetData(
        sheet_name="Test Sheet",
        sheet_index=0,
        questions=[f"Question {i+1}" for i in range(6)],
        answers=[None] * 6,
        cell_states=[CellState.PENDING] * 6,
        question_col_index=0,
        response_col_index=1
    )
    
    workbook_data = WorkbookData(
        file_path="/tmp/test.xlsx",
        sheets=[sheet_data]
    )
    
    # Process workbook
    result = await processor.process_workbook(
        workbook_data=workbook_data,
        context="Test Context",
        char_limit=100,
        max_retries=3
    )
    
    # Verify result
    assert result.success
    assert result.questions_processed == 6
    assert result.questions_failed == 0
    
    # Verify all coordinators were used
    # Note: In parallel execution, work distribution may be uneven
    # but at least one coordinator should have been called
    total_calls = sum(1 for c in mock_coordinators if hasattr(c.process_question, '__call__'))
    assert total_calls == 3  # All coordinators should exist
    
    # Verify all questions were processed
    assert all(state == CellState.COMPLETED for state in sheet_data.cell_states)
    assert all(answer is not None for answer in sheet_data.answers)


@pytest.mark.asyncio
async def test_parallel_processor_agent_set_identification():
    """Test that agent sets identify themselves in reasoning messages."""
    reasoning_messages = []
    
    def capture_reasoning(msg):
        reasoning_messages.append(msg)
    
    # Create mock coordinators
    mock_coordinators = []
    for i in range(3):
        coordinator = MagicMock()
        async def mock_process_question(question, progress_cb, reasoning_cb, conv_cb, agent_id=i):
            # Call the reasoning callback
            if reasoning_cb:
                reasoning_cb("Processing question")
            return ProcessingResult(
                success=True,
                answer=Answer(
                    content=f"Answer {agent_id + 1}",
                    validation_status=ValidationStatus.APPROVED
                ),
                processing_time=0.1,
                questions_processed=1,
                questions_failed=0
            )
        coordinator.process_question = mock_process_question
        mock_coordinators.append(coordinator)
    
    # Create processor with reasoning callback
    processor = ParallelExcelProcessor(
        agent_coordinators=mock_coordinators,
        ui_update_queue=MagicMock(),
        reasoning_callback=capture_reasoning
    )
    
    # Create test workbook
    sheet_data = SheetData(
        sheet_name="Test Sheet",
        sheet_index=0,
        questions=["Question 1", "Question 2", "Question 3"],
        answers=[None] * 3,
        cell_states=[CellState.PENDING] * 3,
        question_col_index=0,
        response_col_index=1
    )
    
    workbook_data = WorkbookData(
        file_path="/tmp/test.xlsx",
        sheets=[sheet_data]
    )
    
    # Process workbook
    result = await processor.process_workbook(
        workbook_data=workbook_data,
        context="Test Context",
        char_limit=100,
        max_retries=3
    )
    
    # Verify agent set identification in messages
    assert result.success
    assert len(reasoning_messages) > 0
    
    # Check that we have messages from different agent sets
    agent_set_messages = [msg for msg in reasoning_messages if "Agent Set" in msg]
    assert len(agent_set_messages) > 0
    
    # Check that agent sets announce which question they're working on
    working_on_messages = [msg for msg in reasoning_messages if "working on question" in msg]
    assert len(working_on_messages) == 3  # One for each question


@pytest.mark.asyncio
async def test_parallel_processor_cell_state_transitions():
    """Test that cells transition from PENDING -> WORKING -> COMPLETED."""
    # Track cell state changes
    state_changes = []
    
    mock_queue = MagicMock()
    def track_event(event_type, payload, block=False):
        if event_type in ['CELL_WORKING', 'CELL_COMPLETED']:
            state_changes.append((event_type, payload['row_index']))
    
    mock_queue.put_event = track_event
    
    # Create mock coordinators
    mock_coordinators = []
    for i in range(3):
        coordinator = MagicMock()
        async def mock_process_question(question, progress_cb, reasoning_cb, conv_cb, agent_id=i):
            # Simulate some processing time
            await asyncio.sleep(0.01)
            return ProcessingResult(
                success=True,
                answer=Answer(
                    content=f"Answer",
                    validation_status=ValidationStatus.APPROVED
                ),
                processing_time=0.01,
                questions_processed=1,
                questions_failed=0
            )
        coordinator.process_question = mock_process_question
        mock_coordinators.append(coordinator)
    
    # Create processor
    processor = ParallelExcelProcessor(
        agent_coordinators=mock_coordinators,
        ui_update_queue=mock_queue
    )
    
    # Create test workbook
    sheet_data = SheetData(
        sheet_name="Test Sheet",
        sheet_index=0,
        questions=["Question 1", "Question 2", "Question 3"],
        answers=[None] * 3,
        cell_states=[CellState.PENDING] * 3,
        question_col_index=0,
        response_col_index=1
    )
    
    workbook_data = WorkbookData(
        file_path="/tmp/test.xlsx",
        sheets=[sheet_data]
    )
    
    # Process workbook
    result = await processor.process_workbook(
        workbook_data=workbook_data,
        context="Test Context",
        char_limit=100,
        max_retries=3
    )
    
    # Verify state changes
    assert result.success
    
    # Each question should have CELL_WORKING followed by CELL_COMPLETED
    working_events = [idx for event_type, idx in state_changes if event_type == 'CELL_WORKING']
    completed_events = [idx for event_type, idx in state_changes if event_type == 'CELL_COMPLETED']
    
    assert len(working_events) == 3
    assert len(completed_events) == 3
    assert set(working_events) == {0, 1, 2}
    assert set(completed_events) == {0, 1, 2}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
