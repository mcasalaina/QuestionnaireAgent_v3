"""Integration test for link checker connection ID resolution."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.link_checker import LinkCheckerExecutor
from utils.data_types import Question, ValidationStatus
from utils.exceptions import AgentExecutionError

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
test_logger = logging.getLogger("TEST")
test_logger.setLevel(logging.DEBUG)
test_handler = logging.StreamHandler()
test_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
test_logger.addHandler(test_handler)


class TestConnectionResolution:
    """Tests for connection ID resolution in LinkCheckerExecutor."""
    
    @pytest.mark.asyncio
    async def test_async_connection_get_is_awaited(self):
        """Test that connections.get() is properly awaited."""
        
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST: Async connection.get() is properly awaited")
        test_logger.info("=" * 60)
        
        # Create mock azure_client
        mock_azure_client = MagicMock()
        mock_project_client = MagicMock()
        mock_azure_client.project_client = mock_project_client
        
        # Mock connection object with full ID
        mock_connection = MagicMock()
        full_id = "/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.CognitiveServices/accounts/test-account/projects/test-project/connections/BrowserAutomation"
        mock_connection.id = full_id
        
        # Mock the async connections.get method
        async def async_get(*args, **kwargs):
            return mock_connection
        
        mock_project_client.connections.get = async_get
        
        # Create executor
        executor = LinkCheckerExecutor(
            azure_client=mock_azure_client,
            browser_automation_connection_id="BrowserAutomation"
        )
        
        # Test resolution
        resolved_id = await executor._resolve_connection_id()
        
        # Verify
        assert resolved_id == full_id
        test_logger.info(f"✅ Successfully resolved async connection ID")
        assert executor.browser_automation_connection_id == full_id
        test_logger.info(f"✅ Connection ID cached correctly")
    
    @pytest.mark.asyncio
    async def test_connection_resolution_called_during_agent_creation(self):
        """Test that connection resolution happens when agent is created."""
        
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST: Connection resolution happens during agent creation")
        test_logger.info("=" * 60)
        
        # Create mock azure_client
        mock_azure_client = MagicMock()
        mock_project_client = MagicMock()
        mock_azure_client.project_client = mock_project_client
        
        # Mock connection
        mock_connection = MagicMock()
        full_id = "/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.CognitiveServices/accounts/test-account/projects/test-project/connections/BrowserAutomation"
        mock_connection.id = full_id
        
        async def async_get(*args, **kwargs):
            return mock_connection
        
        mock_project_client.connections.get = async_get
        
        # Create executor
        executor = LinkCheckerExecutor(
            azure_client=mock_azure_client,
            browser_automation_connection_id="BrowserAutomation"
        )
        
        # Before getting agent, connection ID should be None
        assert executor.browser_automation_connection_id is None
        test_logger.info("✅ Connection ID is None before agent creation")
        
        # Mock BrowserAutomationTool
        with patch("agents.link_checker.BrowserAutomationTool") as mock_tool_class:
            agent = await executor._get_agent()
            
            # Verify BrowserAutomationTool was called with resolved full ID
            mock_tool_class.assert_called_once_with(connection_id=full_id)
            test_logger.info(f"✅ BrowserAutomationTool called with full connection ID")
            
            # Verify connection ID is now cached
            assert executor.browser_automation_connection_id == full_id
            test_logger.info(f"✅ Connection ID cached after agent creation")
    
    @pytest.mark.asyncio
    async def test_connection_resolution_failure_raises_error(self):
        """Test that connection resolution failures are properly handled."""
        
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST: Connection resolution failure handling")
        test_logger.info("=" * 60)
        
        # Create mock azure_client that fails
        mock_azure_client = MagicMock()
        mock_project_client = MagicMock()
        mock_azure_client.project_client = mock_project_client
        
        # Mock async failure
        async def async_get_failure(*args, **kwargs):
            raise Exception("Connection 'NonExistent' not found in project")
        
        mock_project_client.connections.get = async_get_failure
        
        # Create executor
        executor = LinkCheckerExecutor(
            azure_client=mock_azure_client,
            browser_automation_connection_id="NonExistent"
        )
        
        # Test that error is raised
        try:
            await executor._resolve_connection_id()
            assert False, "Should have raised AgentExecutionError"
        except AgentExecutionError as e:
            assert "Failed to resolve Browser Automation connection" in str(e)
            test_logger.info(f"✅ Correctly raised AgentExecutionError on resolution failure")


async def run_all_tests():
    """Run all tests."""
    test_suite = TestConnectionResolution()
    
    try:
        await test_suite.test_async_connection_get_is_awaited()
        await test_suite.test_connection_resolution_called_during_agent_creation()
        await test_suite.test_connection_resolution_failure_raises_error()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.exception("Test failure details:")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
