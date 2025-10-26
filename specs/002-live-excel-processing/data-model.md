# Data Model: Live Excel Processing Visualization

**Feature**: 002-live-excel-processing  
**Date**: October 23, 2025  
**Phase**: 1 - Design

## Overview

This document defines the data structures and state management for live Excel processing visualization. The model supports multi-sheet workbooks with real-time cell status updates synchronized with the multi-agent processing workflow.

## Core Entities

### CellState (Enum)

Represents the processing state of a single response cell.

**States**:

- `PENDING`: Initial state, no processing started
- `WORKING`: Agent actively processing this question
- `COMPLETED`: Processing finished, answer available

**Transitions**:

```
PENDING → WORKING → COMPLETED
```

**Validation Rules**:

- State can only progress forward (no backward transitions)
- COMPLETED state requires non-empty answer text

---

### SheetData

Represents a single worksheet with questions and their processing state.

**Fields**:

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `sheet_name` | str | Display name of the sheet | Non-empty, max 31 chars (Excel limit) |
| `sheet_index` | int | Zero-based position in workbook | >= 0 |
| `questions` | List[str] | Question text for each row | Non-empty list, each question non-empty |
| `answers` | List[Optional[str]] | Answer text for each row | Same length as questions |
| `cell_states` | List[CellState] | Processing state for each row | Same length as questions |
| `is_processing` | bool | Whether this sheet is currently active | - |
| `is_complete` | bool | Whether all questions in sheet are done | - |

**Invariants**:

- `len(questions) == len(answers) == len(cell_states)`
- `is_complete == all(s == CellState.COMPLETED for s in cell_states)`
- `is_processing` is mutually exclusive across sheets (only one active at a time)

**Operations**:

- `get_pending_questions() -> List[Tuple[int, str]]`: Returns indices and text of questions in PENDING state
- `mark_working(row_index: int)`: Transitions cell to WORKING state
- `mark_completed(row_index: int, answer: str)`: Transitions cell to COMPLETED with answer
- `get_progress() -> float`: Returns completion percentage (0.0 to 1.0)

---

### WorkbookData

Represents the entire Excel workbook being processed.

**Fields**:

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `file_path` | str | Absolute path to Excel file | Must exist, must end in .xlsx or .xls |
| `sheets` | List[SheetData] | All sheets in workbook order | Non-empty, max 10 sheets |
| `current_sheet_index` | int | Sheet currently being processed | Valid index into sheets list |
| `total_questions` | int | Total questions across all sheets | Sum of len(sheet.questions) for all sheets |
| `completed_questions` | int | Total completed across all sheets | Sum of COMPLETED cells |

**Invariants**:

- Only one sheet has `is_processing=True` at any time
- `current_sheet_index` points to sheet with `is_processing=True`
- `completed_questions <= total_questions`

**Operations**:

- `get_active_sheet() -> SheetData`: Returns currently processing sheet
- `advance_to_next_sheet() -> bool`: Moves to next sheet, returns False if no more sheets
- `get_overall_progress() -> float`: Returns global completion percentage
- `is_complete() -> bool`: Returns True if all sheets complete

---

### NavigationState

Tracks user interaction with sheet tabs to control auto-navigation.

**Fields**:

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `user_selected_sheet` | Optional[int] | Index of sheet user manually clicked, or None | Valid sheet index or None |
| `auto_navigation_enabled` | bool | Whether system can auto-navigate | Derived: True if user_selected_sheet is None |

**Operations**:

- `lock_to_sheet(sheet_index: int)`: User clicked tab, disable auto-navigation
- `enable_auto_navigation()`: Clear user selection, enable auto-navigation
- `should_navigate_to(sheet_index: int) -> bool`: Returns True if navigation allowed

**Behavior**:

```python
def should_navigate_to(sheet_index: int) -> bool:
    """Returns True if the view should switch to the given sheet."""
    if self.user_selected_sheet is None:
        return True  # Auto-navigation enabled
    return False  # User has control
```

---

### UIUpdateEvent

Represents an event from the background processing workflow to the UI thread.

**Event Types**:

| Type | Payload | Description |
|------|---------|-------------|
| `SHEET_START` | `{sheet_index: int}` | Processing started on a new sheet |
| `CELL_WORKING` | `{sheet_index: int, row_index: int}` | Agent started processing a question |
| `CELL_COMPLETED` | `{sheet_index: int, row_index: int, answer: str}` | Agent completed a question |
| `SHEET_COMPLETE` | `{sheet_index: int}` | All questions in sheet done |
| `WORKBOOK_COMPLETE` | `{file_path: str}` | All sheets processed, file saved |
| `ERROR` | `{error_type: str, message: str}` | Processing error occurred |

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | str | One of the event types above |
| `payload` | Dict[str, Any] | Type-specific data |
| `timestamp` | float | Time event was created (time.time()) |

**Usage**:

Events are placed in a `queue.Queue` by background processing thread and consumed by UI thread via `root.after()` polling.

---

## UI Component Models

### SpreadsheetViewModel

Manages the visual representation of a single sheet in the Treeview.

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `sheet_data` | SheetData | Underlying sheet data |
| `row_ids` | List[str] | Treeview item IDs for each row |
| `treeview_widget` | ttk.Treeview | The actual tkinter widget |

**Operations**:

- `render_initial()`: Populate treeview with all questions
- `update_cell(row_index: int, state: CellState, answer: Optional[str])`: Update visual state
- `refresh()`: Redraw entire view from sheet_data

**Cell Rendering Rules**:

- `PENDING`: White background, question in column 1, empty column 2
- `WORKING`: Pink background (#FFB6C1), question in column 1, "Working..." in column 2
- `COMPLETED`: Light green background (#90EE90), question in column 1, answer in column 2

---

### WorkbookViewModel

Manages the Notebook widget with multiple sheet tabs.

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `workbook_data` | WorkbookData | Underlying workbook data |
| `navigation_state` | NavigationState | Tab navigation control |
| `sheet_views` | List[SpreadsheetViewModel] | One view per sheet |
| `notebook_widget` | ttk.Notebook | The actual tkinter widget |

**Operations**:

- `render_initial()`: Create all tabs and their SpreadsheetViewModels
- `navigate_to_sheet(sheet_index: int)`: Switch visible tab if allowed
- `update_tab_indicator(sheet_index: int, is_processing: bool)`: Add/remove spinner
- `handle_user_tab_click(sheet_index: int)`: Lock navigation to user selection

**Tab Display Rules**:

- Processing sheet: `"{sheet_name} ⟳"` (with Unicode spinner)
- Other sheets: `"{sheet_name}"` (plain text)
- User-selected tab: Notebook highlights it (built-in behavior)

---

## State Transitions

### Question Processing Flow

```
1. SHEET_START event
   → WorkbookData: set current_sheet_index, sheet.is_processing = True
   → UI: navigate_to_sheet(index) if auto-navigation enabled
   → UI: update_tab_indicator(index, is_processing=True)

2. CELL_WORKING event
   → SheetData: cell_states[row] = WORKING
   → UI: update_cell(row, WORKING, answer=None)

3. CELL_COMPLETED event
   → SheetData: cell_states[row] = COMPLETED, answers[row] = answer
   → WorkbookData: completed_questions += 1
   → UI: update_cell(row, COMPLETED, answer=answer)

4. SHEET_COMPLETE event
   → SheetData: is_processing = False, is_complete = True
   → UI: update_tab_indicator(index, is_processing=False)
   → WorkbookData: advance_to_next_sheet()
   → If next sheet exists: goto step 1
   → Else: goto step 5

5. WORKBOOK_COMPLETE event
   → Save Excel file with all answers
   → UI: Show completion message
   → Reset navigation_state
```

### User Navigation Flow

```
1. User clicks sheet tab
   → NavigationState: lock_to_sheet(clicked_index)
   → UI: notebook_widget.select(clicked_index)
   → Auto-navigation disabled

2. Processing continues in background
   → CELL_WORKING, CELL_COMPLETED events still processed
   → UI updates occur on all sheets (not just visible one)
   → View remains locked to user's selection

3. User clicks different tab
   → NavigationState: update user_selected_sheet
   → View switches to new selection
   → Auto-navigation still disabled

(Optional) User re-enables auto-navigation (future enhancement):
   → NavigationState: enable_auto_navigation()
   → System can now navigate to processing sheet
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Background Thread                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Excel Loader                                         │  │
│  │  ↓                                                     │  │
│  │  WorkbookData (sheets, questions)                     │  │
│  │  ↓                                                     │  │
│  │  AgentCoordinator.process_batch()                     │  │
│  │  ↓                                                     │  │
│  │  For each question:                                   │  │
│  │    - Emit CELL_WORKING → UIUpdateQueue               │  │
│  │    - Process with agents                              │  │
│  │    - Emit CELL_COMPLETED → UIUpdateQueue             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
                     UIUpdateQueue (thread-safe)
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Main Thread (UI)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  root.after(50ms, poll_queue)                         │  │
│  │  ↓                                                     │  │
│  │  Process UIUpdateEvents                               │  │
│  │  ↓                                                     │  │
│  │  Update WorkbookViewModel                             │  │
│  │  ↓                                                     │  │
│  │  Update SpreadsheetViewModel                          │  │
│  │  ↓                                                     │  │
│  │  Apply to ttk.Treeview (visual update)               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Validation Rules

### Excel File Validation

- File must exist and be readable
- File extension must be .xlsx or .xls
- File must contain at least 1 visible sheet
- Each sheet must have at least 1 question in column A
- File size should be < 10MB (soft limit)

### Sheet Validation

- Sheet name must be non-empty and <= 31 characters
- Questions must be in column A (first column)
- Responses will be written to column B (second column)
- Hidden sheets are skipped (not processed)
- Maximum 10 sheets per workbook

### Question Validation

- Question text must be non-empty after stripping whitespace
- Maximum 100 questions per sheet
- Questions must be contiguous (no gaps in column A)

---

## Error Handling

### Invalid Excel File

- Event: `ERROR` with `error_type='excel_format'`
- UI: Display error dialog, clear spreadsheet view
- State: Reset to initial (no workbook loaded)

### Agent Processing Failure

- Event: `ERROR` with `error_type='agent_failure'`
- UI: Mark cell with red background, show error in tooltip
- State: Continue processing remaining questions

### Unexpected Crash During Processing

- Excel file not saved (remains unchanged)
- No partial data written
- User can restart application and re-process

---

## Performance Considerations

### Memory Usage

- WorkbookData holds all questions/answers in memory
- Estimated: 1KB per question × 1000 questions = 1MB (acceptable)
- Treeview widget holds all rows (100 rows × 10 sheets = 1000 items)

### Update Frequency

- UI update queue polled every 50ms
- Maximum update rate: 20 updates/second
- Batch multiple updates if queue has >1 event

### Threading Model

- Background thread: Excel loading, agent processing
- Main thread: All UI updates via `root.after()`
- Thread communication: `queue.Queue` (thread-safe)

---

## Future Extensions

### Possible Enhancements (Not in MVP)

- **Pause/Resume**: Allow user to pause processing
- **Cell tooltips**: Show full answer text on hover for long answers
- **Export progress**: Save intermediate results to separate file
- **Undo**: Ability to re-process specific questions
- **Batch operations**: Select multiple cells for re-processing

These would require additional state management and UI components but follow the same data model patterns.
