# Questionnaire Multiagent Application

**Version 3** - A windowed application that orchestrates three Azure AI Foundry agents to answer questions with fact-checking and link validation. Features both individual question processing and Excel import/export functionality, with a legacy command-line interface also available.

Originally created by Marco Casalaina. This version was authored using [GitHub Copilot Agent](https://github.com/features/copilot), the [Microsoft Agent Framework](https://github.com/microsoft/azureai-agent-framework), and [Spec Kit](https://github.com/microsoft/spec).

## Overview

This tool implements a multi-agent system that:

1. **Question Answerer**: Searches the web for evidence and synthesizes a candidate answer
2. **Answer Checker**: Validates factual correctness, completeness, and consistency
3. **Link Checker**: Verifies that every URL cited in the answer is reachable and relevant

If either checker rejects the answer, the Question Answerer reformulates and the cycle repeats up to 25 attempts.

## Features

- **Windowed GUI**: User-friendly interface built with Python tkinter
- **Command Line Options**: Configure settings and auto-start processing from the command line
- **Excel Integration**: Import questions from Excel files and export results
- **Real-time Progress**: Live reasoning display showing agent workflow
- **Character Limit Control**: Configurable answer length with automatic retries
- **Web Grounding**: All agents use Bing search via Azure AI Foundry
- **Multi-agent Validation**: Three-stage validation ensures answer quality
- **Source Verification**: All cited URLs are checked for reachability and relevance

## Installation

### Prerequisites

- Python 3.8 or higher
- Azure subscription with AI Foundry project
- Bing Search resource connected to your AI Foundry project

**Authentication:** The application will test your Azure authentication immediately on startup. If you have already run `az login` or `azd login`, the application will use that existing session. Otherwise, it will automatically open a browser window for interactive login. 

If you prefer to authenticate before starting the app, you can:
- Run `az login` in your terminal
- Set up environment variables for service principal authentication

### Install Dependencies

Create and activate a virtual environment, then install the required dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Build the Project

```bash
pip install -e .
```

## Usage

### Primary GUI Application

Ensure your virtual environment is activated, then run the main windowed application:

```bash
python run_app.py
```

#### Command Line Options

The application supports command line options to configure settings and auto-start processing:

**Configure Settings:**
```bash
# Set context (default: "Microsoft Azure AI")
python run_app.py --context "Custom Context"

# Set character limit (default: 2000)
python run_app.py --charlimit 3000

# Combine both
python run_app.py --context "Azure Services" --charlimit 1500
```

**Auto-start Question Processing:**
```bash
# Process a question immediately after initialization
python run_app.py --question "What types of text-to-speech do you offer?"

# With custom settings
python run_app.py --context "Microsoft Azure AI" --charlimit 2000 --question "How many languages does your TTS service support?"
```

**Auto-start Spreadsheet Processing:**
```bash
# Process an Excel file immediately after initialization
python run_app.py --spreadsheet ./tests/sample_questionnaire_1_sheet.xlsx

# With custom settings
python run_app.py --context "Azure AI" --charlimit 1500 --spreadsheet ./path/to/questionnaire.xlsx
```

**View All Options:**
```bash
python run_app.py --help
```

**Single Question Mode:**
1. Enter your context (default: "Microsoft Azure AI")
2. Set character limit (default: 2000)
3. Type your question and click "Ask!"
4. Monitor progress in the Reasoning tab
5. View results in Answer and Documentation tabs

**Excel Import Mode:**
1. Click "Import From Excel" button
2. Select Excel file with questions
3. System auto-detects question columns
4. Monitor real-time processing progress
5. Choose save location when complete

## Example Output

```
================================================================================
FINAL ANSWER:
================================================================================
Based on web search results, here's what I found:

The sky appears blue due to a phenomenon called Rayleigh scattering. When sunlight enters Earth's atmosphere, it collides with tiny gas molecules. Blue light has a shorter wavelength than other colors, so it gets scattered more in all directions by these molecules. This scattered blue light is what we see when we look at the sky.

Sources:
- [NASA Science](https://science.nasa.gov/earth/earth-atmosphere/why-is-the-sky-blue/)
- [National Weather Service](https://www.weather.gov/jetstream/color)
================================================================================
```

## Architecture

### Components

| Component | Responsibility | Grounding Source |
|-----------|---------------|------------------|
| **Question Answerer** | Searches the web for evidence, synthesizes a candidate answer | Web search API |
| **Answer Checker** | Validates factual correctness, completeness, and consistency | Web search API |
| **Link Checker** | Verifies that every URL cited in the answer is reachable and relevant | HTTP requests + web search |

### Workflow

1. **Read Input**: Accept a question from the command line
2. **Answer Generation**: Question Answerer retrieves evidence and produces a draft answer
3. **Validation**: 
   - Answer Checker reviews the draft for accuracy and completeness
   - Link Checker tests all cited URLs for reachability and relevance
4. **Decision**:
   - If both checkers approve: Output the final answer and terminate successfully
   - If either checker rejects: Log rejection reasons, increment attempt counter, and retry (up to 25 attempts)

## Configuration

### Environment Setup

#### Step 1: Create Environment File

Copy the template file and configure your values:

```bash
cp .env.template .env
```

Then edit `.env` with your actual Azure AI Foundry configuration values.

### Required Environment Variables

The application requires the following environment variables to be set in your `.env` file:

| Variable | Description | Where to Find |
|----------|-------------|---------------|
| `AZURE_OPENAI_ENDPOINT` | Azure AI Foundry project endpoint | Azure AI Foundry Portal > Project Overview > Project Details |
| `AZURE_OPENAI_MODEL_DEPLOYMENT` | Your deployed model name | Azure AI Foundry Portal > Models + Endpoints |
| `BING_CONNECTION_ID` | Bing Search connection name | Azure AI Foundry Portal > Connected Resources |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Application Insights connection string | Azure Portal > Application Insights > Overview |
| `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED` | Enable AI content tracing (optional) | Set to `true` or `false` |

**Example `.env` file:**

```bash
AZURE_OPENAI_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
AZURE_OPENAI_MODEL_DEPLOYMENT=gpt-4.1
BING_CONNECTION_ID=your-bing-connection-name
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key;IngestionEndpoint=https://your-region.in.applicationinsights.azure.com/;LiveEndpoint=https://your-region.livediagnostics.monitor.azure.com/;ApplicationId=your-app-id
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

**Important Security Notes:**

- Never commit your `.env` file to version control (it's already in `.gitignore`)
- The `.env.template` file shows the required structure without sensitive values
- Application Insights connection string enables Azure AI Foundry tracing for monitoring and debugging

### Azure AI Foundry Tracing

The application includes built-in Azure AI Foundry tracing integration that provides:

- **Distributed Tracing**: Full visibility into multi-agent workflows
- **Performance Monitoring**: Track execution times and bottlenecks  
- **Gen AI Content Capture**: Record prompts and responses (when enabled)
- **Error Tracking**: Detailed error context and stack traces
- **Resource Usage**: Monitor token consumption and API calls

Traces appear in:

- **Azure AI Foundry Portal** → Tracing tab
- **Azure Portal** → Application Insights → Transaction search

Set `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=false` in production if you want to exclude AI content from traces for privacy reasons.

### FoundryAgentSession Helper

The `FoundryAgentSession` class in `utils/resource_manager.py` provides a context manager for safely managing Azure AI Foundry agent and thread resources. This helper is **required** because:

1. **Resource Cleanup**: Azure AI Foundry agents and threads are persistent resources that must be explicitly deleted to avoid resource leaks
2. **Exception Safety**: Ensures cleanup occurs even if exceptions are raised during agent operations
3. **Cost Management**: Prevents accumulation of unused resources that could incur costs

Usage example:

```python
with FoundryAgentSession(client, model="gpt-4o-mini", 
                        name="my-agent", 
                        instructions="You are a helpful assistant") as (agent, thread):
    # Use agent and thread for operations
    # Resources are automatically cleaned up when exiting the context
```

The context manager handles:

- Creating agent and thread resources on entry
- Automatic cleanup on exit (even if exceptions occur)
- Robust error handling during cleanup to prevent masking original exceptions

### API Configuration

The tool uses Azure AI Foundry with integrated Bing search grounding. For alternative search APIs, consider:

- Google Custom Search API
- Bing Search API  
- SerpAPI

## Limitations

- **Demo Implementation**: Uses basic web search and text processing
- **Rate Limiting**: May encounter rate limits with free APIs
- **Language Support**: Optimized for English questions
- **Fact Checking**: Uses heuristic-based validation rather than advanced fact-checking

## Development

### Project Structure

```text
QuestionnaireAgent_v3/
├── run_app.py                   # Main application entry point
├── src/
│   ├── agents/                  # Agent implementations
│   │   ├── __init__.py
│   │   ├── workflow_manager.py
│   ├── ui/                      # GUI components
│   │   ├── main_window.py
│   │   └── ...
│   ├── excel/                   # Excel processing
│   │   ├── loader.py
│   │   ├── processor.py
│   │   └── column_identifier.py
│   ├── utils/                   # Shared utilities
│   │   ├── __init__.py
│   │   ├── logger.py
│   ├── resource_manager.py      # Azure AI Foundry resource management
│   └── web_search.py
├── tests/                       # Test suite
├── requirements.txt             # Python dependencies
├── setup.py                     # Installation script
├── README.md                    # This documentation
└── README_Questionnaire_UI.md   # Detailed UI documentation
```

### Adding New Features

To extend the system:

1. **New Validation**: Add checks to `AnswerChecker`
2. **Better Search**: Upgrade `WebSearcher` with more sophisticated APIs
3. **Advanced NLP**: Integrate language models for better synthesis and validation
4. **Caching**: Add response caching to reduce API calls

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please read the contributing guidelines and submit pull requests for any improvements.
