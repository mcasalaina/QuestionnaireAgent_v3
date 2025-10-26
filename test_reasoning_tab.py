#!/usr/bin/env python3
"""Test reasoning tab functionality."""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from utils.logger import setup_logging
import logging
import tkinter as tk
import time

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def test_reasoning_tab():
    """Test reasoning tab updates."""
    try:
        logger.info("Testing reasoning tab functionality...")
        
        # Import UIManager
        from ui.main_window import UIManager
        logger.info("✓ UIManager imported successfully")
        
        # Create UIManager instance (without agent coordinator)
        ui_manager = UIManager(agent_coordinator=None)
        logger.info("✓ UIManager instance created")
        
        # Test reasoning updates
        ui_manager.update_reasoning("Test message 1: Reasoning tab test starting")
        ui_manager.update_reasoning("Test message 2: This should appear in the Reasoning tab")
        ui_manager.update_reasoning("Test message 3: Agent would typically be processing now")
        ui_manager.update_reasoning("Test message 4: Multiple messages should show with timestamps")
        logger.info("✓ Test reasoning messages sent")
        
        # Schedule automatic close after 3 seconds
        def auto_close():
            logger.info("Auto-closing test window...")
            ui_manager.root.quit()
        
        ui_manager.root.after(3000, auto_close)
        
        # Start GUI briefly
        logger.info("Starting GUI test (will auto-close in 3 seconds)...")
        ui_manager.root.mainloop()
        
        logger.info("✓ Reasoning tab test completed")
        return True
        
    except Exception as e:
        logger.error(f"Reasoning tab test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_reasoning_tab()
    print(f"Test result: {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)