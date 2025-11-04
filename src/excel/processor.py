"""Excel workbook processing with multi-agent workflow."""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from agents.workflow_manager import AgentCoordinator
from utils.data_types import (
    WorkbookData, Question, UIUpdateEvent, ExcelProcessingResult, CellState
)
from utils.ui_queue import UIUpdateQueue
import logging

logger = logging.getLogger(__name__)


class ExcelProcessor:
    """Processes Excel workbooks through multi-agent workflow with live UI updates."""
    
    def __init__(
        self,
        agent_coordinator: AgentCoordinator,
        ui_update_queue: UIUpdateQueue,
        reasoning_callback = None,
        agent_conversation_callback = None,
        progress_callback = None
    ):
        """Initialize processor.
        
        Args:
            agent_coordinator: Initialized AgentCoordinator instance
            ui_update_queue: Thread-safe queue for UI updates
            reasoning_callback: Optional callback for agent reasoning updates
            agent_conversation_callback: Optional callback for displaying formatted agent conversation
            progress_callback: Optional callback for progress updates (agent, message, progress)
        """
        self.agent_coordinator = agent_coordinator
        self.ui_queue = ui_update_queue
        self.reasoning_callback = reasoning_callback
        self.agent_conversation_callback = agent_conversation_callback
        self.progress_callback = progress_callback
        self.cancelled = False
    
    async def process_workbook(
        self,
        workbook_data: WorkbookData,
        context: str,
        char_limit: int,
        max_retries: int
    ) -> ExcelProcessingResult:
        """Process all sheets in workbook sequentially.
        
        Args:
            workbook_data: Loaded workbook with questions
            context: Domain context for questions
            char_limit: Maximum answer length
            max_retries: Maximum retry attempts per question
            
        Returns:
            ExcelProcessingResult with completion statistics
        """
        start_time = time.time()
        total_processed = 0
        total_failed = 0
        
        logger.info(f"Starting Excel workbook processing: {len(workbook_data.sheets)} sheets, {workbook_data.total_questions} total questions")
        
        try:
            for sheet_idx, sheet_data in enumerate(workbook_data.sheets):
                if self.cancelled:
                    logger.info("Processing cancelled by user")
                    break
                
                # Emit sheet start event
                self._emit_event('SHEET_START', {'sheet_index': sheet_idx})
                sheet_data.is_processing = True
                workbook_data.current_sheet_index = sheet_idx
                
                logger.info(f"Processing sheet '{sheet_data.sheet_name}' ({sheet_idx + 1}/{len(workbook_data.sheets)}) with {len(sheet_data.questions)} questions")
                
                # Process each question in the sheet
                for row_idx, question_text in enumerate(sheet_data.questions):
                    if self.cancelled:
                        break
                    
                    # Emit cell working event
                    self._emit_event('CELL_WORKING', {
                        'sheet_index': sheet_idx,
                        'row_index': row_idx
                    })
                    sheet_data.mark_working(row_idx)
                    
                    # Create Question object
                    question = Question(
                        text=question_text,
                        context=context,
                        char_limit=char_limit,
                        max_retries=max_retries
                    )
                    
                    # Process with agents
                    try:
                        logger.info(f"📋 PROCESSING QUESTION {row_idx + 1}/{len(sheet_data.questions)} in sheet '{sheet_data.sheet_name}'")
                        logger.info(f"❓ Question: '{question_text}'")
                        logger.info(f"🎯 Context: {context}")
                        logger.info(f"📏 Character limit: {char_limit}")
                        logger.info(f"🔄 Max retries: {max_retries}")
                        
                        # Create progress callback that logs and updates UI
                        def local_progress_callback(agent, msg, progress):
                            progress_msg = f"Agent progress - {agent}: {msg} ({progress:.1%})"
                            logger.info(f"📊 {progress_msg}")
                            # Update UI progress bar if callback provided
                            if self.progress_callback:
                                self.progress_callback(agent, msg, progress)
                        
                        # Create reasoning callback that logs and updates UI
                        def reasoning_callback(msg):
                            reasoning_msg = f"Question {row_idx + 1}: {msg}"
                            logger.info(f"🧠 Agent reasoning: {reasoning_msg}")
                            if self.reasoning_callback:
                                self.reasoning_callback(reasoning_msg)
                        
                        logger.info(f"🚀 Starting agent processing for question {row_idx + 1}...")
                        result = await self.agent_coordinator.process_question(
                            question,
                            local_progress_callback,
                            reasoning_callback,
                            self.agent_conversation_callback
                        )
                        
                        if result.success and result.answer:
                            # Success - emit completed event
                            answer_text = result.answer.content
                            sheet_data.mark_completed(row_idx, answer_text)
                            
                            logger.info(f"✅ Question {row_idx + 1} SUCCESSFULLY processed - Answer: '{answer_text[:100]}...'")
                            
                            # Display formatted agent conversation if callback provided
                            if self.agent_conversation_callback and result.answer.agent_reasoning:
                                self.agent_conversation_callback(
                                    result.answer.agent_reasoning,
                                    result.answer.documentation_links
                                )
                            
                            self._emit_event('CELL_COMPLETED', {
                                'sheet_index': sheet_idx,
                                'row_index': row_idx,
                                'answer': answer_text
                            })
                            
                            total_processed += 1
                            logger.debug(f"Successfully processed question {row_idx + 1}")
                        else:
                            # Failed - emit error completion
                            error_text = f"ERROR: {result.error_message or 'Processing failed'}"
                            sheet_data.mark_completed(row_idx, error_text)
                            
                            logger.error(f"❌ Question {row_idx + 1} FAILED - Error: {result.error_message}")
                            
                            # Display formatted agent conversation even for failures if available
                            # This helps understand what went wrong in the agent workflow
                            if self.agent_conversation_callback and result.answer and result.answer.agent_reasoning:
                                self.agent_conversation_callback(
                                    result.answer.agent_reasoning,
                                    result.answer.documentation_links if result.answer else []
                                )
                            
                            self._emit_event('CELL_COMPLETED', {
                                'sheet_index': sheet_idx,
                                'row_index': row_idx,
                                'answer': error_text
                            })
                            
                            total_failed += 1
                            logger.warning(f"Failed to process question {row_idx + 1}: {result.error_message}")
                    
                    except Exception as e:
                        # Exception during processing
                        error_text = f"ERROR: {str(e)}"
                        sheet_data.mark_completed(row_idx, error_text)
                        
                        self._emit_event('CELL_COMPLETED', {
                            'sheet_index': sheet_idx,
                            'row_index': row_idx,
                            'answer': error_text
                        })
                        
                        total_failed += 1
                        logger.error(f"Exception processing question {row_idx + 1}: {e}")
                
                # Emit sheet complete event
                sheet_data.is_processing = False
                sheet_data.is_complete = True
                self._emit_event('SHEET_COMPLETE', {'sheet_index': sheet_idx})
                
                logger.info(f"Completed sheet '{sheet_data.sheet_name}': {sum(1 for s in sheet_data.cell_states if s == CellState.COMPLETED)} questions processed")
            
            # Emit workbook complete event
            processing_time = time.time() - start_time
            self._emit_event('WORKBOOK_COMPLETE', {'file_path': workbook_data.file_path})
            
            logger.info(f"Excel workbook processing completed in {processing_time:.1f}s: {total_processed} successful, {total_failed} failed")
            
            return ExcelProcessingResult(
                success=True,
                output_file_path=workbook_data.file_path,
                questions_processed=total_processed,
                questions_failed=total_failed,
                processing_time=processing_time
            )
        
        except Exception as e:
            # Emit error event
            processing_time = time.time() - start_time
            self._emit_event('ERROR', {
                'error_type': 'processing_error',
                'message': str(e)
            })
            
            logger.error(f"Fatal error in Excel processing: {e}", exc_info=True)
            
            return ExcelProcessingResult(
                success=False,
                error_message=f"Processing failed: {str(e)}",
                questions_processed=total_processed,
                questions_failed=total_failed,
                processing_time=processing_time
            )
    
    def cancel_processing(self) -> None:
        """Cancel the current processing operation."""
        self.cancelled = True
        logger.info("Excel processing cancellation requested")
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit UI update event to queue.
        
        Args:
            event_type: Type of event to emit
            payload: Event payload data
        """
        try:
            self.ui_queue.put_event(event_type, payload, block=False)
        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {e}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'cancelled': self.cancelled,
            'queue_size': self.ui_queue.qsize() if self.ui_queue else 0
        }


class ParallelExcelProcessor:
    """Processes Excel workbooks with 3 parallel agent sets."""
    
    def __init__(
        self,
        agent_coordinators: List[AgentCoordinator],
        ui_update_queue: UIUpdateQueue,
        reasoning_callback = None,
        agent_conversation_callback = None,
        progress_callback = None
    ):
        """Initialize parallel processor.
        
        Args:
            agent_coordinators: List of 3 initialized AgentCoordinator instances
            ui_update_queue: Thread-safe queue for UI updates
            reasoning_callback: Optional callback for agent reasoning updates
            agent_conversation_callback: Optional callback for displaying formatted agent conversation
            progress_callback: Optional callback for progress updates
        """
        if len(agent_coordinators) != 3:
            raise ValueError("ParallelExcelProcessor requires exactly 3 agent coordinators")
        
        self.agent_coordinators = agent_coordinators
        self.ui_queue = ui_update_queue
        self.reasoning_callback = reasoning_callback
        self.agent_conversation_callback = agent_conversation_callback
        self.progress_callback = progress_callback
        self.cancelled = False
        
        # Lock for thread-safe state updates
        self._state_lock = asyncio.Lock()
    
    async def process_workbook(
        self,
        workbook_data: WorkbookData,
        context: str,
        char_limit: int,
        max_retries: int
    ) -> ExcelProcessingResult:
        """Process all sheets in workbook with 3 parallel agent sets.
        
        Args:
            workbook_data: Loaded workbook with questions
            context: Domain context for questions
            char_limit: Maximum answer length
            max_retries: Maximum retry attempts per question
            
        Returns:
            ExcelProcessingResult with completion statistics
        """
        start_time = time.time()
        total_processed = 0
        total_failed = 0
        
        logger.info(f"Starting parallel Excel workbook processing: {len(workbook_data.sheets)} sheets, {workbook_data.total_questions} total questions with 3 agent sets")
        
        try:
            for sheet_idx, sheet_data in enumerate(workbook_data.sheets):
                if self.cancelled:
                    logger.info("Processing cancelled by user")
                    break
                
                # Emit sheet start event
                self._emit_event('SHEET_START', {'sheet_index': sheet_idx})
                sheet_data.is_processing = True
                workbook_data.current_sheet_index = sheet_idx
                
                logger.info(f"Processing sheet '{sheet_data.sheet_name}' ({sheet_idx + 1}/{len(workbook_data.sheets)}) with {len(sheet_data.questions)} questions using 3 parallel agent sets")
                
                # Create work queue with all questions for this sheet
                pending_questions = [
                    (row_idx, question_text)
                    for row_idx, question_text in enumerate(sheet_data.questions)
                ]
                
                # Process questions in parallel with 3 agent sets
                processed, failed = await self._process_sheet_parallel(
                    sheet_idx,
                    sheet_data,
                    pending_questions,
                    context,
                    char_limit,
                    max_retries
                )
                
                total_processed += processed
                total_failed += failed
                
                # Emit sheet complete event
                sheet_data.is_processing = False
                sheet_data.is_complete = True
                self._emit_event('SHEET_COMPLETE', {'sheet_index': sheet_idx})
                
                logger.info(f"Completed sheet '{sheet_data.sheet_name}': {processed} questions processed, {failed} failed")
            
            # Emit workbook complete event
            processing_time = time.time() - start_time
            self._emit_event('WORKBOOK_COMPLETE', {'file_path': workbook_data.file_path})
            
            logger.info(f"Parallel Excel workbook processing completed in {processing_time:.1f}s: {total_processed} successful, {total_failed} failed")
            
            return ExcelProcessingResult(
                success=True,
                output_file_path=workbook_data.file_path,
                questions_processed=total_processed,
                questions_failed=total_failed,
                processing_time=processing_time
            )
        
        except Exception as e:
            # Emit error event
            processing_time = time.time() - start_time
            self._emit_event('ERROR', {
                'error_type': 'processing_error',
                'message': str(e)
            })
            
            logger.error(f"Fatal error in parallel Excel processing: {e}", exc_info=True)
            
            return ExcelProcessingResult(
                success=False,
                error_message=f"Processing failed: {str(e)}",
                questions_processed=total_processed,
                questions_failed=total_failed,
                processing_time=processing_time
            )
    
    async def _process_sheet_parallel(
        self,
        sheet_idx: int,
        sheet_data,
        pending_questions: List[Tuple[int, str]],
        context: str,
        char_limit: int,
        max_retries: int
    ) -> Tuple[int, int]:
        """Process a single sheet with 3 parallel agent sets.
        
        Args:
            sheet_idx: Sheet index
            sheet_data: Sheet data object
            pending_questions: List of (row_idx, question_text) tuples
            context: Domain context
            char_limit: Character limit
            max_retries: Max retry attempts
            
        Returns:
            Tuple of (processed_count, failed_count)
        """
        # Create a work queue
        work_queue = asyncio.Queue()
        for item in pending_questions:
            await work_queue.put(item)
        
        # Create 3 worker tasks, one per agent set
        workers = [
            asyncio.create_task(
                self._agent_set_worker(
                    agent_set_id=i + 1,
                    sheet_idx=sheet_idx,
                    sheet_data=sheet_data,
                    work_queue=work_queue,
                    context=context,
                    char_limit=char_limit,
                    max_retries=max_retries
                )
            )
            for i in range(3)
        ]
        
        # Wait for all workers to complete
        results = await asyncio.gather(*workers, return_exceptions=True)
        
        # Aggregate results
        total_processed = 0
        total_failed = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent Set {i + 1} encountered error: {result}")
                continue
            
            processed, failed = result
            total_processed += processed
            total_failed += failed
            logger.info(f"Agent Set {i + 1} completed: {processed} processed, {failed} failed")
        
        return total_processed, total_failed
    
    async def _agent_set_worker(
        self,
        agent_set_id: int,
        sheet_idx: int,
        sheet_data,
        work_queue: asyncio.Queue,
        context: str,
        char_limit: int,
        max_retries: int
    ) -> Tuple[int, int]:
        """Worker for a single agent set.
        
        Args:
            agent_set_id: ID of this agent set (1, 2, or 3)
            sheet_idx: Sheet index
            sheet_data: Sheet data object
            work_queue: Queue of pending questions
            context: Domain context
            char_limit: Character limit
            max_retries: Max retry attempts
            
        Returns:
            Tuple of (processed_count, failed_count)
        """
        coordinator = self.agent_coordinators[agent_set_id - 1]
        processed_count = 0
        failed_count = 0
        
        logger.info(f"🚀 Agent Set {agent_set_id} starting work")
        
        while not self.cancelled:
            try:
                # Get next question from queue (non-blocking)
                try:
                    row_idx, question_text = await asyncio.wait_for(
                        work_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    # No more work available
                    break
                
                # Announce which question this agent set is working on
                agent_msg = f"Agent Set {agent_set_id} working on question \"{question_text[:50]}{'...' if len(question_text) > 50 else ''}\""
                logger.info(f"📋 {agent_msg}")
                if self.reasoning_callback:
                    self.reasoning_callback(agent_msg)
                
                # Mark cell as working
                async with self._state_lock:
                    self._emit_event('CELL_WORKING', {
                        'sheet_index': sheet_idx,
                        'row_index': row_idx
                    })
                    sheet_data.mark_working(row_idx)
                
                # Create Question object
                question = Question(
                    text=question_text,
                    context=context,
                    char_limit=char_limit,
                    max_retries=max_retries
                )
                
                # Process with agents
                try:
                    # Create reasoning callback that prefixes with agent set ID
                    def reasoning_callback(msg):
                        reasoning_msg = f"Agent Set {agent_set_id}: {msg}"
                        logger.info(f"🧠 {reasoning_msg}")
                        if self.reasoning_callback:
                            self.reasoning_callback(reasoning_msg)
                    
                    # Create progress callback
                    def progress_callback(agent, msg, progress):
                        progress_msg = f"Agent Set {agent_set_id} - {agent}: {msg} ({progress:.1%})"
                        logger.info(f"📊 {progress_msg}")
                    
                    result = await coordinator.process_question(
                        question,
                        progress_callback,
                        reasoning_callback,
                        self.agent_conversation_callback
                    )
                    
                    async with self._state_lock:
                        if result.success and result.answer:
                            # Success
                            answer_text = result.answer.content
                            sheet_data.mark_completed(row_idx, answer_text)
                            
                            logger.info(f"✅ Agent Set {agent_set_id} completed question at row {row_idx + 1}")
                            
                            # Display formatted agent conversation if callback provided
                            if self.agent_conversation_callback and result.answer.agent_reasoning:
                                self.agent_conversation_callback(
                                    result.answer.agent_reasoning,
                                    result.answer.documentation_links
                                )
                            
                            self._emit_event('CELL_COMPLETED', {
                                'sheet_index': sheet_idx,
                                'row_index': row_idx,
                                'answer': answer_text
                            })
                            
                            processed_count += 1
                        else:
                            # Failed
                            error_text = f"ERROR: {result.error_message or 'Processing failed'}"
                            sheet_data.mark_completed(row_idx, error_text)
                            
                            logger.error(f"❌ Agent Set {agent_set_id} failed question at row {row_idx + 1}: {result.error_message}")
                            
                            self._emit_event('CELL_COMPLETED', {
                                'sheet_index': sheet_idx,
                                'row_index': row_idx,
                                'answer': error_text
                            })
                            
                            failed_count += 1
                
                except Exception as e:
                    # Exception during processing
                    async with self._state_lock:
                        error_text = f"ERROR: {str(e)}"
                        sheet_data.mark_completed(row_idx, error_text)
                        
                        self._emit_event('CELL_COMPLETED', {
                            'sheet_index': sheet_idx,
                            'row_index': row_idx,
                            'answer': error_text
                        })
                        
                        failed_count += 1
                        logger.error(f"❌ Agent Set {agent_set_id} exception at row {row_idx + 1}: {e}")
                
            except Exception as e:
                logger.error(f"❌ Agent Set {agent_set_id} worker error: {e}", exc_info=True)
                break
        
        logger.info(f"🏁 Agent Set {agent_set_id} finished: {processed_count} processed, {failed_count} failed")
        return processed_count, failed_count
    
    def cancel_processing(self) -> None:
        """Cancel the current processing operation."""
        self.cancelled = True
        logger.info("Parallel Excel processing cancellation requested")
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit UI update event to queue.
        
        Args:
            event_type: Type of event to emit
            payload: Event payload data
        """
        try:
            self.ui_queue.put_event(event_type, payload, block=False)
        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {e}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'cancelled': self.cancelled,
            'queue_size': self.ui_queue.qsize() if self.ui_queue else 0
        }