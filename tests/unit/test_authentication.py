"""Unit tests for Azure authentication functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError

# Add src to path
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from utils.azure_auth import test_authentication as verify_auth, AzureAuthenticator
from utils.exceptions import AuthenticationError


class TestAuthenticationFlow:
    """Test authentication flow and immediate login testing."""
    
    @pytest.mark.asyncio
    async def test_authentication_success(self):
        """Test successful authentication returns true."""
        with patch('utils.azure_auth.azure_authenticator') as mock_auth:
            # Mock credential that returns a valid token
            mock_credential = Mock()
            mock_token = AccessToken(token="valid_token", expires_on=9999999999)
            mock_credential.get_token.return_value = mock_token
            
            mock_auth.get_credential = AsyncMock(return_value=mock_credential)
            
            # Test authentication
            result = await verify_auth()
            
            assert result is True
            mock_credential.get_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_failure_raises_error(self):
        """Test authentication failure raises AuthenticationError."""
        with patch('utils.azure_auth.azure_authenticator') as mock_auth:
            # Mock credential that fails to get token
            mock_credential = Mock()
            mock_credential.get_token.side_effect = ClientAuthenticationError("Auth failed")
            
            mock_auth.get_credential = AsyncMock(return_value=mock_credential)
            
            # Test authentication should raise error
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_auth()
            
            assert "Azure authentication failed" in str(exc_info.value)
            assert "az login" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_authentication_token_request_uses_correct_scope(self):
        """Test that authentication requests token with correct scope."""
        with patch('utils.azure_auth.azure_authenticator') as mock_auth:
            mock_credential = Mock()
            mock_token = AccessToken(token="valid_token", expires_on=9999999999)
            mock_credential.get_token.return_value = mock_token
            
            mock_auth.get_credential = AsyncMock(return_value=mock_credential)
            
            await verify_auth()
            
            # Verify the scope used for token request
            call_args = mock_credential.get_token.call_args
            assert "https://management.azure.com/.default" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_authenticator_caches_credential(self):
        """Test that authenticator caches credential after first use."""
        authenticator = AzureAuthenticator()
        
        with patch('utils.azure_auth.DefaultAzureCredential') as mock_cred_class:
            mock_credential = Mock()
            mock_cred_class.return_value = mock_credential
            
            # First call should create credential
            cred1 = await authenticator.get_credential()
            
            # Second call should return cached credential
            cred2 = await authenticator.get_credential()
            
            assert cred1 is cred2
            mock_cred_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticator_enables_interactive_browser(self):
        """Test that authenticator enables interactive browser credential."""
        authenticator = AzureAuthenticator()
        
        with patch('utils.azure_auth.DefaultAzureCredential') as mock_cred_class:
            await authenticator.get_credential()
            
            # Verify interactive browser credential is enabled
            call_kwargs = mock_cred_class.call_args.kwargs
            assert call_kwargs.get('exclude_interactive_browser_credential') is False
    
    @pytest.mark.asyncio
    async def test_reset_authentication_clears_cache(self):
        """Test that reset_authentication clears cached credential."""
        authenticator = AzureAuthenticator()
        
        with patch('utils.azure_auth.DefaultAzureCredential') as mock_cred_class:
            mock_credential = Mock()
            mock_cred_class.return_value = mock_credential
            
            # Get credential
            await authenticator.get_credential()
            
            # Reset authentication
            authenticator.reset_authentication()
            
            # Get credential again - should create new instance
            await authenticator.get_credential()
            
            # Should be called twice (once before reset, once after)
            assert mock_cred_class.call_count == 2


class TestAuthenticationErrorMessages:
    """Test that authentication errors provide helpful guidance."""
    
    @pytest.mark.asyncio
    async def test_authentication_error_includes_helpful_guidance(self):
        """Test that authentication error includes helpful user guidance."""
        with patch('utils.azure_auth.azure_authenticator') as mock_auth:
            mock_credential = Mock()
            mock_credential.get_token.side_effect = ClientAuthenticationError("Auth failed")
            mock_auth.get_credential = AsyncMock(return_value=mock_credential)
            
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_auth()
            
            error_message = str(exc_info.value)
            
            # Check for helpful guidance in error message
            assert "az login" in error_message
            assert "Visual Studio Code" in error_message or "browser login" in error_message
            assert "service principal" in error_message
    
    @pytest.mark.asyncio
    async def test_authentication_error_contains_original_error(self):
        """Test that authentication error preserves original error details."""
        original_error = ClientAuthenticationError("Specific auth error details")
        
        with patch('utils.azure_auth.azure_authenticator') as mock_auth:
            mock_credential = Mock()
            mock_credential.get_token.side_effect = original_error
            mock_auth.get_credential = AsyncMock(return_value=mock_credential)
            
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_auth()
            
            # Check that original error is preserved
            assert exc_info.value.__cause__ is original_error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
