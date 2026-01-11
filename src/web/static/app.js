/**
 * Questionnaire Agent Web Interface - Main Application JavaScript
 */

// ============================================================================
// Global State
// ============================================================================

let sessionId = null;
let eventSource = null;
let isProcessing = false;
let processingCompleted = false;  // Flag to ignore stale events after completion
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
    // Check Azure status first
    await checkAzureStatus();

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
            applySessionConfig(data.config);
        } else {
            showError('Failed to create session');
        }
    } catch (e) {
        showError('Failed to connect to server');
        console.error('Session creation error:', e);
    }
}

async function checkAzureStatus() {
    try {
        const response = await fetch('/health');
        if (response.ok) {
            const data = await response.json();
            if (data.azure_auth === 'authenticated') {
                updateAzureStatus(true);
            } else {
                updateAzureStatus(false, data.message || 'Not authenticated');
            }
        } else {
            updateAzureStatus(false, 'Server error');
        }
    } catch (e) {
        console.error('Health check error:', e);
        updateAzureStatus(false, 'Connection error');
    }
}

function updateAzureStatus(connected, message = null) {
    const indicator = document.getElementById('azure-status-indicator');
    const label = document.getElementById('azure-status-text');

    if (indicator) {
        indicator.classList.remove('checking', 'connected', 'disconnected');
        indicator.classList.add(connected ? 'connected' : 'disconnected');
    }

    if (label) {
        if (connected) {
            label.textContent = 'Azure: Connected';
        } else {
            label.textContent = message ? `Azure: ${message}` : 'Azure: Disconnected';
        }
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
    if (!sessionId) {
        console.error('[SSE] Cannot connect: sessionId is null');
        return;
    }

    if (eventSource) {
        eventSource.close();
    }

    updateConnectionIndicator(false);

    console.log(`[SSE] Connecting to /api/sse/${sessionId}`);
    eventSource = new EventSource(`/api/sse/${sessionId}`);
    window.eventSource = eventSource;  // Expose for debugging

    eventSource.onopen = () => {
        console.log('[SSE] Connection opened');
        updateConnectionIndicator(true);
    };

    eventSource.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            console.log('[SSE] Received message:', message.type);
            handleSSEMessage(message);
        } catch (e) {
            console.error('[SSE] Message parse error:', e);
        }
    };

    eventSource.onerror = (error) => {
        console.error('[SSE] Connection error:', error, 'ReadyState:', eventSource.readyState);
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
        case 'AGENT_PROGRESS':
            handleAgentProgress(message.data);
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

    // Populate sheet selector (hidden dropdown, used internally)
    const sheetSelect = document.getElementById('sheet-select');
    sheetSelect.innerHTML = data.sheets.map(sheet =>
        `<option value="${sheet}"${sheet === data.suggested_columns.sheet_name ? ' selected' : ''}>${sheet}</option>`
    ).join('');

    // Generate sheet tabs at bottom of spreadsheet
    generateSheetTabs(data.sheets, data.suggested_columns.sheet_name);

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

        // Set documentation column if identified
        const docColSelect = document.getElementById('doc-col-select');
        if (docColSelect && data.suggested_columns.documentation_column) {
            docColSelect.value = data.suggested_columns.documentation_column;
        }

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

        // Set documentation column if suggested
        const docColSelect = document.getElementById('doc-col-select');
        if (docColSelect && data.suggested_columns.documentation_column) {
            docColSelect.value = data.suggested_columns.documentation_column;
        }

        // Initialize grid but don't start processing
        if (typeof initializeSpreadsheetGrid === 'function') {
            initializeSpreadsheetGrid();
        }

        updateStatusBar('Could not auto-detect columns. Please select manually.');
    }
}

// ============================================================================
// Sheet Tabs
// ============================================================================

function generateSheetTabs(sheets, activeSheet) {
    const tabsContainer = document.getElementById('sheet-tabs');
    if (!tabsContainer) return;

    tabsContainer.innerHTML = sheets.map(sheet => `
        <div class="sheet-tab${sheet === activeSheet ? ' active' : ''}"
             data-sheet="${sheet}"
             onclick="switchSheet('${sheet}')">
            <span class="sheet-tab-icon">📄</span>
            ${sheet}
        </div>
    `).join('');
}

function switchSheet(sheetName) {
    // Don't switch if processing is active
    if (isProcessing) {
        showError('Cannot switch sheets while processing is active');
        return;
    }

    // Update hidden sheet selector
    const sheetSelect = document.getElementById('sheet-select');
    if (sheetSelect) {
        sheetSelect.value = sheetName;
    }

    // Update tab active states
    const tabs = document.querySelectorAll('.sheet-tab');
    tabs.forEach(tab => {
        if (tab.dataset.sheet === sheetName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update column selectors for new sheet
    updateColumnSelectors(sheetName);

    // Re-initialize grid with new sheet data
    if (typeof initializeSpreadsheetGrid === 'function') {
        initializeSpreadsheetGrid();
    }

    // Clear any stored reasoning data for previous sheet
    Object.keys(rowReasoningData).forEach(key => delete rowReasoningData[key]);

    updateStatusBar(`Switched to sheet: ${sheetName}`);
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
    const docColSelect = document.getElementById('doc-col-select');

    // Preserve currently selected values
    const prevQuestion = questionColSelect.value;
    const prevContext = contextColSelect.value;
    const prevAnswer = answerColSelect.value;
    const prevDoc = docColSelect ? docColSelect.value : '';

    const columnOptions = columns.map(col => `<option value="${col}">${col}</option>`).join('');

    // Update options
    questionColSelect.innerHTML = columnOptions;
    contextColSelect.innerHTML = '<option value="">Use default context</option>' + columnOptions;
    answerColSelect.innerHTML = columnOptions;
    if (docColSelect) {
        docColSelect.innerHTML = '<option value="">No documentation column</option>' + columnOptions;
    }

    // Restore previous selections if those columns exist in new sheet
    if (columns.includes(prevQuestion)) {
        questionColSelect.value = prevQuestion;
    }
    if (prevContext && columns.includes(prevContext)) {
        contextColSelect.value = prevContext;
    } else if (!prevContext) {
        contextColSelect.value = '';  // Restore empty selection
    }
    if (columns.includes(prevAnswer)) {
        answerColSelect.value = prevAnswer;
    }
    if (docColSelect) {
        if (prevDoc && columns.includes(prevDoc)) {
            docColSelect.value = prevDoc;
        } else if (!prevDoc) {
            docColSelect.value = '';  // Restore empty selection
        }
    }
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
            processingCompleted = false;  // Reset flag for new job
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
            // Clear all working cells - only completed (green) rows should remain
            if (typeof clearAllWorkingCells === 'function') {
                clearAllWorkingCells();
            }
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
    // Ignore stale events after processing has completed
    if (processingCompleted) {
        console.log('Ignoring stale ROW_STARTED event after completion');
        return;
    }

    updateStatusBar(`Processing row ${data.row + 1}...`);

    // Highlight current row with "Working..." indicator
    if (typeof setRowProcessing === 'function') {
        setRowProcessing(data.row, true);
    }
}

function handleAgentProgress(data) {
    // Ignore stale agent progress events after processing has completed
    if (processingCompleted) {
        console.log('Ignoring stale AGENT_PROGRESS event after completion');
        return;
    }

    // Update the agent name for a row being processed
    if (typeof updateRowAgent === 'function') {
        updateRowAgent(data.row, data.agent_name);
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
        updateGridCell(data.row, data.answer, data.documentation || null);
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

async function handleProcessingComplete(data) {
    isProcessing = false;
    processingCompleted = true;  // Set flag to ignore stale events
    setProcessingUI(false, 0);

    // Refresh grid with completed data from server
    await refreshGridWithCompletedData();

    // Enable and highlight download button
    const downloadBtn = document.getElementById('download-btn');
    downloadBtn.disabled = false;
    downloadBtn.classList.add('highlight-download');

    // Create comprehensive completion message
    const sheetText = data.total_sheets > 1 ? `across ${data.total_sheets} sheets` : '';
    const statusMessage = `✅ Complete! Processed ${data.total_processed} questions ${sheetText} in ${data.duration_seconds.toFixed(1)}s. Ready to download.`;

    updateStatusBar(statusMessage);

    // Show longer-lasting success notification
    showSuccess(`✅ Processing complete! ${data.total_processed} questions answered ${sheetText}. Click Download Results to save your file.`, 10000);
}

async function refreshGridWithCompletedData() {
    // Fetch completed data from server for current sheet
    const sheetName = document.getElementById('sheet-select').value;
    console.log('[REFRESH] Starting grid refresh for sheet:', sheetName);

    if (!sheetName) {
        console.error('[REFRESH] No sheet name found');
        return;
    }

    try {
        const url = `/api/spreadsheet/data/${sessionId}/${encodeURIComponent(sheetName)}`;
        console.log('[REFRESH] Fetching data from:', url);

        const response = await fetch(url);
        if (!response.ok) {
            console.error('[REFRESH] Failed to fetch completed data, status:', response.status);
            return;
        }

        const sheetData = await response.json();
        console.log('[REFRESH] Received sheet data:', sheetData);

        // Update grid with all answers and documentation
        if (typeof updateGridWithCompletedData === 'function') {
            console.log('[REFRESH] Calling updateGridWithCompletedData');
            updateGridWithCompletedData(sheetData);
        } else {
            console.error('[REFRESH] updateGridWithCompletedData is not a function!');
            console.log('[REFRESH] typeof updateGridWithCompletedData:', typeof updateGridWithCompletedData);
        }
    } catch (error) {
        console.error('[REFRESH] Error refreshing grid with completed data:', error);
    }
}

function handleStatusChange(data) {
    if (data.status === 'CANCELLED') {
        isProcessing = false;
        setProcessingUI(false, 0);
        // Clear all working cells - only completed (green) rows should remain
        if (typeof clearAllWorkingCells === 'function') {
            clearAllWorkingCells();
        }
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

function showSuccess(message, duration = 3000) {
    const toast = document.getElementById('success-toast');
    const messageEl = document.getElementById('success-message');
    messageEl.textContent = message;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, duration);
}

function hideSuccessToast() {
    document.getElementById('success-toast').classList.add('hidden');
}
