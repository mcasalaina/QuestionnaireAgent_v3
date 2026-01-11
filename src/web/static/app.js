/**
 * Questionnaire Agent Web Interface - Main Application JavaScript
 */

// ============================================================================
// Global State
// ============================================================================

let sessionId = null;
let eventSource = null;
let isProcessing = false;
let currentJobId = null;
let currentMode = 'question'; // 'question' or 'spreadsheet'

// Store for spreadsheet row reasoning
const rowReasoningData = {};

// Auto-mapping confidence threshold
const AUTO_MAP_CONFIDENCE_THRESHOLD = 0.7;

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize session
    await initializeSession();

    // Set up event listeners
    setupEventListeners();

    // Connect to SSE
    connectSSE();

    // Set initial mode
    switchMode('question');
});

async function initializeSession() {
    // Check for existing session in localStorage
    sessionId = localStorage.getItem('sessionId');

    if (sessionId) {
        // Verify session still exists
        try {
            const response = await fetch(`/api/session/${sessionId}`);
            if (response.ok) {
                const data = await response.json();
                updateSessionDisplay(sessionId);
                applySessionConfig(data.config);

                // Check for active processing job
                if (data.processing_status === 'RUNNING') {
                    await checkProcessingStatus();
                }
                return;
            }
        } catch (e) {
            console.warn('Existing session invalid, creating new one');
        }
    }

    // Create new session
    try {
        const response = await fetch('/api/session/create', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            sessionId = data.session_id;
            localStorage.setItem('sessionId', sessionId);
            updateSessionDisplay(sessionId);
            applySessionConfig(data.config);
        } else {
            showError('Failed to create session');
        }
    } catch (e) {
        showError('Failed to connect to server');
        console.error('Session creation error:', e);
    }
}

function updateSessionDisplay(id) {
    const sessionIdEl = document.getElementById('session-id');
    if (sessionIdEl) {
        sessionIdEl.textContent = id.substring(0, 8) + '...';
        sessionIdEl.title = id;
    }
}

function applySessionConfig(config) {
    document.getElementById('context-input').value = config.context || 'Microsoft Azure AI';
    document.getElementById('char-limit-input').value = config.char_limit || 2000;
}

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Ask button
    document.getElementById('ask-btn').addEventListener('click', submitQuestion);

    // Enter key for question submission (Ctrl+Enter)
    document.getElementById('question-input').addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            submitQuestion();
        }
    });

    // File upload
    document.getElementById('file-upload').addEventListener('change', handleFileUpload);

    // Spreadsheet processing
    document.getElementById('start-processing-btn').addEventListener('click', startProcessing);
    document.getElementById('stop-processing-btn').addEventListener('click', stopProcessing);
    document.getElementById('download-btn').addEventListener('click', downloadResults);

    // Sheet selection change
    document.getElementById('sheet-select').addEventListener('change', handleSheetChange);
}

// ============================================================================
// Mode Switching
// ============================================================================

function switchMode(mode) {
    currentMode = mode;

    const questionMode = document.getElementById('question-mode');
    const spreadsheetMode = document.getElementById('spreadsheet-mode');
    const spreadsheetControls = document.getElementById('spreadsheet-controls');

    if (mode === 'question') {
        questionMode.classList.remove('hidden');
        spreadsheetMode.classList.add('hidden');
        spreadsheetControls.classList.add('hidden');
    } else {
        questionMode.classList.add('hidden');
        spreadsheetMode.classList.remove('hidden');
        spreadsheetControls.classList.remove('hidden');
    }
}

// ============================================================================
// Status Bar
// ============================================================================

function updateStatusBar(message) {
    const statusText = document.getElementById('status-text');
    if (statusText) {
        statusText.textContent = message;
    }
}

function updateConnectionIndicator(connected) {
    const indicator = document.getElementById('connection-indicator');
    if (indicator) {
        indicator.classList.remove('connected', 'disconnected', 'connecting');
        if (connected) {
            indicator.classList.add('connected');
        } else {
            indicator.classList.add('disconnected');
        }
    }
}

// ============================================================================
// Question Processing
// ============================================================================

async function submitQuestion() {
    const questionInput = document.getElementById('question-input');
    const question = questionInput.value.trim();

    if (!question) {
        showError('Please enter a question');
        return;
    }

    if (question.length < 5) {
        showError('Question must be at least 5 characters');
        return;
    }

    const context = document.getElementById('context-input').value;
    const charLimit = parseInt(document.getElementById('char-limit-input').value);

    // Show loading state
    setQuestionLoading(true);
    updateStatusBar('Working...');

    // Hide empty state
    document.getElementById('empty-state').classList.add('hidden');

    try {
        const response = await fetch('/api/question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                question,
                context,
                char_limit: charLimit
            })
        });

        if (response.ok) {
            const data = await response.json();
            displayAnswer(data);
            updateStatusBar('Ready');
        } else {
            const error = await response.json();
            showError(error.detail || 'Failed to process question');
            updateStatusBar('Error');
        }
    } catch (e) {
        showError('Failed to process question');
        console.error('Question processing error:', e);
        updateStatusBar('Error');
    } finally {
        setQuestionLoading(false);
    }
}

function setQuestionLoading(loading) {
    const askBtn = document.getElementById('ask-btn');
    const loadingEl = document.getElementById('question-loading');
    const questionInput = document.getElementById('question-input');

    askBtn.disabled = loading;
    questionInput.disabled = loading;
    loadingEl.classList.toggle('hidden', !loading);
}

function displayAnswer(data) {
    const answerSection = document.getElementById('answer-section');
    const answerContent = document.getElementById('answer-content');
    const answerTime = document.getElementById('answer-time');
    const answerLinks = document.getElementById('answer-links');
    const reasoningContent = document.getElementById('reasoning-content');

    // Format answer with clickable links
    answerContent.innerHTML = formatAnswerWithLinks(data.answer);

    // Meta info
    answerTime.textContent = `Processing time: ${data.processing_time_seconds.toFixed(1)}s`;
    answerLinks.textContent = `Links checked: ${data.links_checked}`;

    // Reasoning
    reasoningContent.textContent = data.reasoning;

    // Show section
    answerSection.classList.remove('hidden');

    // Scroll into view
    answerSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function formatAnswerWithLinks(text) {
    // Convert URLs to clickable links
    const urlRegex = /(https?:\/\/[^\s<]+)/g;
    return text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
}

// ============================================================================
// Server-Sent Events
// ============================================================================

function connectSSE() {
    if (!sessionId) return;

    if (eventSource) {
        eventSource.close();
    }

    updateConnectionIndicator(false);

    eventSource = new EventSource(`/api/sse/${sessionId}`);

    eventSource.onopen = () => {
        updateConnectionIndicator(true);
    };

    eventSource.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleSSEMessage(message);
        } catch (e) {
            console.error('SSE message parse error:', e);
        }
    };

    eventSource.onerror = () => {
        updateConnectionIndicator(false);
        updateStatusBar('Connection lost. Reconnecting...');
        // Attempt reconnect after delay
        setTimeout(connectSSE, 5000);
    };
}

function handleSSEMessage(message) {
    switch (message.type) {
        case 'PROGRESS':
            handleProgressUpdate(message.data);
            break;
        case 'ANSWER':
            handleAnswerUpdate(message.data);
            break;
        case 'ERROR':
            handleErrorMessage(message.data);
            break;
        case 'COMPLETE':
            handleProcessingComplete(message.data);
            break;
        case 'STATUS':
            handleStatusChange(message.data);
            break;
        case 'ROW_STARTED':
            handleRowStarted(message.data);
            break;
        default:
            console.log('Unknown SSE message type:', message.type);
    }
}

// ============================================================================
// File Upload
// ============================================================================

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Update file name display
    document.getElementById('file-name').textContent = file.name;

    updateStatusBar('Uploading file...');

    // Create form data
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('file', file);

    try {
        const response = await fetch('/api/spreadsheet/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            handleUploadSuccess(data);
        } else {
            const error = await response.json();
            showError(error.detail || 'Failed to upload file');
            updateStatusBar('Error: ' + (error.detail || 'Upload failed'));
        }
    } catch (e) {
        showError('Failed to upload file');
        console.error('File upload error:', e);
        updateStatusBar('Error: Upload failed');
    }
}

function handleUploadSuccess(data) {
    // Store column data
    window.uploadedData = data;

    // Switch to spreadsheet mode
    switchMode('spreadsheet');

    // Populate sheet selector
    const sheetSelect = document.getElementById('sheet-select');
    sheetSelect.innerHTML = data.sheets.map(sheet =>
        `<option value="${sheet}"${sheet === data.suggested_columns.sheet_name ? ' selected' : ''}>${sheet}</option>`
    ).join('');

    // Populate column selectors for the selected sheet
    updateColumnSelectors(data.suggested_columns.sheet_name);

    // Check if auto-mapping was successful
    const autoMapSuccess = data.suggested_columns.confidence >= AUTO_MAP_CONFIDENCE_THRESHOLD &&
                          data.suggested_columns.question_column &&
                          data.suggested_columns.answer_column;

    if (autoMapSuccess) {
        // Apply auto-mapped columns
        document.getElementById('question-col-select').value = data.suggested_columns.question_column;
        document.getElementById('answer-col-select').value = data.suggested_columns.answer_column;

        // Hide column mapping UI
        document.getElementById('column-mapping').classList.add('hidden');

        // Initialize and show grid
        if (typeof initializeSpreadsheetGrid === 'function') {
            initializeSpreadsheetGrid();
        }

        updateStatusBar(`Auto-mapped columns. Processing row 1 of ${data.row_count}...`);

        // Auto-start processing
        startProcessing();
    } else {
        // Show column mapping UI for manual selection
        document.getElementById('column-mapping').classList.remove('hidden');

        // Apply suggestions if available
        if (data.suggested_columns.question_column) {
            document.getElementById('question-col-select').value = data.suggested_columns.question_column;
        }
        if (data.suggested_columns.answer_column) {
            document.getElementById('answer-col-select').value = data.suggested_columns.answer_column;
        }

        // Initialize grid but don't start processing
        if (typeof initializeSpreadsheetGrid === 'function') {
            initializeSpreadsheetGrid();
        }

        updateStatusBar('Could not auto-detect columns. Please select manually.');
    }
}

function handleSheetChange() {
    const sheetName = document.getElementById('sheet-select').value;
    updateColumnSelectors(sheetName);

    // Re-initialize grid for new sheet
    if (typeof initializeSpreadsheetGrid === 'function') {
        initializeSpreadsheetGrid();
    }
}

function updateColumnSelectors(sheetName) {
    const data = window.uploadedData;
    if (!data || !data.columns[sheetName]) return;

    const columns = data.columns[sheetName];

    const questionColSelect = document.getElementById('question-col-select');
    const contextColSelect = document.getElementById('context-col-select');
    const answerColSelect = document.getElementById('answer-col-select');

    const columnOptions = columns.map(col => `<option value="${col}">${col}</option>`).join('');

    questionColSelect.innerHTML = columnOptions;
    contextColSelect.innerHTML = '<option value="">Use default context</option>' + columnOptions;
    answerColSelect.innerHTML = columnOptions;
}

// ============================================================================
// Spreadsheet Processing
// ============================================================================

async function startProcessing() {
    const sheetName = document.getElementById('sheet-select').value;
    const questionColumn = document.getElementById('question-col-select').value;
    const contextColumn = document.getElementById('context-col-select').value || null;
    const answerColumn = document.getElementById('answer-col-select').value;

    if (!questionColumn || !answerColumn) {
        showError('Please select question and answer columns');
        return;
    }

    // Hide column mapping if visible
    document.getElementById('column-mapping').classList.add('hidden');

    try {
        const response = await fetch('/api/spreadsheet/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                sheet_name: sheetName,
                question_column: questionColumn,
                context_column: contextColumn,
                answer_column: answerColumn
            })
        });

        if (response.ok) {
            const data = await response.json();
            currentJobId = data.job_id;
            isProcessing = true;
            setProcessingUI(true, data.total_rows);
            updateStatusBar(`Processing row 1 of ${data.total_rows}...`);
        } else {
            const error = await response.json();
            showError(error.detail || 'Failed to start processing');
            updateStatusBar('Error: ' + (error.detail || 'Failed to start'));
        }
    } catch (e) {
        showError('Failed to start processing');
        console.error('Start processing error:', e);
        updateStatusBar('Error: Failed to start processing');
    }
}

async function stopProcessing() {
    try {
        const response = await fetch('/api/spreadsheet/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });

        if (response.ok) {
            const data = await response.json();
            isProcessing = false;
            setProcessingUI(false, 0);
            updateStatusBar(`Stopped at row ${data.processed_rows} of ${data.total_rows}`);
            showSuccess(`Stopped processing. ${data.processed_rows} rows completed.`);
        } else {
            const error = await response.json();
            showError(error.detail || 'Failed to stop processing');
        }
    } catch (e) {
        showError('Failed to stop processing');
        console.error('Stop processing error:', e);
    }
}

function setProcessingUI(processing, totalRows) {
    document.getElementById('start-processing-btn').disabled = processing;
    document.getElementById('stop-processing-btn').disabled = !processing;
    document.getElementById('download-btn').disabled = processing;
    document.getElementById('file-upload').disabled = processing;
    document.getElementById('import-btn').disabled = processing;
}

function handleProgressUpdate(data) {
    updateStatusBar(`Processing row ${data.row} of ${data.total}...`);

    // Highlight current row in grid
    if (typeof highlightProcessingRow === 'function') {
        highlightProcessingRow(data.row - 1);
    }
}

function handleRowStarted(data) {
    updateStatusBar(`Processing row ${data.row + 1}...`);

    // Highlight current row with "Working..." indicator
    if (typeof setRowProcessing === 'function') {
        setRowProcessing(data.row, true);
    }
}

function handleAnswerUpdate(data) {
    // Store reasoning for modal
    rowReasoningData[data.row] = {
        question: data.question,
        answer: data.answer,
        reasoning: data.reasoning
    };

    // Update grid if available
    if (typeof updateGridCell === 'function') {
        updateGridCell(data.row, data.answer);
    }

    // Clear processing indicator for this row
    if (typeof setRowProcessing === 'function') {
        setRowProcessing(data.row, false);
    }
}

function handleErrorMessage(data) {
    if (data.row !== undefined) {
        updateStatusBar(`Error at row ${data.row + 1}: ${data.message}`);
        // Mark row as error in grid
        if (typeof setRowError === 'function') {
            setRowError(data.row, data.message);
        }
    } else {
        updateStatusBar(`Error: ${data.message}`);
        showError(data.message);
    }
}

function handleProcessingComplete(data) {
    isProcessing = false;
    setProcessingUI(false, 0);
    document.getElementById('download-btn').disabled = false;
    updateStatusBar(`Complete. Processed ${data.total_processed} rows.`);
    showSuccess(`Processing complete! ${data.total_processed} rows processed in ${data.duration_seconds.toFixed(1)}s`);
}

function handleStatusChange(data) {
    if (data.status === 'CANCELLED') {
        isProcessing = false;
        setProcessingUI(false, 0);
    }
}

async function checkProcessingStatus() {
    try {
        const response = await fetch(`/api/spreadsheet/status/${sessionId}`);
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'RUNNING') {
                isProcessing = true;
                currentJobId = data.job_id;
                setProcessingUI(true, data.total_rows);
                updateStatusBar(`Processing row ${data.processed_rows + 1} of ${data.total_rows}...`);

                // Switch to spreadsheet mode
                switchMode('spreadsheet');
            }
        }
    } catch (e) {
        console.error('Failed to check processing status:', e);
    }
}

async function downloadResults() {
    window.location.href = `/api/spreadsheet/download/${sessionId}`;
}

// ============================================================================
// Reasoning Modal
// ============================================================================

function showReasoningModal(rowIndex) {
    const data = rowReasoningData[rowIndex];
    if (!data) return;

    document.getElementById('modal-title').textContent = `Row ${rowIndex + 1} Details`;
    document.getElementById('modal-question').textContent = data.question;
    document.getElementById('modal-answer').textContent = data.answer;
    document.getElementById('modal-reasoning').textContent = data.reasoning;

    document.getElementById('reasoning-modal').classList.remove('hidden');
}

function closeReasoningModal() {
    document.getElementById('reasoning-modal').classList.add('hidden');
}

// ============================================================================
// Toast Notifications
// ============================================================================

function showError(message) {
    const toast = document.getElementById('error-toast');
    const messageEl = document.getElementById('error-message');
    messageEl.textContent = message;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 5000);
}

function hideToast() {
    document.getElementById('error-toast').classList.add('hidden');
}

function showSuccess(message) {
    const toast = document.getElementById('success-toast');
    const messageEl = document.getElementById('success-message');
    messageEl.textContent = message;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function hideSuccessToast() {
    document.getElementById('success-toast').classList.add('hidden');
}
