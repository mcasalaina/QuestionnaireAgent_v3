"""
Live end-to-end test for Azure question answering with multi-agent workflow.

This test runs actual Azure questions through the complete multi-agent workflow
(Question Answerer -> Answer Checker -> Link Checker) and verifies that it returns
meaningful results. It does not mock any components and requires valid Azure credentials.
"""

import pytest
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.data_types import Question, ValidationStatus
from utils.config import config_manager
from utils.azure_auth import foundry_agent_session
from agents.workflow_manager import create_agent_coordinator


# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

# Suppress verbose HTTP logs from Azure SDK
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("TEST MODULE LOADED: test_live_azure_question.py")
print("="*80 + "\n")


class TestLiveAzureQuestion:
    """Test live Azure questions through the multi-agent workflow."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_question_workflow(self):
        """Test a complete end-to-end question through all agents."""
        print("\n" + "="*80)
        print("TEST STARTING: test_end_to_end_question_workflow")
        print("="*80 + "\n")
        
        logger.info("Step 1: Validating Azure configuration...")
        print("Step 1: Validating Azure configuration...")
        
        # Validate configuration first
        validation = config_manager.validate_configuration()
        if not validation.is_valid:
            print(f"SKIPPING TEST: {validation.error_message}")
            pytest.skip(f"Azure configuration required: {validation.error_message}")
        
        print("OK Configuration is valid")
        logger.info("OK Configuration is valid")
        
        print("\nStep 2: Creating test question...")
        logger.info("Step 2: Creating test question...")
        
        # Create a simple test question
        question = Question(
            text="What is Azure AI?",
            context="Microsoft Azure AI",
            char_limit=2000,
            max_retries=3
        )
        
        print(f"OK Question created: '{question.text}'")
        print(f"  - Context: {question.context}")
        print(f"  - Char limit: {question.char_limit}")
        print(f"  - Max retries: {question.max_retries}")
        logger.info(f"OK Question created: '{question.text}'")
        
        print("\nStep 3: Setting up callbacks...")
        logger.info("Step 3: Setting up callbacks...")
        
        # Track progress
        progress_updates = []
        def progress_callback(agent: str, message: str, progress: float):
            update = f"[{agent}] {message} ({progress:.0%})"
            progress_updates.append(update)
            print(f"  PROGRESS: {update}")
            logger.info(f"PROGRESS: {update}")
        
        # Track reasoning
        reasoning_steps = []
        def reasoning_callback(message: str):
            reasoning_steps.append(message)
            print(f"  REASONING: {message}")
            logger.info(f"REASONING: {message}")
        
        print("OK Callbacks configured")
        
        print("\nStep 4: Establishing Azure session...")
        logger.info("Step 4: Establishing Azure session...")
        
        # Create workflow coordinator with Azure client
        coordinator = None
        try:
            print("  - Calling foundry_agent_session()...")
            async with foundry_agent_session() as azure_client:
                print("OK Azure session established")
                logger.info("OK Azure session established")
                
                print("\nStep 5: Creating agent coordinator...")
                logger.info("Step 5: Creating agent coordinator...")
                print(f"  - Bing connection: {config_manager.get_bing_connection_id()}")
                print(f"  - Browser automation connection: {config_manager.get_browser_automation_connection_id()}")
                
                # Create coordinator
                coordinator = await create_agent_coordinator(
                    azure_client=azure_client,
                    bing_connection_id=config_manager.get_bing_connection_id(),
                    browser_automation_connection_id=config_manager.get_browser_automation_connection_id()
                )
                print("OK Agent coordinator created")
                logger.info("OK Agent coordinator created")
                
                print("\nStep 6: Processing question through workflow...")
                logger.info("Step 6: Processing question through workflow...")
                
                # Process the question
                result = await coordinator.process_question(
                    question=question,
                    progress_callback=progress_callback,
                    reasoning_callback=reasoning_callback
                )
                
                print("\nOK Question processing completed")
                logger.info("OK Question processing completed")
                
                print("\nStep 7: Analyzing results...")
                logger.info("Step 7: Analyzing results...")
                
                # Log the result
                print(f"\n{'='*80}")
                print("RESULT:")
                print(f"Success: {result.success}")
                logger.info(f"\n{'='*80}")
                logger.info("RESULT:")
                logger.info(f"Success: {result.success}")
                
                if result.success:
                    print(f"Answer length: {len(result.answer.content)} characters")
                    print(f"Validation status: {result.answer.validation_status}")
                    print(f"Retry count: {result.answer.retry_count}")
                    print(f"Number of sources: {len(result.answer.sources)}")
                    print(f"Number of documentation links: {len(result.answer.documentation_links)}")
                    print(f"Agent steps: {len(result.answer.agent_reasoning)}")
                    print(f"\nAnswer preview:\n{result.answer.content[:300]}...")
                    if result.answer.sources:
                        print(f"\nSources:")
                        for i, source in enumerate(result.answer.sources[:3], 1):
                            print(f"  {i}. {source}")
                    
                    logger.info(f"Answer length: {len(result.answer.content)} characters")
                    logger.info(f"Validation status: {result.answer.validation_status}")
                    logger.info(f"Retry count: {result.answer.retry_count}")
                    logger.info(f"Number of sources: {len(result.answer.sources)}")
                    logger.info(f"Number of documentation links: {len(result.answer.documentation_links)}")
                    logger.info(f"Agent steps: {len(result.answer.agent_reasoning)}")
                    logger.info(f"\nAnswer preview:\n{result.answer.content[:300]}...")
                    if result.answer.sources:
                        logger.info(f"\nSources:")
                        for i, source in enumerate(result.answer.sources[:3], 1):
                            logger.info(f"  {i}. {source}")
                else:
                    print(f"Error: {result.error_message}")
                    logger.info(f"Error: {result.error_message}")
                
                print(f"Processing time: {result.processing_time:.2f}s")
                print(f"{'='*80}\n")
                logger.info(f"Processing time: {result.processing_time:.2f}s")
                logger.info(f"{'='*80}\n")
                
                print("\nStep 8: Running assertions...")
                logger.info("Step 8: Running assertions...")
                
                # Assertions
                assert result.success, f"Question processing should succeed: {result.error_message}"
                print("  OK Result is successful")
                
                assert result.answer is not None, "Should receive an answer"
                print("  OK Answer is not None")
                
                assert isinstance(result.answer.content, str), "Answer should be a string"
                print("  OK Answer is a string")
                
                assert len(result.answer.content) > 50, "Answer should be substantial (>50 chars)"
                print(f"  OK Answer is substantial ({len(result.answer.content)} chars)")
                
                # Check that answer mentions relevant concepts
                answer_lower = result.answer.content.lower()
                assert 'azure' in answer_lower or 'ai' in answer_lower, \
                    "Answer should mention Azure or AI concepts"
                print("  OK Answer mentions relevant concepts")
                
                # Verify validation status
                assert result.answer.validation_status == ValidationStatus.APPROVED, \
                    f"Answer should be approved, got: {result.answer.validation_status}"
                print(f"  OK Validation status is APPROVED")
                
                # Verify agent steps
                assert len(result.answer.agent_reasoning) >= 2, \
                    "Should have steps from Question Answerer and Answer Checker at minimum"
                print(f"  OK Agent steps recorded ({len(result.answer.agent_reasoning)} steps)")
                
                # Verify progress was tracked
                assert len(progress_updates) > 0, "Progress callbacks should have been called"
                print(f"  OK Progress tracked ({len(progress_updates)} updates)")
                
                print("\nOK ALL ASSERTIONS PASSED!")
                logger.info("OK All assertions passed!")
                
        finally:
            # Clean up
            print("\nStep 9: Cleaning up resources...")
            logger.info("Step 9: Cleaning up resources...")
            if coordinator:
                await coordinator.cleanup_agents()
                print("OK Cleanup complete")
                logger.info("OK Cleanup complete")
            else:
                print("OK No coordinator to clean up")
        
        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")


if __name__ == '__main__':
    # Run with pytest
    print("Running live Azure question test...")
    print("Note: This test requires valid Azure credentials and network access.")
    print("Make sure you have run 'az login' or 'azd login' before running this test.\n")
    
    pytest.main([__file__, "-v", "-s"])
