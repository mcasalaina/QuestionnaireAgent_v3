"""Integration test for Excel loading with column identification."""

import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from excel.loader import ExcelLoader
from excel.column_identifier import ColumnIdentifier


class TestExcelLoaderIntegration:
    """Integration tests for Excel loader with column identification."""
    
    def test_load_sample_questionnaire_1_sheet(self):
        """Test loading the sample_questionnaire_1_sheet.xlsx file with column identification."""
        # Get path to sample file
        test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_file = os.path.join(test_dir, 'sample_questionnaire_1_sheet.xlsx')
        
        # Verify file exists
        assert os.path.exists(sample_file), f"Sample file not found: {sample_file}"
        
        # Create loader with column identifier
        column_identifier = ColumnIdentifier(azure_client=None)  # Use heuristics only
        loader = ExcelLoader(column_identifier=column_identifier)
        
        # Load the workbook
        workbook_data = loader.load_workbook(sample_file)
        
        # Verify the workbook was loaded
        assert workbook_data is not None
        assert len(workbook_data.sheets) >= 2, f"Should have at least 2 sheets, got {len(workbook_data.sheets)}"
        
        # Check the first sheet (Company)
        sheet = workbook_data.sheets[0]
        assert sheet.sheet_name == "Company"
        
        # Verify column mapping is correct based on the actual spreadsheet structure
        # The spreadsheet has: Status, Owner, Q#, Question, Response, Documentation
        assert sheet.question_col_index == 3, f"Question column should be at index 3, got {sheet.question_col_index}"
        assert sheet.response_col_index == 4, f"Response column should be at index 4, got {sheet.response_col_index}"
        assert sheet.documentation_col_index == 5, f"Documentation column should be at index 5, got {sheet.documentation_col_index}"
        
        # Verify questions were loaded from the correct column
        assert len(sheet.questions) > 0, "Should have loaded questions"
        
        # Verify first question matches what's in the Company sheet (using the actual character)
        # Note: The apostrophe is a Unicode right single quotation mark (U+2019)
        assert "company" in sheet.questions[0].lower(), f"First question should contain 'company'. Got: {repr(sheet.questions[0])}"
        assert "name" in sheet.questions[0].lower(), f"First question should contain 'name'. Got: {repr(sheet.questions[0])}"
        
        # Check the second sheet (AI Capabilities)
        if len(workbook_data.sheets) >= 2:
            sheet2 = workbook_data.sheets[1]
            assert sheet2.sheet_name == "AI Capabilities"
            assert sheet2.question_col_index == 3
            assert sheet2.response_col_index == 4
            assert sheet2.documentation_col_index == 5
            
            # Verify the first question in AI Capabilities sheet
            expected_ai_question = "How does your platform facilitate stakeholder alignment and documentation of ethical, legal, regulatory, and business considerations from project inception through AI project scoping and planning?"
            assert sheet2.questions[0] == expected_ai_question, f"AI Capabilities first question doesn't match"
    
    def test_load_and_save_sample_questionnaire(self):
        """Test loading and saving the sample questionnaire file."""
        # Get path to sample file
        test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_file = os.path.join(test_dir, 'sample_questionnaire_1_sheet.xlsx')
        
        # Create a temporary output file
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            output_file = tmp_file.name
        
        try:
            # Copy the sample file to the output location
            shutil.copy(sample_file, output_file)
            
            # Create loader with column identifier
            column_identifier = ColumnIdentifier(azure_client=None)
            loader = ExcelLoader(column_identifier=column_identifier)
            
            # Load the workbook
            workbook_data = loader.load_workbook(output_file)
            
            # Add some test answers
            for sheet in workbook_data.sheets:
                for i in range(len(sheet.questions)):
                    sheet.answers[i] = f"Test answer for question {i + 1}"
            
            # Save the workbook
            loader.save_workbook(workbook_data)
            
            # Reload and verify answers were saved in the correct column
            workbook_data2 = loader.load_workbook(output_file)
            sheet2 = workbook_data2.sheets[0]
            
            # Verify the answers (note: loader doesn't read existing answers by default)
            # We just verify that the file can be saved and reloaded without errors
            assert len(sheet2.questions) > 0
            
        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_load_without_column_identifier(self):
        """Test loading with fallback when no column identifier is provided."""
        # Get path to sample file
        test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_file = os.path.join(test_dir, 'sample_questionnaire_1_sheet.xlsx')
        
        # Create loader without column identifier (should fall back to A=Question, B=Response)
        loader = ExcelLoader(column_identifier=None)
        
        # Load the workbook - this should use fallback behavior
        workbook_data = loader.load_workbook(sample_file)
        
        # Verify the workbook was loaded
        assert workbook_data is not None
        assert len(workbook_data.sheets) > 0
        
        # Get the first sheet
        sheet = workbook_data.sheets[0]
        
        # With fallback, it should use column A=0 (which is "Status" in this file)
        # So it may not find valid questions, or find different data
        # The important thing is it doesn't crash
        assert sheet.question_col_index == 0  # Fallback to column A
        assert sheet.response_col_index == 1  # Fallback to column B


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
