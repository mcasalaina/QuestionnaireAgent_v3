"""Unit tests for spreadsheet view text wrapping functionality."""

import pytest
import tkinter as tk
from ui.spreadsheet_view import SpreadsheetView
from utils.data_types import SheetData, CellState


class TestSpreadsheetTextWrapping:
    """Test text wrapping in SpreadsheetView."""
    
    @pytest.fixture
    def root_window(self):
        """Create a root tkinter window for testing."""
        root = tk.Tk()
        yield root
        root.destroy()
    
    @pytest.fixture
    def sample_sheet_data(self):
        """Create sample sheet data for testing."""
        sheet_data = SheetData(
            sheet_name="Test Sheet",
            sheet_index=0,
            questions=[
                "Short question?",
                "This is a much longer question that should wrap to multiple lines when displayed in the spreadsheet view to ensure proper formatting",
                "Medium length question about testing?"
            ],
            answers=["", "", ""],
            cell_states=[
                CellState.PENDING,
                CellState.PENDING,
                CellState.PENDING
            ]
        )
        return sheet_data
    
    @pytest.fixture
    def spreadsheet_view(self, root_window, sample_sheet_data):
        """Create a SpreadsheetView instance."""
        return SpreadsheetView(root_window, sample_sheet_data)
    
    def test_wrap_text_short(self, spreadsheet_view):
        """Test wrapping short text that doesn't need wrapping."""
        text = "Short text"
        result = spreadsheet_view._wrap_text(text, 80, 5)
        assert result == "Short text"
        assert len(result.split('\n')) == 1
    
    def test_wrap_text_medium(self, spreadsheet_view):
        """Test wrapping medium text to multiple lines."""
        text = "Microsoft Azure is a cloud computing platform and set of services offered by Microsoft. It provides a wide range of services."
        result = spreadsheet_view._wrap_text(text, 80, 5)
        lines = result.split('\n')
        assert len(lines) >= 2
        assert len(lines) <= 5
        # Verify no line exceeds the width significantly
        for line in lines:
            assert len(line) <= 85  # Allow some tolerance for word boundaries
    
    def test_wrap_text_long_truncate(self, spreadsheet_view):
        """Test wrapping very long text truncates at max lines."""
        text = " ".join(["This is a very long sentence that will need multiple lines."] * 10)
        result = spreadsheet_view._wrap_text(text, 80, 5)
        lines = result.split('\n')
        assert len(lines) == 5
        # Last line should end with ellipsis
        assert lines[-1].endswith('...')
    
    def test_wrap_text_empty(self, spreadsheet_view):
        """Test wrapping empty text."""
        result = spreadsheet_view._wrap_text("", 80, 5)
        assert result == ""
    
    def test_wrap_text_with_newlines(self, spreadsheet_view):
        """Test wrapping text that already contains newlines."""
        text = "Line 1\nLine 2\nLine 3"
        result = spreadsheet_view._wrap_text(text, 80, 5)
        lines = result.split('\n')
        assert len(lines) == 3
        assert "Line 1" in lines[0]
        assert "Line 2" in lines[1]
        assert "Line 3" in lines[2]
    
    def test_get_response_text_pending(self, spreadsheet_view):
        """Test getting response text for pending state."""
        result = spreadsheet_view._get_response_text(CellState.PENDING, "")
        assert result == ""
    
    def test_get_response_text_working(self, spreadsheet_view):
        """Test getting response text for working state."""
        result = spreadsheet_view._get_response_text(CellState.WORKING, "")
        assert result == "Working..."
    
    def test_get_response_text_completed_short(self, spreadsheet_view):
        """Test getting response text for completed state with short answer."""
        answer = "Short answer"
        result = spreadsheet_view._get_response_text(CellState.COMPLETED, answer)
        assert result == "Short answer"
    
    def test_get_response_text_completed_long(self, spreadsheet_view):
        """Test getting response text for completed state with long answer."""
        answer = "Microsoft Azure is a cloud computing platform and set of services offered by Microsoft. " * 5
        result = spreadsheet_view._get_response_text(CellState.COMPLETED, answer)
        lines = result.split('\n')
        # Should wrap to multiple lines
        assert len(lines) >= 2
        # Should not exceed max lines
        assert len(lines) <= 5
    
    def test_constants_defined(self, spreadsheet_view):
        """Test that wrapping constants are properly defined."""
        assert hasattr(spreadsheet_view, 'MAX_LINES_PER_CELL')
        assert hasattr(spreadsheet_view, 'CHARS_PER_LINE_RESPONSE')
        assert hasattr(spreadsheet_view, 'CHARS_PER_LINE_QUESTION')
        assert spreadsheet_view.MAX_LINES_PER_CELL == 5
        assert spreadsheet_view.CHARS_PER_LINE_RESPONSE == 80
        assert spreadsheet_view.CHARS_PER_LINE_QUESTION == 50
    
    def test_wrap_text_very_small_width(self, spreadsheet_view):
        """Test wrapping with very small width doesn't cause errors."""
        text = "Test text that is longer than expected"
        # Test with width smaller than 3 (edge case)
        result = spreadsheet_view._wrap_text(text, 2, 5)
        # Should handle gracefully without errors
        assert isinstance(result, str)
    
    def test_row_height_configured(self, root_window, sample_sheet_data):
        """Test that row height is properly configured for multi-line text."""
        view = SpreadsheetView(root_window, sample_sheet_data)
        treeview = view.render()
        
        # Get the style and check row height
        from tkinter import ttk
        style = ttk.Style()
        rowheight = style.lookup("Treeview", "rowheight")
        
        # Should be set to accommodate 5 lines (110 pixels)
        assert rowheight == 110
