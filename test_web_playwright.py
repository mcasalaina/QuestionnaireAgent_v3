#!/usr/bin/env python3
"""Playwright test script for web interface testing with the new clarifications-based UI."""

import asyncio
import time
import subprocess
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

BASE_URL = "http://127.0.0.1:8889"
SAMPLE_FILE = "tests/fixtures/excel/single_sheet_5_questions.xlsx"
TIMEOUT_MS = 120000  # 2 minutes for processing timeout


async def wait_for_server(port: int, timeout: float = 30.0) -> bool:
    """Wait for the web server to become available."""
    import aiohttp
    start_time = time.time()
    url = f"http://127.0.0.1:{port}/health"

    while time.time() - start_time < timeout:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        return True
        except Exception:
            pass
        await asyncio.sleep(0.5)

    return False


async def test_web_interface():
    """Test the web interface with Playwright."""
    from playwright.async_api import async_playwright

    issues = []
    server_process = None

    try:
        # Start the web server with --no-browser flag
        print("Starting web server on port 8889...")
        server_process = subprocess.Popen(
            [sys.executable, "run_app.py", "--web", "--port", "8889", "--no-browser"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(Path(__file__).parent)
        )

        # Wait for server to be ready
        print("Waiting for server to start...")
        if not await wait_for_server(8889, timeout=60):
            issues.append("Server did not start within timeout")
            print("FAIL: Server did not start")
            return issues

        print("Server started successfully!")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            print("\n" + "=" * 60)
            print("Starting Web Interface Tests")
            print("=" * 60)

            # Test 1: Check health endpoint
            print("\n[TEST 1] Health endpoint check...")
            try:
                response = await page.request.get(f"{BASE_URL}/health")
                if response.status == 200:
                    print("  PASS: Health endpoint returns 200")
                else:
                    issues.append(f"Health endpoint returned {response.status}")
                    print(f"  FAIL: Health endpoint returned {response.status}")
            except Exception as e:
                issues.append(f"Health check failed: {e}")
                print(f"  FAIL: {e}")

            # Test 2: Load main page
            print("\n[TEST 2] Load main page...")
            try:
                await page.goto(BASE_URL)
                await page.wait_for_selector("#session-id", timeout=15000)
                title = await page.title()
                if "Questionnaire" in title:
                    print(f"  PASS: Page loaded with title '{title}'")
                else:
                    issues.append(f"Unexpected page title: {title}")
                    print(f"  FAIL: Unexpected title '{title}'")
            except Exception as e:
                issues.append(f"Page load failed: {e}")
                print(f"  FAIL: {e}")

            # Test 3: Session creation
            print("\n[TEST 3] Session creation...")
            try:
                await page.wait_for_function(
                    "document.getElementById('session-id').textContent !== 'Connecting...'",
                    timeout=15000
                )
                session_text = await page.locator("#session-id").text_content()
                if session_text and len(session_text) > 5:
                    print(f"  PASS: Session created: {session_text}")
                else:
                    issues.append(f"Invalid session: {session_text}")
                    print(f"  FAIL: Invalid session: {session_text}")
            except Exception as e:
                issues.append(f"Session creation failed: {e}")
                print(f"  FAIL: {e}")

            # Test 4: Verify UI layout matches clarifications (no tabs)
            print("\n[TEST 4] UI layout verification (clarifications spec)...")
            try:
                # Verify sidebar elements exist
                sidebar_elements = {
                    "#context-input": "Context input",
                    "#char-limit-input": "Character limit input",
                    "#max-retries-input": "Max retries input",
                    "#question-input": "Question textarea",
                    "#ask-btn": "Ask button",
                    "#import-btn": "Import From Excel button",
                }
                for selector, name in sidebar_elements.items():
                    el = page.locator(selector)
                    if await el.is_visible():
                        print(f"  PASS: {name} is visible")
                    else:
                        issues.append(f"{name} not visible")
                        print(f"  FAIL: {name} not visible")

                # Verify status bar at bottom
                status_bar = page.locator(".status-bar")
                if await status_bar.is_visible():
                    status_text = await page.locator("#status-text").text_content()
                    print(f"  PASS: Status bar visible with text: '{status_text}'")
                else:
                    issues.append("Status bar not visible")
                    print("  FAIL: Status bar not visible")

                # Verify NO tabs exist (per clarifications)
                tabs = page.locator(".tab-btn")
                tab_count = await tabs.count()
                if tab_count == 0:
                    print("  PASS: No tabs found (matches clarifications spec)")
                else:
                    issues.append(f"Found {tab_count} tabs - should have none per clarifications")
                    print(f"  FAIL: Found {tab_count} tabs - should have none")

            except Exception as e:
                issues.append(f"UI layout check failed: {e}")
                print(f"  FAIL: {e}")

            # Test 5: File upload with auto-mapping
            print("\n[TEST 5] File upload and auto-mapping...")
            try:
                file_input = page.locator("#file-upload")
                sample_path = Path(SAMPLE_FILE).absolute()

                if not sample_path.exists():
                    issues.append(f"Sample file not found: {sample_path}")
                    print(f"  FAIL: Sample file not found: {sample_path}")
                else:
                    await file_input.set_input_files(str(sample_path))
                    print("  INFO: File selected, waiting for upload processing...")

                    # Wait for spreadsheet mode to activate
                    await page.wait_for_selector("#spreadsheet-mode:not(.hidden)", timeout=10000)
                    print("  PASS: Switched to spreadsheet mode")

                    # Check if auto-mapping succeeded (no manual column mapping visible)
                    column_mapping = page.locator("#column-mapping")
                    await asyncio.sleep(1)  # Give UI time to update

                    if await column_mapping.is_visible():
                        print("  INFO: Manual column mapping shown (auto-map may have failed)")
                        # Click Start Processing to proceed
                        await page.click("#start-processing-btn")
                    else:
                        print("  PASS: Auto-mapping succeeded (no manual mapping required)")

            except Exception as e:
                issues.append(f"File upload failed: {e}")
                print(f"  FAIL: {e}")

            # Test 6: Monitor processing progress
            print("\n[TEST 6] Processing progress monitoring...")
            try:
                # Wait for processing to start
                await page.wait_for_function(
                    """() => {
                        const status = document.getElementById('status-text');
                        return status && status.textContent.includes('Processing');
                    }""",
                    timeout=30000
                )
                print("  PASS: Processing started")

                # Monitor for completion or timeout
                completed_rows = 0
                start_time = time.time()
                max_wait = 300  # 5 minutes max for 5 questions

                while time.time() - start_time < max_wait:
                    status_text = await page.locator("#status-text").text_content()
                    print(f"  STATUS: {status_text}")

                    if "Complete" in status_text:
                        print("  PASS: Processing completed!")
                        break
                    elif "Error" in status_text:
                        issues.append(f"Processing error: {status_text}")
                        print(f"  FAIL: {status_text}")
                        break

                    await asyncio.sleep(5)  # Check every 5 seconds
                else:
                    issues.append("Processing timed out after 5 minutes")
                    print("  FAIL: Processing timed out")

            except Exception as e:
                issues.append(f"Processing monitoring failed: {e}")
                print(f"  FAIL: {e}")

            # Test 7: Verify answers were generated
            print("\n[TEST 7] Verify answers in grid...")
            try:
                # Check if grid has populated cells
                grid = page.locator("#spreadsheet-grid")
                if await grid.is_visible():
                    # Look for answer content in cells
                    answer_cells = page.locator(".answer-filled")
                    answer_count = await answer_cells.count()

                    if answer_count > 0:
                        print(f"  PASS: Found {answer_count} answered rows in grid")
                    else:
                        # Check for any text in Response column
                        grid_text = await grid.inner_text()
                        if "AI" in grid_text or "machine learning" in grid_text.lower():
                            print("  PASS: Grid contains answer text")
                        else:
                            issues.append("No answers found in grid")
                            print("  FAIL: No answers found in grid")
                else:
                    issues.append("Grid not visible")
                    print("  FAIL: Grid not visible")
            except Exception as e:
                issues.append(f"Answer verification failed: {e}")
                print(f"  FAIL: {e}")

            # Test 8: Take screenshot
            print("\n[TEST 8] Taking screenshot...")
            try:
                screenshot_path = "specs/004-add-web-mode/test-screenshot.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"  PASS: Screenshot saved to {screenshot_path}")
            except Exception as e:
                issues.append(f"Screenshot failed: {e}")
                print(f"  FAIL: {e}")

            await browser.close()

    except Exception as e:
        issues.append(f"Test execution error: {e}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup: stop the server
        if server_process:
            print("\nStopping web server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("Server stopped.")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    if issues:
        print(f"\nFOUND {len(issues)} ISSUE(S):")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\nALL TESTS PASSED!")

    return issues


if __name__ == "__main__":
    issues = asyncio.run(test_web_interface())
    print(f"\n\nTotal issues: {len(issues)}")
    sys.exit(0 if len(issues) == 0 else 1)
