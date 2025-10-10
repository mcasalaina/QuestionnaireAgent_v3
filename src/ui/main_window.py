"""Main GUI window using tkinter for the questionnaire application."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import asyncio
from typing import Optional, Callable, Any
import logging
from utils.data_types import Question, ProcessingResult, ExcelProcessingResult
from utils.exceptions import (
    AzureServiceError, NetworkError, AuthenticationError, 
    ConfigurationError, ExcelFormatError
)
from utils.logger import setup_logging
from agents.workflow_manager import AgentCoordinator
from utils.config import config_manager
from utils.azure_auth import get_azure_client
from .status_manager import StatusManager
from .dialogs import ErrorDialog


logger = logging.getLogger(__name__)


class UIManager:
    """Main GUI interface for the questionnaire application."""
    
    def __init__(self, agent_coordinator: Optional[AgentCoordinator] = None):
        """Initialize UI with agent coordinator dependency.
        
        Args:
            agent_coordinator: Pre-initialized agent coordinator (optional).
        """
        self.agent_coordinator = agent_coordinator
        self.root = tk.Tk()
        self.status_manager: Optional[StatusManager] = None
        self.error_dialog: Optional[ErrorDialog] = None
        self.processing_active = False
        
        # UI components
        self.question_entry: Optional[scrolledtext.ScrolledText] = None
        self.ask_button: Optional[ttk.Button] = None
        self.import_button: Optional[ttk.Button] = None
        self.answer_display: Optional[scrolledtext.ScrolledText] = None
        self.sources_display: Optional[scrolledtext.ScrolledText] = None
        
        # Settings
        self.char_limit_var = tk.IntVar(value=2000)
        self.context_var = tk.StringVar(value="Microsoft Azure AI")
        self.max_retries_var = tk.IntVar(value=10)
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the main GUI layout."""
        self.root.title("Questionnaire Answerer (Microsoft Agent Framework)")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main paned window for left/right split
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        
        # Create left panel for input controls
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Create right panel for results
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # Create UI sections in appropriate panels
        self._create_left_panel(left_frame)
        self._create_right_panel(right_frame)
        
        # Initialize status manager and error dialog
        self.status_manager = StatusManager(self.root)
        self.error_dialog = ErrorDialog(self.root)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        logger.info("GUI initialized successfully")
    
    def _create_left_panel(self, parent: ttk.Frame) -> None:
        """Create the left panel with input controls."""
        # Context section
        context_label = ttk.Label(parent, text="Context")
        context_label.pack(anchor=tk.W, pady=(0, 5))
        
        context_entry = ttk.Entry(parent, textvariable=self.context_var, width=40)
        context_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Character Limit section
        limit_label = ttk.Label(parent, text="Character Limit")
        limit_label.pack(anchor=tk.W, pady=(0, 5))
        
        char_limit_spinbox = ttk.Spinbox(
            parent,
            from_=100,
            to=10000,
            textvariable=self.char_limit_var,
            width=40
        )
        char_limit_spinbox.pack(fill=tk.X, pady=(0, 15))
        
        # Maximum Retries section
        retries_label = ttk.Label(parent, text="Maximum Retries")
        retries_label.pack(anchor=tk.W, pady=(0, 5))
        
        retries_spinbox = ttk.Spinbox(
            parent,
            from_=1,
            to=25,
            textvariable=self.max_retries_var,
            width=40
        )
        retries_spinbox.pack(fill=tk.X, pady=(0, 15))
        
        # Question section
        question_label = ttk.Label(parent, text="Question")
        question_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.question_entry = scrolledtext.ScrolledText(
            parent,
            height=8,
            width=40,
            font=('Segoe UI', 12),
            wrap=tk.WORD
        )
        self.question_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.ask_button = ttk.Button(
            button_frame,
            text="Ask!",
            command=self._on_ask_clicked
        )
        self.ask_button.pack(fill=tk.X, pady=(0, 10))
        
        self.import_button = ttk.Button(
            button_frame,
            text="Import From Excel",
            command=self._on_import_excel_clicked
        )
        self.import_button.pack(fill=tk.X)
    
    def _create_right_panel(self, parent: ttk.Frame) -> None:
        """Create the right panel with results display."""
        # Results notebook for tabbed display
        results_notebook = ttk.Notebook(parent)
        results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Answer tab
        answer_frame = ttk.Frame(results_notebook)
        results_notebook.add(answer_frame, text="Answer")
        
        answer_label = ttk.Label(answer_frame, text="Answer")
        answer_label.pack(anchor=tk.W, pady=(5, 5))
        
        self.answer_display = scrolledtext.ScrolledText(
            answer_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            state=tk.DISABLED
        )
        self.answer_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Documentation tab
        docs_frame = ttk.Frame(results_notebook)
        results_notebook.add(docs_frame, text="Documentation")
        
        docs_label = ttk.Label(docs_frame, text="Documentation")
        docs_label.pack(anchor=tk.W, pady=(5, 5))
        
        self.sources_display = scrolledtext.ScrolledText(
            docs_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            state=tk.DISABLED
        )
        self.sources_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
    
    def _setup_event_handlers(self) -> None:
        """Set up keyboard and window event handlers."""
        # Bind Ctrl+Enter to ask button
        self.root.bind('<Control-Return>', lambda e: self._on_ask_clicked())
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Bind Enter key in question entry to ask (if not multiline)
        self.question_entry.bind('<Return>', self._on_question_enter)
    
    def _on_question_enter(self, event: tk.Event) -> str:
        """Handle Enter key in question entry."""
        # If Shift+Enter, allow new line; otherwise trigger ask
        if not event.state & 0x1:  # No Shift key
            self._on_ask_clicked()
            return "break"  # Prevent default behavior
        return None
    
    def _on_ask_clicked(self) -> None:
        """Handle Ask button click."""
        if self.processing_active:
            return
        
        question_text = self.question_entry.get("1.0", tk.END).strip()
        if not question_text:
            messagebox.showwarning("Empty Question", "Please enter a question before clicking Ask!")
            self.question_entry.focus()
            return
        
        # Disable UI during processing
        self._set_processing_state(True)
        
        # Start processing in background thread
        threading.Thread(
            target=self._process_question_async,
            args=(question_text,),
            daemon=True
        ).start()
    
    def _on_import_excel_clicked(self) -> None:
        """Handle Import Excel button click."""
        if self.processing_active:
            return
        
        # Show file dialog
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Disable UI during processing
            self._set_processing_state(True)
            
            # Start Excel processing in background thread
            threading.Thread(
                target=self._process_excel_async,
                args=(file_path,),
                daemon=True
            ).start()
    
    def _on_clear_clicked(self) -> None:
        """Handle Clear button click."""
        if self.processing_active:
            return
        
        # Clear question entry
        self.question_entry.delete("1.0", tk.END)
        
        # Clear results
        self._clear_results()
        
        # Focus question entry
        self.question_entry.focus()
    
    def _on_window_close(self) -> None:
        """Handle window close event."""
        if self.processing_active:
            if not messagebox.askokcancel("Processing Active", 
                                        "Processing is currently active. Are you sure you want to exit?"):
                return
        
        # Cleanup and close
        self._cleanup()
        self.root.destroy()
    
    def _process_question_async(self, question_text: str) -> None:
        """Process question asynchronously in background thread."""
        try:
            # Run async processing
            result = asyncio.run(self._process_question_internal(question_text))
            
            # Update UI on main thread
            self.root.after(0, self._handle_question_result, result)
            
        except Exception as e:
            logger.error(f"Error in question processing: {e}", exc_info=True)
            # Show error on main thread
            self.root.after(0, self._handle_processing_error, e)
    
    def _process_excel_async(self, file_path: str) -> None:
        """Process Excel file asynchronously in background thread."""
        try:
            # Run async processing
            result = asyncio.run(self._process_excel_internal(file_path))
            
            # Update UI on main thread
            self.root.after(0, self._handle_excel_result, result)
            
        except Exception as e:
            logger.error(f"Error in Excel processing: {e}", exc_info=True)
            # Show error on main thread
            self.root.after(0, self._handle_processing_error, e)
    
    async def _process_question_internal(self, question_text: str) -> ProcessingResult:
        """Internal async question processing."""
        # Ensure agent coordinator is available
        if not self.agent_coordinator:
            azure_client = await get_azure_client()
            bing_connection_id = config_manager.get_bing_connection_id()
            
            from agents.workflow_manager import create_agent_coordinator
            self.agent_coordinator = await create_agent_coordinator(azure_client, bing_connection_id)
        
        # Create question object
        question = Question(
            text=question_text,
            context=self.context_var.get(),
            char_limit=self.char_limit_var.get(),
            max_retries=self.max_retries_var.get()
        )
        
        # Process with progress updates
        return await self.agent_coordinator.process_question(question, self.update_progress)
    
    async def _process_excel_internal(self, file_path: str) -> ExcelProcessingResult:
        """Internal async Excel processing."""
        # TODO: Implement Excel processing workflow
        # This will be implemented in User Story 2
        raise NotImplementedError("Excel processing will be implemented in User Story 2")
    
    def _handle_question_result(self, result: ProcessingResult) -> None:
        """Handle question processing result on main thread."""
        try:
            if result.success and result.answer:
                self.display_answer(result.answer.content, result.answer.sources)
                self.status_manager.set_status(f"Processing completed successfully in {result.processing_time:.1f}s", "success")
            else:
                self.display_error("processing", result.error_message or "Unknown processing error")
                self.status_manager.set_status("Processing failed", "error")
        
        finally:
            self._set_processing_state(False)
    
    def _handle_excel_result(self, result: ExcelProcessingResult) -> None:
        """Handle Excel processing result on main thread."""
        try:
            if result.success:
                # Display Excel results
                summary = f"Excel processing completed: {result.questions_processed} questions processed"
                if result.output_file_path:
                    summary += f"\nOutput saved to: {result.output_file_path}"
                
                self.display_answer(summary, [])
                self.status_manager.set_status("Excel processing completed", "success")
            else:
                self.display_error("excel_format", result.error_message or "Excel processing failed")
                self.status_manager.set_status("Excel processing failed", "error")
        
        finally:
            self._set_processing_state(False)
    
    def _handle_processing_error(self, error: Exception) -> None:
        """Handle processing error on main thread."""
        try:
            if isinstance(error, AzureServiceError):
                self.display_error("azure_service", str(error))
            elif isinstance(error, NetworkError):
                self.display_error("network", str(error))
            elif isinstance(error, AuthenticationError):
                self.display_error("authentication", str(error))
            elif isinstance(error, ConfigurationError):
                self.display_error("configuration", str(error))
            elif isinstance(error, ExcelFormatError):
                self.display_error("excel_format", str(error))
            else:
                self.display_error("general", f"An unexpected error occurred: {str(error)}")
        
        finally:
            self._set_processing_state(False)
    
    def process_single_question(
        self, 
        question: str, 
        context: str = "Microsoft Azure AI", 
        char_limit: int = 2000,
        max_retries: int = 10
    ) -> ProcessingResult:
        """Process a single question through the multi-agent workflow.
        
        Args:
            question: User's natural language question.
            context: Domain context for the question.
            char_limit: Maximum characters for answer.
            max_retries: Maximum retry attempts.
            
        Returns:
            ProcessingResult with answer or error details.
            
        Raises:
            ValueError: If question is empty or parameters invalid.
            NetworkError: If connectivity issues prevent processing.
            AuthenticationError: If Azure credentials are invalid.
        """
        # This method provides the interface contract for testing
        # Actual implementation is async and handled by _process_question_internal
        if not question or len(question.strip()) < 5:
            raise ValueError("Question text must be at least 5 characters")
        
        # For testing purposes, return a synchronous result
        # In production, this would be handled by the async workflow
        return asyncio.run(self._process_question_internal(question))
    
    def import_excel_file(self, file_path: str) -> ExcelProcessingResult:
        """Process questions from Excel file through batch workflow.
        
        Args:
            file_path: Absolute path to Excel file.
            
        Returns:
            ExcelProcessingResult with processed data or error details.
            
        Raises:
            FileNotFoundError: If Excel file doesn't exist.
            ExcelFormatError: If file format is unsupported.
        """
        # This method provides the interface contract for testing
        # Implementation will be completed in User Story 2
        return asyncio.run(self._process_excel_internal(file_path))
    
    def update_progress(self, agent: str, message: str, progress: float) -> None:
        """Update UI with current processing progress.
        
        Args:
            agent: Current agent name.
            message: Status message for reasoning panel.
            progress: Completion percentage (0.0 to 1.0).
        """
        # Update status manager on main thread
        self.root.after(0, self.status_manager.update_progress, agent, message, progress)
    
    def display_answer(self, answer_content: str, sources: list[str] = None) -> None:
        """Display answer and sources in the UI.
        
        Args:
            answer_content: The answer text to display.
            sources: List of source URLs.
        """
        # Display answer
        self.answer_display.config(state=tk.NORMAL)
        self.answer_display.delete("1.0", tk.END)
        self.answer_display.insert("1.0", answer_content)
        self.answer_display.config(state=tk.DISABLED)
        
        # Display sources
        if sources:
            sources_text = "\n".join(f"• {source}" for source in sources)
        else:
            sources_text = "No sources provided."
        
        self.sources_display.config(state=tk.NORMAL)
        self.sources_display.delete("1.0", tk.END)
        self.sources_display.insert("1.0", sources_text)
        self.sources_display.config(state=tk.DISABLED)
    
    def display_error(
        self, 
        error_type: str, 
        message: str, 
        details: Optional[str] = None
    ) -> None:
        """Display error dialog with specific failure information.
        
        Args:
            error_type: Category of error.
            message: Primary error message.
            details: Additional troubleshooting information.
        """
        self.error_dialog.show_error(error_type, message, details)
    
    def _set_processing_state(self, processing: bool) -> None:
        """Enable/disable UI elements during processing."""
        self.processing_active = processing
        
        # Update button states
        state = tk.DISABLED if processing else tk.NORMAL
        self.ask_button.config(state=state)
        self.import_button.config(state=state)
        
        # Update status
        if processing:
            self.status_manager.set_status("Processing...", "info")
            self.status_manager.show_progress()
        else:
            self.status_manager.hide_progress()
    
    def _clear_results(self) -> None:
        """Clear all result displays."""
        self.answer_display.config(state=tk.NORMAL)
        self.answer_display.delete("1.0", tk.END)
        self.answer_display.config(state=tk.DISABLED)
        
        self.sources_display.config(state=tk.NORMAL)
        self.sources_display.delete("1.0", tk.END)
        self.sources_display.config(state=tk.DISABLED)
        
        self.status_manager.set_status("Ready", "info")
    
    def _cleanup(self) -> None:
        """Clean up resources before closing."""
        if self.agent_coordinator:
            try:
                asyncio.run(self.agent_coordinator.cleanup_agents())
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
    
    def run(self) -> None:
        """Start the GUI event loop."""
        logger.info("Starting GUI application")
        self.status_manager.set_status("Ready", "info")
        self.question_entry.focus()
        self.root.mainloop()