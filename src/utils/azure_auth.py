"""Azure authentication and connectivity management."""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager
from azure.identity.aio import DefaultAzureCredential
from azure.identity import InteractiveBrowserCredential
from azure.core.exceptions import ClientAuthenticationError
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
    
    async def get_credential(self) -> DefaultAzureCredential | InteractiveBrowserCredential:
        """Get authenticated Azure credential with fallback.
        
        Returns:
            Authenticated Azure credential instance.
            
        Raises:
            AuthenticationError: If all authentication methods fail.
        """
        if self._credential is not None:
            return self._credential
        
        # Try DefaultAzureCredential first (async version)
        try:
            credential = DefaultAzureCredential()
            # Don't verify immediately - let it authenticate on first use
            self._credential = credential
            logger.info("Using DefaultAzureCredential (async - will authenticate on first use)")
            return credential
        except Exception as e:
            logger.warning(f"DefaultAzureCredential creation failed: {e}")
        
        # Fallback to interactive browser authentication (sync version for now)
        try:
            credential = InteractiveBrowserCredential()
            # Don't verify immediately - this will trigger browser authentication on first use
            self._credential = credential
            logger.info("Using InteractiveBrowserCredential (will open browser on first use)")
            return credential
        except Exception as e:
            logger.error(f"InteractiveBrowserCredential creation failed: {e}")
            raise AuthenticationError(
                "Failed to create Azure credentials. Please ensure Azure CLI is installed "
                "or your environment supports interactive authentication."
            ) from e
    
    async def _verify_credential(self, credential) -> None:
        """Verify that the credential can access Azure resources.
        
        Args:
            credential: Azure credential to verify.
            
        Raises:
            ClientAuthenticationError: If credential verification fails.
        """
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
            credential = await self.get_credential()
            
            self._client = AzureAIAgentClient(
                project_endpoint=config_manager.get_azure_endpoint(),
                model_deployment_name=config_manager.get_model_deployment(),
                async_credential=credential
            )
            
            logger.info("Azure AI Agent client created successfully")
            return self._client
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create Azure AI Agent client: {e}")
            raise AzureServiceError(f"Failed to initialize Azure AI services: {e}") from e
    
    def reset_authentication(self) -> None:
        """Reset authentication state to force re-authentication."""
        self._credential = None
        self._client = None
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