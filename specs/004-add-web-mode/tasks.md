# Tasks: Web Interface Mode

**Input**: Design documents from `/specs/004-add-web-mode/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: This feature specification includes Test-Driven Development (TDD) approach with Playwright tests (User Story 7, FR-022, Constitution Check). Tests are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, and basic web module structure

- [ ] T001 Update requirements.txt with web dependencies: fastapi, uvicorn, jinja2, python-multipart, playwright
- [ ] T002 [P] Create web module directory structure: `src/web/__init__.py`
- [ ] T003 [P] Create static files directory: `src/web/static/` (empty placeholder)
- [ ] T004 [P] Create test directory structure: `tests/web/__init__.py`, `tests/web/playwright/__init__.py`
- [ ] T005 [P] Install Playwright browsers: run `playwright install chromium firefox webkit`
- [ ] T006 [P] Create pytest configuration for Playwright in `tests/web/conftest.py` with server fixture

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core web infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Data Models

- [ ] T007 [P] Create Pydantic models for session entities in `src/web/models.py`: SessionConfig, WebSession, JobStatus enum
- [ ] T008 [P] Create Pydantic models for API requests in `src/web/models.py`: QuestionRequest, ProcessingStartRequest
- [ ] T009 [P] Create Pydantic models for API responses in `src/web/models.py`: SessionCreateResponse, QuestionResponse, ProcessingStatusResponse
- [ ] T010 [P] Create SSEMessage Pydantic model with SSEMessageType enum in `src/web/models.py`

### Core Managers

- [ ] T011 Implement SessionManager class in `src/web/session_manager.py` with create_session(), get_session(), update_config(), delete_session() methods
- [ ] T012 Implement SSEManager class in `src/web/sse_manager.py` with per-session asyncio queues, send_event(), stream_events() async generator
- [ ] T013 [P] Create web module logger configuration in `src/web/logger.py` using existing `utils.logger` patterns

### FastAPI Application Core

- [ ] T014 Create FastAPI app skeleton in `src/web/app.py` with title, static file mount, health endpoint
- [ ] T015 Add session manager singleton import and initialization in `src/web/app.py`
- [ ] T016 Add SSE manager singleton import and initialization in `src/web/app.py`
- [ ] T017 Implement health check endpoint GET /health in `src/web/app.py` returning status and Azure auth state

### Entry Point Integration

- [ ] T018 Add `--web` and `--port` command-line arguments to `run_app.py` using argparse
- [ ] T019 Implement web mode branch in `run_app.py` main(): server thread start, health check wait, webbrowser.open(), thread join
- [ ] T020 Add graceful shutdown handling in `run_app.py` for web server (SIGINT/SIGTERM)

**Checkpoint**: Foundation ready - FastAPI server starts with `python run_app.py --web`, health endpoint works, user story implementation can begin

---

## Phase 3: User Story 1 - Launch Web Interface Mode (Priority: P1) 🎯 MVP

**Goal**: Users can start the application with --web flag, launching web server and opening browser automatically

**Independent Test**: Run `python run_app.py --web --port 8080`, verify browser opens to localhost:8080, verify page loads, verify no tkinter window

### Tests for User Story 1

- [ ] T021 [P] [US1] Create Playwright test file `tests/web/playwright/test_launch_and_navigation.py`
- [ ] T022 [P] [US1] Write test_server_starts_on_web_flag: verify GET http://localhost:8080/health returns 200
- [ ] T023 [P] [US1] Write test_index_page_loads: navigate to /, verify page contains expected title/elements
- [ ] T024 [US1] Write test_unique_session_per_tab: open two browser contexts, verify different session IDs in localStorage
- [ ] T025 [P] [US1] Write test_port_already_in_use_error: start server, try starting another on same port, verify error message
- [ ] T026 [P] [US1] Create unit test file `tests/web/test_session_manager.py` with tests for create_session, get_session, session isolation

### Implementation for User Story 1

- [ ] T027 [P] [US1] Create minimal `src/web/static/index.html` with HTML5 boilerplate, app title, loading placeholder div
- [ ] T028 [P] [US1] Create `src/web/static/styles.css` with CSS reset and basic layout styles (minimal, before Foundry styling)
- [ ] T029 [US1] Create `src/web/static/app.js` with session initialization: check localStorage, call POST /api/session/create if needed
- [ ] T030 [US1] Implement POST /api/session/create endpoint in `src/web/app.py` returning session_id, created_at, config
- [ ] T031 [US1] Implement GET /api/session/{session_id} endpoint in `src/web/app.py`
- [ ] T032 [US1] Implement PUT /api/session/{session_id}/config endpoint in `src/web/app.py`
- [ ] T033 [US1] Implement GET / route in `src/web/app.py` serving index.html via FileResponse
- [ ] T034 [US1] Add error handling for port-in-use scenario in `run_app.py` with user-friendly error message

**Checkpoint**: User Story 1 complete - `python run_app.py --web` starts server, opens browser, each tab gets unique session

---

## Phase 4: User Story 2 - Process Questions Through Web Interface (Priority: P1) 🎯 MVP

**Goal**: Users can enter questions in web form, submit for processing, and see answers with reasoning

**Independent Test**: Load web interface, enter question "What is Azure?", click Submit, verify answer appears with expandable reasoning

### Tests for User Story 2

- [ ] T035 [P] [US2] Create Playwright test file `tests/web/playwright/test_single_question.py`
- [ ] T036 [P] [US2] Write test_question_form_visible: verify question input, context input, char limit input, submit button exist
- [ ] T037 [P] [US2] Write test_submit_question_shows_loading: click submit, verify loading indicator appears, button disabled
- [ ] T038 [US2] Write test_answer_displayed_after_processing: submit question, wait for answer, verify answer text appears
- [ ] T039 [US2] Write test_reasoning_expandable: verify reasoning section is collapsed by default, expands on click
- [ ] T040 [P] [US2] Write test_char_limit_respected: set char limit to 500, submit question, verify answer length constraint
- [ ] T041 [P] [US2] Create unit test `tests/web/test_api_routes.py` with test_process_question_success, test_process_question_invalid_session

### Implementation for User Story 2

- [ ] T042 [US2] Add question form HTML to `src/web/static/index.html`: textarea, context input, char_limit input, submit button, loading div, results div
- [ ] T043 [US2] Add reasoning expandable section HTML to `src/web/static/index.html`: details/summary pattern with reasoning-content div
- [ ] T044 [US2] Implement question submission JavaScript in `src/web/static/app.js`: event listener, fetch POST /api/question, update results
- [ ] T045 [US2] Add loading state management in `src/web/static/app.js`: show/hide loading indicator, enable/disable submit button
- [ ] T046 [US2] Implement POST /api/question endpoint in `src/web/app.py` delegating to AgentCoordinator from agents.workflow_manager
- [ ] T047 [US2] Add session validation and error handling for /api/question (404 if session not found, 422 for validation errors)
- [ ] T048 [US2] Format reasoning trace in response using existing `utils.reasoning_formatter` patterns
- [ ] T049 [US2] Add link clickability in answers: JavaScript to detect URLs and make them clickable with target="_blank"

**Checkpoint**: User Stories 1 AND 2 complete - full single question flow works through web interface

---

## Phase 5: User Story 3 - Load and Process Excel Files (Priority: P2)

**Goal**: Users can upload Excel files, view in grid, select columns, process batch questions with progress updates

**Independent Test**: Upload test Excel file, select columns, click Process, verify all rows get answers with progress bar

### Tests for User Story 3

- [ ] T050 [P] [US3] Create Playwright test file `tests/web/playwright/test_spreadsheet_upload.py`
- [ ] T051 [P] [US3] Write test_file_upload_button_visible: verify file upload input exists
- [ ] T052 [US3] Write test_upload_excel_shows_grid: upload test.xlsx, verify spreadsheet grid appears with data
- [ ] T053 [US3] Write test_column_dropdowns_populated: after upload, verify Question/Context/Answer column selectors have options
- [ ] T054 [US3] Write test_column_auto_selection: verify auto-detected columns are pre-selected in dropdowns
- [ ] T055 [P] [US3] Write test_invalid_file_rejected: upload .txt file, verify error message
- [ ] T056 [P] [US3] Create Playwright test file `tests/web/playwright/test_spreadsheet_processing.py`
- [ ] T057 [US3] Write test_start_processing_shows_progress: click Process, verify progress bar appears and updates
- [ ] T058 [US3] Write test_answers_appear_in_grid: during processing, verify answer cells update in real-time
- [ ] T059 [US3] Write test_download_button_after_complete: verify Download button appears after processing completes

### Implementation for User Story 3

- [ ] T060 [US3] Add spreadsheet section HTML to `src/web/static/index.html`: file input, column selectors, process button, grid container, download button
- [ ] T061 [US3] Create `src/web/static/spreadsheet.js` with ag-Grid CDN import and initializeGrid() function
- [ ] T062 [US3] Implement file upload JavaScript in `src/web/static/app.js`: FormData construction, POST /api/spreadsheet/upload, grid initialization
- [ ] T063 [US3] Implement column selector population and auto-selection in `src/web/static/app.js` from upload response suggestions
- [ ] T064 [US3] Implement POST /api/spreadsheet/upload endpoint in `src/web/app.py` using UploadFile, tempfile, ExcelLoader, ColumnIdentifier
- [ ] T065 [US3] Create ColumnSuggestions and SpreadsheetUploadResponse models in `src/web/models.py`
- [ ] T066 [US3] Implement POST /api/spreadsheet/process endpoint in `src/web/app.py` creating ProcessingJob, starting async processing
- [ ] T067 [US3] Add ProcessingJob model to `src/web/models.py` with status, progress tracking, results list
- [ ] T068 [US3] Implement async spreadsheet processing loop in `src/web/app.py` or `src/web/processor.py` calling AgentCoordinator per row
- [ ] T069 [US3] Integrate SSE progress updates during processing: call sse_manager.send_event() with PROGRESS type after each row
- [ ] T070 [US3] Integrate SSE answer updates: call sse_manager.send_event() with ANSWER type containing row and answer data
- [ ] T071 [US3] Implement GET /api/spreadsheet/status/{session_id} endpoint in `src/web/app.py` returning ProcessingStatusResponse
- [ ] T072 [US3] Implement GET /api/spreadsheet/download/{session_id} endpoint in `src/web/app.py` returning FileResponse with updated Excel
- [ ] T073 [US3] Add progress bar HTML and update logic in `src/web/static/app.js` driven by SSE PROGRESS messages
- [ ] T074 [US3] Add grid cell update logic in `src/web/static/spreadsheet.js` using gridApi.setDataValue() from SSE ANSWER messages

**Checkpoint**: User Stories 1, 2, AND 3 complete - full spreadsheet processing works with real-time updates

---

## Phase 6: User Story 4 - View Reasoning and Diagnostics (Priority: P2)

**Goal**: Users can view detailed reasoning traces for each answer including agent actions and links checked

**Independent Test**: Process question, click "Show Reasoning", verify detailed trace with timestamps and agent steps

### Tests for User Story 4

- [ ] T075 [P] [US4] Create Playwright test file `tests/web/playwright/test_reasoning_display.py`
- [ ] T076 [US4] Write test_reasoning_toggle_works: submit question, click show reasoning, verify details visible, click hide, verify collapsed
- [ ] T077 [US4] Write test_reasoning_has_structure: verify reasoning contains headings, timestamps, agent action sections
- [ ] T078 [US4] Write test_spreadsheet_row_reasoning: click on answer cell in grid, verify side panel shows that row's reasoning

### Implementation for User Story 4

- [ ] T079 [US4] Enhance reasoning formatting in `src/web/app.py` question endpoint to include structured agent workflow data
- [ ] T080 [US4] Add CSS for reasoning display in `src/web/static/styles.css`: indentation, timestamps, agent step styling
- [ ] T081 [US4] Implement reasoning toggle JavaScript in `src/web/static/app.js` for single question results
- [ ] T082 [US4] Add row click handler in `src/web/static/spreadsheet.js` to open reasoning modal/side panel for spreadsheet rows
- [ ] T083 [US4] Create reasoning modal HTML structure in `src/web/static/index.html` for spreadsheet row details

**Checkpoint**: User Stories 1-4 complete - users can view reasoning for any answer

---

## Phase 7: User Story 5 - Modern Spreadsheet Component Features (Priority: P3)

**Goal**: Professional spreadsheet with sorting, filtering, cell selection, copy/paste, smooth scrolling

**Independent Test**: Load 100+ row spreadsheet, sort columns, filter rows, select cells, copy to clipboard, scroll smoothly

### Tests for User Story 5

- [ ] T084 [P] [US5] Create Playwright test file `tests/web/playwright/test_spreadsheet_features.py`
- [ ] T085 [US5] Write test_column_sorting: click column header, verify rows reorder, click again for reverse
- [ ] T086 [US5] Write test_column_filtering: enter filter text, verify only matching rows visible
- [ ] T087 [US5] Write test_cell_selection: click and drag across cells, verify selection highlighting
- [ ] T088 [US5] Write test_copy_to_clipboard: select cells, press Ctrl+C, verify clipboard has tab-separated data
- [ ] T089 [P] [US5] Write test_large_dataset_scroll: load 1000 rows, scroll, verify 60fps performance (visual check)

### Implementation for User Story 5

- [ ] T090 [US5] Configure ag-Grid sorting in `src/web/static/spreadsheet.js`: sortable column definitions
- [ ] T091 [US5] Configure ag-Grid filtering in `src/web/static/spreadsheet.js`: filter: true on columns, add filter row
- [ ] T092 [US5] Configure ag-Grid range selection in `src/web/static/spreadsheet.js`: enableRangeSelection: true
- [ ] T093 [US5] Configure ag-Grid clipboard in `src/web/static/spreadsheet.js`: enable copy, Excel-compatible format
- [ ] T094 [US5] Configure ag-Grid virtual scrolling in `src/web/static/spreadsheet.js`: rowBuffer, animateRows settings for large datasets

**Checkpoint**: User Stories 1-5 complete - professional spreadsheet UX

---

## Phase 8: User Story 6 - Microsoft Foundry Visual Design (Priority: P3)

**Goal**: Polished visual design matching Microsoft Foundry aesthetics

**Independent Test**: Visual inspection comparing interface to Foundry screenshots, verify typography, colors, spacing, shadows

### Tests for User Story 6

- [ ] T095 [P] [US6] Create Playwright test file `tests/web/playwright/test_visual_design.py`
- [ ] T096 [US6] Write test_typography: verify font-family is Segoe UI, check heading/body font sizes
- [ ] T097 [US6] Write test_button_styles: verify buttons have correct border-radius, shadows, hover states
- [ ] T098 [US6] Write test_responsive_layout: resize viewport, verify layout adapts without breaking

### Implementation for User Story 6

- [ ] T099 [US6] Implement CSS variables for Foundry design tokens in `src/web/static/styles.css`: --primary, --spacing-*, --shadow-*, --radius-*
- [ ] T100 [US6] Style typography in `src/web/static/styles.css`: Segoe UI font-family, weight/size scale for headings and body
- [ ] T101 [US6] Style buttons in `src/web/static/styles.css`: primary color, hover states, disabled state, border-radius, transitions
- [ ] T102 [US6] Style form inputs in `src/web/static/styles.css`: border, focus state, padding, border-radius
- [ ] T103 [US6] Style cards/panels in `src/web/static/styles.css`: background, shadows (depth-4, depth-8), border-radius
- [ ] T104 [US6] Add spacing utilities in `src/web/static/styles.css`: margins/padding based on 4px base unit (8px, 12px, 16px, 24px)
- [ ] T105 [US6] Style loading indicators in `src/web/static/styles.css`: spinner animation, colors
- [ ] T106 [US6] Style progress bars in `src/web/static/styles.css`: track/fill colors, border-radius, animation
- [ ] T107 [US6] Add responsive breakpoints in `src/web/static/styles.css` for tablet/mobile viewports
- [ ] T108 [US6] Update HTML structure in `src/web/static/index.html` to add appropriate CSS classes for Foundry styling

**Checkpoint**: User Stories 1-6 complete - visually polished interface

---

## Phase 9: User Story 7 - Automated End-to-End Testing (Priority: P3)

**Goal**: Comprehensive Playwright test suite covering all scenarios across browsers

**Independent Test**: Run full test suite, verify all tests pass in Chromium/Firefox/WebKit, verify failure screenshots captured

### Tests for User Story 7 (Meta-tests - testing the test infrastructure)

- [ ] T109 [P] [US7] Write test_screenshot_on_failure: intentionally failing test, verify screenshot captured
- [ ] T110 [P] [US7] Write test_multi_browser_execution: verify tests run in chromium, firefox, webkit

### Implementation for User Story 7

- [ ] T111 [US7] Configure pytest-playwright in `tests/web/conftest.py` with multi-browser fixtures (chromium, firefox, webkit)
- [ ] T112 [US7] Add screenshot-on-failure hook in `tests/web/conftest.py` using pytest_runtest_makereport
- [ ] T113 [US7] Add video recording configuration in `tests/web/conftest.py` for debugging (optional, off by default)
- [ ] T114 [US7] Create test runner script `tests/web/run_tests.py` to start server, run tests, stop server
- [ ] T115 [US7] Document test execution in `tests/web/README.md` with commands for single browser, all browsers, headed mode

**Checkpoint**: User Stories 1-7 complete - full test suite ready for CI

---

## Phase 10: Additional Features & Integration

**Purpose**: SSE infrastructure, stop/cancel, session recovery, and cross-cutting concerns

### SSE Stream Endpoint

- [ ] T116 [P] Implement GET /api/sse/{session_id} endpoint in `src/web/app.py` using StreamingResponse
- [ ] T117 Add SSE connection handling in `src/web/static/app.js`: EventSource creation, message handler, reconnection logic

### Stop/Cancel Processing

- [ ] T118 Create Playwright test `tests/web/playwright/test_stop_processing.py` with test_stop_button_visible, test_stop_cancels_job
- [ ] T119 Implement POST /api/spreadsheet/stop endpoint in `src/web/app.py` setting job status to CANCELLED
- [ ] T120 Add stop button HTML and JavaScript in `src/web/static/app.js` and `src/web/static/index.html`
- [ ] T121 Implement graceful cancellation in processing loop checking job.status before each row

### Session Recovery

- [ ] T122 Create Playwright test `tests/web/playwright/test_session_recovery.py` with test_reconnect_shows_progress
- [ ] T123 Implement session recovery JavaScript in `src/web/static/app.js`: on load, check for active job, fetch status, resume SSE

### Error Handling

- [ ] T124 [P] Implement WebErrorResponse model in `src/web/models.py` with error_code, message, details
- [ ] T125 [P] Add global exception handlers in `src/web/app.py` for HTTPException, validation errors, Azure auth errors
- [ ] T126 Implement Azure auth error handling: catch CredentialUnavailableError, return 401 with re-auth message
- [ ] T127 Add error display component in `src/web/static/app.js`: show error messages in toast/banner UI

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, validation

- [ ] T128 [P] Update README.md with web mode documentation: `--web` flag usage, port configuration, browser requirements
- [ ] T129 [P] Update requirements.txt to include version pins for web dependencies
- [ ] T130 [P] Add type hints to all `src/web/*.py` files for mypy compatibility
- [ ] T131 Run ruff linting on all `src/web/` files and fix any issues
- [ ] T132 Run quickstart.md validation: follow steps, verify each phase works as documented
- [ ] T133 Performance testing: load 1000 row spreadsheet, verify <2s SSE latency, 60fps scrolling
- [ ] T134 Security review: verify no sensitive data in HTML/JS, proper error message sanitization
- [ ] T135 Add inline code documentation to `src/web/app.py` explaining key endpoints and patterns

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-9)**: All depend on Foundational phase completion
  - US1 (P1), US2 (P1): Required for MVP, must complete first
  - US3 (P2), US4 (P2): Can proceed after US1+US2
  - US5 (P3), US6 (P3), US7 (P3): Can proceed in parallel after P2 stories
- **Additional Features (Phase 10)**: Depends on US1, US2, US3 for integration
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

| Story | Priority | Depends On | Can Start After |
|-------|----------|------------|-----------------|
| US1 - Launch Web Interface | P1 | Foundational | Phase 2 complete |
| US2 - Process Questions | P1 | US1 | T034 (US1 complete) |
| US3 - Load Excel Files | P2 | US1, US2 | T049 (US2 complete) |
| US4 - View Reasoning | P2 | US2 | T049 (US2 complete) |
| US5 - Spreadsheet Features | P3 | US3 | T074 (US3 complete) |
| US6 - Visual Design | P3 | US1 | T034 (US1 complete, can parallelize) |
| US7 - Automated Testing | P3 | US1-US6 | After all features implemented |

### Within Each User Story

1. Tests FIRST (TDD approach per constitution)
2. Models/data structures
3. Backend endpoints
4. Frontend HTML/CSS
5. Frontend JavaScript
6. Integration and error handling

### Parallel Opportunities

**Phase 2 (Foundational)** - All T007-T010 models can run in parallel:
```
T007 [P] Session entities models
T008 [P] API request models
T009 [P] API response models
T010 [P] SSE message models
```

**Phase 3 (US1)** - Tests can run in parallel:
```
T021 [P] Test file creation
T022 [P] test_server_starts_on_web_flag
T023 [P] test_index_page_loads
T025 [P] test_port_already_in_use_error
T026 [P] test_session_manager unit tests
```

**Phase 3 (US1)** - Static files can be created in parallel:
```
T027 [P] index.html
T028 [P] styles.css
```

**Phase 8 (US6)** - CSS styling tasks can be parallelized by developer:
```
T100-T108 can be distributed across multiple developers working on different style sections
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all model creation tasks together:
T007 "Create Pydantic models for session entities in src/web/models.py"
T008 "Create Pydantic models for API requests in src/web/models.py"
T009 "Create Pydantic models for API responses in src/web/models.py"
T010 "Create SSEMessage Pydantic model in src/web/models.py"
# Note: These are [P] because they define separate model classes in same file - can be merged

# Then sequentially:
T011 "Implement SessionManager class" (depends on T007 for type hints)
T012 "Implement SSEManager class" (depends on T010 for SSEMessage type)
```

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together:
T022 [P] test_server_starts_on_web_flag
T023 [P] test_index_page_loads
T025 [P] test_port_already_in_use_error
T026 [P] test_session_manager unit tests

# Launch static file creation together:
T027 [P] index.html
T028 [P] styles.css

# Sequential: JavaScript and endpoints (JavaScript calls endpoints)
T029 app.js session init (calls T030-T031)
T030 POST /api/session/create
T031 GET /api/session/{session_id}
T032 PUT /api/session/{session_id}/config
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T006) - ~30 min
2. Complete Phase 2: Foundational (T007-T020) - ~2 hours
3. Complete Phase 3: User Story 1 (T021-T034) - ~2 hours
4. Complete Phase 4: User Story 2 (T035-T049) - ~3 hours
5. **STOP and VALIDATE**: Run `python run_app.py --web`, test question submission
6. **MVP Delivered**: Users can ask questions through web interface!

### Incremental Delivery

| Delivery | Stories | Value Delivered |
|----------|---------|-----------------|
| MVP | US1 + US2 | Basic web question answering |
| V1.1 | + US3 | Excel spreadsheet processing |
| V1.2 | + US4 | Reasoning transparency |
| V2.0 | + US5 + US6 | Professional UX |
| V2.1 | + US7 | Automated quality assurance |

### Time Estimates

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Setup | T001-T006 | 30 minutes |
| Foundational | T007-T020 | 2-3 hours |
| US1 (P1) | T021-T034 | 2-3 hours |
| US2 (P1) | T035-T049 | 3-4 hours |
| US3 (P2) | T050-T074 | 4-5 hours |
| US4 (P2) | T075-T083 | 2-3 hours |
| US5 (P3) | T084-T094 | 2-3 hours |
| US6 (P3) | T095-T108 | 3-4 hours |
| US7 (P3) | T109-T115 | 1-2 hours |
| Additional | T116-T127 | 2-3 hours |
| Polish | T128-T135 | 1-2 hours |
| **Total** | 135 tasks | ~25-35 hours |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD approach: Write tests first, ensure they FAIL before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All paths assume repository root is working directory
- Static files served from `src/web/static/` mounted at `/static`
- ag-Grid loaded from CDN to avoid bundling complexity
