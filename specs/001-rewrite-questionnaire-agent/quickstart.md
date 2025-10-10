# Quickstart: Rewrite Questionnaire Agent using Microsoft Agent Framework

**Date**: 2025-10-09  
**Purpose**: Get started with developing and running the Microsoft Agent Framework-based questionnaire agent

## Prerequisites

### Development Environment
- Python 3.11 or higher
- Visual Studio Code with Python extension
- Git for version control

### Azure Resources
- Azure subscription with AI Foundry project
- Azure AI Foundry project with deployed model (gpt-4.1-mini recommended)
- Bing Search resource connected to AI Foundry project
- Application Insights resource for tracing (optional but recommended)

### Authentication Setup
- Azure CLI installed: `az login` for development authentication
- OR Azure account with browser-based authentication available

## Quick Setup

### 1. Environment Setup

Create and activate Python virtual environment:
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)  
source .venv/bin/activate
```

### 2. Install Dependencies

Install Microsoft Agent Framework and required packages:
```bash
# Install with preview flag (required while Agent Framework is in preview)
pip install agent-framework-azure-ai --pre

# Install additional dependencies
pip install azure-ai-projects azure-identity azure-ai-evaluation
pip install openpyxl pandas playwright python-dotenv
pip install azure-monitor-opentelemetry opentelemetry-sdk
pip install pytest pytest-asyncio

# Update requirements.txt
pip freeze > requirements.txt
```

**Important**: The `--pre` flag is required for agent-framework-azure-ai while it's in preview.

### 3. Configuration

Create `.env` file in project root (never commit this file):
```bash
# Copy template
cp .env.template .env

# Edit with your Azure AI Foundry details
AZURE_OPENAI_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
AZURE_OPENAI_MODEL_DEPLOYMENT=gpt-4.1-mini
BING_CONNECTION_ID=your-bing-connection-name
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key;...
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

### 4. Verify Azure Connectivity

Test Azure AI Foundry connection:
```python
# utils/verify_azure.py
from azure.identity import DefaultAzureCredential
from agent_framework_azure_ai import AzureAIAgentClient
import os
from dotenv import load_dotenv

load_dotenv()

async def verify_connection():
    try:
        credential = DefaultAzureCredential()
        client = AzureAIAgentClient(
            project_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            model_deployment_name=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT"),
            async_credential=credential
        )
        print("✅ Azure AI Foundry connection successful")
        return True
    except Exception as e:
        print(f"❌ Azure connection failed: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_connection())
```

Run verification:
```bash
python utils/verify_azure.py
```

## Development Workflow

### 1. Project Structure Setup

Create the modular directory structure:
```bash
# Main application
touch question_answerer.py

# UI module
mkdir ui
touch ui/__init__.py ui/main_window.py ui/status_manager.py ui/dialogs.py

# Excel processing module  
mkdir excel
touch excel/__init__.py excel/processor.py excel/column_identifier.py excel/formatter.py

# Agents module
mkdir agents
touch agents/__init__.py agents/workflow_manager.py
touch agents/question_answerer.py agents/answer_checker.py agents/link_checker.py

# Utilities
mkdir utils
touch utils/__init__.py utils/config.py utils/logger.py utils/azure_auth.py

# Tests
mkdir tests tests/unit tests/integration tests/mock
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py tests/mock/__init__.py
```

### 2. Start with Core Configuration

Begin development with configuration management:

```python
# utils/config.py
import os
from dataclasses import dataclass
from typing import Optional
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from agent_framework_azure_ai import AzureAIAgentClient
from dotenv import load_dotenv

@dataclass
class AppConfig:
    azure_endpoint: str
    model_deployment: str
    bing_connection_id: str
    app_insights_connection: Optional[str] = None
    max_retries: int = 10
    default_char_limit: int = 2000

class ConfigurationManager:
    def __init__(self):
        load_dotenv()
        self.config = self._load_config()
    
    def _load_config(self) -> AppConfig:
        return AppConfig(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            model_deployment=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT"), 
            bing_connection_id=os.getenv("BING_CONNECTION_ID"),
            app_insights_connection=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        )
    
    async def get_azure_client(self) -> AzureAIAgentClient:
        # Implementation with authentication fallback
        pass
```

### 3. Implement Agent Framework Integration

Start with the workflow manager using Microsoft Agent Framework patterns:

```python
# agents/workflow_manager.py
from agent_framework import WorkflowBuilder, Executor, WorkflowContext
from agent_framework_azure_ai import AzureAIAgentClient

class QuestionAnswererExecutor(Executor):
    def __init__(self, client: AzureAIAgentClient, agent_id: str):
        super().__init__(id="question_answerer")
        self.client = client
        self.agent_id = agent_id
    
    @handler
    async def handle(self, question: str, ctx: WorkflowContext[dict]) -> None:
        # Implement question answering logic
        pass

# Similar for AnswerCheckerExecutor and LinkCheckerExecutor

class AgentCoordinator:
    def __init__(self, azure_client: AzureAIAgentClient):
        self.client = azure_client
        self.workflow = None
    
    async def create_workflow(self):
        # Build the sequential workflow
        question_answerer = QuestionAnswererExecutor(self.client, "qa_agent")
        answer_checker = AnswerCheckerExecutor(self.client, "ac_agent") 
        link_checker = LinkCheckerExecutor(self.client, "lc_agent")
        
        self.workflow = (WorkflowBuilder()
            .add_edge(question_answerer, answer_checker)
            .add_edge(answer_checker, link_checker)
            .set_start_executor(question_answerer)
            .build())
```

### 4. Build UI Module

Create the main GUI interface:

```python
# ui/main_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from typing import Callable

class UIManager:
    def __init__(self, agent_coordinator):
        self.coordinator = agent_coordinator
        self.root = tk.Tk()
        self.setup_ui()
    
    def setup_ui(self):
        self.root.title("Questionnaire Answerer (Microsoft Agent Framework)")
        self.root.geometry("1200x800")
        # Implement UI layout matching original design
        pass
    
    def on_ask_clicked(self):
        # Handle single question processing in background thread
        pass
    
    def on_import_excel_clicked(self):
        # Handle Excel file import and processing
        pass
```

## Testing Strategy

### 1. Unit Tests with Mocking

Create mock implementations for Azure services:

```python
# tests/mock/mock_azure_services.py
class MockAzureAIAgentClient:
    def __init__(self):
        self.agents = {}
        self.threads = {}
    
    async def create_agent(self, **kwargs):
        # Mock agent creation
        pass

# tests/unit/test_workflow_manager.py
import pytest
from agents.workflow_manager import AgentCoordinator
from tests.mock.mock_azure_services import MockAzureAIAgentClient

@pytest.mark.asyncio
async def test_question_processing():
    mock_client = MockAzureAIAgentClient()
    coordinator = AgentCoordinator(mock_client)
    # Test workflow execution
    pass
```

### 2. Integration Tests

Test with live Azure services (requires valid credentials):

```python
# tests/integration/test_azure_integration.py
import pytest
from utils.config import ConfigurationManager

@pytest.mark.integration
@pytest.mark.asyncio
async def test_azure_agent_creation():
    config_manager = ConfigurationManager()
    client = await config_manager.get_azure_client()
    # Test actual agent creation and cleanup
    pass
```

Run tests:
```bash
# Unit tests only (with mocks)
pytest tests/unit/

# Integration tests (requires Azure credentials)
pytest tests/integration/ -m integration

# All tests
pytest tests/
```

## Running the Application

### Development Mode
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Run with full logging
python question_answerer.py --debug

# Run in mock mode (no Azure required)
python question_answerer.py --mock
```

### Production Mode
```bash
# Run with minimal logging
python question_answerer.py

# Run with specific model
python question_answerer.py --model gpt-4.1-mini
```

## Troubleshooting

### Common Issues

**Azure Authentication Failures**
```bash
# Check Azure CLI login
az account show

# Re-authenticate if needed
az login

# Verify AI Foundry access
az account list --query "[].{Name:name, SubscriptionId:id}"
```

**Agent Framework Installation Issues**
```bash
# Ensure preview flag is used
pip uninstall agent-framework-azure-ai
pip install agent-framework-azure-ai --pre

# Check version
python -c "import agent_framework; print(agent_framework.__version__)"
```

**Network Connectivity Problems**
- Verify firewall allows HTTPS traffic to Azure
- Check corporate proxy settings
- Test basic connectivity: `curl https://management.azure.com/`

**Excel Processing Failures**
- Ensure Excel files are not password protected
- Verify file permissions (read/write access)
- Check for complex formatting (merged cells, embedded objects)

### Debug Mode

Enable detailed logging for troubleshooting:
```python
# utils/logger.py
import logging
from azure.core.tracing.ext.opentelemetry_span import OpenTelemetrySpan

def setup_debug_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Enable Azure SDK debug logging
    logging.getLogger('azure').setLevel(logging.DEBUG)
```

## Next Steps

1. **Follow Implementation Plan**: Proceed with Phase 1 design artifacts
2. **Create Tasks**: Run `/speckit.tasks` to generate implementation tasks
3. **Start Development**: Begin with configuration module and tests
4. **Iterative Testing**: Test each module independently before integration
5. **Documentation**: Update README.md with deployment instructions