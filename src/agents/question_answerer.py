"""Question Answerer agent executor using Azure AI Agent Framework."""

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
            # Create the agent and track its ID for cleanup
            try:
                # Create ChatAgent directly with Azure client
                self.agent = ChatAgent(
                    chat_client=self.azure_client,
                    name="Question Answerer",
                    instructions="""You are an expert Question Answerer who provides comprehensive, accurate answers to technical questions. Use web search to find current, authoritative information.

REQUIREMENTS:
- Provide detailed, technically accurate answers
- Include relevant documentation URLs from authoritative sources when possible
- Focus on current, up-to-date information
- Be comprehensive but stay within character limits
- Include specific examples and best practices where helpful
- Always verify information using web search for the latest details

CRITICAL - RESPONSE STYLE:
- NEVER refer to yourself or your capabilities (e.g., "I am an AI assistant", "As an AI", "I can help you")
- NEVER use first-person language or self-referential statements
- NEVER include introductory phrases about who or what you are
- Provide ONLY the direct answer to the question without any preamble
- Start your response immediately with the answer content

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
2. Use authoritative documentation and official sources
3. Include practical examples where relevant (in plain text)
4. Provide clear, well-structured explanations in prose format
5. Include relevant documentation links at the end

Provide authoritative, helpful information in plain text format only."""
                )
                
            except Exception as e:
                logger.error(f"Failed to create Question Answerer agent: {e}")
                raise
                
        return self.agent
    
    @handler
    async def handle(self, question: Question, ctx: WorkflowContext[dict]) -> None:
        """Handle question answering with web grounding.
        
        Args:
            question: The question to answer.
            ctx: Workflow context for passing data between agents.
        """
        start_time = time.time()
        
        logger.info(f"🤖 QUESTION ANSWERER AGENT CALLED")
        logger.info(f"📋 Input Question: '{question.text}'")
        logger.info(f"🎯 Context: {question.context}")
        logger.info(f"📏 Character Limit: {question.char_limit}")
        logger.info(f"🔄 Max Retries: {question.max_retries}")
        
        with create_span("question_answerer_execution", question_text=question.text):
            try:
                logger.info(f"🚀 Question Answerer starting: '{question.text[:100]}...'")
                log_agent_step(
                    "question_answerer",
                    f"Starting question analysis: '{question.text[:50]}...'",
                    "started"
                )
                
                # Get the agent
                logger.info("🔧 Getting Question Answerer agent instance...")
                agent = await self._get_agent()
                logger.info("✅ Question Answerer agent retrieved successfully")
                
                # Create the question message with context
                question_prompt = self._build_question_prompt(question)
                messages = [ChatMessage(role=Role.USER, text=question_prompt)]
                logger.info(f"📝 Built question prompt ({len(question_prompt)} chars), sending to agent...")
                logger.info(f"💬 Prompt preview: {question_prompt[:200]}...")
                
                # Run the agent to get the answer
                logger.info("🎯 Calling agent.run() to get answer...")
                response = await agent.run(messages)
                raw_answer_with_urls = response.text
                logger.info(f"📄 Agent returned response ({len(raw_answer_with_urls)} chars)")
                logger.info(f"🔍 Answer preview: {raw_answer_with_urls[:150]}...")
                
                execution_time = time.time() - start_time
                
                # Extract sources from the answer
                sources = self._extract_sources(raw_answer_with_urls)
                logger.info(f"🔗 Extracted {len(sources)} sources from answer")
                if sources:
                    for i, source in enumerate(sources[:3]):  # Show first 3 sources
                        logger.info(f"   Source {i+1}: {source}")
                
                # Separate URLs from answer content - Answer Checker should check clean answer
                clean_answer = self._remove_urls_from_answer(raw_answer_with_urls)
                
                # Store result in context for next agent
                # raw_answer is the clean answer without URLs (for Answer Checker)
                # answer_sources contains the extracted URLs (for Link Checker)
                result_data = {
                    "question": question,
                    "raw_answer": clean_answer,
                    "answer_sources": sources,
                    "agent_steps": [
                        AgentStep(
                            agent_name=AgentType.QUESTION_ANSWERER,
                            input_data=question.text,
                            output_data=clean_answer,
                            execution_time=execution_time,
                            status=StepStatus.SUCCESS
                        )
                    ]
                }
                
                await ctx.send_message(result_data)
                
                logger.info(f"📤 Question Answerer sending result data to next agent: {list(result_data.keys())}")
                logger.info(f"✅ Question Answerer completed successfully in {execution_time:.2f}s")
                
                log_agent_step(
                    "question_answerer",
                    f"Generated answer ({len(clean_answer)} chars)",
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
- Include relevant documentation URLs from authoritative sources
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
    
    def _remove_urls_from_answer(self, answer_content: str) -> str:
        """Remove URLs from answer content.
        
        This separates documentation URLs from the answer prose so that:
        - Answer Checker validates the clean answer text
        - Link Checker validates the extracted URLs
        - UI displays answer and documentation separately
        
        Args:
            answer_content: The raw answer text that may contain URLs at the end.
            
        Returns:
            Clean answer text without trailing URLs.
        """
        import re
        
        # URL pattern for detection
        url_pattern = r'https?://[^\s]+'
        
        # Split content into lines
        lines = answer_content.split('\n')
        
        # Find the first line that contains only a URL (not embedded in prose)
        url_start_index = None
        for i, line in enumerate(lines):
            if re.search(url_pattern, line.strip()):
                # Check if this line is mostly/only a URL (not embedded in prose)
                line_without_urls = re.sub(url_pattern, '', line).strip()
                # If after removing URLs, the line is empty or just punctuation, it's a URL-only line
                if not line_without_urls or all(c in '.,;:!? \t' for c in line_without_urls):
                    url_start_index = i
                    break
        
        # If we found URL-only lines, remove them and any empty lines before them
        if url_start_index is not None:
            # Trim trailing empty lines before the URLs
            while url_start_index > 0 and not lines[url_start_index - 1].strip():
                url_start_index -= 1
            
            # Return content before the URLs
            clean_content = '\n'.join(lines[:url_start_index]).rstrip()
            logger.debug(f"Removed URLs from answer: {len(answer_content)} -> {len(clean_content)} chars")
            return clean_content
        
        # If no URL-only lines found, return original content
        # (URLs might be embedded in prose, which is acceptable)
        return answer_content
    
    async def cleanup(self) -> None:
        """Clean up resources used by the executor."""
        if self.agent:
            # Log cleanup for debugging
            logger.info("Cleaning up Question Answerer agent...")
            try:
                # The Azure AI Agent Framework handles agent lifecycle automatically
                # when the underlying AzureAIAgentClient is closed
                logger.debug("Question Answerer agent cleanup completed")
            except Exception as e:
                logger.warning(f"Error during Question Answerer cleanup: {e}")
            finally:
                self.agent = None
                self.agent_id = None