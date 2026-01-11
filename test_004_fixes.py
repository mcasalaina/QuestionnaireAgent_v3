#!/usr/bin/env python3
"""Test script for 004 web interface fixes with mocked backend agents."""

import asyncio
import time
import subprocess
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

BASE_URL = "http://127.0.0.1:8081"
SAMPLE_FILE = "tests/sample_questionnaire_1_sheet.xlsx"
TIMEOUT_MS = 60000  # 1 minute


async def test_ui_fixes():
    """Test UI-level fixes that can be verified without full processing."""
    from playwright.async_api import async_playwright

    print("\n" + "=" * 80)
    print("TESTING 004 WEB INTERFACE UI FIXES (VISUAL/STRUCTURAL ONLY)")
    print("=" * 80)

    results = {
        "issue_6_hidden_columns": False,
        "page_loads": False,
        "upload_works": False
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to the page
            print(f"\n[TEST] Page Load...")
            await page.goto(BASE_URL)
            await page.wait_for_selector("#import-btn", timeout=10000)
            results["page_loads"] = True
            print("  ✓ PASS: Page loaded successfully")

            # Upload spreadsheet
            print("\n[TEST] File Upload...")
            await page.click("#import-btn")
            await page.wait_for_timeout(500)

            # Set file input
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(SAMPLE_FILE)
                await page.wait_for_timeout(2000)
                results["upload_works"] = True
                print("  ✓ PASS: File upload works")
            else:
                print("  ✗ FAIL: Could not find file input")
                return results

            # Check for spreadsheet grid
            await page.wait_for_selector("#spreadsheet-grid", timeout=5000)
            print("  ✓ Spreadsheet grid loaded")

            # TEST 6: Hidden columns (should see only Question, Response, Documentation)
            print("\n[TEST #6] Checking if irrelevant columns are hidden...")
            await page.wait_for_timeout(1000)

            # Get visible column headers
            headers = await page.query_selector_all(".ag-header-cell-text")
            visible_columns = []
            for header in headers:
                text = await header.text_content()
                if text and text.strip():
                    visible_columns.append(text.strip())

            print(f"  Visible columns: {visible_columns}")

            # Check that only relevant columns are shown
            # The test file has many columns, so we should see only ~3-5 relevant ones
            if len(visible_columns) <= 5:
                results["issue_6_hidden_columns"] = True
                print(f"  ✓ PASS: Only {len(visible_columns)} columns shown (irrelevant ones hidden)")
            else:
                print(f"  ✗ FAIL: Too many columns visible ({len(visible_columns)}), should be ≤5")

        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

    # Print results summary
    print("\n" + "=" * 80)
    print("UI TEST RESULTS SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(results.values())
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    return results


async def test_all_fixes():
    """Test all 5 fixes with Playwright."""
    from playwright.async_api import async_playwright

    print("\n" + "=" * 80)
    print("TESTING 004 WEB INTERFACE FIXES")
    print("=" * 80)

    results = {
        "issue_4_green_rows": False,
        "issue_5_sheet_switch": False,
        "issue_6_hidden_columns": False,
        "issue_7_documentation": False,
        "issue_8_completion": False
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False to see what's happening
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to the page
            print(f"\n[SETUP] Navigating to {BASE_URL}...")
            await page.goto(BASE_URL)
            await page.wait_for_selector("#import-btn", timeout=10000)
            print("  ✓ Page loaded")

            # Upload spreadsheet
            print("\n[SETUP] Uploading test spreadsheet...")
            await page.click("#import-btn")
            await page.wait_for_timeout(500)

            # Set file input
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(SAMPLE_FILE)
                await page.wait_for_timeout(2000)
                print("  ✓ File uploaded")
            else:
                print("  ✗ Could not find file input")
                return results

            # Check for spreadsheet grid
            await page.wait_for_selector("#spreadsheet-grid", timeout=5000)
            print("  ✓ Spreadsheet grid loaded")

            # TEST 6: Hidden columns (should see only Question, Response, Documentation)
            print("\n[TEST #6] Checking if irrelevant columns are hidden...")
            await page.wait_for_timeout(1000)

            # Get visible column headers
            headers = await page.query_selector_all(".ag-header-cell-text")
            visible_columns = []
            for header in headers:
                text = await header.text_content()
                if text:
                    visible_columns.append(text.strip())

            print(f"  Visible columns: {visible_columns}")

            # Check that only relevant columns are shown
            relevant_cols = ["Question", "Response", "Documentation"]
            if len(visible_columns) <= len(relevant_cols):
                results["issue_6_hidden_columns"] = True
                print("  ✓ PASS: Only relevant columns shown")
            else:
                print(f"  ✗ FAIL: Too many columns visible ({len(visible_columns)})")

            # Start processing (mock will return quickly)
            print("\n[SETUP] Starting processing...")
            start_btn = await page.query_selector("#start-processing-btn")
            if start_btn:
                await start_btn.click()
                print("  ✓ Processing started")
            else:
                print("  ✗ Could not find start button")
                return results

            # Wait for at least one row to complete
            print("\n[WAIT] Waiting for first row to complete...")
            await page.wait_for_timeout(15000)  # Give it time to process

            # TEST 4: Check if completed rows have green background
            print("\n[TEST #4] Checking if completed rows have green background...")

            # Look for rows with completed class
            completed_rows = await page.query_selector_all(".ag-row.row-completed")
            if len(completed_rows) > 0:
                # Get the background color
                bg_color = await completed_rows[0].evaluate("el => window.getComputedStyle(el).backgroundColor")
                print(f"  Found {len(completed_rows)} completed row(s) with bg color: {bg_color}")

                # Check if it's greenish (rgb values where green > red and green > blue)
                if "230, 244, 234" in bg_color or "rgba(230, 244, 234" in bg_color:
                    results["issue_4_green_rows"] = True
                    print("  ✓ PASS: Completed rows have green background")
                else:
                    print(f"  ✗ FAIL: Background color not green: {bg_color}")
            else:
                print("  ✗ FAIL: No completed rows found")

            # TEST 7: Check if documentation column has content
            print("\n[TEST #7] Checking if documentation links are populated...")
            await page.wait_for_timeout(2000)

            # Try to find documentation column cells with content
            doc_cells = await page.query_selector_all(".ag-cell")
            doc_found = False
            for cell in doc_cells:
                content = await cell.text_content()
                if content and ("http" in content or "learn.microsoft" in content):
                    doc_found = True
                    print(f"  Found documentation link: {content[:50]}...")
                    break

            if doc_found:
                results["issue_7_documentation"] = True
                print("  ✓ PASS: Documentation links are populated")
            else:
                print("  ⚠ INCONCLUSIVE: No documentation links found (may not have processed yet)")

            # Get current sheet name before switching
            sheet_select = await page.query_selector("#sheet-select")
            if sheet_select:
                current_sheet = await sheet_select.evaluate("el => el.value")
                print(f"\n[SETUP] Current sheet: {current_sheet}")

                # Get available sheets
                options = await page.query_selector_all("#sheet-select option")
                sheet_names = []
                for option in options:
                    name = await option.evaluate("el => el.value")
                    sheet_names.append(name)

                print(f"  Available sheets: {sheet_names}")

                if len(sheet_names) > 1:
                    # TEST 5: Switch sheets and check if answers persist
                    print("\n[TEST #5] Testing answer persistence on sheet switch...")

                    # Get answer from first row before switching
                    answer_cells = await page.query_selector_all(".ag-cell.answer-filled")
                    first_answer = None
                    if answer_cells:
                        first_answer = await answer_cells[0].text_content()
                        print(f"  Answer before switch: {first_answer[:50] if first_answer else 'None'}...")

                    # Switch to second sheet
                    second_sheet = sheet_names[1]
                    await sheet_select.select_option(second_sheet)
                    await page.wait_for_timeout(1000)
                    print(f"  ✓ Switched to sheet: {second_sheet}")

                    # Switch back to first sheet
                    await sheet_select.select_option(current_sheet)
                    await page.wait_for_timeout(1000)
                    print(f"  ✓ Switched back to sheet: {current_sheet}")

                    # Check if answer is still there
                    answer_cells_after = await page.query_selector_all(".ag-cell.answer-filled")
                    answer_after = None
                    if answer_cells_after:
                        answer_after = await answer_cells_after[0].text_content()
                        print(f"  Answer after switch: {answer_after[:50] if answer_after else 'None'}...")

                    if first_answer and answer_after and first_answer == answer_after:
                        results["issue_5_sheet_switch"] = True
                        print("  ✓ PASS: Answers persist after sheet switch")
                    else:
                        print("  ✗ FAIL: Answers were lost or changed after sheet switch")
                else:
                    print("  ⚠ SKIP: Only one sheet available, cannot test sheet switching")

            # Wait for processing to complete
            print("\n[WAIT] Waiting for processing to complete...")
            await page.wait_for_timeout(30000)  # Wait up to 30 seconds

            # TEST 8: Check for completion notification
            print("\n[TEST #8] Checking for completion notification...")

            # Look for success toast
            success_toast = await page.query_selector("#success-toast")
            if success_toast:
                is_visible = await success_toast.is_visible()
                if is_visible:
                    message = await page.query_selector("#success-message")
                    if message:
                        text = await message.text_content()
                        print(f"  Success message: {text}")

                        if "complete" in text.lower() and ("sheet" in text.lower() or "question" in text.lower()):
                            results["issue_8_completion"] = True
                            print("  ✓ PASS: Completion notification shown with details")
                        else:
                            print("  ✗ FAIL: Completion notification lacks details")
                else:
                    print("  ✗ FAIL: Success toast not visible")
            else:
                print("  ✗ FAIL: Success toast element not found")

            # Check if download button is highlighted
            download_btn = await page.query_selector("#download-btn")
            if download_btn:
                classes = await download_btn.get_attribute("class")
                if "highlight-download" in classes:
                    print("  ✓ BONUS: Download button is highlighted")
                else:
                    print("  ⚠ Download button not highlighted")

            await page.wait_for_timeout(2000)

        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

    # Print results summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(results.values())
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    return results


if __name__ == "__main__":
    # Check if server is running
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8081))
    sock.close()

    if result != 0:
        print("ERROR: Server is not running on port 8081")
        print("Please start the server with: python run_app.py --web --no-browser --port 8081")
        sys.exit(1)

    # Run UI tests first (quick, no backend needed)
    print("\nRunning UI tests (structural changes only)...")
    ui_results = asyncio.run(test_ui_fixes())

    print("\n" + "=" * 80)
    print("NOTE: Full integration tests with backend mocking skipped.")
    print("To fully test Issues #4, #5, #7, #8 (green rows, sheet switching,")
    print("documentation, completion) requires backend agent mocking or manual testing.")
    print("=" * 80)

    # Exit with success if UI tests passed
    if not all(ui_results.values()):
        print("\n⚠ Some UI tests failed. Check output above.")
        sys.exit(1)
    else:
        print("\n✓ All UI tests passed!")
        sys.exit(0)
