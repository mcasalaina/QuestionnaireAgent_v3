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
            # Skip blank rows and section headers, tracking original row indices
            questions = []
            row_indices = []  # Track original Excel row numbers (1-based)
            
            for row in ws.iter_rows(min_row=2, min_col=question_col+1, max_col=question_col+1):
                cell = row[0]
                cell_value = str(cell.value).strip() if cell.value else ''
                
                # Skip blank cells
                if not cell_value:
                    logger.debug(f"Skipping blank row {cell.row} in sheet '{sheet_name}'")
                    continue
                
                # Skip section headers (heuristic detection)
                if self._is_section_header(cell_value):
                    logger.info(f"Skipping section header at row {cell.row} in sheet '{sheet_name}': '{cell_value}'")
                    continue
                
                questions.append(cell_value)
                row_indices.append(cell.row)  # Store the actual Excel row number (1-based)
            
            if not questions:
                logger.warning(f"Sheet '{sheet_name}' has no questions, skipping")
                continue
            
            # Limit questions per sheet
            if len(questions) > 100:
                logger.warning(f"Sheet '{sheet_name}' has {len(questions)} questions, limiting to 100")
                questions = questions[:100]
                row_indices = row_indices[:100]
            
            # Create SheetData with column mapping and row indices
            sheet_data = SheetData(
                sheet_name=sheet_name,
                sheet_index=len(sheets),  # Reindex after filtering
                questions=questions,
                answers=[None] * len(questions),
                cell_states=[CellState.PENDING] * len(questions),
                question_col_index=question_col,
                response_col_index=response_col,
                documentation_col_index=doc_col,
                row_indices=row_indices
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
    
    # Constants for section header detection heuristics
    _MIN_TEXT_LENGTH = 3
    _MAX_NUMBERED_HEADER_LENGTH = 60
    _MAX_UPPERCASE_HEADER_WORDS = 6
    _MAX_TITLE_HEADER_WORDS = 5
    
    def _is_section_header(self, text: str) -> bool:
        """Determine if text appears to be a section header rather than a question.
        
        Uses heuristic rules to detect common section header patterns.
        
        Args:
            text: The cell text to analyze
            
        Returns:
            True if the text appears to be a section header, False otherwise
        """
        import re
        
        text = text.strip()
        
        # Empty or very short text
        if len(text) < self._MIN_TEXT_LENGTH:
            return True
        
        # Pattern 1: Starts with common section prefixes like "Section", "Part", "Chapter"
        section_prefixes = (
            'section ', 'part ', 'chapter ', 'category ', 'topic ', 
            'section:', 'part:', 'chapter:', 'category:', 'topic:',
            '---', '===', '***', '###'
        )
        if text.lower().startswith(section_prefixes):
            return True
        
        # Pattern 2: Entirely wrapped in decorators (dashes, equals, asterisks)
        if re.match(r'^[-=*#]+\s*.*\s*[-=*#]+$', text):
            return True
        
        # Pattern 3: Numbered sections like "1.", "1.1", "I.", "A." followed by short title
        if re.match(r'^(?:\d+\.|\d+\.\d+|[IVXLCDM]+\.|[A-Z]\.)\s+[^?]*$', text):
            # Only consider it a header if it doesn't end with '?'
            if not text.rstrip().endswith('?'):
                # And if it's relatively short without punctuation at end
                if len(text) < self._MAX_NUMBERED_HEADER_LENGTH and not text.rstrip().endswith(('.', '!', '?')):
                    return True
        
        # Pattern 4: All uppercase text (likely a header)
        if text.isupper() and len(text.split()) <= self._MAX_UPPERCASE_HEADER_WORDS:
            return True
        
        # Pattern 5: Text that contains only title-like content (no question marks, short)
        # and looks like a category label
        words = text.split()
        if (len(words) <= self._MAX_TITLE_HEADER_WORDS and 
            not text.endswith('?') and 
            text.istitle() and 
            ':' in text):
            return True
        
        return False
    
    def save_workbook(self, workbook_data: WorkbookData, output_path: str = None) -> str:
        """Save all answers back to the Excel file.
        
        Args:
            workbook_data: WorkbookData with completed answers
            output_path: Optional custom output path. If None, saves to original file.
            
        Returns:
            The path where the file was saved
            
        Raises:
            ExcelFormatError: If workbook structure changed
            IOError: If file cannot be written
        """
        # Use provided output path or default to original file path
        save_path = output_path if output_path else workbook_data.file_path
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
            
            # Write answers to the correct rows using stored row indices
            for i, answer in enumerate(sheet_data.answers):
                if answer:
                    # Use the original row index if available, otherwise fall back to sequential
                    if sheet_data.row_indices and i < len(sheet_data.row_indices):
                        row_num = sheet_data.row_indices[i]
                    else:
                        row_num = i + 2  # Fallback to sequential starting from row 2
                    ws.cell(row=row_num, column=response_col + 1, value=answer)
        
        try:
            wb.save(save_path)
            logger.info(f"Saved workbook to {save_path}")
        except Exception as e:
            raise IOError(f"Cannot save Excel file: {e}")
        finally:
            wb.close()
        
        return save_path