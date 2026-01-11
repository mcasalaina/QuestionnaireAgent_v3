# API Contracts: Web Interface Mode

**Date**: January 10, 2026  
**Feature**: 004-add-web-mode  
**Base URL**: `http://localhost:8080`

## Overview

This document defines the REST API contracts for the web interface mode. All endpoints use JSON for request/response payloads unless otherwise specified. The API follows RESTful conventions with FastAPI automatic validation.

## Authentication

No authentication required - localhost-only deployment. Azure authentication is handled server-side using existing `DefaultAzureCredential`.

## Common Headers

**Request**:
- `Content-Type: application/json` (for POST/PUT requests)

**Response**:
- `Content-Type: application/json` (for standard endpoints)
- `Content-Type: text/event-stream` (for SSE endpoints)

## Endpoints

### 1. Create Session

**Purpose**: Initialize a new web session and receive session ID.

```http
POST /api/session/create
```

**Request Body**: None

**Response** (201 Created):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-10T14:30:00Z",
  "config": {
    "context": "Microsoft Azure AI",
    "char_limit": 2000
  }
}
```

**Error Responses**:
- 500: Server error during session creation

---

### 2. Get Session

**Purpose**: Retrieve current session state.

```http
GET /api/session/{session_id}
```

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-10T14:30:00Z",
  "config": {
    "context": "Microsoft Azure AI",
    "char_limit": 2000
  },
  "has_workbook": false,
  "processing_status": null
}
```

**Error Responses**:
- 404: Session not found

---

### 3. Update Session Config

**Purpose**: Update session configuration settings.

```http
PUT /api/session/{session_id}/config
```

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Request Body**:
```json
{
  "context": "Azure AI Services",
  "char_limit": 1500
}
```

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "config": {
    "context": "Azure AI Services",
    "char_limit": 1500
  }
}
```

**Error Responses**:
- 404: Session not found
- 422: Validation error (invalid char_limit range, empty context)

---

### 4. Process Single Question

**Purpose**: Process a single question and return answer with reasoning.

```http
POST /api/question
```

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What is Azure AI Foundry?",
  "context": "Microsoft Azure AI",
  "char_limit": 2000
}
```

**Response** (200 OK):
```json
{
  "answer": "Azure AI Foundry is a unified platform for building...",
  "reasoning": "## Agent Workflow\n1. Question Analysis...",
  "processing_time_seconds": 15.3,
  "links_checked": 5
}
```

**Error Responses**:
- 404: Session not found
- 401: Azure authentication failed
- 422: Validation error (empty question, invalid char_limit)
- 500: Processing error

---

### 5. Upload Spreadsheet

**Purpose**: Upload Excel file and analyze structure.

```http
POST /api/spreadsheet/upload
```

**Request**: multipart/form-data
- `session_id` (form field): Session UUID
- `file` (file upload): Excel file (.xlsx or .xls)

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "questions.xlsx",
  "sheets": ["Sheet1", "Questions", "Data"],
  "columns": {
    "Sheet1": ["Question", "Context", "Answer", "Status"],
    "Questions": ["Q", "A"],
    "Data": ["Column1", "Column2"]
  },
  "suggested_columns": {
    "sheet_name": "Sheet1",
    "question_column": "Question",
    "context_column": "Context",
    "answer_column": "Answer",
    "confidence": 0.95
  }
}
```

**Error Responses**:
- 404: Session not found
- 400: Invalid file format (not .xlsx/.xls)
- 422: Validation error (file too large, corrupted file)
- 500: File processing error

---

### 6. Start Spreadsheet Processing

**Purpose**: Begin batch processing of spreadsheet questions.

```http
POST /api/spreadsheet/process
```

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "sheet_name": "Sheet1",
  "question_column": "Question",
  "context_column": "Context",
  "answer_column": "Answer",
  "start_row": 0,
  "end_row": null
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "RUNNING",
  "total_rows": 50,
  "processed_rows": 0,
  "started_at": "2026-01-10T14:35:00Z"
}
```

**Error Responses**:
- 404: Session not found or no workbook loaded
- 400: Invalid sheet name or column names
- 409: Processing job already running for this session
- 422: Validation error (invalid row range)

---

### 7. Get Processing Status

**Purpose**: Query current status of spreadsheet processing job.

```http
GET /api/spreadsheet/status/{session_id}
```

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Response** (200 OK):
```json
{
  "job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "RUNNING",
  "processed_rows": 23,
  "total_rows": 50,
  "current_row": 24,
  "estimated_time_remaining_seconds": 405.5,
  "started_at": "2026-01-10T14:35:00Z",
  "completed_at": null
}
```

**Response when no job** (200 OK):
```json
{
  "status": "NO_JOB",
  "message": "No processing job active for this session"
}
```

**Error Responses**:
- 404: Session not found

---

### 8. Stop Processing

**Purpose**: Gracefully stop spreadsheet processing job.

```http
POST /api/spreadsheet/stop
```

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (200 OK):
```json
{
  "job_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "CANCELLED",
  "processed_rows": 23,
  "total_rows": 50
}
```

**Error Responses**:
- 404: Session or job not found
- 400: No active job to stop

---

### 9. Download Processed Spreadsheet

**Purpose**: Download Excel file with answers populated.

```http
GET /api/spreadsheet/download/{session_id}
```

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Response** (200 OK):
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="questions_answered.xlsx"`
- Body: Excel file binary data

**Error Responses**:
- 404: Session not found or no workbook loaded
- 400: Processing not completed

---

### 10. Server-Sent Events Stream

**Purpose**: Real-time updates for question processing and spreadsheet progress.

```http
GET /api/sse/{session_id}
```

**Path Parameters**:
- `session_id` (string, required): Session UUID

**Response** (200 OK):
- Content-Type: `text/event-stream`
- Connection: `keep-alive`
- Cache-Control: `no-cache`

**Event Format** (SSE protocol):
```
data: {"type": "PROGRESS", "timestamp": "2026-01-10T14:35:15Z", "data": {"row": 5, "total": 50, "percentage": 10.0}}

data: {"type": "ANSWER", "timestamp": "2026-01-10T14:35:30Z", "data": {"row": 5, "question": "What is...", "answer": "Azure...", "reasoning": "..."}}

data: {"type": "ERROR", "timestamp": "2026-01-10T14:35:45Z", "data": {"message": "Azure service unavailable", "row": 6}}

data: {"type": "COMPLETE", "timestamp": "2026-01-10T14:50:00Z", "data": {"total_processed": 50, "duration_seconds": 900.0}}

data: {"type": "STATUS", "timestamp": "2026-01-10T14:36:00Z", "data": {"status": "PAUSED", "job_id": "7c9e6679..."}}
```

**Client Example**:
```javascript
const eventSource = new EventSource(`/api/sse/${sessionId}`);
eventSource.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleSSEMessage(message);
};
eventSource.onerror = () => {
    // Automatic reconnection by browser
};
```

**Error Responses**:
- 404: Session not found

---

### 11. Health Check

**Purpose**: Verify server is running and ready.

```http
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2026-01-10T14:30:00Z",
  "azure_auth": "authenticated"
}
```

**Response if Azure auth failed** (200 OK):
```json
{
  "status": "degraded",
  "timestamp": "2026-01-10T14:30:00Z",
  "azure_auth": "unauthenticated",
  "message": "Azure credentials not available"
}
```

---

## Error Response Format

All error responses follow this standard format:

```json
{
  "error": "Error message describing what went wrong",
  "detail": "Additional context or validation details",
  "status_code": 404
}
```

## Rate Limiting

No rate limiting applied - localhost single-user scenario.

## WebSocket Alternative (Not Implemented)

Per specification clarifications, WebSockets are explicitly out of scope. Server-Sent Events provide sufficient unidirectional server-to-client push capabilities.

## CORS Policy

CORS headers not required - same-origin policy applies (frontend served from same server as API).

## API Versioning

No API versioning in initial implementation. All endpoints are v1 implicit. Future versions would use `/api/v2/` prefix if breaking changes required.

## Testing Notes

All endpoints are tested with:
- Playwright for end-to-end browser flows
- pytest for unit tests of individual route handlers
- Mock Azure services for testing without live credentials

See `tests/web/playwright/` and `tests/web/test_api_routes.py` for implementation.
