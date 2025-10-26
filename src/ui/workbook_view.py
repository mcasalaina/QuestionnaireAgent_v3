"""Workbook view with multiple sheet tabs using tkinter Notebook."""

import tkinter as tk
from tkinter import ttk
import queue
from typing import Optional, List
from utils.data_types import WorkbookData, NavigationState, UIUpdateEvent, CellState
from utils.ui_queue import UIUpdateQueue
from .spreadsheet_view import SpreadsheetView
import logging

logger = logging.getLogger(__name__)


class WorkbookView:
    """Multi-sheet workbook view with tab navigation and live updates."""
    
    POLL_INTERVAL_MS = 50  # Poll UI queue every 50ms
    SPINNER_CHAR = "⟳"  # Unicode spinner character
    MAX_TAB_NAME_LENGTH = 20  # Maximum characters for tab names
    
    def __init__(
        self,
        parent: tk.Widget,
        workbook_data: WorkbookData,
        ui_update_queue: UIUpdateQueue
    ):
        """Initialize workbook view.
        
        Args:
            parent: Parent tkinter widget
            workbook_data: Complete workbook data
            ui_update_queue: Queue for receiving UI updates
        """
        self.parent = parent
        self.workbook_data = workbook_data
        self.ui_update_queue = ui_update_queue
        self.navigation_state = NavigationState()
        
        self.notebook: Optional[ttk.Notebook] = None
        self.sheet_views: List[SpreadsheetView] = []
        self.sheet_frames: List[ttk.Frame] = []
        self.is_polling = False
        self.poll_after_id: Optional[str] = None
    
    def render(self) -> ttk.Notebook:
        """Create notebook with all sheet tabs.
        
        Returns:
            Configured Notebook widget ready for display
        """
        # Create a custom style for this notebook to position tabs at bottom
        style = ttk.Style()
        style.configure('WorkbookNotebook.TNotebook', tabposition='s')  # 's' = south (bottom)
        
        # Create notebook widget with custom style
        self.notebook = ttk.Notebook(self.parent, style='WorkbookNotebook.TNotebook')
        
        # Create a frame and SpreadsheetView for each sheet
        for sheet_idx, sheet_data in enumerate(self.workbook_data.sheets):
            # Create frame for this sheet
            frame = ttk.Frame(self.notebook)
            self.sheet_frames.append(frame)
            
            # Create SpreadsheetView for this sheet
            spreadsheet_view = SpreadsheetView(frame, sheet_data)
            treeview = spreadsheet_view.render()
            self.sheet_views.append(spreadsheet_view)
            
            # Add tab with truncated name if necessary
            tab_text = self._get_tab_text(sheet_data.sheet_name, is_processing=False)
            self.notebook.add(frame, text=tab_text)
            
            logger.debug(f"Added tab for sheet '{sheet_data.sheet_name}' (index: {sheet_idx})")
        
        # Bind tab change event to handle user navigation
        self.notebook.bind('<<NotebookTabChanged>>', self._handle_user_tab_click)
        
        logger.info(f"Rendered workbook view with {len(self.workbook_data.sheets)} sheets")
        
        return self.notebook
    
    def _get_tab_text(self, sheet_name: str, is_processing: bool) -> str:
        """Get display text for a tab, handling truncation and spinner.
        
        Args:
            sheet_name: Original sheet name
            is_processing: Whether to show spinner
            
        Returns:
            Formatted tab text
        """
        # Truncate long sheet names
        if len(sheet_name) > self.MAX_TAB_NAME_LENGTH:
            display_name = sheet_name[:self.MAX_TAB_NAME_LENGTH - 3] + "..."
        else:
            display_name = sheet_name
        
        # Add spinner if processing
        if is_processing:
            return f"{display_name} {self.SPINNER_CHAR}"
        else:
            return display_name
    
    def navigate_to_sheet(self, sheet_index: int) -> None:
        """Switch visible tab to specified sheet if auto-navigation enabled.
        
        Args:
            sheet_index: Zero-based sheet index
        """
        if not self.navigation_state.auto_navigation_enabled:
            logger.debug(f"Auto-navigation disabled, not switching to sheet {sheet_index}")
            return
        
        if not self.notebook:
            logger.error("Cannot navigate: notebook not initialized")
            return
        
        if 0 <= sheet_index < len(self.sheet_views):
            try:
                self.notebook.select(sheet_index)
                logger.info(f"Auto-navigated to sheet {sheet_index}")
            except Exception as e:
                logger.error(f"Failed to navigate to sheet {sheet_index}: {e}")
    
    def update_tab_indicator(self, sheet_index: int, is_processing: bool) -> None:
        """Add or remove spinner indicator on tab.
        
        Args:
            sheet_index: Zero-based sheet index
            is_processing: True to show spinner, False to hide
        """
        if not self.notebook:
            logger.error("Cannot update tab: notebook not initialized")
            return
        
        if 0 <= sheet_index < len(self.workbook_data.sheets):
            sheet_name = self.workbook_data.sheets[sheet_index].sheet_name
            tab_text = self._get_tab_text(sheet_name, is_processing)
            
            try:
                self.notebook.tab(sheet_index, text=tab_text)
                logger.debug(f"Updated tab {sheet_index} indicator: processing={is_processing}")
            except Exception as e:
                logger.error(f"Failed to update tab {sheet_index}: {e}")
    
    def _handle_user_tab_click(self, event: tk.Event) -> None:
        """Handle user clicking a sheet tab.
        
        Args:
            event: Notebook tab change event
        """
        if not self.notebook:
            return
        
        try:
            selected_index = self.notebook.index(self.notebook.select())
            self.navigation_state.lock_to_sheet(selected_index)
            logger.info(f"User selected sheet {selected_index}, auto-navigation disabled")
        except Exception as e:
            logger.error(f"Error handling tab click: {e}")
    
    def start_update_polling(self) -> None:
        """Begin polling ui_update_queue for events."""
        if self.is_polling:
            logger.warning("Update polling already started")
            return
        
        self.is_polling = True
        self._poll_queue()
        logger.info("Started UI update polling")
    
    def stop_update_polling(self) -> None:
        """Stop polling the update queue."""
        self.is_polling = False
        if self.poll_after_id:
            self.parent.after_cancel(self.poll_after_id)
            self.poll_after_id = None
        logger.info("Stopped UI update polling")
    
    def _poll_queue(self) -> None:
        """Poll queue and process events (main thread only)."""
        if not self.is_polling:
            return
        
        try:
            # Process all available events in this cycle
            events_processed = 0
            max_events_per_cycle = 10  # Prevent blocking UI
            
            while events_processed < max_events_per_cycle:
                try:
                    event = self.ui_update_queue.get_nowait()
                    self._process_event(event)
                    events_processed += 1
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error processing UI event: {e}")
                    break
            
            if events_processed > 0:
                logger.debug(f"Processed {events_processed} UI events")
        
        except Exception as e:
            logger.error(f"Error in queue polling: {e}")
        
        finally:
            # Schedule next poll
            if self.is_polling:
                self.poll_after_id = self.parent.after(self.POLL_INTERVAL_MS, self._poll_queue)
    
    def _process_event(self, event: UIUpdateEvent) -> None:
        """Process a single UI update event.
        
        Args:
            event: UIUpdateEvent to process
        """
        event_type = event.event_type
        payload = event.payload
        
        logger.debug(f"Processing UI event: {event_type}")
        
        try:
            if event_type == 'SHEET_START':
                self._handle_sheet_start(payload)
            
            elif event_type == 'CELL_WORKING':
                self._handle_cell_working(payload)
            
            elif event_type == 'CELL_COMPLETED':
                self._handle_cell_completed(payload)
            
            elif event_type == 'SHEET_COMPLETE':
                self._handle_sheet_complete(payload)
            
            elif event_type == 'WORKBOOK_COMPLETE':
                self._handle_workbook_complete(payload)
            
            elif event_type == 'ERROR':
                self._handle_error(payload)
            
            else:
                logger.warning(f"Unknown event type: {event_type}")
        
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}")
    
    def _handle_sheet_start(self, payload: dict) -> None:
        """Handle SHEET_START event."""
        sheet_idx = payload.get('sheet_index', 0)
        
        # Navigate to the sheet if auto-navigation enabled
        self.navigate_to_sheet(sheet_idx)
        
        # Show spinner on tab
        self.update_tab_indicator(sheet_idx, is_processing=True)
        
        # Update workbook data
        if 0 <= sheet_idx < len(self.workbook_data.sheets):
            self.workbook_data.sheets[sheet_idx].is_processing = True
            self.workbook_data.current_sheet_index = sheet_idx
    
    def _handle_cell_working(self, payload: dict) -> None:
        """Handle CELL_WORKING event."""
        sheet_idx = payload.get('sheet_index', 0)
        row_idx = payload.get('row_index', 0)
        
        if 0 <= sheet_idx < len(self.sheet_views):
            self.sheet_views[sheet_idx].update_cell(row_idx, CellState.WORKING)
    
    def _handle_cell_completed(self, payload: dict) -> None:
        """Handle CELL_COMPLETED event."""
        sheet_idx = payload.get('sheet_index', 0)
        row_idx = payload.get('row_index', 0)
        answer = payload.get('answer', '')
        
        if 0 <= sheet_idx < len(self.sheet_views):
            self.sheet_views[sheet_idx].update_cell(row_idx, CellState.COMPLETED, answer)
    
    def _handle_sheet_complete(self, payload: dict) -> None:
        """Handle SHEET_COMPLETE event."""
        sheet_idx = payload.get('sheet_index', 0)
        
        # Remove spinner from tab
        self.update_tab_indicator(sheet_idx, is_processing=False)
        
        # Update workbook data
        if 0 <= sheet_idx < len(self.workbook_data.sheets):
            self.workbook_data.sheets[sheet_idx].is_processing = False
            self.workbook_data.sheets[sheet_idx].is_complete = True
    
    def _handle_workbook_complete(self, payload: dict) -> None:
        """Handle WORKBOOK_COMPLETE event."""
        file_path = payload.get('file_path', '')
        logger.info(f"Workbook processing completed: {file_path}")
        
        # Re-enable auto-navigation (optional)
        # self.navigation_state.enable_auto_navigation()
    
    def _handle_error(self, payload: dict) -> None:
        """Handle ERROR event."""
        error_type = payload.get('error_type', 'unknown')
        message = payload.get('message', 'Unknown error')
        
        logger.error(f"Processing error ({error_type}): {message}")
        
        # TODO: Show error dialog or status message
        # This would typically call a method on UIManager to show error dialog
    
    def get_current_sheet_index(self) -> int:
        """Get index of currently visible sheet.
        
        Returns:
            Zero-based index of current sheet, or 0 if none selected
        """
        if not self.notebook:
            return 0
        
        try:
            return self.notebook.index(self.notebook.select())
        except Exception:
            return 0
    
    def get_sheet_view(self, sheet_index: int) -> Optional[SpreadsheetView]:
        """Get SpreadsheetView for a specific sheet.
        
        Args:
            sheet_index: Zero-based sheet index
            
        Returns:
            SpreadsheetView instance or None if invalid index
        """
        if 0 <= sheet_index < len(self.sheet_views):
            return self.sheet_views[sheet_index]
        return None
    
    def refresh_all_sheets(self) -> None:
        """Refresh all sheet views from current workbook data."""
        for sheet_view in self.sheet_views:
            sheet_view.refresh()
        logger.debug("Refreshed all sheet views")
    
    def enable_auto_navigation(self) -> None:
        """Re-enable auto-navigation after user override."""
        self.navigation_state.enable_auto_navigation()
        logger.info("Re-enabled auto-navigation")
    
    def is_auto_navigation_enabled(self) -> bool:
        """Check if auto-navigation is currently enabled.
        
        Returns:
            True if auto-navigation is enabled
        """
        return self.navigation_state.auto_navigation_enabled
    
    def destroy(self) -> None:
        """Clean up the workbook view and its resources."""
        # Stop polling
        self.stop_update_polling()
        
        # Destroy sheet views
        for sheet_view in self.sheet_views:
            sheet_view.destroy()
        self.sheet_views.clear()
        
        # Destroy frames
        for frame in self.sheet_frames:
            frame.destroy()
        self.sheet_frames.clear()
        
        # Destroy notebook
        if self.notebook:
            self.notebook.destroy()
            self.notebook = None
        
        logger.info("Destroyed workbook view")