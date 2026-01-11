"""Playwright E2E tests for web interface launch and navigation.

Tests User Story 1: Launch Web Interface Mode
"""

import pytest
from playwright.sync_api import Page, expect


class TestServerLaunch:
    """Tests for server startup and initial page load."""

    def test_health_endpoint_accessible(self, page: Page, server_url: str):
        """Health endpoint should be accessible."""
        response = page.request.get(f"{server_url}/health")
        assert response.status == 200

    def test_index_page_loads(self, page: Page):
        """Main page should load successfully."""
        # Page fixture already navigates to server
        expect(page).to_have_title("Questionnaire Agent")

    def test_page_contains_header(self, page: Page):
        """Page should contain the app header."""
        header = page.locator(".app-header")
        expect(header).to_be_visible()

    def test_page_contains_session_id(self, page: Page):
        """Page should display a session ID."""
        session_el = page.locator("#session-id")
        expect(session_el).to_be_visible()
        # Should contain UUID-like text
        expect(session_el).not_to_have_text("Connecting...")


class TestSessionManagement:
    """Tests for session creation and persistence."""

    def test_session_created_on_load(self, page: Page):
        """A session should be created when page loads."""
        session_el = page.locator("#session-id")
        # Wait for session to be created
        page.wait_for_function(
            "() => document.getElementById('session-id').textContent !== 'Connecting...'"
        )
        text = session_el.text_content()
        assert len(text) > 0
        assert "..." in text  # Truncated UUID

    def test_session_persists_on_refresh(self, page: Page):
        """Session should persist across page refresh."""
        # Get initial session ID
        page.wait_for_function(
            "() => document.getElementById('session-id').textContent !== 'Connecting...'"
        )
        initial_session = page.evaluate("() => localStorage.getItem('sessionId')")

        # Refresh page
        page.reload()

        # Wait for session display
        page.wait_for_function(
            "() => document.getElementById('session-id').textContent !== 'Connecting...'"
        )

        # Check session is the same
        new_session = page.evaluate("() => localStorage.getItem('sessionId')")
        assert initial_session == new_session

    def test_different_tabs_get_same_session(self, browser, server_url, running_server):
        """Multiple tabs should share the same session (same localStorage)."""
        # Create first context/page
        context1 = browser.new_context()
        page1 = context1.new_page()
        page1.goto(server_url)
        page1.wait_for_selector("#session-id")
        page1.wait_for_function(
            "() => document.getElementById('session-id').textContent !== 'Connecting...'"
        )
        session1 = page1.evaluate("() => localStorage.getItem('sessionId')")

        # Create second page in same context (simulating new tab)
        page2 = context1.new_page()
        page2.goto(server_url)
        page2.wait_for_selector("#session-id")
        page2.wait_for_function(
            "() => document.getElementById('session-id').textContent !== 'Connecting...'"
        )
        session2 = page2.evaluate("() => localStorage.getItem('sessionId')")

        # Should be same session in same context
        assert session1 == session2

        context1.close()


class TestModeDisplay:
    """Tests for mode switching between Question and Spreadsheet modes."""

    def test_question_mode_visible_by_default(self, page: Page):
        """Question mode should be visible by default."""
        question_mode = page.locator("#question-mode")
        expect(question_mode).to_be_visible()

    def test_spreadsheet_mode_hidden_by_default(self, page: Page):
        """Spreadsheet mode should be hidden by default."""
        spreadsheet_mode = page.locator("#spreadsheet-mode")
        expect(spreadsheet_mode).to_be_hidden()

    def test_status_bar_shows_ready(self, page: Page):
        """Status bar should show 'Ready' on initial load."""
        status_text = page.locator("#status-text")
        expect(status_text).to_have_text("Ready")


class TestUIElements:
    """Tests for presence of essential UI elements."""

    def test_question_input_exists(self, page: Page):
        """Question textarea should exist."""
        textarea = page.locator("#question-input")
        expect(textarea).to_be_visible()

    def test_context_input_exists(self, page: Page):
        """Context input should exist with default value."""
        context_input = page.locator("#context-input")
        expect(context_input).to_be_visible()
        expect(context_input).to_have_value("Microsoft Azure AI")

    def test_char_limit_input_exists(self, page: Page):
        """Character limit input should exist with default value."""
        char_limit = page.locator("#char-limit-input")
        expect(char_limit).to_be_visible()
        expect(char_limit).to_have_value("2000")

    def test_ask_button_exists(self, page: Page):
        """Ask button should exist."""
        ask_btn = page.locator("#ask-btn")
        expect(ask_btn).to_be_visible()
        expect(ask_btn).to_be_enabled()
        expect(ask_btn).to_have_text("Ask!")

    def test_import_button_exists(self, page: Page):
        """Import From Excel button should exist."""
        import_btn = page.locator("#import-btn")
        expect(import_btn).to_be_visible()
        expect(import_btn).to_have_text("Import From Excel")

    def test_file_upload_exists(self, page: Page):
        """File upload input should exist (hidden)."""
        file_upload = page.locator("#file-upload")
        expect(file_upload).to_be_attached()


class TestStatusBar:
    """Tests for status bar display."""

    def test_status_bar_exists(self, page: Page):
        """Status bar should exist at bottom of page."""
        status_bar = page.locator(".status-bar")
        expect(status_bar).to_be_visible()

    def test_connection_indicator_exists(self, page: Page):
        """Connection indicator should exist."""
        indicator = page.locator("#connection-indicator")
        expect(indicator).to_be_visible()

    def test_status_text_exists(self, page: Page):
        """Status text should exist and show Ready."""
        status_text = page.locator("#status-text")
        expect(status_text).to_be_visible()
        expect(status_text).to_have_text("Ready")


class TestEmptyState:
    """Tests for empty state display."""

    def test_empty_state_shown_on_load(self, page: Page):
        """Empty state message should be shown on initial load."""
        empty_state = page.locator("#empty-state")
        expect(empty_state).to_be_visible()

    def test_answer_section_hidden_on_load(self, page: Page):
        """Answer section should be hidden on initial load."""
        answer_section = page.locator("#answer-section")
        expect(answer_section).to_be_hidden()
