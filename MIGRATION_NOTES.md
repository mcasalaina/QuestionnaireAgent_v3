# agent-framework rc5 Migration – Complete

## Root Cause

Two issues combined:

1. The `agent-framework-azure-ai` package was upgraded from `1.0.0b260107` → `1.0.0rc5`, requiring API migration across the codebase.
2. The `AzureAIAgentClient` (Foundry Agent Service v1) uses the `/assistants` API endpoint, which returns empty HTTP responses for `gpt-4.1` deployments — causing `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

## Fix Applied

Migrated to **Foundry Agent Service v2** (`AzureAIClient`) which uses the `/agents` API endpoint, plus all rc5 API changes.

**Packages installed:**
- `agent-framework-azure-ai == 1.0.0rc5`
- `agent-framework-core == 1.0.0rc5`
- `azure-ai-agents == 1.2.0b5`

## API Changes Applied

| Old (b260107) | New (rc5) |
|-----|-----|
| `from agent_framework_azure_ai import AzureAIAgentClient` | `from agent_framework.azure import AzureAIClient` |
| `AzureAIAgentClient(project_endpoint=..., credential=...)` | `AzureAIClient(project_endpoint=..., credential=..., model_deployment_name=...)` |
| `ChatAgent(chat_client=client, name=..., instructions=...)` | `RawAgent(client, name=..., instructions=...)` |
| `ChatMessage(role=Role.USER, text=...)` | `Message(role="user", text=...)` |
| `Role.USER` (enum) | `"user"` (string literal) |
| `WorkflowBuilder().set_start_executor(x).build()` | `WorkflowBuilder(start_executor=x).build()` |
| `workflow.run_stream(data)` | `workflow.run(data, stream=True)` |
| Agent names with spaces: `"Question Answerer"` | Kebab-case names: `"question-answerer"` |

**Note:** `Role` changed from an enum to a `NewType` — use string literals `"user"` instead.

**Note:** Agent names must be alphanumeric with hyphens, max 63 chars (Foundry v2 requirement).

## Files Changed

- `src/utils/azure_auth.py` — `AzureAIAgentClient` → `AzureAIClient` (import, type hints, constructors)
- `src/agents/workflow_manager.py` — `AzureAIClient` import, `WorkflowBuilder(start_executor=...)`, `run(stream=True)`
- `src/agents/question_answerer.py` — `RawAgent`, `Message`, `"user"` role, kebab-case name
- `src/agents/answer_checker.py` — `RawAgent`, `Message`, `"user"` role, kebab-case name
- `src/agents/link_checker.py` — `RawAgent`, `Message`, `"user"` role, kebab-case name
- `src/excel/loader.py` — `AzureAIClient` import, kebab-case agent names
- `src/excel/column_identifier.py` — `"user"` role string
- `src/web/app.py` — `RawAgent` import, kebab-case agent name
- `tests/unit/test_column_identifier.py` — Updated mock patches for `RawAgent`/`Message`

## Current Status

✅ **All migration changes applied and verified.**

- Live test (`tests/test_live_azure_question.py`) passes end-to-end
- 123 unit tests pass; 21 have pre-existing failures unrelated to this migration

## How to Run

```bash
source .venv312/bin/activate && python run_app.py
```
