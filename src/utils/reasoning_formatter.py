"""Formatter for rendering agent reasoning as rich text conversations."""

from typing import List, Tuple, Optional
from utils.data_types import AgentStep, AgentType, DocumentationLink


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
    def format_agent_steps(agent_steps: List[AgentStep], documentation_links: Optional[List[DocumentationLink]] = None) -> List[Tuple[str, str, str]]:
        """Format agent steps as a list of (agent_name, content, color) tuples.
        
        Args:
            agent_steps: List of agent execution steps from the workflow.
            documentation_links: Optional list of documentation links with validation status.
            
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
            if step.agent_name == AgentType.LINK_CHECKER:
                # For Link Checker, first show the summary, then individual links
                summary = ReasoningFormatter._extract_link_checker_summary(step)
                if summary:
                    formatted_steps.append((agent_name, summary, color))
                
                # Then show individual link results if available
                if documentation_links:
                    link_entries = ReasoningFormatter._format_link_checker_links(documentation_links)
                    for link_content in link_entries:
                        formatted_steps.append((agent_name, link_content, color))
            else:
                # For other agents, format normally
                content = ReasoningFormatter._extract_content(step)
                if content:
                    formatted_steps.append((agent_name, content, color))
        
        return formatted_steps
    
    @staticmethod
    def _extract_link_checker_summary(step: AgentStep) -> str:
        """Extract summary message from Link Checker output.
        
        Args:
            step: The Link Checker agent step.
            
        Returns:
            A summary message about the link validation.
        """
        output_data = step.output_data.strip()
        
        if not output_data:
            return ""
        
        # Check for no links case
        if "No documentation links provided" in output_data:
            return "No documentation links found - answer rejected."
        
        # Extract the validation decision from the output
        if "LINKS_VALID:" in output_data:
            # Count approved links if we can extract them
            return "Links validated and approved."
        elif "LINKS_INVALID:" in output_data:
            return "Links validation failed - issues detected."
        else:
            # Generic message if we can't parse the decision
            return "Link validation completed."
    
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
        
        # For Link Checker: this should not be called since we handle it separately
        if step.agent_name == AgentType.LINK_CHECKER:
            return ""
        
        return output_data
    
    @staticmethod
    def _format_link_checker_links(documentation_links: List[DocumentationLink]) -> List[str]:
        """Format link checker output to show individual link statuses.
        
        Args:
            documentation_links: List of documentation links with validation status.
            
        Returns:
            List of formatted link status messages.
        """
        link_messages = []
        
        for link in documentation_links:
            if link.is_reachable and link.is_relevant:
                link_messages.append(f"WORKING LINK. {link.url}")
            else:
                link_messages.append(f"FAILED LINK. {link.url}")
        
        return link_messages
