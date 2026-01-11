# Research: Web Interface Mode

**Date**: January 10, 2026  
**Feature**: 004-add-web-mode  
**Phase**: 0 (Outline & Research)

## Overview

This document consolidates research findings for implementing a web interface mode for the QuestionnaireAgent application, focusing on technology selection and best practices for FastAPI web servers, modern spreadsheet components, Server-Sent Events, browser automation testing, and Microsoft Foundry design patterns.

## 1. Web Framework Selection: FastAPI

### Decision
Use **FastAPI** as the web framework with **Uvicorn** as the ASGI server.

### Rationale
- **Async Support**: Native async/await support essential for Server-Sent Events and concurrent session handling
- **Type Safety**: Pydantic integration provides request/response validation matching existing data_types.py patterns
- **Static Files**: Built-in StaticFiles middleware for serving frontend assets without additional dependencies
- **Performance**: High-performance ASGI framework suitable for real-time updates and multiple concurrent sessions
- **Python Ecosystem**: Seamless integration with existing Python 3.11+ codebase and dependencies
- **Development Velocity**: Automatic OpenAPI documentation, minimal boilerplate, clear patterns for separation of concerns

### Alternatives Considered
- **Flask**: Synchronous by default, would require Flask-SSE extension, more complex async handling
- **Django**: Over-engineered for localhost single-user scenario, includes unnecessary ORM and admin features
- **aiohttp**: Lower-level, requires more boilerplate for common web patterns

### Implementation Notes
- FastAPI app in `src/web/app.py` with route definitions for: `/` (index), `/api/question`, `/api/spreadsheet/upload`, `/api/spreadsheet/process`, `/api/sse`
- Mount `src/web/static/` directory using `app.mount("/static", StaticFiles(directory="static"), name="static")`
- Use `@app.post()` decorators with Pydantic models for request/response schemas
- Uvicorn server launched from `run_app.py` when `--web` flag is present: `uvicorn.run(app, host="127.0.0.1", port=8080)`

## 2. Spreadsheet Component Selection

### Decision
Use **ag-Grid Community Edition** for the web spreadsheet component.

### Rationale
- **Performance**: Handles 10,000+ rows with virtual scrolling and 60fps rendering
- **Feature Complete**: Built-in sorting, filtering, cell selection, copy/paste, fixed headers
- **Free License**: Community edition is free for use (MIT license)
- **Active Development**: Well-maintained with extensive documentation and examples
- **Excel-Like UX**: Familiar interaction patterns for users transitioning from desktop Excel processing
- **API Simplicity**: Clear JavaScript API for programmatic cell updates during real-time processing

### Alternatives Considered
- **Handsontable**: Excellent Excel compatibility but requires paid license for production use ($990/year)
- **jExcel/jspreadsheet**: Lightweight but limited features (no virtual scrolling for large datasets)
- **Custom HTML Table**: Would require significant development time to match professional spreadsheet UX

### Implementation Notes
- Include ag-Grid Community from CDN in `index.html`: `<script src="https://cdn.jsdelivr.net/npm/ag-grid-community/dist/ag-grid-community.min.js"></script>`
- Initialize grid with: `new agGrid.Grid(container, { columnDefs, rowData, enableRangeSelection: true, animateRows: true })`
- Update cells programmatically during SSE processing: `gridApi.getRowNode(rowId).setDataValue('Answer', newAnswer)`
- Export to Excel using ag-Grid CSV export then convert server-side, or implement download with original Excel file + updates

## 3. Server-Sent Events (SSE) Implementation

### Decision
Implement real-time updates using **Server-Sent Events (SSE)** with FastAPI StreamingResponse.

### Rationale
- **Simplicity**: Unidirectional server-to-client push matches requirements (no client-to-server messages during processing)
- **Browser Support**: Native EventSource API in all modern browsers, no libraries required
- **Reconnection**: Automatic reconnection handling built into browser EventSource with exponential backoff
- **Specification Match**: Directly implements clarified requirement for server push updates
- **HTTP/1.1 Compatible**: Works over standard HTTP without WebSocket upgrade handshake
- **FastAPI Integration**: Clean async generator pattern with StreamingResponse

### Alternatives Considered
- **WebSockets**: Bidirectional capability unnecessary for this use case, more complex error handling
- **Long Polling**: Higher latency (1-2s), more server load, complex state management between polls
- **Short Polling**: Inefficient, increased latency, unnecessary network traffic

### Implementation Notes
```python
from fastapi.responses import StreamingResponse
from asyncio import Queue

async def event_stream(session_id: str):
    queue = sse_manager.get_queue(session_id)
    async for message in queue:
        yield f"data: {json.dumps(message)}\n\n"

@app.get("/api/sse/{session_id}")
async def sse_endpoint(session_id: str):
    return StreamingResponse(event_stream(session_id), media_type="text/event-stream")
```

Client-side:
```javascript
const eventSource = new EventSource(`/api/sse/${sessionId}`);
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateUI(data);
};
```

## 4. Browser Automation Testing: Playwright

### Decision
Use **Playwright** for end-to-end browser automation testing.

### Rationale
- **Multi-Browser**: Single API for Chromium, Firefox, WebKit (matches FR-021 cross-browser requirement)
- **Modern Architecture**: Auto-waits for elements, built-in retry logic, eliminates flaky tests
- **Python API**: Native Python bindings integrate seamlessly with existing pytest infrastructure
- **Performance**: Parallel test execution, fast browser context isolation
- **Microsoft Support**: Maintained by Microsoft, aligns with Azure/Microsoft technology stack
- **Screenshots/Videos**: Automatic capture on failure for debugging (matches FR-021 requirement)

### Alternatives Considered
- **Selenium**: Older architecture, more flaky tests, slower execution, requires explicit waits
- **Cypress**: JavaScript-only, would require separate test stack outside Python ecosystem
- **Puppeteer**: Chromium-only, lacks cross-browser testing capability

### Implementation Notes
- Install: `pip install playwright` and `playwright install chromium firefox webkit`
- Pytest integration: Use `pytest-playwright` plugin for fixtures
- Test structure:
```python
def test_single_question(page):
    page.goto("http://localhost:8080")
    page.fill("#question-input", "What is Azure?")
    page.click("#submit-button")
    page.wait_for_selector("#answer-result")
    assert "cloud platform" in page.text_content("#answer-result")
```
- Run tests: `pytest tests/web/playwright/ --browser=chromium --browser=firefox --browser=webkit`

## 5. Microsoft Foundry Design System

### Decision
Implement custom CSS inspired by Microsoft Foundry design patterns rather than using a full framework.

### Rationale
- **Specificity**: Exact visual match to Foundry screenshot requires custom implementation
- **Lightweight**: No framework overhead for a localhost application with limited screens
- **Flexibility**: Full control over typography, spacing, shadows, colors without fighting framework defaults
- **Learning Curve**: Simpler than learning Fluent UI React or Fluent UI Web Components
- **Maintenance**: Fewer dependencies, no framework version migration concerns

### Alternatives Considered
- **Fluent UI React**: Requires React build system, heavy for simple static page serving
- **Fluent UI Web Components**: Still in preview, API instability risk
- **Tailwind CSS**: Utility-first classes don't match Foundry's component-based patterns

### Implementation Notes
Design tokens from Microsoft Foundry analysis:
- **Typography**: Segoe UI font family, font-weights: 400 (regular), 600 (semibold), sizes: 14px body, 20px heading, 16px subheading
- **Colors**: Primary blue: #0078D4, hover: #106EBE, neutral-0: #FFFFFF, neutral-10: #F3F2F1, neutral-90: #323130
- **Spacing**: 4px base unit, common: 8px, 12px, 16px, 24px, 32px
- **Shadows**: Depth-4: `0 1.6px 3.6px rgba(0,0,0,.13), 0 0.3px 0.9px rgba(0,0,0,.11)`, Depth-8: `0 3.2px 7.2px rgba(0,0,0,.13), 0 0.6px 1.8px rgba(0,0,0,.11)`
- **Border-radius**: 2px for buttons/inputs, 4px for cards/modals
- **Transitions**: `transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1)` for hover states

CSS structure in `styles.css`:
```css
:root {
    --primary: #0078D4;
    --spacing-xs: 4px;
    --shadow-depth4: 0 1.6px 3.6px rgba(0,0,0,.13);
    --radius-sm: 2px;
}
```

## 6. Session Management Strategy

### Decision
Use in-memory dictionary with UUID-based session IDs, no persistent storage.

### Rationale
- **Simplicity**: Matches localhost single-user scenario, no database overhead
- **Performance**: O(1) session lookup, minimal latency
- **Clarification Alignment**: Sessions persist indefinitely (no timeout) until server shutdown
- **Independence**: Each tab gets unique UUID, fully independent processing state
- **Sufficient Scale**: Handles 5+ concurrent tabs easily with in-memory storage

### Alternatives Considered
- **Redis**: Over-engineered for localhost, adds external dependency
- **SQLite**: Unnecessary persistence for localhost scenario where server restart is acceptable
- **Browser Cookies**: Insufficient for storing processing state and spreadsheet data

### Implementation Notes
```python
import uuid
from typing import Dict, Any

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "workbook": None,
            "processing_job": None,
            "config": {"context": "Microsoft Azure AI", "char_limit": 2000}
        }
        return session_id
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self.sessions.get(session_id)
```

## 7. Browser Auto-Open Implementation

### Decision
Use Python's `webbrowser` module to automatically open default browser on startup.

### Rationale
- **Cross-Platform**: Works on Windows, macOS, Linux without platform-specific code
- **Standard Library**: No additional dependencies required
- **User Preference**: Respects user's default browser setting
- **Timing Control**: Can delay open until server is fully started and health check passes

### Implementation Notes
```python
import webbrowser
import time
import requests

def launch_web_mode(port=8080):
    # Start FastAPI server in background thread
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    
    # Wait for server to be ready
    url = f"http://127.0.0.1:{port}"
    for _ in range(30):  # 30 second timeout
        try:
            requests.get(f"{url}/health", timeout=1)
            break
        except:
            time.sleep(1)
    
    # Open browser
    webbrowser.open(url)
    
    # Keep main thread alive
    server_thread.join()
```

## 8. Excel File Upload and Processing

### Decision
Use FastAPI's `UploadFile` with temporary storage in OS temp directory, process with existing `excel.loader` and `excel.processor` modules.

### Rationale
- **Reusability**: Leverages existing Excel processing logic without duplication
- **Memory Efficiency**: Streaming upload for large files, temp storage prevents memory bloat
- **Security**: Automatic cleanup of temp files, validates Excel format before processing
- **Integration**: Existing `ColumnIdentifier` for auto-selecting columns works unchanged

### Implementation Notes
```python
from fastapi import UploadFile, File
import tempfile
import shutil

@app.post("/api/spreadsheet/upload")
async def upload_spreadsheet(session_id: str, file: UploadFile = File(...)):
    # Validate Excel format
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Invalid file format")
    
    # Save to temp file
    temp_path = tempfile.mktemp(suffix='.xlsx')
    with open(temp_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Load with existing loader
    loader = ExcelLoader()
    workbook_data = loader.load(temp_path)
    
    # Store in session
    session = session_manager.get_session(session_id)
    session['workbook'] = workbook_data
    session['temp_file'] = temp_path
    
    return {"sheets": workbook_data.sheet_names}
```

## 9. Azure Credential Re-Authentication

### Decision
Reuse existing `utils.azure_auth.test_authentication()` with error handling that triggers browser-based credential refresh.

### Rationale
- **Consistency**: Same authentication flow as desktop version
- **No Duplication**: Existing DefaultAzureCredential logic handles token refresh
- **Clarification Match**: Azure auth is separate from web session lifecycle
- **User Experience**: Clear error message prompts browser-based re-auth when token expires

### Implementation Notes
- Wrap agent calls in try/except for Azure authentication errors
- On `AuthenticationError`, return 401 response to client
- Client displays message: "Azure credentials expired. Please re-authenticate." with button
- Button triggers `/api/reauth` endpoint that calls `test_authentication()` with interactive flow
- Desktop browser window opens for Azure login, returns success/failure to web interface

## 10. Real-Time Progress Updates

### Decision
Implement progress tracking with asyncio queues per session, push to clients via SSE.

### Rationale
- **Async Safety**: asyncio.Queue is thread-safe for async contexts
- **Per-Session Isolation**: Independent queues ensure tab independence
- **Backpressure Handling**: Queue size limits prevent memory bloat if client disconnects
- **Clean Integration**: Existing `excel.processor` can be wrapped to emit progress events

### Implementation Notes
```python
class SSEManager:
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
    
    async def send_progress(self, session_id: str, progress_data: dict):
        if session_id in self.queues:
            await self.queues[session_id].put(progress_data)
    
    async def stream_events(self, session_id: str):
        queue = asyncio.Queue(maxsize=100)
        self.queues[session_id] = queue
        try:
            while True:
                message = await queue.get()
                yield f"data: {json.dumps(message)}\n\n"
        finally:
            del self.queues[session_id]
```

Wrap processor:
```python
async def process_spreadsheet_with_progress(session_id: str, workbook_data):
    for row_idx, result in enumerate(processor.process_rows(workbook_data)):
        await sse_manager.send_progress(session_id, {
            "type": "progress",
            "row": row_idx,
            "total": workbook_data.total_rows,
            "answer": result.answer
        })
```

## Summary

All technology decisions are finalized with no outstanding `NEEDS CLARIFICATION` items:

1. **FastAPI + Uvicorn**: Async web framework with SSE support
2. **ag-Grid Community**: Professional spreadsheet component with virtual scrolling
3. **Server-Sent Events**: Unidirectional real-time updates via EventSource API
4. **Playwright**: Multi-browser automation testing with Python API
5. **Custom CSS**: Microsoft Foundry-inspired design without framework overhead
6. **In-Memory Sessions**: UUID-based session storage with no timeout
7. **webbrowser Module**: Cross-platform browser auto-launch
8. **Existing Excel Modules**: Reuse loader/processor/column_identifier
9. **Existing Azure Auth**: Reuse DefaultAzureCredential with re-auth flow
10. **asyncio Queues**: Per-session progress tracking for SSE streaming

All selections align with constitutional requirements (Azure AI Foundry integration, multi-agent architecture, resource management, test-first development).
