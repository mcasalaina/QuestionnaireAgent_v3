# Implementation Plan: Web Interface Mode

**Branch**: `004-add-web-mode` | **Date**: January 10, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-add-web-mode/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a --web command-line mode to run_app.py that launches a local web server with a modern web interface for the questionnaire agent, replacing the tkinter desktop GUI. The web interface provides the same functionality as the desktop version (single question processing, Excel spreadsheet batch processing, reasoning display) with enhanced UX through a professional spreadsheet component, Microsoft Foundry-inspired design, Server-Sent Events for real-time updates, and comprehensive Playwright test coverage.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI (web server), Uvicorn (ASGI server), Jinja2 (templates), ag-Grid Community Edition or Handsontable (spreadsheet), Playwright (testing)  
**Storage**: Server-side session storage (in-memory dict with session IDs), temporary file storage for uploaded Excel files  
**Testing**: Playwright for end-to-end browser automation, pytest for backend unit tests, mock modes for Azure services  
**Target Platform**: Windows/Linux/macOS localhost server, modern browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: <10s startup, <2s progress update latency, 60fps spreadsheet scrolling for 1000 rows, <5min test suite execution  
**Constraints**: Localhost-only (no remote access), single-server architecture (no distribution), SSE for real-time updates (no WebSockets), sessions persist indefinitely  
**Scale/Scope**: Single-user local deployment, 5+ concurrent browser tabs, 10,000 row spreadsheets, 20+ Playwright test scenarios

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Multi-Agent Architecture**: Feature integrates with existing Question Answerer, Answer Checker, and Link Checker pattern - web interface is a presentation layer that delegates to existing agents/workflow_manager.py
- [x] **Azure AI Foundry Integration**: Uses Azure AI Foundry Agent Service and SDK exclusively with DefaultAzureCredential - web backend reuses existing utils/azure_auth.py and agents/ modules
- [x] **Resource Management**: All agents/threads managed through FoundryAgentSession context managers - existing agents/workflow_manager.py patterns maintained
- [x] **Environment Configuration**: Sensitive data in .env files, never committed to version control - web mode reuses existing .env configuration
- [x] **Test-Driven Development**: Tests written first, including Azure service failure scenarios and mock modes - Playwright tests include mock mode scenarios

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
├── web/                         # NEW: Web interface backend
│   ├── __init__.py
│   ├── app.py                   # FastAPI application and routes
│   ├── session_manager.py       # Session ID generation and storage
│   ├── sse_manager.py           # Server-Sent Events coordination
│   └── static/                  # Frontend assets
│       ├── index.html           # Main web interface
│       ├── styles.css           # Microsoft Foundry-inspired styles
│       ├── app.js               # Client-side logic and SSE handling
│       └── spreadsheet.js       # Spreadsheet component integration
├── agents/                      # EXISTING: Reused by web backend
│   ├── workflow_manager.py
│   ├── question_answerer.py
│   ├── answer_checker.py
│   └── link_checker.py
├── excel/                       # EXISTING: Reused for file handling
│   ├── loader.py
│   ├── processor.py
│   └── column_identifier.py
└── utils/                       # EXISTING: Reused for auth/config
    ├── azure_auth.py
    ├── config.py
    ├── data_types.py
    └── logger.py

tests/
├── web/                         # NEW: Web-specific tests
│   ├── test_api_routes.py       # Backend API unit tests
│   ├── test_session_manager.py  # Session management tests
│   ├── test_sse_manager.py      # SSE functionality tests
│   └── playwright/              # E2E browser tests
│       ├── test_single_question.py
│       ├── test_spreadsheet_upload.py
│       ├── test_real_time_updates.py
│       ├── test_session_recovery.py
│       └── test_multi_tab.py
└── [existing test directories remain unchanged]

run_app.py                       # MODIFIED: Add --web flag and web server launch
```

**Structure Decision**: Web application structure with backend (src/web/) and frontend (src/web/static/) colocated since this is a single-server localhost deployment. Frontend is served as static files by FastAPI. Existing src/ modules are reused without modification - web layer is a thin presentation wrapper over existing agent architecture.

## Complexity Tracking

*No constitutional violations - this section is empty*

All constitutional requirements are satisfied:
- Web interface delegates to existing multi-agent architecture
- Azure AI Foundry integration maintained through existing modules
- Resource management patterns preserved
- Environment configuration reused
- Test-first approach with Playwright and pytest

## Phase 0: Technology Research

Complete technology research and decision documentation in [research.md](./research.md). Key decisions:
- **Web Framework**: FastAPI selected over Flask/Django for async/await support and automatic OpenAPI generation
- **Spreadsheet Component**: ag-Grid Community Edition selected for virtual scrolling performance and professional features
- **Real-time Updates**: Server-Sent Events (SSE) selected over WebSockets for unidirectional server-to-client updates
- **Testing Framework**: Playwright selected for multi-browser automation with Python API integration
- **Design System**: Custom CSS implementation inspired by Microsoft Foundry design aesthetics
- **Session Management**: UUID-based session IDs with in-memory dict storage for localhost deployment
- **Azure Integration**: Reuse existing DefaultAzureCredential and FoundryAgentSession patterns from utils/
- **Browser Launch**: Python webbrowser.open() for automatic launch after server startup
- **Static File Serving**: FastAPI StaticFiles middleware for CSS/JS/images
- **Error Handling**: Standardized JSON error responses with HTTP status codes and error_code fields

## Phase 1: Design & Contracts

### Data Model Definition

Complete entity definitions in [data-model.md](./data-model.md). Entities include:
- **WebSession**: Session state container (UUID, config, workbook reference, processing job, temp file path, timestamps)
- **ProcessingJob**: Batch processing state (job ID, question rows, progress tracking, results, status, SSE integration)
- **SSEMessage**: Typed event messages (PROGRESS, ANSWER, ERROR, COMPLETE, STATUS) with timestamps and data payloads
- **WebWorkbookView**: Frontend presentation model (rows array, columns array, cell data mapping)
- **WebAnswerDisplay**: Answer presentation (answer text, character count, reasoning, processing time, links checked)
- **WebSpreadsheetCellUpdate**: Real-time cell update payload for SSE streaming (row, column, new value, formatting)
- **WebErrorResponse**: Standardized error format (error_code, message, details, HTTP status)
- **Reused Entities**: WorkbookData, WorkbookSheet, ProcessingResult from existing utils.data_types module

### API Contracts

Complete REST API specifications in [contracts/api-spec.md](./contracts/api-spec.md). Endpoints:
- **Session Management**: POST /api/session/create, GET /api/session/{id}, PUT /api/session/{id}/config, DELETE /api/session/{id}
- **Single Question**: POST /api/question (async processing with agent delegation)
- **Spreadsheet Operations**: POST /api/spreadsheet/upload, POST /api/spreadsheet/process, GET /api/spreadsheet/download/{session_id}
- **Real-time Updates**: GET /api/sse/{session_id} (Server-Sent Events streaming)
- **Health Check**: GET /health (service monitoring)
- **Request/Response Schemas**: Complete JSON schemas for all payloads
- **Error Handling**: HTTP status codes (400/404/500) with structured error responses

### Developer Onboarding

Complete quickstart guide in [quickstart.md](./quickstart.md). Contents:
- **Prerequisites**: Python 3.11+, venv activation, Azure authentication setup, dependency installation
- **Phase-by-Phase Implementation**: Basic web server → session management → single question → SSE → spreadsheet processing
- **Code Examples**: FastAPI routes, SessionManager implementation, HTML/JavaScript frontend patterns, ag-Grid integration
- **Testing Strategy**: pytest unit tests with TestClient, Playwright browser automation scenarios
- **Deployment Checklist**: Constitution compliance verification, documentation updates, requirements.txt
- **Troubleshooting**: Port conflicts, browser launch issues, SSE disconnects, ag-Grid CDN loading

### Agent Context Update

Agent context updated successfully via `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot`:
- Added language: Python 3.11+
- Added frameworks: FastAPI, Uvicorn, Jinja2, ag-Grid Community Edition, Playwright
- Added storage: Server-side session storage (in-memory dict), temporary file storage
- Updated project type: Web application (backend + frontend)
- Modified file: `.github/copilot-instructions.md`

## Phase 2: Task Breakdown

**Phase 2 output is created by the `/speckit.tasks` command - NOT by this `/speckit.plan` command.**

The tasks.md file will be generated separately using `/speckit.tasks` after this plan is complete.
