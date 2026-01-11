"""Server-Sent Events (SSE) manager for real-time updates.

Handles per-session event queues and streaming to connected clients.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, AsyncGenerator, Any

from .models import SSEMessage, SSEMessageType

logger = logging.getLogger(__name__)


class SSEManager:
    """Manages Server-Sent Events streams for web clients."""

    def __init__(self, max_queue_size: int = 100):
        """Initialize the SSE manager.

        Args:
            max_queue_size: Maximum number of queued messages per session
        """
        self._queues: Dict[str, asyncio.Queue] = {}
        self._max_queue_size = max_queue_size
        logger.info("SSEManager initialized")

    def register_session(self, session_id: str) -> asyncio.Queue:
        """Register a session for SSE events.

        Args:
            session_id: The session UUID

        Returns:
            The event queue for this session
        """
        if session_id not in self._queues:
            self._queues[session_id] = asyncio.Queue(maxsize=self._max_queue_size)
            logger.debug(f"Registered SSE queue for session: {session_id}")
        return self._queues[session_id]

    def unregister_session(self, session_id: str) -> bool:
        """Unregister a session's SSE queue.

        Args:
            session_id: The session UUID

        Returns:
            True if unregistered, False if not found
        """
        if session_id in self._queues:
            del self._queues[session_id]
            logger.debug(f"Unregistered SSE queue for session: {session_id}")
            return True
        return False

    def is_registered(self, session_id: str) -> bool:
        """Check if a session has an active SSE queue.

        Args:
            session_id: The session UUID

        Returns:
            True if session is registered
        """
        return session_id in self._queues

    async def send_event(self, session_id: str, event_type: SSEMessageType,
                         data: Dict[str, Any]) -> bool:
        """Send an event to a specific session.

        Args:
            session_id: The session UUID
            event_type: Type of SSE message
            data: Event payload data

        Returns:
            True if event was queued, False if session not registered
        """
        queue = self._queues.get(session_id)
        if not queue:
            logger.warning(f"Attempted to send event to unregistered session: {session_id}")
            return False

        message = SSEMessage(
            type=event_type,
            timestamp=datetime.now(),
            data=data
        )

        try:
            # Use put_nowait to avoid blocking if queue is full
            queue.put_nowait(message)
            logger.debug(f"Sent {event_type.value} event to session {session_id}")
            return True
        except asyncio.QueueFull:
            logger.warning(f"SSE queue full for session {session_id}, dropping event")
            return False

    async def send_progress(self, session_id: str, row: int, total: int) -> bool:
        """Send a progress update event.

        Args:
            session_id: The session UUID
            row: Current row number
            total: Total number of rows

        Returns:
            True if event was sent
        """
        percentage = (row / total * 100) if total > 0 else 0
        return await self.send_event(
            session_id,
            SSEMessageType.PROGRESS,
            {"row": row, "total": total, "percentage": round(percentage, 1)}
        )

    async def send_answer(self, session_id: str, row: int, question: str,
                          answer: str, reasoning: str = "") -> bool:
        """Send an answer completed event.

        Args:
            session_id: The session UUID
            row: Row number that was answered
            question: The question text
            answer: The generated answer
            reasoning: Optional reasoning trace

        Returns:
            True if event was sent
        """
        return await self.send_event(
            session_id,
            SSEMessageType.ANSWER,
            {"row": row, "question": question, "answer": answer, "reasoning": reasoning}
        )

    async def send_error(self, session_id: str, message: str,
                         row: Optional[int] = None) -> bool:
        """Send an error event.

        Args:
            session_id: The session UUID
            message: Error message
            row: Optional row number where error occurred

        Returns:
            True if event was sent
        """
        data = {"message": message}
        if row is not None:
            data["row"] = row
        return await self.send_event(session_id, SSEMessageType.ERROR, data)

    async def send_complete(self, session_id: str, total_processed: int,
                            duration_seconds: float) -> bool:
        """Send a job completion event.

        Args:
            session_id: The session UUID
            total_processed: Total rows processed
            duration_seconds: Total processing time

        Returns:
            True if event was sent
        """
        return await self.send_event(
            session_id,
            SSEMessageType.COMPLETE,
            {"total_processed": total_processed, "duration_seconds": round(duration_seconds, 2)}
        )

    async def send_status(self, session_id: str, status: str, job_id: str) -> bool:
        """Send a status change event.

        Args:
            session_id: The session UUID
            status: New status string
            job_id: The job identifier

        Returns:
            True if event was sent
        """
        return await self.send_event(
            session_id,
            SSEMessageType.STATUS,
            {"status": status, "job_id": job_id}
        )

    async def send_row_started(self, session_id: str, row: int, total: int) -> bool:
        """Send a row started event when processing begins on a row.

        Args:
            session_id: The session UUID
            row: Row index (0-based) that is starting
            total: Total number of rows to process

        Returns:
            True if event was sent
        """
        return await self.send_event(
            session_id,
            SSEMessageType.ROW_STARTED,
            {"row": row, "total": total}
        )

    async def send_agent_progress(self, session_id: str, row: int, agent_name: str,
                                   message: str = "") -> bool:
        """Send an agent progress event when agent changes within a row.

        Args:
            session_id: The session UUID
            row: Row index (0-based) being processed
            agent_name: Name of the agent currently processing (e.g., "QuestionAnswerer")
            message: Optional progress message

        Returns:
            True if event was sent
        """
        return await self.send_event(
            session_id,
            SSEMessageType.AGENT_PROGRESS,
            {"row": row, "agent_name": agent_name, "message": message}
        )

    async def stream_events(self, session_id: str) -> AsyncGenerator[str, None]:
        """Async generator that yields SSE-formatted events.

        This is used with FastAPI's StreamingResponse for SSE endpoints.

        Args:
            session_id: The session UUID

        Yields:
            SSE-formatted event strings
        """
        queue = self.register_session(session_id)
        try:
            while True:
                try:
                    # Wait for next message with timeout for keepalive
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message.to_sse_string()
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent connection timeout
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            logger.debug(f"SSE stream cancelled for session: {session_id}")
            raise
        finally:
            self.unregister_session(session_id)

    def cleanup_all(self) -> int:
        """Clean up all SSE queues.

        Returns:
            Number of queues cleaned up
        """
        count = len(self._queues)
        self._queues.clear()
        logger.info(f"Cleaned up {count} SSE queues")
        return count


# Global SSE manager instance
sse_manager = SSEManager()
