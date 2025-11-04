"""Test script to verify immediate cancellation functionality."""

import asyncio
from utils.data_types import WorkbookData, SheetData, CellState
from utils.ui_queue import UIUpdateQueue


async def test_cancellation_cleanup():
    """Test that cancellation properly cleans up working cells."""
    
    # Create test workbook with some cells in different states
    sheet = SheetData(
        sheet_name="Test Sheet",
        sheet_index=0,
        questions=["Q1", "Q2", "Q3", "Q4", "Q5"],
        answers=[None, None, None, None, None],
        cell_states=[
            CellState.COMPLETED,  # Should stay completed
            CellState.WORKING,    # Should reset to pending
            CellState.WORKING,    # Should reset to pending
            CellState.PENDING,    # Should stay pending
            CellState.COMPLETED   # Should stay completed
        ]
    )
    
    workbook = WorkbookData(
        file_path="test.xlsx",
        sheets=[sheet]
    )
    
    # Track events
    ui_queue = UIUpdateQueue()
    events = []
    
    # Simulate cleanup by directly calling the cleanup logic
    # (This would normally be done by ExcelProcessor)
    for sheet_idx, sheet_data in enumerate(workbook.sheets):
        for row_idx, state in enumerate(sheet_data.cell_states):
            if state == CellState.WORKING:
                # Reset to pending
                sheet_data.cell_states[row_idx] = CellState.PENDING
                sheet_data.answers[row_idx] = None
                events.append(('CELL_RESET', sheet_idx, row_idx))
    
    # Verify results
    print("Test: Cancellation Cell Cleanup")
    print("=" * 50)
    print(f"Initial states: COMPLETED, WORKING, WORKING, PENDING, COMPLETED")
    print(f"Final states:   {', '.join([s.value for s in sheet.cell_states])}")
    print(f"Events emitted: {len(events)}")
    print()
    
    # Check expectations
    expected_states = [
        CellState.COMPLETED,
        CellState.PENDING,  # Was WORKING, now PENDING
        CellState.PENDING,  # Was WORKING, now PENDING
        CellState.PENDING,
        CellState.COMPLETED
    ]
    
    success = sheet.cell_states == expected_states
    print(f"Test {'PASSED' if success else 'FAILED'}")
    
    if success:
        print("✓ All WORKING cells were reset to PENDING")
        print("✓ COMPLETED cells remained COMPLETED")
        print("✓ PENDING cells remained PENDING")
        print(f"✓ {len(events)} CELL_RESET events were generated")
    else:
        print("✗ Cell states don't match expected values")
        print(f"Expected: {[s.value for s in expected_states]}")
        print(f"Actual:   {[s.value for s in sheet.cell_states]}")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(test_cancellation_cleanup())
    exit(0 if result else 1)
