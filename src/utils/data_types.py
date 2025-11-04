"""Data transfer objects for the questionnaire application."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import time


class AgentType(Enum):
    """Types of agents in the multi-agent workflow."""
    QUESTION_ANSWERER = "question_answerer"
    ANSWER_CHECKER = "answer_checker"
    LINK_CHECKER = "link_checker"


class ValidationStatus(Enum):
    """Status of answer validation process."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED_CONTENT = "rejected_content"
    REJECTED_LINKS = "rejected_links"
    FAILED_TIMEOUT = "failed_timeout"


class StepStatus(Enum):
    """Status of individual agent workflow steps."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class ProcessingStatus(Enum):
    """Status of overall processing operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentInitState(Enum):
    """State of agent initialization process.
    
    Note: While this enum shares some values with ProcessingStatus,
    they represent different concepts and having separate enums provides
    better type safety and clarity in the codebase.
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Question:
    """Represents a user-submitted question requiring research and validation."""
    
    text: str
    context: str = "Microsoft Azure AI"
    char_limit: int = 2000
    max_retries: int = 10
    id: Optional[str] = None
    
    def __post_init__(self):
        """Validate question parameters."""
        if not self.text or len(self.text.strip()) < 5:
            raise ValueError("Question text must be at least 5 characters long")
        
        if self.char_limit < 100 or self.char_limit > 10000:
            raise ValueError("Character limit must be between 100 and 10000")
        
        if self.max_retries < 1 or self.max_retries > 25:
            raise ValueError("Max retries must be between 1 and 25")


@dataclass
class AgentStep:
    """Individual agent execution record in the workflow."""
    
    agent_name: AgentType
    input_data: str
    output_data: str
    execution_time: float
    status: StepStatus
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate agent step parameters."""
        if self.execution_time < 0:
            raise ValueError("Execution time must be positive")
        
        if self.status == StepStatus.FAILURE and not self.error_message:
            raise ValueError("Error message required when status is FAILURE")


@dataclass
class DocumentationLink:
    """Verified URL supporting the answer content."""
    
    url: str
    title: Optional[str] = None
    is_reachable: bool = False
    is_relevant: bool = False
    http_status: Optional[int] = None
    validation_error: Optional[str] = None
    
    def __post_init__(self):
        """Validate URL format."""
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError("URL must be a valid HTTP/HTTPS format")
    
    @property
    def is_valid(self) -> bool:
        """Check if link is valid for inclusion."""
        return self.is_reachable and self.is_relevant


@dataclass
class Answer:
    """Generated response that has passed multi-agent validation."""
    
    content: str
    sources: list[str] = field(default_factory=list)
    agent_reasoning: list[AgentStep] = field(default_factory=list)
    char_count: int = 0
    validation_status: ValidationStatus = ValidationStatus.PENDING
    retry_count: int = 0
    documentation_links: list[DocumentationLink] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate character count and validate content."""
        self.char_count = len(self.content)
    
    @property
    def is_approved(self) -> bool:
        """Check if answer is approved for delivery."""
        return self.validation_status == ValidationStatus.APPROVED
    
    @property
    def valid_links(self) -> list[DocumentationLink]:
        """Get only valid documentation links."""
        return [link for link in self.documentation_links if link.is_valid]


@dataclass
class ProcessingResult:
    """Result of single question or Excel batch processing."""
    
    success: bool
    answer: Optional[Answer] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    questions_processed: int = 0
    questions_failed: int = 0
    
    def __post_init__(self):
        """Validate processing result consistency."""
        if self.processing_time < 0:
            raise ValueError("Processing time must be positive")
        
        if self.success and not self.answer:
            raise ValueError("Answer required when success is True")
        
        if not self.success and not self.error_message:
            raise ValueError("Error message required when success is False")


@dataclass
class ExcelSheet:
    """Individual worksheet within an Excel workbook."""
    
    name: str
    question_column: Optional[str] = None
    answer_column: Optional[str] = None
    documentation_column: Optional[str] = None
    rows: list[dict] = field(default_factory=list)
    has_headers: bool = True
    
    def __post_init__(self):
        """Validate sheet configuration."""
        if not self.question_column and not self.answer_column:
            raise ValueError("At least one of question_column or answer_column must be specified")


@dataclass
class ColumnMapping:
    """Identified question and answer columns in Excel worksheets."""
    
    sheet_mappings: dict[str, ExcelSheet] = field(default_factory=dict)
    confidence_score: float = 0.0
    
    def __post_init__(self):
        """Validate column mapping confidence."""
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")


@dataclass
class ExcelWorkbook:
    """Represents loaded Excel file with identified columns."""
    
    file_path: str
    sheets: list[ExcelSheet] = field(default_factory=list)
    column_mapping: Optional[ColumnMapping] = None
    total_questions: int = 0
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    
    @property
    def has_questions(self) -> bool:
        """Check if workbook contains any questions to process."""
        return self.total_questions > 0


@dataclass
class ExcelProcessingResult:
    """Result of Excel batch processing operation."""
    
    success: bool
    output_file_path: Optional[str] = None
    results: list[ProcessingResult] = field(default_factory=list)
    questions_processed: int = 0
    questions_failed: int = 0
    error_message: Optional[str] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        """Validate Excel processing result consistency."""
        if self.processing_time < 0:
            raise ValueError("Processing time must be positive")
        
        if self.success and not self.output_file_path:
            raise ValueError("Output file path required when success is True")
        
        if not self.success and not self.error_message:
            raise ValueError("Error message required when success is False")
    
    @property
    def total_questions(self) -> int:
        """Get total number of questions processed."""
        return self.questions_processed + self.questions_failed
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.questions_processed / self.total_questions) * 100


@dataclass
class ValidationResult:
    """Result of validation operation."""
    
    is_valid: bool
    error_message: Optional[str] = None
    error_details: list[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return not self.is_valid or len(self.error_details) > 0


@dataclass
class HealthStatus:
    """System health and service availability status."""
    
    azure_connectivity: bool = False
    authentication_valid: bool = False
    configuration_valid: bool = False
    agent_services_available: bool = False
    error_details: list[str] = field(default_factory=list)
    
    @property
    def is_healthy(self) -> bool:
        """Check if all systems are healthy."""
        return (
            self.azure_connectivity and
            self.authentication_valid and
            self.configuration_valid and
            self.agent_services_available
        )


@dataclass
class RetrySettings:
    """Retry and timeout configuration settings."""
    
    max_attempts: int = 10
    timeout_seconds: int = 120
    exponential_backoff: bool = True
    base_delay: float = 1.0
    max_delay: float = 60.0
    
    def __post_init__(self):
        """Validate retry settings."""
        if self.max_attempts < 1:
            raise ValueError("Max attempts must be at least 1")
        
        if self.timeout_seconds < 30:
            raise ValueError("Timeout must be at least 30 seconds")
        
        if self.base_delay <= 0:
            raise ValueError("Base delay must be positive")
        
        if self.max_delay < self.base_delay:
            raise ValueError("Max delay must be greater than or equal to base delay")


# Live Excel Processing Data Types

class CellState(Enum):
    """Processing state of a single response cell."""
    PENDING = "pending"
    WORKING = "working"
    COMPLETED = "completed"


@dataclass
class SheetData:
    """Data for a single Excel sheet."""
    sheet_name: str
    sheet_index: int
    questions: List[str]
    answers: List[Optional[str]]
    cell_states: List[CellState]
    is_processing: bool = False
    is_complete: bool = False
    question_col_index: Optional[int] = None
    response_col_index: Optional[int] = None
    documentation_col_index: Optional[int] = None
    
    def __post_init__(self):
        """Validate invariants."""
        if len(self.questions) != len(self.answers) or len(self.questions) != len(self.cell_states):
            raise ValueError("Questions, answers, and cell_states must have the same length")
        
        if len(self.sheet_name) > 31:
            raise ValueError("Sheet name cannot exceed 31 characters (Excel limit)")
    
    def get_progress(self) -> float:
        """Return completion percentage (0.0 to 1.0)."""
        if not self.questions:
            return 0.0
        completed = sum(1 for s in self.cell_states if s == CellState.COMPLETED)
        return completed / len(self.questions)
    
    def get_pending_questions(self) -> List[tuple[int, str]]:
        """Returns indices and text of questions in PENDING state."""
        return [
            (idx, question) 
            for idx, (question, state) in enumerate(zip(self.questions, self.cell_states))
            if state == CellState.PENDING
        ]
    
    def mark_working(self, row_index: int) -> None:
        """Transitions cell to WORKING state."""
        if 0 <= row_index < len(self.cell_states):
            self.cell_states[row_index] = CellState.WORKING
    
    def mark_completed(self, row_index: int, answer: str) -> None:
        """Transitions cell to COMPLETED with answer."""
        if 0 <= row_index < len(self.cell_states):
            self.cell_states[row_index] = CellState.COMPLETED
            self.answers[row_index] = answer
            
            # Update completion status
            self.is_complete = all(s == CellState.COMPLETED for s in self.cell_states)


@dataclass
class WorkbookData:
    """Data for entire Excel workbook."""
    file_path: str
    sheets: List[SheetData]
    current_sheet_index: int = 0
    
    def __post_init__(self):
        """Validate workbook data."""
        if not self.sheets:
            raise ValueError("Workbook must contain at least one sheet")
        
        if self.current_sheet_index < 0 or self.current_sheet_index >= len(self.sheets):
            raise ValueError("Current sheet index out of range")
        
        if len(self.sheets) > 10:
            raise ValueError("Maximum 10 sheets supported")
    
    @property
    def total_questions(self) -> int:
        """Total questions across all sheets."""
        return sum(len(sheet.questions) for sheet in self.sheets)
    
    @property
    def completed_questions(self) -> int:
        """Total completed questions across all sheets."""
        return sum(
            sum(1 for s in sheet.cell_states if s == CellState.COMPLETED)
            for sheet in self.sheets
        )
    
    def get_active_sheet(self) -> Optional[SheetData]:
        """Returns currently processing sheet."""
        for sheet in self.sheets:
            if sheet.is_processing:
                return sheet
        return None
    
    def advance_to_next_sheet(self) -> bool:
        """Moves to next sheet, returns False if no more sheets."""
        # Mark current sheet as not processing
        if self.current_sheet_index < len(self.sheets):
            self.sheets[self.current_sheet_index].is_processing = False
        
        # Find next incomplete sheet
        for idx in range(self.current_sheet_index + 1, len(self.sheets)):
            if not self.sheets[idx].is_complete:
                self.current_sheet_index = idx
                self.sheets[idx].is_processing = True
                return True
        
        return False
    
    def get_overall_progress(self) -> float:
        """Returns global completion percentage."""
        if self.total_questions == 0:
            return 0.0
        return self.completed_questions / self.total_questions
    
    def is_complete(self) -> bool:
        """Returns True if all sheets complete."""
        return all(sheet.is_complete for sheet in self.sheets)


@dataclass
class NavigationState:
    """Tracks user interaction with sheet tabs to control auto-navigation."""
    user_selected_sheet: Optional[int] = None
    
    @property
    def auto_navigation_enabled(self) -> bool:
        """Whether system can auto-navigate."""
        return self.user_selected_sheet is None
    
    def lock_to_sheet(self, sheet_index: int) -> None:
        """User clicked tab, disable auto-navigation."""
        self.user_selected_sheet = sheet_index
    
    def enable_auto_navigation(self) -> None:
        """Clear user selection, enable auto-navigation."""
        self.user_selected_sheet = None
    
    def should_navigate_to(self, sheet_index: int) -> bool:
        """Returns True if the view should switch to the given sheet."""
        if self.user_selected_sheet is None:
            return True  # Auto-navigation enabled
        return False  # User has control


@dataclass
class UIUpdateEvent:
    """Event from background processing workflow to UI thread."""
    event_type: str  # SHEET_START, CELL_WORKING, CELL_COMPLETED, etc.
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Validate event data."""
        valid_types = {
            'SHEET_START', 'CELL_WORKING', 'CELL_COMPLETED', 
            'CELL_RESET', 'CELL_CANCELLED',
            'SHEET_COMPLETE', 'WORKBOOK_COMPLETE', 'ERROR'
        }
        if self.event_type not in valid_types:
            raise ValueError(f"Invalid event type: {self.event_type}")
        
        if not isinstance(self.payload, dict):
            raise ValueError("Payload must be a dictionary")