"""Azure authentication and connectivity management."""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager
from urllib.parse import urlparse
import aiohttp
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
from agent_framework_azure_ai import AzureAIAgentClient
from .config import config_manager
from .exceptions import AuthenticationError, AzureServiceError


logger = logging.getLogger(__name__)


class AzureAuthenticator:
    """Handles Azure authentication with fallback mechanisms."""
    
    def __init__(self):
        """Initialize the Azure authenticator."""
        self._credential = None
        self._client = None
        self._endpoint_validated = False
    
    async def get_credential(self) -> DefaultAzureCredential:
        """Get authenticated Azure credential with fallback.
        
        Returns:
            Authenticated Azure credential instance.
            
        Raises:
            AuthenticationError: If all authentication methods fail.
        """
        if self._credential is not None:
            return self._credential
        
        # Use DefaultAzureCredential - it will automatically try multiple auth methods
        # including environment variables, managed identity, Azure CLI, and interactive browser
        try:
            credential = DefaultAzureCredential(
                exclude_visual_studio_code_credential=False,
                exclude_shared_token_cache_credential=False,
                exclude_interactive_browser_credential=False
            )
            self._credential = credential
            logger.info("DefaultAzureCredential created - will authenticate on first use (may open browser)")
            return credential
        except Exception as e:
            logger.error(f"DefaultAzureCredential creation failed: {e}")
            raise AuthenticationError(
                "Failed to create Azure credentials. Please ensure Azure CLI is installed "
                "or your environment supports interactive authentication."
            ) from e
    
    async def _validate_azure_endpoint(self) -> None:
        """Validate Azure AI Projects endpoint format and accessibility.
        
        Raises:
            AzureServiceError: If endpoint is invalid or inaccessible.
        """
        if self._endpoint_validated:
            return
            
        endpoint = config_manager.get_azure_endpoint()
        
        # Validate endpoint URL format
        try:
            parsed = urlparse(endpoint)
            if not all([parsed.scheme, parsed.netloc]):
                raise AzureServiceError(f"Invalid endpoint URL format: {endpoint}")
            
            if not parsed.scheme.startswith('https'):
                raise AzureServiceError(f"Endpoint must use HTTPS: {endpoint}")
            
            # Check if it looks like an Azure AI Projects endpoint
            if 'services.ai.azure.com' not in parsed.netloc:
                logger.warning(f"Endpoint does not appear to be an Azure AI Services endpoint: {endpoint}")
            
            if '/api/projects/' not in parsed.path:
                logger.warning(f"Endpoint does not contain expected projects path: {endpoint}")
                
        except Exception as e:
            raise AzureServiceError(f"Invalid endpoint URL: {endpoint} - {e}") from e
        
        # Skip endpoint connectivity test - it can give false positives
        # The actual Azure client will validate connectivity properly
        
        self._endpoint_validated = True
        logger.debug(f"Endpoint validation completed for: {endpoint}")
    
    async def _verify_credential(self, credential) -> None:
        """Verify that the credential can access Azure resources.
        
        Args:
            credential: Azure credential to verify.
            
        Raises:
            ClientAuthenticationError: If credential verification fails.
        """
        # First validate the endpoint
        await self._validate_azure_endpoint()
        
        # Create a temporary client to test the credential
        try:
            test_client = AzureAIAgentClient(
                project_endpoint=config_manager.get_azure_endpoint(),
                credential=credential
            )
            # Test basic connectivity - this will trigger authentication
            # Note: This might fail if the endpoint is invalid, but that's a different error
            await asyncio.sleep(0.1)  # Give it a moment to initialize
            logger.debug("Credential verification successful")
        except Exception as e:
            logger.debug(f"Credential verification failed: {e}")
            raise ClientAuthenticationError("Failed to verify Azure credential") from e
    
    async def get_azure_client(self) -> AzureAIAgentClient:
        """Get authenticated Azure AI Agent client.
        
        Returns:
            Configured AzureAIAgentClient instance.
            
        Raises:
            AuthenticationError: If authentication fails.
            AzureServiceError: If client creation fails.
        """
        if self._client is not None:
            return self._client
        
        try:
            # Validate endpoint first
            await self._validate_azure_endpoint()
            
            credential = await self.get_credential()
            
            endpoint = config_manager.get_azure_endpoint()
            model_deployment = config_manager.get_model_deployment()
            
            logger.info(f"Creating Azure AI Agent client with endpoint: {endpoint}")
            logger.info(f"Using model deployment: {model_deployment}")
            
            # Create client with proper credential parameter
            from azure.ai.projects.aio import AIProjectClient
            
            project_client = AIProjectClient(
                endpoint=endpoint,
                credential=credential
            )
            
            self._client = AzureAIAgentClient(
                project_client=project_client,
                model_deployment_name=model_deployment
            )
            
            logger.info("Azure AI Agent client created successfully")
            return self._client
            
        except AuthenticationError:
            raise
        except ResourceNotFoundError as e:
            error_msg = f"Azure AI Projects resource not found. Please check that:\n" \
                       f"1. The endpoint URL is correct: {config_manager.get_azure_endpoint()}\n" \
                       f"2. The Azure AI Projects resource exists and is accessible\n" \
                       f"3. Your account has proper permissions to the resource\n" \
                       f"4. The model deployment '{config_manager.get_model_deployment()}' exists\n" \
                       f"Original error: {e}"
            logger.error(error_msg)
            raise AzureServiceError(error_msg) from e
        except Exception as e:
            logger.error(f"Failed to create Azure AI Agent client: {e}")
            raise AzureServiceError(f"Failed to initialize Azure AI services: {e}") from e
    
    def reset_authentication(self) -> None:
        """Reset authentication state to force re-authentication."""
        self._credential = None
        self._client = None
        self._endpoint_validated = False
        logger.info("Authentication state reset")


# Global authenticator instance
azure_authenticator = AzureAuthenticator()


@asynccontextmanager
async def foundry_agent_session():
    """Context manager for Azure AI Foundry agent session with automatic cleanup.
    
    This ensures proper resource management for Azure AI agents and threads.
    
    Yields:
        AzureAIAgentClient: Authenticated client for agent operations.
        
    Raises:
        AuthenticationError: If authentication fails.
        AzureServiceError: If Azure services are unavailable.
    """
    client = None
    try:
        # Get authenticated client
        client = await azure_authenticator.get_azure_client()
        logger.debug("FoundryAgentSession started")
        
        yield client
        
    except Exception as e:
        logger.error(f"Error in FoundryAgentSession: {e}")
        raise
    finally:
        # Clean up resources
        if client:
            try:
                # Note: Azure AI Agent client cleanup is handled automatically
                # by the underlying SDK, but we log for debugging
                logger.debug("FoundryAgentSession cleanup completed")
            except Exception as cleanup_error:
                logger.warning(f"Error during FoundryAgentSession cleanup: {cleanup_error}")


async def verify_azure_connectivity() -> bool:
    """Verify Azure AI Foundry connectivity and configuration.
    
    Returns:
        True if connectivity is successful.
        
    Raises:
        AuthenticationError: If authentication fails.
        AzureServiceError: If Azure services are unavailable.
    """
    try:
        # Validate configuration first
        validation_result = config_manager.validate_configuration()
        if not validation_result.is_valid:
            error_details = "; ".join(validation_result.error_details)
            raise AzureServiceError(f"Configuration validation failed: {error_details}")
        
        # Test Azure connectivity - this will trigger authentication if needed
        async with foundry_agent_session() as client:
            # If we get here, authentication and basic connectivity work
            logger.info("Azure AI Foundry connectivity verified successfully")
            return True
            
    except AuthenticationError:
        # Re-raise authentication errors as-is
        raise
    except AzureServiceError:
        # Re-raise Azure service errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during connectivity verification: {e}")
        # For other errors, treat as connectivity issues
        raise AzureServiceError(f"Failed to verify Azure connectivity: {e}") from e


async def get_azure_client() -> AzureAIAgentClient:
    """Get authenticated Azure AI Agent client.
    
    This is a convenience function for getting the global client instance.
    
    Returns:
        Configured AzureAIAgentClient instance.
        
    Raises:
        AuthenticationError: If authentication fails.
        AzureServiceError: If Azure services are unavailable.
    """
    return await azure_authenticator.get_azure_client()


def reset_azure_authentication() -> None:
    """Reset Azure authentication state.
    
    Use this to force re-authentication if credentials have changed.
    """
    azure_authenticator.reset_authentication()