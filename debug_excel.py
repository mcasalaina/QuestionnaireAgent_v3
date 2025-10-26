#!/usr/bin/env python3
"""Debug Excel loading to see what's happening."""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_excel_loading():
    """Test Excel loading step by step."""
    try:
        print("1. Testing Excel loader and column identifier import...")
        from excel.loader import ExcelLoader
        from excel.column_identifier import ColumnIdentifier
        print("   ✓ ExcelLoader and ColumnIdentifier imported successfully")
        
        print("2. Testing WorkbookData import...")
        from utils.data_types import WorkbookData
        print("   ✓ WorkbookData imported successfully")
        
        print("3. Testing Excel file loading with column identification...")
        column_identifier = ColumnIdentifier(azure_client=None)
        loader = ExcelLoader(column_identifier=column_identifier)
        
        # Use the test file we created earlier
        test_file = "test_files/sample_questions.xlsx"
        if not os.path.exists(test_file):
            print(f"   ✗ Test file {test_file} not found")
            return
            
        print(f"   Loading file: {test_file}")
        workbook_data = loader.load_workbook(test_file)
        print(f"   ✓ File loaded successfully")
        print(f"   - Sheets: {len(workbook_data.sheets)}")
        print(f"   - Total questions: {workbook_data.total_questions}")
        
        for i, sheet in enumerate(workbook_data.sheets):
            print(f"   - Sheet {i+1}: '{sheet.sheet_name}' ({len(sheet.questions)} questions)")
            if sheet.questions:
                print(f"     First question: '{sheet.questions[0][:50]}...'")  # It's a string, not object
        
        print("4. Testing WorkbookView import...")
        from ui.workbook_view import WorkbookView
        print("   ✓ WorkbookView imported successfully")
        
        print("5. Testing UI queue...")
        from utils.ui_queue import UIUpdateQueue
        ui_queue = UIUpdateQueue(maxsize=100)
        print("   ✓ UI queue created successfully")
        
        print("\nAll components loaded successfully!")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_loading()