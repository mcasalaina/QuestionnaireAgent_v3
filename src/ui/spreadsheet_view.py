"""Spreadsheet view using tkinter Treeview for single Excel sheet rendering."""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from utils.data_types import SheetData, CellState
import logging

logger = logging.getLogger(__name__)


class SpreadsheetView:
    """Visual representation of a single Excel sheet using tkinter Treeview."""
    
    # Cell background colors for different states
    COLOR_PENDING = "#FFFFFF"      # White
    COLOR_WORKING = "#FFB6C1"      # Pink
    COLOR_COMPLETED = "#90EE90"    # Light green
    
    # Agent name to user-friendly message mapping
    AGENT_MESSAGES = {
        "question_answerer": "Composing Answer...",
        "answer_checker": "Checking Answer...",
        "link_checker": "Checking Links..."
    }
    
    def __init__(self, parent: tk.Widget, sheet_data: SheetData):
        """Initialize spreadsheet view.
        
        Args:
            parent: Parent tkinter widget
            sheet_data: Sheet data to render
        """
        self.parent = parent
        self.sheet_data = sheet_data
        self.treeview: Optional[ttk.Treeview] = None
        self.row_ids: list[str] = []
        self.scrollbar_v: Optional[ttk.Scrollbar] = None
        self.scrollbar_h: Optional[ttk.Scrollbar] = None
    
    def render(self) -> ttk.Treeview:
        """Create and return configured Treeview widget.
        
        Returns:
            Configured Treeview widget ready for display
        """
        # Create frame to hold treeview and scrollbars
        frame = ttk.Frame(self.parent)
        
        # Create Treeview with columns
        self.treeview = ttk.Treeview(
            frame,
            columns=('question', 'response'),
            show='headings',
            selectmode='none'
        )
        
        # Configure column headings
        self.treeview.heading('question', text='Question')
        self.treeview.heading('response', text='Response')
        
        # Configure column widths and properties
        self.treeview.column('question', width=400, minwidth=200, anchor='w')
        self.treeview.column('response', width=600, minwidth=300, anchor='w')
        
        # Configure row height to accommodate multi-line text better
        style = ttk.Style()
        style.configure("Treeview", rowheight=60)  # Increase row height from default ~20 to 60
        
        # Configure borders and styling - use a combination of approaches
        style.configure("Treeview", 
                       background="white",
                       fieldbackground="white",
                       selectbackground="#e6f3ff",
                       selectforeground="black")
        
        # Configure header styling with visible borders
        style.configure("Treeview.Heading",
                       background="#f0f0f0",
                       foreground="black",
                       relief="solid",
                       borderwidth=1)
        
        # Map different states for better visual separation
        style.map("Treeview",
                 background=[('selected', '#e6f3ff')],
                 foreground=[('selected', 'black')])
        
        # Configure Treeview to show lines between items
        self.treeview.configure(show='tree headings')  # Show both tree lines and headings
        
        # Re-configure to show headings only but with better styling
        self.treeview.configure(show='headings')
        
        # Configure cell state tags for styling
        self._configure_cell_tags()
        
        # Add scrollbars
        self._add_scrollbars(frame)
        
        # Insert all rows from sheet data
        self._populate_rows()
        
        # Pack components
        self.treeview.grid(row=0, column=0, sticky='nsew')
        self.scrollbar_v.grid(row=0, column=1, sticky='ns')
        self.scrollbar_h.grid(row=1, column=0, sticky='ew')
        
        # Configure grid weights for resizing
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Pack frame in parent
        frame.pack(fill=tk.BOTH, expand=True)
        
        logger.debug(f"Rendered spreadsheet view for sheet '{self.sheet_data.sheet_name}' with {len(self.sheet_data.questions)} questions")
        
        return self.treeview
    
    def _configure_cell_tags(self) -> None:
        """Configure Treeview tags for different cell states."""
        # Configure cell state colors with alternating backgrounds for better separation
        self.treeview.tag_configure('pending', background=self.COLOR_PENDING)
        self.treeview.tag_configure('working', background=self.COLOR_WORKING)
        self.treeview.tag_configure('completed', background=self.COLOR_COMPLETED)
        
        # Add alternating row colors for better visual separation
        self.treeview.tag_configure('odd_row', background='#f9f9f9')
        self.treeview.tag_configure('even_row', background='#ffffff')
        
        # Working state variants with alternating backgrounds
        self.treeview.tag_configure('working_odd', background='#FFB6C1')  # Pink
        self.treeview.tag_configure('working_even', background='#FFC0CB')  # Light pink
        
        # Completed state variants with alternating backgrounds  
        self.treeview.tag_configure('completed_odd', background='#90EE90')  # Light green
        self.treeview.tag_configure('completed_even', background='#98FB98')  # Pale green
        
        # Text color for all states
        for tag in ['pending', 'working', 'completed', 'odd_row', 'even_row', 
                   'working_odd', 'working_even', 'completed_odd', 'completed_even']:
            self.treeview.tag_configure(tag, foreground='#000000')
    
    def _add_scrollbars(self, frame: ttk.Frame) -> None:
        """Add vertical and horizontal scrollbars to the treeview."""
        # Vertical scrollbar
        self.scrollbar_v = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.scrollbar_v.set)
        
        # Horizontal scrollbar
        self.scrollbar_h = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.treeview.xview)
        self.treeview.configure(xscrollcommand=self.scrollbar_h.set)
    
    def _populate_rows(self) -> None:
        """Populate treeview with all questions from sheet data."""
        self.row_ids.clear()
        
        for row_idx, question in enumerate(self.sheet_data.questions):
            state = self.sheet_data.cell_states[row_idx]
            answer = self.sheet_data.answers[row_idx]
            
            response_text = self._get_response_text(state, answer or "", agent_name=None)
            
            # Use alternating row colors with state-specific variants
            is_odd = (row_idx % 2) == 1
            
            if state == CellState.WORKING:
                tag = 'working_odd' if is_odd else 'working_even'
            elif state == CellState.COMPLETED:
                tag = 'completed_odd' if is_odd else 'completed_even'
            else:  # PENDING
                tag = 'odd_row' if is_odd else 'even_row'
            
            row_id = self.treeview.insert(
                '',
                'end',
                values=(question, response_text),
                tags=(tag,)
            )
            self.row_ids.append(row_id)
        
        logger.debug(f"Populated {len(self.row_ids)} rows in treeview with alternating colors")
    
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
        if row_index < 0 or row_index >= len(self.row_ids):
            logger.warning(f"Invalid row_index: {row_index} (valid range: 0-{len(self.row_ids)-1})")
            return
        
        if not self.treeview:
            logger.error("Cannot update cell: treeview not initialized")
            return
        
        row_id = self.row_ids[row_index]
        question = self.sheet_data.questions[row_index]
        response_text = self._get_response_text(state, answer or "", agent_name)
        
        # Use alternating row colors with state-specific variants
        is_odd = (row_index % 2) == 1
        
        if state == CellState.WORKING:
            tag = 'working_odd' if is_odd else 'working_even'
        elif state == CellState.COMPLETED:
            tag = 'completed_odd' if is_odd else 'completed_even'
        else:  # PENDING
            tag = 'odd_row' if is_odd else 'even_row'
        
        # Update the treeview item
        self.treeview.item(
            row_id,
            values=(question, response_text),
            tags=(tag,)
        )
        
        # Update sheet data to stay in sync
        self.sheet_data.cell_states[row_index] = state
        if answer and state == CellState.COMPLETED:
            self.sheet_data.answers[row_index] = answer
        
        # Auto-scroll to keep active cell visible
        if state == CellState.WORKING:
            self._auto_scroll_to_row(row_index)
        
        logger.debug(f"Updated cell [{row_index}] to {state.value} with alternating color")
    
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
            # Map agent names to user-friendly messages
            return self.AGENT_MESSAGES.get(agent_name, "Working...")
        elif state == CellState.COMPLETED:
            return answer or ""
        else:  # PENDING
            return ""
    
    def _auto_scroll_to_row(self, row_index: int) -> None:
        """Auto-scroll to keep specified row visible.
        
        Args:
            row_index: Row to scroll to
        """
        if not self.treeview or row_index >= len(self.row_ids):
            return
        
        try:
            # Get the item ID for the row
            item_id = self.row_ids[row_index]
            
            # Calculate scroll position to center the row
            total_rows = len(self.row_ids)
            if total_rows > 0:
                # Scroll to position that shows the row with some context
                target_position = max(0, (row_index - 3) / total_rows)
                self.treeview.yview_moveto(target_position)
                
                # Ensure the specific item is visible
                self.treeview.see(item_id)
            
            logger.debug(f"Auto-scrolled to row {row_index}")
        
        except Exception as e:
            logger.warning(f"Failed to auto-scroll to row {row_index}: {e}")
    
    def refresh(self) -> None:
        """Redraw entire view from current sheet_data."""
        if not self.treeview:
            logger.warning("Cannot refresh: treeview not initialized")
            return
        
        # Clear existing items
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        
        # Repopulate with current data
        self._populate_rows()
        
        logger.debug(f"Refreshed spreadsheet view for sheet '{self.sheet_data.sheet_name}'")
    
    def get_visible_row_range(self) -> tuple[int, int]:
        """Get the range of currently visible rows.
        
        Returns:
            Tuple of (first_visible_row, last_visible_row) indices
        """
        if not self.treeview or not self.row_ids:
            return (0, 0)
        
        try:
            # Get first and last visible items
            visible_items = []
            for item_id in self.row_ids:
                bbox = self.treeview.bbox(item_id)
                if bbox:  # Item is visible
                    visible_items.append(item_id)
            
            if not visible_items:
                return (0, 0)
            
            # Find indices of first and last visible items
            first_visible = self.row_ids.index(visible_items[0])
            last_visible = self.row_ids.index(visible_items[-1])
            
            return (first_visible, last_visible)
        
        except Exception as e:
            logger.warning(f"Failed to get visible row range: {e}")
            return (0, len(self.row_ids) - 1)
    
    def select_row(self, row_index: int) -> None:
        """Select and highlight a specific row.
        
        Args:
            row_index: Zero-based row index to select
        """
        if not self.treeview or row_index < 0 or row_index >= len(self.row_ids):
            return
        
        # Clear existing selection
        self.treeview.selection_remove(self.treeview.selection())
        
        # Select the specified row
        item_id = self.row_ids[row_index]
        self.treeview.selection_add(item_id)
        self.treeview.focus(item_id)
        
        # Ensure it's visible
        self._auto_scroll_to_row(row_index)
    
    def get_row_count(self) -> int:
        """Get the total number of rows in the view.
        
        Returns:
            Number of question rows
        """
        return len(self.sheet_data.questions)
    
    def destroy(self) -> None:
        """Clean up the view and its resources."""
        if self.treeview:
            self.treeview.destroy()
            self.treeview = None
        
        if self.scrollbar_v:
            self.scrollbar_v.destroy()
            self.scrollbar_v = None
        
        if self.scrollbar_h:
            self.scrollbar_h.destroy()
            self.scrollbar_h = None
        
        self.row_ids.clear()
        logger.debug(f"Destroyed spreadsheet view for sheet '{self.sheet_data.sheet_name}'")