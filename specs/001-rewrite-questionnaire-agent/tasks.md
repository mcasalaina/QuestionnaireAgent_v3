# Tasks: Rewrite Questionnaire Agent using Microsoft Agent Framework

**Input**: Design documents from `/specs/001-rewrite-questionnaire-agent/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL based on constitutional requirement for TDD. Mock modes are included for testing without Azure dependencies.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
Based on plan.md structure - single desktop application with modular architecture at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per implementation plan with ui/, excel/, agents/, utils/, tests/ modules
- [X] T002 Initialize Python 3.11+ project with .venv virtual environment and requirements.txt
- [X] T003 [P] Create .env.template file with required Azure AI Foundry configuration variables
- [X] T004 [P] Setup .gitignore to exclude .env files and Python cache directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Install agent-framework-azure-ai --pre and all dependencies in utils/requirements_installer.py
- [X] T006 [P] Implement ConfigurationManager in utils/config.py with .env loading and validation
- [X] T007 [P] Implement Azure authentication with DefaultAzureCredential fallback in utils/azure_auth.py
- [X] T008 [P] Create structured logging setup in utils/logger.py with Azure tracing integration
- [X] T009 [P] Implement custom exception classes in utils/exceptions.py for specific error handling
- [X] T010 [P] Create data transfer objects in utils/data_types.py (Question, Answer, ProcessingResult, etc.)
- [X] T011 [P] Implement mock Azure services in tests/mock/mock_azure_services.py for testing without Azure
- [X] T012 Create FoundryAgentSession resource management pattern in utils/azure_auth.py
- [X] T013 Setup Azure AI Foundry connectivity verification and startup authentication check

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Single Question Processing via GUI (Priority: P1) 🎯 MVP

**Goal**: User can launch GUI, enter a question, and receive a validated answer with real-time progress and separated documentation

**Independent Test**: Launch application, enter "Does Azure AI support video generation?", click "Ask!", verify validated answer appears with documentation links separated

### Tests for User Story 1 (TDD - Constitutional Requirement) ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Unit test for Question data validation in tests/unit/test_data_types.py
- [ ] T015 [P] [US1] Unit test for UIManager.process_single_question in tests/unit/test_ui_components.py
- [ ] T016 [P] [US1] Integration test for single question workflow in tests/integration/test_agent_workflow.py
- [ ] T017 [P] [US1] Mock mode test for GUI question processing in tests/mock/test_mock_modes.py

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement AgentCoordinator.process_question in agents/workflow_manager.py
- [ ] T019 [P] [US1] Create Question Answerer agent executor in agents/question_answerer.py
- [ ] T020 [P] [US1] Create Answer Checker agent executor in agents/answer_checker.py
- [ ] T021 [P] [US1] Create Link Checker agent executor in agents/link_checker.py
- [ ] T022 [US1] Implement sequential workflow orchestration using Microsoft Agent Framework in agents/workflow_manager.py (depends on T018-T021)
- [ ] T023 [P] [US1] Create main GUI window layout in ui/main_window.py with tkinter interface
- [ ] T024 [P] [US1] Implement status bar and progress tracking in ui/status_manager.py
- [ ] T025 [P] [US1] Create error dialog system in ui/dialogs.py with specific error types
- [ ] T026 [US1] Integrate GUI with AgentCoordinator for question processing in ui/main_window.py (depends on T022, T023)
- [ ] T027 [US1] Implement real-time reasoning display and progress updates in ui/main_window.py
- [ ] T028 [US1] Add window title "Questionnaire Answerer (Microsoft Agent Framework)" and GUI layout matching original
- [ ] T029 [US1] Implement retry logic with configurable maximum attempts and character limit handling
- [ ] T030 [US1] Create main application entry point in question_answerer.py coordinating all modules

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - users can process single questions through complete multi-agent workflow

---

## Phase 4: User Story 2 - Excel Batch Processing (Priority: P2)

**Goal**: User can import Excel files, have columns automatically identified, process multiple questions, and export results with preserved formatting

**Independent Test**: Prepare Excel file with questions, click "Import From Excel", verify processed output file generated with answers and links in appropriate columns

### Tests for User Story 2 (TDD - Constitutional Requirement) ⚠️

- [ ] T031 [P] [US2] Unit test for ExcelProcessor.load_file in tests/unit/test_excel_processor.py
- [ ] T032 [P] [US2] Unit test for column identification AI analysis in tests/unit/test_excel_processor.py
- [ ] T033 [P] [US2] Integration test for Excel batch processing workflow in tests/integration/test_excel_processing.py
- [ ] T034 [P] [US2] Mock mode test for Excel processing without Azure in tests/mock/test_mock_modes.py

### Implementation for User Story 2

- [ ] T035 [P] [US2] Implement ExcelProcessor.load_file in excel/processor.py with format validation
- [ ] T036 [P] [US2] Create AI-powered column identification in excel/column_identifier.py using Azure AI
- [ ] T037 [P] [US2] Implement output file generation with formatting preservation in excel/formatter.py
- [ ] T038 [US2] Integrate Excel loading with column identification in excel/processor.py (depends on T035, T036)
- [ ] T039 [US2] Implement ExcelProcessor.save_results with original formatting preservation (depends on T037)
- [ ] T040 [US2] Add "Import From Excel" button and file selection dialog in ui/main_window.py
- [ ] T041 [US2] Implement batch processing progress tracking in ui/status_manager.py with question counts
- [ ] T042 [US2] Integrate Excel processing with AgentCoordinator.process_batch in agents/workflow_manager.py
- [ ] T043 [US2] Add Excel error handling for unsupported formats and complex formatting in excel/processor.py
- [ ] T044 [US2] Implement save dialog and output file generation in ui/main_window.py
- [ ] T045 [US2] Add background threading for Excel processing to maintain GUI responsiveness

**Checkpoint**: At this point, User Story 2 should work independently - users can process Excel files with automatic column detection and preserved formatting

---

## Phase 5: User Story 3 - Multi-Agent Workflow Orchestration (Priority: P3)

**Goal**: System orchestrates three specialized agents with distinct responsibilities, continuing until approval or maximum retries reached, with visible reasoning

**Independent Test**: Monitor reasoning output during question processing to verify three distinct agents are involved and validation failures trigger retries

### Tests for User Story 3 (TDD - Constitutional Requirement) ⚠️

- [ ] T046 [P] [US3] Unit test for Microsoft Agent Framework workflow creation in tests/unit/test_agents.py
- [ ] T047 [P] [US3] Unit test for agent validation and retry logic in tests/unit/test_agents.py
- [ ] T048 [P] [US3] Integration test for multi-agent orchestration patterns in tests/integration/test_agent_workflow.py
- [ ] T049 [P] [US3] Mock test for agent failure scenarios and retry handling in tests/mock/test_mock_modes.py

### Implementation for User Story 3

- [ ] T050 [P] [US3] Implement WorkflowBuilder pattern for sequential agent orchestration in agents/workflow_manager.py
- [ ] T051 [P] [US3] Add Bing Search grounding tool integration for Question Answerer in agents/question_answerer.py
- [ ] T052 [P] [US3] Implement web validation capabilities for Answer Checker in agents/answer_checker.py
- [ ] T053 [P] [US3] Add HTTP requests and content analysis for Link Checker in agents/link_checker.py
- [ ] T054 [US3] Integrate agent validation checkpoints with retry mechanisms (depends on T050-T053)
- [ ] T055 [US3] Implement workflow context management and state tracking in agents/workflow_manager.py
- [ ] T056 [US3] Add agent reasoning logging and progress reporting to UI in agents/workflow_manager.py
- [ ] T057 [US3] Implement special case handling for Answer Checker approved / Link Checker failed scenarios
- [ ] T058 [US3] Add workflow streaming events for real-time UI updates in agents/workflow_manager.py
- [ ] T059 [US3] Integrate FoundryAgentSession cleanup with workflow completion in agents/workflow_manager.py

**Checkpoint**: At this point, User Story 3 should demonstrate sophisticated multi-agent validation with proper reasoning visibility and error handling

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T060 [P] Add comprehensive error handling for all Azure service failure scenarios across modules
- [ ] T061 [P] Implement memory usage monitoring and leak prevention in utils/logger.py
- [ ] T062 [P] Add startup time optimization and Azure connectivity verification
- [ ] T063 [P] Implement network connectivity error handling for web search operations
- [ ] T064 [P] Add detailed error dialogs with specific failure reasons and suggested fixes
- [ ] T065 [P] Run integration test suite validation across all user stories
- [ ] T066 [P] Performance optimization for character limit retry logic
- [ ] T067 [P] Code cleanup and documentation updates in all modules
- [ ] T068 Update README.md with Microsoft Agent Framework setup and usage instructions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May reuse Agent orchestration from US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances agents from US1/US2 but independently testable

### Within Each User Story

- Tests (TDD requirement) MUST be written and FAIL before implementation
- Agent executors before workflow orchestration
- UI components before integration
- Core implementation before error handling and progress tracking
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks can run in parallel within Phase 1
- Foundational tasks marked [P] can run in parallel within Phase 2
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each user story, tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD requirement):
Task T014: "Unit test for Question data validation"
Task T015: "Unit test for UIManager.process_single_question"
Task T016: "Integration test for single question workflow"
Task T017: "Mock mode test for GUI question processing"

# Launch all agent executors for User Story 1 together:
Task T019: "Create Question Answerer agent executor"
Task T020: "Create Answer Checker agent executor" 
Task T021: "Create Link Checker agent executor"

# Launch all UI components for User Story 1 together:
Task T023: "Create main GUI window layout"
Task T024: "Implement status bar and progress tracking"
Task T025: "Create error dialog system"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with single question processing
5. Deploy/demo if ready - users can process individual questions with multi-agent validation

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Excel capability added)
4. Add User Story 3 → Test independently → Deploy/Demo (Enhanced orchestration)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Single Question Processing)
   - Developer B: User Story 2 (Excel Batch Processing)
   - Developer C: User Story 3 (Multi-Agent Orchestration)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Constitutional requirement: Tests written first (TDD) with mock modes for Azure-free testing
- Verify tests fail before implementing to ensure proper test coverage
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Microsoft Agent Framework --pre flag required for installation
- FoundryAgentSession pattern mandatory for Azure resource cleanup
