# Feature Specification: Live Excel Processing Visualization

**Feature Branch**: `002-live-excel-processing`  
**Created**: October 23, 2025  
**Status**: Draft  
**Input**: User description: "Amend the Answer area so that, when the user selects Import From Excel, live results are shown. The Answer area should be amended in such a way as to render the spreadsheet. On this spreadsheet, as the agent is working on a question for a given cell, it should render that cell in pink with a notification saying Working... When the agents complete a question, the text should be written to that cell. Completed cells should render in light green. This should not change the saving behavior of the Excel spreadsheet - it should only be saved once the whole spreadsheet is done. But this will give users the ability to see the questionnaire agent fill out the questionnaire while it is in progress."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - View Live Spreadsheet in Answer Area (Priority: P1)

When a user imports questions from Excel, they see the spreadsheet rendered in the Answer area with all questions visible in a table format matching the original Excel structure. This provides immediate visual feedback that the import was successful and shows the complete set of questions that will be processed.

**Why this priority**: This is the foundational requirement - without rendering the spreadsheet, no live progress visualization is possible. This delivers immediate value by showing users what will be processed.

**Independent Test**: Can be fully tested by clicking "Import From Excel", selecting a spreadsheet file, and verifying that the Answer area displays a table showing all questions from the Excel file.

**Acceptance Scenarios**:

1.  **Given** the application is open with no questions loaded, **When** the user clicks "Import From Excel" and selects a valid Excel file, **Then** the Answer area displays a table rendering the spreadsheet with columns for questions and responses
2.  **Given** an Excel file with 10 questions in column A, **When** the user imports the file, **Then** the Answer area shows all 10 questions in the table with empty response cells
3.  **Given** a previously typed question in the Question field, **When** the user imports from Excel, **Then** the Question field is cleared and the Answer area switches to spreadsheet view

---

### User Story 2 - Show In-Progress Status for Active Questions (Priority: P2)

As the agent processes each question, the user sees the current question's cell highlighted in pink with a "Working..." indicator. This provides real-time feedback about which question is currently being answered, helping users understand progress and estimated completion time.

**Why this priority**: This is the core visual feedback mechanism that shows the system is actively working. Without this, users cannot tell which question is being processed.

**Independent Test**: Can be tested by starting question processing and observing that the currently active cell turns pink and displays "Working..." text.

**Acceptance Scenarios**:

1.  **Given** a spreadsheet with 5 questions imported, **When** the agent starts processing the first question, **Then** the first response cell turns pink and displays "Working..."
2.  **Given** the agent is processing question 3 of 10, **When** viewing the Answer area, **Then** only the third response cell is pink with "Working..." while others remain their default state
3.  **Given** the agent moves from question 2 to question 3, **When** the transition occurs, **Then** question 2's cell loses the pink styling and question 3's cell becomes pink with "Working..."

---

### User Story 3 - Display Completed Answers with Visual Confirmation (Priority: P2)

When the agent completes answering a question, the response text appears in the corresponding cell and the cell background changes to light green. This provides clear visual feedback about completed work and allows users to review answers as they are generated.

**Why this priority**: This completes the feedback loop by showing what has been accomplished. Users can review answers in real-time and gain confidence in the progress.

**Independent Test**: Can be tested by allowing the agent to complete at least one question and verifying the cell turns light green and contains the generated answer text.

**Acceptance Scenarios**:

1.  **Given** the agent is processing a question with pink "Working..." status, **When** the agent completes the answer, **Then** the "Working..." text is replaced with the actual answer and the cell background becomes light green
2.  **Given** a spreadsheet with 8 questions where 3 have been completed, **When** viewing the Answer area, **Then** the first 3 response cells show light green backgrounds with answer text, the 4th shows pink with "Working...", and cells 5-8 remain in default state
3.  **Given** completed answer cells, **When** the user scrolls through the spreadsheet view, **Then** all completed cells maintain their light green background and display their full answer text

---

### User Story 4 - Process All Sheets Sequentially (Priority: P1)

When an Excel file contains multiple sheets, the agent processes all sheets one by one in order. The system automatically switches the view to show the currently active sheet being processed, allowing users to see progress across the entire workbook.

**Why this priority**: This is essential for handling real-world Excel files which commonly have multiple sheets. Users need comprehensive processing across their entire workbook, not just a single sheet.

**Independent Test**: Can be tested by importing an Excel file with 3 sheets, observing that the agent processes all questions in Sheet 1, then automatically moves to Sheet 2, then Sheet 3, completing all sheets.

**Acceptance Scenarios**:

1.  **Given** an Excel file with 3 sheets (each with 5 questions), **When** processing starts, **Then** the agent processes all 5 questions in Sheet 1 first, then all 5 in Sheet 2, then all 5 in Sheet 3
2.  **Given** the agent has completed Sheet 1 and is starting Sheet 2, **When** the transition occurs, **Then** the Answer area automatically switches to display Sheet 2's spreadsheet view
3.  **Given** an Excel file with sheets named "Basic Info", "Technical", and "Advanced", **When** viewing the Answer area, **Then** sheet tabs are displayed below the spreadsheet content showing all sheet names

---

### User Story 5 - Visual Sheet Status Indicators (Priority: P2)

Sheet tabs display visual indicators showing the processing status of each sheet. The currently active sheet being processed shows a spinning spinner icon. This helps users understand which sheet is being worked on and track overall progress across multiple sheets.

**Why this priority**: This provides essential feedback for multi-sheet workbooks, helping users understand the agent's progress across the entire file and which sheet is currently active.

**Independent Test**: Can be tested by importing a multi-sheet Excel file and observing that the current sheet's tab displays a spinner icon while processing.

**Acceptance Scenarios**:

1.  **Given** an Excel file with 3 sheets where Sheet 2 is currently being processed, **When** viewing the Answer area, **Then** Sheet 2's tab displays a spinning spinner icon
2.  **Given** the agent completes all questions in Sheet 1 and moves to Sheet 2, **When** the transition occurs, **Then** Sheet 1's tab spinner disappears and Sheet 2's tab shows the spinner
3.  **Given** processing has completed on Sheets 1 and 2 but Sheet 3 is in progress, **When** viewing the sheet tabs, **Then** Sheets 1 and 2 show no spinner, and Sheet 3 shows a spinner

---

### User Story 6 - Respect User Sheet Navigation (Priority: P2)

When a user manually clicks on a sheet tab to view a different sheet, the view remains on that user-selected sheet even as the agent continues processing other sheets. This allows users to review completed answers or check upcoming questions without being forced to watch the currently processing sheet.

**Why this priority**: This respects user control and allows users to navigate freely while processing continues in the background, improving the user experience for multi-sheet workbooks.

**Independent Test**: Can be tested by starting processing on a 3-sheet file, waiting for Sheet 1 to complete and Sheet 2 to start, then clicking on Sheet 1's tab and verifying the view stays on Sheet 1 even as Sheet 2 processing continues.

**Acceptance Scenarios**:

1.  **Given** the agent is processing Sheet 2 (view auto-navigated there), **When** the user clicks on Sheet 1's tab, **Then** the view switches to Sheet 1 and remains there even as Sheet 2 processing continues
2.  **Given** the user has manually selected Sheet 3 to preview upcoming questions, **When** the agent completes Sheet 1 and moves to Sheet 2, **Then** the view remains on Sheet 3 (does not auto-navigate to Sheet 2)
3.  **Given** the agent is processing Sheet 2 with the view locked on user-selected Sheet 1, **When** Sheet 2 completes and processing moves to Sheet 3, **Then** the view still remains on Sheet 1 until the user clicks a different tab

---

### User Story 7 - Preserve Deferred Save Behavior (Priority: P1)

The Excel file is only saved to disk once all sheets and all questions have been processed and answered, not incrementally as each answer or sheet completes. This ensures data integrity and prevents partial results from being saved if processing is interrupted.

**Why this priority**: This is a critical requirement to maintain data consistency and prevent corruption of the Excel file. Users expect the file to be saved only when all processing is completely finished.

**Independent Test**: Can be tested by processing an Excel file with multiple sheets, checking the file system timestamp during processing, and verifying it only changes after all sheets are completed.

**Acceptance Scenarios**:

1.  **Given** an Excel file with 2 sheets being processed, **When** Sheet 1 is fully completed (all cells light green), **Then** the Excel file on disk has not been modified (original timestamp unchanged)
2.  **Given** processing is in progress on Sheet 2 question 7 of 10, **When** the user closes the application or cancels processing, **Then** no answers from any sheet are saved to the Excel file
3.  **Given** all questions in all sheets have been completed (all cells light green across all sheets), **When** the final processing finishes, **Then** the Excel file is saved once with all answers from all sheets included

---

## Clarifications

### Session 2025-10-23

*   Q: What happens when the Excel file contains merged cells or complex formatting? → A: The UI should render colors and basic font details (bold, italic, regular) but not different fonts or fancier things. If a cell contains a dropdown box then it should just be rendered as a normal cell. If cells are merged, they ideally should be rendered as merged cells, just as they would look in Excel.
*   Q: Do we need to create new .xlsx test files? → A: No, necessary test files already exist in /tests directory
*   Q: What testing strategy for Azure AI Foundry integration? → A: Both mock tests (simulating Azure output) and live tests (actual Azure connection) required. Mock tests enable asynchronous GitHub Copilot work. Existing test patterns already present in tests directory.
*   Q: What happens if processing is interrupted (crash, user cancellation) before all questions complete? → A: Crash: unrecoverable. User exit: stop processing, close window, cleanup agents from Azure AI Foundry, save nothing.
*   Q: What happens when one sheet has 5 questions and another has 100 questions (significantly different sizes)? → A: Scrollbar in spreadsheet renderer. Blank cells for sheets with fewer questions than visible area.
*   Q: What happens when the Answer area needs to display a spreadsheet with hundreds of rows? → A: Scrollbars like normal spreadsheets. Auto-scroll 3 cells down if current question off-screen.
*   Q: How does the system handle Excel files where questions and answers are in non-standard columns (not A and B)? → A: Use AI model to detect question/answer/documentation columns from headers. Determine if sheet is a questionnaire. Render non-questionnaire sheets but skip agent processing.
*   Q: What happens if the user tries to import a new Excel file while processing is already in progress? → A: Stop processing, stop agents, unload current document, load new file, start processing new file.
*   Q: What happens when an Excel file has hidden sheets? → A: Don't show hidden sheets in UI. Include hidden sheets verbatim when saving.
*   Q: How does the system handle sheet names with special characters or very long names in the tab display? → A: Special characters render as default box. Long names truncated with "..." before overflow.
*   Q: What happens if a user rapidly clicks between sheet tabs during processing? → A: System renders whichever sheet user clicked on.

---

### Edge Cases

*   How does the system handle very long answer text that exceeds typical cell display width? (Cells should support horizontal scrolling or text wrapping as appropriate for the UI component)

## Requirements _(mandatory)_

### Functional Requirements

*   **FR-001**: System MUST render the imported Excel spreadsheet in the Answer area as a table with columns for questions and responses
*   **FR-002**: System MUST display each response cell with a pink background and "Working..." text while the agent is actively processing that question
*   **FR-003**: System MUST update each response cell with the generated answer text and change the background to light green when the agent completes that question
*   **FR-004**: System MUST maintain visual distinction between three cell states: pending (default), in-progress (pink with "Working..."), and completed (light green with answer text)
*   **FR-005**: System MUST only save the Excel file to disk after all sheets and all questions have been processed, not incrementally during processing
*   **FR-006**: Users MUST be able to view all imported questions in the spreadsheet view within the Answer area
*   **FR-007**: System MUST clear any existing content in the Answer area when switching to spreadsheet view after Excel import
*   **FR-008**: System MUST maintain the original question order from the Excel file in the spreadsheet view
*   **FR-009**: System MUST handle scrolling for spreadsheets with more questions than can fit in the visible Answer area
*   **FR-009a**: System MUST provide scrollbars in the spreadsheet renderer for both vertical and horizontal scrolling
*   **FR-009b**: System MUST render blank cells for sheets with fewer questions than the visible area (matching normal spreadsheet behavior)
*   **FR-009c**: System MUST automatically scroll the spreadsheet view down 3 cells when the currently processing question is off-screen and the user has not manually interacted with the canvas
*   **FR-010**: System MUST preserve cell formatting (colors, status indicators) when users scroll through the spreadsheet view
*   **FR-010a**: System MUST render basic Excel formatting including cell colors, bold, italic, and regular font styles
*   **FR-010b**: System MUST render merged cells as merged (spanning multiple columns/rows) matching Excel appearance
*   **FR-010c**: System SHOULD render Excel dropdown boxes as normal cells (no dropdown functionality preserved)
*   **FR-010d**: System MAY skip rendering advanced formatting (custom fonts, gradients, borders beyond basic)
*   **FR-011**: System MUST process all sheets in an Excel file sequentially in their original order
*   **FR-012**: System MUST display sheet tabs below the spreadsheet content showing all sheet names from the Excel file
*   **FR-013**: System MUST display a spinning spinner icon on the sheet tab for the sheet currently being processed
*   **FR-014**: System MUST automatically switch the view to the currently active sheet being processed when processing moves to a new sheet
*   **FR-015**: System MUST stop auto-navigation to processing sheets once a user manually clicks on a sheet tab
*   **FR-016**: System MUST allow users to manually navigate between sheets by clicking sheet tabs while processing continues
*   **FR-017**: System MUST maintain the user's selected sheet view when they manually click a sheet tab, even as processing continues on other sheets
*   **FR-018**: System MUST reuse existing spreadsheet rendering components/libraries available in the Python UI framework
*   **FR-019**: System MUST render sheet tabs in the same visual style as Excel (horizontally aligned below the spreadsheet content)
*   **FR-020**: System MUST use the Azure AI Foundry model to analyze column headers and determine which columns contain questions, answers, and documentation
*   **FR-020a**: System MUST use the AI model to determine whether each sheet is a questionnaire (has at least question and answer columns)
*   **FR-020b**: System MUST render non-questionnaire sheets but skip agent processing on them
*   **FR-020c**: System MUST NOT assume questions are in column A or answers are in column B
*   **FR-021**: When user exits the application during processing, system MUST stop all processing, close the window, cleanup all agents from Azure AI Foundry, and save nothing
*   **FR-021a**: System MUST delete all agents from Azure AI Foundry when user exits during processing
*   **FR-021b**: System MUST NOT save any partial results when user exits during processing
*   **FR-022**: When user imports a new Excel file during active processing, system MUST stop current processing, stop all agents, unload current document, load new file, and start processing the new file
*   **FR-023**: System MUST NOT display hidden sheets in the UI
*   **FR-023a**: System MUST include hidden sheets verbatim when saving the final Excel file
*   **FR-024**: System MUST render special characters in sheet names as default box characters if they cannot be displayed
*   **FR-024a**: System MUST truncate long sheet names with "..." before they overflow the tab display area
*   **FR-025**: System MUST render the sheet corresponding to rapid user clicks between sheet tabs

### Key Entities

*   **SpreadsheetView**: Represents the rendered table in the Answer area showing questions and their response status/content for a single sheet
*   **QuestionCell**: Represents a single row in the spreadsheet containing the question text (read-only display)
*   **ResponseCell**: Represents a single response cell that can be in one of three states (pending, in-progress, completed) with corresponding visual styling
*   **ProcessingStatus**: Tracks the current state of each question (not started, processing, completed) to drive the visual rendering
*   **SheetTab**: Represents a clickable tab for navigating between sheets, displaying the sheet name and optional spinner icon
*   **WorkbookView**: Represents the complete multi-sheet view containing the active SpreadsheetView and all SheetTabs
*   **SheetProcessingState**: Tracks whether a sheet is not started, in progress (showing spinner), or completed
*   **NavigationLock**: Tracks whether the user has manually selected a sheet, preventing auto-navigation to the currently processing sheet
*   **ColumnMapping**: Contains the detected question, answer, and documentation column indices for a sheet as determined by AI model analysis
*   **SheetType**: Indicates whether a sheet is a questionnaire (has question/answer columns) or non-questionnaire (render only, no processing)
*   **AgentCleanupManager**: Handles deletion of all agents from Azure AI Foundry when user exits during processing

## Success Criteria _(mandatory)_

### Measurable Outcomes

*   **SC-001**: Users can see the complete imported spreadsheet rendered in the Answer area within 2 seconds of selecting the Excel file
*   **SC-002**: Visual status updates (pink "Working..." and light green completed cells) appear within 500 milliseconds of the agent state changing
*   **SC-003**: Users can correctly identify which question is currently being processed by visual inspection (pink cell) 100% of the time during processing
*   **SC-004**: All completed answers are visible in light green cells with full text displayed before the Excel file is saved
*   **SC-005**: System successfully handles spreadsheets with up to 100 questions per sheet and up to 10 sheets without performance degradation in the Answer area rendering
*   **SC-006**: Users can distinguish between pending, in-progress, and completed questions by color alone (accessibility via visual indicators)
*   **SC-007**: Zero instances of partial data being saved to Excel files (file is only modified once when all sheets and processing completes)
*   **SC-008**: Users can identify which sheet is currently being processed by visual inspection (spinner icon on tab) 100% of the time
*   **SC-009**: Sheet tab navigation responds to user clicks within 200 milliseconds
*   **SC-010**: View remains on user-selected sheet 100% of the time after manual navigation, even as processing continues on other sheets
*   **SC-011**: System automatically switches to the next sheet within 1 second of completing the previous sheet (when no user navigation lock exists)

## Assumptions

*   The Answer area currently exists as a component that can be modified to display different content types (transitioning from single answer display to table view)
*   The Excel import functionality already exists and provides access to the questions from all sheets in the spreadsheet
*   The agent processing system can expose status change events or hooks that the UI can subscribe to for real-time updates
*   The existing UI framework (tkinter) supports dynamic table rendering with per-cell styling and tab navigation components
*   Python UI ecosystem includes existing spreadsheet rendering components/libraries that can be reused (e.g., tkinter Treeview, custom widgets, or third-party libraries)
*   Users are running the application on displays with sufficient resolution to view spreadsheet tables effectively (minimum 1024x768 assumed)
*   The typical questionnaire contains between 5-50 questions per sheet (design optimized for this range)
*   Excel files may have questions and answers in any columns; the AI model will detect the correct columns from headers
*   Most Excel files will have 1-5 sheets, with occasional files having up to 10 sheets
*   Sheet names may contain special characters or be very long; the UI will handle truncation and rendering fallbacks
*   Some Excel files may contain hidden sheets that need to be preserved but not displayed
*   Some sheets may not be questionnaires and should be rendered but not processed
*   Test Excel files for various scenarios already exist in the /tests directory
*   Testing infrastructure includes both mock tests (simulating Azure AI Foundry responses) and live tests (actual Azure connections) following existing patterns in tests directory, enabling asynchronous development by GitHub Copilot without Azure credentials