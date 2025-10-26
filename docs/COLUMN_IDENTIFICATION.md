# Column Identification Feature

## Overview

The application now automatically identifies the Question, Response, and Documentation columns in Excel spreadsheets instead of assuming they are always in columns A, B, and C.

## How It Works

When you load an Excel file, the system:

1. **Reads the header row** from each sheet
2. **Identifies columns** using either:
   - Azure AI (when available) - for intelligent, context-aware identification
   - Heuristic matching (fallback) - using keyword matching
3. **Extracts questions** from the identified Question column
4. **Writes answers** to the identified Response column
5. **Saves documentation links** to the Documentation column (if present)

## Supported Column Names

The heuristic identifier recognizes common column header patterns:

### Question Column
- "Question", "Q", "Query", "Ask", "Prompt"
- Case-insensitive matching
- Prioritizes full word "Question" over abbreviations

### Response Column
- "Response", "Answer", "Reply", "Result", "Output"

### Documentation Column
- "Documentation", "Docs", "Reference", "Link", "URL", "Source"

## Examples

### Example 1: Standard Format
```
| Status | Owner | Q# | Question | Response | Documentation |
```
**Identified as:**
- Question: Column D (index 3)
- Response: Column E (index 4)
- Documentation: Column F (index 5)

### Example 2: Simple Format
```
| Question | Answer |
```
**Identified as:**
- Question: Column A (index 0)
- Response: Column B (index 1)
- Documentation: None

### Example 3: Abbreviated Format
```
| Q | A | Docs |
```
**Identified as:**
- Question: Column A (index 0)
- Response: Column B (index 1)
- Documentation: Column C (index 2)

## Technical Details

### ColumnIdentifier Class

Located in `src/excel/column_identifier.py`, this service:

- **Accepts an Azure AI client** for intelligent identification (optional)
- **Falls back to heuristics** if Azure AI is unavailable or fails
- **Validates column mappings** to ensure consistency
- **Returns 0-based column indices** for easy programmatic access

### ExcelLoader Integration

The `ExcelLoader` class in `src/excel/loader.py`:

- **Accepts a ColumnIdentifier** in its constructor
- **Calls identify_columns()** when loading each sheet
- **Uses identified columns** for reading questions and writing answers
- **Falls back to defaults** (A=Question, B=Response) if no identifier is provided

### SheetData Structure

The `SheetData` class now includes column mapping information:

```python
@dataclass
class SheetData:
    sheet_name: str
    sheet_index: int
    questions: List[str]
    answers: List[Optional[str]]
    cell_states: List[CellState]
    question_col_index: Optional[int] = None      # NEW
    response_col_index: Optional[int] = None      # NEW
    documentation_col_index: Optional[int] = None # NEW
```

## Testing

### Unit Tests
- `tests/unit/test_column_identifier.py` - Tests heuristic matching, validation, and parsing

### Integration Tests
- `tests/integration/test_excel_column_identification.py` - Tests with real Excel files

Run tests with:
```bash
pytest tests/unit/test_column_identifier.py tests/integration/test_excel_column_identification.py -v
```

## Usage in Code

### Basic Usage (Heuristics Only)
```python
from excel.loader import ExcelLoader
from excel.column_identifier import ColumnIdentifier

# Create identifier without Azure AI (uses heuristics)
column_identifier = ColumnIdentifier(azure_client=None)

# Create loader with identifier
loader = ExcelLoader(column_identifier=column_identifier)

# Load workbook - columns will be auto-identified
workbook_data = loader.load_workbook('my_questionnaire.xlsx')
```

### With Azure AI (Future Enhancement)
```python
from excel.loader import ExcelLoader
from excel.column_identifier import ColumnIdentifier
from utils.azure_auth import get_azure_client

# Create identifier with Azure AI for intelligent identification
azure_client = await get_azure_client()
column_identifier = ColumnIdentifier(azure_client=azure_client)

# Rest is the same...
loader = ExcelLoader(column_identifier=column_identifier)
workbook_data = loader.load_workbook('my_questionnaire.xlsx')
```

## Future Enhancements

Potential improvements:

1. **User Confirmation UI** - Show identified columns to user for confirmation
2. **Column Mapping Editor** - Allow users to manually override column mapping
3. **Learning from Corrections** - Remember user corrections for similar files
4. **Multi-language Support** - Recognize column names in different languages
5. **Custom Column Names** - Allow users to define custom patterns

## Troubleshooting

### Issue: Wrong columns identified

**Solution:** The system prioritizes full word matches over abbreviations. If you have both "Q#" and "Question" columns, it will correctly choose "Question".

### Issue: No question column found

**Solution:** Ensure your column headers contain one of the recognized keywords. If using custom names, the system will need to be extended to support them.

### Issue: Want to use custom column names

**Solution:** You can either:
1. Rename your columns to match the recognized patterns
2. Extend the `ColumnIdentifier._identify_with_heuristics()` method to include your custom patterns

## Related Files

- `src/excel/column_identifier.py` - Column identification service
- `src/excel/loader.py` - Excel loading with column identification
- `src/utils/data_types.py` - SheetData with column mapping fields
- `tests/unit/test_column_identifier.py` - Unit tests
- `tests/integration/test_excel_column_identification.py` - Integration tests
- `src/ui/main_window.py` - GUI integration
