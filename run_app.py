#!/usr/bin/env python3
"""Launch script for the questionnaire application."""

import sys
import os
import asyncio
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print(f"Python path: {sys.path[:3]}...")
print("Starting application...")


async def initialize_and_run():
    """Initialize application with authentication check before showing UI."""
    from utils.azure_auth import test_authentication
    from utils.config import config_manager
    from utils.exceptions import AuthenticationError, ConfigurationError
    from ui.main_window import UIManager
    
    try:
        # Step 1: Validate configuration
        print("Validating configuration...")
        validation_result = config_manager.validate_configuration()
        
        if not validation_result.is_valid:
            error_details = "; ".join(validation_result.error_details)
            print(f"\n❌ Configuration Error: {error_details}")
            print("\nPlease check:")
            print("1. .env file exists and contains required values")
            print("2. AZURE_OPENAI_ENDPOINT is set")
            print("3. AZURE_OPENAI_MODEL_DEPLOYMENT is set")
            print("4. BING_CONNECTION_ID is set")
            return 1
        
        print("✓ Configuration validated successfully")
        
        # Step 2: Test Azure authentication immediately
        print("\nTesting Azure authentication...")
        print("(Checking for existing 'az login' or 'azd login' session)")
        print("(Browser login will only be used if no existing session is found)")
        
        try:
            await test_authentication()
            print("✓ Azure authentication successful")
        except AuthenticationError as e:
            print(f"\n❌ Authentication Error: {e}")
            return 1
        
        # Step 3: Initialize and run UI
        print("\nInitializing user interface...")
        app = UIManager()
        print("✓ Application ready")
        print("\nStarting application...\n")
        app.run()
        return 0
        
    except ConfigurationError as e:
        print(f"\n❌ Configuration Error: {e}")
        return 1
    except AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


# Now import and run the application
if __name__ == "__main__":
    try:
        # Set up event loop policy for Windows
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run async initialization
        exit_code = asyncio.run(initialize_and_run())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Ensure the global asyncio runner is shutdown
        try:
            from utils.asyncio_runner import shutdown_asyncio_runner
            shutdown_asyncio_runner()
            print("Global asyncio runner shutdown completed")
        except Exception as e:
            print(f"Warning: Error shutting down asyncio runner: {e}")