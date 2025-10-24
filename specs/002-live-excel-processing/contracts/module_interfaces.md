# Module Interfaces: Live Excel Processing Visualization

**Feature**: 002-live-excel-processing  
**Date**: October 23, 2025  
**Phase**: 1 - Design

## Overview

This document defines the interfaces between modules for the live Excel processing visualization feature. All interfaces follow the existing project patterns and integrate with the established multi-agent architecture.

---

## Module: `src/excel/loader.py`

### Purpose

Load and parse Excel files into internal data structures for processing.

### Public Interface

```python
class ExcelLoader:
    """Loads Excel workbooks and extracts questions from multiple sheets."""
    
    def load_workbook(self, file_path: str) -> WorkbookData:
        """Load Excel file and create WorkbookData structure.
        
        Args:
            file_path: Absolute path to Excel file (.xlsx or .xls)
            
        Returns:
            WorkbookData with all visible sheets and questions
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ExcelFormatError: If file format is invalid
            ExcelFormatError: If no visible sheets found
        """
        pass
    
    def save_workbook(self, workbook_data: WorkbookData) -> None:
        """Save all answers back to the Excel file.
        
        Args:
            workbook_data: WorkbookData with completed answers
            
        Raises:
            ExcelFormatError: If workbook structure changed
            IOError: If file cannot be written
        """
        pass
```

### Dependencies

- `openpyxl`: Excel file reading/writing
- `utils.data_types`: WorkbookData, SheetData
- `utils.exceptions`: ExcelFormatError

### Notes

- Skips hidden sheets (`worksheet.sheet_state != 'visible'`)
- Reads questions from column A, will write answers to column B
- Preserves Excel formatting and formulas

---

## Module: `src/excel/processor.py`

### Purpose

Orchestrate multi-sheet Excel processing with agent workflow integration.

### Public Interface

```python
class ExcelProcessor:
    """Processes Excel workbooks through multi-agent workflow."""
    
    def __init__(
        self, 
        agent_coordinator: AgentCoordinator,
        ui_update_queue: queue.Queue
    ):
        """Initialize processor with agent coordinator and UI queue.
        
        Args:
            agent_coordinator: Initialized AgentCoordinator instance
            ui_update_queue: Thread-safe queue for UI update events
        """
        pass
    
    async def process_workbook(
        self, 
        workbook_data: WorkbookData,
        context: str,
        char_limit: int,
        max_retries: int
    ) -> ExcelProcessingResult:
        """Process all sheets in workbook sequentially.
        
        Args:
            workbook_data: Loaded workbook with questions
            context: Domain context for questions
            char_limit: Maximum answer length
            max_retries: Maximum retry attempts per question
            
        Returns:
            ExcelProcessingResult with completion statistics
            
        Raises:
            AzureServiceError: If agent services fail
        """
        pass
```

### Event Emission

Emits UIUpdateEvents to ui_update_queue:

- `SHEET_START`: When starting new sheet
- `CELL_WORKING`: Before processing each question
- `CELL_COMPLETED`: After each question completes
- `SHEET_COMPLETE`: After sheet finishes
- `WORKBOOK_COMPLETE`: After all sheets done
- `ERROR`: On any processing error

### Dependencies

- `agents.workflow_manager`: AgentCoordinator
- `utils.data_types`: WorkbookData, UIUpdateEvent
- `queue`: Standard library Queue

---

## Module: `src/ui/spreadsheet_view.py`

### Purpose

Render a single Excel sheet as a tkinter Treeview with live cell updates.

### Public Interface

```python
class SpreadsheetView:
    """Visual representation of a single Excel sheet."""
    
    def __init__(
        self, 
        parent: tk.Widget,
        sheet_data: SheetData
    ):
        """Initialize spreadsheet view.
        
        Args:
            parent: Parent tkinter widget
            sheet_data: Sheet data to render
        """
        pass
    
    def render(self) -> ttk.Treeview:
        """Create and return the Treeview widget.
        
        Returns:
            Configured Treeview widget
        """
        pass
    
    def update_cell(
        self, 
        row_index: int, 
        state: CellState, 
        answer: Optional[str] = None
    ) -> None:
        """Update visual state of a single cell.
        
        Args:
            row_index: Zero-based row index
            state: New cell state (PENDING, WORKING, COMPLETED)
            answer: Answer text (required for COMPLETED state)
        """
        pass
    
    def refresh(self) -> None:
        """Redraw entire view from sheet_data."""
        pass
```

### Cell Styling

- **PENDING**: White background, empty response
- **WORKING**: Pink background (#FFB6C1), "Working..." text
- **COMPLETED**: Light green background (#90EE90), answer text

### Dependencies

- `tkinter.ttk`: Treeview widget
- `utils.data_types`: SheetData, CellState

---

## Module: `src/ui/workbook_view.py`

### Purpose

Manage multi-sheet notebook with tabs and navigation control.

### Public Interface

```python
class WorkbookView:
    """Multi-sheet workbook view with tab navigation."""
    
    def __init__(
        self, 
        parent: tk.Widget,
        workbook_data: WorkbookData,
        ui_update_queue: queue.Queue
    ):
        """Initialize workbook view.
        
        Args:
            parent: Parent tkinter widget
            workbook_data: Complete workbook data
            ui_update_queue: Queue for receiving UI updates
        """
        pass
    
    def render(self) -> ttk.Notebook:
        """Create notebook with all sheet tabs.
        
        Returns:
            Configured Notebook widget
        """
        pass
    
    def navigate_to_sheet(self, sheet_index: int) -> None:
        """Switch visible tab to specified sheet.
        
        Args:
            sheet_index: Zero-based sheet index
        """
        pass
    
    def update_tab_indicator(
        self, 
        sheet_index: int, 
        is_processing: bool
    ) -> None:
        """Add or remove spinner indicator on tab.
        
        Args:
            sheet_index: Zero-based sheet index
            is_processing: True to show spinner, False to hide
        """
        pass
    
    def start_update_polling(self) -> None:
        """Begin polling ui_update_queue for events.
        
        Polls queue every 50ms and processes UIUpdateEvents.
        """
        pass
    
    def handle_user_tab_click(self, event: tk.Event) -> None:
        """Handle user clicking a sheet tab.
        
        Args:
            event: Notebook tab change event
        """
        pass
```

### Navigation Rules

- Auto-navigation enabled initially
- User clicking tab disables auto-navigation
- View remains locked to user selection
- Background processing continues on all sheets

### Dependencies

- `tkinter.ttk`: Notebook widget
- `ui.spreadsheet_view`: SpreadsheetView
- `utils.data_types`: WorkbookData, NavigationState, UIUpdateEvent
- `queue`: Standard library Queue

---

## Module: `src/ui/main_window.py` (Modified)

### Purpose

Integrate WorkbookView into existing UIManager.

### Modified Interface

```python
class UIManager:
    """Main GUI interface for the questionnaire application."""
    
    # ... existing methods ...
    
    def _on_import_excel_clicked(self) -> None:
        """Handle Import Excel button click.
        
        Modified to:
        1. Load Excel file
        2. Replace answer_display with WorkbookView
        3. Start background processing
        """
        pass
    
    async def _process_excel_internal(self, file_path: str) -> ExcelProcessingResult:
        """Internal async Excel processing.
        
        Modified to:
        1. Load workbook via ExcelLoader
        2. Create WorkbookView in answer area
        3. Start ExcelProcessor with UI queue
        4. Wait for completion
        5. Save workbook
        """
        pass
```

### Integration Points

- Replace `answer_display` (ScrolledText) with `workbook_view` (Notebook) dynamically
- Create `ui_update_queue` for WorkbookView polling
- Pass queue to ExcelProcessor for event emission
- Restore answer_display when processing completes

---

## Data Flow Contracts

### Excel Loading Flow

```
User clicks "Import From Excel"
  ↓
UIManager._on_import_excel_clicked()
  ↓
ExcelLoader.load_workbook(file_path)
  ↓
Returns WorkbookData
  ↓
UIManager creates WorkbookView(workbook_data, ui_queue)
  ↓
WorkbookView.render() → displays in answer area
```

### Processing Flow

```
UIManager._process_excel_internal()
  ↓
ExcelProcessor.process_workbook(workbook_data, ...)
  ↓
For each sheet:
  For each question:
    Emit CELL_WORKING → ui_update_queue
    ↓
    AgentCoordinator.process_question()
    ↓
    Emit CELL_COMPLETED → ui_update_queue
  ↓
  Emit SHEET_COMPLETE → ui_update_queue
↓
Emit WORKBOOK_COMPLETE → ui_update_queue
  ↓
ExcelLoader.save_workbook(workbook_data)
```

### UI Update Flow

```
WorkbookView.start_update_polling() (main thread)
  ↓
root.after(50ms, poll_queue)
  ↓
ui_update_queue.get_nowait()
  ↓
Process UIUpdateEvent:
  - CELL_WORKING → SpreadsheetView.update_cell(row, WORKING)
  - CELL_COMPLETED → SpreadsheetView.update_cell(row, COMPLETED, answer)
  - SHEET_START → WorkbookView.navigate_to_sheet()
  - SHEET_COMPLETE → WorkbookView.update_tab_indicator(False)
  ↓
Schedule next poll via root.after(50ms, poll_queue)
```

---

## Error Handling Contracts

### Excel Loading Errors

```python
try:
    workbook_data = loader.load_workbook(file_path)
except FileNotFoundError:
    # Show error dialog: "File not found"
    # Return to initial state
except ExcelFormatError as e:
    # Show error dialog: str(e)
    # Return to initial state
```

### Processing Errors

```python
# ExcelProcessor emits ERROR event
event = UIUpdateEvent(
    event_type='ERROR',
    payload={'error_type': 'agent_failure', 'message': str(error)}
)
ui_update_queue.put(event)

# WorkbookView handles ERROR event
def handle_error_event(event):
    error_type = event.payload['error_type']
    message = event.payload['message']
    # Show error dialog via UIManager.display_error()
```

### Resource Cleanup

```python
# UIManager ensures cleanup on window close
def _on_window_close(self):
    if self.processing_active:
        # Prompt user to cancel
        if not confirm_cancel():
            return
    
    # Cleanup agents (existing pattern)
    await self.agent_coordinator.cleanup_agents()
    
    # No special cleanup needed for WorkbookView
    self.root.destroy()
```

---

## Testing Interfaces

### Mock Excel Files

Create test fixtures:

```python
# tests/fixtures/excel/
# - single_sheet_5_questions.xlsx
# - multi_sheet_3x10_questions.xlsx
# - hidden_sheets.xlsx
# - invalid_format.xlsx
```

### Mock Agent Responses

```python
class MockAgentCoordinator:
    """Mock for testing without Azure."""
    
    async def process_question(self, question, callback):
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        # Return mock answer
        return ProcessingResult(
            success=True,
            answer=Answer(content=f"Mock answer for: {question.text}", sources=[])
        )
```

### UI Component Tests

```python
def test_spreadsheet_view_cell_update():
    """Test cell state transitions."""
    sheet_data = create_test_sheet_data(5)
    view = SpreadsheetView(parent, sheet_data)
    view.render()
    
    # Test PENDING → WORKING
    view.update_cell(0, CellState.WORKING)
    assert_cell_background(view, 0, '#FFB6C1')
    
    # Test WORKING → COMPLETED
    view.update_cell(0, CellState.COMPLETED, "Test answer")
    assert_cell_background(view, 0, '#90EE90')
    assert_cell_text(view, 0, "Test answer")
```

---

## Performance Contracts

### Response Time Targets

- **Spreadsheet render**: < 2s for 100 rows
- **Cell update**: < 500ms from event to visual change
- **Tab navigation**: < 200ms from click to view switch
- **Queue polling**: 50ms intervals (20 updates/second max)

### Memory Limits

- **WorkbookData**: ~1MB for 1000 questions
- **Treeview widgets**: ~5MB for 10 sheets × 100 rows
- **Total overhead**: < 10MB above baseline

### Scalability

- **Supported**: 10 sheets × 100 questions = 1000 total
- **Degradation**: Performance may degrade beyond these limits
- **Hard limit**: Reject files with >1000 questions

---

## Version Compatibility

### Python Version

- Minimum: Python 3.11
- Tested: Python 3.11, 3.12

### Dependencies

- `tkinter`: Standard library (included with Python)
- `openpyxl`: Version 3.0+ (current: latest)
- `agent-framework-azure-ai`: Version as specified in requirements.txt

### Platform Support

- **Windows**: Primary platform, fully tested
- **Linux**: Compatible, may need tkinter package install
- **macOS**: Compatible, uses native widgets

---

## Future Interface Extensions

### Planned Enhancements (Post-MVP)

```python
class SpreadsheetView:
    def add_tooltip(self, row_index: int, text: str) -> None:
        """Add hover tooltip to cell (for long answers)."""
        pass
    
    def highlight_error(self, row_index: int, error: str) -> None:
        """Mark cell as error state with red background."""
        pass

class WorkbookView:
    def enable_auto_navigation(self) -> None:
        """Re-enable auto-navigation after user lock."""
        pass
    
    def show_progress_overlay(self) -> None:
        """Display global progress bar across all sheets."""
        pass
```

These extensions maintain interface compatibility while adding optional features.
