#!/usr/bin/env python3
"""Launch script for the questionnaire application."""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print(f"Python path: {sys.path[:3]}...")
print("Starting application...")

# Now import and run the application
if __name__ == "__main__":
    try:
        print("Importing UIManager...")
        from ui.main_window import UIManager
        
        print("Creating UIManager instance...")
        # Create and run the application
        app = UIManager()
        print("Running application...")
        app.run()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure the global asyncio runner is shutdown
        try:
            from utils.asyncio_runner import shutdown_asyncio_runner
            shutdown_asyncio_runner()
            print("Global asyncio runner shutdown completed")
        except Exception as e:
            print(f"Warning: Error shutting down asyncio runner: {e}")