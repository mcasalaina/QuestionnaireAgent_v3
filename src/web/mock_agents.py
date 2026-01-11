"""Mock agent coordinator for web server testing.

Provides fast mock responses for testing the web interface without requiring
Azure AI services or real agent processing.
"""

import asyncio
import logging
import random
import time
from typing import Callable, List, Optional

from utils.data_types import (
    Question, Answer, ProcessingResult, AgentStep, AgentType,
    ValidationStatus, StepStatus
)

logger = logging.getLogger(__name__)


# Sample documentation links for mock responses
MOCK_DOCUMENTATION_LINKS = [
    "https://docs.microsoft.com/azure/ai-services/openai/",
    "https://learn.microsoft.com/azure/cognitive-services/",
    "https://docs.microsoft.com/azure/machine-learning/",
    "https://docs.microsoft.com/azure/ai-foundry/",
    "https://learn.microsoft.com/azure/architecture/ai-ml/",
]

# Sample mock answers with documentation
MOCK_ANSWERS = [
    {
        "content": "Azure AI services provide comprehensive machine learning and artificial intelligence capabilities. The platform offers pre-built AI models for vision, speech, language, and decision-making tasks. Azure OpenAI Service provides access to advanced language models like GPT-4 for text generation, code completion, and natural language understanding.",
        "links": [
            "https://docs.microsoft.com/azure/ai-services/openai/",
            "https://docs.microsoft.com/azure/cognitive-services/"
        ]
    },
    {
        "content": "Microsoft Azure offers a wide range of cloud computing services including virtual machines, storage, networking, and AI/ML capabilities. Azure AI Foundry provides a unified platform for building, training, and deploying AI models. The platform supports both managed AI services and custom model development.",
        "links": [
            "https://docs.microsoft.com/azure/ai-foundry/",
            "https://learn.microsoft.com/azure/machine-learning/"
        ]
    },
    {
        "content": "Azure Cognitive Services provides AI models as APIs for vision, speech, language, and search capabilities. These pre-built models can be integrated into applications without requiring machine learning expertise. Services include Computer Vision, Speech Services, Language Understanding (LUIS), and Azure Search.",
        "links": [
            "https://docs.microsoft.com/azure/cognitive-services/",
            "https://learn.microsoft.com/azure/architecture/ai-ml/"
        ]
    },
    {
        "content": "Azure Machine Learning is a cloud-based service for training, deploying, and managing machine learning models at scale. It supports automated ML, MLOps practices, and integration with popular frameworks like TensorFlow and PyTorch. The service provides tools for both no-code and code-first approaches.",
        "links": [
            "https://docs.microsoft.com/azure/machine-learning/",
            "https://docs.microsoft.com/azure/ai-foundry/"
        ]
    },
    {
        "content": "Azure AI Document Intelligence (formerly Form Recognizer) uses AI to extract text, key-value pairs, tables, and structures from documents. It supports various document types including invoices, receipts, and custom forms. The service can be customized for specific document layouts.",
        "links": [
            "https://docs.microsoft.com/azure/ai-services/document-intelligence/",
            "https://learn.microsoft.com/azure/cognitive-services/"
        ]
    }
]


class MockAgentCoordinator:
    """Mock agent coordinator that returns fast test responses.

    Simulates the multi-agent workflow with realistic delays and
    provides meaningful mock responses with documentation links.
    """

    def __init__(self):
        """Initialize the mock agent coordinator."""
        self.executors_created = True  # Already "created"
        self._response_index = 0
        logger.info("MockAgentCoordinator initialized")

    async def create_agents(self) -> None:
        """Mock agent creation - no-op since already initialized."""
        logger.info("Mock agents already created")
        self.executors_created = True

    async def process_question(
        self,
        question: Question,
        progress_callback: Callable[[str, str, float], None],
        reasoning_callback: Optional[Callable[[str], None]] = None,
        agent_conversation_callback: Optional[Callable] = None
    ) -> ProcessingResult:
        """Process a question using mock agents.

        Simulates the multi-agent workflow with realistic delays (0.1-0.5s total)
        and returns meaningful mock responses with documentation links.

        Args:
            question: Question to process
            progress_callback: Progress update callback
            reasoning_callback: Reasoning update callback
            agent_conversation_callback: Agent conversation callback

        Returns:
            ProcessingResult with mock answer
        """
        start_time = time.time()
        agent_steps = []

        # Simulate Question Answerer agent
        progress_callback("question_answerer", "Searching for relevant information...", 0.1)
        if reasoning_callback:
            reasoning_callback("Question Answerer: Analyzing question and searching web...")
        await asyncio.sleep(random.uniform(0.05, 0.15))

        agent_steps.append(AgentStep(
            agent_name=AgentType.QUESTION_ANSWERER,
            input_data=question.text,
            output_data="Generated initial answer",
            execution_time=0.1,
            status=StepStatus.SUCCESS
        ))

        # Simulate Answer Checker agent
        progress_callback("answer_checker", "Validating answer accuracy...", 0.5)
        if reasoning_callback:
            reasoning_callback("Answer Checker: Verifying factual accuracy...")
        await asyncio.sleep(random.uniform(0.05, 0.15))

        agent_steps.append(AgentStep(
            agent_name=AgentType.ANSWER_CHECKER,
            input_data="Initial answer",
            output_data="APPROVED: Answer is accurate",
            execution_time=0.1,
            status=StepStatus.SUCCESS
        ))

        # Simulate Link Checker agent
        progress_callback("link_checker", "Verifying documentation links...", 0.8)
        if reasoning_callback:
            reasoning_callback("Link Checker: Validating all URLs...")
        await asyncio.sleep(random.uniform(0.05, 0.2))

        agent_steps.append(AgentStep(
            agent_name=AgentType.LINK_CHECKER,
            input_data="Answer with links",
            output_data="LINKS_VALID: All links verified",
            execution_time=0.1,
            status=StepStatus.SUCCESS
        ))

        # Get mock answer (rotate through available answers)
        mock_data = MOCK_ANSWERS[self._response_index % len(MOCK_ANSWERS)]
        self._response_index += 1

        # Create documentation links as strings (the expected format for documentation_links in Answer)
        doc_links = mock_data["links"]

        # Create answer - documentation_links should be a list of strings (URLs)
        answer = Answer(
            content=mock_data["content"],
            sources=mock_data["links"],
            agent_reasoning=agent_steps,
            validation_status=ValidationStatus.APPROVED,
            retry_count=0,
            documentation_links=doc_links
        )

        processing_time = time.time() - start_time

        progress_callback("workflow", "Processing complete!", 1.0)
        if reasoning_callback:
            reasoning_callback(f"Completed in {processing_time:.2f}s")

        logger.info(f"Mock question processed in {processing_time:.2f}s")

        return ProcessingResult(
            success=True,
            answer=answer,
            processing_time=processing_time,
            questions_processed=1,
            questions_failed=0
        )

    async def cleanup_agents(self) -> None:
        """Mock cleanup - no-op."""
        logger.info("Mock agents cleanup (no-op)")


async def create_mock_agent_coordinator() -> MockAgentCoordinator:
    """Create a mock agent coordinator for testing.

    Returns:
        MockAgentCoordinator instance ready for use
    """
    coordinator = MockAgentCoordinator()
    await coordinator.create_agents()
    return coordinator
