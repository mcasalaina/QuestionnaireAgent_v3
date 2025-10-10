# Research: Rewrite Questionnaire Agent using Microsoft Agent Framework

**Date**: 2025-10-09  
**Purpose**: Resolve technical unknowns and establish implementation approach for Microsoft Agent Framework migration

## Model Selection for Multi-Agent System

**Decision**: gpt-4.1-mini for cost-effective multi-agent orchestration  
**Rationale**: 
- Optimal balance of quality (0.8066) and cost ($0.7 per 1M tokens) for multi-agent workflows
- 1M context window supports complex agent instructions and conversation history
- High throughput (125.04 tokens/sec) suitable for real-time UI updates
- Strong instruction following capabilities essential for agent role separation

**Alternatives considered**:
- gpt-4.1: Higher quality (0.844) but 5x cost increase not justified for this application
- gpt-4o-mini: Lower cost ($0.2625) but smaller context (131K) may limit agent conversation depth
- o3-mini: Better reasoning (0.8658) but significantly higher cost ($1.925) and lower throughput

## Microsoft Agent Framework Integration Patterns

**Decision**: Sequential workflow with validation checkpoints using Microsoft Agent Framework's built-in orchestration  
**Rationale**:
- Sequential pattern (Question Answerer → Answer Checker → Link Checker) matches existing workflow
- Built-in retry mechanisms align with requirement for configurable maximum attempts
- Microsoft Agent Framework's executor pattern enables clean agent separation
- WorkflowBuilder provides clear orchestration without complex custom logic

**Implementation approach**:
```python
from agent_framework import WorkflowBuilder, Executor, WorkflowContext
from agent_framework_azure_ai import AzureAIAgentClient

# Each agent becomes an Executor in the workflow
class QuestionAnswererExecutor(Executor):
    @handler
    async def handle(self, question: str, ctx: WorkflowContext[dict]) -> None:
        # Generate answer and forward to next stage
        
# Workflow orchestration
workflow = (WorkflowBuilder()
    .add_edge(question_answerer, answer_checker)
    .add_edge(answer_checker, link_checker)
    .set_start_executor(question_answerer)
    .build())
```

**Alternatives considered**:
- Custom orchestration: More control but violates constitutional requirement for Agent Framework exclusive use
- Concurrent pattern: Would require complex merge logic and doesn't fit validation sequence
- Connected Agents (Azure AI Foundry): Less control over retry logic and workflow state

## Azure AI Foundry Authentication and Resource Management

**Decision**: DefaultAzureCredential with interactive fallback, FoundryAgentSession context managers  
**Rationale**:
- DefaultAzureCredential supports multiple auth methods (managed identity, CLI, interactive)
- Interactive browser credential provides user-friendly login experience for desktop application
- FoundryAgentSession ensures proper cleanup preventing resource leaks and cost accumulation
- Startup authentication check prevents runtime failures during processing

**Implementation pattern**:
```python
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from utils.azure_auth import verify_azure_connectivity

async def initialize_azure_client():
    try:
        credential = DefaultAzureCredential()
        await verify_azure_connectivity(credential)
    except AuthenticationError:
        credential = InteractiveBrowserCredential()
        await verify_azure_connectivity(credential)
    
    return AzureAIAgentClient(
        project_endpoint=endpoint,
        async_credential=credential
    )
```

## Error Handling Strategy for Service Failures

**Decision**: Fail-fast approach with detailed error dialogs and immediate termination  
**Rationale**:
- Clarifications specified immediate failure for all service unavailability scenarios
- Users prefer clear failure feedback over ambiguous degraded functionality
- Prevents partial processing states that could confuse users
- Aligns with constitutional requirement for graceful degradation

**Error categorization**:
1. **Azure Service Failures**: Display "Azure AI Foundry Unavailable" with retry instructions
2. **Network Connectivity**: Display "Network Connection Error" with troubleshooting steps  
3. **Excel Format Issues**: Display specific formatting problems with suggested fixes
4. **Authentication Failures**: Trigger automatic login flow with fallback to manual instructions

## Module Communication Architecture

**Decision**: Direct method calls with shared data structures and synchronous interfaces  
**Rationale**:
- Clarification specified direct method calls over event-driven or callback patterns
- Synchronous interfaces simplify error propagation and state management
- Shared data structures reduce serialization overhead for local desktop application
- Easier debugging and testing compared to asynchronous message passing

**Interface contracts**:
```python
# UI to Main Application
class UIManager:
    def process_question(self, question: str, context: str, char_limit: int) -> ProcessingResult
    def process_excel_file(self, file_path: str) -> ExcelProcessingResult
    def update_progress(self, agent: str, message: str) -> None

# Excel Handler to Main Application  
class ExcelProcessor:
    def load_file(self, file_path: str) -> ExcelWorkbook
    def identify_columns(self, workbook: ExcelWorkbook) -> ColumnMapping
    def save_results(self, workbook: ExcelWorkbook, results: List[QuestionResult]) -> str
```

## Testing Strategy for Azure Service Dependencies

**Decision**: Mock modes for unit testing, contract tests for integration validation  
**Rationale**:
- Constitutional requirement for mock modes to enable testing without Azure consumption
- Contract tests validate Azure SDK integration without testing external service reliability
- Separate integration test suite for end-to-end validation with live services
- Mock implementations mirror real service interfaces to catch integration issues

**Test organization**:
- Unit tests: Mock all Azure services, focus on business logic
- Contract tests: Validate Azure SDK usage patterns and error handling
- Integration tests: Live Azure services for critical path validation
- Mock mode: Full application functionality without external dependencies

## Performance Optimization for GUI Responsiveness

**Decision**: Threading for long-running operations with progress callbacks  
**Rationale**:
- Desktop GUI requires responsive interface during multi-agent processing
- Threading prevents UI freezing during 2-minute processing windows
- Progress callbacks enable real-time status updates in reasoning panel
- Synchronous module interfaces simplify thread safety

**Implementation approach**:
- Main UI thread handles user interactions and progress updates
- Background thread executes agent workflow with progress reporting
- Thread-safe queue for progress messages from agents to UI
- Cancel capability for long-running Excel processing operations