"""Structured logging setup with Azure tracing integration."""

import logging
import sys
from typing import Optional
from pathlib import Path
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from .config import config_manager


class QuestionnaireLogger:
    """Centralized logging configuration for the questionnaire application."""
    
    def __init__(self):
        """Initialize the logging system."""
        self._configured = False
        self._tracer = None
    
    def setup_logging(self, debug: bool = False) -> None:
        """Configure structured logging for the application.
        
        Args:
            debug: Whether to enable debug level logging.
        """
        if self._configured:
            return
        
        # Configure basic logging
        log_level = logging.DEBUG if debug else logging.INFO
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                # Console handler
                logging.StreamHandler(sys.stdout),
                # File handler
                logging.FileHandler(log_dir / "questionnaire_agent.log", encoding='utf-8')
            ]
        )
        
        # Configure Azure SDK logging
        if debug:
            logging.getLogger('azure').setLevel(logging.DEBUG)
            logging.getLogger('agent_framework').setLevel(logging.DEBUG)
        else:
            logging.getLogger('azure').setLevel(logging.WARNING)
            logging.getLogger('agent_framework').setLevel(logging.INFO)
        
        # Suppress verbose libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        
        self._configured = True
        
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured - Level: {logging.getLevelName(log_level)}")
    
    def setup_azure_tracing(self) -> None:
        """Configure Azure Application Insights tracing.
        
        This enables distributed tracing for Azure AI operations.
        """
        if not config_manager.is_tracing_enabled():
            logging.getLogger(__name__).info("Azure tracing disabled by configuration")
            return
        
        connection_string = config_manager.get_app_insights_connection()
        if not connection_string:
            logging.getLogger(__name__).warning("Application Insights connection string not configured")
            return
        
        try:
            # Configure Azure Monitor with Application Insights
            configure_azure_monitor(
                connection_string=connection_string,
                enable_live_metrics=True,
                enable_standard_metrics=True,
                enable_logging=True
            )
            
            # Get the tracer for application-specific spans
            self._tracer = trace.get_tracer(__name__)
            
            logging.getLogger(__name__).info("Azure Application Insights tracing configured")
            
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to configure Azure tracing: {e}")
    
    def get_tracer(self) -> Optional[trace.Tracer]:
        """Get the Azure tracer for creating custom spans.
        
        Returns:
            OpenTelemetry tracer instance, or None if tracing not configured.
        """
        return self._tracer
    
    def setup_debug_logging(self) -> None:
        """Enable detailed debug logging for troubleshooting."""
        # Set debug level for our application modules
        logging.getLogger('src').setLevel(logging.DEBUG)
        logging.getLogger('agents').setLevel(logging.DEBUG)
        logging.getLogger('utils').setLevel(logging.DEBUG)
        logging.getLogger('ui').setLevel(logging.DEBUG)
        logging.getLogger('excel').setLevel(logging.DEBUG)
        
        # Enable Azure SDK debug logging
        logging.getLogger('azure').setLevel(logging.DEBUG)
        logging.getLogger('agent_framework').setLevel(logging.DEBUG)
        
        logger = logging.getLogger(__name__)
        logger.info("Debug logging enabled for all application modules")


# Global logger instance
questionnaire_logger = QuestionnaireLogger()


def setup_logging(debug: bool = False) -> None:
    """Setup application logging.
    
    Args:
        debug: Whether to enable debug level logging.
    """
    questionnaire_logger.setup_logging(debug)
    questionnaire_logger.setup_azure_tracing()


def setup_debug_logging() -> None:
    """Enable detailed debug logging for troubleshooting."""
    questionnaire_logger.setup_debug_logging()


def get_tracer() -> Optional[trace.Tracer]:
    """Get the Azure tracer for creating custom spans.
    
    Returns:
        OpenTelemetry tracer instance, or None if tracing not configured.
    """
    return questionnaire_logger.get_tracer()


def create_span(name: str, **attributes):
    """Create a custom tracing span.
    
    Args:
        name: Name of the span.
        **attributes: Additional span attributes.
        
    Returns:
        Span context manager, or a no-op context if tracing not available.
    """
    tracer = get_tracer()
    if tracer:
        span = tracer.start_span(name)
        for key, value in attributes.items():
            span.set_attribute(key, value)
        return span
    else:
        # Return a no-op context manager
        from contextlib import nullcontext
        return nullcontext()


def log_agent_step(agent_name: str, step: str, status: str, duration: float = None) -> None:
    """Log an agent workflow step with structured data.
    
    Args:
        agent_name: Name of the agent (question_answerer, answer_checker, link_checker).
        step: Description of the step being performed.
        status: Status of the step (started, completed, failed).
        duration: Duration in seconds if step is completed.
    """
    logger = logging.getLogger(f"agents.{agent_name}")
    
    extra = {
        'agent': agent_name,
        'step': step,
        'status': status
    }
    
    if duration is not None:
        extra['duration'] = duration
    
    if status == "failed":
        logger.error(f"Agent step failed: {step}", extra=extra)
    elif status == "completed":
        duration_str = f" ({duration:.2f}s)" if duration else ""
        logger.info(f"Agent step completed: {step}{duration_str}", extra=extra)
    else:
        logger.info(f"Agent step {status}: {step}", extra=extra)


def log_workflow_progress(current_step: int, total_steps: int, description: str) -> None:
    """Log workflow progress with structured data.
    
    Args:
        current_step: Current step number (1-based).
        total_steps: Total number of steps.
        description: Description of current step.
    """
    logger = logging.getLogger("workflow")
    
    progress = (current_step / total_steps) * 100
    
    logger.info(
        f"Workflow progress: Step {current_step}/{total_steps} ({progress:.1f}%) - {description}",
        extra={
            'current_step': current_step,
            'total_steps': total_steps,
            'progress_percent': progress,
            'description': description
        }
    )