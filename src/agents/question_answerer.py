"""Question Answerer agent executor using Microsoft Agent Framework."""

import logging
import time
import asyncio
from typing import Any, Dict, Optional
from agent_framework import Executor, handler, WorkflowContext, ChatAgent, ChatMessage, Role
from agent_framework_azure_ai import AzureAIAgentClient
from azure.core.exceptions import ResourceNotFoundError
from utils.data_types import Question, AgentStep, AgentType, StepStatus
from utils.logger import log_agent_step, create_span
from utils.exceptions import AgentExecutionError, AzureServiceError


logger = logging.getLogger(__name__)


class QuestionAnswererExecutor(Executor):
    """Executor for the Question Answerer agent in the multi-agent workflow."""
    
    def __init__(self, azure_client: AzureAIAgentClient, bing_connection_id: str):
        """Initialize the Question Answerer executor.
        
        Args:
            azure_client: Azure AI Agent client instance.
            bing_connection_id: Bing search connection for web grounding.
        """
        super().__init__(id="question_answerer")
        self.azure_client = azure_client
        self.bing_connection_id = bing_connection_id
        self.agent: Optional[ChatAgent] = None
    
    async def _get_agent(self) -> ChatAgent:
        """Get or create the question answerer agent."""
        if self.agent is None:
            self.agent = ChatAgent(
                chat_client=self.azure_client,
                instructions="""You are an expert Question Answerer specializing in Microsoft Azure AI services and technologies.

Your role is to provide comprehensive, accurate answers to technical questions about Azure AI. Use web search to find current, authoritative information.

REQUIREMENTS:
- Provide detailed, technically accurate answers
- Include relevant documentation URLs from official Microsoft sources when possible
- Focus on current, up-to-date information about Azure AI services
- Be comprehensive but stay within character limits
- Include specific examples and best practices where helpful
- Always verify information using web search for the latest details

FORMATTING REQUIREMENTS:
- Write in PLAIN TEXT ONLY - no markdown, no bold, no italics, no headers
- Do NOT use **bold**, *italics*, `code blocks`, or # headers
- Do NOT use bullet points (-), numbered lists (1. 2. 3.), or any special formatting
- Write in complete sentences as natural prose paragraphs
- Your answer must end with a period and contain only complete sentences
- Do NOT include closing phrases like 'Learn more:', 'References:', 'For more information, see:', etc.
- Put documentation URLs at the end, separated by newlines with no other text

When answering questions:
1. Search for the most current information
2. Prioritize official Microsoft documentation
3. Include practical examples where relevant (in plain text)
4. Provide clear, well-structured explanations in prose format
5. Include relevant documentation links at the end

Remember to stay focused on Azure AI technologies and provide authoritative, helpful information in plain text format only."""
            )
        return self.agent
    
    @handler
    async def handle(self, question: Question, ctx: WorkflowContext[dict]) -> None:
        """Handle question answering with web grounding.
        
        Args:
            question: The question to answer.
            ctx: Workflow context for passing data between agents.
        """
        start_time = time.time()
        
        with create_span("question_answerer_execution", question_text=question.text):
            try:
                log_agent_step(
                    "question_answerer",
                    f"Starting question analysis: '{question.text[:50]}...'",
                    "started"
                )
                
                # Get the agent
                agent = await self._get_agent()
                
                # Create the question message with context
                question_prompt = self._build_question_prompt(question)
                messages = [ChatMessage(role=Role.USER, text=question_prompt)]
                
                # Run the agent to get the answer
                response = await agent.run(messages)
                answer_content = response.text
                
                execution_time = time.time() - start_time
                
                # Extract sources from the answer
                sources = self._extract_sources(answer_content)
                
                # Store result in context for next agent
                result_data = {
                    "question": question,
                    "raw_answer": answer_content,
                    "answer_sources": sources,
                    "agent_steps": [
                        AgentStep(
                            agent_name=AgentType.QUESTION_ANSWERER,
                            input_data=question.text,
                            output_data=answer_content,
                            execution_time=execution_time,
                            status=StepStatus.SUCCESS
                        )
                    ]
                }
                
                await ctx.send_message(result_data)
                
                log_agent_step(
                    "question_answerer",
                    f"Generated answer ({len(answer_content)} chars)",
                    "completed",
                    execution_time
                )
                
                logger.info(f"Question Answerer completed successfully in {execution_time:.2f}s")
                
            except ResourceNotFoundError as e:
                execution_time = time.time() - start_time
                error_message = (
                    "Azure resource not found. Please check your configuration:\\n"
                    "- Azure AI Projects endpoint is correct\\n"
                    "- Model deployment exists and is accessible\\n"
                    "- Your account has proper permissions\\n"
                    f"Original error: {str(e)}"
                )
                
                log_agent_step(
                    "question_answerer",
                    error_message,
                    "failed",
                    execution_time
                )
                
                logger.error(error_message, exc_info=True)
                
                # Store error in context
                error_data = {
                    "error": AzureServiceError(error_message),
                    "agent_steps": [
                        AgentStep(
                            agent_name=AgentType.QUESTION_ANSWERER,
                            input_data=question.text if question else "Unknown question",
                            output_data="",
                            execution_time=execution_time,
                            status=StepStatus.FAILURE,
                            error_message=error_message
                        )
                    ]
                }
                
                await ctx.send_message(error_data)
                raise AzureServiceError(error_message) from e
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_message = f"Question Answerer failed: {str(e)}"
                
                log_agent_step(
                    "question_answerer",
                    error_message,
                    "failed",
                    execution_time
                )
                
                logger.error(error_message, exc_info=True)
                
                # Store error in context
                error_data = {
                    "error": AgentExecutionError(error_message),
                    "agent_steps": [
                        AgentStep(
                            agent_name=AgentType.QUESTION_ANSWERER,
                            input_data=question.text if question else "Unknown question",
                            output_data="",
                            execution_time=execution_time,
                            status=StepStatus.FAILURE,
                            error_message=error_message
                        )
                    ]
                }
                
                await ctx.send_message(error_data)
                raise AgentExecutionError(error_message) from e
    
    def _build_question_prompt(self, question: Question) -> str:
        """Build the prompt for the Question Answerer agent.
        
        Args:
            question: The question object with context and constraints.
            
        Returns:
            Formatted prompt for the agent.
        """
        prompt = f"""Please answer the following question about {question.context}:

Question: {question.text}

Requirements:
- Maximum {question.char_limit} characters in your response
- Include relevant documentation URLs from official Microsoft sources
- Provide accurate, up-to-date information
- Use web search to verify current details
- Include practical examples where helpful

IMPORTANT - FORMATTING:
- Write ONLY in plain text with NO markdown formatting
- NO **bold**, *italics*, `code`, # headers, bullet points, or numbered lists
- Write as natural prose in complete sentences
- End answer with a period
- Place documentation URLs at the end, separated by newlines

Please provide a comprehensive answer in plain text with supporting documentation links."""

        return prompt
    
    def _extract_sources(self, answer_content: str) -> list[str]:
        """Extract URL sources from the answer content.
        
        Args:
            answer_content: The generated answer text.
            
        Returns:
            List of URLs found in the answer.
        """
        import re
        
        # Find URLs in the answer content
        url_pattern = r'https?://[^\s\)]+(?:[^\s\.\,\)\>]*)'
        urls = re.findall(url_pattern, answer_content)
        
        # Clean up URLs (remove trailing punctuation)
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation
            url = url.rstrip('.,;:!?)')
            if url and url not in cleaned_urls:
                cleaned_urls.append(url)
        
        logger.debug(f"Extracted {len(cleaned_urls)} sources from answer")
        return cleaned_urls
    
    async def cleanup(self) -> None:
        """Clean up resources used by the executor."""
        if self.agent:
            # Agent cleanup is handled automatically by the framework
            logger.debug("Question Answerer executor cleanup completed")
            self.agent = None