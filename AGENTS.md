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

---

## Running the Web Application

### For Automated Testing (Playwright, CI/CD)

**Always use `--no-browser` when running Playwright tests or any automated browser testing:**

```bash
# Correct: Start server without opening a browser tab
python run_app.py --web --port 8080 --no-browser

# Incorrect: This will pop up a browser tab on your default browser
python run_app.py --web --port 8080
```

**Why this matters:**
- When an AI agent runs Playwright or automated tests, it controls its own browser instance
- Without `--no-browser`, the app will open a tab in the user's default browser every time
- This causes random browser popups during test runs, which is disruptive
- The Playwright-controlled browser is separate from the user's browser

**Rule:** If you are writing or running automated tests that involve the web interface, always include `--no-browser` in the server start command.

### For Manual Testing

When you want to manually interact with the UI:
```bash
python run_app.py --web --port 8080
```
This will start the server AND open a browser tab automatically.
