# Module Interface Contracts

**Date**: 2025-10-09  
**Purpose**: Define interface contracts between UI, Excel, and Agent modules using direct method calls

## UI Manager Interface

**Module**: `ui/main_window.py`  
**Responsibility**: GUI interface management and user interaction handling

```python
class UIManager:
    """Main GUI interface for the questionnaire application."""
    
    def __init__(self, agent_coordinator: AgentCoordinator):
        """Initialize UI with agent coordinator dependency."""
        pass
    
    def process_single_question(
        self, 
        question: str, 
        context: str = "Microsoft Azure AI", 
        char_limit: int = 2000,
        max_retries: int = 10
    ) -> ProcessingResult:
        """
        Process a single question through the multi-agent workflow.
        
        Args:
            question: User's natural language question
            context: Domain context for the question
            char_limit: Maximum characters for answer
            max_retries: Maximum retry attempts
            
        Returns:
            ProcessingResult with answer or error details
            
        Raises:
            ValueError: If question is empty or parameters invalid
            NetworkError: If connectivity issues prevent processing
            AuthenticationError: If Azure credentials are invalid
        """
        pass
    
    def import_excel_file(self, file_path: str) -> ExcelProcessingResult:
        """
        Process questions from Excel file through batch workflow.
        
        Args:
            file_path: Absolute path to Excel file
            
        Returns:
            ExcelProcessingResult with processed data or error details
            
        Raises:
            FileNotFoundError: If Excel file doesn't exist
            ExcelFormatError: If file format is unsupported
            ColumnIdentificationError: If question columns cannot be identified
        """
        pass
    
    def update_progress(self, agent: str, message: str, progress: float) -> None:
        """
        Update UI with current processing progress.
        
        Args:
            agent: Current agent name (question_answerer, answer_checker, link_checker)
            message: Status message for reasoning panel
            progress: Completion percentage (0.0 to 1.0)
        """
        pass
    
    def display_error(
        self, 
        error_type: str, 
        message: str, 
        details: Optional[str] = None
    ) -> None:
        """
        Display error dialog with specific failure information.
        
        Args:
            error_type: Category of error (azure_service, network, excel_format)
            message: Primary error message
            details: Additional troubleshooting information
        """
        pass
```

## Excel Processor Interface

**Module**: `excel/processor.py`  
**Responsibility**: Excel file loading, processing, and output generation

```python
class ExcelProcessor:
    """Handles Excel file operations for batch question processing."""
    
    def __init__(self, column_identifier: ColumnIdentifier):
        """Initialize with column identification service."""
        pass
    
    def load_file(self, file_path: str) -> ExcelWorkbook:
        """
        Load and validate Excel file structure.
        
        Args:
            file_path: Absolute path to Excel file
            
        Returns:
            ExcelWorkbook with loaded sheet data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ExcelFormatError: If file format is unsupported or corrupted
            PermissionError: If file is locked or read-only
        """
        pass
    
    def identify_columns(self, workbook: ExcelWorkbook) -> ColumnMapping:
        """
        Use AI to identify question and answer columns in worksheets.
        
        Args:
            workbook: Loaded Excel workbook data
            
        Returns:
            ColumnMapping with identified column locations
            
        Raises:
            ColumnIdentificationError: If no valid question columns found
            AzureServiceError: If AI analysis service fails
        """
        pass
    
    def save_results(
        self, 
        workbook: ExcelWorkbook, 
        results: List[QuestionResult],
        output_path: str
    ) -> str:
        """
        Save processed results to new Excel file preserving formatting.
        
        Args:
            workbook: Original workbook structure
            results: Processed question answers
            output_path: Target file location
            
        Returns:
            Absolute path to saved output file
            
        Raises:
            PermissionError: If cannot write to output location
            FormatPreservationError: If original formatting cannot be maintained
        """
        pass
    
    def validate_file_format(self, file_path: str) -> ValidationResult:
        """
        Check if Excel file can be processed by the application.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            ValidationResult with specific format issues if any
        """
        pass
```

## Agent Coordinator Interface

**Module**: `agents/workflow_manager.py`  
**Responsibility**: Microsoft Agent Framework orchestration and multi-agent workflow execution

```python
class AgentCoordinator:
    """Orchestrates multi-agent workflow using Microsoft Agent Framework."""
    
    def __init__(self, azure_client: AzureAIAgentClient):
        """Initialize with Azure AI client for agent creation."""
        pass
    
    def process_question(
        self, 
        question: Question,
        progress_callback: Callable[[str, str, float], None]
    ) -> ProcessingResult:
        """
        Execute multi-agent workflow for single question.
        
        Args:
            question: Question with context and limits
            progress_callback: Function to report workflow progress
            
        Returns:
            ProcessingResult with validated answer or failure details
            
        Raises:
            AzureServiceError: If agent services are unavailable
            ValidationTimeoutError: If validation exceeds time limits
            MaxRetriesExceededError: If retry limit reached without valid answer
        """
        pass
    
    def process_batch(
        self, 
        questions: List[Question],
        progress_callback: Callable[[str, str, float], None]
    ) -> List[ProcessingResult]:
        """
        Execute multi-agent workflow for multiple questions.
        
        Args:
            questions: List of questions to process
            progress_callback: Function to report batch progress
            
        Returns:
            List of ProcessingResult for each question
            
        Raises:
            AzureServiceError: If agent services become unavailable during batch
        """
        pass
    
    def create_agents(self) -> None:
        """
        Initialize the three specialized agents with Azure AI Foundry.
        
        Raises:
            AuthenticationError: If Azure credentials are invalid
            ResourceCreationError: If agent creation fails
        """
        pass
    
    def cleanup_agents(self) -> None:
        """
        Clean up Azure AI agent resources using FoundryAgentSession.
        """
        pass
    
    def health_check(self) -> HealthStatus:
        """
        Verify Azure AI Foundry connectivity and agent availability.
        
        Returns:
            HealthStatus with service availability details
        """
        pass
```

## Configuration Manager Interface

**Module**: `utils/config.py`  
**Responsibility**: Environment configuration and Azure authentication management

```python
class ConfigurationManager:
    """Manages application configuration and Azure authentication."""
    
    def __init__(self):
        """Load configuration from environment variables and .env file."""
        pass
    
    def validate_configuration(self) -> ValidationResult:
        """
        Verify all required configuration is present and valid.
        
        Returns:
            ValidationResult with missing or invalid configuration details
        """
        pass
    
    def get_azure_client(self) -> AzureAIAgentClient:
        """
        Create authenticated Azure AI client with fallback authentication.
        
        Returns:
            Configured AzureAIAgentClient instance
            
        Raises:
            AuthenticationError: If all authentication methods fail
            ConfigurationError: If required settings are missing
        """
        pass
    
    def get_model_deployment(self) -> str:
        """
        Get the configured model deployment name.
        
        Returns:
            Model deployment identifier for Azure AI Foundry
        """
        pass
    
    def get_retry_settings(self) -> RetrySettings:
        """
        Get configured retry and timeout settings.
        
        Returns:
            RetrySettings with max attempts and timeout values
        """
        pass
```

## Error Types

**Module**: `utils/exceptions.py`  
**Purpose**: Custom exception types for specific error handling

```python
class QuestionnaireError(Exception):
    """Base exception for questionnaire application errors."""
    pass

class AzureServiceError(QuestionnaireError):
    """Azure AI Foundry service is unavailable or returned error."""
    pass

class NetworkError(QuestionnaireError):
    """Network connectivity issues prevent processing."""
    pass

class AuthenticationError(QuestionnaireError):
    """Azure authentication failed or credentials invalid."""
    pass

class ExcelFormatError(QuestionnaireError):
    """Excel file format is unsupported or corrupted."""
    pass

class ColumnIdentificationError(QuestionnaireError):
    """Cannot identify question/answer columns in Excel file."""
    pass

class ValidationTimeoutError(QuestionnaireError):
    """Agent validation exceeded configured timeout."""
    pass

class MaxRetriesExceededError(QuestionnaireError):
    """Maximum retry attempts reached without valid answer."""
    pass
```

## Data Transfer Objects

**Module**: `utils/data_types.py`  
**Purpose**: Shared data structures for module communication

```python
@dataclass
class Question:
    """User question with processing parameters."""
    text: str
    context: str = "Microsoft Azure AI"
    char_limit: int = 2000
    max_retries: int = 10
    id: Optional[str] = None

@dataclass
class ProcessingResult:
    """Result of question processing operation."""
    success: bool
    answer: Optional[Answer] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    retry_count: int = 0

@dataclass
class ExcelProcessingResult:
    """Result of Excel batch processing operation."""
    success: bool
    output_file_path: Optional[str] = None
    results: List[ProcessingResult] = field(default_factory=list)
    questions_processed: int = 0
    questions_failed: int = 0
    error_message: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    error_message: Optional[str] = None
    error_details: List[str] = field(default_factory=list)
```
