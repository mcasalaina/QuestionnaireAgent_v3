# QuestionnaireAgent_v3 Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-09

## Active Technologies
- Python 3.11+ + agent-framework-azure-ai (--pre), azure-ai-projects, azure-identity, tkinter, openpyxl, pandas, playwright, pytest (001-rewrite-questionnaire-agent)
- Python 3.11+ + tkinter (GUI), openpyxl (Excel), agent-framework-azure-ai (multi-agent), azure-ai-projects, azure-identity (002-amend-the-answer)
- Excel files (.xlsx) on local filesystem (002-amend-the-answer)
- Python 3.11+ + FastAPI (web server), Uvicorn (ASGI server), Jinja2 (templates), ag-Grid Community Edition or Handsontable (spreadsheet), Playwright (testing) (004-add-web-mode)
- Server-side session storage (in-memory dict with session IDs), temporary file storage for uploaded Excel files (004-add-web-mode)

## Project Structure
```
src/
tests/
```

## Commands
cd src; pytest; ruff check .

## Code Style
Python 3.11+: Follow standard conventions

## Recent Changes
- 004-add-web-mode: Added Python 3.11+ + FastAPI (web server), Uvicorn (ASGI server), Jinja2 (templates), ag-Grid Community Edition or Handsontable (spreadsheet), Playwright (testing)
- 002-amend-the-answer: Added Python 3.11+ + tkinter (GUI), openpyxl (Excel), agent-framework-azure-ai (multi-agent), azure-ai-projects, azure-identity
- 001-rewrite-questionnaire-agent: Added Python 3.11+ + agent-framework-azure-ai (--pre), azure-ai-projects, azure-identity, tkinter, openpyxl, pandas, playwright, pytest

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
