"""Session management for web interface.

Handles session lifecycle: creation, retrieval, updating, and cleanup.
Sessions are stored in memory (suitable for localhost single-user deployment).
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, Any

from .models import (
    WebSession,
    SessionConfig,
    ProcessingJob,
    JobStatus,
)

logger = logging.getLogger(__name__)


class SessionData:
    """Internal session data container with mutable state."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.config = SessionConfig()
        self.workbook_data: Optional[Any] = None  # WorkbookData from utils.data_types
        self.processing_job: Optional[ProcessingJob] = None
        self.temp_file_path: Optional[str] = None
        self.spreadsheet_rows: list = []  # Cached rows for grid display
        self.spreadsheet_columns: Dict[str, list] = {}  # Sheet -> column names


class SessionManager:
    """Manages web sessions with in-memory storage."""

    def __init__(self):
        """Initialize the session manager."""
        self._sessions: Dict[str, SessionData] = {}
        logger.info("SessionManager initialized")

    def create_session(self) -> str:
        """Create a new session and return its ID.

        Returns:
            str: UUID of the newly created session
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = SessionData(session_id)
        logger.info(f"Created session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve a session by ID.

        Args:
            session_id: The session UUID

        Returns:
            SessionData if found, None otherwise
        """
        return self._sessions.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: The session UUID

        Returns:
            True if session exists
        """
        return session_id in self._sessions

    def update_config(self, session_id: str, context: Optional[str] = None,
                      char_limit: Optional[int] = None) -> bool:
        """Update session configuration.

        Args:
            session_id: The session UUID
            context: New context value (optional)
            char_limit: New character limit (optional)

        Returns:
            True if update successful, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        if context is not None:
            session.config.context = context
        if char_limit is not None:
            session.config.char_limit = char_limit

        logger.debug(f"Updated config for session {session_id}: context={context}, char_limit={char_limit}")
        return True

    def set_workbook(self, session_id: str, workbook_data: Any,
                     temp_file_path: str, columns: Dict[str, list]) -> bool:
        """Store workbook data for a session.

        Args:
            session_id: The session UUID
            workbook_data: WorkbookData instance from utils.data_types
            temp_file_path: Path to temporary Excel file
            columns: Dict mapping sheet names to column name lists

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session.workbook_data = workbook_data
        session.temp_file_path = temp_file_path
        session.spreadsheet_columns = columns
        logger.info(f"Set workbook for session {session_id}: {temp_file_path}")
        return True

    def set_processing_job(self, session_id: str, job: ProcessingJob) -> bool:
        """Set the active processing job for a session.

        Args:
            session_id: The session UUID
            job: ProcessingJob instance

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session.processing_job = job
        logger.info(f"Set processing job {job.job_id} for session {session_id}")
        return True

    def get_processing_job(self, session_id: str) -> Optional[ProcessingJob]:
        """Get the active processing job for a session.

        Args:
            session_id: The session UUID

        Returns:
            ProcessingJob if exists, None otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return None
        return session.processing_job

    def update_job_status(self, session_id: str, status: JobStatus,
                          error: Optional[str] = None) -> bool:
        """Update processing job status.

        Args:
            session_id: The session UUID
            status: New job status
            error: Error message (for ERROR status)

        Returns:
            True if successful, False if session/job not found
        """
        session = self.get_session(session_id)
        if not session or not session.processing_job:
            return False

        session.processing_job.status = status
        if error:
            session.processing_job.error = error
        if status in (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.ERROR):
            session.processing_job.completed_at = datetime.now()

        logger.info(f"Updated job status for session {session_id}: {status}")
        return True

    def update_job_progress(self, session_id: str, processed_rows: int,
                            current_row: Optional[int] = None) -> bool:
        """Update processing job progress.

        Args:
            session_id: The session UUID
            processed_rows: Number of rows completed
            current_row: Current row being processed

        Returns:
            True if successful, False if session/job not found
        """
        session = self.get_session(session_id)
        if not session or not session.processing_job:
            return False

        session.processing_job.processed_rows = processed_rows
        session.processing_job.current_row = current_row
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and clean up resources.

        Args:
            session_id: The session UUID

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # Clean up temp file if exists
        if session.temp_file_path and os.path.exists(session.temp_file_path):
            try:
                os.remove(session.temp_file_path)
                logger.debug(f"Removed temp file: {session.temp_file_path}")
            except OSError as e:
                logger.warning(f"Failed to remove temp file: {e}")

        del self._sessions[session_id]
        logger.info(f"Deleted session: {session_id}")
        return True

    def cleanup_all(self) -> int:
        """Clean up all sessions and their resources.

        Returns:
            Number of sessions cleaned up
        """
        count = len(self._sessions)
        session_ids = list(self._sessions.keys())
        for session_id in session_ids:
            self.delete_session(session_id)
        logger.info(f"Cleaned up {count} sessions")
        return count

    @property
    def session_count(self) -> int:
        """Get the current number of active sessions."""
        return len(self._sessions)


# Global session manager instance
session_manager = SessionManager()
