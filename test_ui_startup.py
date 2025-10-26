#!/usr/bin/env python3
"""Test UI startup without agent framework imports."""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from utils.logger import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def test_ui_startup():
    """Test UI startup with minimal imports."""
    try:
        logger.info("Testing UI startup...")
        
        # Import UIManager
        from ui.main_window import UIManager
        logger.info("✓ UIManager imported successfully")
        
        # Create UIManager instance (without agent coordinator)
        ui_manager = UIManager(agent_coordinator=None)
        logger.info("✓ UIManager instance created")
        
        # Show initial reasoning message
        ui_manager.update_reasoning("UI startup test - components initialized successfully")
        logger.info("✓ Reasoning display updated")
        
        # Start GUI
        logger.info("Starting GUI...")
        ui_manager.run()
        
    except Exception as e:
        logger.error(f"UI startup test failed: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    success = test_ui_startup()
    exit(0 if success else 1)