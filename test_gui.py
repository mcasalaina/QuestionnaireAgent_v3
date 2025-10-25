#!/usr/bin/env python3
"""Minimal launcher for testing GUI without agent framework."""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def create_minimal_gui():
    """Create a minimal GUI to test the basic interface."""
    root = tk.Tk()
    root.title("Questionnaire Agent - Minimal Test")
    root.geometry("800x600")
    
    # Create main frame
    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # Title
    title_label = ttk.Label(main_frame, text="Questionnaire Agent - Minimal Test", 
                           font=("Arial", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # Test Excel import button
    import_btn = ttk.Button(main_frame, text="Test Excel Import", 
                           command=lambda: test_excel_import())
    import_btn.grid(row=1, column=0, padx=(0, 10), pady=5, sticky="w")
    
    # Status label
    status_label = ttk.Label(main_frame, text="Ready for testing")
    status_label.grid(row=2, column=0, columnspan=2, pady=10)
    
    # Text area for results
    text_area = tk.Text(main_frame, width=80, height=30)
    text_area.grid(row=3, column=0, columnspan=2, pady=10)
    
    def test_excel_import():
        try:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, "Testing Excel import functionality...\\n")
            
            # Test Excel loading
            from excel.loader import ExcelLoader
            text_area.insert(tk.END, "✓ Excel loader imported successfully\\n")
            
            # Test file dialog
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
            )
            
            if file_path:
                text_area.insert(tk.END, f"Selected file: {file_path}\\n")
                
                # Try to load the file
                loader = ExcelLoader()
                workbook_data = loader.load_workbook(file_path)
                
                text_area.insert(tk.END, f"✓ Loaded workbook with {len(workbook_data.sheets)} sheets\\n")
                
                for i, sheet in enumerate(workbook_data.sheets):
                    text_area.insert(tk.END, f"  Sheet {i+1}: '{sheet.sheet_name}' - {len(sheet.questions)} questions\\n")
                    
                text_area.insert(tk.END, "\\n✓ Excel import test successful!\\n")
                
            else:
                text_area.insert(tk.END, "No file selected\\n")
                
        except Exception as e:
            text_area.insert(tk.END, f"❌ Error: {e}\\n")
            import traceback
            text_area.insert(tk.END, traceback.format_exc())
    
    # Configure grid weights
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(3, weight=1)
    
    return root

if __name__ == "__main__":
    try:
        print("Creating minimal GUI test...")
        root = create_minimal_gui()
        print("Starting GUI...")
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()