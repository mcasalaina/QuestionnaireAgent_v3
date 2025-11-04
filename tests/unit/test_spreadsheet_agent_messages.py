"""Unit tests for agent-specific messages in spreadsheet view."""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock tkinter before importing spreadsheet_view
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.spreadsheet_view import SpreadsheetView
from utils.data_types import CellState


class TestAgentMessages:
    """Test agent-specific message display in spreadsheet view."""
    
    def test_get_response_text_with_question_answerer(self):
        """Test that question_answerer agent shows 'Composing Answer...'"""
        view = SpreadsheetView(None, None)
        result = view._get_response_text(CellState.WORKING, "", "question_answerer")
        assert result == "Composing Answer..."
    
    def test_get_response_text_with_answer_checker(self):
        """Test that answer_checker agent shows 'Checking Answer...'"""
        view = SpreadsheetView(None, None)
        result = view._get_response_text(CellState.WORKING, "", "answer_checker")
        assert result == "Checking Answer..."
    
    def test_get_response_text_with_link_checker(self):
        """Test that link_checker agent shows 'Checking Links...'"""
        view = SpreadsheetView(None, None)
        result = view._get_response_text(CellState.WORKING, "", "link_checker")
        assert result == "Checking Links..."
    
    def test_get_response_text_with_no_agent(self):
        """Test that no agent name shows 'Working...'"""
        view = SpreadsheetView(None, None)
        result = view._get_response_text(CellState.WORKING, "", None)
        assert result == "Working..."
    
    def test_get_response_text_with_unknown_agent(self):
        """Test that unknown agent name shows 'Working...'"""
        view = SpreadsheetView(None, None)
        result = view._get_response_text(CellState.WORKING, "", "unknown_agent")
        assert result == "Working..."
    
    def test_get_response_text_completed_state(self):
        """Test that completed state shows the answer text."""
        view = SpreadsheetView(None, None)
        answer = "This is the answer"
        result = view._get_response_text(CellState.COMPLETED, answer, "question_answerer")
        assert result == answer
    
    def test_get_response_text_pending_state(self):
        """Test that pending state shows empty string."""
        view = SpreadsheetView(None, None)
        result = view._get_response_text(CellState.PENDING, "", "question_answerer")
        assert result == ""
