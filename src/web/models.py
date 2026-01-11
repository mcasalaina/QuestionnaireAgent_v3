"""Pydantic models for the web interface API.

Defines request/response schemas and data entities for the web module.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


# ============================================================================
# Enums
# ============================================================================

class JobStatus(str, Enum):
    """Processing job state enumeration."""
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class SSEMessageType(str, Enum):
    """Server-Sent Event message type discriminator."""
    PROGRESS = "PROGRESS"
    ANSWER = "ANSWER"
    ERROR = "ERROR"
    COMPLETE = "COMPLETE"
    STATUS = "STATUS"
    ROW_STARTED = "ROW_STARTED"  # Sent when a row begins processing
    AGENT_PROGRESS = "AGENT_PROGRESS"  # Sent when agent changes within a row


# ============================================================================
# Configuration Models
# ============================================================================

class SessionConfig(BaseModel):
    """User-configurable settings for question processing."""
    context: str = Field(default="Microsoft Azure AI", min_length=1)
    char_limit: int = Field(default=2000, ge=100, le=10000)


# ============================================================================
# Session Models
# ============================================================================

class WebSession(BaseModel):
    """Represents an active user session in the web browser."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    config: SessionConfig = Field(default_factory=SessionConfig)
    has_workbook: bool = False
    temp_file_path: Optional[str] = None

    class Config:
        from_attributes = True


class SessionCreateResponse(BaseModel):
    """Response after creating a new session."""
    session_id: str
    created_at: str
    config: SessionConfig


class SessionGetResponse(BaseModel):
    """Response for getting session state."""
    session_id: str
    created_at: str
    config: SessionConfig
    has_workbook: bool
    processing_status: Optional[str] = None


class SessionConfigUpdate(BaseModel):
    """Request to update session configuration."""
    context: Optional[str] = Field(default=None, min_length=1)
    char_limit: Optional[int] = Field(default=None, ge=100, le=10000)


class SessionConfigUpdateResponse(BaseModel):
    """Response after updating session config."""
    session_id: str
    config: SessionConfig


# ============================================================================
# Processing Job Models
# ============================================================================

class ProcessingJob(BaseModel):
    """Represents an active spreadsheet batch processing task."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    status: JobStatus = JobStatus.RUNNING
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_rows: int = Field(gt=0)
    processed_rows: int = Field(default=0, ge=0)
    current_row: Optional[int] = None
    error: Optional[str] = None

    @field_validator('processed_rows')
    @classmethod
    def validate_processed_rows(cls, v, info):
        if 'total_rows' in info.data and v > info.data['total_rows']:
            raise ValueError('processed_rows cannot exceed total_rows')
        return v


# ============================================================================
# SSE Models
# ============================================================================

class SSEMessage(BaseModel):
    """Server-Sent Event message structure for real-time updates."""
    type: SSEMessageType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]

    def to_sse_string(self) -> str:
        """Convert to SSE wire format."""
        import json
        payload = {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }
        return f"data: {json.dumps(payload)}\n\n"


# ============================================================================
# Question Processing Models
# ============================================================================

class QuestionRequest(BaseModel):
    """API request for single question processing."""
    session_id: str
    question: str = Field(min_length=5)
    context: str = Field(default="Microsoft Azure AI", min_length=1)
    char_limit: int = Field(default=2000, ge=100, le=10000)


class QuestionResponse(BaseModel):
    """API response for single question processing."""
    answer: str
    reasoning: str
    processing_time_seconds: float
    links_checked: int


# ============================================================================
# Spreadsheet Models
# ============================================================================

class ColumnSuggestions(BaseModel):
    """Suggested column mappings from automatic analysis."""
    sheet_name: str
    question_column: Optional[str] = None
    context_column: Optional[str] = None
    answer_column: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    auto_map_success: bool = False


class SpreadsheetUploadResponse(BaseModel):
    """API response after Excel file upload."""
    session_id: str
    filename: str
    sheets: List[str]
    columns: Dict[str, List[str]]
    suggested_columns: ColumnSuggestions
    row_count: int
    data: Dict[str, List[Dict[str, str]]] = {}  # Sheet name -> list of row dicts


class ProcessingStartRequest(BaseModel):
    """API request to start spreadsheet processing."""
    session_id: str
    sheet_name: str
    question_column: str
    context_column: Optional[str] = None
    answer_column: str
    start_row: int = Field(default=0, ge=0)
    end_row: Optional[int] = None

    @field_validator('end_row')
    @classmethod
    def validate_end_row(cls, v, info):
        if v is not None and 'start_row' in info.data and v <= info.data['start_row']:
            raise ValueError('end_row must be greater than start_row')
        return v


class ProcessingStartResponse(BaseModel):
    """API response after starting spreadsheet processing."""
    job_id: str
    session_id: str
    status: JobStatus
    total_rows: int
    processed_rows: int
    started_at: str


class ProcessingStatusResponse(BaseModel):
    """API response for processing status queries."""
    job_id: Optional[str] = None
    status: str
    processed_rows: int = 0
    total_rows: int = 0
    current_row: Optional[int] = None
    estimated_time_remaining_seconds: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    message: Optional[str] = None


class StopProcessingRequest(BaseModel):
    """API request to stop spreadsheet processing."""
    session_id: str


class StopProcessingResponse(BaseModel):
    """API response after stopping processing."""
    job_id: str
    status: JobStatus
    processed_rows: int
    total_rows: int


# ============================================================================
# Error Models
# ============================================================================

class WebErrorResponse(BaseModel):
    """Standardized error response format."""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============================================================================
# Health Check Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    azure_auth: str
    message: Optional[str] = None
