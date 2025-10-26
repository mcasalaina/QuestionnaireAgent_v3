"""Unit tests for agent pre-initialization functionality."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add src directory to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Mock tkinter before importing UIManager
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

from utils.data_types import Question, ProcessingResult, Answer, ValidationStatus


class TestAgentPreinitialization:
    """Test agent pre-initialization at startup."""
    
    def test_agent_init_state_tracking(self):
        """Test that agent initialization state is properly tracked."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            
            # Initially should be "not_started"
            assert ui_manager.agent_init_state == "not_started"
            assert ui_manager.agent_init_error is None
    
    @pytest.mark.asyncio
    async def test_ensure_agents_ready_when_already_initialized(self):
        """Test _ensure_agents_ready returns immediately when agents already initialized."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            ui_manager.agent_coordinator = Mock()  # Already initialized
            
            # Should return immediately without error
            await ui_manager._ensure_agents_ready()
            
            # State should still be not_started since we bypassed initialization
            assert ui_manager.agent_init_state == "not_started"
    
    @pytest.mark.asyncio
    async def test_ensure_agents_ready_waits_during_initialization(self):
        """Test _ensure_agents_ready waits when initialization is in progress."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            ui_manager.agent_init_state = "in_progress"
            
            # Simulate initialization completing after a delay
            async def simulate_init_complete():
                await asyncio.sleep(0.1)
                ui_manager.agent_init_state = "completed"
                ui_manager.agent_coordinator = Mock()
            
            # Start simulation in background
            asyncio.create_task(simulate_init_complete())
            
            # Should wait for initialization to complete
            await ui_manager._ensure_agents_ready()
            
            assert ui_manager.agent_init_state == "completed"
            assert ui_manager.agent_coordinator is not None
    
    @pytest.mark.asyncio
    async def test_ensure_agents_ready_raises_on_failed_initialization(self):
        """Test _ensure_agents_ready raises exception when initialization failed."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            ui_manager.agent_init_state = "failed"
            ui_manager.agent_init_error = "Test error message"
            
            # Should raise exception
            with pytest.raises(Exception, match="Test error message"):
                await ui_manager._ensure_agents_ready()
    
    @pytest.mark.asyncio
    async def test_process_question_waits_for_agents(self):
        """Test that _process_question_internal waits for agents to be ready."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            
            # Mock the coordinator with a successful response
            mock_coordinator = AsyncMock()
            mock_coordinator.process_question.return_value = ProcessingResult(
                success=True,
                answer=Answer(content="Test answer", validation_status=ValidationStatus.APPROVED),
                processing_time=1.0,
                questions_processed=1,
                questions_failed=0
            )
            
            # Simulate agents becoming ready
            ui_manager.agent_init_state = "completed"
            ui_manager.agent_coordinator = mock_coordinator
            
            # Mock the update methods
            ui_manager.update_reasoning = Mock()
            ui_manager.update_progress = Mock()
            
            # Process a question
            result = await ui_manager._process_question_internal("Test question?")
            
            # Should succeed
            assert result.success is True
            assert mock_coordinator.process_question.called
    
    @pytest.mark.asyncio
    async def test_process_question_handles_agent_init_failure(self):
        """Test that _process_question_internal handles agent initialization failure."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            ui_manager.agent_init_state = "failed"
            ui_manager.agent_init_error = "Agent creation failed"
            
            # Mock the update methods
            ui_manager.update_reasoning = Mock()
            
            # Process a question
            result = await ui_manager._process_question_internal("Test question?")
            
            # Should return failed result
            assert result.success is False
            assert "Agent initialization failed" in result.error_message
            assert result.questions_failed == 1
    
    def test_start_agent_initialization_only_runs_once(self):
        """Test that _start_agent_initialization only runs once."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            ui_manager.status_manager = Mock()
            ui_manager.root = Mock()
            
            # Mock threading.Thread to track calls
            with patch('ui.main_window.threading.Thread') as mock_thread:
                # First call should start initialization
                ui_manager._start_agent_initialization()
                assert mock_thread.called
                
                # Reset mock
                mock_thread.reset_mock()
                
                # Second call should not start again (state is "in_progress")
                ui_manager._start_agent_initialization()
                assert not mock_thread.called
    
    def test_start_agent_initialization_with_existing_coordinator(self):
        """Test that _start_agent_initialization does nothing if coordinator already exists."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            ui_manager.agent_coordinator = Mock()  # Already initialized
            
            with patch('ui.main_window.threading.Thread') as mock_thread:
                ui_manager._start_agent_initialization()
                # Should not start initialization
                assert not mock_thread.called


class TestAgentInitializationCallbacks:
    """Test agent initialization success/error callbacks."""
    
    def test_handle_agent_init_success_updates_state(self):
        """Test that _handle_agent_init_success updates state correctly."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            ui_manager.status_manager = Mock()
            ui_manager.root = Mock()
            
            mock_coordinator = Mock()
            ui_manager._handle_agent_init_success(mock_coordinator)
            
            assert ui_manager.agent_coordinator == mock_coordinator
            assert ui_manager.agent_init_state == "completed"
            assert ui_manager.status_manager.set_status.called
    
    def test_handle_agent_init_error_updates_state(self):
        """Test that _handle_agent_init_error updates state correctly."""
        from ui.main_window import UIManager
        
        with patch.object(UIManager, 'setup_ui'):
            ui_manager = UIManager()
            ui_manager.status_manager = Mock()
            ui_manager.root = Mock()
            
            test_error = Exception("Test initialization error")
            ui_manager._handle_agent_init_error(test_error)
            
            assert ui_manager.agent_init_state == "failed"
            assert ui_manager.agent_init_error == "Test initialization error"
            assert ui_manager.status_manager.set_status.called


