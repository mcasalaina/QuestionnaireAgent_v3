"""Mock Azure services for testing without Azure dependencies."""

import asyncio
import json
import random
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, AsyncMock
from datetime import datetime


class MockAzureAIAgentClient:
    """Mock implementation of AzureAIAgentClient for testing."""
    
    def __init__(self, project_endpoint: str = None, credential: Any = None, **kwargs):
        """Initialize mock client.
        
        Args:
            project_endpoint: Mock endpoint URL.
            credential: Mock credential.
            **kwargs: Additional arguments.
        """
        self.project_endpoint = project_endpoint or "https://mock-project.services.ai.azure.com"
        self.credential = credential
        self.agents = {}
        self.threads = {}
        self.runs = {}
        self._agent_counter = 0
        self._thread_counter = 0
        self._run_counter = 0
    
    async def create_agent(
        self,
        model: str = "gpt-4.1-mini",
        name: str = "Mock Agent",
        instructions: str = "",
        tools: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a mock agent.
        
        Args:
            model: Model name.
            name: Agent name.
            instructions: Agent instructions.
            tools: Agent tools.
            **kwargs: Additional arguments.
            
        Returns:
            Mock agent object.
        """
        await asyncio.sleep(0.1)  # Simulate network delay
        
        agent_id = f"mock_agent_{self._agent_counter}"
        self._agent_counter += 1
        
        agent = {
            "id": agent_id,
            "object": "assistant",
            "model": model,
            "name": name,
            "instructions": instructions,
            "tools": tools or [],
            "created_at": int(datetime.now().timestamp()),
            "metadata": {}
        }
        
        self.agents[agent_id] = agent
        return agent
    
    async def create_thread(self, **kwargs) -> Dict[str, Any]:
        """Create a mock thread.
        
        Returns:
            Mock thread object.
        """
        await asyncio.sleep(0.05)  # Simulate network delay
        
        thread_id = f"mock_thread_{self._thread_counter}"
        self._thread_counter += 1
        
        thread = {
            "id": thread_id,
            "object": "thread",
            "created_at": int(datetime.now().timestamp()),
            "metadata": {}
        }
        
        self.threads[thread_id] = thread
        return thread
    
    async def create_message(
        self,
        thread_id: str,
        role: str = "user",
        content: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a mock message in a thread.
        
        Args:
            thread_id: Thread identifier.
            role: Message role (user/assistant).
            content: Message content.
            **kwargs: Additional arguments.
            
        Returns:
            Mock message object.
        """
        await asyncio.sleep(0.02)  # Simulate network delay
        
        message = {
            "id": f"mock_msg_{random.randint(1000, 9999)}",
            "object": "thread.message",
            "thread_id": thread_id,
            "role": role,
            "content": [{"type": "text", "text": {"value": content}}],
            "created_at": int(datetime.now().timestamp()),
            "metadata": {}
        }
        
        return message
    
    async def create_run(
        self,
        thread_id: str,
        assistant_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a mock run.
        
        Args:
            thread_id: Thread identifier.
            assistant_id: Assistant/agent identifier.
            **kwargs: Additional arguments.
            
        Returns:
            Mock run object.
        """
        await asyncio.sleep(0.1)  # Simulate network delay
        
        run_id = f"mock_run_{self._run_counter}"
        self._run_counter += 1
        
        run = {
            "id": run_id,
            "object": "thread.run",
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "status": "in_progress",
            "created_at": int(datetime.now().timestamp()),
            "metadata": {}
        }
        
        self.runs[run_id] = run
        return run
    
    async def get_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Get a mock run status.
        
        Args:
            thread_id: Thread identifier.
            run_id: Run identifier.
            
        Returns:
            Mock run object with updated status.
        """
        await asyncio.sleep(0.05)  # Simulate network delay
        
        run = self.runs.get(run_id, {})
        
        # Simulate run completion after a few checks
        if run.get("status") == "in_progress":
            # Randomly complete the run
            if random.random() > 0.3:  # 70% chance to complete
                run["status"] = "completed"
                run["completed_at"] = int(datetime.now().timestamp())
        
        return run
    
    async def list_messages(self, thread_id: str, **kwargs) -> Dict[str, Any]:
        """List mock messages in a thread.
        
        Args:
            thread_id: Thread identifier.
            **kwargs: Additional arguments.
            
        Returns:
            Mock messages list.
        """
        await asyncio.sleep(0.05)  # Simulate network delay
        
        # Generate mock response based on agent type
        agent_type = kwargs.get("agent_type", "question_answerer")
        
        if agent_type == "question_answerer":
            content = self._generate_mock_answer()
        elif agent_type == "answer_checker":
            content = self._generate_mock_validation()
        elif agent_type == "link_checker":
            content = self._generate_mock_link_check()
        else:
            content = "Mock response from agent."
        
        mock_message = {
            "id": f"mock_msg_response_{random.randint(1000, 9999)}",
            "object": "thread.message",
            "thread_id": thread_id,
            "role": "assistant",
            "content": [{"type": "text", "text": {"value": content}}],
            "created_at": int(datetime.now().timestamp()),
            "metadata": {}
        }
        
        return {
            "object": "list",
            "data": [mock_message],
            "first_id": mock_message["id"],
            "last_id": mock_message["id"],
            "has_more": False
        }
    
    def _generate_mock_answer(self) -> str:
        """Generate a mock answer from Question Answerer agent."""
        answers = [
            "Azure AI supports various video generation capabilities through Azure OpenAI Service and Azure Cognitive Services. "
            "You can use models like DALL-E for image generation and combine with video synthesis tools. "
            "For more information, see: https://docs.microsoft.com/azure/ai-services/openai/",
            
            "Microsoft Azure provides comprehensive AI services including machine learning, cognitive services, and OpenAI integration. "
            "The platform offers scalable solutions for businesses of all sizes. "
            "Learn more at: https://azure.microsoft.com/services/machine-learning/",
            
            "Azure AI Foundry is a unified platform for building, deploying, and managing AI applications. "
            "It provides tools for model fine-tuning, prompt engineering, and responsible AI practices. "
            "Documentation: https://docs.microsoft.com/azure/ai-foundry/"
        ]
        return random.choice(answers)
    
    def _generate_mock_validation(self) -> str:
        """Generate a mock validation response from Answer Checker agent."""
        validations = [
            "APPROVED: The answer provides accurate information about Azure AI services with proper documentation links.",
            "REJECTED: The answer contains outdated information. Please provide current Azure AI capabilities.",
            "APPROVED: Content is factually correct and within character limits. Links are relevant to the topic."
        ]
        return random.choice(validations)
    
    def _generate_mock_link_check(self) -> str:
        """Generate a mock link validation response from Link Checker agent."""
        link_checks = [
            "LINKS_VALID: All documentation links are accessible and relevant to Azure AI services.",
            "LINKS_INVALID: Found 1 broken link. Please replace with current documentation URLs.",
            "LINKS_VALID: All Microsoft documentation links verified and content is relevant."
        ]
        return random.choice(link_checks)
    
    async def delete_agent(self, agent_id: str) -> None:
        """Delete a mock agent.
        
        Args:
            agent_id: Agent identifier to delete.
        """
        await asyncio.sleep(0.02)
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    async def delete_thread(self, thread_id: str) -> None:
        """Delete a mock thread.
        
        Args:
            thread_id: Thread identifier to delete.
        """
        await asyncio.sleep(0.02)
        if thread_id in self.threads:
            del self.threads[thread_id]


class MockDefaultAzureCredential:
    """Mock implementation of DefaultAzureCredential for testing."""
    
    def __init__(self, exclude_interactive_browser_credential: bool = False):
        """Initialize mock credential.
        
        Args:
            exclude_interactive_browser_credential: Whether to exclude browser auth.
        """
        self.exclude_interactive = exclude_interactive_browser_credential
    
    async def get_token(self, *args, **kwargs):
        """Mock token retrieval.
        
        Returns:
            Mock access token.
        """
        await asyncio.sleep(0.1)  # Simulate auth delay
        
        mock_token = Mock()
        mock_token.token = "mock_access_token_" + str(random.randint(10000, 99999))
        mock_token.expires_on = datetime.now().timestamp() + 3600  # 1 hour
        
        return mock_token


class MockInteractiveBrowserCredential:
    """Mock implementation of InteractiveBrowserCredential for testing."""
    
    def __init__(self, **kwargs):
        """Initialize mock interactive credential."""
        pass
    
    async def get_token(self, *args, **kwargs):
        """Mock interactive token retrieval.
        
        Returns:
            Mock access token.
        """
        await asyncio.sleep(0.2)  # Simulate browser auth delay
        
        mock_token = Mock()
        mock_token.token = "mock_interactive_token_" + str(random.randint(10000, 99999))
        mock_token.expires_on = datetime.now().timestamp() + 3600  # 1 hour
        
        return mock_token


def create_mock_azure_client(**kwargs) -> MockAzureAIAgentClient:
    """Create a mock Azure AI Agent client for testing.
    
    Args:
        **kwargs: Client configuration arguments.
        
    Returns:
        Mock client instance.
    """
    return MockAzureAIAgentClient(**kwargs)


def create_mock_credential(interactive: bool = False):
    """Create a mock Azure credential for testing.
    
    Args:
        interactive: Whether to create interactive credential.
        
    Returns:
        Mock credential instance.
    """
    if interactive:
        return MockInteractiveBrowserCredential()
    else:
        return MockDefaultAzureCredential()


class MockPlaywrightBrowser:
    """Mock Playwright browser for link checking tests."""
    
    def __init__(self):
        """Initialize mock browser."""
        self.pages = []
    
    async def new_page(self):
        """Create a mock page."""
        page = MockPlaywrightPage()
        self.pages.append(page)
        return page
    
    async def close(self):
        """Close mock browser."""
        self.pages.clear()


class MockPlaywrightPage:
    """Mock Playwright page for URL testing."""
    
    def __init__(self):
        """Initialize mock page."""
        self.status = 200
        self.title = "Mock Page Title"
    
    async def goto(self, url: str, **kwargs):
        """Mock navigation to URL.
        
        Args:
            url: Target URL.
            **kwargs: Additional arguments.
            
        Returns:
            Mock response.
        """
        await asyncio.sleep(0.1)  # Simulate page load
        
        # Simulate different responses based on URL
        if "broken" in url or "404" in url:
            self.status = 404
            self.title = "Page Not Found"
        elif "timeout" in url:
            await asyncio.sleep(5)  # Simulate timeout
            raise Exception("Navigation timeout")
        else:
            self.status = 200
            self.title = "Azure Documentation - Microsoft Docs"
        
        mock_response = Mock()
        mock_response.status = self.status
        return mock_response
    
    async def title(self):
        """Get mock page title."""
        return self.title
    
    async def close(self):
        """Close mock page."""
        pass


def create_mock_playwright_browser() -> MockPlaywrightBrowser:
    """Create a mock Playwright browser for testing.
    
    Returns:
        Mock browser instance.
    """
    return MockPlaywrightBrowser()