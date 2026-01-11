# Web Interface Clarifications

**Date**: 2026-01-11
**Reference**: `specs/002-live-excel-processing/live_excel_output.png`

This document clarifies how the web interface should work, superseding any conflicting specifications in other documents.

---

## 1. User Interface Layout

The interface should match the desktop GUI layout from `live_excel_output.png`:

### Left Sidebar
- **Context** input field (default: "Microsoft Azure AI")
- **Character Limit** input field (default: 2000)
- **Maximum Retries** input field (default: 10)
- **Question** textarea for single question input
- **Ask!** button - submits the single question
- **Import From Excel** button - opens file picker to load a spreadsheet

### Main Area
- In **Ask Question mode**: Shows the response to the current question
- In **Spreadsheet mode**: Shows the Question/Response grid with live updates

### Status Bar (Bottom)
- Shows current status: "Ready", "Working...", "Processing row X of Y", "Complete", errors, etc.
- **NOT** shown in the left sidebar - must be at the bottom of the window

### What to Remove
- No tabs for "Ask Question" / "Spreadsheet Processing"
- No "Configuration" or "Status" panels in the sidebar
- No column mapping UI visible by default

---

## 2. Mode Switching

The interface operates in two modes, switching automatically based on user action:

### Ask Question Mode (Default)
- Active when the application starts
- Active when no spreadsheet is loaded
- User enters a question in the Question textarea
- User clicks "Ask!" to submit
- Response displays in the main area
- Status bar shows: "Ready" → "Working..." → "Ready"

### Spreadsheet Mode
- Activated automatically when user clicks "Import From Excel" and selects a valid file
- Main area transforms to show the Question/Response grid
- Processing begins automatically (if auto-mapping succeeds)
- Status bar shows progress: "Processing row 1 of 5..."
- "Import From Excel" button remains available to load a different file

---

## 3. Spreadsheet Loading & Auto-Mapping

When a spreadsheet is loaded:

### Step 1: Parse the File
- Read the Excel file (.xlsx, .xls)
- Identify all sheets and their columns

### Step 2: Auto-Map Columns
Attempt to automatically identify:
- **Question column**: Look for columns named "Question", "Query", "Ask", "Q", or similar
- **Response/Answer column**: Look for columns named "Response", "Answer", "Reply", "A", or similar
- **Documentation column** (optional): Look for columns named "Documentation", "Docs", "Sources", "References", or similar

### Step 3: Evaluate Auto-Mapping Success
Auto-mapping is **successful** if:
- Question column is identified with high confidence
- Answer column is identified with high confidence

Auto-mapping is **unsuccessful** if:
- Question column cannot be identified
- Answer column cannot be identified
- Multiple ambiguous matches exist

### Step 4a: If Auto-Mapping Succeeds
1. Do NOT show the column mapping interface
2. Immediately switch to Spreadsheet mode
3. Begin processing automatically
4. Status bar: "Auto-mapped columns. Processing row 1 of X..."

### Step 4b: If Auto-Mapping Fails
1. Show the column mapping interface (modal or inline)
2. Let user manually select: Worksheet, Question Column, Answer Column, Context Column (optional)
3. User clicks "Start Processing" to begin
4. Hide mapping interface and switch to Spreadsheet mode

---

## 4. Processing Behavior

### Starting Processing
- Begins automatically after successful auto-mapping
- Or begins when user clicks "Start Processing" after manual mapping

### During Processing
- Process questions sequentially (row by row)
- Status bar updates: "Processing row X of Y..."
- Current row being processed is highlighted (pink/red background with "Working..." indicator)
- Completed rows show their response text
- Grid scrolls to keep the current row visible

### Real-Time Updates (SSE)
The following events are sent via Server-Sent Events:
- `processing_started`: Processing has begun
- `row_started`: Started processing a specific row
- `row_completed`: Row finished with answer text
- `row_error`: Error processing a row
- `processing_completed`: All rows finished
- `processing_stopped`: User stopped processing

### Stopping Processing
- User can click "Stop" button (or re-use "Import From Excel" area for stop control)
- Current row completes, then processing halts
- Status bar: "Stopped at row X of Y"

### Completion
- Status bar: "Complete. Processed X rows."
- "Download Results" becomes available

---

## 5. Error Handling

### File Load Errors
- Invalid file format → Status bar: "Error: Invalid file format. Please select an .xlsx or .xls file."
- Corrupted file → Status bar: "Error: Could not read file."
- Empty file → Status bar: "Error: File contains no data."

### Auto-Mapping Errors
- Cannot identify columns → Show mapping interface with message: "Could not auto-detect columns. Please select manually."

### Processing Errors
- Single row error → Highlight row in red, show error in Response cell, continue to next row
- API error → Status bar: "Error: [message]. Retrying..." (up to max retries)
- Fatal error → Status bar: "Error: [message]. Processing stopped."

### Connection Errors
- SSE disconnect → Status bar: "Connection lost. Reconnecting..."
- Reconnect success → Resume updates, status bar: "Reconnected."

---

## 6. Session Management

### Session Creation
- Session created automatically when page loads
- Session ID displayed subtly (not prominently)
- Session persists across page refreshes (stored in localStorage)

### Session State
Each session maintains:
- Current mode (Ask Question / Spreadsheet)
- Configuration (context, char limit, max retries)
- Loaded spreadsheet data (if any)
- Processing state (row index, status)
- SSE connection

### Session Cleanup
- Sessions expire after 30 minutes of inactivity
- Expired sessions are cleaned up server-side
- Client detects expired session and creates new one

---

## 7. Visual Design

### Color Scheme (Microsoft Foundry-inspired)
- Primary blue: `#0078D4`
- Success green: `#107C10`
- Error red: `#D13438`
- Warning yellow: `#FFB900`
- Background: `#F3F2F1`
- Surface: `#FFFFFF`

### Grid Styling
- Header row: Blue background (`#0078D4`), white text
- Completed rows: White background, normal text
- Processing row: Pink/light red background (`#FFECEC`), "Working..." indicator with spinner
- Error rows: Light red background with error text in Response cell

### Status Bar
- Fixed to bottom of window
- Gray background
- Left-aligned status text
- Shows connection indicator (green dot = connected)

---

## 8. Implementation Changes Required

Based on these clarifications, the following changes are needed to the current implementation:

### index.html
- Remove tab navigation
- Restructure layout: sidebar with inputs + buttons, main area for content
- Add status bar at bottom
- Remove Configuration/Status panels from sidebar

### styles.css
- Update layout to match reference design
- Add status bar styling
- Add row highlighting for processing state
- Remove tab-related styles

### app.js
- Remove tab switching logic
- Implement mode switching (Ask Question ↔ Spreadsheet)
- Auto-start processing on successful auto-map
- Update status bar instead of status panel

### spreadsheet.js
- Add row highlighting during processing
- Implement "Working..." indicator in active row
- Auto-scroll to current row

### app.py
- Improve auto-mapping confidence scoring
- Return auto-mapping success/failure flag
- Possibly auto-start processing endpoint

---

## 9. Summary of Key Behaviors

| Scenario | Behavior |
|----------|----------|
| Page loads | Ask Question mode, status bar shows "Ready" |
| User clicks "Ask!" | Submit question, show response in main area |
| User clicks "Import From Excel" | Open file picker |
| File selected, auto-map succeeds | Switch to Spreadsheet mode, begin processing immediately |
| File selected, auto-map fails | Show column mapping UI, wait for user to configure |
| Processing in progress | Grid shows progress, current row highlighted, status bar updates |
| User stops processing | Complete current row, halt, show "Stopped" status |
| Processing completes | Show "Complete" status, enable download |

---

## 10. Implementation Status

**Last Updated**: 2026-01-11

### ✅ Completed Items

#### UI Implementation (All Complete)
- [x] **index.html**: Removed tab navigation, restructured layout with sidebar + main area, added status bar at bottom
- [x] **styles.css**: Added status bar styling, row highlighting (`.row-processing` pink, `.row-error` red), "Working..." indicator with spinner
- [x] **app.js**: Removed tab switching, implemented `switchMode()` for Ask Question ↔ Spreadsheet, auto-start on successful auto-map, status bar updates via `updateStatusBar()`
- [x] **spreadsheet.js**: Added row highlighting (`setRowProcessing()`, `setRowError()`), "Working..." indicator in answer column, auto-scroll to current row

#### Backend Implementation (Partial)
- [x] **app.py**: Enhanced `_identify_columns()` with pattern matching and confidence scoring, returns `auto_map_success` flag
- [x] **models.py**: Added `auto_map_success: bool` field to `ColumnSuggestions`
- [x] **azure_auth.py**: Fixed credential passing to `AzureAIAgentClient`, set `AZURE_AI_PROJECT_ENDPOINT` from existing config

#### Configuration & Dependencies
- [x] **requirements.txt**: Added `opentelemetry-exporter-otlp` dependency
- [x] Fixed `ConfigurationManager` method calls (replaced `get_azure_config()` with individual methods)

### ✅ Fixed Issues

#### Backend: Link Checker Agent Error (FIXED)
**Error**: `Cannot access project_client from azure_client`

**Fix Applied**:
1. Added `get_project_client()` function to `src/utils/azure_auth.py`
2. Updated `create_agent_coordinator()` to accept and pass `project_client`
3. Updated `LinkCheckerExecutor` to receive `project_client` directly instead of trying to extract it from `azure_client`
4. Updated both call sites in `src/web/app.py` to get and pass `project_client`

### ❌ New Issues (Identified During Testing)

#### Issue: Row Count Shows Retries Instead of Actual Rows
**Observed**: Status bar shows "Complete. Processed 10 rows." when the spreadsheet only has 5 questions.

**Root Cause**: The counter is incrementing for each agent iteration/retry attempt rather than counting actual spreadsheet rows completed.

**Expected Behavior**:
- Status should show "Processing row X of Y" where Y is the actual number of rows in the spreadsheet
- "Complete. Processed X rows." should show the actual number of rows, not retry attempts
- A row should only be counted as "processed" when all agent iterations are complete (success or final failure)

**Affected Files**:
- `src/web/app.py` - `_process_spreadsheet()` function row counting logic

#### Issue: Sequential Processing Instead of Parallel (3 Agent Sets)
**Observed**: The web interface processes questions one at a time (sequentially), but the Python desktop GUI uses 3 parallel agent sets working on 3 cells simultaneously.

**Reference**: This was already working in the Python frontend (Issue #54 - fixed). The web backend should reuse the `ParallelExcelProcessor` class from `src/excel/processor.py`.

**Required Changes**:
1. Create 3 agent coordinators instead of 1 in `_process_spreadsheet()`
2. Use `ParallelExcelProcessor` instead of sequential loop
3. Update SSE events to show 3 "Working..." indicators simultaneously
4. The UI already supports multiple highlighted rows (CSS is ready)

**Affected Files**:
- `src/web/app.py` - `_process_spreadsheet()` function needs to use `ParallelExcelProcessor`
- `src/web/static/app.js` - May need updates for multiple concurrent "Working..." indicators

### 🔄 Not Yet Tested
- Stop processing functionality
- Download results functionality
- Manual column mapping (when auto-map fails)
- Multi-sheet workbooks
- SSE reconnection after disconnect

---

## 11. Command Line Options

### `--no-browser` Switch

When running the web interface with `python run_app.py --web`, the application should support a `--no-browser` flag:

```bash
python run_app.py --web --port 8080 --no-browser
```

**Behavior:**
- `--web` (default): Starts web server AND automatically opens browser tab to the UI
- `--web --no-browser`: Starts web server only, does NOT open browser tab

**Use Cases:**
- Automated testing with Playwright (prevents random browser popups)
- CI/CD pipelines
- Running as a background service
- When the agent/test framework will open its own browser instance

**Implementation:**
- Add `--no-browser` argument to `run_app.py` argument parser
- Only call `webbrowser.open()` when `--no-browser` is NOT set
