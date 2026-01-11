# Quickstart: Web Interface Mode

**Date**: January 10, 2026  
**Feature**: 004-add-web-mode

## Overview

This quickstart guide provides step-by-step instructions for implementing the web interface mode feature, following the architecture and contracts defined in the planning phase.

## Prerequisites

Before starting implementation:

1. **Environment Setup**:
   - Python 3.11+ installed
   - Virtual environment activated: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux)
   - Existing Azure authentication configured (`.env` file with Azure AI project settings)
   - Access to Azure AI Foundry services

2. **Dependencies to Install**:
   ```bash
   pip install fastapi uvicorn jinja2 python-multipart playwright
   playwright install chromium firefox webkit
   ```

3. **Knowledge Required**:
   - FastAPI basics (routing, request/response models, async/await)
   - Server-Sent Events (EventSource API)
   - ag-Grid JavaScript API for spreadsheet component
   - Playwright testing framework

## Implementation Phases

### Phase 1: Basic Web Server (P1 - User Story 1)

**Goal**: Launch web server with --web flag, serve static HTML, auto-open browser.

**Steps**:

1. **Create web module structure**:
   ```bash
   mkdir src/web
   mkdir src/web/static
   touch src/web/__init__.py
   touch src/web/app.py
   touch src/web/session_manager.py
   ```

2. **Implement FastAPI app** (`src/web/app.py`):
   ```python
   from fastapi import FastAPI
   from fastapi.staticfiles import StaticFiles
   from fastapi.responses import FileResponse
   import uvicorn
   
   app = FastAPI(title="Questionnaire Agent Web")
   
   # Mount static files
   app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
   
   @app.get("/")
   async def index():
       return FileResponse("src/web/static/index.html")
   
   @app.get("/health")
   async def health():
       return {"status": "healthy", "timestamp": datetime.now().isoformat()}
   
   def run_server(port=8080):
       uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
   ```

3. **Create minimal HTML** (`src/web/static/index.html`):
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>Questionnaire Agent</title>
       <link rel="stylesheet" href="/static/styles.css">
   </head>
   <body>
       <h1>Questionnaire Agent Web Interface</h1>
       <div id="app">Loading...</div>
       <script src="/static/app.js"></script>
   </body>
   </html>
   ```

4. **Modify run_app.py to support --web**:
   ```python
   parser.add_argument("--web", action="store_true", help="Launch in web mode")
   parser.add_argument("--port", type=int, default=8080, help="Web server port")
   
   # In main:
   if args.web:
       from web.app import run_server
       import webbrowser
       import threading
       
       # Start server in background
       server_thread = threading.Thread(target=run_server, args=(args.port,), daemon=True)
       server_thread.start()
       
       # Wait for server health check
       time.sleep(2)
       
       # Open browser
       webbrowser.open(f"http://127.0.0.1:{args.port}")
       
       # Keep main thread alive
       server_thread.join()
   else:
       # Existing tkinter UI code
       ...
   ```

5. **Test**:
   ```bash
   python run_app.py --web --port 8080
   ```
   - Verify browser opens automatically
   - Verify http://localhost:8080 loads the page
   - Verify no tkinter window appears

**Acceptance Criteria**: User Story 1, Scenario 1 passes.

---

### Phase 2: Session Management (P1 - User Story 1 cont.)

**Goal**: Each browser tab gets unique session ID, independent state.

**Steps**:

1. **Implement SessionManager** (`src/web/session_manager.py`):
   ```python
   import uuid
   from typing import Dict, Any
   from datetime import datetime
   
   class SessionManager:
       def __init__(self):
           self.sessions: Dict[str, Dict[str, Any]] = {}
       
       def create_session(self) -> str:
           session_id = str(uuid.uuid4())
           self.sessions[session_id] = {
               "created_at": datetime.now(),
               "config": {"context": "Microsoft Azure AI", "char_limit": 2000},
               "workbook": None,
               "processing_job": None,
               "temp_file": None
           }
           return session_id
       
       def get_session(self, session_id: str) -> Dict[str, Any]:
           return self.sessions.get(session_id)
       
       def update_config(self, session_id: str, config: dict):
           if session_id in self.sessions:
               self.sessions[session_id]["config"].update(config)
   
   # Global instance
   session_manager = SessionManager()
   ```

2. **Add session API endpoints** (`src/web/app.py`):
   ```python
   from web.session_manager import session_manager
   from pydantic import BaseModel
   
   class SessionCreateResponse(BaseModel):
       session_id: str
       created_at: str
       config: dict
   
   @app.post("/api/session/create", response_model=SessionCreateResponse)
   async def create_session():
       session_id = session_manager.create_session()
       session = session_manager.get_session(session_id)
       return {
           "session_id": session_id,
           "created_at": session["created_at"].isoformat(),
           "config": session["config"]
       }
   ```

3. **Update frontend to request session** (`src/web/static/app.js`):
   ```javascript
   // Initialize session on page load
   let sessionId = localStorage.getItem('sessionId');
   
   if (!sessionId) {
       fetch('/api/session/create', { method: 'POST' })
           .then(res => res.json())
           .then(data => {
               sessionId = data.session_id;
               localStorage.setItem('sessionId', sessionId);
               initializeUI();
           });
   } else {
       initializeUI();
   }
   
   function initializeUI() {
       document.getElementById('app').innerHTML = `
           <p>Session ID: ${sessionId}</p>
           <div id="question-form">...</div>
       `;
   }
   ```

4. **Test**:
   - Open multiple browser tabs
   - Verify each gets unique session ID in localStorage
   - Verify session IDs persist across page refreshes

**Acceptance Criteria**: User Story 1, Scenario 3 passes.

---

### Phase 3: Single Question Processing (P1 - User Story 2)

**Goal**: User can submit question, see answer with reasoning.

**Steps**:

1. **Add question endpoint** (`src/web/app.py`):
   ```python
   from agents.workflow_manager import AgentCoordinator
   from utils.data_types import Question
   
   class QuestionRequest(BaseModel):
       session_id: str
       question: str
       context: str
       char_limit: int
   
   @app.post("/api/question")
   async def process_question(req: QuestionRequest):
       session = session_manager.get_session(req.session_id)
       if not session:
           raise HTTPException(404, "Session not found")
       
       # Delegate to existing agent coordinator
       coordinator = AgentCoordinator()
       question_obj = Question(
           text=req.question,
           context=req.context,
           char_limit=req.char_limit
       )
       
       result = await coordinator.process_question(question_obj)
       
       return {
           "answer": result.answer,
           "reasoning": result.reasoning,
           "processing_time_seconds": result.processing_time,
           "links_checked": len(result.checked_links)
       }
   ```

2. **Add question form to HTML** (`src/web/static/index.html`):
   ```html
   <div id="question-section">
       <h2>Ask a Question</h2>
       <textarea id="question-input" placeholder="Enter your question"></textarea>
       <input type="text" id="context-input" value="Microsoft Azure AI" />
       <input type="number" id="char-limit-input" value="2000" min="100" max="10000" />
       <button id="submit-btn">Submit</button>
       <div id="loading" style="display:none;">Processing...</div>
       <div id="answer-result"></div>
       <details id="reasoning-details">
           <summary>Show Reasoning</summary>
           <div id="reasoning-content"></div>
       </details>
   </div>
   ```

3. **Wire up JavaScript** (`src/web/static/app.js`):
   ```javascript
   document.getElementById('submit-btn').addEventListener('click', async () => {
       const question = document.getElementById('question-input').value;
       const context = document.getElementById('context-input').value;
       const charLimit = parseInt(document.getElementById('char-limit-input').value);
       
       document.getElementById('loading').style.display = 'block';
       document.getElementById('submit-btn').disabled = true;
       
       const response = await fetch('/api/question', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ session_id: sessionId, question, context, char_limit: charLimit })
       });
       
       const data = await response.json();
       
       document.getElementById('answer-result').innerHTML = `<p>${data.answer}</p>`;
       document.getElementById('reasoning-content').innerHTML = `<pre>${data.reasoning}</pre>`;
       document.getElementById('loading').style.display = 'none';
       document.getElementById('submit-btn').disabled = false;
   });
   ```

4. **Test**:
   - Enter question "What is Azure AI Foundry?"
   - Click Submit
   - Verify answer appears within 30 seconds
   - Verify reasoning can be expanded

**Acceptance Criteria**: User Story 2, Scenarios 1, 4, 5 pass.

---

### Phase 4: Server-Sent Events (P1/P2 - Real-time Updates)

**Goal**: Implement SSE for progress updates during processing.

**Steps**:

1. **Create SSEManager** (`src/web/sse_manager.py`):
   ```python
   import asyncio
   from typing import Dict
   import json
   
   class SSEManager:
       def __init__(self):
           self.queues: Dict[str, asyncio.Queue] = {}
       
       async def send_event(self, session_id: str, event_type: str, data: dict):
           if session_id in self.queues:
               message = {
                   "type": event_type,
                   "timestamp": datetime.now().isoformat(),
                   "data": data
               }
               await self.queues[session_id].put(message)
       
       async def stream_events(self, session_id: str):
           queue = asyncio.Queue(maxsize=100)
           self.queues[session_id] = queue
           try:
               while True:
                   message = await queue.get()
                   yield f"data: {json.dumps(message)}\n\n"
           finally:
               del self.queues[session_id]
   
   sse_manager = SSEManager()
   ```

2. **Add SSE endpoint** (`src/web/app.py`):
   ```python
   from fastapi.responses import StreamingResponse
   from web.sse_manager import sse_manager
   
   @app.get("/api/sse/{session_id}")
   async def sse_stream(session_id: str):
       return StreamingResponse(
           sse_manager.stream_events(session_id),
           media_type="text/event-stream"
       )
   ```

3. **Connect frontend to SSE** (`src/web/static/app.js`):
   ```javascript
   const eventSource = new EventSource(`/api/sse/${sessionId}`);
   
   eventSource.onmessage = (event) => {
       const message = JSON.parse(event.data);
       handleSSEMessage(message);
   };
   
   function handleSSEMessage(message) {
       if (message.type === 'PROGRESS') {
           updateProgressBar(message.data.percentage);
       } else if (message.type === 'ANSWER') {
           updateSpreadsheetCell(message.data.row, message.data.answer);
       }
   }
   ```

**Acceptance Criteria**: SSE connection established, messages received.

---

### Phase 5: Spreadsheet Upload & Processing (P2 - User Story 3)

**Goal**: Upload Excel, display in grid, process batch questions.

**Steps**:

1. **Add upload endpoint** (`src/web/app.py`):
   ```python
   from fastapi import UploadFile, File
   from excel.loader import ExcelLoader
   from excel.column_identifier import ColumnIdentifier
   import tempfile
   import shutil
   
   @app.post("/api/spreadsheet/upload")
   async def upload_spreadsheet(session_id: str, file: UploadFile = File(...)):
       session = session_manager.get_session(session_id)
       if not session:
           raise HTTPException(404, "Session not found")
       
       # Save to temp
       temp_path = tempfile.mktemp(suffix='.xlsx')
       with open(temp_path, 'wb') as buffer:
           shutil.copyfileobj(file.file, buffer)
       
       # Load workbook
       loader = ExcelLoader()
       workbook_data = loader.load(temp_path)
       
       # Identify columns
       identifier = ColumnIdentifier()
       suggestions = identifier.identify_columns(workbook_data)
       
       session['workbook'] = workbook_data
       session['temp_file'] = temp_path
       
       return {
           "session_id": session_id,
           "filename": file.filename,
           "sheets": workbook_data.sheet_names,
           "columns": {sheet: list(workbook_data.get_sheet(sheet).columns) for sheet in workbook_data.sheet_names},
           "suggested_columns": suggestions
       }
   ```

2. **Add spreadsheet UI** (`src/web/static/index.html`):
   ```html
   <div id="spreadsheet-section">
       <h2>Spreadsheet Processing</h2>
       <input type="file" id="file-upload" accept=".xlsx,.xls" />
       <div id="column-selectors" style="display:none;">
           <select id="sheet-select"></select>
           <select id="question-col"></select>
           <select id="context-col"></select>
           <select id="answer-col"></select>
           <button id="process-btn">Start Processing</button>
       </div>
       <div id="spreadsheet-grid"></div>
   </div>
   ```

3. **Integrate ag-Grid** (`src/web/static/spreadsheet.js`):
   ```javascript
   function initializeGrid(rows, columns) {
       const columnDefs = columns.map(col => ({ field: col, editable: false }));
       const gridOptions = {
           columnDefs,
           rowData: rows,
           enableRangeSelection: true,
           animateRows: true
       };
       const gridDiv = document.getElementById('spreadsheet-grid');
       new agGrid.Grid(gridDiv, gridOptions);
   }
   ```

**Acceptance Criteria**: User Story 3, Scenarios 1-3 pass.

---

## Testing Strategy

### Unit Tests (`tests/web/`)

```python
import pytest
from fastapi.testclient import TestClient
from web.app import app

client = TestClient(app)

def test_create_session():
    response = client.post("/api/session/create")
    assert response.status_code == 201
    assert "session_id" in response.json()

def test_process_question():
    # Create session
    session_resp = client.post("/api/session/create")
    session_id = session_resp.json()["session_id"]
    
    # Process question
    response = client.post("/api/question", json={
        "session_id": session_id,
        "question": "Test question",
        "context": "Test context",
        "char_limit": 1000
    })
    assert response.status_code == 200
    assert "answer" in response.json()
```

### Playwright Tests (`tests/web/playwright/`)

```python
def test_single_question_flow(page):
    page.goto("http://localhost:8080")
    page.wait_for_selector("#question-input")
    
    page.fill("#question-input", "What is Azure?")
    page.click("#submit-btn")
    
    page.wait_for_selector("#answer-result", timeout=60000)
    answer = page.text_content("#answer-result")
    assert len(answer) > 0
```

### Running Tests

```bash
# Unit tests
pytest tests/web/test_api_routes.py

# Playwright tests (requires server running)
python run_app.py --web &
sleep 5
pytest tests/web/playwright/
kill %1
```

## Deployment Checklist

- [ ] All Phase 1-5 implementations complete
- [ ] Unit tests passing (pytest)
- [ ] Playwright tests passing (all browsers)
- [ ] Constitution compliance verified
- [ ] Documentation updated (README.md)
- [ ] Requirements.txt updated with new dependencies

## Next Steps

After quickstart implementation:
1. Microsoft Foundry CSS styling (Phase 6)
2. Enhanced spreadsheet features (sorting, filtering)
3. Performance optimization (large file handling)
4. Additional Playwright test scenarios
5. Error handling improvements

## Troubleshooting

**Server won't start**: Check port 8080 not in use: `netstat -an | findstr 8080`
**Browser doesn't open**: Verify `webbrowser` module works: `python -c "import webbrowser; webbrowser.open('http://google.com')"`
**SSE disconnects**: Check firewall/antivirus not blocking EventSource connections
**ag-Grid not loading**: Verify CDN accessible, check browser console for errors

## Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- ag-Grid Community: https://www.ag-grid.com/javascript-data-grid/
- Playwright Python: https://playwright.dev/python/
- Server-Sent Events: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
