"""Asyncio thread runner for proper event loop management in GUI applications."""

import asyncio
import threading
import logging
from typing import Callable, Any, Optional, Coroutine
from concurrent.futures import ThreadPoolExecutor, Future
import time

logger = logging.getLogger(__name__)


class AsyncioThreadRunner:
    """Manages a dedicated asyncio event loop in a separate thread.
    
    This class provides a way to run asyncio coroutines from a synchronous
    context (like tkinter) without interfering with the main event loop.
    """
    
    def __init__(self):
        """Initialize the asyncio thread runner."""
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._shutdown_requested = False
        self._started = False
        self._loop_ready = threading.Event()
        
    def _run_event_loop(self):
        """Run the asyncio event loop in a separate thread."""
        loop = None
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            
            # Signal that the loop is ready
            self._loop_ready.set()
            
            logger.info("AsyncioThreadRunner: Starting event loop")
            
            # Run the event loop until shutdown is requested
            loop.run_forever()
            
            logger.info("AsyncioThreadRunner: Event loop stopped")
            
        except Exception as e:
            logger.error(f"AsyncioThreadRunner: Fatal error in event loop: {e}", exc_info=True)
        finally:
            # Clean up
            try:
                if loop and not loop.is_closed():
                    # Cancel all running tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    
                    # Wait for tasks to complete cancellation
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    
                    loop.close()
            except Exception as e:
                logger.warning(f"Error cleaning up event loop: {e}")
            
            self._loop = None
    
    def start(self):
        """Start the asyncio thread if not already started."""
        if self._started:
            return
        
        self._started = True
        self._shutdown_requested = False
        self._loop_ready.clear()
        
        # Start the event loop thread
        self._thread = threading.Thread(
            target=self._run_event_loop,
            name="AsyncioEventLoop",
            daemon=True
        )
        self._thread.start()
        
        # Wait for the loop to be ready
        if not self._loop_ready.wait(timeout=5.0):
            raise RuntimeError("Failed to start asyncio event loop within timeout")
        
        logger.info("AsyncioThreadRunner: Started successfully")
    
    def run_coroutine(
        self, 
        coro: Coroutine[Any, Any, Any], 
        callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """Schedule a coroutine to run in the asyncio thread.
        
        Args:
            coro: The coroutine to run
            callback: Optional callback to call with the result
            error_callback: Optional callback to call on error
        """
        if not self._started:
            self.start()
        
        if not self._loop or self._shutdown_requested:
            if error_callback:
                error_callback(RuntimeError("Event loop not available"))
            return
        
        async def wrapper():
            """Wrapper to handle the coroutine execution and callbacks."""
            try:
                result = await coro
                if callback:
                    callback(result)
            except asyncio.CancelledError:
                # Task was cancelled during shutdown - this is expected behavior
                logger.debug("Coroutine cancelled during shutdown")
                raise  # Re-raise to properly propagate cancellation
            except Exception as e:
                logger.error(f"Error running coroutine: {e}", exc_info=True)
                if error_callback:
                    error_callback(e)
        
        # Schedule the wrapper in the event loop
        asyncio.run_coroutine_threadsafe(wrapper(), self._loop)
    
    def shutdown(self):
        """Shutdown the asyncio thread runner."""
        if not self._started:
            return
        
        logger.info("AsyncioThreadRunner: Shutting down...")
        
        self._shutdown_requested = True
        
        # Stop the event loop
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                logger.warning("AsyncioThreadRunner: Thread did not shutdown gracefully")
        
        self._started = False
        logger.info("AsyncioThreadRunner: Shutdown complete")
    
    def is_running(self) -> bool:
        """Check if the asyncio thread runner is running."""
        return (self._started and 
                not self._shutdown_requested and
                self._thread is not None and 
                self._thread.is_alive())


# Global instance for the application
_global_runner: Optional[AsyncioThreadRunner] = None


def get_asyncio_runner() -> AsyncioThreadRunner:
    """Get the global asyncio thread runner instance."""
    global _global_runner
    if _global_runner is None:
        _global_runner = AsyncioThreadRunner()
    return _global_runner


def shutdown_asyncio_runner():
    """Shutdown the global asyncio thread runner."""
    global _global_runner
    if _global_runner:
        _global_runner.shutdown()
        _global_runner = None