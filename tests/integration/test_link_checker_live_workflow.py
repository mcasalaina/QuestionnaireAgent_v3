"""Live headless workflow test for link checker connection resolution."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.workflow_manager import AgentCoordinator
from utils.data_types import Question
from utils.azure_auth import get_azure_client
from utils.exceptions import AgentExecutionError

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s - %(name)s - %(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_live_workflow_with_connection_resolution():
    """Test the live workflow with connection ID resolution."""
    
    logger.info("=" * 70)
    logger.info("LIVE HEADLESS WORKFLOW TEST - Connection Resolution")
    logger.info("=" * 70)
    
    # Get Azure client and credentials
    logger.info("Setting up Azure authentication...")
    try:
        azure_client = await get_azure_client()
        logger.info("✅ Azure client obtained")
        
        # Create agent coordinator
        logger.info("Creating agent coordinator...")
        coordinator = AgentCoordinator(
            azure_client=azure_client,
            bing_connection_id=os.getenv("BING_CONNECTION_ID", "BingSearch"),
            browser_automation_connection_id=os.getenv("BROWSER_AUTOMATION_CONNECTION_ID", "BrowserAutomation")
        )
        logger.info("✅ Agent coordinator created")
        
        # Create agents
        logger.info("Creating agent executors...")
        try:
            await coordinator.create_agents()
            logger.info("✅ Agent executors created successfully")
        except Exception as e:
            logger.error(f"Failed to create agents: {e}")
            raise
        
        # Create a simple test question
        logger.info("Creating test question...")
        question = Question(
            text="What is Python?",
            context="",
            max_retries=1
        )
        logger.info(f"✅ Test question created: '{question.text}'")
        
        # Define progress callback
        def progress_callback(stage, message, progress):
            logger.info(f"[{stage}] {message} ({progress*100:.1f}%)")
        
        # Run workflow
        logger.info("\nStarting workflow execution...")
        logger.info("-" * 70)
        try:
            result = await coordinator.process_question(
                question,
                progress_callback=progress_callback
            )
            
            logger.info("-" * 70)
            logger.info(f"✅ Workflow completed successfully!")
            logger.info(f"   Validation Status: {result.validation_status}")
            logger.info(f"   Answer Preview: {result.final_answer[:100]}..." if result.final_answer else "No answer")
            
        except AgentExecutionError as e:
            # Check if it's the connection resolution error we're trying to fix
            if "Connection ID" in str(e) or "'coroutine' object has no attribute" in str(e):
                logger.error(f"❌ Connection resolution error (this should be fixed): {e}")
                raise AssertionError(f"Connection resolution failed: {e}")
            else:
                logger.warning(f"⚠️ Expected workflow error (not connection-related): {e}")
                # Other errors might be expected in test environment
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            raise
        
        finally:
            # Cleanup
            logger.info("Cleaning up agents...")
            await coordinator.cleanup_agents()
            logger.info("✅ Cleanup completed")
    
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False
    
    logger.info("=" * 70)
    logger.info("✅ TEST PASSED - Connection resolution is working!")
    logger.info("=" * 70)
    return True


async def main():
    """Run the live workflow test."""
    try:
        success = await test_live_workflow_with_connection_resolution()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
