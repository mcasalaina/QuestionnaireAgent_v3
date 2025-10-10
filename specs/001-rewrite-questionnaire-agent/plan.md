# Implementation Plan: Rewrite Questionnaire Agent using Microsoft Agent Framework

**Branch**: `001-rewrite-questionnaire-agent` | **Date**: 2025-10-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rewrite-questionnaire-agent/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Rewrite the existing Questionnaire Agent application to use Microsoft Agent Framework for multi-agent orchestration, separating UI and Excel handling into distinct modules. The system will maintain the three-agent pattern (Question Answerer, Answer Checker, Link Checker) while upgrading to modern Azure AI Foundry integration with improved error handling and modular architecture. Key technical approach includes using agent-framework-azure-ai SDK, direct method calls between modules, and FoundryAgentSession for resource management.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: agent-framework-azure-ai (--pre), azure-ai-projects, azure-identity, tkinter, openpyxl, pandas, playwright, pytest  
**Storage**: Local .env files for configuration, temporary Excel files during processing, no persistent database required  
**Testing**: pytest with mock modes for Azure service testing, integration tests for multi-agent workflows  
**Target Platform**: Windows/macOS/Linux desktop with Azure AI Foundry connectivity  
**Project Type**: single desktop application with modular architecture  
**Performance Goals**: <2 minutes for single question processing, <50 questions Excel batch processing without timeouts  
**Constraints**: <10 second startup time, stable memory usage during extended sessions, immediate failure on service unavailability  
**Scale/Scope**: Single-user desktop application, up to 50 questions per Excel batch, ~2000 character answer limits

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check (Pre-Phase 0):**
- [x] **Multi-Agent Architecture**: Feature integrates with existing Question Answerer, Answer Checker, and Link Checker pattern
- [x] **Azure AI Foundry Integration**: Uses Azure AI Foundry Agent Service and SDK exclusively with DefaultAzureCredential
- [x] **Resource Management**: All agents/threads managed through FoundryAgentSession context managers
- [x] **Environment Configuration**: Sensitive data in .env files, never committed to version control
- [x] **Test-Driven Development**: Tests written first, including Azure service failure scenarios and mock modes

**Post-Phase 1 Design Review:**
- [x] **Multi-Agent Architecture**: Confirmed in workflow_manager.py design with sequential orchestration pattern using Microsoft Agent Framework
- [x] **Azure AI Foundry Integration**: AzureAIAgentClient integration specified in module interfaces with DefaultAzureCredential
- [x] **Resource Management**: FoundryAgentSession pattern referenced in quickstart and agent coordinator interface
- [x] **Environment Configuration**: .env configuration management detailed in ConfigurationManager interface
- [x] **Test-Driven Development**: Mock implementations and test strategy defined in quickstart guide

**Gate Status: ✅ PASSED** - All constitutional requirements satisfied in design phase.

## Project Structure

### Documentation (this feature)

```
specs/001-rewrite-questionnaire-agent/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
# Single desktop application with modular architecture
question_answerer.py            # Main entry point and application coordinator
ui/
├── __init__.py
├── main_window.py              # Primary GUI interface (tkinter)
├── status_manager.py           # Status bar and progress tracking
└── dialogs.py                  # Error dialogs and file selection

excel/
├── __init__.py
├── processor.py                # Excel file loading and processing
├── column_identifier.py        # AI-powered column identification
└── formatter.py                # Output file generation with formatting preservation

agents/
├── __init__.py
├── workflow_manager.py         # Microsoft Agent Framework orchestration
├── question_answerer.py        # Question Answerer agent implementation
├── answer_checker.py           # Answer Checker agent implementation
└── link_checker.py             # Link Checker agent implementation

utils/
├── __init__.py
├── config.py                   # Environment and configuration management
├── logger.py                   # Structured logging setup
└── azure_auth.py               # Azure authentication and connectivity

tests/
├── __init__.py
├── unit/
│   ├── test_agents.py
│   ├── test_excel_processor.py
│   └── test_ui_components.py
├── integration/
│   ├── test_agent_workflow.py
│   └── test_excel_processing.py
└── mock/
    ├── mock_azure_services.py
    └── test_mock_modes.py

requirements.txt                # Python dependencies including --pre flag note
.env.template                   # Template for required environment variables
```

**Structure Decision**: Selected single project structure with clear module separation as specified in requirements. The modular design enables independent development and testing of UI, Excel processing, and agent orchestration components while maintaining direct method call interfaces between modules.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
