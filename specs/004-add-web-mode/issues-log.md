# Web Interface Testing Issues Log

**Date**: 2026-01-10
**Test File**: `tests/fixtures/excel/single_sheet_5_questions.xlsx`

## Testing Session

---

### Issue 1: Module not found when running with system Python
**Status**: FIXED
**Error**: `ModuleNotFoundError: No module named 'agent_framework_azure_ai'`
**Cause**: The `agent-framework-azure-ai` package requires Python 3.10+, but .venv uses Python 3.9
**Fix**: Created new virtualenv `.venv312` with Python 3.12.12 from /opt/homebrew/bin/python3.12
**Action**: Use `.venv312/bin/python` instead of `.venv/bin/python`

---

### Issue 2: Missing .env configuration
**Status**: FIXED
**Error**: Configuration errors when starting server
**Fix**: Copied .env file from OneDrive temp directory and added missing `BROWSER_AUTOMATION_CONNECTION_ID=BrowserAutomation`

---

### Issue 3: Grid not displaying actual data from Excel file
**Status**: FIXED
**Error**: Grid showed 5 rows but Question/Response columns were empty
**Cause**: `SpreadsheetUploadResponse` model didn't include actual row data, only metadata (columns, row_count, sheets). The `initializeSpreadsheetGrid()` function created empty placeholder rows.
**Fix**:
1. Added `data: Dict[str, List[Dict[str, str]]]` field to `SpreadsheetUploadResponse` in `models.py`
2. Created `_get_sheet_data()` function in `app.py` to extract row data from Excel
3. Updated upload endpoint to populate the `data` field
4. Updated `spreadsheet.js` to use actual data from response instead of creating placeholders

---

### Issue 4: AG Grid deprecation warnings
**Status**: FIXED
**Error**: Console warnings about deprecated `new agGrid.Grid()` API
**Fix**: Changed to modern `agGrid.createGrid(gridDiv, gridOptions)` API in `spreadsheet.js`

---

### Issue 5: AG Grid enterprise-only features causing warnings
**Status**: FIXED
**Error**: Warnings about `enableRangeSelection` and `enableClipboard` requiring enterprise module
**Fix**: Removed enterprise-only features from grid options:
- Removed `enableRangeSelection: true`
- Removed `enableClipboard: true`
- Removed `processCellForClipboard` callback
- Removed `gridColumnApi` (no longer returned by createGrid)
- Updated `exportGridToClipboard()` to manually copy data using `navigator.clipboard`
- Updated keyboard shortcuts to remove `clearRangeSelection()` call

---

### Issue 6: Pydantic validation error for rowIndex
**Status**: FIXED
**Error**: `Input should be a valid string [type=string_type, input_value=0, input_type=int]`
**Cause**: `rowIndex` was being set as integer but model expects `Dict[str, str]` (all string values)
**Fix**: Changed `row_dict = {"rowIndex": row_idx}` to `row_dict = {"rowIndex": str(row_idx)}` in `_get_sheet_data()`

---

### Issue 7: Missing favicon causing 404 error
**Status**: FIXED
**Error**: `Failed to load resource: the server responded with a status of 404 (Not Found) @ /favicon.ico`
**Fix**:
1. Created `src/web/static/favicon.svg` with a simple "Q" icon in Microsoft blue
2. Added `/favicon.ico` route in `app.py` to serve the SVG file
3. Added `<link rel="icon" type="image/svg+xml" href="/favicon.ico">` to `index.html`

---

## Test Results Summary

**All automated Playwright tests passed:**
- Health endpoint check: PASS
- Page load: PASS
- Session creation: PASS
- Form elements visibility: PASS
- Tab navigation: PASS
- File upload and column selection: PASS
- Grid data display: PASS (questions now show correctly)

**Screenshots saved:**
- `specs/004-add-web-mode/test-screenshot.png` - Initial test
- `specs/004-add-web-mode/grid-data-fixed.png` - After fixing data display
- `specs/004-add-web-mode/grid-with-data.png` - Full page with grid showing all 5 questions

**Sample questions displayed correctly:**
1. What is artificial intelligence?
2. How does machine learning work?
3. What are the benefits of cloud computing?
4. Explain natural language processing.
5. What is the difference between AI and ML?
