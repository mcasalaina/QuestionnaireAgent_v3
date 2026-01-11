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


class TestTabNavigation:
    """Tests for tab navigation between Question and Spreadsheet modes."""

    def test_question_tab_active_by_default(self, page: Page):
        """Question tab should be active by default."""
        question_btn = page.locator('.tab-btn[data-tab="question-tab"]')
        expect(question_btn).to_have_class(/active/)

    def test_question_content_visible_by_default(self, page: Page):
        """Question content should be visible by default."""
        question_content = page.locator("#question-tab")
        expect(question_content).to_be_visible()

    def test_spreadsheet_content_hidden_by_default(self, page: Page):
        """Spreadsheet content should be hidden by default."""
        spreadsheet_content = page.locator("#spreadsheet-tab")
        expect(spreadsheet_content).to_be_hidden()

    def test_clicking_spreadsheet_tab_switches_view(self, page: Page):
        """Clicking spreadsheet tab should switch to spreadsheet view."""
        spreadsheet_btn = page.locator('.tab-btn[data-tab="spreadsheet-tab"]')
        spreadsheet_btn.click()

        # Spreadsheet tab should now be active
        expect(spreadsheet_btn).to_have_class(/active/)

        # Spreadsheet content should be visible
        spreadsheet_content = page.locator("#spreadsheet-tab")
        expect(spreadsheet_content).to_be_visible()

        # Question content should be hidden
        question_content = page.locator("#question-tab")
        expect(question_content).to_be_hidden()

    def test_can_switch_back_to_question_tab(self, page: Page):
        """Should be able to switch back to question tab."""
        # Switch to spreadsheet
        spreadsheet_btn = page.locator('.tab-btn[data-tab="spreadsheet-tab"]')
        spreadsheet_btn.click()

        # Switch back to question
        question_btn = page.locator('.tab-btn[data-tab="question-tab"]')
        question_btn.click()

        expect(question_btn).to_have_class(/active/)
        question_content = page.locator("#question-tab")
        expect(question_content).to_be_visible()


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

    def test_submit_button_exists(self, page: Page):
        """Submit button should exist."""
        submit_btn = page.locator("#submit-question-btn")
        expect(submit_btn).to_be_visible()
        expect(submit_btn).to_be_enabled()

    def test_file_upload_exists_in_spreadsheet_tab(self, page: Page):
        """File upload should exist in spreadsheet tab."""
        # Switch to spreadsheet tab
        spreadsheet_btn = page.locator('.tab-btn[data-tab="spreadsheet-tab"]')
        spreadsheet_btn.click()

        file_upload = page.locator("#file-upload")
        expect(file_upload).to_be_attached()


class TestStatusIndicators:
    """Tests for status indicator displays."""

    def test_connection_status_exists(self, page: Page):
        """Connection status indicator should exist."""
        status = page.locator("#connection-status")
        expect(status).to_be_visible()

    def test_processing_status_exists(self, page: Page):
        """Processing status indicator should exist."""
        status = page.locator("#processing-status")
        expect(status).to_be_visible()
        expect(status).to_contain_text("Idle")
