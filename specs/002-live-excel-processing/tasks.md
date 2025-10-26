---
description: "Implementation tasks for Live Excel Processing Visualization feature"
---

# Tasks: Live Excel Processing Visualization

**Input**: Design documents from `/specs/002-live-excel-processing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/module_interfaces.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Excel processing module structure

- [ ] T001 Create Excel processing module structure: `src/excel/__init__.py`, `src/excel/loader.py`, `src/excel/processor.py`
- [ ] T002 [P] Create UI component module structure for spreadsheet rendering: `src/ui/spreadsheet_view.py`, `src/ui/workbook_view.py`
- [ ] T003 [P] Create test fixtures directory: `tests/fixtures/excel/` with sample Excel files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Extend data types in `src/utils/data_types.py` with CellState enum, SheetData, WorkbookData, NavigationState, UIUpdateEvent classes per data-model.md
- [ ] T005 [P] Implement ExcelLoader class in `src/excel/loader.py` with load_workbook() and save_workbook() methods
- [ ] T006 [P] Create UIUpdateQueue wrapper class for thread-safe communication between background processing and UI thread
- [ ] T007 [P] Create test Excel files in `tests/fixtures/excel/`: single_sheet_5_questions.xlsx, multi_sheet_3x10_questions.xlsx, hidden_sheets.xlsx
- [ ] T008 [P] Setup mock Azure services pattern for ExcelProcessor testing in `tests/mock/mock_excel_processing.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Live Spreadsheet in Answer Area (Priority: P1) 🎯 MVP

**Goal**: When a user imports questions from Excel, they see the spreadsheet rendered in the Answer area with all questions visible in a table format

**Independent Test**: Click "Import From Excel", select a spreadsheet file, verify Answer area displays table with all questions

### Implementation for User Story 1

- [x] T009 [P] [US1] Create SpreadsheetView class in `src/ui/spreadsheet_view.py` with Treeview-based rendering for single sheet
- [x] T010 [P] [US1] Create WorkbookView class in `src/ui/workbook_view.py` with Notebook widget for multi-sheet tabs
- [x] T011 [US1] Modify UIManager._on_import_excel_clicked() in `src/ui/main_window.py` to use ExcelLoader and replace answer_display with WorkbookView
- [x] T012 [US1] Add _show_workbook_view() method to UIManager in `src/ui/main_window.py` for thread-safe UI replacement
- [x] T013 [US1] Implement cell state visual rendering in SpreadsheetView: white background for PENDING state, configure Treeview tags
- [x] T014 [US1] Add error handling for invalid Excel files in UIManager with proper error dialogs

**Checkpoint**: At this point, Excel import should display spreadsheet table in Answer area

---

## Phase 4: User Story 4 - Process All Sheets Sequentially (Priority: P1)

**Goal**: When an Excel file contains multiple sheets, the agent processes all sheets one by one in order with automatic view switching

**Independent Test**: Import 3-sheet Excel file, observe agent processes all questions in Sheet 1, then moves to Sheet 2, then Sheet 3

### Implementation for User Story 4

- [x] T015 [P] [US4] Create ExcelProcessor class in `src/excel/processor.py` with process_workbook() method for sequential sheet processing
- [x] T016 [US4] Implement sheet-by-sheet workflow in ExcelProcessor that emits SHEET_START, SHEET_COMPLETE events
- [x] T017 [US4] Modify UIManager._process_excel_internal() in `src/ui/main_window.py` to use ExcelProcessor with UI queue
- [x] T018 [US4] Add sheet navigation logic to WorkbookView: navigate_to_sheet() method with auto-navigation support
- [x] T019 [US4] Implement tab management in WorkbookView: create tabs for all sheets, handle sheet switching
- [x] T020 [US4] Add workbook completion workflow: save Excel file only after all sheets processed

**Checkpoint**: Multi-sheet Excel files should process sequentially with automatic sheet navigation

---

## Phase 5: User Story 2 - Show In-Progress Status for Active Questions (Priority: P2)

**Goal**: As the agent processes each question, the user sees the current question's cell highlighted in pink with a "Working..." indicator

**Independent Test**: Start question processing, observe currently active cell turns pink and displays "Working..." text

### Implementation for User Story 2

- [x] T021 [P] [US2] Implement cell state transitions in SpreadsheetView: update_cell() method with pink background for WORKING state
- [x] T022 [US2] Add CELL_WORKING event emission in ExcelProcessor.process_workbook() for each question start
- [x] T023 [US2] Implement UI event polling in WorkbookView: start_update_polling() method with 50ms queue polling
- [x] T024 [US2] Add event processing in WorkbookView._process_event() to handle CELL_WORKING events and update cell visuals
- [x] T025 [US2] Configure Treeview tags in SpreadsheetView for pink background (#FFB6C1) and "Working..." text display

**Checkpoint**: Active questions should show pink cells with "Working..." indicator during processing

---

## Phase 6: User Story 3 - Display Completed Answers with Visual Confirmation (Priority: P2)

**Goal**: When the agent completes answering a question, the response text appears in the cell and background changes to light green

**Independent Test**: Allow agent to complete at least one question, verify cell turns light green and contains the generated answer text

### Implementation for User Story 3

- [x] T026 [P] [US3] Add CELL_COMPLETED event emission in ExcelProcessor.process_workbook() when agent finishes each question
- [x] T027 [US3] Configure light green background (#90EE90) tag in SpreadsheetView for COMPLETED state
- [x] T028 [US3] Implement completed cell handling in WorkbookView._process_event() for CELL_COMPLETED events
- [x] T029 [US3] Add answer text display in SpreadsheetView.update_cell() for COMPLETED state with full answer content
- [x] T030 [US3] Update sheet progress tracking in SheetData: mark cells as COMPLETED and update is_complete status

**Checkpoint**: Completed questions should show light green cells with answer text

---

## Phase 7: User Story 5 - Visual Sheet Status Indicators (Priority: P2)

**Goal**: Sheet tabs display visual indicators showing processing status - currently active sheet shows a spinning spinner icon

**Independent Test**: Import multi-sheet Excel file, observe current sheet's tab displays spinner icon while processing

### Implementation for User Story 5

- [x] T031 [P] [US5] Add spinner character (⟳) support to WorkbookView.update_tab_indicator() for processing sheet tabs
- [x] T032 [US5] Implement tab text updates in WorkbookView: add/remove spinner based on sheet processing state
- [x] T033 [US5] Add SHEET_START event handling in WorkbookView._process_event() to show spinner on active sheet tab
- [x] T034 [US5] Add SHEET_COMPLETE event handling in WorkbookView._process_event() to remove spinner from completed sheet tab
- [x] T035 [US5] Handle edge cases: tab truncation for long sheet names with spinner, special character fallback rendering

**Checkpoint**: Processing sheet tabs should display spinner indicator

---

## Phase 8: User Story 6 - Respect User Sheet Navigation (Priority: P2)

**Goal**: When user manually clicks sheet tab, view remains on that user-selected sheet even as agent continues processing other sheets

**Independent Test**: Start processing on 3-sheet file, click Sheet 1 tab while Sheet 2 processes, verify view stays on Sheet 1

### Implementation for User Story 6

- [x] T036 [P] [US6] Implement NavigationState tracking in WorkbookView: lock_to_sheet() and auto_navigation_enabled property
- [x] T037 [US6] Add user tab click handler in WorkbookView.handle_user_tab_click() to disable auto-navigation
- [x] T038 [US6] Modify navigate_to_sheet() in WorkbookView to respect navigation lock state
- [x] T039 [US6] Add tab change event binding in WorkbookView.render() for `<<NotebookTabChanged>>` events
- [x] T040 [US6] Ensure background processing continues on all sheets regardless of which sheet user is viewing

**Checkpoint**: User tab clicks should override auto-navigation while preserving background processing

---

## Phase 9: User Story 7 - Preserve Deferred Save Behavior (Priority: P1)

**Goal**: Excel file is only saved to disk once all sheets and questions are processed, not incrementally during processing

**Independent Test**: Process multi-sheet Excel file, check file timestamp during processing, verify it only changes after all sheets complete

### Implementation for User Story 7

- [x] T041 [P] [US7] Add WORKBOOK_COMPLETE event emission in ExcelProcessor after all sheets finish processing
- [x] T042 [US7] Implement deferred save logic in UIManager._process_excel_internal(): call ExcelLoader.save_workbook() only after processing completes
- [x] T043 [US7] Add cancellation handling: no save operation if user exits during processing
- [x] T044 [US7] Implement file replacement workflow: stop current processing, cleanup agents, start new file processing
- [x] T045 [US7] Add hidden sheet preservation in ExcelLoader.save_workbook(): maintain hidden sheets unchanged

**Checkpoint**: Excel file should save only once after all processing completes, preserving hidden sheets

---

## Phase 10: Testing & Validation

**Purpose**: Comprehensive testing of all user stories and edge cases

- [ ] T046 [P] Create unit tests for data types in `tests/unit/test_data_types.py`: CellState, SheetData, WorkbookData, NavigationState
- [ ] T047 [P] Create unit tests for ExcelLoader in `tests/unit/test_excel_loader.py`: loading, saving, error handling
- [ ] T048 [P] Create unit tests for UI components in `tests/unit/test_ui_components.py`: SpreadsheetView, WorkbookView
- [ ] T049 [P] Create integration test for complete Excel workflow in `tests/integration/test_excel_workflow.py`
- [ ] T050 [P] Create UI update queue tests in `tests/integration/test_ui_updates.py`: event processing, thread safety
- [ ] T051 Create end-to-end test with sample Excel files: test all user stories together
- [ ] T052 Create performance test: 100 questions per sheet, 10 sheets maximum load testing

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T053 [P] Add logging throughout Excel processing workflow for debugging and monitoring
- [ ] T054 [P] Implement graceful shutdown handling in UIManager: cleanup agents on window close during processing
- [ ] T055 [P] Add error dialogs for Excel processing failures with user-friendly messages
- [ ] T056 Performance optimization: implement virtual scrolling for large spreadsheets (future enhancement)
- [ ] T057 [P] Update documentation in `README_Questionnaire_UI.md` with Excel processing features
- [ ] T058 Code cleanup and refactoring for consistency with existing codebase patterns

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories  
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - US1 and US4 are P1 priority and provide foundation for other stories
  - US2, US3, US5, US6 are P2 priority and can be developed in parallel after US1/US4
  - US7 is P1 priority and integrates with completion of processing workflow
- **Testing (Phase 10)**: Depends on all implemented user stories
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 4 (P1)**: Can start after Foundational - No dependencies on other stories, works with US1
- **User Story 2 (P2)**: Depends on US1 (SpreadsheetView) and US4 (ExcelProcessor) for visual updates
- **User Story 3 (P2)**: Depends on US1 (SpreadsheetView) and US4 (ExcelProcessor) for completed state display
- **User Story 5 (P2)**: Depends on US4 (WorkbookView tabs) for tab status indicators
- **User Story 6 (P2)**: Depends on US4 (WorkbookView) for navigation state management
- **User Story 7 (P1)**: Depends on US4 (ExcelProcessor) for save coordination

### Within Each User Story

- SpreadsheetView and WorkbookView UI components before integration
- ExcelProcessor workflow before UI event handling
- Core functionality before error handling and edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- After US1/US4 complete, US2, US3, US5, US6 can be developed in parallel
- All test creation tasks marked [P] can run in parallel
- Documentation and polish tasks marked [P] can run in parallel

---

## Parallel Example: After Foundational Phase

```bash
# Can start together after Foundational phase completes:
User Story 1: "View Live Spreadsheet in Answer Area" 
User Story 4: "Process All Sheets Sequentially"

# After US1/US4 complete, can start together:
User Story 2: "Show In-Progress Status for Active Questions"
User Story 3: "Display Completed Answers with Visual Confirmation" 
User Story 5: "Visual Sheet Status Indicators"
User Story 6: "Respect User Sheet Navigation"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Spreadsheet display)
4. Complete Phase 4: User Story 4 (Multi-sheet processing)
5. **STOP and VALIDATE**: Test basic Excel import and processing
6. Deploy/demo basic functionality

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + 4 → Test multi-sheet import/processing → Deploy/Demo (MVP!)
3. Add User Story 2 + 3 → Test visual progress indicators → Deploy/Demo  
4. Add User Story 5 + 6 → Test tab navigation and status → Deploy/Demo
5. Add User Story 7 → Test complete save workflow → Deploy/Demo
6. Each increment adds value without breaking previous functionality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Spreadsheet display)
   - Developer B: User Story 4 (Excel processing workflow)
3. After US1/US4 complete:
   - Developer A: User Story 2 + 3 (Visual progress)
   - Developer B: User Story 5 + 6 (Tab management)
   - Developer C: User Story 7 (Save workflow)
4. Stories integrate and test independently

---

## Statistics

- **Total Tasks**: 58 tasks across 11 phases
- **P1 Priority User Stories**: 3 stories (US1, US4, US7) - 21 tasks
- **P2 Priority User Stories**: 4 stories (US2, US3, US5, US6) - 21 tasks  
- **Parallel Opportunities**: 23 tasks marked [P] for concurrent execution
- **Independent Testing**: Each user story has clear acceptance criteria and can be validated independently
- **MVP Scope**: User Stories 1 + 4 provide complete basic Excel processing functionality (14 implementation tasks)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability  
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Focus on P1 stories (US1, US4, US7) for MVP delivery
- P2 stories (US2, US3, US5, US6) add polish and enhanced user experience
