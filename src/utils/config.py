"""Configuration management for the questionnaire application."""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # Azure AI Foundry configuration
    azure_endpoint: str
    model_deployment: str
    bing_connection_id: str
    app_insights_connection: Optional[str] = None
    
    # Application settings
    max_retries: int = 10
    default_char_limit: int = 2000
    default_context: str = "Microsoft Azure AI"
    
    # Timeout settings (in seconds)
    agent_timeout: int = 120
    workflow_timeout: int = 300
    excel_processing_timeout: int = 1800
    
    # Tracing configuration
    tracing_enabled: bool = True


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    
    is_valid: bool
    error_message: Optional[str] = None
    error_details: list[str] = None
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []


class ConfigurationManager:
    """Manages application configuration and environment variables."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            env_file: Path to environment file. Defaults to .env in project root.
        """
        self.env_file = env_file or self._find_env_file()
        load_dotenv(self.env_file)
        self.config = self._load_config()
    
    def _find_env_file(self) -> str:
        """Find the .env file in the project root."""
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent  # Go up from src/utils to project root
        env_file = project_root / ".env"
        return str(env_file)
    
    def _load_config(self) -> AppConfig:
        """Load configuration from environment variables."""
        return AppConfig(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            model_deployment=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4.1"),
            bing_connection_id=os.getenv("BING_CONNECTION_ID", ""),
            app_insights_connection=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"),
            max_retries=int(os.getenv("MAX_RETRIES", "10")),
            default_char_limit=int(os.getenv("DEFAULT_CHAR_LIMIT", "2000")),
            default_context=os.getenv("DEFAULT_CONTEXT", "Microsoft Azure AI"),
            agent_timeout=int(os.getenv("AGENT_TIMEOUT", "120")),
            workflow_timeout=int(os.getenv("WORKFLOW_TIMEOUT", "300")),
            excel_processing_timeout=int(os.getenv("EXCEL_PROCESSING_TIMEOUT", "1800")),
            tracing_enabled=os.getenv("AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED", "true").lower() == "true"
        )
    
    def validate_configuration(self) -> ValidationResult:
        """Verify all required configuration is present and valid.
        
        Returns:
            ValidationResult with missing or invalid configuration details.
        """
        errors = []
        
        # Check required Azure configuration
        if not self.config.azure_endpoint:
            errors.append("AZURE_OPENAI_ENDPOINT is required")
        elif not self.config.azure_endpoint.startswith("https://"):
            errors.append("AZURE_OPENAI_ENDPOINT must be a valid HTTPS URL")
        
        if not self.config.model_deployment:
            errors.append("AZURE_OPENAI_MODEL_DEPLOYMENT is required")
        
        if not self.config.bing_connection_id:
            errors.append("BING_CONNECTION_ID is required")
        
        # Validate numeric settings
        if self.config.max_retries < 1 or self.config.max_retries > 25:
            errors.append("MAX_RETRIES must be between 1 and 25")
        
        if self.config.default_char_limit < 100 or self.config.default_char_limit > 10000:
            errors.append("DEFAULT_CHAR_LIMIT must be between 100 and 10000")
        
        # Validate timeout settings
        if self.config.agent_timeout < 30:
            errors.append("AGENT_TIMEOUT must be at least 30 seconds")
        
        if self.config.workflow_timeout < 60:
            errors.append("WORKFLOW_TIMEOUT must be at least 60 seconds")
        
        if self.config.excel_processing_timeout < 300:
            errors.append("EXCEL_PROCESSING_TIMEOUT must be at least 300 seconds")
        
        is_valid = len(errors) == 0
        error_message = None if is_valid else f"Configuration validation failed: {len(errors)} errors found"
        
        return ValidationResult(
            is_valid=is_valid,
            error_message=error_message,
            error_details=errors
        )
    
    def get_model_deployment(self) -> str:
        """Get the configured model deployment name.
        
        Returns:
            Model deployment identifier for Azure AI Foundry.
        """
        return self.config.model_deployment
    
    def get_retry_settings(self) -> tuple[int, int]:
        """Get configured retry and timeout settings.
        
        Returns:
            Tuple of (max_attempts, timeout_seconds).
        """
        return self.config.max_retries, self.config.agent_timeout
    
    def is_tracing_enabled(self) -> bool:
        """Check if Azure tracing is enabled.
        
        Returns:
            True if tracing should be enabled.
        """
        return self.config.tracing_enabled
    
    def get_azure_endpoint(self) -> str:
        """Get the Azure AI Foundry endpoint URL.
        
        Returns:
            Full endpoint URL for Azure AI Foundry project.
        """
        return self.config.azure_endpoint
    
    def get_bing_connection_id(self) -> str:
        """Get the Bing search connection identifier.
        
        Returns:
            Connection ID for Bing search service.
        """
        return self.config.bing_connection_id
    
    def get_app_insights_connection(self) -> Optional[str]:
        """Get the Application Insights connection string.
        
        Returns:
            Connection string for Application Insights, or None if not configured.
        """
        return self.config.app_insights_connection


# Global configuration instance
config_manager = ConfigurationManager()