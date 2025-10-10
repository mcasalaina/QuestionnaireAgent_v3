"""Data transfer objects for the questionnaire application."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


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