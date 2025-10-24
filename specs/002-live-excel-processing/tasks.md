# Task Breakdown: Live Excel Processing Visualization# Implementation Tasks: Live Excel Processing Visualization

**Feature**: 002-live-excel-processing **Feature**: 002-live-excel-processing

**Branch**: `002-live-excel-processing` **Date**: October 23, 2025

**Date**: October 23, 2025 **Status**: Ready for Implementation

**Status**: Ready for Implementation

## Overview

## Overview

This document breaks down the implementation into discrete, testable tasks organized by user story. Tasks are sequenced to maximize parallel development opportunities while respecting dependencies.

This document breaks down the Live Excel Processing Visualization feature into concrete, executable tasks organized by user story. Each phase corresponds to a complete, independently testable user story from the specification. Tasks are ordered to enable incremental delivery with P1 stories (foundational functionality) delivered first, followed by P2 stories (enhanced user experience).

**Legend**:

**Total Tasks**: 57 tasks across 10 phases

**Estimated Effort**: High (full-feature implementation) \* **\[P\]** = Parallelizable (can be worked on simultaneously with other \[P\] tasks)

**Testing Strategy**: TDD - Tests written before implementation per constitution \* **\[Story: US#\]** = Maps to user story in spec.md

**Parallelization Opportunities**: 23 tasks marked \[P\] for parallel execution\* **Dependencies** = Must complete before starting this task

## Implementation Strategy---

**MVP Scope**: Phase 3 (User Story 1) delivers the minimum viable product - basic spreadsheet rendering in the Answer area. This provides immediate value by showing users what will be processed.## Phase 1: Project Setup & Infrastructure

**Incremental Delivery Order**:### T001 - Create Feature Branch and Directory Structure \[P\]

**Setup** (Phase 1): Infrastructure and data types

**Foundational** (Phase 2): Excel loading and core UI framework**Description**: Set up branch and create empty module directories for new code.

**US1** (Phase 3): View live spreadsheet - Basic visualization

**US4** (Phase 4): Multi-sheet processing - Essential for real workbooks**Story**: Foundation for all user stories

**US7** (Phase 5): Deferred save - Data integrity guarantee

**US2** (Phase 6): In-progress status - Live feedback**Steps**:

**US3** (Phase 7): Completed answers - Visual confirmation

**US5** (Phase 8): Sheet status indicators - Progress tracking1. Ensure on `002-live-excel-processing` branch (already created)

**US6** (Phase 9): User navigation - User control2. Create empty `src/excel/__init__.py`

**Polish** (Phase 10): Cross-cutting concerns3. Verify `src/ui/` directory exists (already present)

Create empty `tests/unit/` files for new tests

\---5. Create `tests/fixtures/excel/` directory for test files

## Phase 1: Setup & Infrastructure**Acceptance Criteria**:

**Goal**: Establish shared data types, exceptions, and test infrastructure needed by all user stories.\* Directory structure matches plan.md

*   All `__init__.py` files created

**Tasks**:\* No import errors when importing new modules

### T001: \[P\] Create data type enums and basic structures**Estimated Time**: 15 minutes

**File**: `src/utils/data_types.py`

**Description**: Add CellState enum (PENDING, WORKING, COMPLETED) and basic type imports. **Dependencies**: None

**Definition of Done**:

CellState enum defined with 3 states---

Type hints imported (List, Optional, Dict)

Enum supports string conversion### T002 - Update .github/copilot-instructions.md \[P\]

### T002: \[P\] Create test fixtures directory structure**Description**: Update agent context with new tech stack and structure.

**File**: `tests/fixtures/excel/`

**Description**: Create directory structure for test Excel files. **Story**: Foundation

**Definition of Done**:

`tests/fixtures/excel/` directory exists**Steps**:

README.md explaining fixture naming convention

.gitkeep files to preserve empty directories1. Add "Python 3.11+ + tkinter (GUI), openpyxl (Excel), agent-framework-azure-ai (multi-agent)" to Active Technologies

1.  Add "Excel files (.xlsx) on local filesystem" to Active Technologies

### T003: \[P\] Add Excel-specific exceptions3. Update project structure section with new src/excel/ and src/ui/ files

**File**: `src/utils/exceptions.py` 4. Commit changes

**Description**: Verify ExcelFormatError exists, add ExcelProcessingError if needed.

**Definition of Done**:**Acceptance Criteria**:

ExcelFormatError exception class exists

ExcelProcessingError exception class created\* .github/copilot-instructions.md reflects current architecture

Both inherit from appropriate base exception\* No merge conflicts with existing content

### T004: \[P\] Create UIUpdateEvent data class**Estimated Time**: 10 minutes

**File**: `src/utils/data_types.py`

**Description**: Define UIUpdateEvent class for thread-safe UI updates. **Dependencies**: None

**Definition of Done**:

UIUpdateEvent dataclass with event\_type, payload, timestamp---

Event type constants (SHEET\_START, CELL\_WORKING, etc.)

Type hints for all fields## Phase 2: Core Data Structures (Foundational)

**Checkpoint**: Infrastructure ready for module development### T003 - Implement CellState Enum

\---**Description**: Create enum for cell processing states.

## Phase 2: Foundational Components (Blocking Prerequisites)**Story**: Foundation for US2, US3

**Goal**: Build core Excel loading, data structures, and base UI framework required by ALL user stories. Nothing can proceed without these.**Steps**:

**Tasks**:1. Open `src/utils/data_types.py`

1.  Add `from enum import Enum` import

### T005: Create SheetData data class3. Define `CellState` enum with PENDING, WORKING, COMPLETED values

**File**: `src/utils/data_types.py` 4. Add docstring explaining state transitions

**Description**: Define SheetData class per data-model.md specification.

**Definition of Done**:**Acceptance Criteria**:

All fields defined (sheet\_name, sheet\_index, questions, answers, cell\_states, is\_processing, is\_complete)

Invariant: len(questions) == len(answers) == len(cell\_states)\* CellState.PENDING.value == "pending"

Methods: get\_pending\_questions(), mark\_working(), mark\_completed(), get\_progress()\* CellState.WORKING.value == "working"

Unit test validates invariants\* CellState.COMPLETED.value == "completed"

*   No import errors

### T006: Create WorkbookData data class

**File**: `src/utils/data_types.py` **Estimated Time**: 10 minutes

**Description**: Define WorkbookData class per data-model.md specification.

**Definition of Done**:**Dependencies**: T001

All fields defined (file\_path, sheets, current\_sheet\_index, total\_questions, completed\_questions)

Methods: get\_active\_sheet(), advance\_to\_next\_sheet(), get\_overall\_progress(), is\_complete()---

Unit test validates sheet progression logic

### T004 - Implement SheetData Dataclass

### T007: Create NavigationState class

**File**: `src/utils/data_types.py` **Description**: Create dataclass for single sheet representation.

**Description**: Define NavigationState class for tracking user tab selection.

**Definition of Done**:**Story**: Foundation for US1, US4

Fields: user\_selected\_sheet (Optional\[int\]), auto\_navigation\_enabled (bool)

Methods: lock\_to\_sheet(), enable\_auto\_navigation(), should\_navigate\_to()**Steps**:

Unit test validates navigation lock behavior

1.  Add SheetData dataclass to `src/utils/data_types.py`

### T008: \[P\] Write unit tests for data types2. Include fields: sheet\_name, sheet\_index, questions, answers, cell\_states, is\_processing, is\_complete

**File**: `tests/unit/test_data_types.py` 3. Add `__post_init__` validation for list length invariants

**Description**: Test all data type classes, state transitions, and invariants. 4. Implement `get_progress()` method returning completion percentage

**Definition of Done**:

Tests for CellState transitions**Acceptance Criteria**:

Tests for SheetData operations and invariants

Tests for WorkbookData progression\* All fields defined with correct types

Tests for NavigationState lock/unlock\* Invariant validation raises AssertionError if lists differ in length

100% coverage of data type logic\* get\_progress() returns 0.0 for empty sheet, 1.0 for all completed

*   Dataclass can be instantiated successfully

### T009: Create ExcelLoader class skeleton

**File**: `src/excel/loader.py` **Estimated Time**: 30 minutes

**Description**: Create ExcelLoader class with method signatures per contracts.

**Definition of Done**:**Dependencies**: T003

Class defined with **init**

load\_workbook() method signature---

save\_workbook() method signature

Docstrings from module\_interfaces.md### T005 - Implement WorkbookData Dataclass

### T010: \[P\] Create test Excel fixtures**Description**: Create dataclass for entire workbook.

**File**: `tests/fixtures/excel/`

**Description**: Create test Excel files for various scenarios. **Story**: Foundation for US1, US4, US7

**Definition of Done**:

`single_sheet_5_questions.xlsx`: 1 sheet, 5 questions in column A**Steps**:

`multi_sheet_3x10_questions.xlsx`: 3 sheets, 10 questions each

`hidden_sheets.xlsx`: 2 visible sheets, 1 hidden sheet1. Add WorkbookData dataclass to `src/utils/data_types.py`

`invalid_format.xlsx`: Corrupted/invalid Excel file2. Include fields: file\_path, sheets, current\_sheet\_index

All fixtures documented in fixtures README3. Add properties: total\_questions, completed\_questions

1.  Implement `get_active_sheet()` method

### T011: Implement ExcelLoader.load\_workbook()

**File**: `src/excel/loader.py` **Acceptance Criteria**:

**Description**: Load Excel file and create WorkbookData structure.

**Definition of Done**:\* All fields defined with correct types

Opens .xlsx files with openpyxl\* Properties compute correct totals across all sheets

Reads all visible sheets (skips hidden via sheet\_state check)\* get\_active\_sheet() returns sheet with is\_processing=True or None

Extracts questions from column A\* Dataclass can be instantiated with multiple sheets

Creates WorkbookData with SheetData for each sheet

Raises ExcelFormatError for invalid files**Estimated Time**: 30 minutes

Unit test with all fixtures

**Dependencies**: T004

### T012: Implement ExcelLoader.save\_workbook()

**File**: `src/excel/loader.py` ---

**Description**: Save answers back to column B of Excel file.

**Definition of Done**:### T006 - Implement NavigationState Dataclass

Opens existing workbook

Writes answers to column B for each sheet**Description**: Create dataclass for tracking user sheet navigation.

Preserves all Excel formatting

Preserves hidden sheets (writes to original workbook)**Story**: US6

Unit test verifies round-trip (load → modify → save → load)

**Steps**:

### T013: \[P\] Write unit tests for ExcelLoader

**File**: `tests/unit/test_excel_loader.py` 1. Add NavigationState dataclass to `src/utils/data_types.py`

**Description**: Test Excel loading and saving with all fixtures. 2. Include fields: user\_selected\_sheet (Optional\[int\])

**Definition of Done**:3. Add property: auto\_navigation\_enabled

Tests load\_workbook() with each fixture4. Implement methods: lock\_to\_sheet(), enable\_auto\_navigation()

Tests save\_workbook() round-trip

Tests hidden sheet preservation**Acceptance Criteria**:

Tests error cases (file not found, invalid format)

100% coverage of ExcelLoader\* auto\_navigation\_enabled returns True when user\_selected\_sheet is None

*   lock\_to\_sheet(idx) sets user\_selected\_sheet

### T014: Create SpreadsheetView class skeleton\* enable\_auto\_navigation() clears user\_selected\_sheet

**File**: `src/ui/spreadsheet_view.py` \* State correctly reflects navigation control

**Description**: Create SpreadsheetView class with method signatures per contracts.

**Definition of Done**:**Estimated Time**: 20 minutes

Class defined with **init**(parent, sheet\_data)

Method signatures: render(), update\_cell(), refresh()**Dependencies**: T003

Docstrings from module\_interfaces.md

Basic ttk.Treeview creation in render()---

### T015: Create WorkbookView class skeleton### T007 - Implement UIUpdateEvent Dataclass

**File**: `src/ui/workbook_view.py`

**Description**: Create WorkbookView class with method signatures per contracts. **Description**: Create dataclass for UI update events from background thread.

**Definition of Done**:

Class defined with **init**(parent, workbook\_data, ui\_update\_queue)**Story**: Foundation for US2, US3, US4, US5

Method signatures: render(), navigate\_to\_sheet(), update\_tab\_indicator(), start\_update\_polling(), handle\_user\_tab\_click()

Docstrings from module\_interfaces.md**Steps**:

Basic ttk.Notebook creation in render()

1.  Add UIUpdateEvent dataclass to `src/utils/data_types.py`

**Checkpoint**: Excel loading and base UI framework complete2. Include fields: event\_type (str), payload (Dict\[str, Any\]), timestamp (float)

1.  Add default\_factory for timestamp using time.time()

\---4. Document event types in docstring: SHEET\_START, CELL\_WORKING, CELL\_COMPLETED, SHEET\_COMPLETE, WORKBOOK\_COMPLETE, ERROR

## Phase 3: User Story 1 - View Live Spreadsheet in Answer Area (P1)**Acceptance Criteria**:

**Story**: When a user imports questions from Excel, they see the spreadsheet rendered in the Answer area with all questions visible in a table format.\* Dataclass can be instantiated with any event\_type and payload

*   Timestamp automatically populated on creation

**Independent Test**: Click "Import From Excel", select a file, verify Answer area displays table with all questions.\* Docstring lists all event types

**Tasks**:**Estimated Time**: 20 minutes

### T016: \[P\] Write test for SpreadsheetView rendering**Dependencies**: T003

**File**: `tests/unit/test_ui_components.py`

**Story**: \[US1\] ---

**Description**: Test SpreadsheetView creates Treeview with correct columns and rows.

**Definition of Done**:### T008 - Create Unit Tests for Data Types \[P\]

Test creates SpreadsheetView with test SheetData

Verifies Treeview has 2 columns (Question, Response)**Description**: Write comprehensive unit tests for all new data structures.

Verifies row count matches SheetData.questions length

Verifies all questions appear in correct order**Story**: Foundation

### T017: Implement SpreadsheetView.render()**Steps**:

**File**: `src/ui/spreadsheet_view.py`

**Story**: \[US1\] 1. Create `tests/unit/test_data_types.py`

**Description**: Create and configure Treeview widget to display sheet as table. 2. Test CellState enum values

**Definition of Done**:3. Test SheetData creation, validation, and get\_progress()

Creates ttk.Treeview with columns=('Question', 'Response')4. Test WorkbookData properties and get\_active\_sheet()

Configures column headings and widths5. Test NavigationState state transitions

Hides tree column (show="tree headings")6. Test UIUpdateEvent creation with timestamp

Adds vertical scrollbar

Inserts all questions as rows from sheet\_data**Acceptance Criteria**:

Test from T016 passes

*   All data type tests pass

### T018: Implement SpreadsheetView.refresh()\* Coverage includes edge cases (empty lists, None values)

**File**: `src/ui/spreadsheet_view.py` \* Tests verify invariant violations raise errors

**Story**: \[US1\]

**Description**: Redraw entire Treeview from current sheet\_data state. **Estimated Time**: 45 minutes

**Definition of Done**:

Deletes all existing Treeview items**Dependencies**: T003-T007

Re-inserts all rows from sheet\_data

Applies correct tags based on cell\_states---

Unit test verifies refresh with modified data

## Phase 3: User Story 1 - View Live Spreadsheet (P1)

### T019: \[P\] Write test for WorkbookView multi-sheet rendering

**File**: `tests/unit/test_ui_components.py` ### T009 - Implement ExcelLoader.load\_workbook()

**Story**: \[US1\]

**Description**: Test WorkbookView creates Notebook with tab for each sheet. **Description**: Load Excel file and extract questions from all visible sheets.

**Definition of Done**:

Test creates WorkbookView with multi-sheet WorkbookData**Story**: US1

Verifies Notebook has correct number of tabs

Verifies tab labels match sheet names**Steps**:

Verifies each tab contains SpreadsheetView

1.  Create `src/excel/loader.py`

### T020: Implement WorkbookView.render()2. Implement ExcelLoader class

**File**: `src/ui/workbook_view.py` 3. Implement load\_workbook(file\_path) method using openpyxl

**Story**: \[US1\] 4. Read questions from column A (starting row 2)

**Description**: Create Notebook with tab for each sheet, each containing SpreadsheetView. 5. Skip hidden sheets (sheet\_state != 'visible')

**Definition of Done**:6. Return WorkbookData with all sheets

Creates ttk.Notebook widget7. Raise FileNotFoundError or ExcelFormatError on failures

For each sheet in workbook\_data: creates tab with SpreadsheetView

Sets tab labels to sheet names**Acceptance Criteria**:

Stores sheet\_views list for later updates

Test from T019 passes\* Loads valid .xlsx files successfully

*   Extracts questions from column A

### T021: \[P\] Write integration test for Excel import UI flow\* Skips hidden sheets and logs warning

**File**: `tests/integration/test_excel_workflow.py` \* Raises appropriate exceptions for invalid files

**Story**: \[US1\] \* Returns WorkbookData with correct sheet count

**Description**: Test complete flow from Import button to rendered spreadsheet.

**Definition of Done**:**Estimated Time**: 1.5 hours

Test clicks Import Excel button

Selects test Excel file**Dependencies**: T005

Verifies Answer area replaced with WorkbookView

Verifies all sheets and questions visible---

Uses mock UIManager in test harness

### T010 - Create Test Fixtures for Excel Files \[P\]

### T022: Modify UIManager.\_on\_import\_excel\_clicked()

**File**: `src/ui/main_window.py` **Description**: Create sample Excel files for testing.

**Story**: \[US1\]

**Description**: Replace answer\_display with WorkbookView when Excel imported. **Story**: US1, US4

**Definition of Done**:

File dialog to select Excel file**Steps**:

Call ExcelLoader.load\_workbook()

Create WorkbookView(workbook\_data, ui\_update\_queue)1. Create `tests/fixtures/excel/` directory

Replace answer\_display widget with workbook\_view.render()2. Create `single_sheet_5_questions.xlsx` with 5 questions in Sheet1

Handle errors with dialogs3. Create `multi_sheet_3x10_questions.xlsx` with 3 sheets, 10 questions each

Integration test from T021 passes4. Create `hidden_sheets.xlsx` with 1 visible + 1 hidden sheet

1.  Create `invalid_format.txt` (non-Excel file)

### T023: \[P\] Add Excel basic formatting support to SpreadsheetView6. Create `empty_sheets.xlsx` with sheets containing no questions

**File**: `src/ui/spreadsheet_view.py`

**Story**: \[US1\] **Acceptance Criteria**:

**Description**: Read and render cell colors, bold, italic from Excel (FR-010a).

**Definition of Done**:\* All fixture files created and committed

Read openpyxl cell.font (bold, italic) and cell.fill (color)\* Files loadable with openpyxl

Apply to Treeview tags during render()\* Cover edge cases (hidden, empty, invalid)

Test with fixture containing formatted cells

Bold/italic applied to text**Estimated Time**: 30 minutes

Background colors applied to rows

**Dependencies**: T001

**Acceptance Test** (User Story 1):

Click "Import From Excel"---

Select `single_sheet_5_questions.xlsx`

Verify Answer area shows table with 2 columns### T011 - Create Unit Tests for ExcelLoader \[P\]

Verify 5 questions appear in Question column

Verify Response column is empty**Description**: Test Excel loading with various file formats.

Verify basic Excel formatting (colors, bold, italic) rendered

**Story**: US1

**Checkpoint**: MVP Complete - Users can see imported spreadsheets

**Steps**:

---

1.  Create `tests/unit/test_excel_loader.py`

## Phase 4: User Story 4 - Process All Sheets Sequentially (P1)2. Test loading valid single-sheet file

1.  Test loading multi-sheet file

**Story**: When an Excel file contains multiple sheets, the agent processes all sheets one by one in order, automatically switching the view to show the currently active sheet.4. Test skipping hidden sheets

1.  Test FileNotFoundError for missing file

**Independent Test**: Import 3-sheet file, verify agent processes Sheet 1 completely, then Sheet 2, then Sheet 3.6. Test ExcelFormatError for invalid format

1.  Test handling empty sheets

**Tasks**:

**Acceptance Criteria**:

### T024: Create ExcelProcessor class skeleton

**File**: `src/excel/processor.py` \* All ExcelLoader tests pass

**Story**: \[US4\] \* Tests use fixture files from T010

**Description**: Create ExcelProcessor class per contracts. \* Edge cases covered (empty, hidden, invalid)

**Definition of Done**:

Class defined with **init**(agent\_coordinator, ui\_update\_queue)**Estimated Time**: 1 hour

process\_workbook() method signature (async)

Docstrings from module\_interfaces.md**Dependencies**: T009, T010

### T025: \[P\] Write test for ExcelProcessor sheet sequencing---

**File**: `tests/integration/test_excel_workflow.py`

**Story**: \[US4\] ### T012 - Implement SpreadsheetView Class

**Description**: Test ExcelProcessor processes sheets in order.

**Definition of Done**:**Description**: Create tkinter Treeview-based spreadsheet renderer.

Mock AgentCoordinator with instant responses

Create 3-sheet WorkbookData**Story**: US1

Verify SHEET\_START events in order (0, 1, 2)

Verify all questions in sheet 0 before sheet 1 starts**Steps**:

Verify SHEET\_COMPLETE events in order

1.  Create `src/ui/spreadsheet_view.py`

### T026: Implement ExcelProcessor.process\_workbook() - basic loop2. Implement SpreadsheetView class with **init**(parent, sheet\_data)

**File**: `src/excel/processor.py` 3. Implement render() method creating ttk.Treeview

**Story**: \[US4\] 4. Configure columns: 'question' and 'response'

**Description**: Sequential sheet processing with event emission. 5. Configure tags for cell states: pending, working, completed

**Definition of Done**:6. Insert all rows from sheet\_data with appropriate tags

For each sheet in workbook\_data.sheets:7. Add vertical scrollbar

Emit SHEET\_START event8. Store row\_ids for later updates

For each question: process with agent\_coordinator

Emit SHEET\_COMPLETE event**Acceptance Criteria**:

Emit WORKBOOK\_COMPLETE event at end

Test from T025 passes\* Treeview renders with 2 columns

*   All questions from sheet\_data appear as rows

### T027: Integrate ExcelProcessor into UIManager\* Tags configured with correct colors (white, pink, green)

**File**: `src/ui/main_window.py` \* Scrollbar functional

**Story**: \[US4\] \* render() returns configured Treeview widget

**Description**: Create async method to start ExcelProcessor after Excel import.

**Definition of Done**:**Estimated Time**: 2 hours

\_process\_excel\_internal(file\_path) async method

Creates ExcelProcessor with agent\_coordinator and ui\_update\_queue**Dependencies**: T004

Starts processing in background thread/task

Returns immediately to keep UI responsive---

Integration test verifies processing starts

### T013 - Implement SpreadsheetView.update\_cell() \[P\]

### T028: Implement WorkbookView.start\_update\_polling()

**File**: `src/ui/workbook_view.py` **Description**: Add method to update individual cell visual state.

**Story**: \[US4\]

**Description**: Poll ui\_update\_queue and process events. **Story**: US2, US3

**Definition of Done**:

Poll queue every 50ms via root.after()**Steps**:

Process all events in queue (get\_nowait() loop)

Handle SHEET\_START event (navigate to sheet if allowed)1. Add update\_cell(row\_index, state, answer) method to SpreadsheetView

Handle SHEET\_COMPLETE event (update tab)2. Implement \_get\_response\_text() helper for state-based text

Re-schedule next poll3. Update Treeview item with new values and tags

Unit test verifies event processing4. Add logging for cell updates

1.  Handle invalid row\_index gracefully

### T029: Implement WorkbookView.navigate\_to\_sheet()

**File**: `src/ui/workbook_view.py` **Acceptance Criteria**:

**Story**: \[US4\]

**Description**: Switch visible tab to specified sheet. \* update\_cell() changes cell background and text

**Definition of Done**:\* PENDING: white background, empty response

Check navigation\_state.should\_navigate\_to(sheet\_index)\* WORKING: pink background, "Working..." text

If allowed: notebook\_widget.select(tab\_index)\* COMPLETED: green background, answer text displayed

Update workbook\_data.current\_sheet\_index\* Invalid row\_index logs warning without crashing

Unit test verifies navigation and lock respect

**Estimated Time**: 45 minutes

### T030: \[P\] Write integration test for multi-sheet processing

**File**: `tests/integration/test_excel_workflow.py` **Dependencies**: T012

**Story**: \[US4\]

**Description**: End-to-end test with 3-sheet Excel file. ---

**Definition of Done**:

Load multi\_sheet\_3x10\_questions.xlsx### T014 - Create Mock UI Tests for SpreadsheetView \[P\]

Start processing with mock agents

Verify view switches to Sheet 1, then 2, then 3**Description**: Test SpreadsheetView rendering and updates without full UI.

Verify all 30 questions processed (10 per sheet)

Verify WORKBOOK\_COMPLETE event fires**Story**: US1

**Acceptance Test** (User Story 4):**Steps**:

Import `multi_sheet_3x10_questions.xlsx` (3 sheets, 10 questions each)

Start processing1. Create `tests/unit/test_ui_components.py`

Verify Sheet 1 processes all 10 questions first2. Create helper to instantiate SpreadsheetView with mock parent

Verify view auto-switches to Sheet 2 when Sheet 1 done3. Test render() creates Treeview with correct columns

Verify Sheet 2 processes all 10 questions4. Test initial rendering shows all questions

Verify view auto-switches to Sheet 3 when Sheet 2 done5. Test update\_cell() changes visual state

Verify Sheet 3 processes all 10 questions6. Test cell color transitions (PENDING → WORKING → COMPLETED)

Verify all sheets complete

**Acceptance Criteria**:

**Checkpoint**: Multi-sheet sequential processing works

*   All SpreadsheetView tests pass

\---\* Tests don't require full tkinter main loop

*   Cell state transitions verified

## Phase 5: User Story 7 - Preserve Deferred Save Behavior (P1)\* Edge cases tested (invalid row\_index)

**Story**: The Excel file is only saved to disk once all sheets and all questions have been processed, not incrementally.**Estimated Time**: 1.5 hours

**Independent Test**: Process multi-sheet file, check disk timestamp during processing, verify it only changes after completion.**Dependencies**: T012, T013

**Tasks**:---

### T031: \[P\] Write test for deferred save behavior## Phase 4: User Story 4 - Process All Sheets Sequentially (P1)

**File**: `tests/integration/test_excel_workflow.py`

**Story**: \[US7\] ### T015 - Implement WorkbookView Class

**Description**: Verify file not saved until WORKBOOK\_COMPLETE.

**Definition of Done**:**Description**: Create tkinter Notebook-based multi-sheet view.

Copy test Excel file to temp location

Record original mtime**Story**: US4

Start processing (pause after sheet 1 completes)

Verify file mtime unchanged**Steps**:

Resume processing to completion

Verify file mtime changed after WORKBOOK\_COMPLETE1. Create `src/ui/workbook_view.py`

1.  Implement WorkbookView class with **init**(parent, workbook\_data, ui\_update\_queue)

### T032: Add save call to ExcelProcessor.process\_workbook()3. Implement render() method creating ttk.Notebook

**File**: `src/excel/processor.py` 4. Create one SpreadsheetView per sheet in separate frames

**Story**: \[US7\] 5. Add all frames as Notebook tabs with sheet names

**Description**: Call ExcelLoader.save\_workbook() only after all sheets done. 6. Bind `<<NotebookTabChanged>>` event to handle\_user\_tab\_click()

**Definition of Done**:7. Initialize NavigationState

After processing all sheets

After emitting WORKBOOK\_COMPLETE event**Acceptance Criteria**:

Call loader.save\_workbook(workbook\_data)

Handle IOError with error event\* Notebook renders with one tab per sheet

Test from T031 passes\* Each tab contains a SpreadsheetView

*   Tab names match sheet names from workbook\_data

### T033: \[P\] Write test for no save on interruption\* Tab click event bound correctly

**File**: `tests/integration/test_excel_workflow.py` \* render() returns configured Notebook widget

**Story**: \[US7\]

**Description**: Verify file unchanged if processing cancelled. **Estimated Time**: 2 hours

**Definition of Done**:

Start processing**Dependencies**: T012, T006

Cancel after 50% complete (simulate user exit)

Verify file mtime unchanged---

Verify no partial data in file (reload and check)

### T016 - Implement WorkbookView Navigation Methods \[P\]

### T034: Add interruption handler to UIManager

**File**: `src/ui/main_window.py` **Description**: Add sheet navigation and tab indicator methods.

**Story**: \[US7\]

**Description**: Handle window close during processing - don't save. **Story**: US4, US5, US6

**Definition of Done**:

Override window close event (WM\_DELETE\_WINDOW)**Steps**:

If processing active: confirm cancellation

Stop ExcelProcessor (cancellation token)1. Add navigate\_to\_sheet(sheet\_index) method to WorkbookView

Cleanup agents via agent\_coordinator2. Check NavigationState.auto\_navigation\_enabled before navigating

Do NOT call save\_workbook()3. Use notebook.select(sheet\_index) to switch tabs

Test from T033 passes4. Add update\_tab\_indicator(sheet\_index, is\_processing) method

1.  Update tab text with spinner character (⟳) when processing

**Acceptance Test** (User Story 7):6. Implement handle\_user\_tab\_click() to lock navigation

Import 2-sheet Excel file

Start processing**Acceptance Criteria**:

After Sheet 1 complete, check file mtime (unchanged)

Let processing complete\* navigate\_to\_sheet() switches tabs when auto-navigation enabled

After WORKBOOK\_COMPLETE, check file mtime (changed)\* navigate\_to\_sheet() does nothing when user has locked navigation

Open saved file, verify all answers present\* update\_tab\_indicator() adds/removes spinner from tab text

*   handle\_user\_tab\_click() calls NavigationState.lock\_to\_sheet()

**Checkpoint**: Deferred save guarantee implemented\* Logging indicates navigation state changes

\---**Estimated Time**: 1 hour

## Phase 6: User Story 2 - Show In-Progress Status for Active Questions (P2)**Dependencies**: T015

**Story**: As the agent processes each question, the user sees the current question's cell highlighted in pink with "Working..." indicator.---

**Independent Test**: Start processing, observe currently active cell turns pink with "Working..." text.### T017 - Implement WorkbookView UI Update Polling \[P\]

**Tasks**:**Description**: Add queue polling for background thread events.

### T035: \[P\] Write test for cell state updates**Story**: US2, US3, US4, US5

**File**: `tests/unit/test_ui_components.py`

**Story**: \[US2\] **Steps**:

**Description**: Test SpreadsheetView updates cell visual state.

**Definition of Done**:1. Add start\_update\_polling() method to WorkbookView

Test update\_cell(row, WORKING)2. Implement \_poll\_queue() method with try/except queue.Empty

Verify cell background pink (#FFB6C1)3. Process events via \_process\_event(event)

Verify cell text "Working..."4. Schedule next poll with root.after(50ms)

Test update\_cell(row, COMPLETED, "Answer")5. Handle event types: SHEET\_START, CELL\_WORKING, CELL\_COMPLETED, SHEET\_COMPLETE, ERROR

Verify cell background light green (#90EE90)6. Dispatch to appropriate methods (navigate, update\_cell, update\_tab\_indicator)

Verify cell text shows answer

**Acceptance Criteria**:

### T036: Implement SpreadsheetView.update\_cell()

**File**: `src/ui/spreadsheet_view.py` \* Polling starts on start\_update\_polling() call

**Story**: \[US2\] \* Polls every 50ms without blocking

**Description**: Update visual state of a single cell based on CellState. \* All event types handled correctly

**Definition of Done**:\* Events trigger UI updates on correct sheets/cells

Configure Treeview tags: 'working', 'completed', 'pending'\* Errors logged appropriately

Tag 'working': background=#FFB6C1

Tag 'completed': background=#90EE90**Estimated Time**: 1.5 hours

update\_cell() changes item values and tags

For WORKING: values=(question, "Working..."), tags=('working',)**Dependencies**: T015, T016, T007

For COMPLETED: values=(question, answer), tags=('completed',)

Test from T035 passes---

### T037: Add CELL\_WORKING event emission to ExcelProcessor### T018 - Create Unit Tests for WorkbookView \[P\]

**File**: `src/excel/processor.py`

**Story**: \[US2\] **Description**: Test WorkbookView multi-sheet rendering and navigation.

**Description**: Emit CELL\_WORKING event before processing each question.

**Definition of Done**:**Story**: US4, US6

Before agent\_coordinator.process\_question()

Create UIUpdateEvent(CELL\_WORKING, {sheet\_index, row\_index})**Steps**:

Put event in ui\_update\_queue

Integration test verifies event fired1. Add WorkbookView tests to `tests/unit/test_ui_components.py`

1.  Test render() creates Notebook with all sheets

### T038: Handle CELL\_WORKING events in WorkbookView3. Test navigate\_to\_sheet() with auto-navigation enabled/disabled

**File**: `src/ui/workbook_view.py` 4. Test update\_tab\_indicator() adds/removes spinner

**Story**: \[US2\] 5. Test handle\_user\_tab\_click() locks navigation

**Description**: Process CELL\_WORKING events in update polling loop. 6. Test \_process\_event() handles all event types

**Definition of Done**:

In start\_update\_polling() event handler**Acceptance Criteria**:

Extract sheet\_index, row\_index from event payload

Call sheet\_views\[sheet\_index\].update\_cell(row\_index, WORKING)\* All WorkbookView tests pass

Update sheet\_data.cell\_states\[row\_index\] = WORKING\* Navigation state correctly managed

Unit test verifies cell updates\* Tab indicators update as expected

*   Event processing verified for all types

**Acceptance Test** (User Story 2):

Import 5-question Excel file**Estimated Time**: 2 hours

Start processing

Verify first cell turns pink with "Working..."**Dependencies**: T015, T016, T017

Verify only one cell pink at a time

When processing moves to question 2, verify question 1 still pink (until completed)---

**Checkpoint**: In-progress status indicators working### T019 - Implement ExcelProcessor Class

\---**Description**: Orchestrate multi-sheet processing with agent workflow.

## Phase 7: User Story 3 - Display Completed Answers with Visual Confirmation (P2)**Story**: US4

**Story**: When the agent completes answering a question, the response text appears in the cell and the background changes to light green.**Steps**:

**Independent Test**: Allow agent to complete one question, verify cell turns green with answer text.1. Create `src/excel/processor.py`

1.  Implement ExcelProcessor class with **init**(agent\_coordinator, ui\_update\_queue)

**Tasks**:3. Implement async process\_workbook(workbook\_data, context, char\_limit, max\_retries)

1.  Loop through all sheets sequentially

### T039: Add CELL\_COMPLETED event emission to ExcelProcessor5. Emit SHEET\_START event for each sheet

**File**: `src/excel/processor.py` 6. Process questions via agent\_coordinator.process\_question()

**Story**: \[US3\] 7. Emit CELL\_WORKING before each question, CELL\_COMPLETED after

**Description**: Emit CELL\_COMPLETED event after each question processed. 8. Emit SHEET\_COMPLETE after each sheet, WORKBOOK\_COMPLETE at end

**Definition of Done**:9. Track statistics (processed, failed, time)

After agent\_coordinator.process\_question() returns

Extract answer from ProcessingResult**Acceptance Criteria**:

Create UIUpdateEvent(CELL\_COMPLETED, {sheet\_index, row\_index, answer})

Put event in ui\_update\_queue\* Processes all sheets in workbook sequentially

Integration test verifies event with answer\* Emits correct UIUpdateEvents at each stage

*   Integrates with existing AgentCoordinator

### T040: Handle CELL\_COMPLETED events in WorkbookView\* Returns ExcelProcessingResult with statistics

**File**: `src/ui/workbook_view.py` \* Handles errors gracefully, continues processing remaining questions

**Story**: \[US3\]

**Description**: Process CELL\_COMPLETED events in update polling loop. **Estimated Time**: 2.5 hours

**Definition of Done**:

In start\_update\_polling() event handler**Dependencies**: T005, T007

Extract sheet\_index, row\_index, answer from payload

Call sheet\_views\[sheet\_index\].update\_cell(row\_index, COMPLETED, answer)---

Update sheet\_data.answers\[row\_index\] = answer

Update sheet\_data.cell\_states\[row\_index\] = COMPLETED### T020 - Create Integration Test for Excel Workflow \[P\]

Update workbook\_data.completed\_questions += 1

Unit test verifies updates**Description**: End-to-end test with mock agents processing multi-sheet Excel.

### T041: \[P\] Write integration test for complete workflow**Story**: US4

**File**: `tests/integration/test_excel_workflow.py`

**Story**: \[US3\] **Steps**:

**Description**: End-to-end test with mock agents producing answers.

**Definition of Done**:1. Create `tests/integration/test_excel_workflow.py`

Load single\_sheet\_5\_questions.xlsx2. Create MockAgentCoordinator returning mock answers

Start processing with mock agents returning answers3. Load multi-sheet test fixture

Verify all cells transition: PENDING → WORKING → COMPLETED4. Run ExcelProcessor.process\_workbook() with mock coordinator

Verify all answers appear in cells5. Verify all UIUpdateEvents emitted in correct order

Verify all cells light green at end6. Verify all questions processed across all sheets

1.  Verify statistics in result (processed count, time)

**Acceptance Test** (User Story 3):

Import 8-question Excel file**Acceptance Criteria**:

Start processing

When first question completes, verify:\* Integration test passes with mock agents

Cell background light green\* All sheets processed in order

"Working..." replaced with actual answer\* All expected events emitted

Let 3 questions complete\* Statistics correct

Verify first 3 cells light green with answers\* Test completes in \<5 seconds

Verify 4th cell pink "Working..."

Verify cells 5-8 white (pending)**Estimated Time**: 2 hours

**Checkpoint**: Complete answer display working**Dependencies**: T019, T010

---

## Phase 8: User Story 5 - Visual Sheet Status Indicators (P2)## Phase 5: User Story 7 - Preserve Deferred Save (P1)

**Story**: Sheet tabs display visual indicators showing processing status - currently active sheet shows a spinning spinner icon.### T021 - Implement ExcelLoader.save\_workbook()

**Independent Test**: Import multi-sheet file, observe current sheet tab has spinner icon.**Description**: Save all answers back to Excel file after processing.

**Tasks**:**Story**: US7

### T042: Implement WorkbookView.update\_tab\_indicator()**Steps**:

**File**: `src/ui/workbook_view.py`

**Story**: \[US5\] 1. Add save\_workbook(workbook\_data) method to ExcelLoader

**Description**: Add or remove spinner from tab text. 2. Re-open Excel file with openpyxl

**Definition of Done**:3. Iterate through workbook\_data.sheets

For is\_processing=True: append " ⟳" to tab text4. Write answers to column B (row 2+) for each sheet

For is\_processing=False: remove " ⟳" from tab text5. Save workbook with wb.save(file\_path)

Use notebook\_widget.tab(index, text=new\_text)6. Handle errors (file locked, format changed, IO errors)

Unit test verifies text updates

**Acceptance Criteria**:

### T043: Call update\_tab\_indicator from event handlers

**File**: `src/ui/workbook_view.py` \* Saves answers to correct cells (column B)

**Story**: \[US5\] \* Preserves Excel formatting and formulas

**Description**: Update tab indicators when SHEET\_START/SHEET\_COMPLETE events processed. \* All sheets updated in single save operation

**Definition of Done**:\* Raises IOError or ExcelFormatError on failures

On SHEET\_START: call update\_tab\_indicator(sheet\_index, True)\* Original file modified only on successful save

On SHEET\_COMPLETE: call update\_tab\_indicator(sheet\_index, False)

Integration test verifies spinner appears and disappears**Estimated Time**: 1 hour

**Acceptance Test** (User Story 5):**Dependencies**: T009

Import 3-sheet Excel file

Start processing---

Verify Sheet 1 tab shows "Sheet1 ⟳"

When Sheet 1 completes, verify spinner removed### T022 - Add Save Tests to ExcelLoader Unit Tests \[P\]

Verify Sheet 2 tab shows "Sheet2 ⟳"

Continue through all sheets**Description**: Test saving answers back to Excel files.

Verify only active sheet has spinner at any time

**Story**: US7

**Checkpoint**: Sheet status indicators working

**Steps**:

---

1.  Update `tests/unit/test_excel_loader.py`

## Phase 9: User Story 6 - Respect User Sheet Navigation (P2)2. Test save\_workbook() writes answers to column B

1.  Test re-loading saved file shows answers

**Story**: When a user manually clicks a sheet tab, the view remains on that user-selected sheet even as the agent continues processing other sheets.4. Test save preserves formatting

1.  Test error handling (file locked, invalid path)

**Independent Test**: Start processing 3-sheet file, wait for Sheet 2 to start, click Sheet 1 tab, verify view stays on Sheet 1.6. Test multi-sheet save updates all sheets

**Tasks**:**Acceptance Criteria**:

### T044: Implement WorkbookView.handle\_user\_tab\_click()\* All save tests pass

**File**: `src/ui/workbook_view.py` \* Saved files loadable and contain correct answers

**Story**: \[US6\] \* Formatting preserved (verify with openpyxl)

**Description**: Handle \<> event to lock navigation. \* Error cases handled gracefully

**Definition of Done**:

Bind \<> event in render()**Estimated Time**: 1 hour

In handler: get selected tab index

Call navigation\_state.lock\_to\_sheet(selected\_index)**Dependencies**: T021, T011

Unit test verifies navigation locked after click

---

### T045: \[P\] Write integration test for navigation lock

**File**: `tests/integration/test_excel_workflow.py` ### T023 - Add Deferred Save to Integration Test \[P\]

**Story**: \[US6\]

**Description**: Verify user tab click prevents auto-navigation. **Description**: Verify file only saved after complete processing.

**Definition of Done**:

Start processing 3-sheet file**Story**: US7

After Sheet 1 starts, simulate user clicking Sheet 3 tab

Verify view switches to Sheet 3**Steps**:

Continue processing Sheet 1 and Sheet 2

Verify view stays on Sheet 3 (does not auto-navigate)1. Update `tests/integration/test_excel_workflow.py`

Verify processing continues in background2. Check file timestamp before processing

1.  Monitor file timestamp during processing (should not change)

**Acceptance Test** (User Story 6):4. Verify file timestamp changes only after process\_workbook() completes

Import 3-sheet Excel file5. Verify saved file contains all answers

Start processing

When Sheet 2 starts processing, click Sheet 1 tab**Acceptance Criteria**:

Verify view switches to Sheet 1

Verify Sheet 2 processing continues (spinner on Sheet 2 tab)\* File not modified during processing

Verify view remains on Sheet 1 (does not auto-navigate back to Sheet 2)\* File only saved after WORKBOOK\_COMPLETE event

Click Sheet 3 tab\* All answers present in saved file

Verify view switches to Sheet 3

Verify processing continues on Sheet 2**Estimated Time**: 30 minutes

**Checkpoint**: User navigation control working**Dependencies**: T020, T021

---

## Phase 10: Polish & Cross-Cutting Concerns## Phase 6: User Story 2 - Show In-Progress Status (P2)

**Goal**: Address edge cases, error handling, and quality-of-life improvements.### T024 - Verify CELL\_WORKING Event Flow \[P\]

**Tasks**:**Description**: Ensure CELL\_WORKING events correctly trigger pink cells.

### T046: \[P\] Add scrolling support to SpreadsheetView**Story**: US2

**File**: `src/ui/spreadsheet_view.py`

**Description**: Add vertical and horizontal scrollbars for large sheets (FR-009, FR-009a, FR-009b). **Steps**:

**Definition of Done**:

Add ttk.Scrollbar (vertical and horizontal) to render()1. Review ExcelProcessor.\_emit\_event() calls for CELL\_WORKING

Configure Treeview yscrollcommand and xscrollcommand2. Review WorkbookView.\_process\_event() handling for CELL\_WORKING

Render blank cells for sheets with fewer rows than visible area3. Create manual test: start processing, verify pink cells appear

Test with 100-question sheet4. Add integration test verifying CELL\_WORKING events emitted for all questions

### T047: \[P\] Add auto-scroll to active question**Acceptance Criteria**:

**File**: `src/ui/spreadsheet_view.py`

**Description**: Auto-scroll when active question off-screen (FR-009c). \* CELL\_WORKING event emitted before each question processing

**Definition of Done**:\* WorkbookView updates correct cell to WORKING state

In update\_cell(WORKING), check if row visible\* Cell background turns pink (#FFB6C1)

If not visible and user hasn't manually scrolled: scroll to row\* Cell displays "Working..." text

Track user scroll events to disable auto-scroll\* Only one cell pink at a time (sequential processing)

Test auto-scroll behavior

**Estimated Time**: 1 hour

### T048: \[P\] Add sheet name truncation

**File**: `src/ui/workbook_view.py` **Dependencies**: T019, T017, T013

**Description**: Truncate long sheet names in tabs (FR-024a).

**Definition of Done**:---

Measure tab text width

If >150px, truncate with "..." at end### T025 - Add Visual Verification Test \[P\]

Apply to tab text in render()

Test with long sheet names**Description**: Manual test to visually confirm pink "Working..." cells.

### T049: \[P\] Add hidden sheet handling to ExcelLoader**Story**: US2

**File**: `src/excel/loader.py`

**Description**: Skip hidden sheets in load, preserve in save (FR-023, FR-023a). **Steps**:

**Definition of Done**:

In load\_workbook(), check worksheet.sheet\_state1. Create `tests/manual/test_visual_feedback.md` with instructions

Only process sheets where sheet\_state == 'visible'2. Document steps: Import multi-sheet Excel, start processing

In save\_workbook(), write to original workbook (preserves hidden sheets)3. Document expected: Each cell turns pink with "Working..." before answer appears

Test with hidden\_sheets.xlsx fixture4. Document verification: Screenshot showing pink cell during processing

1.  Perform manual test and capture screenshot

### T050: \[P\] Add column detection via AI model

**File**: `src/excel/column_detector.py` **Acceptance Criteria**:

**Description**: Use Azure AI to detect question/answer columns from headers (FR-020, FR-020a, FR-020b, FR-020c).

**Definition of Done**:\* Manual test document created

New ColumnDetector class\* Test performed successfully

analyze\_headers(sheet) method calls Azure AI model\* Screenshot shows pink cell with "Working..." text

Returns ColumnMapping(question\_col, answer\_col, doc\_col)\* Visual feedback matches spec (pink #FFB6C1)

Determines if sheet is questionnaire (has question + answer columns)

Integration with ExcelLoader to use detected columns**Estimated Time**: 30 minutes

Test with non-standard column layouts

**Dependencies**: T024

### T051: \[P\] Add AgentCleanupManager

**File**: `src/agents/cleanup_manager.py` ---

**Description**: Handle agent deletion on user exit (FR-021, FR-021a).

**Definition of Done**:## Phase 7: User Story 3 - Display Completed Answers (P2)

AgentCleanupManager class

cleanup\_all\_agents() method deletes agents from Azure AI Foundry### T026 - Verify CELL\_COMPLETED Event Flow \[P\]

Integration with UIManager window close handler

Test verifies agents deleted on exit**Description**: Ensure CELL\_COMPLETED events correctly trigger green cells with answers.

### T052: \[P\] Add file replacement handling**Story**: US3

**File**: `src/excel/processor.py`

**Description**: Support importing new file during active processing (FR-022). **Steps**:

**Definition of Done**:

Add cancellation token to process\_workbook()1. Review ExcelProcessor.\_emit\_event() calls for CELL\_COMPLETED

Stop processing when cancel() called2. Review WorkbookView.\_process\_event() handling for CELL\_COMPLETED

UIManager detects Import click during processing3. Verify answer text passed in payload

Stops current processor, starts new one4. Create integration test verifying CELL\_COMPLETED events include answers

Test file replacement workflow5. Add manual test verifying green cells with answer text

### T053: \[P\] Add merged cell rendering**Acceptance Criteria**:

**File**: `src/ui/spreadsheet_view.py`

**Description**: Render merged cells spanning multiple rows/columns (FR-010b). \* CELL\_COMPLETED event emitted after each question completes

**Definition of Done**:\* Event payload includes answer text

Detect merged cells from openpyxl\* WorkbookView updates cell to COMPLETED state with answer

Calculate span in Treeview (may require custom rendering)\* Cell background turns light green (#90EE90)

Test with fixture containing merged cells\* Cell displays actual answer text (not "Working...")

Note: Full merged cell support may be limited by Treeview

**Estimated Time**: 1 hour

### T054: \[P\] Add comprehensive error handling

**File**: `src/excel/processor.py`, `src/ui/workbook_view.py` **Dependencies**: T019, T017, T013

**Description**: Handle and display agent failures, Excel errors.

**Definition of Done**:---

Emit ERROR events for all exception types

Handle ERROR events in WorkbookView### T027 - Test Long Answer Text Handling \[P\]

Display error dialogs via UIManager.display\_error()

Test error scenarios (agent failure, file write error, etc.)**Description**: Verify long answers display correctly in cells.

### T055: \[P\] Add performance monitoring**Story**: US3

**File**: `tests/integration/test_excel_workflow.py`

**Description**: Verify performance targets from success criteria. **Steps**:

**Definition of Done**:

Test spreadsheet render time \< 2s for 100 questions1. Create test with mock agent returning 500+ character answer

Test cell update time \< 500ms from event to visual2. Process question and verify answer appears in cell

Test tab navigation time \< 200ms3. Check Treeview column width handles long text

Test with maximum scale (10 sheets × 100 questions)4. Verify scrolling works for long text

1.  Document any truncation or wrapping behavior

### T056: \[P\] Write end-to-end integration test

**File**: `tests/integration/test_excel_workflow.py` **Acceptance Criteria**:

**Description**: Complete workflow test with real Excel files and mock agents.

**Definition of Done**:\* Long answers (500+ chars) display in cells

Load multi-sheet Excel file\* No text truncation or overflow

Process all questions with mock agents\* Treeview remains responsive

Verify all UI updates occur correctly\* Scrollbar functional for viewing full text

Verify final Excel file saved with all answers

Test covers all user stories**Estimated Time**: 45 minutes

### T057: \[P\] Update documentation**Dependencies**: T026, T013

**File**: `README.md`, `specs/002-live-excel-processing/quickstart.md`

**Description**: Document new Excel import feature for users and developers. ---

**Definition of Done**:

User guide: How to import Excel files## Phase 8: User Story 5 - Visual Sheet Status Indicators (P2)

Developer guide: How to run tests, architecture overview

Known limitations documented### T028 - Verify Tab Spinner Display \[P\]

**Checkpoint**: Feature complete and polished**Description**: Ensure spinner appears on processing sheet tabs.

\---**Story**: US5

## Task Dependencies**Steps**:

### Dependency Graph by User Story1. Review WorkbookView.update\_tab\_indicator() implementation

1.  Verify SHEET\_START event triggers update\_tab\_indicator(idx, True)

```

Phase 1 (Setup)4.  Create manual test showing spinner on active sheet tab

  ↓5.  Verify Unicode spinner character (⟳) displays correctly

Phase 2 (Foundational - BLOCKS ALL)

  ↓**Acceptance Criteria**:

  ├─→ Phase 3 (US1 - View Spreadsheet) ─→ MVP Complete

  ↓*   Spinner appears on tab when sheet processing starts

  ├─→ Phase 4 (US4 - Multi-sheet Processing)*   Spinner disappears when sheet completes

  ↓*   Only one spinner visible at a time

  ├─→ Phase 5 (US7 - Deferred Save)*   Spinner character renders correctly (⟳ U+27F3)

  ↓

  ├─→ Phase 6 (US2 - In-Progress Status) ─┐**Estimated Time**: 45 minutes

  ├─→ Phase 7 (US3 - Completed Status) ───┼─→ Core Processing Complete

  ├─→ Phase 8 (US5 - Sheet Indicators) ───┘**Dependencies**: T016, T017

  ↓

  ├─→ Phase 9 (US6 - User Navigation)---

  ↓

Phase 10 (Polish)### T029 - Test Spinner Across All Sheets \[P\]
```

**Description**: Verify spinner transitions correctly through multi-sheet processing.

### Critical Path

**Story**: US5

1.  Setup (Phase 1) → 2. Foundational (Phase 2) → 3. US1 (Phase 3) → 4. US4 (Phase 4) → 5. US2 (Phase 6) → 6. US3 (Phase 7) → 7. Polish (Phase 10)

**Steps**:

### Parallel Execution Opportunities

1.  Use 3-sheet test fixture

**Within Phase 1**: T001, T002, T003, T004 can run in parallel (4 tasks)2. Start processing and monitor tab indicators

1.  Verify spinner moves from Sheet 1 → Sheet 2 → Sheet 3

**Within Phase 2**: T008, T010, T013 can run in parallel after their prerequisites (3 tasks)4. Verify no spinner on Sheet 1 after it completes

1.  Document expected behavior in manual test

**Within Phase 3**: T016, T019, T021, T023 can run in parallel after T017 (4 tasks)

**Acceptance Criteria**:

**Within Phase 10**: All polish tasks (T046-T057) can run in parallel (12 tasks)

*   Spinner appears on Sheet 1 first

**Total Parallelizable**: 23 tasks out of 57 (40%)\* Spinner moves to Sheet 2 after Sheet 1 completes

*   Spinner moves to Sheet 3 after Sheet 2 completes

\---\* No spinner on completed sheets

## Testing Strategy**Estimated Time**: 30 minutes

### Test-Driven Development (TDD) Approach**Dependencies**: T028

Per constitution requirement, tests are written BEFORE implementation:---

Each phase includes test tasks before implementation tasks

Unit tests for all data structures and classes## Phase 9: User Story 6 - Respect User Navigation (P2)

Integration tests for complete workflows

Mock Azure services for testing without live credentials### T030 - Test User Tab Click Behavior \[P\]

### Test Categories**Description**: Verify user clicking tab disables auto-navigation.

**Unit Tests** (15 tasks):**Story**: US6

Data types validation

Excel loader round-trip**Steps**:

UI component rendering

State transitions1. Review WorkbookView.handle\_user\_tab\_click() implementation

Create integration test simulating tab click event

**Integration Tests** (8 tasks):3. Verify NavigationState.lock\_to\_sheet() called

Complete Excel workflow4. Verify subsequent navigate\_to\_sheet() calls do nothing

Multi-sheet processing5. Create manual test: click Sheet 1 tab during Sheet 2 processing

UI update synchronization

Navigation and locking**Acceptance Criteria**:

**Mock Tests**:\* User clicking tab calls lock\_to\_sheet()

MockAgentCoordinator for Azure-free testing\* Auto-navigation disabled after user click

Mock UIUpdateQueue for UI testing\* View remains on user-selected sheet

Mock Excel files in fixtures/\* Processing continues in background (verified by completed cells)

**Performance Tests** (1 task):**Estimated Time**: 1 hour

Response time validation

Scale testing (1000 questions)**Dependencies**: T016, T017, T006

### Test Coverage Goals---

**Data Types**: 100% coverage### T031 - Test Navigation Lock Persistence \[P\]

**Excel Loader**: 100% coverage

**UI Components**: >90% coverage (excluding tkinter internals)**Description**: Verify navigation remains locked across multiple sheet transitions.

**Integration**: All user stories covered

**Story**: US6

---

**Steps**:

## Definition of Done (Feature-Level)

1.  Start processing 3-sheet workbook

The Live Excel Processing Visualization feature is complete when:2. Click Sheet 1 tab during Sheet 1 processing

1.  Wait for Sheet 2 to start (verify spinner appears on Sheet 2 tab)

✅ All 57 tasks completed and checked in 4. Verify view still shows Sheet 1 (not auto-navigated)

✅ All 7 user stories independently testable and passing 5. Verify Sheet 3 start also doesn't trigger navigation

✅ All unit tests passing (>95% coverage)

✅ All integration tests passing **Acceptance Criteria**:

✅ Performance criteria met (SC-001 through SC-011)

✅ Constitution compliance verified (TDD, resource management, Azure integration) \* User click locks navigation permanently

✅ Documentation updated (README, quickstart) \* View stays on user-selected sheet through all transitions

✅ Code reviewed and approved \* Background processing completes successfully

✅ Feature branch merged to main\* All sheets show completed answers (verified by checking data)

\---**Estimated Time**: 45 minutes

## Risk Mitigation**Dependencies**: T030

**Risk**: Treeview widget limitations for merged cells ---

**Mitigation**: Document limitation, implement best-effort rendering, defer advanced merging to future enhancement

## Phase 10: UI Integration with UIManager

**Risk**: Performance degradation with >100 questions per sheet

**Mitigation**: Performance tests in Phase 10 validate targets, add virtual scrolling if needed### T032 - Add WorkbookView Integration to UIManager

**Risk**: Thread synchronization issues with UI updates **Description**: Integrate WorkbookView into existing UIManager.

**Mitigation**: Strict adherence to `root.after()` pattern, comprehensive threading tests

**Story**: US1, US4

**Risk**: Excel file corruption on unexpected crashes

**Mitigation**: Deferred save pattern ensures original file untouched, no partial writes**Steps**:

\---1. Open `src/ui/main_window.py`

1.  Add imports: ExcelLoader, ExcelProcessor, WorkbookView, queue

## Future Enhancements (Post-MVP)3. Modify \_process\_excel\_internal() to:

```
*   Load workbook via ExcelLoader
```

Not included in current task breakdown: \* Create ui\_update\_queue

```
*   Call \_show\_workbook\_view() on main thread
```

**Pause/Resume Processing**: Allow users to pause and resume workflows \* Start ExcelProcessor

**Cell Tooltips**: Show full answer on hover for long text \* Save workbook on completion

**Progress Bar Overlay**: Global progress indicator across all sheets4. Implement \_show\_workbook\_view(workbook\_data, ui\_queue):

**Export Intermediate Results**: Save progress to separate file \* Hide current answer\_display

**Re-process Individual Questions**: Select and rerun specific cells \* Create WorkbookView

**Advanced Formatting**: Full merged cell support, custom fonts, borders \* Pack Notebook widget

*   Start update polling

These would require additional tasks and phases but follow the established patterns.

**Acceptance Criteria**:

---

*   Import Excel button triggers new workflow

**Next Step**: Begin implementation with Phase 1 (Setup) tasks T001-T004, executed in parallel where marked \[P\].\* answer\_display replaced with WorkbookView

*   Processing starts and UI updates in real-time
*   Workbook saved at end
*   No UI thread errors

**Estimated Time**: 2 hours

**Dependencies**: T015, T019, T021

---

### T033 - Handle UI Cleanup and Error States \[P\]

**Description**: Add proper cleanup when processing completes or errors.

**Story**: US1, US4, US7

**Steps**:

1.  Add \_restore\_answer\_display() method to UIManager
2.  Call from \_process\_excel\_internal() on success/error
3.  Remove WorkbookView, re-show answer\_display
4.  Display success message with statistics
5.  Handle ERROR events in WorkbookView with error dialogs
6.  Ensure resources cleaned up on window close

**Acceptance Criteria**:

*   WorkbookView removed after processing
*   answer\_display restored
*   Success message shows statistics
*   Error events trigger error dialogs
*   No resource leaks on close

**Estimated Time**: 1.5 hours

**Dependencies**: T032

---

### T034 - Create End-to-End Manual Test \[P\]

**Description**: Complete manual test with real Azure agents.

**Story**: All user stories

**Steps**:

1.  Create `tests/manual/test_end_to_end.md`
2.  Document setup: Real Azure credentials, test Excel file
3.  Document steps: Import Excel, verify UI updates, check saved file
4.  Perform test with 2-sheet, 5-question-each file
5.  Verify all acceptance criteria from spec.md

**Acceptance Criteria**:

*   Manual test document created
*   Test performed with real agents
*   All spec.md acceptance criteria verified
*   Screenshots captured for documentation

**Estimated Time**: 1 hour

**Dependencies**: T032, T033

---

## Phase 11: Testing & Polish

### T035 - Run All Unit Tests and Fix Failures \[P\]

**Description**: Execute full unit test suite and resolve any issues.

**Story**: All

**Steps**:

1.  Run `pytest tests/unit/ -v`
2.  Identify any failing tests
3.  Fix implementation or test issues
4.  Rerun until all pass
5.  Verify coverage for new modules

**Acceptance Criteria**:

*   All unit tests pass
*   No skipped tests (unless documented reason)
*   Coverage >80% for new modules

**Estimated Time**: 2 hours

**Dependencies**: All previous unit test tasks

---

### T036 - Run All Integration Tests and Fix Failures \[P\]

**Description**: Execute integration test suite and resolve issues.

**Story**: All

**Steps**:

1.  Run `pytest tests/integration/ -v`
2.  Identify any failing tests
3.  Fix implementation or test issues
4.  Verify mock agent integration
5.  Rerun until all pass

**Acceptance Criteria**:

*   All integration tests pass
*   Tests complete in \<30 seconds
*   Mock agents work correctly

**Estimated Time**: 1.5 hours

**Dependencies**: All previous integration test tasks

---

### T037 - Perform Accessibility and UX Review \[P\]

**Description**: Review UI for accessibility and user experience.

**Story**: US1, US2, US3, US5

**Steps**:

1.  Test with high-DPI display (verify scaling)
2.  Test with low-resolution display (1024x768 minimum)
3.  Verify color contrast (pink, green) for accessibility
4.  Test keyboard navigation (tab through widgets)
5.  Verify scrolling performance with 100 rows
6.  Document any UX issues

**Acceptance Criteria**:

*   UI readable on 1024x768 display
*   Colors distinguishable (WCAG AA compliant if possible)
*   Keyboard navigation functional
*   Scrolling smooth with 100 rows
*   No UX blockers identified

**Estimated Time**: 1 hour

**Dependencies**: T032

---

### T038 - Update Documentation (README, etc.) \[P\]

**Description**: Update project documentation with new feature.

**Story**: All

**Steps**:

1.  Update main README.md with "Live Excel Processing" feature description
2.  Add screenshots showing spreadsheet view
3.  Document Import Excel workflow
4.  Update requirements.txt if any dependencies changed (should not)
5.  Add CHANGES\_SUMMARY.md entry for this feature

**Acceptance Criteria**:

*   README.md describes new feature
*   Screenshots included
*   Workflow documented clearly
*   CHANGES\_SUMMARY.md updated

**Estimated Time**: 45 minutes

**Dependencies**: T032, T034

---

### T039 - Performance Testing with Large Workbooks \[P\]

**Description**: Test performance with maximum supported load.

**Story**: All (performance validation)

**Steps**:

1.  Create test Excel with 10 sheets, 100 questions each (1000 total)
2.  Run with mock agents (fast responses)
3.  Measure render time (\<2s target)
4.  Measure cell update time (\<500ms target)
5.  Measure tab navigation time (\<200ms target)
6.  Document results and any performance issues

**Acceptance Criteria**:

*   Initial render \<2s for 100 rows
*   Cell updates \<500ms
*   Tab navigation \<200ms
*   Memory usage \<10MB overhead
*   No UI freezing or lag

**Estimated Time**: 1.5 hours

**Dependencies**: T032

---

### T040 - Create Feature Demo Video \[P\]

**Description**: Record short demo video showing feature in action.

**Story**: All

**Steps**:

1.  Set up screen recording software
2.  Prepare 2-sheet Excel file with 5 questions each
3.  Record: Import Excel → Watch cells turn pink/green → Final save
4.  Show tab navigation and spinner indicators
5.  Save video to docs/ folder
6.  Add link to README.md

**Acceptance Criteria**:

*   Video \<2 minutes
*   Shows complete workflow start to finish
*   Clearly demonstrates visual feedback
*   Saved in accessible format (MP4)

**Estimated Time**: 45 minutes

**Dependencies**: T032, T034

---

## Phase 12: Final Review & Merge

### T041 - Code Review Preparation

**Description**: Prepare feature branch for code review.

**Story**: All

**Steps**:

1.  Review all code for style consistency
2.  Run ruff linter: `ruff check src/ tests/`
3.  Fix any linting issues
4.  Review all docstrings for completeness
5.  Ensure no debug prints or commented code
6.  Run all tests one final time

**Acceptance Criteria**:

*   No linting errors
*   All docstrings present
*   All tests pass
*   Code follows project conventions

**Estimated Time**: 1 hour

**Dependencies**: All previous tasks

---

### T042 - Create Pull Request

**Description**: Create PR for feature branch.

**Story**: All

**Steps**:

1.  Push final commits to `002-live-excel-processing` branch
2.  Create PR on GitHub
3.  Reference spec.md in PR description
4.  List all user stories implemented
5.  Attach screenshots and demo video
6.  Request review from team

**Acceptance Criteria**:

*   PR created with detailed description
*   All commits pushed
*   CI/CD pipeline passes (if configured)
*   Reviewers assigned

**Estimated Time**: 30 minutes

**Dependencies**: T041

---

## Task Summary

**Total Tasks**: 42  
**Estimated Total Time**: 44.5 hours

### Breakdown by Phase:

*   Phase 1 (Setup): 25 min
*   Phase 2 (Data Structures): 3 hours
*   Phase 3 (US1): 6.5 hours
*   Phase 4 (US4): 10 hours
*   Phase 5 (US7): 2.5 hours
*   Phase 6 (US2): 1.5 hours
*   Phase 7 (US3): 1.75 hours
*   Phase 8 (US5): 1.25 hours
*   Phase 9 (US6): 1.75 hours
*   Phase 10 (Integration): 4.5 hours
*   Phase 11 (Testing & Polish): 7 hours
*   Phase 12 (Final Review): 1.5 hours

### Parallelization Opportunities:

**Can work in parallel after Phase 2 complete**:

*   T009-T011 (ExcelLoader) + T012-T014 (SpreadsheetView)
*   T015-T018 (WorkbookView) + T019-T020 (ExcelProcessor)

**Can work in parallel after Phase 5 complete**:

*   T024-T025 (US2) + T026-T027 (US3) + T028-T029 (US5) + T030-T031 (US6)

**Can work in parallel after Phase 10 complete**:

*   T035-T040 (all testing and polish tasks)

---

## Dependency Graph

```
T001 → T003 → T004 → T005 → T009 → T021
                           ↘        ↗
                             T011 → T022
       ↓
     T006 → T015 → T016 → T017 → T018
             ↓
           T032 → T033 → T034
             ↓
     [All US2-US6 tasks] → T035 → T041 → T042
                       ↘
                         T036 → T037 → T038 → T039 → T040
```

---

## Risk Mitigation Tasks

### High-Risk Areas:

1.  **UI Threading** (T017, T032): Test thoroughly with asyncio integration
2.  **Performance** (T039): May need optimization if targets not met
3.  **Excel Format Handling** (T009, T021): Need robust error handling

### Mitigation Strategies:

*   Test threading patterns early (T008, T014)
*   Profile performance continuously during development
*   Use diverse Excel test fixtures (T010)

---

## Success Metrics

### Definition of Done:

*   All 42 tasks completed
*   All unit tests passing (>80% coverage)
*   All integration tests passing
*   Manual tests performed and documented
*   Performance targets met (T039)
*   Code review approved
*   PR merged to main branch

### Verification:

Run the following to verify completion:

```
# All tests pass
pytest tests/ -v

# No linting errors
ruff check src/ tests/

# Performance test
pytest tests/integration/test_excel_workflow.py -v -k "performance"
```

---

## Notes

*   **Mock Mode**: All tasks should work with mock agents (no Azure required)
*   **Incremental Testing**: Test after each phase, not just at the end
*   **Documentation**: Update docstrings as you implement, not after
*   **Git Commits**: Commit after each major task (every 2-3 hours of work)

---

**Next Steps**: Start with T001-T002 (setup), then proceed through Phase 2 (foundational data structures). Phase 3-5 implement P1 user stories, Phase 6-9 implement P2 user stories, Phase 10-11 integrate and polish, Phase 12 reviews and merges.