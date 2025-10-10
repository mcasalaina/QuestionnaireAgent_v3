"""Status bar and progress tracking for the questionnaire application."""

import tkinter as tk
from tkinter import ttk
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class StatusManager:
    """Manages status bar and progress tracking in the GUI."""
    
    def __init__(self, parent: ttk.Frame):
        """Initialize the status manager.
        
        Args:
            parent: Parent frame to contain status components.
        """
        self.parent = parent
        self.status_frame: Optional[ttk.Frame] = None
        self.status_label: Optional[ttk.Label] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.agent_label: Optional[ttk.Label] = None
        
        # Status tracking
        self.current_agent = ""
        self.current_message = ""
        self.current_progress = 0.0
        
        self._create_status_ui()
    
    def _create_status_ui(self) -> None:
        """Create the status UI components."""
        # Status frame at bottom
        self.status_frame = ttk.Frame(self.parent)
        self.status_frame.grid(row=10, column=0, columnspan=2, sticky="we", pady=(5, 0))
        self.status_frame.columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Progress bar (initially hidden)
        self.progress_bar = ttk.Progressbar(
            self.status_frame, 
            mode='determinate',
            length=200
        )
        # Don't grid it yet - will be shown when needed
        
        # Agent activity label (initially hidden)
        self.agent_label = ttk.Label(self.status_frame, text="", foreground="blue")
        # Don't grid it yet - will be shown when needed
        
        logger.debug("Status UI components created")
    
    def set_status(self, message: str, status_type: str = "info") -> None:
        """Set the main status message.
        
        Args:
            message: Status message to display.
            status_type: Type of status (info, success, warning, error).
        """
        self.status_label.config(text=message)
        
        # Set color based on status type
        color_map = {
            "info": "black",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        
        color = color_map.get(status_type, "black")
        self.status_label.config(foreground=color)
        
        logger.debug(f"Status set: {message} ({status_type})")
    
    def update_progress(self, agent: str, message: str, progress: float) -> None:
        """Update progress tracking with agent activity.
        
        Args:
            agent: Current agent name.
            message: Current activity message.
            progress: Progress value (0.0 to 1.0).
        """
        self.current_agent = agent
        self.current_message = message
        self.current_progress = progress
        
        # Update progress bar
        progress_percentage = progress * 100
        self.progress_bar.config(value=progress_percentage)
        
        # Update agent activity label
        agent_display_name = self._format_agent_name(agent)
        activity_text = f"{agent_display_name}: {message}"
        self.agent_label.config(text=activity_text)
        
        # Update main status with progress percentage
        if progress >= 1.0:
            self.set_status("Processing completed", "success")
        else:
            self.set_status(f"Processing... ({progress_percentage:.1f}%)", "info")
        
        logger.debug(f"Progress updated: {agent} - {message} ({progress_percentage:.1f}%)")
    
    def show_progress(self) -> None:
        """Show progress tracking components."""
        # Grid the progress bar and agent label
        self.progress_bar.grid(row=0, column=1, sticky="we", padx=(0, 10))
        self.agent_label.grid(row=0, column=2, sticky="w")
        
        # Reset progress
        self.progress_bar.config(value=0)
        self.agent_label.config(text="Initializing...")
        
        logger.debug("Progress tracking shown")
    
    def hide_progress(self) -> None:
        """Hide progress tracking components."""
        # Remove from grid
        self.progress_bar.grid_remove()
        self.agent_label.grid_remove()
        
        # Reset state
        self.current_agent = ""
        self.current_message = ""
        self.current_progress = 0.0
        
        logger.debug("Progress tracking hidden")
    
    def _format_agent_name(self, agent: str) -> str:
        """Format agent name for display.
        
        Args:
            agent: Raw agent name.
            
        Returns:
            Formatted display name.
        """
        name_map = {
            "question_answerer": "Question Answerer",
            "answer_checker": "Answer Checker", 
            "link_checker": "Link Checker",
            "workflow": "Workflow Manager",
            "batch": "Batch Processor"
        }
        
        return name_map.get(agent, agent.replace("_", " ").title())
    
    def set_agent_activity(self, agent: str, activity: str) -> None:
        """Set current agent activity without progress update.
        
        Args:
            agent: Agent name.
            activity: Current activity description.
        """
        agent_display_name = self._format_agent_name(agent)
        activity_text = f"{agent_display_name}: {activity}"
        self.agent_label.config(text=activity_text)
        
        logger.debug(f"Agent activity: {agent} - {activity}")
    
    def clear_status(self) -> None:
        """Clear all status information."""
        self.set_status("Ready", "info")
        self.hide_progress()
        
        logger.debug("Status cleared")
    
    def get_current_status(self) -> dict:
        """Get current status information.
        
        Returns:
            Dictionary with current status details.
        """
        return {
            "message": self.status_label.cget("text"),
            "agent": self.current_agent,
            "activity": self.current_message,
            "progress": self.current_progress
        }