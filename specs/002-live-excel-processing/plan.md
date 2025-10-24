# Implementation Plan: Live Excel Processing Visualization

**Branch**: `002-live-excel-processing` | **Date**: October 23, 2025 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/002-live-excel-processing/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the Answer area to render Excel spreadsheets with live visual feedback during multi-agent question processing. When users import Excel files, the system uses Azure AI to detect question/answer columns from headers (supporting arbitrary column layouts), displays all visible sheets with tabs (Excel-style), shows pink "Working..." indicators for questions being processed, and updates cells to light green with completed answers in real-time. The system processes all questionnaire sheets sequentially with automatic view navigation that respects user sheet selection, handles graceful interruption with agent cleanup, supports file replacement during processing, and saves the entire workbook (including hidden sheets) only after all processing completes.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: tkinter (GUI), openpyxl (Excel), agent-framework-azure-ai (multi-agent), azure-ai-projects, azure-identity  
**Storage**: Excel files (.xlsx) on local filesystem  
**Testing**: pytest with pytest-asyncio, mock Azure services for unit tests  
**Target Platform**: Windows desktop (primary), cross-platform capable (Linux, macOS)  
**Project Type**: Single desktop application with GUI  
**Performance Goals**:

*   Spreadsheet render \< 2s for 100 questions per sheet
*   Cell status update \< 500ms after agent state change
*   Sheet tab navigation \< 200ms response time
*   Support up to 10 sheets with 100 questions each

**Constraints**:

*   Must integrate with existing multi-agent workflow (Question Answerer → Answer Checker → Link Checker)
*   Must not modify Excel save behavior (deferred until all complete)
*   Must reuse existing tkinter infrastructure and Azure AI Foundry patterns
*   Must maintain FoundryAgentSession resource management patterns
*   Must NOT assume questions/answers in columns A/B - AI model detects columns from headers
*   Must handle hidden sheets (preserve but don't display)
*   Must support graceful interruption (user exit: cleanup agents, save nothing)
*   Must support file replacement during active processing (stop current, start new)

**Scale/Scope**:

*   Typical: 5-50 questions per sheet, 1-5 sheets
*   Maximum: 100 questions per sheet, 10 sheets (1000 questions total)
*   Display resolution: 1024x768 minimum
*   Scrolling: Auto-scroll 3 cells down when active question off-screen
*   Sheet naming: Support special characters (fallback to box), truncate long names with "..."

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

*   **Multi-Agent Architecture**: Feature integrates with existing Question Answerer, Answer Checker, and Link Checker pattern - UI enhancement only, uses existing AgentCoordinator workflow
*   **Azure AI Foundry Integration**: Uses Azure AI Foundry Agent Service and SDK exclusively with DefaultAzureCredential - no changes to agent infrastructure
*   **Resource Management**: All agents/threads managed through FoundryAgentSession context managers - reuses existing cleanup patterns in UIManager
*   **Environment Configuration**: Sensitive data in .env files, never committed to version control - no new configuration needed
*   **Test-Driven Development**: Tests written first, including Azure service failure scenarios and mock modes - will create UI component tests and Excel processing integration tests

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── excel/                    # NEW: Excel file handling
│   ├── __init__.py
│   ├── loader.py            # Load/save Excel workbooks with hidden sheet support
│   ├── column_detector.py   # NEW: AI-based column detection from headers
│   └── processor.py         # Multi-sheet processing workflow with cancellation
├── ui/                       # MODIFIED: Enhanced UI components
│   ├── __init__.py
│   ├── main_window.py       # MODIFIED: Integrate WorkbookView + shutdown handler
│   ├── spreadsheet_view.py  # NEW: Single sheet Treeview with auto-scroll
│   ├── workbook_view.py     # NEW: Multi-sheet Notebook with tab truncation
│   ├── dialogs.py           # Existing: Error dialogs
│   └── status_manager.py    # Existing: Status bar
├── agents/                   # MODIFIED: Add cleanup manager
│   ├── question_answerer.py
│   ├── answer_checker.py
│   ├── link_checker.py
│   ├── workflow_manager.py
│   └── cleanup_manager.py   # NEW: Agent deletion on interruption
└── utils/                    # MODIFIED: Extended data types
    ├── data_types.py        # MODIFIED: Add WorkbookData, SheetData, CellState, ColumnMapping, etc.
    ├── exceptions.py        # Existing: ExcelFormatError already defined
    └── config.py            # Existing: No changes

tests/
├── unit/                     # NEW: UI and loader unit tests
│   ├── test_data_types.py   # NEW: Test WorkbookData, SheetData, etc.
│   ├── test_excel_loader.py # NEW: Test Excel loading/saving
│   └── test_ui_components.py # NEW: Test SpreadsheetView, WorkbookView
├── integration/              # NEW: End-to-end workflow tests
│   ├── test_excel_workflow.py # NEW: Full Excel processing test
│   └── test_ui_updates.py   # NEW: UI update queue tests
└── fixtures/                 # NEW: Test Excel files
    └── excel/
        ├── single_sheet.xlsx
        ├── multi_sheet.xlsx
        └── invalid.xlsx
```

**Structure Decision**: Single project structure (Option 1). This feature extends the existing desktop application with new Excel handling modules and enhanced UI components. No new projects or services are introduced. All code follows the existing `src/` layout with new subdirectories for Excel functionality and enhanced UI widgets.

**Key Additions**:

*   `src/excel/` - New module for Excel file operations with hidden sheet support
*   `src/excel/column_detector.py` - AI-based column header analysis
*   `src/ui/spreadsheet_view.py` - New UI component for sheet rendering with auto-scroll
*   `src/ui/workbook_view.py` - New UI component for multi-sheet navigation with tab truncation
*   `src/agents/cleanup_manager.py` - Agent deletion on user exit/interruption
*   Enhanced `src/utils/data_types.py` with workbook-related data structures (ColumnMapping, SheetType, etc.)
*   New test files for Excel, column detection, and UI components

**Modifications**:

*   `src/ui/main_window.py` - Integrate WorkbookView + shutdown handler for graceful exit
*   `src/excel/processor.py` - Add cancellation support for file replacement
*   `src/utils/data_types.py` - Add new data classes (WorkbookData, SheetData, ColumnMapping, CellState, etc.)

## Complexity Tracking

_No constitutional violations - feature fully complies with all principles._

This feature introduces no architectural complexity beyond the existing patterns:

*   ✅ Reuses existing multi-agent workflow (no new agents)
*   ✅ Follows existing UI patterns (tkinter widgets)
*   ✅ Maintains resource management patterns (FoundryAgentSession)
*   ✅ Extends existing data types (utils.data\_types)
*   ✅ No new external services or dependencies

All complexity is inherent to the feature requirements (multi-sheet visualization, live updates) and handled through standard patterns already established in the codebase.

## Key Clarifications from Spec

The following clarifications were resolved during specification review and drive implementation decisions:

### Column Detection & Sheet Classification

*   **Challenge**: Excel files have questions/answers in arbitrary columns
*   **Solution**: Use Azure AI Foundry model to analyze column headers and detect question/answer/documentation columns
*   **Impact**: Adds pre-processing step before sheet rendering; some sheets may not be questionnaires (render-only, no processing)

### Scrolling & Navigation

*   **Challenge**: Sheets can have 5-100 questions (variable sizes)
*   **Solution**: Scrollbars in renderer + auto-scroll 3 cells when active question off-screen (if user hasn't manually scrolled)
*   **Impact**: Requires scroll position tracking and user interaction detection

### Interruption Handling

*   **Challenge**: User exit vs. crash behavior
*   **Solution**: User exit → stop processing, cleanup agents from Azure AI Foundry, close window, save nothing. Crash → unrecoverable.
*   **Impact**: Requires graceful shutdown handler and agent cleanup in UIManager

### File Replacement During Processing

*   **Challenge**: User imports new file while processing active
*   **Solution**: Stop current processing, stop all agents, unload document, load new file, start fresh
*   **Impact**: Requires cancellation token pattern and state machine for processing workflow

### Hidden Sheets

*   **Challenge**: Excel files may have hidden sheets
*   **Solution**: Don't show in UI tabs, but preserve verbatim when saving final file
*   **Impact**: Requires openpyxl hidden sheet detection and passthrough logic

### Sheet Name Display

*   **Challenge**: Sheet names may have special characters or be very long
*   **Solution**: Special chars → render as box, long names → truncate with "..."
*   **Impact**: Requires text sanitization and measurement for tab labels

### Formatting Support

*   **Challenge**: Excel cells have complex formatting (merged, colors, fonts, dropdowns)
*   **Solution**: Render colors + basic font styles (bold/italic), render merged cells as merged, dropdowns as normal cells, skip advanced formatting
*   **Impact**: Requires openpyxl cell style reading and tkinter Treeview styling

### Rapid Sheet Tab Clicking

*   **Challenge**: User rapidly clicks between sheets during processing
*   **Solution**: System renders whichever sheet user clicked (no debouncing/throttling)
*   **Impact**: UI must handle rapid view switches without blocking or crashing

## Phase 0: Research & Design Decisions

### Research Tasks

**Tkinter Spreadsheet Rendering**

*   **Question**: Which tkinter widget best supports Excel-like table rendering with per-cell styling, scrolling, and merged cells?
*   **Options**: Treeview, Canvas + custom grid, third-party (tksheet, tkintertable)
*   **Decision Criteria**: Merged cell support, performance with 100 rows, styling flexibility, maintenance burden

**Azure AI Model for Column Detection**

*   **Question**: How to structure prompt for reliable column header analysis?
*   **Options**: JSON schema output, structured text parsing, few-shot examples
*   **Decision Criteria**: Accuracy on ambiguous headers, token efficiency, error handling

**Processing Cancellation Pattern**

*   **Question**: How to cancel multi-agent async workflow mid-execution?
*   **Options**: asyncio.CancelledError, threading.Event, agent-framework cancellation tokens
*   **Decision Criteria**: Compatibility with FoundryAgentSession, cleanup guarantees, existing patterns in codebase

**Auto-Scroll UX**

*   **Question**: How to detect user manual scrolling vs. programmatic scrolling?
*   **Options**: Scroll event binding, last-interaction timestamp, explicit user-lock flag
*   **Decision Criteria**: Reliability, simplicity, compatibility with chosen widget

**Openpyxl Hidden Sheet Handling**

*   **Question**: How to preserve hidden sheets without modifying them?
*   **Options**: Load all → filter for display → write all, separate read/write workflows
*   **Decision Criteria**: Data integrity, simplicity, performance

### Research Outcomes

_This section will be filled by Phase 0 execution. Each research task above will result in a documented decision with rationale and implementation notes._

## Phase 1: Data Model & Contracts

_This section will be filled by Phase 1 execution after research is complete. Will include:_

*   `data-model.md` - WorkbookData, SheetData, ColumnMapping, CellState entities
*   `contracts/` - UI component interfaces, Excel processor interfaces
*   `quickstart.md` - Developer setup and testing guide

## Phase 2: Task Breakdown

_This section is NOT filled by /speckit.plan. Use /speckit.tasks command after Phase 1 completion to generate tasks.md._