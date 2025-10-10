"""Error dialog system for the questionnaire application."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict
import logging


logger = logging.getLogger(__name__)


class ErrorDialog:
    """Manages error dialogs with specific error types and troubleshooting information."""
    
    def __init__(self, parent: tk.Tk):
        """Initialize the error dialog system.
        
        Args:
            parent: Parent window for modal dialogs.
        """
        self.parent = parent
        self.error_messages = self._initialize_error_messages()
    
    def _initialize_error_messages(self) -> Dict[str, Dict[str, str]]:
        """Initialize error message templates.
        
        Returns:
            Dictionary mapping error types to message templates.
        """
        return {
            "azure_service": {
                "title": "Azure Service Error",
                "icon": "error",
                "details": """Azure AI Foundry services are currently unavailable.

Possible solutions:
• Check your internet connection
• Verify Azure service status at status.azure.com
• Ensure your Azure subscription is active
• Try again in a few minutes

If the problem persists, contact Azure support."""
            },
            "network": {
                "title": "Network Connection Error",
                "icon": "error", 
                "details": """Unable to connect to Azure services.

Troubleshooting steps:
• Check your internet connection
• Verify firewall settings allow HTTPS traffic
• Check corporate proxy configuration
• Try connecting to other websites
• Restart your network adapter

Contact your IT administrator if using corporate network."""
            },
            "authentication": {
                "title": "Authentication Error",
                "icon": "error",
                "details": """Azure authentication failed.

Troubleshooting steps:
• Run 'az login' in command prompt to re-authenticate
• Check if your Azure account has proper permissions
• Verify Azure AI Foundry project access
• Clear browser cache if using browser authentication

Contact your Azure administrator for access issues."""
            },
            "configuration": {
                "title": "Configuration Error", 
                "icon": "error",
                "details": """Application configuration is invalid or incomplete.

Required configuration:
• Azure AI Foundry project endpoint
• Model deployment name
• Bing search connection ID

Check your .env file and ensure all required values are set.
Copy from .env.template if needed."""
            },
            "excel_format": {
                "title": "Excel Format Error",
                "icon": "warning",
                "details": """Excel file format is not supported or file is corrupted.

Supported formats:
• .xlsx (Excel 2007 and later)
• .xls (Excel 97-2003)

Common issues:
• File is password protected
• File contains complex formatting
• File is corrupted or incomplete
• Insufficient permissions to read file

Try saving the file in a simpler format or check file permissions."""
            },
            "processing": {
                "title": "Processing Error",
                "icon": "warning", 
                "details": """Question processing failed.

Possible causes:
• Question is too complex or ambiguous
• Maximum retry limit reached
• Service timeout occurred
• Character limit constraints

Try:
• Simplifying your question
• Increasing character limit
• Checking service status
• Trying again later"""
            },
            "general": {
                "title": "Unexpected Error",
                "icon": "error",
                "details": """An unexpected error occurred.

If this problem persists:
• Restart the application
• Check log files for details
• Report the issue with error details
• Try using mock mode for testing

Contact support if the issue continues."""
            }
        }
    
    def show_error(
        self, 
        error_type: str, 
        message: str, 
        details: Optional[str] = None
    ) -> None:
        """Display error dialog with specific failure information.
        
        Args:
            error_type: Category of error (azure_service, network, authentication, etc.).
            message: Primary error message.
            details: Additional troubleshooting information.
        """
        try:
            # Get error template
            error_template = self.error_messages.get(error_type, self.error_messages["general"])
            
            # Create custom dialog
            dialog = tk.Toplevel(self.parent)
            dialog.title(error_template["title"])
            dialog.geometry("500x400")
            dialog.resizable(True, True)
            dialog.transient(self.parent)
            dialog.grab_set()
            
            # Center the dialog
            self._center_dialog(dialog)
            
            # Create dialog content
            self._create_error_dialog_content(dialog, error_template, message, details)
            
            logger.info(f"Error dialog shown: {error_type} - {message}")
            
        except Exception as e:
            logger.error(f"Failed to show error dialog: {e}")
            # Fallback to simple messagebox
            messagebox.showerror("Error", f"{message}\n\nFailed to show detailed error dialog.")
    
    def _create_error_dialog_content(
        self, 
        dialog: tk.Toplevel,
        error_template: Dict[str, str],
        message: str,
        details: Optional[str]
    ) -> None:
        """Create the content of the error dialog.
        
        Args:
            dialog: Dialog window.
            error_template: Error message template.
            message: Primary error message.
            details: Additional details.
        """
        # Main frame with padding
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Error icon and title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title label
        title_label = ttk.Label(
            title_frame, 
            text=error_template["title"],
            font=("Segoe UI", 12, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Primary error message
        message_frame = ttk.LabelFrame(main_frame, text="Error Details", padding="10")
        message_frame.pack(fill=tk.X, pady=(0, 15))
        
        message_label = ttk.Label(
            message_frame,
            text=message,
            wraplength=450,
            justify=tk.LEFT
        )
        message_label.pack(fill=tk.X)
        
        # Troubleshooting information
        troubleshooting_frame = ttk.LabelFrame(main_frame, text="Troubleshooting", padding="10")
        troubleshooting_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Use details if provided, otherwise use template details
        troubleshooting_text = details if details else error_template["details"]
        
        troubleshooting_display = tk.Text(
            troubleshooting_frame,
            wrap=tk.WORD,
            height=8,
            font=("Segoe UI", 9),
            bg=dialog.cget("bg"),
            relief=tk.FLAT,
            state=tk.NORMAL
        )
        troubleshooting_display.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(troubleshooting_frame, orient=tk.VERTICAL, command=troubleshooting_display.yview)
        troubleshooting_display.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert troubleshooting text
        troubleshooting_display.insert("1.0", troubleshooting_text)
        troubleshooting_display.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Close button
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=dialog.destroy
        )
        close_button.pack(side=tk.RIGHT)
        
        # Copy to clipboard button
        copy_button = ttk.Button(
            button_frame,
            text="Copy Details",
            command=lambda: self._copy_error_details(message, troubleshooting_text)
        )
        copy_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Set focus and key bindings
        close_button.focus()
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def _center_dialog(self, dialog: tk.Toplevel) -> None:
        """Center the dialog on the parent window.
        
        Args:
            dialog: Dialog window to center.
        """
        dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _copy_error_details(self, message: str, details: str) -> None:
        """Copy error details to clipboard.
        
        Args:
            message: Error message.
            details: Detailed information.
        """
        try:
            error_text = f"Error: {message}\n\nDetails:\n{details}"
            self.parent.clipboard_clear()
            self.parent.clipboard_append(error_text)
            
            # Show brief confirmation
            messagebox.showinfo("Copied", "Error details copied to clipboard.", parent=self.parent)
            
        except Exception as e:
            logger.warning(f"Failed to copy to clipboard: {e}")
            messagebox.showwarning("Copy Failed", "Could not copy to clipboard.", parent=self.parent)
    
    def show_simple_error(self, title: str, message: str) -> None:
        """Show a simple error messagebox.
        
        Args:
            title: Dialog title.
            message: Error message.
        """
        messagebox.showerror(title, message, parent=self.parent)
    
    def show_warning(self, title: str, message: str) -> None:
        """Show a warning messagebox.
        
        Args:
            title: Dialog title.
            message: Warning message.
        """
        messagebox.showwarning(title, message, parent=self.parent)
    
    def show_info(self, title: str, message: str) -> None:
        """Show an info messagebox.
        
        Args:
            title: Dialog title.
            message: Information message.
        """
        messagebox.showinfo(title, message, parent=self.parent)