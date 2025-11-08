"""Spreadsheet view using tksheet for single Excel sheet rendering with automatic text wrapping."""

import tkinter as tk
from typing import Optional
from tksheet import Sheet
from utils.data_types import SheetData, CellState
import logging

logger = logging.getLogger(__name__)


class SpreadsheetView:
    """Visual representation of a single Excel sheet using tksheet with automatic text wrapping."""
    
    # Cell background colors for different states
    COLOR_PENDING = "#FFFFFF"      # White
    COLOR_WORKING = "#FFB6C1"      # Pink
    COLOR_COMPLETED = "#90EE90"    # Light green
    
    # Agent name to user-friendly message mapping
    AGENT_MESSAGES = {
        "question_answerer": "𝗔𝗻𝘀𝘄𝗲𝗿𝗶𝗻𝗴...",
        "answer_checker": "𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗔𝗻𝘀𝘄𝗲𝗿...",
        "link_checker": "𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗟𝗶𝗻𝗸𝘀...",
        None: "𝗔𝗻𝘀𝘄𝗲𝗿𝗶𝗻𝗴..."  # Default fallback
    }
    
    def __init__(self, parent: tk.Widget, sheet_data: SheetData):
        """Initialize spreadsheet view.
        
        Args:
            parent: Parent tkinter widget
            sheet_data: Sheet data to render
        """
        self.parent = parent
        self.sheet_data = sheet_data
        self.sheet: Optional[Sheet] = None
        self.frame: Optional[tk.Frame] = None
    
    def render(self) -> Sheet:
        """Create and return configured tksheet widget.
        
        Returns:
            Configured Sheet widget ready for display
        """
        # Create frame to hold sheet
        self.frame = tk.Frame(self.parent)
        
        # Create Sheet widget with better configuration
        self.sheet = Sheet(
            self.frame,
            headers=["Question", "Response"],
            header_height=35,
            default_row_height=30,  # Initial row height (will auto-resize)
            show_top_left=False,
            show_row_index=False,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            auto_resize_columns=True,  # Allow columns to resize
            auto_resize_rows=True,     # KEY: Auto-resize rows for content
            empty_horizontal=0,
            empty_vertical=0,
            page_up_down_select_row=True,
            expand_sheet_if_paste_too_big=True,
            arrow_key_down_right_scroll_page=False,
            displayed_columns=[0, 1],  # Show both columns
            all_columns_displayed=True,
            index_width=0,  # No row index
        )
        
        # Enable features
        self.sheet.enable_bindings(
            "single_select",
            "column_select", 
            "column_width_resize",
            "double_click_column_resize",
            "copy",
            "rc_select",
        )
        
        # Set initial column widths (will auto-resize based on content)
        self.sheet.column_width(column=0, width=400)  # Question column
        self.sheet.column_width(column=1, width=620)  # Response column
        
        # Configure text wrapping and alignment
        self.sheet.set_options(
            wrap_text=True,      # Enable text wrapping
            align="w",           # Left align text
            header_align="center", # Center align headers
            auto_resize_default_row_index=True,
        )
        
        # Populate with data
        self._populate_data()
        
        # Pack the sheet to fill available space
        self.sheet.pack(fill="both", expand=True)
        self.frame.pack(fill="both", expand=True)
        
        logger.debug(f"Rendered tksheet view for sheet '{self.sheet_data.sheet_name}' with {len(self.sheet_data.questions)} questions")
        
        return self.sheet
    
    def _populate_data(self) -> None:
        """Populate sheet with questions and responses."""
        data = []
        
        for row_idx, question in enumerate(self.sheet_data.questions):
            state = self.sheet_data.cell_states[row_idx]
            answer = self.sheet_data.answers[row_idx]
            
            response_text = self._get_response_text(state, answer, agent_name=None)
            data.append([question, response_text])
        
        # Set the data
        self.sheet.set_sheet_data(data)
        
        # Apply cell colors based on state
        for row_idx in range(len(self.sheet_data.questions)):
            self._update_row_color(row_idx)
        
        logger.debug(f"Populated tksheet with {len(data)} rows")
    
    def _update_row_color(self, row_index: int) -> None:
        """Update the background color of a row based on its state.
        
        Args:
            row_index: Zero-based row index
        """
        if row_index < 0 or row_index >= len(self.sheet_data.cell_states):
            return
        
        state = self.sheet_data.cell_states[row_index]
        
        # Determine color based on state
        if state == CellState.WORKING:
            color = self.COLOR_WORKING
        elif state == CellState.COMPLETED:
            color = self.COLOR_COMPLETED
        else:  # PENDING
            color = self.COLOR_PENDING
        
        # Apply color to both cells in the row
        self.sheet.highlight_rows(
            rows=[row_index],
            bg=color,
            fg="black",
            redraw=True
        )
    
    def update_cell(
        self, 
        row_index: int, 
        state: CellState, 
        answer: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> None:
        """Update visual state of a single cell.
        
        Args:
            row_index: Zero-based row index
            state: New cell state
            answer: Answer text (required for COMPLETED state)
            agent_name: Name of the currently active agent (for WORKING state)
        """
        if row_index < 0 or row_index >= len(self.sheet_data.questions):
            logger.warning(f"Invalid row_index: {row_index} (valid range: 0-{len(self.sheet_data.questions)-1})")
            return
        
        if not self.sheet:
            logger.error("Cannot update cell: sheet not initialized")
            return
        
        # Update sheet data to stay in sync
        self.sheet_data.cell_states[row_index] = state
        if answer and state == CellState.COMPLETED:
            self.sheet_data.answers[row_index] = answer
        
        # Get response text
        response_text = self._get_response_text(state, answer or "", agent_name)
        
        # Update the response cell (column 1)
        self.sheet.set_cell_data(row_index, 1, value=response_text, redraw=True)
        
        # Update row color
        self._update_row_color(row_index)
        
        # Auto-scroll to keep active cell visible
        if state == CellState.WORKING:
            self._auto_scroll_to_row(row_index)
        
        logger.debug(f"Updated cell [{row_index}] to {state.value}")
    
    def _get_response_text(self, state: CellState, answer: str, agent_name: Optional[str] = None) -> str:
        """Get display text for response cell based on state.
        
        Args:
            state: Current cell state
            answer: Answer text
            agent_name: Name of the currently active agent (for WORKING state)
            
        Returns:
            Text to display in response column
        """
        if state == CellState.WORKING:
            # Map agent names to user-friendly messages with fallback
            message = self.AGENT_MESSAGES.get(agent_name, self.AGENT_MESSAGES[None])
            logger.debug(f"Getting response text for agent_name='{agent_name}' -> message='{message}'")
            return message
        elif state == CellState.COMPLETED:
            return answer or ""
        else:  # PENDING
            return ""
    
    def _auto_scroll_to_row(self, row_index: int) -> None:
        """Auto-scroll to keep specified row visible.
        
        Args:
            row_index: Row to scroll to
        """
        if not self.sheet or row_index >= len(self.sheet_data.questions):
            return
        
        try:
            # Use tksheet's see method to make the row visible
            self.sheet.see(row=row_index, column=0, keep_yscroll=False, keep_xscroll=True)
            logger.debug(f"Auto-scrolled to row {row_index}")
        except Exception as e:
            logger.warning(f"Failed to auto-scroll to row {row_index}: {e}")
    
    def refresh(self) -> None:
        """Redraw entire view from current sheet_data."""
        if not self.sheet:
            logger.warning("Cannot refresh: sheet not initialized")
            return
        
        # Repopulate with current data
        self._populate_data()
        
        logger.debug(f"Refreshed spreadsheet view for sheet '{self.sheet_data.sheet_name}'")
    
    def get_visible_row_range(self) -> tuple[int, int]:
        """Get the range of currently visible rows.
        
        Returns:
            Tuple of (first_visible_row, last_visible_row) indices
        """
        if not self.sheet:
            return (0, 0)
        
        try:
            # Get visible rows from tksheet
            visible = self.sheet.get_currently_visible()
            if visible:
                first_row = visible[0]
                last_row = visible[1]
                return (first_row, last_row)
            return (0, len(self.sheet_data.questions) - 1)
        except Exception as e:
            logger.warning(f"Failed to get visible row range: {e}")
            return (0, len(self.sheet_data.questions) - 1)
    
    def select_row(self, row_index: int) -> None:
        """Select and highlight a specific row.
        
        Args:
            row_index: Zero-based row index to select
        """
        if not self.sheet or row_index < 0 or row_index >= len(self.sheet_data.questions):
            return
        
        try:
            # Select the row
            self.sheet.select_row(row_index, redraw=True)
            
            # Ensure it's visible
            self._auto_scroll_to_row(row_index)
        except Exception as e:
            logger.warning(f"Failed to select row {row_index}: {e}")
    
    def get_row_count(self) -> int:
        """Get the total number of rows in the view.
        
        Returns:
            Number of question rows
        """
        return len(self.sheet_data.questions)
    
    def destroy(self) -> None:
        """Clean up the view and its resources."""
        if self.sheet:
            self.sheet.destroy()
            self.sheet = None
        
        if self.frame:
            self.frame.destroy()
            self.frame = None
        
        logger.debug(f"Destroyed spreadsheet view for sheet '{self.sheet_data.sheet_name}'")
