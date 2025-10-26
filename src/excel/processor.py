"""Excel workbook processing with multi-agent workflow."""

import asyncio
import time
from typing import Dict, Any
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
        agent_conversation_callback = None
    ):
        """Initialize processor.
        
        Args:
            agent_coordinator: Initialized AgentCoordinator instance
            ui_update_queue: Thread-safe queue for UI updates
            reasoning_callback: Optional callback for agent reasoning updates
            agent_conversation_callback: Optional callback for displaying formatted agent conversation
        """
        self.agent_coordinator = agent_coordinator
        self.ui_queue = ui_update_queue
        self.reasoning_callback = reasoning_callback
        self.agent_conversation_callback = agent_conversation_callback
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
                        
                        # Create progress callback that logs and optionally updates UI
                        def progress_callback(agent, msg, progress):
                            progress_msg = f"Agent progress - {agent}: {msg} ({progress:.1%})"
                            logger.info(f"📊 {progress_msg}")
                        
                        # Create reasoning callback that logs and updates UI
                        def reasoning_callback(msg):
                            reasoning_msg = f"Question {row_idx + 1}: {msg}"
                            logger.info(f"🧠 Agent reasoning: {reasoning_msg}")
                            if self.reasoning_callback:
                                self.reasoning_callback(reasoning_msg)
                        
                        logger.info(f"🚀 Starting agent processing for question {row_idx + 1}...")
                        result = await self.agent_coordinator.process_question(
                            question,
                            progress_callback,
                            reasoning_callback
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