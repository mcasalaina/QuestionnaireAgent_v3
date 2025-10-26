"""Thread-safe UI update queue for background processing communication."""

import queue
import threading
import time
from typing import Optional, Callable
from .data_types import UIUpdateEvent
import logging

logger = logging.getLogger(__name__)


class UIUpdateQueue:
    """Thread-safe queue wrapper for UI updates from background processing."""
    
    def __init__(self, maxsize: int = 0):
        """Initialize UI update queue.
        
        Args:
            maxsize: Maximum queue size (0 = unlimited)
        """
        self._queue = queue.Queue(maxsize=maxsize)
        self._lock = threading.Lock()
        self._closed = False
    
    def put(self, event: UIUpdateEvent, block: bool = True, timeout: Optional[float] = None) -> None:
        """Put an event into the queue.
        
        Args:
            event: UIUpdateEvent to queue
            block: Whether to block if queue is full
            timeout: Timeout for blocking put
            
        Raises:
            queue.Full: If queue is full and block=False
            ValueError: If queue is closed
        """
        with self._lock:
            if self._closed:
                raise ValueError("Cannot put to closed queue")
        
        try:
            self._queue.put(event, block=block, timeout=timeout)
            logger.debug(f"Queued event: {event.event_type}")
        except queue.Full:
            logger.warning(f"Queue full, dropping event: {event.event_type}")
            raise
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> UIUpdateEvent:
        """Get an event from the queue.
        
        Args:
            block: Whether to block if queue is empty
            timeout: Timeout for blocking get
            
        Returns:
            UIUpdateEvent from queue
            
        Raises:
            queue.Empty: If queue is empty and block=False
        """
        return self._queue.get(block=block, timeout=timeout)
    
    def get_nowait(self) -> UIUpdateEvent:
        """Get an event without blocking.
        
        Returns:
            UIUpdateEvent from queue
            
        Raises:
            queue.Empty: If queue is empty
        """
        return self._queue.get_nowait()
    
    def put_nowait(self, event: UIUpdateEvent) -> None:
        """Put an event without blocking.
        
        Args:
            event: UIUpdateEvent to queue
            
        Raises:
            queue.Full: If queue is full
            ValueError: If queue is closed
        """
        self.put(event, block=False)
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    def qsize(self) -> int:
        """Get approximate queue size."""
        return self._queue.qsize()
    
    def close(self) -> None:
        """Close the queue, preventing new puts."""
        with self._lock:
            self._closed = True
    
    def is_closed(self) -> bool:
        """Check if queue is closed."""
        with self._lock:
            return self._closed
    
    def clear(self) -> int:
        """Clear all events from queue.
        
        Returns:
            Number of events cleared
        """
        count = 0
        try:
            while True:
                self._queue.get_nowait()
                count += 1
        except queue.Empty:
            pass
        
        logger.debug(f"Cleared {count} events from queue")
        return count
    
    def put_event(self, event_type: str, payload: dict, block: bool = True) -> None:
        """Convenience method to create and put an event.
        
        Args:
            event_type: Type of event
            payload: Event payload data
            block: Whether to block if queue is full
        """
        event = UIUpdateEvent(event_type=event_type, payload=payload)
        self.put(event, block=block)
    
    def start_polling(self, callback: Callable[[UIUpdateEvent], None], 
                     interval_ms: int = 50, stop_event: Optional[threading.Event] = None) -> threading.Thread:
        """Start background polling thread to process events.
        
        Args:
            callback: Function to call for each event
            interval_ms: Polling interval in milliseconds
            stop_event: Event to signal stop (optional)
            
        Returns:
            Started polling thread
        """
        def poll_loop():
            """Polling loop that runs in background thread."""
            logger.info("Started UI update polling")
            
            while True:
                if stop_event and stop_event.is_set():
                    break
                
                try:
                    # Process all available events
                    while True:
                        event = self.get_nowait()
                        try:
                            callback(event)
                        except Exception as e:
                            logger.error(f"Error processing event {event.event_type}: {e}")
                
                except queue.Empty:
                    # No events available, sleep and continue
                    time.sleep(interval_ms / 1000.0)
                
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    break
            
            logger.info("Stopped UI update polling")
        
        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()
        return thread


def create_ui_queue(maxsize: int = 100) -> UIUpdateQueue:
    """Factory function to create a UI update queue.
    
    Args:
        maxsize: Maximum queue size
        
    Returns:
        Configured UIUpdateQueue instance
    """
    return UIUpdateQueue(maxsize=maxsize)