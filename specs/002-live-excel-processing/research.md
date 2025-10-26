# Research: Live Excel Processing Visualization

**Feature**: 002-live-excel-processing  
**Date**: October 23, 2025  
**Phase**: 0 - Research & Technical Decisions

## Executive Summary

This feature requires live UI updates synchronized with asynchronous agent processing across multiple Excel sheets. The primary technical challenges are: (1) rendering spreadsheet-like tables in tkinter with dynamic cell styling, (2) coordinating UI updates from background async workflows, and (3) managing multi-sheet navigation state while respecting user control.

## Research Topics

### 1. tkinter Spreadsheet Rendering Options

**Decision**: Use tkinter Treeview widget in "table mode" for spreadsheet rendering

**Rationale**:
- Treeview supports table display with column headers and rows
- Built-in scrolling for large datasets
- Supports per-row tag-based styling (backgrounds, colors)
- Already available in tkinter standard library (no new dependencies)
- Proven performance for 100-1000 rows

**Alternatives Considered**:
- **tksheet library**: Third-party Excel-like widget with rich features, but adds dependency and may be overkill for our needs
- **Custom Canvas-based rendering**: Maximum control but significant development effort and complexity
- **Grid of Label widgets**: Simple but poor performance with >50 cells and no built-in scrolling

**Implementation Notes**:
- Use Treeview with `show="tree headings"` to hide tree column
- Configure columns for "Question" and "Response"
- Apply tags like `'working'`, `'completed'`, `'pending'` for cell styling
- Use `item()` method to update cell content and tags dynamically

**References**:
- tkinter.ttk.Treeview documentation
- Existing codebase pattern: status_manager.py uses ttk widgets effectively

---

### 2. Async-to-UI Thread Communication Pattern

**Decision**: Use `root.after()` with thread-safe queue for UI updates from async workflows

**Rationale**:
- tkinter is not thread-safe - all UI updates must occur on main thread
- `root.after(0, callback)` schedules callback on main thread's next event loop iteration
- Existing codebase already uses this pattern in main_window.py (see `_handle_question_result`)
- Queue provides thread-safe mechanism for background threads to send update messages

**Alternatives Considered**:
- **Direct UI updates from async code**: Not safe with tkinter - causes crashes
- **Threading.Event synchronization**: Too low-level, doesn't solve UI thread requirement
- **asyncio event loop integration**: tkinter's event loop is separate from asyncio

**Implementation Notes**:
- Create `UIUpdateQueue` class wrapping `queue.Queue`
- Background async task puts update events: `{'type': 'cell_update', 'sheet': 0, 'row': 3, 'status': 'working'}`
- Main thread polls queue via `root.after(50, poll_queue)` every 50ms
- Process updates and apply to Treeview widgets

**Code Pattern**:

```python
class SpreadsheetView:
    def __init__(self, parent, ui_update_queue):
        self.queue = ui_update_queue
        self.treeview = ttk.Treeview(parent, columns=('question', 'response'))
        self._start_queue_polling()
    
    def _start_queue_polling(self):
        """Poll queue for updates from async workflow."""
        try:
            while True:
                update = self.queue.get_nowait()
                self._apply_update(update)
        except queue.Empty:
            pass
        finally:
            # Schedule next poll in 50ms
            self.parent.after(50, self._start_queue_polling)
```

---

### 3. Multi-Sheet Tab Navigation

**Decision**: Use ttk.Notebook widget for sheet tabs with custom tab state tracking

**Rationale**:
- ttk.Notebook provides native tab interface similar to Excel
- Tabs display horizontally below content (matches Excel UX)
- Built-in tab click events via `<<NotebookTabChanged>>`
- Can programmatically select tabs via `.select()` method
- Lightweight and part of tkinter standard library

**Alternatives Considered**:
- **Custom tab bar with Frame+Buttons**: More control but requires implementing all tab logic
- **Separate button row**: Less intuitive than tab interface

**Implementation Notes**:
- One ttk.Notebook per workbook
- Each tab contains a SpreadsheetView (Treeview)
- Track navigation state: `user_locked_sheet` (int or None)
- On `<<NotebookTabChanged>>`: set `user_locked_sheet = current_tab_index`
- Auto-navigation only when `user_locked_sheet is None`
- Add spinner icon to tab text: `notebook.tab(index, text=f"Sheet1 ⟳")` using Unicode spinner

**Tab State Machine**:

```
Initial: user_locked_sheet = None
User clicks tab -> user_locked_sheet = clicked_index
Agent moves to new sheet:
    if user_locked_sheet is None:
        notebook.select(new_sheet_index)
    else:
        # Keep current view (user override active)
```

---

### 4. Excel Multi-Sheet Processing Workflow

**Decision**: Sequential sheet processing with progress events for each question

**Rationale**:
- Maintains simplicity - process one sheet at a time, one question at a time
- Fits existing AgentCoordinator.process_batch() pattern
- Clear progress tracking per sheet
- Easier to test and debug than concurrent processing

**Alternatives Considered**:
- **Concurrent sheet processing**: Complex state management, harder to show clear progress
- **Concurrent questions within sheet**: Could overwhelm Azure agents, harder to track visually

**Implementation Notes**:
- Load all sheets into memory: `{sheet_name: [Question objects]}`
- For each sheet in order:
  - Emit sheet start event
  - Process questions via `process_batch()`
  - Each question emits cell updates (working -> completed)
  - Emit sheet complete event
- Save workbook only after all sheets processed

**Workflow Integration**:

```python
async def process_excel_workbook(file_path):
    workbook_data = load_excel_sheets(file_path)  # {sheet_name: questions}
    
    for sheet_index, (sheet_name, questions) in enumerate(workbook_data.items()):
        emit_event('sheet_start', sheet_index=sheet_index)
        
        for q_index, question in enumerate(questions):
            emit_event('cell_working', sheet=sheet_index, row=q_index)
            result = await agent_coordinator.process_question(question)
            emit_event('cell_complete', sheet=sheet_index, row=q_index, answer=result.answer)
        
        emit_event('sheet_complete', sheet_index=sheet_index)
    
    save_excel_workbook(file_path, answers)
```

---

### 5. Cell State Management

**Decision**: Use state machine with three states per cell: PENDING, WORKING, COMPLETED

**Rationale**:
- Clear visual states map directly to user requirements
- Simple state transitions: PENDING -> WORKING -> COMPLETED
- No backward transitions needed
- Easy to represent with Treeview tags

**State Definitions**:
- **PENDING**: Default state, no processing started, white background, empty response cell
- **WORKING**: Agent actively processing, pink background (#FFB6C1), "Working..." text
- **COMPLETED**: Processing done, light green background (#90EE90), answer text displayed

**Implementation Notes**:
- Store cell states in Python dict: `cell_states[sheet_idx][row_idx] = CellState.WORKING`
- Configure Treeview tags with backgrounds:
  - `treeview.tag_configure('working', background='#FFB6C1')`
  - `treeview.tag_configure('completed', background='#90EE90')`
- Update cell: `treeview.item(row_id, values=(question, answer), tags=('completed',))`

---

### 6. Performance Optimization Strategies

**Decision**: Virtual scrolling and lazy loading for large sheets (future optimization)

**Rationale**:
- For MVP (100 questions/sheet), full rendering is acceptable
- Treeview handles 100 rows efficiently with built-in scrolling
- Defer virtualization until performance issues identified

**Alternatives Considered**:
- **Immediate virtualization**: Premature optimization, adds complexity
- **Pagination**: Poor UX for continuous scrolling

**Implementation Notes**:
- Initial release: Render all rows immediately
- Monitor performance with 100+ row sheets
- If needed, implement virtual scrolling:
  - Render only visible rows + buffer (e.g., 50 rows)
  - Update visible range on scroll events
  - Maintain full data model in memory

---

## Best Practices Applied

### tkinter GUI Best Practices

1. **Thread Safety**: All UI updates via `root.after()` from main thread
2. **Responsive UI**: Long operations in background threads, never block main thread
3. **Widget Reuse**: Use ttk widgets for native platform appearance
4. **Layout**: Use pack/grid managers, avoid absolute positioning
5. **State Management**: Separate UI state from business logic

### Azure AI Foundry Integration

1. **Existing Patterns**: Reuse AgentCoordinator and FoundryAgentSession
2. **Progress Callbacks**: Extend existing progress_callback mechanism for cell updates
3. **Error Handling**: Leverage existing exception hierarchy (AzureServiceError, etc.)
4. **Resource Cleanup**: No changes needed - existing cleanup handles all agents

### Excel Processing

1. **openpyxl Usage**: Already in requirements.txt, proven library
2. **Read All Sheets**: `workbook.sheetnames` and `workbook[sheet_name]`
3. **Write Preservation**: Load workbook, modify cells, save (preserves formatting)
4. **Column Detection**: Assume columns A (questions) and B (responses) per spec

---

## Open Questions Resolved

### Q1: How to handle very long answer text in cells?

**Resolution**: Treeview supports multi-line text via word wrapping
- Configure column width appropriately
- Use `rowheight` parameter for taller rows if needed
- Tooltip on hover for full text (future enhancement)

### Q2: How to show spinner icon in tab?

**Resolution**: Use Unicode spinner character (⟳ U+27F3) in tab text
- Update tab text: `notebook.tab(index, text=f"{sheet_name} ⟳")`
- Remove spinner: `notebook.tab(index, text=sheet_name)`
- Alternative: Use animated GIF via PhotoImage (more complex)

### Q3: How to handle hidden Excel sheets?

**Resolution**: Skip hidden sheets by checking `sheet.sheet_state`
- openpyxl exposes `worksheet.sheet_state` property
- Only process sheets where `sheet_state == 'visible'`
- Log skipped sheets for user awareness

---

## Risk Mitigation

### Risk 1: UI Responsiveness During Heavy Processing

**Mitigation**: 
- Background threading already implemented
- UI update queue limits update frequency (50ms polling)
- Test with maximum load (1000 questions across 10 sheets)

### Risk 2: Excel File Corruption on Crash

**Mitigation**:
- Never save until all processing complete (per requirement)
- Original file remains untouched during processing
- Create backup copy before save (future enhancement)

### Risk 3: Memory Usage with Large Workbooks

**Mitigation**:
- Load full workbook into memory (acceptable for 1000 questions ~= 500KB text)
- Monitor memory usage during testing
- Add memory limits if needed (reject files >10MB)

---

## Dependencies & Tools

### No New Dependencies Required

All required libraries already in requirements.txt:
- `tkinter`: Standard library (Python 3.11+)
- `openpyxl`: Excel reading/writing
- `agent-framework-azure-ai`: Agent workflow
- `pytest`: Testing

### Development Tools

- VS Code with Python extension (already in use)
- pytest for unit tests
- Mock Azure services for testing (existing pattern in tests/mock/)

---

## Implementation Phases

Based on research findings:

**Phase 1**: Core UI Components
- SpreadsheetView class with Treeview
- WorkbookView with Notebook tabs
- UIUpdateQueue for thread-safe updates

**Phase 2**: Excel Integration
- Multi-sheet loading with openpyxl
- Sequential processing workflow
- Progress event emission

**Phase 3**: State Management
- Cell state machine implementation
- Navigation lock tracking
- Auto-navigation logic

**Phase 4**: Testing
- Unit tests for UI components
- Integration tests for Excel workflow
- Mock agent tests for state transitions

---

## Conclusion

The research confirms that all required functionality can be implemented using existing dependencies and patterns. The tkinter Treeview and Notebook widgets provide appropriate UI primitives, the existing async-to-UI communication pattern via `root.after()` supports live updates, and the current AgentCoordinator workflow integrates cleanly with sheet-by-sheet processing. No new architectural patterns or dependencies are needed.
