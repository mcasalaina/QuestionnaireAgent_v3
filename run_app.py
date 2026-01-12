#!/usr/bin/env python3
"""Launch script for the questionnaire application."""

import sys
import os
import asyncio
import argparse
import threading
import time
import webbrowser
import socket
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print(f"Python path: {sys.path[:3]}...")
print("Starting application...")


async def initialize_and_run(args):
    """Initialize application with authentication check before showing UI.
    
    Args:
        args: Parsed command line arguments
    """
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
        app = UIManager(
            initial_context=args.context,
            initial_char_limit=args.charlimit,
            auto_question=args.question,
            auto_spreadsheet=args.spreadsheet
        )
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


def parse_arguments():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Questionnaire Answerer - Process questions using Microsoft Agent Framework"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        default="Microsoft Azure AI",
        help="Set the default context (default: Microsoft Azure AI)"
    )
    
    parser.add_argument(
        "--charlimit",
        type=int,
        default=2000,
        help="Set the default character limit (default: 2000)"
    )
    
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="Question to process immediately after initialization"
    )
    
    parser.add_argument(
        "--spreadsheet",
        type=str,
        default=None,
        help="Path to Excel spreadsheet to process immediately after initialization"
    )

    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch in web interface mode instead of desktop GUI"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for web server (default: 8080, only used with --web)"
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser (only used with --web)"
    )

    parser.add_argument(
        "--mockagents",
        action="store_true",
        help="Use mock agents for testing (only used with --web)"
    )

    return parser.parse_args()


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use.

    Args:
        port: Port number to check

    Returns:
        True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except socket.error:
            return True


def wait_for_server(port: int, timeout: float = 10.0) -> bool:
    """Wait for the web server to become available.

    Args:
        port: Port to check
        timeout: Maximum time to wait in seconds

    Returns:
        True if server is available, False if timeout
    """
    import requests
    start_time = time.time()
    url = f"http://127.0.0.1:{port}/health"

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)

    return False


async def initialize_and_run_web(args):
    """Initialize and run the web interface.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    from utils.azure_auth import test_authentication
    from utils.config import config_manager
    from utils.exceptions import AuthenticationError, ConfigurationError

    try:
        # Step 1: Check port availability
        if is_port_in_use(args.port):
            print(f"\n❌ Port {args.port} is already in use.")
            print(f"   Try a different port with: python run_app.py --web --port {args.port + 1}")
            return 1

        # Step 2: Validate configuration
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

        # Step 3: Test Azure authentication (skip if using mock agents)
        if not args.mockagents:
            print("\nTesting Azure authentication...")
            print("(Checking for existing 'az login' or 'azd login' session)")

            try:
                await test_authentication()
                print("✓ Azure authentication successful")
            except AuthenticationError as e:
                print(f"\n❌ Authentication Error: {e}")
                return 1
        else:
            print("\nSkipping Azure authentication (mock agents mode)")

        # Step 4: Start web server
        print(f"\nStarting web server on http://127.0.0.1:{args.port}")
        if args.mockagents:
            print("*** MOCK AGENTS ENABLED - Using mock agents for testing ***")

        from web.app import run_server, cleanup, set_mock_agents_mode

        # Set mock agents mode if requested
        if args.mockagents:
            set_mock_agents_mode(True)

        # Start server in background thread
        server_thread = threading.Thread(
            target=run_server,
            kwargs={"host": "127.0.0.1", "port": args.port, "log_level": "warning"},
            daemon=True
        )
        server_thread.start()

        # Wait for server to be ready
        print("Waiting for server to start...")
        if wait_for_server(args.port):
            print("✓ Web server started successfully")
        else:
            print("\n⚠️  Server may still be starting...")

        # Step 5: Open browser (unless --no-browser flag is set)
        url = f"http://127.0.0.1:{args.port}"
        if not args.no_browser:
            print(f"\nOpening browser to: {url}")
            webbrowser.open(url)
        else:
            print(f"\nServer ready at: {url}")

        print("\n" + "=" * 50)
        print("Web interface is running!")
        print(f"URL: {url}")
        print("Press Ctrl+C to stop the server")
        print("=" * 50 + "\n")

        # Keep main thread alive
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\n\nShutting down web server...")
            cleanup()
            print("Web server stopped.")

        return 0

    except ConfigurationError as e:
        print(f"\n❌ Configuration Error: {e}")
        return 1
    except AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


# Now import and run the application
if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Set up event loop policy for Windows
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        # Choose mode based on --web flag
        if args.web:
            # Web interface mode
            exit_code = asyncio.run(initialize_and_run_web(args))
        else:
            # Desktop GUI mode (tkinter)
            exit_code = asyncio.run(initialize_and_run(args))

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