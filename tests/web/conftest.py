"""Pytest configuration for web interface tests.

Provides fixtures for FastAPI TestClient and Playwright browser automation.
"""

import os
import sys
import pytest
import asyncio
import threading
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


# ============================================================================
# FastAPI TestClient Fixtures
# ============================================================================

@pytest.fixture
def test_client():
    """Create a FastAPI TestClient for API testing."""
    from fastapi.testclient import TestClient
    from web.app import app

    client = TestClient(app)
    yield client


@pytest.fixture
def session_id(test_client):
    """Create a session and return its ID."""
    response = test_client.post("/api/session/create")
    assert response.status_code == 201
    return response.json()["session_id"]


# ============================================================================
# Server Fixtures for Playwright
# ============================================================================

@pytest.fixture(scope="session")
def server_port():
    """Return the port for the test server."""
    return 8888


@pytest.fixture(scope="session")
def server_url(server_port):
    """Return the URL for the test server."""
    return f"http://127.0.0.1:{server_port}"


@pytest.fixture(scope="session")
def running_server(server_port):
    """Start the web server in a background thread for Playwright tests."""
    from web.app import app
    import uvicorn

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=server_port,
        log_level="warning"
    )
    server = uvicorn.Server(config)

    # Run server in background thread
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to be ready
    import requests
    max_wait = 10
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"http://127.0.0.1:{server_port}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)

    yield server

    # Cleanup (server will stop when thread terminates)


# ============================================================================
# Playwright Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Configure browser launch arguments."""
    return {
        "headless": True,  # Set to False for debugging
        "slow_mo": 0,  # Slow down actions for debugging
    }


@pytest.fixture
def page(browser, server_url, running_server):
    """Create a new browser page for each test."""
    context = browser.new_context()
    page = context.new_page()

    # Navigate to server
    page.goto(server_url)

    # Wait for page to load
    page.wait_for_selector("#session-id")

    yield page

    # Cleanup
    context.close()


# ============================================================================
# Screenshot on Failure
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot on test failure."""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        # Check if test has a page fixture
        if "page" in item.fixturenames:
            page = item.funcargs.get("page")
            if page:
                # Create screenshots directory
                screenshots_dir = Path(__file__).parent / "screenshots"
                screenshots_dir.mkdir(exist_ok=True)

                # Save screenshot
                screenshot_path = screenshots_dir / f"{item.name}.png"
                try:
                    page.screenshot(path=str(screenshot_path))
                    print(f"\nScreenshot saved: {screenshot_path}")
                except Exception as e:
                    print(f"\nFailed to capture screenshot: {e}")


# ============================================================================
# Async Support
# ============================================================================

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock Azure Services
# ============================================================================

@pytest.fixture
def mock_azure_auth(monkeypatch):
    """Mock Azure authentication for testing."""
    async def mock_test_auth():
        return True

    monkeypatch.setattr("utils.azure_auth.test_authentication", mock_test_auth)


@pytest.fixture
def mock_agent_coordinator(monkeypatch):
    """Mock the AgentCoordinator for testing without Azure services."""
    from utils.data_types import Answer, ProcessingResult

    class MockCoordinator:
        async def process_question(self, question):
            return ProcessingResult(
                success=True,
                answer=Answer(
                    content=f"Mock answer for: {question.text[:50]}...",
                    sources=[],
                    agent_reasoning=[],
                    char_count=100
                )
            )

    monkeypatch.setattr("web.app.AgentCoordinator", MockCoordinator)
