"""Main entry point for the Questionnaire Agent application."""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import config_manager
from utils.azure_auth import azure_authenticator, verify_azure_connectivity
from utils.exceptions import (
    QuestionnaireError,
    ConfigurationError,
    AzureServiceError,
    NetworkError,
    AuthenticationError
)
from ui.main_window import UIManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('questionnaire_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class QuestionnaireAgentApp:
    """Main application class that coordinates all modules."""
    
    def __init__(self):
        """Initialize the application."""
        self.ui_manager: Optional[UIManager] = None
        
    async def initialize(self) -> bool:
        """Initialize application components.
        
        Returns:
            True if initialization successful, False otherwise.
        """
        try:
            logger.info("Initializing Questionnaire Agent application...")
            
            # Validate configuration
            logger.info("Validating configuration...")
            validation_result = config_manager.validate_configuration()
            
            if not validation_result.is_valid:
                logger.error(f"Configuration validation failed: {validation_result.error_message}")
                error_details = "; ".join(validation_result.error_details)
                self._show_configuration_error(error_details)
                return False
            
            logger.info(f"Configuration validated successfully (endpoint: {config_manager.get_azure_endpoint()})")
            
            # Test Azure connectivity
            logger.info("Testing Azure connectivity...")
            connectivity_ok = await verify_azure_connectivity()
            
            if not connectivity_ok:
                logger.warning("Azure connectivity test failed - will try to continue anyway")
            else:
                logger.info("Azure connectivity test passed")
            
            # Initialize UI
            logger.info("Initializing user interface...")
            self.ui_manager = UIManager()
            
            logger.info("Application initialization completed successfully")
            return True
            
        except ConfigurationError as e:
            logger.error(f"Configuration error during initialization: {e}")
            self._show_configuration_error(str(e))
            return False
            
        except AuthenticationError as e:
            logger.error(f"Authentication error during initialization: {e}")
            self._show_authentication_error(str(e))
            return False
            
        except NetworkError as e:
            logger.error(f"Network error during initialization: {e}")
            self._show_network_error(str(e))
            return False
            
        except AzureServiceError as e:
            logger.error(f"Azure service error during initialization: {e}")
            self._show_azure_service_error(str(e))
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}")
            self._show_general_error(f"Unexpected initialization error: {e}")
            return False
    
    def run(self) -> None:
        """Run the application main loop."""
        try:
            if not self.ui_manager:
                logger.error("UI manager not initialized")
                return
            
            logger.info("Starting application main loop...")
            self.ui_manager.run()
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            self.shutdown()
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self._show_general_error(f"Application error: {e}")
            self.shutdown()
    
    def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        try:
            logger.info("Shutting down application...")
            
            if self.ui_manager:
                logger.info("Shutting down UI manager...")
                # UI manager shutdown is handled by tkinter's mainloop exit
                pass
            
            logger.info("Application shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def _show_configuration_error(self, message: str) -> None:
        """Show configuration error to user.
        
        Args:
            message: Error message.
        """
        error_details = f"""Configuration Error: {message}

Please check:
1. .env file exists and contains required values
2. Copy .env.template to .env if needed
3. Set AZURE_AI_FOUNDRY_ENDPOINT
4. Set AZURE_AI_FOUNDRY_MODEL_DEPLOYMENT_NAME
5. Set BING_CONNECTION_ID (if using web search)

Required configuration format:
AZURE_AI_FOUNDRY_ENDPOINT=https://your-project.eastus2.ai.azure.com
AZURE_AI_FOUNDRY_MODEL_DEPLOYMENT_NAME=your-model-deployment
BING_CONNECTION_ID=your-bing-connection-id"""
        
        print(f"\n{error_details}")
    
    def _show_authentication_error(self, message: str) -> None:
        """Show authentication error to user.
        
        Args:
            message: Error message.
        """
        error_details = f"""Authentication Error: {message}

Please try:
1. Run 'az login' to authenticate with Azure
2. Ensure your account has access to the Azure AI Foundry project
3. Check that your subscription is active
4. Verify project permissions

If using Visual Studio Code, you may also need to:
- Sign in to Azure in VS Code
- Reload the window after authentication"""
        
        print(f"\n{error_details}")
    
    def _show_network_error(self, message: str) -> None:
        """Show network error to user.
        
        Args:
            message: Error message.
        """
        error_details = f"""Network Error: {message}

Please check:
1. Internet connection is working
2. Firewall allows HTTPS traffic
3. Corporate proxy settings (if applicable)
4. Azure service status at status.azure.com

If behind a corporate firewall, contact your IT administrator."""
        
        print(f"\n{error_details}")
    
    def _show_azure_service_error(self, message: str) -> None:
        """Show Azure service error to user.
        
        Args:
            message: Error message.
        """
        error_details = f"""Azure Service Error: {message}

Please check:
1. Azure AI Foundry service is running
2. Your model deployment is active
3. Service quotas are not exceeded
4. Check Azure service status

You can try running in mock mode for testing."""
        
        print(f"\n{error_details}")
    
    def _show_general_error(self, message: str) -> None:
        """Show general error to user.
        
        Args:
            message: Error message.
        """
        error_details = f"""Unexpected Error: {message}

Please try:
1. Restarting the application
2. Checking log files for details
3. Running in mock mode for testing
4. Reporting the issue with error details

Check 'questionnaire_agent.log' for detailed error information."""
        
        print(f"\n{error_details}")


async def main() -> int:
    """Main entry point for the application.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    app = QuestionnaireAgentApp()
    
    try:
        # Initialize the application
        if not await app.initialize():
            logger.error("Application initialization failed")
            return 1
        
        # Run the application
        app.run()
        
        # Successful completion
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
        
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        return 1
        
    finally:
        app.shutdown()


def run_application() -> None:
    """Run the application with proper async handling."""
    try:
        if sys.platform == "win32":
            # Use ProactorEventLoop on Windows for better compatibility
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run the async main function
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\nFatal error: {e}")
        logger.error(f"Fatal error in run_application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_application()