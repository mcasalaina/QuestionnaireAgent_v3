"""Unit tests for asyncio_runner module."""

import asyncio
import pytest
import time
import threading
from src.utils.asyncio_runner import AsyncioThreadRunner


class TestAsyncioThreadRunner:
    """Test cases for AsyncioThreadRunner."""

    def test_basic_coroutine_execution(self):
        """Test that a simple coroutine executes successfully."""
        runner = AsyncioThreadRunner()
        result_holder = []
        
        async def simple_coro():
            await asyncio.sleep(0.1)
            return "success"
        
        def callback(result):
            result_holder.append(result)
        
        runner.start()
        runner.run_coroutine(simple_coro(), callback=callback)
        
        # Wait for the coroutine to complete
        time.sleep(0.5)
        
        assert len(result_holder) == 1
        assert result_holder[0] == "success"
        
        runner.shutdown()
    
    def test_error_handling(self):
        """Test that errors in coroutines are properly handled."""
        runner = AsyncioThreadRunner()
        error_holder = []
        
        async def failing_coro():
            await asyncio.sleep(0.1)
            raise ValueError("Test error")
        
        def error_callback(error):
            error_holder.append(error)
        
        runner.start()
        runner.run_coroutine(failing_coro(), error_callback=error_callback)
        
        # Wait for the coroutine to complete
        time.sleep(0.5)
        
        assert len(error_holder) == 1
        assert isinstance(error_holder[0], ValueError)
        assert str(error_holder[0]) == "Test error"
        
        runner.shutdown()
    
    def test_cancelled_task_during_shutdown(self):
        """Test that cancelled tasks during shutdown don't log errors."""
        runner = AsyncioThreadRunner()
        callback_called = []
        error_called = []
        
        async def long_running_coro():
            # This should be cancelled during shutdown
            await asyncio.sleep(10)
            return "should not reach here"
        
        def callback(result):
            callback_called.append(result)
        
        def error_callback(error):
            error_called.append(error)
        
        runner.start()
        runner.run_coroutine(long_running_coro(), callback=callback, error_callback=error_callback)
        
        # Give the coroutine time to start
        time.sleep(0.1)
        
        # Shutdown should cancel the running task
        runner.shutdown()
        
        # callback should not be called for cancelled tasks
        assert len(callback_called) == 0
        # error_callback SHOULD be called with CancelledError so futures can complete
        assert len(error_called) == 1
        assert isinstance(error_called[0], asyncio.CancelledError)
    
    def test_multiple_coroutines(self):
        """Test that multiple coroutines can be executed."""
        runner = AsyncioThreadRunner()
        results = []
        
        async def numbered_coro(n):
            await asyncio.sleep(0.1)
            return n
        
        def make_callback(results_list):
            def callback(result):
                results_list.append(result)
            return callback
        
        runner.start()
        
        for i in range(5):
            runner.run_coroutine(numbered_coro(i), callback=make_callback(results))
        
        # Wait for all coroutines to complete
        time.sleep(0.5)
        
        assert len(results) == 5
        assert sorted(results) == [0, 1, 2, 3, 4]
        
        runner.shutdown()
    
    def test_is_running(self):
        """Test the is_running method."""
        runner = AsyncioThreadRunner()
        
        assert not runner.is_running()
        
        runner.start()
        assert runner.is_running()
        
        runner.shutdown()
        # After shutdown, should not be running
        assert not runner.is_running()
    
    def test_shutdown_without_start(self):
        """Test that shutdown can be called without start."""
        runner = AsyncioThreadRunner()
        # Should not raise an exception
        runner.shutdown()
        assert not runner.is_running()
    
    def test_double_start(self):
        """Test that starting an already started runner is safe."""
        runner = AsyncioThreadRunner()
        
        runner.start()
        assert runner.is_running()
        
        # Second start should be a no-op
        runner.start()
        assert runner.is_running()
        
        runner.shutdown()


@pytest.mark.asyncio
async def test_coroutine_can_be_awaited():
    """Test that our runner can handle async def coroutines."""
    runner = AsyncioThreadRunner()
    result_holder = []
    
    async def async_function():
        await asyncio.sleep(0.1)
        return "async result"
    
    def callback(result):
        result_holder.append(result)
    
    runner.start()
    runner.run_coroutine(async_function(), callback=callback)
    
    # Wait for completion
    await asyncio.sleep(0.5)
    
    assert len(result_holder) == 1
    assert result_holder[0] == "async result"
    
    runner.shutdown()
