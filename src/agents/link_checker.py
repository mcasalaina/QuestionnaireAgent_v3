"""Link Checker agent executor using Microsoft Agent Framework."""

import logging
import time
import asyncio
import re
from typing import Any, Dict, Optional
from agent_framework import Executor, handler, WorkflowContext, ChatAgent, ChatMessage, Role
from agent_framework_azure_ai import AzureAIAgentClient
from azure.ai.agents.models import BrowserAutomationTool
from utils.data_types import (
    Question, AgentStep, AgentType, StepStatus, ValidationStatus, 
    DocumentationLink
)
from utils.logger import log_agent_step, create_span
from utils.exceptions import AgentExecutionError, LinkValidationError


logger = logging.getLogger(__name__)


class LinkCheckerExecutor(Executor):
    """Executor for the Link Checker agent in the multi-agent workflow."""
    
    def __init__(self, azure_client: AzureAIAgentClient, browser_automation_connection_id: str):
        """Initialize the Link Checker executor.
        
        Args:
            azure_client: Azure AI Agent client instance.
            browser_automation_connection_id: Browser automation connection for web verification.
        """
        super().__init__(id="link_checker")
        self.azure_client = azure_client
        self.browser_automation_connection_id = browser_automation_connection_id
        self.agent: Optional[ChatAgent] = None
    
    async def _get_agent(self) -> ChatAgent:
        """Get or create the link checker agent with Browser Automation tool."""
        if self.agent is None:
            # Create browser automation tool for link verification
            browser_tool = BrowserAutomationTool(
                connection_id=self.browser_automation_connection_id
            )
            
            self.agent = ChatAgent(
                chat_client=self.azure_client,
                tools=[browser_tool],
                name="Link Checker",
                instructions="""You are an expert Link Checker specializing in validating documentation URLs for Microsoft Azure AI services.

Your role is to verify that provided links are accessible and contain information that is pertinent to the response content.

VERIFICATION PROCESS:
1. Use the browser automation tool to visit each URL
2. Verify the link is accessible (loads successfully)
3. Examine the page content to determine if it's relevant to the answer
4. Check if the link is from an official Microsoft documentation source

EVALUATION CRITERIA:
1. Accessibility: Can the link be loaded successfully?
2. Relevance: Does the page content support or relate to the answer content?
3. Authority: Is the link from official Microsoft documentation (docs.microsoft.com, learn.microsoft.com, azure.microsoft.com)?
4. Pertinence: Does the page contain specific information mentioned in or related to the answer?

RESPONSE FORMAT:
You MUST start your response with either "LINKS_VALID:" or "LINKS_INVALID:" followed by your analysis.

For each link in your analysis, please structure your feedback clearly:
- State the URL
- Indicate if it loaded successfully or not
- If loaded, briefly describe what content you found
- Explain how the content relates (or doesn't relate) to the answer
- Note if it's from an official Microsoft source

If LINKS_VALID:
- Confirm that links are accessible and relevant
- For each link, highlight how its content supports the answer
- Mention key information found on each page that validates the answer

If LINKS_INVALID:
- Specify which links are problematic and why
- For inaccessible links: clearly state "not accessible" or "unreachable"
- For irrelevant links: clearly state "not relevant" or "irrelevant" and explain why the content doesn't match
- Suggest what type of links would be more appropriate

IMPORTANT:
- Use the browser automation tool to actually visit and inspect each link
- Be explicit and clear when a link has issues (use phrases like "not accessible", "irrelevant", etc.)
- Focus on official Microsoft documentation sources
- Verify that page content is current and authoritative
- Be specific about what you found on each page
- Reject broken or irrelevant links"""
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
                    f"Checking {len(answer_sources)} links for accessibility and relevance using Browser Automation",
                    "started"
                )
                
                # Get the agent with browser automation tool
                agent = await self._get_agent()
                
                # Create link validation prompt for browser automation
                validation_prompt = self._build_link_validation_prompt(
                    question, raw_answer, answer_sources
                )
                messages = [ChatMessage(role=Role.USER, text=validation_prompt)]
                
                # Run the agent to get link validation result using browser automation
                response = await agent.run(messages)
                link_validation_result = response.text
                
                execution_time = time.time() - start_time
                
                # Parse link validation decision
                links_valid, link_feedback = self._parse_link_validation_response(link_validation_result)
                
                # Extract link check results from the agent's response
                link_check_results = self._extract_link_results(answer_sources, link_validation_result, links_valid)
                
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
    def _extract_link_results(self, urls: list[str], validation_result: str, 
                              links_valid: bool) -> list[DocumentationLink]:
        """Extract link validation results from the agent's response.
        
        Args:
            urls: List of URLs that were checked.
            validation_result: The validation response from the agent.
            links_valid: Whether the overall validation passed.
            
        Returns:
            List of DocumentationLink objects with validation results.
        """
        results = []
        
        # Parse the validation result to extract per-link information
        # The agent will have used browser automation to check each link
        for url in urls:
            # Default to the overall validation status
            is_reachable = links_valid
            is_relevant = links_valid
            
            # Try to extract specific information about this URL from the response
            url_lower = url.lower()
            result_lower = validation_result.lower()
            
            # Check if the URL is specifically mentioned as problematic
            # Note: This is heuristic-based parsing. For production use, consider
            # requesting structured JSON output from the agent for more reliable parsing.
            if url in validation_result or url_lower in result_lower:
                # Look for negative indicators near the URL mention
                # These patterns help identify link-specific issues
                if any(indicator in result_lower for indicator in 
                       ['not accessible', 'broken', 'error', 'failed', 'inaccessible', 
                        'unreachable', 'not found', '404', 'invalid']):
                    is_reachable = False
                    is_relevant = False
                elif any(indicator in result_lower for indicator in 
                         ['not relevant', 'irrelevant', 'unrelated', 'off-topic']):
                    is_relevant = False
            
            # Extract title if mentioned (look for patterns like "Title: ...")
            title = None
            if url in validation_result:
                # Simple heuristic to find title near the URL
                url_pos = validation_result.find(url)
                context = validation_result[max(0, url_pos-200):min(len(validation_result), url_pos+200)]
                if 'title:' in context.lower():
                    # Extract text after "title:" or "Title:"
                    title_match = re.search(r'[Tt]itle:\s*([^\n\r\.]+)', context)
                    if title_match:
                        title = title_match.group(1).strip()
            
            # Note: Browser automation tool doesn't directly provide HTTP status codes
            # Setting http_status to None to accurately reflect that we don't have this information
            results.append(DocumentationLink(
                url=url,
                title=title,
                is_reachable=is_reachable,
                is_relevant=is_relevant,
                http_status=None,  # Browser automation doesn't provide HTTP status codes
                validation_error=None if is_reachable else "Link validation failed via browser automation"
            ))
        
        return results
    
    def _build_link_validation_prompt(self, question: Question, answer: str, 
                                    urls: list[str]) -> str:
        """Build the link validation prompt for the Link Checker agent.
        
        Args:
            question: The original question object.
            answer: The generated answer content.
            urls: List of URLs to validate.
            
        Returns:
            Formatted link validation prompt.
        """
        urls_text = "\n".join(f"- {url}" for url in urls) if urls else "No links found in the answer."
        
        prompt = f"""Please use the browser automation tool to verify the following documentation links for this answer:

ORIGINAL QUESTION:
{question.text}

GENERATED ANSWER:
{answer}

LINKS TO VERIFY:
{urls_text}

INSTRUCTIONS:
1. Use the browser automation tool to visit each URL
2. For each link, verify:
   - Can the page be loaded successfully?
   - Does the page content relate to the question and answer?
   - Is it from an official Microsoft documentation source?
   - Does it contain specific information that supports the answer?

EVALUATION CRITERIA:
- Are the links accessible and loading successfully?
- Do the links contain content relevant to the question and answer?
- Are the links from authoritative Microsoft sources (docs.microsoft.com, learn.microsoft.com, azure.microsoft.com)?
- Do the pages contain specific information that validates or supports the answer content?

RESPONSE FORMAT:
Start with either "LINKS_VALID:" or "LINKS_INVALID:" followed by your detailed analysis.

For each link, describe:
- Whether it loaded successfully
- What content you found on the page
- How the content relates to the answer
- Whether it's from an official Microsoft source

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