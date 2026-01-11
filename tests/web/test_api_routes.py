"""Unit tests for web API routes.

Tests the FastAPI endpoints using TestClient without requiring a browser.
"""

import pytest
from pathlib import Path


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, test_client):
        """Health endpoint should return 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_status(self, test_client):
        """Health endpoint should return status field."""
        response = test_client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_health_check_returns_timestamp(self, test_client):
        """Health endpoint should return timestamp."""
        response = test_client.get("/health")
        data = response.json()
        assert "timestamp" in data


class TestSessionEndpoints:
    """Tests for session management endpoints."""

    def test_create_session_returns_201(self, test_client):
        """Create session should return 201 Created."""
        response = test_client.post("/api/session/create")
        assert response.status_code == 201

    def test_create_session_returns_session_id(self, test_client):
        """Create session should return a session ID."""
        response = test_client.post("/api/session/create")
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format

    def test_create_session_returns_config(self, test_client):
        """Create session should return default config."""
        response = test_client.post("/api/session/create")
        data = response.json()
        assert "config" in data
        assert data["config"]["context"] == "Microsoft Azure AI"
        assert data["config"]["char_limit"] == 2000

    def test_get_session_returns_200(self, test_client, session_id):
        """Get session should return 200 for existing session."""
        response = test_client.get(f"/api/session/{session_id}")
        assert response.status_code == 200

    def test_get_session_returns_404_for_invalid(self, test_client):
        """Get session should return 404 for invalid session ID."""
        response = test_client.get("/api/session/invalid-session-id")
        assert response.status_code == 404

    def test_update_config_returns_200(self, test_client, session_id):
        """Update config should return 200 for valid update."""
        response = test_client.put(
            f"/api/session/{session_id}/config",
            json={"context": "New Context", "char_limit": 1500}
        )
        assert response.status_code == 200

    def test_update_config_changes_values(self, test_client, session_id):
        """Update config should actually change the values."""
        test_client.put(
            f"/api/session/{session_id}/config",
            json={"context": "Updated Context", "char_limit": 1000}
        )

        response = test_client.get(f"/api/session/{session_id}")
        data = response.json()
        assert data["config"]["context"] == "Updated Context"
        assert data["config"]["char_limit"] == 1000

    def test_update_config_validates_char_limit(self, test_client, session_id):
        """Update config should reject invalid char limit."""
        response = test_client.put(
            f"/api/session/{session_id}/config",
            json={"char_limit": 50}  # Too low
        )
        assert response.status_code == 422

    def test_delete_session_returns_200(self, test_client):
        """Delete session should return 200."""
        # Create a session first
        create_response = test_client.post("/api/session/create")
        session_id = create_response.json()["session_id"]

        # Delete it
        response = test_client.delete(f"/api/session/{session_id}")
        assert response.status_code == 200

    def test_delete_session_removes_session(self, test_client):
        """Delete session should actually remove the session."""
        # Create a session
        create_response = test_client.post("/api/session/create")
        session_id = create_response.json()["session_id"]

        # Delete it
        test_client.delete(f"/api/session/{session_id}")

        # Try to get it
        response = test_client.get(f"/api/session/{session_id}")
        assert response.status_code == 404


class TestQuestionEndpoint:
    """Tests for single question processing endpoint."""

    def test_question_requires_session(self, test_client):
        """Question endpoint should require valid session."""
        response = test_client.post(
            "/api/question",
            json={
                "session_id": "invalid-session",
                "question": "What is Azure?",
                "context": "Microsoft",
                "char_limit": 2000
            }
        )
        assert response.status_code == 404

    def test_question_validates_input(self, test_client, session_id):
        """Question endpoint should validate input."""
        # Empty question
        response = test_client.post(
            "/api/question",
            json={
                "session_id": session_id,
                "question": "",
                "context": "Microsoft",
                "char_limit": 2000
            }
        )
        assert response.status_code == 422

    def test_question_validates_char_limit(self, test_client, session_id):
        """Question endpoint should validate char limit."""
        response = test_client.post(
            "/api/question",
            json={
                "session_id": session_id,
                "question": "What is Azure?",
                "context": "Microsoft",
                "char_limit": 50  # Too low
            }
        )
        assert response.status_code == 422


class TestSpreadsheetEndpoints:
    """Tests for spreadsheet processing endpoints."""

    def test_upload_requires_session(self, test_client, tmp_path):
        """Upload should require valid session."""
        # Create a dummy file
        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"dummy content")

        with open(test_file, "rb") as f:
            response = test_client.post(
                "/api/spreadsheet/upload",
                data={"session_id": "invalid-session"},
                files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        assert response.status_code == 404

    def test_upload_validates_file_format(self, test_client, session_id, tmp_path):
        """Upload should reject non-Excel files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("not an excel file")

        with open(test_file, "rb") as f:
            response = test_client.post(
                "/api/spreadsheet/upload",
                data={"session_id": session_id},
                files={"file": ("test.txt", f, "text/plain")}
            )
        assert response.status_code == 400

    def test_processing_status_requires_session(self, test_client):
        """Processing status should require valid session."""
        response = test_client.get("/api/spreadsheet/status/invalid-session")
        assert response.status_code == 404

    def test_processing_status_returns_no_job(self, test_client, session_id):
        """Processing status should indicate no job when none running."""
        response = test_client.get(f"/api/spreadsheet/status/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "NO_JOB"

    def test_stop_requires_active_job(self, test_client, session_id):
        """Stop endpoint should require an active job."""
        response = test_client.post(
            "/api/spreadsheet/stop",
            json={"session_id": session_id}
        )
        assert response.status_code == 400

    def test_download_requires_workbook(self, test_client, session_id):
        """Download should require a loaded workbook."""
        response = test_client.get(f"/api/spreadsheet/download/{session_id}")
        assert response.status_code == 400


class TestSSEEndpoint:
    """Tests for Server-Sent Events endpoint."""

    def test_sse_requires_session(self, test_client):
        """SSE endpoint should require valid session."""
        response = test_client.get("/api/sse/invalid-session")
        assert response.status_code == 404

    def test_sse_returns_stream_content_type(self, test_client, session_id):
        """SSE endpoint should return text/event-stream content type."""
        # Note: TestClient doesn't fully support streaming, but we can check headers
        with test_client.stream("GET", f"/api/sse/{session_id}") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            # Close early to avoid hanging
            break


class TestIndexRoute:
    """Tests for the main index route."""

    def test_index_returns_200(self, test_client):
        """Index should return 200 OK."""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_index_returns_html(self, test_client):
        """Index should return HTML content."""
        response = test_client.get("/")
        assert "text/html" in response.headers.get("content-type", "")

    def test_index_contains_app_title(self, test_client):
        """Index should contain the app title."""
        response = test_client.get("/")
        assert "Questionnaire Agent" in response.text
