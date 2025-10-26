"""Formatter for rendering agent reasoning as rich text conversations."""

from typing import List, Tuple
from utils.data_types import AgentStep, AgentType


class ReasoningFormatter:
    """Format agent reasoning steps as rich text conversations."""
    
    # Agent name display mapping
    AGENT_NAMES = {
        AgentType.QUESTION_ANSWERER: "Question Answerer",
        AgentType.ANSWER_CHECKER: "Answer Checker",
        AgentType.LINK_CHECKER: "Link Checker"
    }
    
    # Agent text colors (for tkinter tags)
    AGENT_COLORS = {
        AgentType.QUESTION_ANSWERER: "black",
        AgentType.ANSWER_CHECKER: "green",
        AgentType.LINK_CHECKER: "blue"
    }
    
    @staticmethod
    def format_agent_steps(agent_steps: List[AgentStep]) -> List[Tuple[str, str, str]]:
        """Format agent steps as a list of (agent_name, content, color) tuples.
        
        Args:
            agent_steps: List of agent execution steps from the workflow.
            
        Returns:
            List of tuples containing:
                - agent_name: Display name of the agent (e.g., "Question Answerer")
                - content: The content to display from the agent
                - color: The color to use for the agent name
        """
        formatted_steps = []
        
        for step in agent_steps:
            agent_name = ReasoningFormatter.AGENT_NAMES.get(step.agent_name, str(step.agent_name))
            color = ReasoningFormatter.AGENT_COLORS.get(step.agent_name, "black")
            
            # Get the content from the agent's output
            content = ReasoningFormatter._extract_content(step)
            
            if content:
                formatted_steps.append((agent_name, content, color))
        
        return formatted_steps
    
    @staticmethod
    def _extract_content(step: AgentStep) -> str:
        """Extract displayable content from an agent step.
        
        Args:
            step: The agent step to extract content from.
            
        Returns:
            The formatted content string.
        """
        output_data = step.output_data.strip()
        
        if not output_data:
            return ""
        
        # For Question Answerer: show the full answer
        if step.agent_name == AgentType.QUESTION_ANSWERER:
            return output_data
        
        # For Answer Checker: extract the decision and reasoning
        if step.agent_name == AgentType.ANSWER_CHECKER:
            # The output_data contains "APPROVED: ..." or "REJECTED: ..."
            if output_data.startswith("APPROVED:"):
                return "APPROVE."
            elif output_data.startswith("REJECTED:"):
                # Extract the reason after "REJECTED:"
                reason = output_data[9:].strip()  # Remove "REJECTED: " prefix
                # Simplify the reason to match the example format
                if reason:
                    # Take only the first sentence or main point
                    first_sentence = reason.split('.')[0].strip()
                    return f"REJECT. {first_sentence}."
                return "REJECT."
            return output_data
        
        # For Link Checker: extract link status
        if step.agent_name == AgentType.LINK_CHECKER:
            return ReasoningFormatter._format_link_checker_output(output_data)
        
        return output_data
    
    @staticmethod
    def _format_link_checker_output(output_data: str) -> str:
        """Format link checker output to show individual link statuses.
        
        The Link Checker output contains validation results for links.
        We need to extract and format them as shown in the issue example.
        
        Args:
            output_data: The raw output from the link checker.
            
        Returns:
            Formatted link status messages.
        """
        # The output typically starts with "LINKS_VALID:" or "LINKS_INVALID:"
        # For now, return the raw output as it may contain detailed link info
        # We'll refine this based on actual output format when we test
        return output_data
