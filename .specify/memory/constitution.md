<!-- 
Sync Impact Report:
- Version change: none → 1.0.0 (initial constitution)
- List of modified principles: none (initial creation)
- Added sections: Core Principles (5), Azure AI Platform Requirements, Development Standards, Governance
- Removed sections: none
- Templates requiring updates: 
  ✅ Updated .specify/templates/plan-template.md (constitution check aligned)
  ✅ Updated .specify/templates/spec-template.md (requirements aligned)
  ✅ Updated .specify/templates/tasks-template.md (task categorization aligned)
- Follow-up TODOs: none
-->

# Questionnaire Agent Constitution

## Core Principles

### I. Multi-Agent Architecture

Every feature MUST be designed around the three-agent pattern: Question Answerer, Answer Checker, and Link Checker. New functionality MUST integrate with this existing architecture rather than bypass it. Agent responsibilities MUST remain clearly separated with distinct roles and capabilities.

**Rationale**: The multi-agent validation pattern ensures answer quality and reliability through independent verification stages.

### II. Azure AI Foundry Integration

All AI functionality MUST use Azure AI Foundry Agent Service and SDK exclusively. Authentication MUST use DefaultAzureCredential (managed identity) or interactive browser credential. No alternative AI services or direct API calls permitted.

**Rationale**: Standardizes on Microsoft's enterprise AI platform for consistency, security, and integrated monitoring.

### III. Resource Management & Cleanup

All Azure AI Foundry agents and threads MUST be managed through FoundryAgentSession context managers to ensure proper cleanup. Resource leaks are NON-NEGOTIABLE failures that MUST be prevented through defensive programming patterns.

**Rationale**: Prevents cost accumulation and resource exhaustion in Azure AI Foundry, ensuring sustainable operation.

### IV. Environment-Based Configuration

All sensitive configuration MUST be stored in .env files that are never committed to version control. DefaultAzureCredential MUST be used for Azure authentication instead of connection strings where possible. Configuration MUST be validated at startup with clear error messages.

**Rationale**: Maintains security best practices and prevents credential exposure while ensuring deployability across environments.

### V. Test-Driven Development

New features MUST have tests written first that demonstrate the expected behavior. Tests MUST cover both success paths and failure scenarios including Azure service failures. Mock modes MUST be available for testing without Azure dependencies.

**Rationale**: Ensures reliability and allows development/testing without consuming Azure resources or requiring live credentials.

## Azure AI Platform Requirements

All development MUST adhere to Microsoft Azure AI and Azure AI Foundry standards:

- **SDK Compliance**: Use only azure-ai-projects, azure-identity, and azure-ai-evaluation SDKs
- **Tracing Integration**: Azure AI Foundry tracing MUST be configured with Application Insights
- **Authentication**: DefaultAzureCredential MUST be primary authentication method
- **Resource Management**: FoundryAgentSession pattern MUST be used for all agent lifecycle management
- **Grounding**: Bing Search integration through Azure AI Foundry grounding tools MUST be used for web search

## Development Standards

Code organization and quality requirements:

- **Modular Structure**: Break functionality into smaller, focused files rather than monolithic implementations
- **Virtual Environment**: All Python development MUST use .venv virtual environment
- **Dependency Management**: requirements.txt MUST be updated when packages are added
- **Error Handling**: Graceful degradation required for Azure service failures
- **Logging**: Structured logging required with appropriate log levels
- **Documentation**: README files MUST be maintained for setup and usage instructions

## Governance

This constitution supersedes all other development practices and guidelines. All code reviews MUST verify constitutional compliance before approval. Any violations MUST be justified with technical rationale and approved by project maintainers.

**Amendment Process**: Changes require documentation of impact, migration plan, and approval. Version increments follow semantic versioning based on scope of change.

**Compliance Review**: All pull requests MUST include constitutional compliance verification. Complex architectural decisions MUST reference constitutional principles.

**Version**: 1.0.0 | **Ratified**: 2025-10-09 | **Last Amended**: 2025-10-09
