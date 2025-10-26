"""Answer Checker agent executor using Microsoft Agent Framework."""

import logging
import time
import asyncio
from typing import Any, Dict, Optional
from agent_framework import Executor, handler, WorkflowContext, ChatAgent, ChatMessage, Role
from agent_framework_azure_ai import AzureAIAgentClient
from utils.data_types import (
    Question, AgentStep, AgentType, StepStatus, ValidationStatus
)
from utils.logger import log_agent_step, create_span
from utils.exceptions import AgentExecutionError, AzureServiceError


logger = logging.getLogger(__name__)


class AnswerCheckerExecutor(Executor):
    """Executor for the Answer Checker agent in the multi-agent workflow."""
    
    def __init__(self, azure_client: AzureAIAgentClient):
        """Initialize the Answer Checker executor.
        
        Args:
            azure_client: Azure AI Agent client instance.
        """
        super().__init__(id="answer_checker")
        self.azure_client = azure_client
        self.agent: Optional[ChatAgent] = None
    
    async def _get_agent(self) -> ChatAgent:
        """Get or create the answer checker agent."""
        if self.agent is None:
            self.agent = ChatAgent(
                chat_client=self.azure_client,
                instructions="""You are an expert Answer Checker specializing in validating technical content about Microsoft Azure AI services.

Your role is to validate the quality, accuracy, and completeness of generated answers. You must evaluate answers against strict quality standards.

VALIDATION CRITERIA:
1. Accuracy: Is the information factually correct and up-to-date?
2. Completeness: Does it adequately answer the question?
3. Relevance: Is the content directly related to the question?
4. Character Limits: Is it within specified limits?
5. Quality: Is it well-structured and professionally written?
6. Sources: Are included links relevant and from authoritative sources?
7. Formatting: Is the answer in PLAIN TEXT with NO markdown formatting?

FORMATTING VALIDATION:
- REJECT if answer contains **bold**, *italics*, `code blocks`, or # headers
- REJECT if answer uses bullet points (-), numbered lists (1. 2. 3.), or special markdown
- REJECT if answer has closing phrases like "Learn more:", "References:", "For more information:", etc.
- APPROVE only if answer is written in natural prose with complete sentences
- Answer should end with a period (after prose, before any URLs)

RESPONSE FORMAT:
You MUST start your response with either "APPROVED:" or "REJECTED:" followed by your reasoning.

If APPROVED: 
- Explain why the answer meets quality standards
- Highlight strengths and accuracy of the content
- Confirm it's in plain text format

If REJECTED:
- Specify exactly what needs to be improved
- Be specific about factual errors, missing information, quality issues, or formatting problems
- Provide clear guidance for improvement

IMPORTANT:
- Be thorough but decisive in your evaluation
- Prioritize accuracy, completeness, and plain text formatting
- Reject answers that are incomplete, inaccurate, poorly structured, or use markdown
- Only approve answers that truly meet professional standards AND are in plain text"""
            )
        return self.agent
    
    @handler
    async def handle(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        """Handle answer validation and quality checking.
        
        Args:
            data: Context data containing the question and generated answer.
            ctx: Workflow context for passing data between agents.
        """
        start_time = time.time()
        
        # Get data from previous agent
        question = data.get("question")
        raw_answer = data.get("raw_answer")
        
        logger.info(f"🔍 ANSWER CHECKER AGENT CALLED")
        logger.info(f"📋 Validating answer for question: '{question.text if question else 'Unknown'}'")
        logger.info(f"📄 Answer to validate ({len(raw_answer) if raw_answer else 0} chars): {raw_answer[:150] if raw_answer else 'None'}...")
        
        if not question or not raw_answer:
            logger.error("❌ Missing question or answer data from previous agent")
            raise AgentExecutionError("Missing question or answer data from previous agent")
        
        with create_span("answer_checker_execution", question_text=question.text):
            try:
                logger.info(f"🚀 Answer Checker starting validation for question: '{question.text[:100]}...'")
                log_agent_step(
                    "answer_checker",
                    f"Validating answer quality (answer length: {len(raw_answer)} chars)",
                    "started"
                )
                
                # Get the agent
                logger.info("🔧 Getting Answer Checker agent instance...")
                agent = await self._get_agent()
                logger.info("✅ Answer Checker agent retrieved successfully")
                
                # Create validation prompt
                validation_prompt = self._build_validation_prompt(question, raw_answer)
                messages = [ChatMessage(role=Role.USER, text=validation_prompt)]
                logger.info(f"📝 Built validation prompt ({len(validation_prompt)} chars), sending to agent...")
                logger.info(f"🎯 Validation criteria: accuracy, completeness, {question.char_limit} char limit, plain text format")
                
                # Run the agent to get validation result
                logger.info("🔍 Calling agent.run() to get validation result...")
                response = await agent.run(messages)
                validation_result = response.text
                logger.info(f"📋 Answer Checker returned validation ({len(validation_result)} chars): {validation_result[:200]}...")
                
                execution_time = time.time() - start_time
                
                # Parse validation decision
                validation_status, feedback = self._parse_validation_response(validation_result)
                logger.info(f"🎯 Parsed validation result: {validation_status.value}")
                logger.info(f"💬 Validation feedback: {feedback[:200]}...")
                
                if validation_status == ValidationStatus.APPROVED:
                    logger.info("✅ ANSWER APPROVED - meets all quality standards")
                else:
                    logger.info(f"❌ ANSWER REJECTED - reason: {validation_status.value}")
                
                # Update context with validation results
                updated_data = data.copy()
                updated_data["validation_status"] = validation_status
                updated_data["validation_feedback"] = feedback
                updated_data["checked_answer"] = raw_answer if validation_status == ValidationStatus.APPROVED else None
                updated_data["processing_complete"] = True  # Mark workflow as complete
                
                # Add agent step to history
                agent_steps = updated_data.get("agent_steps", [])
                agent_steps.append(
                    AgentStep(
                        agent_name=AgentType.ANSWER_CHECKER,
                        input_data=f"Question: {question.text}\nAnswer: {raw_answer[:200]}...",
                        output_data=validation_result,
                        execution_time=execution_time,
                        status=StepStatus.SUCCESS
                    )
                )
                updated_data["agent_steps"] = agent_steps
                
                # Send the result to workflow context AND set as output
                await ctx.send_message(updated_data)
                
                # IMPORTANT: Yield the final output for the workflow
                await ctx.yield_output(updated_data)
                
                logger.info(f"📤 Answer Checker sending result data to workflow: {list(updated_data.keys())}")
                logger.info(f"🏁 Answer Checker completed: {validation_status.value} in {execution_time:.2f}s")
                
                log_agent_step(
                    "answer_checker",
                    f"Validation complete: {validation_status.value}",
                    "completed",
                    execution_time
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_message = f"Answer Checker failed: {str(e)}"
                
                log_agent_step(
                    "answer_checker",
                    error_message,
                    "failed",
                    execution_time
                )
                
                logger.error(error_message, exc_info=True)
                
                # Add failed step to history and pass error forward
                error_data = data.copy()
                agent_steps = error_data.get("agent_steps", [])
                agent_steps.append(
                    AgentStep(
                        agent_name=AgentType.ANSWER_CHECKER,
                        input_data=raw_answer[:100] if raw_answer else "No answer",
                        output_data="",
                        execution_time=execution_time,
                        status=StepStatus.FAILURE,
                        error_message=error_message
                    )
                )
                error_data["agent_steps"] = agent_steps
                error_data["error"] = AgentExecutionError(error_message)
                
                await ctx.send_message(error_data)
                
                # Yield error output for workflow
                await ctx.yield_output(error_data)
                
                raise AgentExecutionError(error_message) from e
    
    def _build_validation_prompt(self, question: Question, answer: str) -> str:
        """Build the validation prompt for the Answer Checker agent.
        
        Args:
            question: The original question object.
            answer: The generated answer to validate.
            
        Returns:
            Formatted validation prompt.
        """
        prompt = f"""Please validate the following answer for accuracy and quality:

ORIGINAL QUESTION:
{question.text}

GENERATED ANSWER:
{answer}

VALIDATION REQUIREMENTS:
- Context: {question.context}
- Character Limit: {question.char_limit} characters
- Must be accurate, complete, and relevant
- Should include authoritative sources
- Must be professionally written
- MUST be in plain text format with NO markdown formatting

FORMATTING CHECK:
- Verify answer has NO **bold**, *italics*, `code`, # headers
- Verify answer has NO bullet points (-), numbered lists (1. 2. 3.)
- Verify answer has NO closing phrases like "Learn more:", "References:", etc.
- Verify answer is written as natural prose in complete sentences
- REJECT if any markdown or special formatting is present

RESPONSE FORMAT:
Start with either "APPROVED:" or "REJECTED:" followed by your detailed reasoning.

Provide your validation decision:"""

        return prompt
    
    def _parse_validation_response(self, validation_result: str) -> tuple[ValidationStatus, str]:
        """Parse the validation response to determine status and feedback.
        
        Args:
            validation_result: The raw validation response from the agent.
            
        Returns:
            Tuple of (validation_status, feedback_message).
        """
        try:
            validation_upper = validation_result.upper()
            
            if validation_result.startswith("APPROVED:"):
                return ValidationStatus.APPROVED, validation_result[9:].strip()
            elif validation_result.startswith("REJECTED:"):
                # Determine rejection reason based on content
                rejection_text = validation_result[9:].strip().lower()
                if any(keyword in rejection_text for keyword in ["link", "url", "source", "documentation"]):
                    return ValidationStatus.REJECTED_LINKS, validation_result[9:].strip()
                else:
                    return ValidationStatus.REJECTED_CONTENT, validation_result[9:].strip()
            elif "APPROVED" in validation_upper:
                return ValidationStatus.APPROVED, validation_result
            elif "REJECTED" in validation_upper:
                # Default to content rejection
                return ValidationStatus.REJECTED_CONTENT, validation_result
            else:
                # Ambiguous response - default to rejection for safety
                logger.warning(f"Ambiguous validation response: {validation_result[:100]}...")
                return ValidationStatus.REJECTED_CONTENT, f"Unclear validation result: {validation_result}"
                
        except Exception as e:
            logger.error(f"Failed to parse validation response: {e}")
            return ValidationStatus.REJECTED_CONTENT, f"Failed to parse validation: {str(e)}"
    
    async def cleanup(self) -> None:
        """Clean up resources used by the executor."""
        if self.agent:
            # Agent cleanup is handled automatically by the framework
            logger.debug("Answer Checker executor cleanup completed")
            self.agent = None