# Quickstart: Live Excel Processing Visualization

**Feature**: 002-live-excel-processing  
**Date**: October 23, 2025  
**Audience**: Developers implementing this feature

## Overview

This guide provides step-by-step instructions for implementing the live Excel processing visualization feature. Follow the phases in order to build incrementally testable functionality.

## Prerequisites

### Environment Setup

1. **Activate virtual environment**:

   ```powershell
   cd C:\src\QuestionnaireAgent_v3
   .\.venv\Scripts\Activate.ps1
   ```

2. **Verify dependencies** (already in requirements.txt):

   ```powershell
   pip list | findstr "openpyxl tkinter"
   ```

3. **Run existing tests** to ensure baseline:

   ```powershell
   cd src
   pytest ../tests/ -v
   ```

### Knowledge Requirements

- Familiarity with tkinter GUI programming
- Understanding of Python asyncio and threading
- Knowledge of the existing AgentCoordinator workflow
- Basic openpyxl Excel manipulation

---

## Phase 1: Core Data Structures (1-2 hours)

### Step 1.1: Create Data Types

**File**: `src/utils/data_types.py`

Add new data classes:

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

class CellState(Enum):
    """Processing state of a response cell."""
    PENDING = "pending"
    WORKING = "working"
    COMPLETED = "completed"

@dataclass
class SheetData:
    """Data for a single Excel sheet."""
    sheet_name: str
    sheet_index: int
    questions: List[str]
    answers: List[Optional[str]]
    cell_states: List[CellState]
    is_processing: bool = False
    is_complete: bool = False
    
    def __post_init__(self):
        """Validate invariants."""
        assert len(self.questions) == len(self.answers) == len(self.cell_states)
    
    def get_progress(self) -> float:
        """Return completion percentage (0.0 to 1.0)."""
        completed = sum(1 for s in self.cell_states if s == CellState.COMPLETED)
        return completed / len(self.questions) if self.questions else 0.0

@dataclass
class WorkbookData:
    """Data for entire Excel workbook."""
    file_path: str
    sheets: List[SheetData]
    current_sheet_index: int = 0
    
    @property
    def total_questions(self) -> int:
        return sum(len(sheet.questions) for sheet in self.sheets)
    
    @property
    def completed_questions(self) -> int:
        return sum(
            sum(1 for s in sheet.cell_states if s == CellState.COMPLETED)
            for sheet in self.sheets
        )
    
    def get_active_sheet(self) -> Optional[SheetData]:
        """Return currently processing sheet."""
        for sheet in self.sheets:
            if sheet.is_processing:
                return sheet
        return None

@dataclass
class NavigationState:
    """Tracks user sheet navigation."""
    user_selected_sheet: Optional[int] = None
    
    @property
    def auto_navigation_enabled(self) -> bool:
        return self.user_selected_sheet is None
    
    def lock_to_sheet(self, sheet_index: int):
        self.user_selected_sheet = sheet_index
    
    def enable_auto_navigation(self):
        self.user_selected_sheet = None

@dataclass
class UIUpdateEvent:
    """Event from background thread to UI."""
    event_type: str  # SHEET_START, CELL_WORKING, CELL_COMPLETED, etc.
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
```

**Test**: Create `tests/unit/test_data_types.py`:

```python
def test_cell_state_enum():
    assert CellState.PENDING.value == "pending"
    assert CellState.WORKING.value == "working"
    assert CellState.COMPLETED.value == "completed"

def test_sheet_data_progress():
    sheet = SheetData(
        sheet_name="Test",
        sheet_index=0,
        questions=["Q1", "Q2", "Q3"],
        answers=[None, "A2", None],
        cell_states=[CellState.PENDING, CellState.COMPLETED, CellState.PENDING]
    )
    assert sheet.get_progress() == 1/3

def test_navigation_state():
    nav = NavigationState()
    assert nav.auto_navigation_enabled
    
    nav.lock_to_sheet(2)
    assert not nav.auto_navigation_enabled
    assert nav.user_selected_sheet == 2
```

---

## Phase 2: Excel Loading (2-3 hours)

### Step 2.1: Create Excel Loader

**File**: `src/excel/loader.py`

```python
"""Excel file loading and saving."""

import openpyxl
from typing import List
from utils.data_types import WorkbookData, SheetData, CellState
from utils.exceptions import ExcelFormatError
import logging

logger = logging.getLogger(__name__)

class ExcelLoader:
    """Loads and saves Excel workbooks."""
    
    def load_workbook(self, file_path: str) -> WorkbookData:
        """Load Excel file into WorkbookData.
        
        Args:
            file_path: Path to .xlsx file
            
        Returns:
            WorkbookData with all visible sheets
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ExcelFormatError: If file format invalid
        """
        try:
            wb = openpyxl.load_workbook(file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        except Exception as e:
            raise ExcelFormatError(f"Invalid Excel file: {e}")
        
        sheets = []
        for sheet_index, sheet_name in enumerate(wb.sheetnames):
            ws = wb[sheet_name]
            
            # Skip hidden sheets
            if ws.sheet_state != 'visible':
                logger.info(f"Skipping hidden sheet: {sheet_name}")
                continue
            
            # Extract questions from column A
            questions = []
            for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):  # Skip header
                cell = row[0]
                if cell.value and str(cell.value).strip():
                    questions.append(str(cell.value).strip())
                else:
                    break  # Stop at first empty cell
            
            if not questions:
                logger.warning(f"Sheet {sheet_name} has no questions, skipping")
                continue
            
            # Create SheetData
            sheet_data = SheetData(
                sheet_name=sheet_name,
                sheet_index=len(sheets),  # Reindex after filtering
                questions=questions,
                answers=[None] * len(questions),
                cell_states=[CellState.PENDING] * len(questions)
            )
            sheets.append(sheet_data)
        
        if not sheets:
            raise ExcelFormatError("No visible sheets with questions found")
        
        logger.info(f"Loaded {len(sheets)} sheets with {sum(len(s.questions) for s in sheets)} total questions")
        
        return WorkbookData(file_path=file_path, sheets=sheets)
    
    def save_workbook(self, workbook_data: WorkbookData) -> None:
        """Save answers back to Excel file.
        
        Args:
            workbook_data: WorkbookData with completed answers
            
        Raises:
            ExcelFormatError: If file structure changed
            IOError: If file cannot be written
        """
        try:
            wb = openpyxl.load_workbook(workbook_data.file_path)
        except Exception as e:
            raise ExcelFormatError(f"Cannot reopen Excel file: {e}")
        
        for sheet_data in workbook_data.sheets:
            ws = wb[sheet_data.sheet_name]
            
            # Write answers to column B
            for row_idx, answer in enumerate(sheet_data.answers, start=2):  # Start at row 2
                if answer:
                    ws.cell(row=row_idx, column=2, value=answer)
        
        try:
            wb.save(workbook_data.file_path)
            logger.info(f"Saved workbook to {workbook_data.file_path}")
        except Exception as e:
            raise IOError(f"Cannot save Excel file: {e}")
```

**Test**: Create `tests/unit/test_excel_loader.py`:

```python
import pytest
from excel.loader import ExcelLoader
from utils.exceptions import ExcelFormatError

def test_load_valid_workbook(tmp_path):
    # Create test Excel file
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws['A1'] = "Question"
    ws['A2'] = "What is AI?"
    ws['A3'] = "What is ML?"
    
    file_path = tmp_path / "test.xlsx"
    wb.save(file_path)
    
    # Load with ExcelLoader
    loader = ExcelLoader()
    workbook_data = loader.load_workbook(str(file_path))
    
    assert len(workbook_data.sheets) == 1
    assert workbook_data.sheets[0].sheet_name == "Sheet1"
    assert len(workbook_data.sheets[0].questions) == 2
    assert workbook_data.sheets[0].questions[0] == "What is AI?"
```

---

## Phase 3: UI Components (3-4 hours)

### Step 3.1: Create SpreadsheetView

**File**: `src/ui/spreadsheet_view.py`

```python
"""Spreadsheet view using tkinter Treeview."""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from utils.data_types import SheetData, CellState
import logging

logger = logging.getLogger(__name__)

class SpreadsheetView:
    """Visual representation of a single Excel sheet."""
    
    # Cell background colors
    COLOR_PENDING = "#FFFFFF"      # White
    COLOR_WORKING = "#FFB6C1"      # Pink
    COLOR_COMPLETED = "#90EE90"    # Light green
    
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
    
    def render(self) -> ttk.Treeview:
        """Create and return configured Treeview."""
        # Create Treeview with columns
        self.treeview = ttk.Treeview(
            self.parent,
            columns=('question', 'response'),
            show='headings',
            selectmode='none'
        )
        
        # Configure columns
        self.treeview.heading('question', text='Question')
        self.treeview.heading('response', text='Response')
        self.treeview.column('question', width=400)
        self.treeview.column('response', width=600)
        
        # Configure cell state tags
        self.treeview.tag_configure('pending', background=self.COLOR_PENDING)
        self.treeview.tag_configure('working', background=self.COLOR_WORKING)
        self.treeview.tag_configure('completed', background=self.COLOR_COMPLETED)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.parent, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=scrollbar.set)
        
        # Insert all rows
        for row_idx, question in enumerate(self.sheet_data.questions):
            state = self.sheet_data.cell_states[row_idx]
            answer = self.sheet_data.answers[row_idx] or ""
            
            response_text = self._get_response_text(state, answer)
            tag = state.value
            
            row_id = self.treeview.insert(
                '',
                'end',
                values=(question, response_text),
                tags=(tag,)
            )
            self.row_ids.append(row_id)
        
        return self.treeview
    
    def update_cell(
        self, 
        row_index: int, 
        state: CellState, 
        answer: Optional[str] = None
    ) -> None:
        """Update visual state of a cell.
        
        Args:
            row_index: Zero-based row index
            state: New cell state
            answer: Answer text (required for COMPLETED)
        """
        if row_index >= len(self.row_ids):
            logger.warning(f"Invalid row_index: {row_index}")
            return
        
        row_id = self.row_ids[row_index]
        question = self.sheet_data.questions[row_index]
        response_text = self._get_response_text(state, answer or "")
        
        self.treeview.item(
            row_id,
            values=(question, response_text),
            tags=(state.value,)
        )
        
        logger.debug(f"Updated cell [{row_index}] to {state.value}")
    
    def _get_response_text(self, state: CellState, answer: str) -> str:
        """Get display text for response cell."""
        if state == CellState.WORKING:
            return "Working..."
        elif state == CellState.COMPLETED:
            return answer
        else:  # PENDING
            return ""
```

### Step 3.2: Create WorkbookView

**File**: `src/ui/workbook_view.py`

```python
"""Workbook view with multiple sheet tabs."""

import tkinter as tk
from tkinter import ttk
import queue
from typing import Optional, List
from utils.data_types import WorkbookData, NavigationState, UIUpdateEvent, CellState
from ui.spreadsheet_view import SpreadsheetView
import logging

logger = logging.getLogger(__name__)

class WorkbookView:
    """Multi-sheet workbook view with tab navigation."""
    
    POLL_INTERVAL_MS = 50  # Poll UI queue every 50ms
    SPINNER_CHAR = "⟳"  # Unicode spinner
    
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
        self.parent = parent
        self.workbook_data = workbook_data
        self.ui_update_queue = ui_update_queue
        self.navigation_state = NavigationState()
        
        self.notebook: Optional[ttk.Notebook] = None
        self.sheet_views: List[SpreadsheetView] = []
    
    def render(self) -> ttk.Notebook:
        """Create notebook with all sheet tabs."""
        self.notebook = ttk.Notebook(self.parent)
        
        # Create a SpreadsheetView for each sheet
        for sheet_data in self.workbook_data.sheets:
            # Create frame for this sheet
            frame = ttk.Frame(self.notebook)
            
            # Create SpreadsheetView
            view = SpreadsheetView(frame, sheet_data)
            treeview = view.render()
            
            # Pack treeview
            treeview.pack(fill=tk.BOTH, expand=True)
            
            # Add tab
            self.notebook.add(frame, text=sheet_data.sheet_name)
            self.sheet_views.append(view)
        
        # Bind tab change event
        self.notebook.bind('<<NotebookTabChanged>>', self.handle_user_tab_click)
        
        return self.notebook
    
    def navigate_to_sheet(self, sheet_index: int) -> None:
        """Switch visible tab to specified sheet."""
        if not self.navigation_state.auto_navigation_enabled:
            logger.debug(f"Auto-navigation disabled, not switching to sheet {sheet_index}")
            return
        
        if 0 <= sheet_index < len(self.sheet_views):
            self.notebook.select(sheet_index)
            logger.info(f"Auto-navigated to sheet {sheet_index}")
    
    def update_tab_indicator(self, sheet_index: int, is_processing: bool) -> None:
        """Add or remove spinner indicator on tab."""
        if 0 <= sheet_index < len(self.workbook_data.sheets):
            sheet_name = self.workbook_data.sheets[sheet_index].sheet_name
            
            if is_processing:
                tab_text = f"{sheet_name} {self.SPINNER_CHAR}"
            else:
                tab_text = sheet_name
            
            self.notebook.tab(sheet_index, text=tab_text)
    
    def handle_user_tab_click(self, event: tk.Event) -> None:
        """Handle user clicking a sheet tab."""
        selected_index = self.notebook.index(self.notebook.select())
        self.navigation_state.lock_to_sheet(selected_index)
        logger.info(f"User selected sheet {selected_index}, auto-navigation disabled")
    
    def start_update_polling(self) -> None:
        """Begin polling ui_update_queue for events."""
        self._poll_queue()
    
    def _poll_queue(self) -> None:
        """Poll queue and process events."""
        try:
            while True:
                event = self.ui_update_queue.get_nowait()
                self._process_event(event)
        except queue.Empty:
            pass
        finally:
            # Schedule next poll
            self.parent.after(self.POLL_INTERVAL_MS, self._poll_queue)
    
    def _process_event(self, event: UIUpdateEvent) -> None:
        """Process a single UI update event."""
        event_type = event.event_type
        payload = event.payload
        
        logger.debug(f"Processing event: {event_type}")
        
        if event_type == 'SHEET_START':
            sheet_idx = payload['sheet_index']
            self.navigate_to_sheet(sheet_idx)
            self.update_tab_indicator(sheet_idx, is_processing=True)
        
        elif event_type == 'CELL_WORKING':
            sheet_idx = payload['sheet_index']
            row_idx = payload['row_index']
            self.sheet_views[sheet_idx].update_cell(row_idx, CellState.WORKING)
        
        elif event_type == 'CELL_COMPLETED':
            sheet_idx = payload['sheet_index']
            row_idx = payload['row_index']
            answer = payload['answer']
            self.sheet_views[sheet_idx].update_cell(row_idx, CellState.COMPLETED, answer)
        
        elif event_type == 'SHEET_COMPLETE':
            sheet_idx = payload['sheet_index']
            self.update_tab_indicator(sheet_idx, is_processing=False)
        
        elif event_type == 'ERROR':
            error_msg = payload.get('message', 'Unknown error')
            logger.error(f"Processing error: {error_msg}")
            # TODO: Show error dialog
```

---

## Phase 4: Excel Processor (2-3 hours)

**File**: `src/excel/processor.py`

```python
"""Excel workbook processing with agent workflow."""

import queue
import time
from typing import Dict
from agents.workflow_manager import AgentCoordinator
from utils.data_types import (
    WorkbookData, Question, UIUpdateEvent,
    ExcelProcessingResult, CellState
)
import logging

logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Processes Excel workbooks through multi-agent workflow."""
    
    def __init__(
        self,
        agent_coordinator: AgentCoordinator,
        ui_update_queue: queue.Queue
    ):
        """Initialize processor.
        
        Args:
            agent_coordinator: Initialized AgentCoordinator
            ui_update_queue: Thread-safe queue for UI updates
        """
        self.agent_coordinator = agent_coordinator
        self.ui_queue = ui_update_queue
    
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
            context: Domain context
            char_limit: Max answer length
            max_retries: Max retry attempts
            
        Returns:
            ExcelProcessingResult with statistics
        """
        start_time = time.time()
        total_processed = 0
        total_failed = 0
        
        for sheet_idx, sheet_data in enumerate(workbook_data.sheets):
            # Emit sheet start
            self._emit_event('SHEET_START', {'sheet_index': sheet_idx})
            sheet_data.is_processing = True
            
            # Process each question in sheet
            for row_idx, question_text in enumerate(sheet_data.questions):
                # Emit cell working
                self._emit_event('CELL_WORKING', {
                    'sheet_index': sheet_idx,
                    'row_index': row_idx
                })
                sheet_data.cell_states[row_idx] = CellState.WORKING
                
                # Create Question object
                question = Question(
                    text=question_text,
                    context=context,
                    char_limit=char_limit,
                    max_retries=max_retries
                )
                
                # Process with agents
                try:
                    result = await self.agent_coordinator.process_question(
                        question,
                        lambda agent, msg, progress: None  # No progress callback needed
                    )
                    
                    if result.success and result.answer:
                        # Success - emit completed
                        sheet_data.answers[row_idx] = result.answer.content
                        sheet_data.cell_states[row_idx] = CellState.COMPLETED
                        
                        self._emit_event('CELL_COMPLETED', {
                            'sheet_index': sheet_idx,
                            'row_index': row_idx,
                            'answer': result.answer.content
                        })
                        
                        total_processed += 1
                    else:
                        # Failed
                        sheet_data.answers[row_idx] = f"ERROR: {result.error_message}"
                        sheet_data.cell_states[row_idx] = CellState.COMPLETED
                        
                        self._emit_event('CELL_COMPLETED', {
                            'sheet_index': sheet_idx,
                            'row_index': row_idx,
                            'answer': f"ERROR: {result.error_message}"
                        })
                        
                        total_failed += 1
                
                except Exception as e:
                    logger.error(f"Error processing question: {e}")
                    sheet_data.answers[row_idx] = f"ERROR: {str(e)}"
                    sheet_data.cell_states[row_idx] = CellState.COMPLETED
                    
                    self._emit_event('CELL_COMPLETED', {
                        'sheet_index': sheet_idx,
                        'row_index': row_idx,
                        'answer': f"ERROR: {str(e)}"
                    })
                    
                    total_failed += 1
            
            # Emit sheet complete
            sheet_data.is_processing = False
            sheet_data.is_complete = True
            self._emit_event('SHEET_COMPLETE', {'sheet_index': sheet_idx})
        
        # Emit workbook complete
        processing_time = time.time() - start_time
        self._emit_event('WORKBOOK_COMPLETE', {'file_path': workbook_data.file_path})
        
        return ExcelProcessingResult(
            success=True,
            questions_processed=total_processed,
            questions_failed=total_failed,
            processing_time=processing_time,
            output_file_path=workbook_data.file_path
        )
    
    def _emit_event(self, event_type: str, payload: Dict) -> None:
        """Emit UI update event to queue."""
        event = UIUpdateEvent(event_type=event_type, payload=payload)
        self.ui_queue.put(event)
```

---

## Phase 5: Integration (2-3 hours)

### Step 5.1: Integrate with UIManager

**File**: `src/ui/main_window.py` (modify existing)

Add imports at top:

```python
import queue
from excel.loader import ExcelLoader
from excel.processor import ExcelProcessor
from ui.workbook_view import WorkbookView
```

Modify `_process_excel_internal`:

```python
async def _process_excel_internal(self, file_path: str) -> ExcelProcessingResult:
    """Internal async Excel processing."""
    # Step 1: Load workbook
    loader = ExcelLoader()
    workbook_data = loader.load_workbook(file_path)
    
    # Step 2: Create UI update queue
    ui_queue = queue.Queue()
    
    # Step 3: Replace answer_display with WorkbookView on main thread
    self.root.after(0, self._show_workbook_view, workbook_data, ui_queue)
    
    # Step 4: Process workbook
    processor = ExcelProcessor(self.agent_coordinator, ui_queue)
    result = await processor.process_workbook(
        workbook_data,
        self.context_var.get(),
        self.char_limit_var.get(),
        self.max_retries_var.get()
    )
    
    # Step 5: Save workbook if successful
    if result.success:
        loader.save_workbook(workbook_data)
    
    return result

def _show_workbook_view(self, workbook_data: WorkbookData, ui_queue: queue.Queue) -> None:
    """Replace answer_display with WorkbookView (main thread only)."""
    # Hide current answer display
    self.answer_display.pack_forget()
    
    # Create and show WorkbookView
    self.workbook_view = WorkbookView(
        self.answer_display.master,
        workbook_data,
        ui_queue
    )
    notebook = self.workbook_view.render()
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Start polling for updates
    self.workbook_view.start_update_polling()
```

---

## Testing Strategy

### Unit Tests

1. `tests/unit/test_data_types.py` - Data structures
2. `tests/unit/test_excel_loader.py` - Excel loading/saving
3. `tests/unit/test_ui_components.py` - SpreadsheetView, WorkbookView

### Integration Tests

1. `tests/integration/test_excel_workflow.py` - End-to-end with mock agents
2. `tests/integration/test_ui_updates.py` - UI update queue processing

### Manual Testing

1. Create test Excel with 3 sheets, 5 questions each
2. Run application, import file
3. Verify:
   - All sheets visible in tabs
   - Cells turn pink then green
   - Answers appear in real-time
   - Tab navigation works
   - Spinner appears/disappears
   - File saves only at end

---

## Troubleshooting

### Issue: Treeview not updating

**Solution**: Ensure updates are on main thread via `root.after()`

### Issue: Tab spinner not showing

**Solution**: Verify Unicode support, use alternative character if needed

### Issue: Performance slow with 100+ rows

**Solution**: Profile with `cProfile`, consider virtual scrolling

---

## Completion Checklist

- [ ] All data types created and tested
- [ ] ExcelLoader loads and saves correctly
- [ ] SpreadsheetView renders and updates cells
- [ ] WorkbookView manages tabs and navigation
- [ ] ExcelProcessor emits events correctly
- [ ] UIManager integration complete
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing completed
- [ ] Documentation updated

---

## Next Steps

After completing this quickstart:

1. Run `/speckit.tasks` to break into detailed implementation tasks
2. Create feature branch: `git checkout -b 002-live-excel-processing`
3. Implement in order: Data → Loader → UI → Processor → Integration
4. Test incrementally after each phase
5. Submit PR when all tests pass

---

## Support

For questions or issues:

1. Check existing codebase patterns in `src/ui/main_window.py`
2. Review similar async patterns in `src/agents/workflow_manager.py`
3. Refer to `research.md` for architectural decisions
4. Consult `data-model.md` for state management details
