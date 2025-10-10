"""Link Checker agent executor using Microsoft Agent Framework."""

import logging
import time
import asyncio
from typing import Any, Dict, Optional
from agent_framework import Executor, handler, WorkflowContext, ChatAgent, ChatMessage, Role
from agent_framework_azure_ai import AzureAIAgentClient
from playwright.async_api import async_playwright
from utils.data_types import (
    Question, AgentStep, AgentType, StepStatus, ValidationStatus, 
    DocumentationLink
)
from utils.logger import log_agent_step, create_span
from utils.exceptions import AgentExecutionError, LinkValidationError


logger = logging.getLogger(__name__)


class LinkCheckerExecutor(Executor):
    """Executor for the Link Checker agent in the multi-agent workflow."""
    
    def __init__(self, azure_client: AzureAIAgentClient):
        """Initialize the Link Checker executor.
        
        Args:
            azure_client: Azure AI Agent client instance.
        """
        super().__init__(id="link_checker")
        self.azure_client = azure_client
        self.agent: Optional[ChatAgent] = None
    
    async def _get_agent(self) -> ChatAgent:
        """Get or create the link checker agent."""
        if self.agent is None:
            self.agent = ChatAgent(
                chat_client=self.azure_client,
                instructions="""You are an expert Link Checker specializing in validating documentation URLs for Microsoft Azure AI services.

Your role is to analyze URL validation results and determine if the provided links are relevant and accessible for the given answer content.

EVALUATION CRITERIA:
1. Accessibility: Are the links reachable (HTTP status 200-299)?
2. Relevance: Do the links support the answer content?
3. Authority: Are the links from official Microsoft documentation?
4. Currency: Do the links appear to contain current information?

RESPONSE FORMAT:
You MUST start your response with either "LINKS_VALID:" or "LINKS_INVALID:" followed by your analysis.

If LINKS_VALID:
- Confirm that links are accessible and relevant
- Highlight how the links support the answer content

If LINKS_INVALID:
- Specify which links are problematic and why
- Suggest replacements or improvements
- Be specific about accessibility or relevance issues

IMPORTANT:
- Focus on official Microsoft documentation sources
- Prioritize current and authoritative links
- Reject broken or irrelevant links
- Consider the context of the original question"""
            )
        return self.agent
    
    @handler
    async def handle(self, data: dict, ctx: WorkflowContext[dict, dict]) -> None:
        """Handle link validation and accessibility checking.
        
        Args:
            data: Context data containing question, answer, and validation status.
            ctx: Workflow context for yielding final results.
        """
        start_time = time.time()
        
        # Get data from previous agents
        question = data.get("question")
        raw_answer = data.get("raw_answer")
        validation_status = data.get("validation_status")
        answer_sources = data.get("answer_sources", [])
        
        if not question or not raw_answer:
            raise AgentExecutionError("Missing question or answer data from previous agents")
        
        with create_span("link_checker_execution", question_text=question.text):
            try:
                log_agent_step(
                    "link_checker",
                    f"Checking {len(answer_sources)} links for accessibility and relevance",
                    "started"
                )
                
                # Check links for accessibility
                link_check_results = await self._check_links_accessibility(answer_sources)
                
                # Get the agent
                agent = await self._get_agent()
                
                # Create link validation prompt
                validation_prompt = self._build_link_validation_prompt(
                    question, raw_answer, link_check_results
                )
                messages = [ChatMessage(role=Role.USER, text=validation_prompt)]
                
                # Run the agent to get link validation result
                response = await agent.run(messages)
                link_validation_result = response.text
                
                execution_time = time.time() - start_time
                
                # Parse link validation decision
                links_valid, link_feedback = self._parse_link_validation_response(link_validation_result)
                
                # Update final validation status if links are invalid
                final_validation_status = validation_status
                if validation_status == ValidationStatus.APPROVED and not links_valid:
                    final_validation_status = ValidationStatus.REJECTED_LINKS
                
                # Add agent step to history
                agent_steps = data.get("agent_steps", [])
                agent_steps.append(
                    AgentStep(
                        agent_name=AgentType.LINK_CHECKER,
                        input_data=f"Links to check: {answer_sources}",
                        output_data=link_validation_result,
                        execution_time=execution_time,
                        status=StepStatus.SUCCESS
                    )
                )
                
                # Prepare final result
                final_result = {
                    "question": question,
                    "raw_answer": raw_answer,
                    "validation_status": final_validation_status,
                    "validation_feedback": data.get("validation_feedback", ""),
                    "link_feedback": link_feedback,
                    "documentation_links": link_check_results,
                    "agent_steps": agent_steps,
                    "processing_complete": True
                }
                
                await ctx.yield_output(final_result)
                
                log_agent_step(
                    "link_checker",
                    f"Link validation complete: {'VALID' if links_valid else 'INVALID'}",
                    "completed",
                    execution_time
                )
                
                logger.info(f"Link Checker completed: {'VALID' if links_valid else 'INVALID'} in {execution_time:.2f}s")
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_message = f"Link Checker failed: {str(e)}"
                
                log_agent_step(
                    "link_checker",
                    error_message,
                    "failed",
                    execution_time
                )
                
                logger.error(error_message, exc_info=True)
                
                # Add failed step and yield error result
                agent_steps = data.get("agent_steps", [])
                agent_steps.append(
                    AgentStep(
                        agent_name=AgentType.LINK_CHECKER,
                        input_data=f"Links: {answer_sources}",
                        output_data="",
                        execution_time=execution_time,
                        status=StepStatus.FAILURE,
                        error_message=error_message
                    )
                )
                
                error_result = {
                    "question": question,
                    "raw_answer": raw_answer,
                    "validation_status": ValidationStatus.FAILED_TIMEOUT,
                    "error": AgentExecutionError(error_message),
                    "agent_steps": agent_steps,
                    "processing_complete": True
                }
                
                await ctx.yield_output(error_result)
                raise AgentExecutionError(error_message) from e
    
    async def _check_links_accessibility(self, urls: list[str]) -> list[DocumentationLink]:
        """Check the accessibility of provided URLs using Playwright.
        
        Args:
            urls: List of URLs to check.
            
        Returns:
            List of DocumentationLink objects with validation results.
        """
        if not urls:
            return []
        
        results = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                for url in urls:
                    try:
                        # Set timeout for page load
                        response = await page.goto(url, timeout=10000, wait_until="domcontentloaded")
                        
                        # Get page title
                        title = await page.title()
                        
                        # Check if response is successful
                        is_reachable = response and response.status < 400
                        
                        # Basic relevance check (look for Microsoft/Azure content)
                        content = await page.content()
                        is_relevant = any(keyword in content.lower() for keyword in [
                            'microsoft', 'azure', 'docs.microsoft.com', 'learn.microsoft.com'
                        ])
                        
                        results.append(DocumentationLink(
                            url=url,
                            title=title if title else None,
                            is_reachable=is_reachable,
                            is_relevant=is_relevant,
                            http_status=response.status if response else None
                        ))
                        
                        logger.debug(f"Link check: {url} - Status: {response.status if response else 'No response'}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to check link {url}: {e}")
                        results.append(DocumentationLink(
                            url=url,
                            is_reachable=False,
                            is_relevant=False,
                            validation_error=str(e)
                        ))
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"Failed to initialize browser for link checking: {e}")
            # Return basic link objects with error status
            for url in urls:
                results.append(DocumentationLink(
                    url=url,
                    is_reachable=False,
                    is_relevant=False,
                    validation_error=f"Browser initialization failed: {str(e)}"
                ))
        
        return results
    
    def _build_link_validation_prompt(self, question: Question, answer: str, 
                                    link_results: list[DocumentationLink]) -> str:
        """Build the link validation prompt for the Link Checker agent.
        
        Args:
            question: The original question object.
            answer: The generated answer content.
            link_results: Results from accessibility checking.
            
        Returns:
            Formatted link validation prompt.
        """
        # Format link results for the prompt
        link_summary = []
        for link in link_results:
            status = "✓ Accessible" if link.is_reachable else "✗ Not accessible"
            relevance = "✓ Relevant" if link.is_relevant else "✗ Not relevant"
            title = f" (Title: {link.title})" if link.title else ""
            error = f" (Error: {link.validation_error})" if link.validation_error else ""
            
            link_summary.append(f"- {link.url}{title}\n  {status}, {relevance}{error}")
        
        links_text = "\n".join(link_summary) if link_summary else "No links found in the answer."
        
        prompt = f"""Please evaluate the documentation links for this answer:

ORIGINAL QUESTION:
{question.text}

GENERATED ANSWER:
{answer}

LINK VALIDATION RESULTS:
{links_text}

EVALUATION CRITERIA:
- Are accessible links relevant to the question and answer?
- Do the links support the information provided in the answer?
- Are the links from authoritative Microsoft sources?
- Are there any broken or irrelevant links that should be removed?

RESPONSE FORMAT:
Start with either "LINKS_VALID:" or "LINKS_INVALID:" followed by your analysis.

Provide your link validation decision:"""

        return prompt
    
    def _parse_link_validation_response(self, validation_result: str) -> tuple[bool, str]:
        """Parse the link validation response.
        
        Args:
            validation_result: The raw link validation response from the agent.
            
        Returns:
            Tuple of (links_are_valid, feedback_message).
        """
        try:
            validation_upper = validation_result.upper()
            
            if validation_result.startswith("LINKS_VALID:"):
                return True, validation_result[12:].strip()
            elif validation_result.startswith("LINKS_INVALID:"):
                return False, validation_result[13:].strip()
            elif "LINKS_VALID" in validation_upper:
                return True, validation_result
            elif "LINKS_INVALID" in validation_upper:
                return False, validation_result
            else:
                # Ambiguous response - default to invalid for safety
                logger.warning(f"Ambiguous link validation response: {validation_result[:100]}...")
                return False, f"Unclear link validation result: {validation_result}"
                
        except Exception as e:
            logger.error(f"Failed to parse link validation response: {e}")
            return False, f"Failed to parse link validation: {str(e)}"
    
    async def cleanup(self) -> None:
        """Clean up resources used by the executor."""
        if self.agent:
            # Agent cleanup is handled automatically by the framework
            logger.debug("Link Checker executor cleanup completed")
            self.agent = None