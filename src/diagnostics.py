"""Diagnostic tool to help troubleshoot Azure AI Projects connectivity issues."""

import asyncio
import sys
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import config_manager
from utils.azure_auth import azure_authenticator
from utils.exceptions import AzureServiceError, AuthenticationError


# Configure logging for diagnostics
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def run_diagnostics():
    """Run comprehensive diagnostics to identify Azure connectivity issues."""
    
    print("=" * 60)
    print("Azure AI Projects Connectivity Diagnostics")
    print("=" * 60)
    print()
    
    # Step 1: Configuration validation
    print("1. Validating configuration...")
    try:
        validation_result = config_manager.validate_configuration()
        
        if validation_result.is_valid:
            print("   ✓ Configuration is valid")
            print(f"   - Endpoint: {config_manager.get_azure_endpoint()}")
            print(f"   - Model deployment: {config_manager.get_model_deployment()}")
            print(f"   - Bing connection: {config_manager.get_bing_connection_id()}")
            print(f"   - Browser automation connection: {config_manager.get_browser_automation_connection_id()}")
        else:
            print("   ✗ Configuration validation failed:")
            for error in validation_result.error_details:
                print(f"     - {error}")
            print("\n   Please fix configuration issues before proceeding.")
            return
            
    except Exception as e:
        print(f"   ✗ Configuration error: {e}")
        return
    
    print()
    
    # Step 2: Test endpoint format and accessibility
    print("2. Testing endpoint accessibility...")
    try:
        # This will trigger endpoint validation
        await azure_authenticator._validate_azure_endpoint()
        print("   ✓ Endpoint validation passed")
        
    except AzureServiceError as e:
        print(f"   ✗ Endpoint validation failed: {e}")
        return
    except Exception as e:
        print(f"   ✗ Unexpected error during endpoint validation: {e}")
        return
    
    print()
    
    # Step 3: Test Azure authentication
    print("3. Testing Azure authentication...")
    try:
        credential = await azure_authenticator.get_credential()
        print("   ✓ Azure credentials obtained")
        
    except AuthenticationError as e:
        print(f"   ✗ Authentication failed: {e}")
        print("   Try running 'az login' to authenticate with Azure CLI")
        return
    except Exception as e:
        print(f"   ✗ Unexpected authentication error: {e}")
        return
    
    print()
    
    # Step 4: Test Azure AI Agent client creation
    print("4. Testing Azure AI Agent client creation...")
    try:
        client = await azure_authenticator.get_azure_client()
        print("   ✓ Azure AI Agent client created successfully")
        
    except AzureServiceError as e:
        print(f"   ✗ Azure AI Agent client creation failed: {e}")
        print("\n   Common solutions:")
        print("   - Ensure the Azure AI Projects resource exists")
        print("   - Check that the endpoint URL is correct")
        print("   - Verify your account has access to the resource")
        print("   - Confirm the model deployment exists")
        return
    except Exception as e:
        print(f"   ✗ Unexpected error creating client: {e}")
        return
    
    print()
    
    # Step 5: Test basic agent creation (this is where the 404 typically occurs)
    print("5. Testing basic agent creation...")
    try:
        from agent_framework import ChatAgent
        
        test_agent = ChatAgent(
            chat_client=client,
            instructions="You are a test agent for diagnostics."
        )
        
        print("   ✓ Test agent created successfully")
        print("\n" + "=" * 60)
        print("All diagnostics passed! Your Azure AI Projects setup appears to be working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print(f"   ✗ Agent creation failed: {e}")
        print(f"\n   This is likely the source of your 404 errors.")
        print("   Common causes:")
        print("   - The Azure AI Projects resource doesn't exist at the specified endpoint")
        print("   - The model deployment name is incorrect or doesn't exist")
        print("   - Your account lacks sufficient permissions")
        print("   - The resource is in a different region or subscription")
        print("\n   Please verify:")
        print(f"   1. Go to Azure Portal and confirm the resource exists at:")
        print(f"      {config_manager.get_azure_endpoint()}")
        print(f"   2. Check that model deployment '{config_manager.get_model_deployment()}' exists")
        print(f"   3. Verify your account has 'Azure AI Developer' or similar role")
        
    print()


def main():
    """Main entry point for diagnostics."""
    try:
        asyncio.run(run_diagnostics())
    except KeyboardInterrupt:
        print("\nDiagnostics interrupted by user")
    except Exception as e:
        print(f"\nFatal error during diagnostics: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()