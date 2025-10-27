#!/usr/bin/env python3
"""
Demo script showing parallel processing with 3 agent sets.
This demonstrates the key feature without requiring Azure credentials.
"""

import sys
import os
import asyncio
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unittest.mock import MagicMock, AsyncMock
from excel.processor import ParallelExcelProcessor
from utils.data_types import (
    WorkbookData, SheetData, CellState, Question, ProcessingResult, Answer, ValidationStatus
)
from utils.ui_queue import UIUpdateQueue

# Constants
MOCK_PROCESSING_TIME = 0.5  # Seconds to simulate processing each question


async def mock_process_question(agent_id, question, progress_cb, reasoning_cb, conv_cb):
    """Mock question processing that simulates work."""
    # Simulate processing time
    await asyncio.sleep(MOCK_PROCESSING_TIME)
    
    # Call callbacks to show progress
    if reasoning_cb:
        reasoning_cb(f"Processing question: {question.text}")
    
    return ProcessingResult(
        success=True,
        answer=Answer(
            content=f"Mock answer from Agent Set {agent_id}",
            validation_status=ValidationStatus.APPROVED
        ),
        processing_time=MOCK_PROCESSING_TIME,
        questions_processed=1,
        questions_failed=0
    )


async def demo_parallel_processing():
    """Demonstrate parallel processing with 3 agent sets."""
    print("=" * 80)
    print("PARALLEL AGENT PROCESSING DEMONSTRATION")
    print("=" * 80)
    print()
    print("This demo shows 3 agent sets working simultaneously on different questions.")
    print("Each agent set consists of: Question Answerer, Answer Checker, Link Checker")
    print()
    
    # Create mock coordinators
    print("Creating 3 agent sets...")
    mock_coordinators = []
    for i in range(3):
        coordinator = MagicMock()
        # Use lambda with default parameter to capture agent_id correctly
        coordinator.process_question = lambda q, p, r, c, aid=i+1: mock_process_question(aid, q, p, r, c)
        mock_coordinators.append(coordinator)
    print("✓ 3 agent sets created")
    print()
    
    # Track reasoning messages
    reasoning_messages = []
    def capture_reasoning(msg):
        reasoning_messages.append(msg)
        print(f"  [REASONING] {msg}")
    
    # Create mock UI queue
    mock_queue = MagicMock()
    events = []
    def track_event(event_type, payload, block=False):
        events.append((event_type, payload))
        if event_type == 'CELL_WORKING':
            print(f"  [STATUS] Cell {payload['row_index']} → WORKING (pink)")
        elif event_type == 'CELL_COMPLETED':
            print(f"  [STATUS] Cell {payload['row_index']} → COMPLETED (green)")
    
    mock_queue.put_event = track_event
    
    # Create processor
    print("Initializing parallel processor...")
    processor = ParallelExcelProcessor(
        agent_coordinators=mock_coordinators,
        ui_update_queue=mock_queue,
        reasoning_callback=capture_reasoning
    )
    print("✓ Parallel processor ready")
    print()
    
    # Create test workbook with 9 questions
    print("Creating test workbook with 9 questions...")
    sheet_data = SheetData(
        sheet_name="Test Questions",
        sheet_index=0,
        questions=[
            "What is the capital of France?",
            "How does photosynthesis work?",
            "What is machine learning?",
            "Explain quantum computing",
            "What is artificial intelligence?",
            "How do neural networks work?",
            "What is cloud computing?",
            "Explain blockchain technology",
            "What is edge computing?"
        ],
        answers=[None] * 9,
        cell_states=[CellState.PENDING] * 9,
        question_col_index=0,
        response_col_index=1
    )
    
    workbook_data = WorkbookData(
        file_path="/tmp/demo.xlsx",
        sheets=[sheet_data]
    )
    print("✓ Workbook created with 9 questions")
    print()
    
    # Process workbook
    print("=" * 80)
    print("STARTING PARALLEL PROCESSING")
    print("=" * 80)
    print()
    
    start = time.perf_counter()
    result = await processor.process_workbook(
        workbook_data=workbook_data,
        context="General Knowledge",
        char_limit=500,
        max_retries=3
    )
    end = time.perf_counter()
    
    print()
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Questions Processed: {result.questions_processed}")
    print(f"Questions Failed: {result.questions_failed}")
    print(f"Processing Time: {result.processing_time:.2f}s")
    print(f"Actual Time: {end - start:.2f}s")
    print()
    
    # Analyze agent set messages
    agent_set_messages = [msg for msg in reasoning_messages if "Agent Set" in msg]
    print(f"Agent Set Messages: {len(agent_set_messages)}")
    
    # Count messages per agent set
    for i in range(1, 4):
        count = len([msg for msg in agent_set_messages if f"Agent Set {i}" in msg])
        print(f"  Agent Set {i}: {count} messages")
    
    print()
    
    # Verify cell state transitions
    working_events = [e for e in events if e[0] == 'CELL_WORKING']
    completed_events = [e for e in events if e[0] == 'CELL_COMPLETED']
    
    print(f"Cell State Transitions:")
    print(f"  PENDING → WORKING: {len(working_events)}")
    print(f"  WORKING → COMPLETED: {len(completed_events)}")
    print()
    
    # Verify all cells are completed
    all_completed = all(state == CellState.COMPLETED for state in sheet_data.cell_states)
    print(f"All cells completed: {all_completed}")
    print()
    
    # Show timing benefit of parallelization
    sequential_time = 9 * MOCK_PROCESSING_TIME  # 9 questions * processing time each
    parallel_time = result.processing_time
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    
    print("=" * 80)
    print("PARALLELIZATION BENEFIT")
    print("=" * 80)
    print(f"Sequential Processing (1 agent set): ~{sequential_time:.1f}s")
    print(f"Parallel Processing (3 agent sets): ~{parallel_time:.1f}s")
    print(f"Speedup: ~{speedup:.1f}x faster")
    print()
    print("✓ Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    print()
    asyncio.run(demo_parallel_processing())
