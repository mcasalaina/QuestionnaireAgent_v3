# Feature Specification: Rewrite Questionnaire Agent using Microsoft Agent Framework

**Feature Branch**: `001-rewrite-questionnaire-agent`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Rewrite Questionnaire Agent using Microsoft Agent Framework with separate UI and Excel handling modules"

## Clarifications

### Session 2025-10-09

- Q: When Excel files cannot be opened or lack identifiable columns, what should the user experience be? → A: Show detailed error dialog with specific failure reason and suggested fixes
- Q: What should happen when Azure AI Foundry services become unavailable during processing? → A: Fail immediately with clear error message and stop all processing. Verify Azure credentials immediately at app startup and attempt login if not authenticated.
- Q: When all retry attempts are exhausted without generating an acceptable answer, what should the system do? → A: Show "Unable to generate acceptable answer" error and return to input screen. Exception: if Answer Checker approved but only Link Checker failed, emit the answer with blank links.
- Q: What occurs when network connectivity fails during web search operations? → A: Fail immediately and display network connectivity error to user.
- Q: For the separate UI and Excel handling modules, how should they communicate with the main application logic? → A: Direct method calls with shared data structures and synchronous interfaces.

## User Scenarios & Testing

### User Story 1 - Single Question Processing via GUI (Priority: P1)

A user launches the GUI application, enters a question about Microsoft Azure AI services in the question box, sets appropriate parameters (context, character limit), and receives a comprehensive answer with fact-checking and link validation. The application displays real-time reasoning progress and separates the final answer from documentation links.

**Why this priority**: This is the core MVP functionality that delivers immediate value to users who need reliable, fact-checked answers to specific questions. It represents the primary use case and validates the entire multi-agent architecture.

**Independent Test**: Can be fully tested by launching the application, entering any question, clicking "Ask!", and verifying a validated answer appears with documentation links separated and reasoning visible.

**Acceptance Scenarios**:

1.  **Given** the application is launched and displays the default GUI, **When** user enters "Does Azure AI support video generation?" and clicks "Ask!", **Then** the application shows reasoning progress, generates a validated answer under 2000 characters, and displays relevant documentation links separately
2.  **Given** an answer exceeds the character limit, **When** the system validates the response, **Then** the Question Answerer agent retries with stricter prompts up to maximum retry attempts
3.  **Given** the Answer Checker rejects an answer for inaccuracy, **When** the validation fails, **Then** the system logs the rejection reason and retries the question generation process

---

### User Story 2 - Excel Batch Processing (Priority: P2)

A user imports an Excel file containing multiple questions via the "Import From Excel" button, and the system automatically identifies question columns, processes each question through the multi-agent validation workflow, and exports a new Excel file with answers and documentation links populated in appropriate columns.

**Why this priority**: This enables high-volume processing for organizations that need to answer many questions systematically, providing significant productivity gains for enterprise users.

**Independent Test**: Can be fully tested by preparing an Excel file with questions, clicking "Import From Excel", selecting the file, and verifying a processed output file is generated with answers and links in appropriate columns.

**Acceptance Scenarios**:

1.  **Given** an Excel file with questions in various columns, **When** user selects "Import From Excel" and chooses the file, **Then** the system automatically identifies question columns using AI analysis and processes each question
2.  **Given** processing is in progress, **When** the system works through questions, **Then** real-time progress is shown in the status bar including current question number and processing agent
3.  **Given** all questions are processed, **When** processing completes, **Then** user is prompted to save the output file with a new name and location

---

### User Story 3 - Multi-Agent Workflow Orchestration (Priority: P3)

The system orchestrates three specialized agents (Question Answerer, Answer Checker, Link Checker) using Microsoft Agent Framework, where each agent has distinct responsibilities and the workflow continues until all agents approve the response or maximum retries are reached.

**Why this priority**: This represents the sophisticated AI architecture that differentiates this solution from simple chat applications, ensuring answer quality through multi-stage validation.

**Independent Test**: Can be tested by monitoring the reasoning output during any question processing to verify three distinct agents are involved and that validation failures trigger retries.

**Acceptance Scenarios**:

1.  **Given** a question is submitted, **When** the Question Answerer generates an initial response, **Then** the Answer Checker validates factual accuracy and completeness using web search
2.  **Given** the Answer Checker approves an answer, **When** the response contains URLs, **Then** the Link Checker verifies each URL is reachable and relevant using HTTP requests and content analysis
3.  **Given** either checker rejects a response, **When** validation fails, **Then** the workflow logs rejection reasons and retries up to the configured maximum attempts

### Edge Cases

- When all retry attempts are exhausted, show "Unable to generate acceptable answer" error and return to input screen (Exception: if Answer Checker approved but only Link Checker failed, emit answer with blank links)
- Excel files that cannot be opened display detailed error dialog with specific failure reason and suggested fixes
- Network connectivity failures during web search operations cause immediate failure with connectivity error displayed to user
- Azure AI Foundry service unavailability causes immediate failure with clear error message and stops all processing
- Excel files with complex formatting or merged cells immediately display error with specific formatting issues identified

## Requirements

### Functional Requirements

*   **FR-001**: System MUST use Microsoft Agent Framework exclusively for multi-agent orchestration and workflow management
*   **FR-002**: System MUST authenticate to Azure AI Foundry using DefaultAzureCredential (managed identity) for production deployments
*   **FR-003**: System MUST verify Azure AI Foundry connectivity and credentials immediately at application startup, attempting automatic login if authentication fails
*   **FR-004**: System MUST separate the GUI interface code from the main application logic into distinct modules
*   **FR-004**: System MUST isolate Excel file handling operations into a dedicated module for maintainability
*   **FR-005**: System MUST implement three specialized agents: Question Answerer with Bing Search grounding, Answer Checker with web validation, and Link Checker with HTTP and content verification
*   **FR-006**: System MUST display the window title as "Questionnaire Answerer (Microsoft Agent Framework)" to distinguish from the original version
*   **FR-007**: System MUST maintain the same GUI layout and functionality as the original question\_answerer\_old.py implementation
*   **FR-008**: System MUST use FoundryAgentSession pattern for proper Azure AI resource management and cleanup
*   **FR-009**: System MUST provide real-time reasoning display showing current agent activity and workflow progress
*   **FR-010**: System MUST separate answer content from documentation links, displaying each in appropriate UI sections
*   **FR-011**: System MUST retry failed responses up to a configurable maximum with progressively stricter prompts for character limit compliance
*   **FR-012**: System MUST automatically identify question and answer columns in Excel files using AI analysis
*   **FR-013**: System MUST preserve original Excel file formatting when generating output files
*   **FR-014**: System MUST enable mock mode for testing without requiring Azure credentials or consuming cloud resources
- **FR-016**: System MUST fail immediately with clear error messages when Azure AI Foundry services become unavailable during processing
- **FR-017**: System MUST show "Unable to generate acceptable answer" error when all retries are exhausted, with exception for Answer Checker approved responses where only Link Checker failed (emit answer with blank links)
- **FR-018**: System MUST display detailed error dialogs for Excel file failures, including specific failure reasons and suggested fixes for unsupported formats, unidentifiable columns, or complex formatting
- **FR-019**: System MUST fail immediately and display network connectivity error when web search operations cannot connect due to network issues
- **FR-020**: System MUST use direct method calls with shared data structures and synchronous interfaces for communication between UI module, Excel handling module, and main application logic

### Key Entities

*   **Agent**: Represents a specialized AI component (Question Answerer, Answer Checker, Link Checker) with specific instructions and tool access
*   **Workflow**: Orchestrates the multi-agent interaction pattern using Microsoft Agent Framework's workflow capabilities
*   **Question**: User input requiring research and validation, with associated context and character limits
*   **Answer**: Generated response that has passed multi-agent validation, separated from supporting documentation
*   **Documentation**: Collection of verified URLs and sources supporting the answer content
*   **ExcelProcessor**: Handles loading, column identification, processing, and saving of Excel workbooks
*   **UIManager**: Manages the tkinter GUI interface, user interactions, and real-time status updates

## Success Criteria

### Measurable Outcomes

*   **SC-001**: Users can successfully process single questions from GUI to validated answer in under 2 minutes for typical Azure AI queries
*   **SC-002**: System successfully processes Excel files with up to 50 questions without failure or timeout errors
*   **SC-003**: Multi-agent validation rejects and retries inaccurate answers at least 90% of the time when presented with deliberately incorrect information
*   **SC-004**: Application maintains responsive GUI during processing with real-time progress updates visible within 1 second of agent status changes
*   **SC-005**: Excel column identification accuracy exceeds 95% for standard spreadsheet formats with clear question/answer column headers
*   **SC-006**: Link validation correctly identifies broken or irrelevant URLs in at least 90% of test cases
*   **SC-007**: System gracefully handles Azure service interruptions with clear error messages and fallback options
*   **SC-008**: Application startup time is under 10 seconds on standard development machines with valid Azure credentials
*   **SC-009**: Memory usage remains stable during extended processing sessions without significant leaks or accumulation
*   **SC-010**: Generated answers meet specified character limits within 3 retry attempts for 95% of processed questions
