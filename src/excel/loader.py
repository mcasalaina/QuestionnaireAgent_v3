"""Excel file loading and saving functionality."""

import openpyxl
from typing import List, Optional
from utils.data_types import WorkbookData, SheetData, CellState
from utils.exceptions import ExcelFormatError
import logging
import os

logger = logging.getLogger(__name__)


class ExcelLoader:
    """Loads and saves Excel workbooks for live processing visualization."""
    
    def __init__(self, column_identifier=None):
        """Initialize Excel loader.
        
        Args:
            column_identifier: Optional ColumnIdentifier instance for detecting columns.
                             If None, will use fallback (column A = Question, B = Response).
        """
        self.column_identifier = column_identifier
    
    def load_workbook(self, file_path: str) -> WorkbookData:
        """Load Excel file into WorkbookData structure.
        
        Args:
            file_path: Absolute path to Excel file (.xlsx or .xls)
            
        Returns:
            WorkbookData with all visible sheets and questions
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ExcelFormatError: If file format is invalid
            ExcelFormatError: If no visible sheets found
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        if not file_path.lower().endswith(('.xlsx', '.xls')):
            raise ExcelFormatError("File must be an Excel file (.xlsx or .xls)")
        
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as e:
            raise ExcelFormatError(f"Invalid Excel file: {e}")
        
        sheets = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            
            # Skip hidden sheets
            if ws.sheet_state != 'visible':
                logger.info(f"Skipping hidden sheet: {sheet_name}")
                continue
            
            # Get headers from first row
            headers = []
            for cell in ws[1]:
                headers.append(cell.value if cell.value else '')
            
            if not headers:
                logger.warning(f"Sheet '{sheet_name}' has no headers, skipping")
                continue
            
            # Identify columns using column identifier or fallback to defaults
            column_mapping = {'question': 0, 'response': 1, 'documentation': None}
            if self.column_identifier:
                try:
                    # Column identification is now synchronous
                    column_mapping = self.column_identifier.identify_columns(headers)
                    logger.info(f"Identified columns for sheet '{sheet_name}': {column_mapping}")
                except Exception as e:
                    logger.warning(f"Failed to identify columns, using defaults (A=Question, B=Response): {e}")
            
            question_col = column_mapping.get('question')
            response_col = column_mapping.get('response')
            doc_col = column_mapping.get('documentation')
            
            if question_col is None:
                logger.warning(f"Sheet '{sheet_name}' has no question column identified, skipping")
                continue
            
            # Extract questions from identified question column (0-based to 1-based for openpyxl)
            questions = []
            for row in ws.iter_rows(min_row=2, min_col=question_col+1, max_col=question_col+1):
                cell = row[0]
                if cell.value and str(cell.value).strip():
                    questions.append(str(cell.value).strip())
                else:
                    break  # Stop at first empty cell
            
            if not questions:
                logger.warning(f"Sheet '{sheet_name}' has no questions, skipping")
                continue
            
            # Limit questions per sheet
            if len(questions) > 100:
                logger.warning(f"Sheet '{sheet_name}' has {len(questions)} questions, limiting to 100")
                questions = questions[:100]
            
            # Create SheetData with column mapping
            sheet_data = SheetData(
                sheet_name=sheet_name,
                sheet_index=len(sheets),  # Reindex after filtering
                questions=questions,
                answers=[None] * len(questions),
                cell_states=[CellState.PENDING] * len(questions),
                question_col_index=question_col,
                response_col_index=response_col,
                documentation_col_index=doc_col
            )
            sheets.append(sheet_data)
        
        if not sheets:
            raise ExcelFormatError("No visible sheets with questions found")
        
        # Limit total sheets
        if len(sheets) > 10:
            logger.warning(f"Workbook has {len(sheets)} sheets, limiting to 10")
            sheets = sheets[:10]
        
        total_questions = sum(len(s.questions) for s in sheets)
        logger.info(f"Loaded {len(sheets)} sheets with {total_questions} total questions")
        
        return WorkbookData(file_path=file_path, sheets=sheets)
    
    def save_workbook(self, workbook_data: WorkbookData) -> None:
        """Save all answers back to the Excel file.
        
        Args:
            workbook_data: WorkbookData with completed answers
            
        Raises:
            ExcelFormatError: If workbook structure changed
            IOError: If file cannot be written
        """
        try:
            wb = openpyxl.load_workbook(workbook_data.file_path)
        except Exception as e:
            raise ExcelFormatError(f"Cannot reopen Excel file: {e}")
        
        # Validate that sheets still exist
        existing_sheet_names = set(wb.sheetnames)
        for sheet_data in workbook_data.sheets:
            if sheet_data.sheet_name not in existing_sheet_names:
                raise ExcelFormatError(f"Sheet '{sheet_data.sheet_name}' no longer exists in file")
        
        # Write answers to identified response columns
        for sheet_data in workbook_data.sheets:
            ws = wb[sheet_data.sheet_name]
            
            # Determine response column (default to column B if not specified)
            response_col = sheet_data.response_col_index if sheet_data.response_col_index is not None else 1
            response_col_letter = openpyxl.utils.get_column_letter(response_col + 1)  # Convert 0-based to 1-based
            
            # Write header if response column is empty
            if ws.cell(row=1, column=response_col + 1).value is None:
                ws.cell(row=1, column=response_col + 1, value="Response")
            
            # Write answers starting from row 2
            for row_idx, answer in enumerate(sheet_data.answers, start=2):
                if answer:
                    ws.cell(row=row_idx, column=response_col + 1, value=answer)
        
        try:
            wb.save(workbook_data.file_path)
            logger.info(f"Saved workbook to {workbook_data.file_path}")
        except Exception as e:
            raise IOError(f"Cannot save Excel file: {e}")
        finally:
            wb.close()