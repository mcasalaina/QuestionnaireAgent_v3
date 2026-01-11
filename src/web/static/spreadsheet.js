/**
 * Questionnaire Agent Web Interface - Spreadsheet Component
 * ag-Grid integration for Excel file display and real-time updates
 */

// ============================================================================
// Global Grid State
// ============================================================================

let gridApi = null;
let gridData = [];
let currentProcessingRow = null;
let answerColumnField = null;

// ============================================================================
// Grid Initialization
// ============================================================================

function initializeSpreadsheetGrid() {
    const gridDiv = document.getElementById('spreadsheet-grid');
    if (!gridDiv) return;

    const uploadedData = window.uploadedData;
    if (!uploadedData) return;

    // Get selected sheet
    const sheetName = document.getElementById('sheet-select').value;
    const columns = uploadedData.columns[sheetName] || [];

    // Determine the answer column field for highlighting
    const answerColSelect = document.getElementById('answer-col-select');
    answerColumnField = answerColSelect ? answerColSelect.value : null;

    // Create column definitions
    const columnDefs = [
        {
            headerName: '#',
            field: 'rowIndex',
            width: 60,
            pinned: 'left',
            sortable: false,
            filter: false,
            cellClass: 'row-number-cell'
        },
        ...columns.map(col => ({
            headerName: col,
            field: col,
            sortable: true,
            filter: true,
            resizable: true,
            editable: false,
            minWidth: 150,
            flex: 1,
            cellRenderer: (params) => {
                // Check if this is the answer column and row is processing
                if (col === answerColumnField && params.data._processing) {
                    const agentName = params.data._agentName || 'Working';
                    // Format agent name for display (e.g., "question_answerer" -> "QuestionAnswerer")
                    const displayName = formatAgentName(agentName);
                    return `<span class="working-indicator"><span class="mini-spinner"></span>${displayName}...</span>`;
                }
                // Make answer cells clickable to show reasoning
                if (col === answerColumnField && params.value) {
                    return `<span class="answer-cell" onclick="showReasoningModal(${params.data.rowIndex})">${escapeHtml(params.value)}</span>`;
                }
                return escapeHtml(params.value || '');
            },
            cellClass: (params) => {
                if (col === answerColumnField) {
                    if (params.data._error) {
                        return 'answer-error';
                    }
                    return params.value ? 'answer-filled' : 'answer-empty';
                }
                return '';
            }
        }))
    ];

    // Get actual data from the upload response
    const sheetData = uploadedData.data && uploadedData.data[sheetName];
    if (sheetData && sheetData.length > 0) {
        gridData = sheetData.map((row, idx) => ({
            ...row,
            rowIndex: idx,
            _processing: false,
            _error: null,
            _agentName: null
        }));
    } else {
        // Fallback: create placeholder rows if no data available
        gridData = [];
        for (let i = 0; i < (uploadedData.row_count || 10); i++) {
            const row = { rowIndex: i, _processing: false, _error: null, _agentName: null };
            columns.forEach(col => {
                row[col] = '';
            });
            gridData.push(row);
        }
    }

    // Grid options
    const gridOptions = {
        columnDefs: columnDefs,
        rowData: gridData,
        defaultColDef: {
            sortable: true,
            filter: true,
            resizable: true,
            minWidth: 100
        },
        // Virtual scrolling for large datasets
        rowBuffer: 20,
        // Animation
        animateRows: true,
        // Row selection
        rowSelection: 'single',
        // Header
        headerHeight: 40,
        rowHeight: 40,
        // Suppress horizontal scroll
        suppressHorizontalScroll: false,
        // Row class rules for highlighting
        getRowClass: (params) => {
            if (params.data._processing) {
                return 'row-processing';
            }
            if (params.data._error) {
                return 'row-error';
            }
            return '';
        },
        // Callbacks
        onGridReady: (params) => {
            gridApi = params.api;
            // Auto-size columns to fit content
            params.api.sizeColumnsToFit();
        },
        onFirstDataRendered: (params) => {
            params.api.sizeColumnsToFit();
        },
        onCellClicked: (params) => {
            // Show reasoning modal for answer cells
            if (params.column.colDef.field === answerColumnField && params.value) {
                showReasoningModal(params.data.rowIndex);
            }
        }
    };

    // Clear existing grid
    gridDiv.innerHTML = '';

    // Add ag-Grid theme class
    gridDiv.classList.add('ag-theme-alpine');

    // Create grid using the modern API
    gridApi = agGrid.createGrid(gridDiv, gridOptions);
}

// ============================================================================
// Row State Management
// ============================================================================

function setRowProcessing(rowIndex, processing) {
    if (!gridApi || rowIndex >= gridData.length) return;

    // Update data
    gridData[rowIndex]._processing = processing;
    gridData[rowIndex]._error = null;
    // Clear agent name when not processing
    if (!processing) {
        gridData[rowIndex]._agentName = null;
    }

    // Track current processing row
    currentProcessingRow = processing ? rowIndex : null;

    // Refresh the row
    const rowNode = gridApi.getRowNode(rowIndex.toString());
    if (rowNode) {
        rowNode.setData(gridData[rowIndex]);
        gridApi.refreshCells({ rowNodes: [rowNode], force: true });
    }

    // Auto-scroll to keep processing row visible
    if (processing) {
        gridApi.ensureIndexVisible(rowIndex, 'middle');
    }
}

function setRowError(rowIndex, errorMessage) {
    if (!gridApi || rowIndex >= gridData.length) return;

    // Update data
    gridData[rowIndex]._processing = false;
    gridData[rowIndex]._error = errorMessage;

    // Update the answer cell with error message
    if (answerColumnField) {
        gridData[rowIndex][answerColumnField] = `Error: ${errorMessage}`;
    }

    // Refresh the row
    const rowNode = gridApi.getRowNode(rowIndex.toString());
    if (rowNode) {
        rowNode.setData(gridData[rowIndex]);
        gridApi.refreshCells({ rowNodes: [rowNode], force: true });
    }
}

function highlightProcessingRow(rowIndex) {
    // Clear previous processing row
    if (currentProcessingRow !== null && currentProcessingRow !== rowIndex) {
        setRowProcessing(currentProcessingRow, false);
    }
    // Set new processing row
    setRowProcessing(rowIndex, true);
}

function updateRowAgent(rowIndex, agentName) {
    if (!gridApi || rowIndex >= gridData.length) return;

    // Only update if row is currently processing
    if (!gridData[rowIndex]._processing) return;

    // Update agent name
    gridData[rowIndex]._agentName = agentName;

    // Refresh the row
    const rowNode = gridApi.getRowNode(rowIndex.toString());
    if (rowNode) {
        rowNode.setData(gridData[rowIndex]);
        gridApi.refreshCells({ rowNodes: [rowNode], force: true });
    }
}

function formatAgentName(agentName) {
    if (!agentName) return 'Working';

    // Map internal agent names to human-readable display names
    const agentDisplayNames = {
        'question_answerer': 'Answering Question',
        'QuestionAnswererExecutor': 'Answering Question',
        'answer_checker': 'Checking Answer',
        'AnswerCheckerExecutor': 'Checking Answer',
        'link_checker': 'Checking Links',
        'LinkCheckerExecutor': 'Checking Links',
        'workflow': 'Processing',
        'batch': 'Processing'
    };

    // Check for exact match first
    if (agentDisplayNames[agentName]) {
        return agentDisplayNames[agentName];
    }

    // Fallback: return as-is
    return 'Working';
}

// ============================================================================
// Grid Updates
// ============================================================================

function updateGridCell(rowIndex, answer) {
    if (!gridApi || rowIndex >= gridData.length) return;

    // Clear processing state
    gridData[rowIndex]._processing = false;
    gridData[rowIndex]._error = null;
    gridData[rowIndex]._agentName = null;

    // Update the answer in data
    if (answerColumnField) {
        gridData[rowIndex][answerColumnField] = answer;
    }

    // Find the row node
    const rowNode = gridApi.getRowNode(rowIndex.toString());
    if (!rowNode) return;

    // Update the data
    rowNode.setData(gridData[rowIndex]);

    // Refresh the cell
    gridApi.refreshCells({
        rowNodes: [rowNode],
        force: true
    });

    // Flash the updated cell
    if (answerColumnField) {
        gridApi.flashCells({
            rowNodes: [rowNode],
            columns: [answerColumnField]
        });
    }
}

function setGridRowData(data) {
    if (!gridApi) return;

    gridData = data;
    gridApi.setRowData(data);
}

function getGridRowData() {
    if (!gridApi) return [];

    const rowData = [];
    gridApi.forEachNode((node) => {
        rowData.push(node.data);
    });
    return rowData;
}

// ============================================================================
// Grid Export
// ============================================================================

function exportGridToClipboard() {
    // Community edition: manually copy grid data to clipboard
    if (!gridApi) return;

    const rowData = getGridRowData();
    if (!rowData || rowData.length === 0) return;

    // Convert to TSV format for clipboard
    const columns = Object.keys(rowData[0]).filter(k => !k.startsWith('_') && k !== 'rowIndex');
    const header = columns.join('\t');
    const rows = rowData.map(row => columns.map(col => row[col] || '').join('\t'));
    const tsv = [header, ...rows].join('\n');

    navigator.clipboard.writeText(tsv).catch(err => {
        console.error('Failed to copy to clipboard:', err);
    });
}

// ============================================================================
// Grid Filtering
// ============================================================================

function filterGrid(searchText) {
    if (!gridApi) return;

    gridApi.setQuickFilter(searchText);
}

function clearGridFilters() {
    if (!gridApi) return;

    gridApi.setFilterModel(null);
    gridApi.setQuickFilter('');
}

// ============================================================================
// Grid Sorting
// ============================================================================

function sortGridByColumn(columnField, direction = 'asc') {
    if (!gridApi) return;

    const sortModel = [
        { colId: columnField, sort: direction }
    ];
    gridApi.setSortModel(sortModel);
}

function clearGridSort() {
    if (!gridApi) return;

    gridApi.setSortModel([]);
}

// ============================================================================
// Utility Functions
// ============================================================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// CSS for Grid Cells
// ============================================================================

// Add custom styles dynamically
const gridStyles = document.createElement('style');
gridStyles.textContent = `
    .ag-theme-alpine .row-number-cell {
        color: var(--color-text-secondary);
        font-size: var(--font-size-sm);
        text-align: center;
    }

    .ag-theme-alpine .answer-cell {
        cursor: pointer;
        color: var(--color-primary);
    }

    .ag-theme-alpine .answer-cell:hover {
        text-decoration: underline;
    }

    .ag-theme-alpine .answer-filled {
        background-color: rgba(16, 124, 16, 0.1);
    }

    .ag-theme-alpine .answer-empty {
        background-color: rgba(0, 0, 0, 0.02);
    }

    .ag-theme-alpine .answer-error {
        background-color: rgba(209, 52, 56, 0.1);
        color: var(--color-danger);
    }

    .ag-theme-alpine .ag-cell-flash {
        animation: cell-flash 0.5s ease-out;
    }

    @keyframes cell-flash {
        0% { background-color: rgba(0, 120, 212, 0.3); }
        100% { background-color: transparent; }
    }

    .ag-theme-alpine .ag-header-cell {
        font-weight: 600;
    }

    .ag-theme-alpine .ag-row-hover {
        background-color: var(--color-surface-hover);
    }

    .ag-theme-alpine .ag-row-selected {
        background-color: rgba(0, 120, 212, 0.1);
    }

    /* Processing row highlight */
    .ag-theme-alpine .row-processing {
        background-color: #FFECEC !important;
    }

    .ag-theme-alpine .row-processing:hover {
        background-color: #FFE0E0 !important;
    }

    /* Error row highlight */
    .ag-theme-alpine .row-error {
        background-color: #FDE7E9 !important;
    }

    /* Working indicator */
    .working-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #D13438;
        font-style: italic;
    }

    .mini-spinner {
        width: 12px;
        height: 12px;
        border: 2px solid #EDEBE9;
        border-top-color: #D13438;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(gridStyles);

// ============================================================================
// Window Resize Handler
// ============================================================================

window.addEventListener('resize', () => {
    if (gridApi) {
        setTimeout(() => {
            gridApi.sizeColumnsToFit();
        }, 100);
    }
});

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Ctrl+C - Copy selected cells (manually in community edition)
    if (e.ctrlKey && e.key === 'c' && gridApi) {
        exportGridToClipboard();
    }

    // Ctrl+F - Focus filter
    if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        // Could add a filter input focus here
    }

    // Escape - Clear selection
    if (e.key === 'Escape' && gridApi) {
        gridApi.deselectAll();
    }
});
