#!/usr/bin/env python3
"""Test the agent workflow to debug the 'No output received from workflow' issue."""

import sys
import os
import asyncio
import logging

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from utils.logger import setup_logging
from utils.data_types import Question
from utils.config import config_manager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

async def test_agent_workflow():
    """Test the agent workflow step by step."""
    try:
        logger.info("=== Starting Agent Workflow Test ===")
        
        # Test 1: Import and setup
        logger.info("Test 1: Testing imports...")
        from utils.azure_auth import get_azure_client
        from agents.workflow_manager import create_agent_coordinator
        logger.info("✓ Imports successful")
        
        # Test 2: Get Azure client
        logger.info("Test 2: Getting Azure client...")
        azure_client = await get_azure_client()
        logger.info("✓ Azure client obtained")
        
        # Test 3: Get configuration
        logger.info("Test 3: Getting Bing connection ID...")
        bing_connection_id = config_manager.get_bing_connection_id()
        logger.info(f"✓ Bing connection ID: {bing_connection_id}")
        
        # Test 4: Create agent coordinator
        logger.info("Test 4: Creating agent coordinator...")
        coordinator = await create_agent_coordinator(azure_client, bing_connection_id)
        logger.info("✓ Agent coordinator created")
        
        # Test 5: Create test question
        logger.info("Test 5: Creating test question...")
        question = Question(
            text="What is Python?",
            context="Microsoft Azure AI",
            char_limit=500,
            max_retries=2
        )
        logger.info(f"✓ Test question created: '{question.text}'")
        
        # Test 6: Test individual agents first
        logger.info("Test 6: Testing individual agent creation...")
        
        # Test Question Answerer
        logger.info("Test 6a: Testing Question Answerer agent...")
        qa_agent = coordinator.question_answerer
        if qa_agent:
            logger.info("✓ Question Answerer agent exists")
        else:
            logger.error("✗ Question Answerer agent is None")
            return False
        
        # Test Answer Checker
        logger.info("Test 6b: Testing Answer Checker agent...")
        ac_agent = coordinator.answer_checker
        if ac_agent:
            logger.info("✓ Answer Checker agent exists")
        else:
            logger.error("✗ Answer Checker agent is None")
            return False
        
        # Test 7: Test workflow object
        logger.info("Test 7: Testing workflow object...")
        workflow = coordinator.workflow
        if workflow:
            logger.info("✓ Workflow object exists")
        else:
            logger.error("✗ Workflow object is None")
            return False
        
        # Test 8: Simple progress/reasoning callbacks
        logger.info("Test 8: Setting up callbacks...")
        progress_messages = []
        reasoning_messages = []
        
        def progress_callback(agent, message, progress):
            msg = f"Progress - {agent}: {message} ({progress:.1%})"
            progress_messages.append(msg)
            logger.info(f"PROGRESS: {msg}")
        
        def reasoning_callback(message):
            reasoning_messages.append(message)
            logger.info(f"REASONING: {message}")
        
        logger.info("✓ Callbacks set up")
        
        # Test 9: Process question with timeout
        logger.info("Test 9: Processing question with 60 second timeout...")
        
        try:
            result = await asyncio.wait_for(
                coordinator.process_question(question, progress_callback, reasoning_callback),
                timeout=60.0
            )
            
            logger.info("✓ Question processing completed!")
            logger.info(f"Result success: {result.success}")
            if result.success:
                logger.info(f"Answer length: {len(result.answer.content) if result.answer else 0}")
                logger.info(f"Processing time: {result.processing_time:.2f}s")
            else:
                logger.error(f"Processing failed: {result.error_message}")
            
            # Log callback messages
            logger.info(f"Progress messages received: {len(progress_messages)}")
            for msg in progress_messages:
                logger.info(f"  - {msg}")
            
            logger.info(f"Reasoning messages received: {len(reasoning_messages)}")
            for msg in reasoning_messages:
                logger.info(f"  - {msg}")
            
            return result.success
            
        except asyncio.TimeoutError:
            logger.error("✗ Question processing timed out after 60 seconds")
            return False
        except Exception as e:
            logger.error(f"✗ Question processing failed with exception: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Test 10: Cleanup
        logger.info("Test 10: Cleaning up...")
        try:
            if 'coordinator' in locals():
                await coordinator.cleanup_agents()
                logger.info("✓ Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

async def test_workflow_components():
    """Test individual workflow components."""
    try:
        logger.info("=== Testing Workflow Components ===")
        
        # Test WorkflowBuilder
        logger.info("Testing WorkflowBuilder...")
        from agent_framework import WorkflowBuilder, Executor, handler, WorkflowContext
        
        # Check what methods are available
        builder_methods = [method for method in dir(WorkflowBuilder) if not method.startswith('_')]
        logger.info(f"WorkflowBuilder methods: {builder_methods}")
        
        # Test basic workflow creation
        logger.info("Testing basic workflow creation...")
        
        class TestExecutor(Executor):
            def __init__(self, name):
                super().__init__(id=name)
            
            @handler
            async def handle(self, data, ctx: WorkflowContext):
                logger.info(f"TestExecutor {self.id} handling data: {data}")
                result = {"processed_by": self.id, "input": data}
                await ctx.send_message(result)
                await ctx.yield_output(result)
                return result
        
        executor1 = TestExecutor("test1")
        executor2 = TestExecutor("test2")
        
        workflow = (
            WorkflowBuilder()
            .add_edge(executor1, executor2)
            .set_start_executor(executor1)
            .build()
        )
        
        logger.info("✓ Basic workflow created successfully")
        
        # Test workflow execution
        logger.info("Testing workflow execution...")
        events = await workflow.run("test_input")
        outputs = events.get_outputs()
        
        logger.info(f"Workflow outputs: {outputs}")
        logger.info(f"Number of outputs: {len(outputs)}")
        
        if outputs:
            logger.info("✓ Workflow produced outputs")
            return True
        else:
            logger.error("✗ Workflow produced no outputs")
            return False
        
    except Exception as e:
        logger.error(f"Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    logger.info("Starting comprehensive workflow testing...")
    
    # Test 1: Component test
    component_success = await test_workflow_components()
    
    # Test 2: Full workflow test
    workflow_success = await test_agent_workflow()
    
    # Results
    logger.info("=== Test Results ===")
    logger.info(f"Component test: {'PASS' if component_success else 'FAIL'}")
    logger.info(f"Workflow test: {'PASS' if workflow_success else 'FAIL'}")
    
    overall_success = component_success and workflow_success
    logger.info(f"Overall: {'PASS' if overall_success else 'FAIL'}")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)