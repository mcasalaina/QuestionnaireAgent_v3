# Data Model: Web Interface Mode

**Date**: January 10, 2026  
**Feature**: 004-add-web-mode  
**Phase**: 1 (Design & Contracts)

## Overview

This document defines the data entities and their relationships for the web interface mode. Most entities are reused from the existing codebase (`utils.data_types`); this document focuses on new web-specific entities and their interactions with existing types.

## Entity Definitions

### WebSession

Represents an active user session in the web browser.

**Attributes**:
- `session_id: str` - UUID v4 unique identifier for this browser tab's session
- `created_at: datetime` - Session creation timestamp
- `config: SessionConfig` - User configuration settings (context, character limit)
- `workbook: Optional[WorkbookData]` - Currently loaded Excel workbook (reuses existing type from `utils.data_types`)
- `processing_job: Optional[ProcessingJob]` - Active spreadsheet processing job
- `temp_file_path: Optional[str]` - Path to temporary uploaded Excel file

**Lifecycle**:
- Created: When browser loads index page and requests session ID
- Active: Throughout user interaction (no timeout)
- Terminated: Only on server shutdown or explicit session deletion

**Validation Rules**:
- `session_id` must be valid UUID format
- `temp_file_path` must exist on filesystem if not None
- Only one `processing_job` can be active per session

**Relationships**:
- One-to-one with `ProcessingJob` (optional)
- One-to-one with `WorkbookData` (optional, reused from `utils.data_types.WorkbookData`)

### SessionConfig

User-configurable settings for question processing.

**Attributes**:
- `context: str` - Default context for question answering (default: "Microsoft Azure AI")
- `char_limit: int` - Character limit for answers (default: 2000)

**Validation Rules**:
- `context` must not be empty string
- `char_limit` must be in range [100, 10000]

### ProcessingJob

Represents an active spreadsheet batch processing task.

**Attributes**:
- `job_id: str` - UUID v4 unique identifier for this job
- `session_id: str` - Foreign key to WebSession
- `status: JobStatus` - Current job state (enum: RUNNING, PAUSED, COMPLETED, CANCELLED, ERROR)
- `started_at: datetime` - Job start timestamp
- `completed_at: Optional[datetime]` - Job completion timestamp (None if not finished)
- `total_rows: int` - Total number of questions to process
- `processed_rows: int` - Number of questions completed
- `current_row: Optional[int]` - Row currently being processed (None if not started or finished)
- `results: List[ProcessingResult]` - List of completed question results (reuses existing type from `utils.data_types`)
- `error: Optional[str]` - Error message if status is ERROR

**State Transitions**:
```
RUNNING -> COMPLETED (all rows processed successfully)
RUNNING -> PAUSED (user clicked stop button)
RUNNING -> CANCELLED (user cancelled explicitly)
RUNNING -> ERROR (Azure service failure or processing error)
PAUSED -> RUNNING (user resumed processing)
PAUSED -> CANCELLED (user cancelled while paused)
```

**Validation Rules**:
- `total_rows` must be > 0
- `processed_rows` must be <= `total_rows`
- `current_row` must be in range [0, total_rows) when processing
- `completed_at` must be > `started_at` when not None
- `results` length must equal `processed_rows`

**Relationships**:
- Many-to-one with WebSession (session_id foreign key)
- One-to-many with ProcessingResult (reused from existing codebase)

### JobStatus (Enum)

Processing job state enumeration.

**Values**:
- `RUNNING` - Job is actively processing questions
- `PAUSED` - Job temporarily stopped, can be resumed
- `COMPLETED` - All questions processed successfully
- `CANCELLED` - User explicitly cancelled the job
- `ERROR` - Job failed due to error (Azure service, network, etc.)

### SSEMessage

Server-Sent Event message structure for real-time updates.

**Attributes**:
- `type: SSEMessageType` - Message type discriminator
- `timestamp: datetime` - When message was generated
- `data: dict` - Type-specific payload

**Message Types** (SSEMessageType enum):
- `PROGRESS`: Progress update during processing
  - `data: {"row": int, "total": int, "percentage": float}`
- `ANSWER`: New answer completed
  - `data: {"row": int, "question": str, "answer": str, "reasoning": str}`
- `ERROR`: Error occurred
  - `data: {"message": str, "row": Optional[int]}`
- `COMPLETE`: Job finished
  - `data: {"total_processed": int, "duration_seconds": float}`
- `STATUS`: Status change notification
  - `data: {"status": str, "job_id": str}`

**Validation Rules**:
- `type` must be valid SSEMessageType enum value
- `data` structure must match the expected schema for the given `type`

### QuestionRequest

API request for single question processing.

**Attributes**:
- `session_id: str` - Session identifier
- `question: str` - Question text to process
- `context: str` - Context for the question (overrides session config)
- `char_limit: int` - Character limit for answer (overrides session config)

**Validation Rules**:
- `session_id` must be valid UUID format and exist in session manager
- `question` must not be empty string
- `context` must not be empty string
- `char_limit` must be in range [100, 10000]

### QuestionResponse

API response for single question processing.

**Attributes**:
- `answer: str` - Generated answer text
- `reasoning: str` - Detailed reasoning trace (formatted)
- `processing_time_seconds: float` - Time taken to process
- `links_checked: int` - Number of links validated

**Reuses**: Derived from existing `ProcessingResult` type in `utils.data_types`

### SpreadsheetUploadResponse

API response after Excel file upload.

**Attributes**:
- `session_id: str` - Session identifier
- `filename: str` - Original uploaded filename
- `sheets: List[str]` - List of worksheet names in the workbook
- `columns: Dict[str, List[str]]` - Column names per worksheet (key: sheet name, value: column names)
- `suggested_columns: ColumnSuggestions` - Auto-identified Question/Context/Answer columns

**Relationships**:
- References WebSession via session_id

### ColumnSuggestions

Suggested column mappings from automatic analysis.

**Attributes**:
- `sheet_name: str` - Recommended worksheet to process
- `question_column: Optional[str]` - Detected question column name
- `context_column: Optional[str]` - Detected context column name
- `answer_column: Optional[str]` - Detected answer column name
- `confidence: float` - Confidence score for suggestions (0.0 to 1.0)

**Validation Rules**:
- `confidence` must be in range [0.0, 1.0]
- At minimum, `question_column` should be identified (others can be None)

**Reuses**: Logic from existing `excel.column_identifier.ColumnIdentifier`

### ProcessingStartRequest

API request to start spreadsheet processing.

**Attributes**:
- `session_id: str` - Session identifier
- `sheet_name: str` - Worksheet to process
- `question_column: str` - Column containing questions
- `context_column: Optional[str]` - Column containing context (None = use session default)
- `answer_column: str` - Column to write answers
- `start_row: int` - First row to process (0-indexed, default: 0)
- `end_row: Optional[int]` - Last row to process (None = process all)

**Validation Rules**:
- `session_id` must exist and have a loaded workbook
- `sheet_name` must exist in workbook
- `question_column` and `answer_column` must exist in sheet
- `context_column` must exist in sheet if not None
- `start_row` must be >= 0
- `end_row` must be > `start_row` if not None

### ProcessingStatusResponse

API response for processing status queries.

**Attributes**:
- `job_id: str` - Processing job identifier
- `status: JobStatus` - Current job status
- `processed_rows: int` - Number of rows completed
- `total_rows: int` - Total rows to process
- `current_row: Optional[int]` - Row currently being processed
- `estimated_time_remaining_seconds: Optional[float]` - Estimated completion time
- `results: List[ProcessingResult]` - Completed results so far

**Reuses**: Built from ProcessingJob attributes

## Entity Relationships Diagram

```
WebSession (1) ----------- (0..1) ProcessingJob
    |                              |
    | session_id                   | job_id, session_id
    |                              |
    +-- (0..1) WorkbookData        +-- (0..*) ProcessingResult
    +-- (1) SessionConfig          +-- (1) JobStatus
    
SSEMessage (independent broadcast per session)
    |
    +-- SSEMessageType (enum)
    +-- data (dict)

API Request/Response entities (stateless):
    QuestionRequest -> QuestionResponse
    (none) -> SpreadsheetUploadResponse (creates WebSession if needed)
    ProcessingStartRequest -> ProcessingStatusResponse
```

## Reused Existing Entities

The following entities from `src/utils/data_types.py` are reused without modification:

- **WorkbookData**: Excel workbook structure with sheets and rows
- **ProcessingResult**: Result of processing a single question (answer, reasoning, links)
- **Question**: Question entity with text, context, character limit

The web interface layer translates between HTTP requests/responses and these existing data structures, maintaining the separation between presentation (web) and business logic (agents, excel processing).

## Storage Strategy

**In-Memory Storage**:
- `Dict[str, WebSession]` - Session manager maintains session dictionary
- `Dict[str, asyncio.Queue[SSEMessage]]` - SSE manager maintains per-session queues
- No persistent storage required (localhost scenario, acceptable to lose state on server restart)

**Temporary Files**:
- Uploaded Excel files stored in OS temp directory via `tempfile.mktemp()`
- Cleaned up on session termination or server shutdown
- Path stored in `WebSession.temp_file_path`

## Data Flow Examples

### Single Question Processing Flow

1. Client sends `QuestionRequest` to `/api/question`
2. Backend retrieves `WebSession` by `session_id`
3. Backend delegates to existing `agents.workflow_manager.AgentCoordinator`
4. AgentCoordinator returns `ProcessingResult`
5. Backend converts to `QuestionResponse` and returns to client
6. Backend broadcasts `SSEMessage` (type: ANSWER) to session's SSE stream

### Spreadsheet Processing Flow

1. Client uploads file to `/api/spreadsheet/upload`
2. Backend creates/updates `WebSession` with `WorkbookData`
3. Backend analyzes columns using existing `ColumnIdentifier`
4. Backend returns `SpreadsheetUploadResponse` with suggestions
5. Client sends `ProcessingStartRequest` to `/api/spreadsheet/process`
6. Backend creates `ProcessingJob` in `WebSession`
7. Backend processes rows asynchronously, broadcasting SSE messages:
   - Type: PROGRESS after each row
   - Type: ANSWER with row data
   - Type: ERROR if failure occurs
   - Type: COMPLETE when finished
8. Client updates spreadsheet grid in real-time from SSE messages

### Session Recovery Flow

1. User closes browser tab during processing
2. `ProcessingJob` continues running server-side
3. User reopens browser, same `session_id` from localStorage
4. Client connects to `/api/sse/{session_id}`
5. Client fetches `/api/processing/status/{session_id}`
6. Backend returns current `ProcessingStatusResponse`
7. Client reconstructs UI state and continues receiving SSE updates

## Validation Summary

All entities include validation rules to ensure data integrity:
- Required fields checked for None/empty values
- Numeric ranges enforced (char_limit, confidence scores)
- Foreign key relationships validated (session_id, job_id existence)
- State transition constraints enforced (JobStatus state machine)
- File path existence validated before use

These validations are implemented using Pydantic models in FastAPI request/response handlers, providing automatic validation and clear error messages.
