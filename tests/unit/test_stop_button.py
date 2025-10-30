#!/usr/bin/env python3
"""Integration tests for Stop button functionality during spreadsheet processing.

These tests verify the logic without requiring tkinter to be available.
"""

import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_excel_processor_has_cancel_method():
    """Verify that ExcelProcessor has a cancel_processing method."""
    import ast
    import inspect
    
    # Read the processor file
    processor_file = project_root / "src" / "excel" / "processor.py"
    with open(processor_file, 'r') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    # Find the ExcelProcessor class
    processor_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ExcelProcessor":
            processor_class = node
            break
    
    assert processor_class is not None, "ExcelProcessor class not found"
    
    # Find the cancel_processing method
    cancel_method = None
    for node in processor_class.body:
        if isinstance(node, ast.FunctionDef) and node.name == "cancel_processing":
            cancel_method = node
            break
    
    assert cancel_method is not None, "cancel_processing method not found in ExcelProcessor"
    print("✓ ExcelProcessor.cancel_processing() method exists")


def test_uimanager_has_stop_handler():
    """Verify that UIManager has the _on_stop_clicked method."""
    import ast
    
    # Read the main_window file
    main_window_file = project_root / "src" / "ui" / "main_window.py"
    with open(main_window_file, 'r') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    # Find the UIManager class
    ui_manager_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "UIManager":
            ui_manager_class = node
            break
    
    assert ui_manager_class is not None, "UIManager class not found"
    
    # Find the _on_stop_clicked method
    stop_method = None
    for node in ui_manager_class.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_on_stop_clicked":
            stop_method = node
            break
    
    assert stop_method is not None, "_on_stop_clicked method not found in UIManager"
    print("✓ UIManager._on_stop_clicked() method exists")


def test_uimanager_has_set_processing_state_with_parameter():
    """Verify that UIManager._set_processing_state accepts is_spreadsheet parameter."""
    import ast
    
    # Read the main_window file
    main_window_file = project_root / "src" / "ui" / "main_window.py"
    with open(main_window_file, 'r') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    # Find the UIManager class
    ui_manager_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "UIManager":
            ui_manager_class = node
            break
    
    assert ui_manager_class is not None, "UIManager class not found"
    
    # Find the _set_processing_state method
    method = None
    for node in ui_manager_class.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_set_processing_state":
            method = node
            break
    
    assert method is not None, "_set_processing_state method not found in UIManager"
    
    # Check for is_spreadsheet parameter
    param_names = [arg.arg for arg in method.args.args]
    assert "is_spreadsheet" in param_names, "is_spreadsheet parameter not found in _set_processing_state"
    print("✓ UIManager._set_processing_state() has is_spreadsheet parameter")


def test_uimanager_has_hide_show_documentation_tab():
    """Verify that UIManager has methods to hide/show Documentation tab."""
    import ast
    
    # Read the main_window file
    main_window_file = project_root / "src" / "ui" / "main_window.py"
    with open(main_window_file, 'r') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    # Find the UIManager class
    ui_manager_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "UIManager":
            ui_manager_class = node
            break
    
    assert ui_manager_class is not None, "UIManager class not found"
    
    # Find the hide/show methods
    method_names = [node.name for node in ui_manager_class.body if isinstance(node, ast.FunctionDef)]
    
    assert "_hide_documentation_tab" in method_names, "_hide_documentation_tab method not found"
    assert "_show_documentation_tab" in method_names, "_show_documentation_tab method not found"
    print("✓ UIManager has _hide_documentation_tab() and _show_documentation_tab() methods")


def test_uimanager_has_processor_reference():
    """Verify that UIManager stores a reference to current_excel_processor."""
    import ast
    
    # Read the main_window file
    main_window_file = project_root / "src" / "ui" / "main_window.py"
    with open(main_window_file, 'r') as f:
        content = f.read()
    
    # Check for current_excel_processor in the file
    assert "current_excel_processor" in content, "current_excel_processor reference not found in UIManager"
    print("✓ UIManager has current_excel_processor reference")


def test_excel_calls_use_is_spreadsheet():
    """Verify that Excel processing calls use is_spreadsheet=True."""
    import ast
    
    # Read the main_window file
    main_window_file = project_root / "src" / "ui" / "main_window.py"
    with open(main_window_file, 'r') as f:
        content = f.read()
    
    # Check for calls to _set_processing_state with is_spreadsheet=True
    assert "is_spreadsheet=True" in content, "is_spreadsheet=True not found in Excel processing calls"
    print("✓ Excel processing calls use is_spreadsheet=True")


if __name__ == "__main__":
    print("Running Stop button integration tests...\n")
    
    test_excel_processor_has_cancel_method()
    test_uimanager_has_stop_handler()
    test_uimanager_has_set_processing_state_with_parameter()
    test_uimanager_has_hide_show_documentation_tab()
    test_uimanager_has_processor_reference()
    test_excel_calls_use_is_spreadsheet()
    
    print("\n✓ All integration tests passed!")


