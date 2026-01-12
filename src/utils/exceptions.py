"""Custom exception classes for the questionnaire application."""
from __future__ import annotations


class QuestionnaireError(Exception):
    """Base exception for questionnaire application errors."""
    
    def __init__(self, message: str, details: str | None = None):
        """Initialize with message and optional details.
        
        Args:
            message: Primary error message.
            details: Additional error details or troubleshooting information.
        """
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class AzureServiceError(QuestionnaireError):
    """Azure AI Foundry service is unavailable or returned error."""
    pass


class NetworkError(QuestionnaireError):
    """Network connectivity issues prevent processing."""
    pass


class AuthenticationError(QuestionnaireError):
    """Azure authentication failed or credentials invalid."""
    pass


class ConfigurationError(QuestionnaireError):
    """Configuration is missing or invalid."""
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


class FormatPreservationError(QuestionnaireError):
    """Cannot preserve original Excel formatting in output file."""
    pass


class ResourceCreationError(QuestionnaireError):
    """Failed to create Azure AI agent resources."""
    pass


class WorkflowError(QuestionnaireError):
    """Error in multi-agent workflow execution."""
    pass


class AgentExecutionError(QuestionnaireError):
    """Individual agent execution failed."""
    pass


class LinkValidationError(QuestionnaireError):
    """Link validation or accessibility check failed."""
    pass