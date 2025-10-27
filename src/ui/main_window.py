"""Main GUI window using tkinter for the questionnaire application."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import asyncio
import queue
import os
import concurrent.futures
from typing import Optional, Callable, Any
import logging
from utils.data_types import Question, ProcessingResult, ExcelProcessingResult, WorkbookData, AgentInitState
from utils.exceptions import (
    AzureServiceError, NetworkError, AuthenticationError, 
    ConfigurationError, ExcelFormatError
)
from utils.logger import setup_logging
from utils.ui_queue import UIUpdateQueue
from utils.asyncio_runner import get_asyncio_runner, shutdown_asyncio_runner
from excel.loader import ExcelLoader
from excel.column_identifier import ColumnIdentifier
# Import ExcelProcessor lazily to avoid slow agent framework imports
# from excel.processor import ExcelProcessor
# Import AgentCoordinator lazily to avoid slow startup
# from agents.workflow_manager import AgentCoordinator
from utils.config import config_manager
# Lazy import: from utils.azure_auth import get_azure_client
from .status_manager import StatusManager
from .dialogs import ErrorDialog
from .workbook_view import WorkbookView


logger = logging.getLogger(__name__)


# Agent initialization constants
AGENT_INIT_MAX_WAIT_SECONDS = 120  # Maximum time to wait for agent initialization
AGENT_INIT_POLL_INTERVAL = 0.5  # How often to check initialization status (seconds)


class UIManager:
    """Main GUI interface for the questionnaire application."""
    
    def __init__(self, agent_coordinator = None, initial_context: str = None, 
                 initial_char_limit: int = None, auto_question: str = None,
                 auto_spreadsheet: str = None):
        """Initialize UI with agent coordinator dependency.
        
        Args:
            agent_coordinator: Pre-initialized agent coordinator (optional).
            initial_context: Initial context value (optional).
            initial_char_limit: Initial character limit value (optional).
            auto_question: Question to process automatically after initialization (optional).
            auto_spreadsheet: Spreadsheet path to process automatically after initialization (optional).
        """
        self.agent_coordinator = agent_coordinator
        
        # Store auto-start settings
        self.auto_question = auto_question
        self.auto_spreadsheet = auto_spreadsheet
        
        # Agent initialization state tracking
        self.agent_init_state = AgentInitState.NOT_STARTED
        self.agent_init_error: Optional[str] = None
        self.agent_init_future = None
        
        # Enable high DPI awareness on Windows for better rendering
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass  # Ignore errors on non-Windows platforms or if not available
        
        self.root = tk.Tk()
        self.status_manager: Optional[StatusManager] = None
        self.error_dialog: Optional[ErrorDialog] = None
        self.processing_active = False
        
        # Asyncio thread runner for proper event loop management
        self.asyncio_runner = get_asyncio_runner()
        
        # UI components
        self.question_entry: Optional[scrolledtext.ScrolledText] = None
        self.ask_button: Optional[ttk.Button] = None
        self.import_button: Optional[ttk.Button] = None
        self.answer_display: Optional[scrolledtext.ScrolledText] = None
        self.sources_display: Optional[scrolledtext.ScrolledText] = None
        self.reasoning_display: Optional[scrolledtext.ScrolledText] = None
        self.char_limit_entry: Optional[ttk.Entry] = None
        self.max_retries_entry: Optional[ttk.Entry] = None
        
        # Excel processing components
        self.workbook_view: Optional[WorkbookView] = None
        self.ui_update_queue: Optional[UIUpdateQueue] = None
        self.current_workbook_data: Optional[WorkbookData] = None
        self._temp_workbook_data: Optional[WorkbookData] = None
        self.current_excel_processor: Optional[Any] = None  # Store current processor for cancellation
        
        # Settings
        self.char_limit_var = tk.IntVar(value=initial_char_limit if initial_char_limit is not None else 2000)
        self.context_var = tk.StringVar(value=initial_context if initial_context is not None else "Microsoft Azure AI")
        self.max_retries_var = tk.IntVar(value=10)
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the main GUI layout."""
        self.root.title("Questionnaire Answerer (Microsoft Agent Framework)")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Maximize window based on OS
        import platform
        try:
            if platform.system() == "Windows":
                self.root.state('zoomed')  # Windows maximized
            elif platform.system() == "Linux":
                self.root.attributes('-zoomed', True)  # Linux maximized
            elif platform.system() == "Darwin":  # macOS
                self.root.attributes('-zoomed', True)  # macOS maximized
        except tk.TclError:
            # Fallback if maximizing fails - just use the geometry
            pass
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Set lighter background color for the window
        light_gray = "#ebebeb"
        self.root.configure(bg=light_gray)
        style.configure("TFrame", background=light_gray)
        style.configure("TLabel", background=light_gray)
        style.configure("TLabelframe", background=light_gray)
        style.configure("TLabelframe.Label", background=light_gray)
        style.configure("TNotebook", background=light_gray)
        # Configure tab colors: inactive tabs darker, active tab very light
        style.configure("TNotebook.Tab", background="#d0d0d0", foreground="black")
        style.map("TNotebook.Tab", 
                  background=[("selected", "#ffffff")],
                  foreground=[("selected", "black")])
        style.configure("TPanedwindow", background=light_gray)
        style.configure("Sash", sashthickness=5, background=light_gray)
        
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
        
        # Create status bar container frame
        status_container = ttk.Frame(self.root)
        status_container.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Initialize status manager and error dialog
        self.status_manager = StatusManager(status_container)
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
        
        self.char_limit_entry = ttk.Entry(
            parent,
            textvariable=self.char_limit_var,
            width=40
        )
        self.char_limit_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Maximum Retries section
        retries_label = ttk.Label(parent, text="Maximum Retries")
        retries_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.max_retries_entry = ttk.Entry(
            parent,
            textvariable=self.max_retries_var,
            width=40
        )
        self.max_retries_entry.pack(fill=tk.X, pady=(0, 15))
        
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
        self.question_entry.insert(tk.END, "How many languages does your text-to-speech service support?")
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
        self.results_notebook = ttk.Notebook(parent)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Answer tab
        answer_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(answer_frame, text="Answer")
        
        self.answer_display = scrolledtext.ScrolledText(
            answer_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            state=tk.DISABLED
        )
        self.answer_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Documentation tab (store reference to the frame)
        self.docs_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.docs_frame, text="Documentation")
        
        self.sources_display = scrolledtext.ScrolledText(
            self.docs_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            state=tk.DISABLED
        )
        self.sources_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Reasoning tab
        reasoning_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(reasoning_frame, text="Reasoning")
        
        self.reasoning_display = scrolledtext.ScrolledText(
            reasoning_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 11),  # Changed to match other tabs
            state=tk.DISABLED,
            bg="white"  # White background for better readability
        )
        self.reasoning_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for colored agent names
        self.reasoning_display.tag_configure("agent_name_black", foreground="black", font=("Segoe UI", 11, "bold"))
        self.reasoning_display.tag_configure("agent_name_green", foreground="green", font=("Segoe UI", 11, "bold"))
        self.reasoning_display.tag_configure("agent_name_blue", foreground="blue", font=("Segoe UI", 11, "bold"))
    
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
        
        # Clear reasoning display
        self._clear_reasoning_display()
        context = self.context_var.get()
        self.update_reasoning(f"Starting single question processing with context '{context}': '{question_text[:100]}...'")
        
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
            # Load and display Excel file immediately on main thread (no threading!)
            try:
                self._load_and_display_excel_sync(file_path)
                
                # Then start async processing in background
                self._set_processing_state(True, is_spreadsheet=True)
                self._start_async_excel_processing(file_path)
                
            except Exception as e:
                logger.error(f"Error loading Excel file: {e}", exc_info=True)
                self.display_error("excel_load_error", f"Failed to load Excel file: {str(e)}")
    
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
        # Always cleanup and close without confirmation, even during processing
        self._cleanup()
        self.root.destroy()
    
    def _process_question_async(self, question_text: str) -> None:
        """Process question asynchronously in background thread."""
        try:
            # Use the asyncio thread runner
            self.asyncio_runner.run_coroutine(
                self._process_question_internal(question_text),
                callback=lambda result: self.root.after(0, self._handle_question_result, result),
                error_callback=lambda e: self.root.after(0, self._handle_processing_error, e)
            )
            
        except Exception as e:
            logger.error(f"Error starting question processing: {e}", exc_info=True)
            # Show error on main thread
            self.root.after(0, self._handle_processing_error, e)
    
    def _process_excel_async(self, file_path: str) -> None:
        """Process Excel file asynchronously in background thread."""
        def load_excel_on_main_thread():
            """Load and display Excel file on the main UI thread."""
            try:
                self._load_and_display_excel_sync(file_path)
                
                # After successful UI load, start async agent processing
                self.asyncio_runner.run_coroutine(
                    self._process_excel_agents(file_path),
                    callback=lambda result: self.root.after(0, self._handle_excel_result, result),
                    error_callback=self._handle_excel_error
                )
                
            except Exception as e:
                logger.error(f"Error loading Excel file: {e}", exc_info=True)
                self._handle_processing_error(e)
        
        # Schedule the Excel loading on the main thread
        self.root.after(0, load_excel_on_main_thread)
    
    def _start_async_excel_processing(self, file_path: str) -> None:
        """Start async Excel processing after UI is loaded."""
        def run_async():
            try:
                self.asyncio_runner.run_coroutine(
                    self._process_excel_agents(file_path),
                    callback=lambda result: self.root.after(0, self._handle_excel_result, result),
                    error_callback=self._handle_excel_error
                )
            except Exception as e:
                logger.error(f"Error starting async Excel processing: {e}", exc_info=True)
                self.root.after(0, self._handle_processing_error, e)
        
        # Run the async processing in a background thread
        threading.Thread(target=run_async, daemon=True).start()
    
    def _load_and_display_excel_sync(self, file_path: str) -> None:
        """Load Excel file and display it in the UI immediately (synchronous)."""
        try:
            # Clear reasoning display and add initial message
            self._clear_reasoning_display()
            self.update_reasoning("Loading Excel file...")
            
            # Load workbook with column identification
            self.status_manager.set_status("Loading Excel file...", "info")
            self.update_reasoning(f"Loading Excel file: {file_path}")
            
            # Create column identifier - use Azure client if available for AI-powered identification
            azure_client = None
            if self.agent_coordinator and hasattr(self.agent_coordinator, 'azure_client'):
                azure_client = self.agent_coordinator.azure_client
                self.update_reasoning("Using Azure AI for intelligent column identification")
            else:
                self.update_reasoning("Using heuristic-based column identification (Azure AI not available)")
            
            column_identifier = ColumnIdentifier(azure_client=azure_client)
            loader = ExcelLoader(column_identifier=column_identifier)
            workbook_data = loader.load_workbook(file_path)
            
            # Create UI update queue
            self.ui_update_queue = UIUpdateQueue(maxsize=100)
            self.update_reasoning(f"Loaded workbook with {len(workbook_data.sheets)} sheets, {workbook_data.total_questions} total questions")
            
            # Show workbook immediately
            self.status_manager.set_status("Creating spreadsheet view...", "info")
            print(f"DEBUG: About to show workbook view with {len(workbook_data.sheets)} sheets")
            self._show_workbook_view(workbook_data, self.ui_update_queue)
            print("DEBUG: _show_workbook_view completed")
            self.update_reasoning("Spreadsheet view created - you can now see questions in the Answer tab")
            
            # Store workbook data for async processing
            self._temp_workbook_data = workbook_data
            
            self.status_manager.set_status("Spreadsheet loaded - initializing agents...", "info")
            
        except Exception as e:
            print(f"DEBUG: Error in _load_and_display_excel_sync: {e}")
            logger.error(f"Error in _load_and_display_excel_sync: {e}", exc_info=True)
            self.update_reasoning(f"Error loading Excel file: {e}")
            raise
    
    def _handle_excel_error(self, e: Exception) -> None:
        """Handle Excel processing errors with proper error result creation."""
        if isinstance(e, (FileNotFoundError, ExcelFormatError)):
            logger.error(f"Excel file error: {e}")
            # For file/format errors, create error result and handle normally
            error_result = ExcelProcessingResult(
                success=False,
                error_message=str(e),
                questions_processed=0,
                questions_failed=0
            )
            self.root.after(0, self._handle_excel_result, error_result)
        else:
            logger.error(f"Error in Excel processing: {e}", exc_info=True)
            # Show error on main thread
            self.root.after(0, self._handle_processing_error, e)
    
    async def _process_question_internal(self, question_text: str) -> ProcessingResult:
        """Internal async question processing."""
        # Ensure agent coordinator is available (wait if initializing)
        try:
            await self._ensure_agents_ready()
        except Exception as e:
            logger.error(f"Failed to ensure agents ready: {e}")
            return ProcessingResult(
                success=False,
                error_message=f"Agent initialization failed: {str(e)}",
                processing_time=0.0,
                questions_processed=0,
                questions_failed=1
            )
        
        # Create question object
        question = Question(
            text=question_text,
            context=self.context_var.get(),
            char_limit=self.char_limit_var.get(),
            max_retries=self.max_retries_var.get()
        )
        
        # Process with progress updates
        return await self.agent_coordinator.process_question(
            question, 
            self.update_progress, 
            self.update_reasoning,
            self._display_agent_conversation
        )
    
    async def _process_excel_agents(self, file_path: str) -> ExcelProcessingResult:
        """Process Excel file with agents (async - UI already loaded)."""
        try:
            # Get the workbook data that was loaded synchronously
            workbook_data = self._temp_workbook_data
            
            self.update_reasoning("Starting agent initialization and question processing...")
            
            # Ensure agent coordinator is available (wait if initializing)
            try:
                await self._ensure_agents_ready()
            except Exception as e:
                logger.error(f"Failed to ensure agents ready: {e}")
                return ExcelProcessingResult(
                    success=False,
                    error_message=f"Agent initialization failed: {str(e)}",
                    questions_processed=0,
                    questions_failed=0
                )
            
            # Process workbook (import ExcelProcessor lazily)
            self.update_reasoning("Starting question processing...")
            from excel.processor import ExcelProcessor
            processor = ExcelProcessor(
                self.agent_coordinator, 
                self.ui_update_queue, 
                self.update_reasoning,
                self._display_agent_conversation
            )
            # Store processor reference for cancellation
            self.current_excel_processor = processor
            
            result = await processor.process_workbook(
                workbook_data,
                self.context_var.get(),
                self.char_limit_var.get(),
                self.max_retries_var.get()
            )
            
            # Save workbook if successful
            if result.success:
                self.update_reasoning("Processing complete - prompting for save location...")
                
                # Generate default filename suggestion
                original_dir = os.path.dirname(workbook_data.file_path)
                original_name = os.path.basename(workbook_data.file_path)
                name_without_ext, ext = os.path.splitext(original_name)
                default_name = f"{name_without_ext}_answered{ext}"
                
                # Store the save dialog result in a variable accessible from main thread
                self._save_dialog_result = None
                self._save_dialog_completed = False
                
                def show_save_dialog():
                    """Show Save As dialog on main thread."""
                    default_path = os.path.join(original_dir, default_name)
                    
                    self._save_dialog_result = filedialog.asksaveasfilename(
                        title="Save Completed Questionnaire",
                        defaultextension=ext,
                        initialfile=default_name,
                        initialdir=original_dir,
                        filetypes=[
                            ("Excel files", "*.xlsx *.xls"),
                            ("All files", "*.*")
                        ]
                    )
                    self._save_dialog_completed = True
                
                # Schedule dialog on main thread
                self.root.after(0, show_save_dialog)
                
                # Wait for dialog to complete
                while not self._save_dialog_completed:
                    await asyncio.sleep(0.1)
                
                output_path = self._save_dialog_result
                
                # If user cancelled the dialog, give them a chance to save
                while not output_path:
                    self.update_reasoning("Save cancelled - prompting user...")
                    
                    # Show warning on main thread
                    retry_save = None
                    def show_cancel_warning():
                        nonlocal retry_save
                        retry_save = messagebox.askyesno(
                            "Save Required",
                            "The questionnaire processing is complete.\n\n"
                            "Please choose a location to save the results.\n\n"
                            "Would you like to choose a save location now?",
                            icon='warning'
                        )
                        self._save_dialog_completed = True
                    
                    self._save_dialog_completed = False
                    self.root.after(0, show_cancel_warning)
                    
                    # Wait for response
                    while not self._save_dialog_completed:
                        await asyncio.sleep(0.1)
                    
                    if not retry_save:
                        # User really doesn't want to save - treat as cancellation
                        self.update_reasoning("Save cancelled by user")
                        return ExcelProcessingResult(
                            success=False,
                            error_message="Save cancelled by user",
                            questions_processed=result.questions_processed,
                            questions_failed=result.questions_failed,
                            processing_time=result.processing_time
                        )
                    
                    # Show save dialog again
                    self._save_dialog_completed = False
                    self.root.after(0, show_save_dialog)
                    
                    while not self._save_dialog_completed:
                        await asyncio.sleep(0.1)
                    
                    output_path = self._save_dialog_result
                
                self.update_reasoning(f"Saving results to: {output_path}")
                # Use same Azure client as the agent coordinator for consistency
                azure_client = None
                if self.agent_coordinator and hasattr(self.agent_coordinator, 'azure_client'):
                    azure_client = self.agent_coordinator.azure_client
                
                column_identifier = ColumnIdentifier(azure_client=azure_client)
                loader = ExcelLoader(column_identifier=column_identifier)
                saved_path = loader.save_workbook(workbook_data, output_path)
                
                # Update result with actual output path
                result.output_file_path = saved_path
                
                self.update_reasoning(f"Excel processing completed successfully: {result.questions_processed} processed, {result.questions_failed} failed")
                logger.info(f"Excel processing completed successfully: {result.questions_processed} processed, {result.questions_failed} failed")
            else:
                self.update_reasoning(f"Excel processing failed: {result.error_message}")
            
            return result
            
        except ImportError as e:
            logger.error(f"Import error in Excel processing: {e}", exc_info=True)
            return ExcelProcessingResult(
                success=False,
                error_message=f"Failed to import required components: {str(e)}",
                questions_processed=0,
                questions_failed=0
            )
        
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout in Excel processing: {e}", exc_info=True)
            return ExcelProcessingResult(
                success=False,
                error_message="Processing timed out. Please check your Azure configuration and network connection.",
                questions_processed=0,
                questions_failed=0
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in Excel processing: {e}", exc_info=True)
            return ExcelProcessingResult(
                success=False,
                error_message=f"Processing failed: {str(e)}",
                questions_processed=0,
                questions_failed=0
            )
        finally:
            # Clear the processor reference
            self.current_excel_processor = None
    
    def _handle_question_result(self, result: ProcessingResult) -> None:
        """Handle question processing result on main thread."""
        try:
            if result.success and result.answer:
                self.update_reasoning("Question processing completed successfully!")
                
                # Display rich text conversation from agent steps
                if result.answer.agent_reasoning:
                    self._display_agent_conversation(
                        result.answer.agent_reasoning,
                        result.answer.documentation_links
                    )
                
                self.display_answer(result.answer.content, result.answer.sources)
                self.status_manager.set_status(f"Processing completed successfully in {result.processing_time:.1f}s", "success")
            else:
                self.update_reasoning(f"Question processing failed: {result.error_message}")
                self.display_error("processing", result.error_message or "Unknown processing error")
                self.status_manager.set_status("Processing failed", "error")
        
        finally:
            self._set_processing_state(False)
    
    def _show_workbook_view(self, workbook_data: WorkbookData, ui_queue: UIUpdateQueue) -> None:
        """Replace answer_display with WorkbookView (main thread only).
        
        Args:
            workbook_data: WorkbookData to display
            ui_queue: UI update queue for live updates
        """
        try:
            print(f"DEBUG: Starting to show workbook view with {len(workbook_data.sheets)} sheets")
            logger.info(f"Starting to show workbook view with {len(workbook_data.sheets)} sheets")
            
            # Store current workbook data
            self.current_workbook_data = workbook_data
            
            # Get the answer frame (parent of answer_display)
            answer_frame = self.answer_display.master if self.answer_display else None
            print(f"DEBUG: answer_frame = {answer_frame}")
            print(f"DEBUG: self.answer_display = {self.answer_display}")
            
            if not answer_frame:
                print("DEBUG: Could not find answer frame")
                logger.error("Could not find answer frame")
                return
            
            # COMPLETELY clear and destroy all widgets from the answer frame
            print(f"DEBUG: Destroying {len(answer_frame.winfo_children())} widgets from answer frame")
            for widget in answer_frame.winfo_children():
                print(f"DEBUG: Destroying widget: {widget}")
                widget.destroy()  # Use destroy() instead of pack_forget()
            
            print("DEBUG: All widgets destroyed from answer frame")
            logger.info("Cleared answer frame contents")
            
            # Create and show WorkbookView directly in the answer frame
            print(f"DEBUG: Creating WorkbookView with parent: {answer_frame}")
            logger.info(f"Creating WorkbookView with parent: {answer_frame}")
            
            self.workbook_view = WorkbookView(
                answer_frame,
                workbook_data,
                ui_queue
            )
            print("DEBUG: WorkbookView created, rendering notebook...")
            logger.info("WorkbookView created, rendering notebook...")
            
            notebook = self.workbook_view.render()
            print(f"DEBUG: Notebook rendered: {notebook}")
            logger.info(f"Notebook rendered: {notebook}")
            
            # Pack the notebook to fill the entire answer frame
            notebook.pack(fill=tk.BOTH, expand=True)
            print("DEBUG: Notebook packed in answer frame")
            logger.info("Notebook packed in answer frame")
            
            # Start polling for updates
            self.workbook_view.start_update_polling()
            print("DEBUG: Update polling started")
            logger.info("Update polling started")
            
            # Force UI update
            answer_frame.update_idletasks()
            self.root.update_idletasks()
            print("DEBUG: UI update forced")
            
            # Force switch to Answer tab and verify visibility
            print(f"DEBUG: Forcing switch to Answer tab")
            self.results_notebook.select(0)  # Select Answer tab (index 0)
            print(f"DEBUG: Current tab: {self.results_notebook.index(self.results_notebook.select())}")
            print(f"DEBUG: Answer frame children after packing: {[str(child) for child in answer_frame.winfo_children()]}")
            print(f"DEBUG: Notebook children: {[str(child) for child in notebook.winfo_children()]}")
            
            # Debug geometry information
            print(f"DEBUG: Answer frame geometry: {answer_frame.winfo_width()}x{answer_frame.winfo_height()}")
            print(f"DEBUG: Notebook geometry: {notebook.winfo_width()}x{notebook.winfo_height()}")
            print(f"DEBUG: Notebook is visible: {notebook.winfo_viewable()}")
            print(f"DEBUG: Answer frame is visible: {answer_frame.winfo_viewable()}")
            
            # Force notebook to be visible and update
            notebook.lift()
            notebook.update_idletasks()
            answer_frame.lift()
            answer_frame.update_idletasks()
            self.root.update()
            
            print(f"DEBUG: Successfully displayed workbook view with {len(workbook_data.sheets)} sheets")
            logger.info(f"Successfully displayed workbook view with {len(workbook_data.sheets)} sheets")
            
        except Exception as e:
            print(f"DEBUG: Error showing workbook view: {e}")
            logger.error(f"Error showing workbook view: {e}", exc_info=True)
            self.display_error("ui_error", f"Failed to display Excel file: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _restore_answer_display(self) -> None:
        """Restore the original answer display after Excel processing."""
        try:
            # Cleanup workbook view
            if self.workbook_view:
                self.workbook_view.destroy()
                self.workbook_view = None
            
            # Clear workbook data
            self.current_workbook_data = None
            
            # Close UI queue
            if self.ui_update_queue:
                self.ui_update_queue.close()
                self.ui_update_queue = None
            
            # Show answer display again
            if self.answer_display:
                self.answer_display.pack(fill=tk.BOTH, expand=True)
            
            logger.info("Restored original answer display")
            
        except Exception as e:
            logger.error(f"Error restoring answer display: {e}", exc_info=True)
    
    def _handle_excel_result(self, result: ExcelProcessingResult) -> None:
        """Handle Excel processing result on main thread."""
        try:
            if result.success:
                # Display simplified Excel results summary (user already chose save location)
                summary = f"Excel processing completed successfully!\n\n"
                summary += f"Questions processed: {result.questions_processed}\n"
                summary += f"Questions failed: {result.questions_failed}\n"
                summary += f"Processing time: {result.processing_time:.1f} seconds"
                
                # Show completion message but keep workbook view visible
                messagebox.showinfo("Excel Processing Complete", summary)
                self.status_manager.set_status("Excel processing completed", "success")
            else:
                # Show error and restore answer display
                self._restore_answer_display()
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
    
    def _append_reasoning_text(self, text: str) -> None:
        """Append text to reasoning display (main thread only).
        
        Args:
            text: Text to append.
        """
        try:
            if self.reasoning_display:
                self.reasoning_display.config(state=tk.NORMAL)
                self.reasoning_display.insert(tk.END, text)
                self.reasoning_display.see(tk.END)  # Auto-scroll to bottom
                self.reasoning_display.config(state=tk.DISABLED)
            else:
                logger.warning("Reasoning display not available")
        except Exception as e:
            logger.error(f"Error appending to reasoning display: {e}")
    
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
            sources_text = ""
        
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
    
    def update_progress(self, agent: str, message: str, progress: float) -> None:
        """Update UI with current processing progress.
        
        Args:
            agent: Current agent name.
            message: Status message.
            progress: Completion percentage (0.0 to 1.0).
        """
        # Update status manager on main thread
        self.root.after(0, self.status_manager.update_progress, agent, message, progress)
    
    def update_reasoning(self, message: str) -> None:
        """Update the reasoning display with agent processing details.
        
        Args:
            message: Reasoning message to display.
        """
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            
            # Update on main thread
            self.root.after(0, self._append_reasoning_text, formatted_message)
            
            # Also log to console for debugging
            logger.info(f"UI Reasoning: {message}")
        except Exception as e:
            logger.error(f"Error updating reasoning display: {e}")
    
    def _display_agent_conversation(self, agent_steps: list, documentation_links: list = None) -> None:
        """Display agent conversation in rich text format.
        
        Args:
            agent_steps: List of AgentStep objects from the workflow.
            documentation_links: Optional list of DocumentationLink objects.
        """
        try:
            from utils.reasoning_formatter import ReasoningFormatter
            
            # Format the agent steps
            formatted_steps = ReasoningFormatter.format_agent_steps(agent_steps, documentation_links)
            
            if not formatted_steps:
                return
            
            # Update on main thread
            self.root.after(0, self._render_agent_conversation, formatted_steps)
            
        except Exception as e:
            logger.error(f"Error displaying agent conversation: {e}", exc_info=True)
    
    def _render_agent_conversation(self, formatted_steps: list) -> None:
        """Render the formatted agent conversation in the reasoning display.
        
        Args:
            formatted_steps: List of (agent_name, content, color) tuples.
        """
        try:
            if not self.reasoning_display:
                logger.warning("Reasoning display not available")
                return
            
            self.reasoning_display.config(state=tk.NORMAL)
            
            # Render each agent step
            for agent_name, content, color in formatted_steps:
                # Map color to tag name
                tag_name = f"agent_name_{color}"
                
                # Insert agent name in bold and colored (without asterisks)
                self.reasoning_display.insert(tk.END, f"{agent_name}: ", tag_name)
                
                # Insert content in normal text
                self.reasoning_display.insert(tk.END, f"{content}\n\n")
            
            # Auto-scroll to bottom
            self.reasoning_display.see(tk.END)
            self.reasoning_display.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Error rendering agent conversation: {e}", exc_info=True)
    
    def _clear_reasoning_display(self) -> None:
        """Clear the reasoning display (main thread only)."""
        try:
            if self.reasoning_display:
                self.reasoning_display.config(state=tk.NORMAL)
                self.reasoning_display.delete("1.0", tk.END)
                self.reasoning_display.config(state=tk.DISABLED)
        except Exception as e:
            logger.error(f"Error clearing reasoning display: {e}")
    
    def _set_processing_state(self, processing: bool, is_spreadsheet: bool = False) -> None:
        """Enable/disable UI elements during processing.
        
        Args:
            processing: Whether processing is active
            is_spreadsheet: Whether this is spreadsheet processing (vs single question)
        """
        self.processing_active = processing
        
        if processing and is_spreadsheet:
            # Spreadsheet mode: special UI state
            # Clear and disable question entry
            self.question_entry.delete("1.0", tk.END)
            self.question_entry.config(state=tk.DISABLED, bg="#f0f0f0")
            
            # Disable character limit and max retries (keep values visible)
            self.char_limit_entry.config(state=tk.DISABLED)
            self.max_retries_entry.config(state=tk.DISABLED)
            
            # Hide Documentation tab
            self._hide_documentation_tab()
            
            # Change Ask button to Stop button
            self.ask_button.config(text="Stop", command=self._on_stop_clicked, state=tk.NORMAL)
            
            # Disable Import button
            self.import_button.config(state=tk.DISABLED)
        elif processing:
            # Single question mode: disable all buttons
            state = tk.DISABLED
            self.ask_button.config(state=state)
            self.import_button.config(state=state)
        else:
            # Not processing: restore normal state
            # Re-enable question entry
            self.question_entry.config(state=tk.NORMAL, bg="white")
            
            # Re-enable character limit and max retries
            self.char_limit_entry.config(state=tk.NORMAL)
            self.max_retries_entry.config(state=tk.NORMAL)
            
            # Show Documentation tab
            self._show_documentation_tab()
            
            # Restore Ask button
            self.ask_button.config(text="Ask!", command=self._on_ask_clicked, state=tk.NORMAL)
            
            # Re-enable Import button
            self.import_button.config(state=tk.NORMAL)
        
        # Update status
        if processing:
            self.status_manager.set_status("Processing...", "info")
            self.status_manager.show_progress()
        else:
            self.status_manager.hide_progress()
    
    def _hide_documentation_tab(self) -> None:
        """Hide the Documentation tab during spreadsheet processing."""
        try:
            # Find the Documentation tab index
            for i in range(self.results_notebook.index("end")):
                if self.results_notebook.tab(i, "text") == "Documentation":
                    self.results_notebook.hide(i)
                    break
        except Exception as e:
            logger.error(f"Error hiding Documentation tab: {e}")
    
    def _show_documentation_tab(self) -> None:
        """Show the Documentation tab after spreadsheet processing."""
        try:
            # Find the Documentation tab index
            for i in range(self.results_notebook.index("end")):
                if self.results_notebook.tab(i, "text") == "Documentation":
                    self.results_notebook.add(self.docs_frame, text="Documentation")
                    break
        except Exception as e:
            logger.error(f"Error showing Documentation tab: {e}")
    
    def _on_stop_clicked(self) -> None:
        """Handle Stop button click during spreadsheet processing."""
        if not self.processing_active:
            return
        
        # Cancel the current processing
        if self.current_excel_processor:
            logger.info("Stop button clicked - cancelling Excel processing")
            self.update_reasoning("Stop requested - cancelling spreadsheet processing...")
            self.current_excel_processor.cancel_processing()
            
            # UI will be restored when processing completes
            self.status_manager.set_status("Cancelling processing...", "info")
    
    def _clear_results(self) -> None:
        """Clear all result displays."""
        self.answer_display.config(state=tk.NORMAL)
        self.answer_display.delete("1.0", tk.END)
        self.answer_display.config(state=tk.DISABLED)
        
        self.sources_display.config(state=tk.NORMAL)
        self.sources_display.delete("1.0", tk.END)
        self.sources_display.config(state=tk.DISABLED)
        
        if self.reasoning_display:
            self.reasoning_display.config(state=tk.NORMAL)
            self.reasoning_display.delete("1.0", tk.END)
            self.reasoning_display.config(state=tk.DISABLED)
        
        self.status_manager.set_status("Ready", "info")
    
    def _cleanup(self) -> None:
        """Clean up resources before closing."""
        if self.agent_coordinator:
            try:
                # Run cleanup synchronously to ensure it completes before window closes
                logger.info("Starting agent cleanup...")
                
                # Create a future to track completion
                cleanup_future = concurrent.futures.Future()
                
                def cleanup_complete(result):
                    logger.info(f"Agent cleanup completed successfully: {result}")
                    cleanup_future.set_result(True)
                
                def cleanup_error(e):
                    logger.warning(f"Error during agent cleanup: {e}")
                    cleanup_future.set_exception(e)
                
                self.asyncio_runner.run_coroutine(
                    self.agent_coordinator.cleanup_agents(),
                    callback=cleanup_complete,
                    error_callback=cleanup_error
                )
                
                # Wait for cleanup to complete (with timeout)
                try:
                    cleanup_future.result(timeout=5.0)
                except concurrent.futures.TimeoutError:
                    logger.warning("Agent cleanup timed out after 5 seconds")
                except Exception as e:
                    logger.warning(f"Agent cleanup failed: {e}")
                    
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
        
        # Shutdown the asyncio runner
        try:
            self.asyncio_runner.shutdown()
        except Exception as e:
            logger.warning(f"Error shutting down asyncio runner: {e}")
    
    def _start_agent_initialization(self) -> None:
        """Start agent initialization asynchronously in background."""
        if self.agent_coordinator or self.agent_init_state != AgentInitState.NOT_STARTED:
            # Already have coordinator or initialization already started/completed
            return
        
        logger.info("Starting background agent initialization...")
        self.agent_init_state = AgentInitState.IN_PROGRESS
        self.status_manager.set_status("Initializing agents in background...", "info")
        self.update_reasoning("Starting agent initialization in background...")
        
        # Start async initialization in background thread
        threading.Thread(
            target=self._initialize_agents_async,
            daemon=True
        ).start()
    
    def _initialize_agents_async(self) -> None:
        """Initialize agents asynchronously in background thread."""
        try:
            # Use the asyncio thread runner
            self.asyncio_runner.run_coroutine(
                self._create_agent_coordinator(),
                callback=lambda result: self.root.after(0, self._handle_agent_init_success, result),
                error_callback=lambda e: self.root.after(0, self._handle_agent_init_error, e)
            )
        except Exception as e:
            logger.error(f"Error starting agent initialization: {e}", exc_info=True)
            self.root.after(0, self._handle_agent_init_error, e)
    
    async def _create_agent_coordinator(self):
        """Create agent coordinator with proper initialization."""
        self.update_reasoning("Initializing Azure AI agents... (this may take 30-60 seconds)")
        
        # Lazy import to avoid slow startup
        from utils.azure_auth import get_azure_client
        
        azure_client = await get_azure_client()
        bing_connection_id = config_manager.get_bing_connection_id()
        browser_automation_connection_id = config_manager.get_browser_automation_connection_id()
        
        from agents.workflow_manager import create_agent_coordinator
        coordinator = await create_agent_coordinator(azure_client, bing_connection_id, 
                                                     browser_automation_connection_id)
        
        self.update_reasoning("Azure AI agents initialized successfully")
        return coordinator
    
    def _handle_agent_init_success(self, coordinator) -> None:
        """Handle successful agent initialization on main thread."""
        self.agent_coordinator = coordinator
        self.agent_init_state = AgentInitState.COMPLETED
        self.status_manager.set_status("Ready - Agents initialized", "success")
        self.update_reasoning("✅ Agent initialization completed - ready to process questions")
        logger.info("Agent initialization completed successfully")
    
    def _handle_agent_init_error(self, error: Exception) -> None:
        """Handle agent initialization error on main thread."""
        self.agent_init_state = AgentInitState.FAILED
        self.agent_init_error = str(error)
        self.status_manager.set_status("Agent initialization failed", "error")
        self.update_reasoning(f"❌ Agent initialization failed: {error}")
        logger.error(f"Agent initialization failed: {error}", exc_info=True)
    
    def _check_and_auto_start(self) -> None:
        """Check if agents are ready and start auto-processing if requested."""
        if self.agent_init_state == AgentInitState.IN_PROGRESS:
            # Still initializing, check again later
            self.root.after(500, self._check_and_auto_start)
            return
        
        if self.agent_init_state == AgentInitState.FAILED:
            # Initialization failed, cannot auto-start
            logger.error("Cannot auto-start: agent initialization failed")
            self.update_reasoning("❌ Cannot auto-start: agent initialization failed")
            return
        
        if self.agent_init_state == AgentInitState.COMPLETED:
            # Agents ready, start auto-processing
            if self.auto_spreadsheet:
                self.update_reasoning(f"Auto-starting spreadsheet processing: {self.auto_spreadsheet}")
                self._auto_start_spreadsheet()
            elif self.auto_question:
                # Set the question in the entry field
                self.question_entry.delete("1.0", tk.END)
                self.question_entry.insert("1.0", self.auto_question)
                self.update_reasoning(f"Auto-starting question processing: {self.auto_question}")
                self._on_ask_clicked()
    
    def _auto_start_spreadsheet(self) -> None:
        """Start spreadsheet processing automatically."""
        if not self.auto_spreadsheet:
            return
        
        file_path = self.auto_spreadsheet
        
        # Validate file exists
        if not os.path.exists(file_path):
            logger.error(f"Auto-start spreadsheet file not found: {file_path}")
            self.display_error("file_not_found", f"Spreadsheet file not found: {file_path}")
            return
        
        # Load and display Excel file immediately on main thread
        try:
            self._load_and_display_excel_sync(file_path)
            
            # Then start async processing in background
            self._set_processing_state(True, is_spreadsheet=True)
            self._start_async_excel_processing(file_path)
            
        except Exception as e:
            logger.error(f"Error auto-starting Excel file: {e}", exc_info=True)
            self.display_error("excel_load_error", f"Failed to load Excel file: {str(e)}")
    
    async def _ensure_agents_ready(self) -> None:
        """Ensure agents are initialized, waiting if necessary.
        
        Raises:
            Exception: If agent initialization failed.
        """
        if self.agent_coordinator:
            # Already initialized
            return
        
        if self.agent_init_state == AgentInitState.COMPLETED:
            # Should have coordinator but don't - this is unexpected
            if not self.agent_coordinator:
                logger.warning("Agent init state is 'completed' but no coordinator - reinitializing")
                self.agent_init_state = AgentInitState.NOT_STARTED
        
        if self.agent_init_state == AgentInitState.FAILED:
            # Previous initialization failed - raise error
            error_msg = f"Agent initialization previously failed: {self.agent_init_error}"
            raise Exception(error_msg)
        
        if self.agent_init_state == AgentInitState.NOT_STARTED:
            # Not started yet - start now and wait
            self.update_reasoning("Agents not yet initialized - starting initialization now...")
            await self._create_agent_coordinator_sync()
            return
        
        if self.agent_init_state == AgentInitState.IN_PROGRESS:
            # Initialization in progress - wait for it to complete
            self.update_reasoning("Waiting for agent initialization to complete...")
            logger.info("Waiting for agent initialization to complete...")
            
            # Poll until initialization completes or fails
            elapsed = 0.0
            
            while self.agent_init_state == AgentInitState.IN_PROGRESS and elapsed < AGENT_INIT_MAX_WAIT_SECONDS:
                await asyncio.sleep(AGENT_INIT_POLL_INTERVAL)
                elapsed += AGENT_INIT_POLL_INTERVAL
            
            if self.agent_init_state == AgentInitState.COMPLETED:
                if self.agent_coordinator:
                    self.update_reasoning("✅ Agent initialization completed")
                    return
                else:
                    # State is completed but no coordinator - shouldn't happen
                    raise Exception("Agent initialization completed but coordinator not available")
            elif self.agent_init_state == AgentInitState.FAILED:
                raise Exception(f"Agent initialization failed: {self.agent_init_error}")
            else:
                # Timed out waiting
                raise Exception(f"Timed out waiting for agent initialization after {AGENT_INIT_MAX_WAIT_SECONDS}s")
    
    async def _create_agent_coordinator_sync(self):
        """Create agent coordinator synchronously (blocking)."""
        self.agent_init_state = AgentInitState.IN_PROGRESS
        try:
            coordinator = await self._create_agent_coordinator()
            self.agent_coordinator = coordinator
            self.agent_init_state = AgentInitState.COMPLETED
        except Exception as e:
            self.agent_init_state = AgentInitState.FAILED
            self.agent_init_error = str(e)
            raise
    
    def run(self) -> None:
        """Start the GUI event loop."""
        logger.info("Starting GUI application")
        self.status_manager.set_status("Ready", "info")
        self.question_entry.focus()
        
        # Start agent initialization in background
        self._start_agent_initialization()
        
        # Schedule auto-start processing if requested
        if self.auto_question or self.auto_spreadsheet:
            self.root.after(500, self._check_and_auto_start)
        
        self.root.mainloop()