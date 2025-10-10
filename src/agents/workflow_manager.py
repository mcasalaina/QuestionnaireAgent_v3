"""Multi-agent workflow orchestration using Microsoft Agent Framework."""

import logging
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable
from agent_framework import WorkflowBuilder, Workflow
from agent_framework_azure_ai import AzureAIAgentClient
from utils.data_types import (
    Question, Answer, ProcessingResult, AgentStep, 
    ValidationStatus, HealthStatus
)
from utils.logger import log_workflow_progress, create_span
from utils.exceptions import (
    AgentExecutionError, AzureServiceError, MaxRetriesExceededError,
    ValidationTimeoutError, AuthenticationError, ResourceCreationError
)
from utils.azure_auth import foundry_agent_session
from agents.question_answerer import QuestionAnswererExecutor
from agents.answer_checker import AnswerCheckerExecutor
from agents.link_checker import LinkCheckerExecutor


logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Orchestrates multi-agent workflow using Microsoft Agent Framework."""
    
    def __init__(self, azure_client: AzureAIAgentClient, bing_connection_id: str):
        """Initialize the agent coordinator.
        
        Args:
            azure_client: Azure AI Agent client for creating agents.
            bing_connection_id: Bing search connection ID for web grounding.
        """
        self.azure_client = azure_client
        self.bing_connection_id = bing_connection_id
        self.workflow: Optional[Workflow] = None
        self.executors_created = False
        
        # Agent executors
        self.question_answerer: Optional[QuestionAnswererExecutor] = None
        self.answer_checker: Optional[AnswerCheckerExecutor] = None
        self.link_checker: Optional[LinkCheckerExecutor] = None
    
    async def create_agents(self) -> None:
        """Initialize the three specialized agents with Azure AI Foundry.
        
        Raises:
            AuthenticationError: If Azure credentials are invalid.
            ResourceCreationError: If agent creation fails.
        """
        try:
            logger.info("Creating specialized agent executors...")
            
            # Create the three agent executors
            self.question_answerer = QuestionAnswererExecutor(
                azure_client=self.azure_client,
                bing_connection_id=self.bing_connection_id
            )
            
            self.answer_checker = AnswerCheckerExecutor(
                azure_client=self.azure_client
            )
            
            self.link_checker = LinkCheckerExecutor(
                azure_client=self.azure_client
            )
            
            # Build the sequential workflow
            self.workflow = (
                WorkflowBuilder()
                .add_edge(self.question_answerer, self.answer_checker)
                .add_edge(self.answer_checker, self.link_checker)
                .set_start_executor(self.question_answerer)
                .build()
            )
            
            self.executors_created = True
            logger.info("Agent executors and workflow created successfully")
            
        except Exception as e:
            error_message = f"Failed to create agent executors: {str(e)}"
            logger.error(error_message, exc_info=True)
            raise ResourceCreationError(error_message) from e
    
    async def process_question(
        self, 
        question: Question,
        progress_callback: Callable[[str, str, float], None]
    ) -> ProcessingResult:
        """Execute multi-agent workflow for single question.
        
        Args:
            question: Question with context and limits.
            progress_callback: Function to report workflow progress.
            
        Returns:
            ProcessingResult with validated answer or failure details.
            
        Raises:
            AzureServiceError: If agent services are unavailable.
            ValidationTimeoutError: If validation exceeds time limits.
            MaxRetriesExceededError: If retry limit reached without valid answer.
        """
        if not self.executors_created or not self.workflow:
            await self.create_agents()
        
        start_time = time.time()
        retry_count = 0
        
        with create_span("question_processing_workflow", question_text=question.text):
            while retry_count < question.max_retries:
                try:
                    log_workflow_progress(1, 3, f"Starting workflow attempt {retry_count + 1}")
                    progress_callback("workflow", f"Processing attempt {retry_count + 1}...", 0.0)
                    
                    # Execute the workflow
                    events = await self.workflow.run(question)
                    
                    # Get the final result
                    outputs = events.get_outputs()
                    if not outputs:
                        raise AgentExecutionError("No output received from workflow")
                    
                    workflow_result = outputs[0]
                    
                    # Check if processing was successful
                    if workflow_result.get("processing_complete", False):
                        validation_status = workflow_result.get("validation_status", ValidationStatus.REJECTED_CONTENT)
                        
                        if validation_status == ValidationStatus.APPROVED:
                            # Success - create approved answer
                            processing_time = time.time() - start_time
                            
                            answer = Answer(
                                content=workflow_result["raw_answer"],
                                sources=workflow_result.get("answer_sources", []),
                                agent_reasoning=workflow_result.get("agent_steps", []),
                                validation_status=validation_status,
                                retry_count=retry_count,
                                documentation_links=workflow_result.get("documentation_links", [])
                            )
                            
                            progress_callback("workflow", "Processing completed successfully!", 1.0)
                            
                            return ProcessingResult(
                                success=True,
                                answer=answer,
                                processing_time=processing_time,
                                questions_processed=1,
                                questions_failed=0
                            )
                        else:
                            # Answer was rejected - retry if attempts remaining
                            retry_count += 1
                            if retry_count >= question.max_retries:
                                break
                            
                            # Log rejection reason and retry
                            rejection_reason = workflow_result.get("validation_feedback", "Unknown rejection reason")
                            logger.info(f"Answer rejected (attempt {retry_count}): {rejection_reason}")
                            progress_callback("workflow", f"Answer rejected, retrying... ({retry_count}/{question.max_retries})", 0.2)
                            
                            # Brief delay before retry
                            await asyncio.sleep(1.0)
                            continue
                    else:
                        # Workflow error occurred
                        error = workflow_result.get("error")
                        if error:
                            raise error
                        else:
                            raise AgentExecutionError("Workflow completed but processing was not successful")
                
                except (AzureServiceError, ValidationTimeoutError) as e:
                    # These errors should not trigger retries
                    processing_time = time.time() - start_time
                    progress_callback("workflow", f"Processing failed: {str(e)}", 0.0)
                    
                    return ProcessingResult(
                        success=False,
                        error_message=str(e),
                        processing_time=processing_time,
                        questions_processed=0,
                        questions_failed=1
                    )
                
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"Workflow attempt {retry_count} failed: {e}")
                    
                    if retry_count >= question.max_retries:
                        break
                    
                    progress_callback("workflow", f"Attempt failed, retrying... ({retry_count}/{question.max_retries})", 0.1)
                    await asyncio.sleep(1.0)
            
            # All retries exhausted
            processing_time = time.time() - start_time
            error_message = f"Maximum retry attempts ({question.max_retries}) reached without valid answer"
            progress_callback("workflow", error_message, 0.0)
            
            return ProcessingResult(
                success=False,
                error_message=error_message,
                processing_time=processing_time,
                questions_processed=0,
                questions_failed=1
            )
    
    async def process_batch(
        self, 
        questions: List[Question],
        progress_callback: Callable[[str, str, float], None]
    ) -> List[ProcessingResult]:
        """Execute multi-agent workflow for multiple questions.
        
        Args:
            questions: List of questions to process.
            progress_callback: Function to report batch progress.
            
        Returns:
            List of ProcessingResult for each question.
            
        Raises:
            AzureServiceError: If agent services become unavailable during batch.
        """
        if not self.executors_created or not self.workflow:
            await self.create_agents()
        
        results = []
        total_questions = len(questions)
        
        logger.info(f"Starting batch processing of {total_questions} questions")
        
        for i, question in enumerate(questions):
            try:
                # Update progress
                progress = i / total_questions
                progress_callback("batch", f"Processing question {i+1}/{total_questions}", progress)
                
                # Create a progress callback for this individual question
                def individual_progress(agent: str, message: str, agent_progress: float):
                    # Combine batch progress with individual question progress
                    overall_progress = progress + (agent_progress / total_questions)
                    progress_callback(agent, message, overall_progress)
                
                # Process the individual question
                result = await self.process_question(question, individual_progress)
                results.append(result)
                
                logger.info(f"Question {i+1}/{total_questions} completed: {'SUCCESS' if result.success else 'FAILED'}")
                
            except Exception as e:
                logger.error(f"Failed to process question {i+1}: {e}")
                
                # Create failed result
                failed_result = ProcessingResult(
                    success=False,
                    error_message=str(e),
                    processing_time=0.0,
                    questions_processed=0,
                    questions_failed=1
                )
                results.append(failed_result)
        
        # Final progress update
        progress_callback("batch", f"Batch processing complete: {total_questions} questions processed", 1.0)
        
        # Log batch summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        logger.info(f"Batch processing complete: {successful} successful, {failed} failed")
        
        return results
    
    async def health_check(self) -> HealthStatus:
        """Verify Azure AI Foundry connectivity and agent availability.
        
        Returns:
            HealthStatus with service availability details.
        """
        health_status = HealthStatus()
        
        try:
            # Test Azure connectivity by creating a simple test workflow
            if not self.executors_created or not self.workflow:
                await self.create_agents()
            
            health_status.azure_connectivity = True
            health_status.authentication_valid = True
            health_status.configuration_valid = True
            health_status.agent_services_available = True
            
            logger.info("Health check passed: All systems operational")
            
        except AuthenticationError as e:
            health_status.authentication_valid = False
            health_status.error_details.append(f"Authentication failed: {str(e)}")
            logger.warning(f"Health check failed: Authentication error - {e}")
            
        except AzureServiceError as e:
            health_status.azure_connectivity = False
            health_status.error_details.append(f"Azure service error: {str(e)}")
            logger.warning(f"Health check failed: Azure service error - {e}")
            
        except Exception as e:
            health_status.agent_services_available = False
            health_status.error_details.append(f"Agent service error: {str(e)}")
            logger.warning(f"Health check failed: General error - {e}")
        
        return health_status
    
    async def cleanup_agents(self) -> None:
        """Clean up Azure AI agent resources using FoundryAgentSession."""
        try:
            # Clean up individual executors
            if self.question_answerer:
                await self.question_answerer.cleanup()
            
            if self.answer_checker:
                await self.answer_checker.cleanup()
            
            if self.link_checker:
                await self.link_checker.cleanup()
            
            # Reset state
            self.workflow = None
            self.executors_created = False
            self.question_answerer = None
            self.answer_checker = None
            self.link_checker = None
            
            logger.info("Agent coordinator cleanup completed")
            
        except Exception as e:
            logger.warning(f"Error during agent cleanup: {e}")


async def create_agent_coordinator(azure_client: AzureAIAgentClient, bing_connection_id: str) -> AgentCoordinator:
    """Create and initialize an agent coordinator.
    
    Args:
        azure_client: Azure AI Agent client.
        bing_connection_id: Bing search connection ID.
        
    Returns:
        Initialized AgentCoordinator instance.
    """
    coordinator = AgentCoordinator(azure_client, bing_connection_id)
    await coordinator.create_agents()
    return coordinator