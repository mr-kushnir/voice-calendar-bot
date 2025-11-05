"""Unit tests for Task Manager"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.tracker.task_manager import TaskManager, FeatureTask


@pytest.fixture
def mock_tracker_client():
    """Mock TrackerClient fixture"""
    client = Mock()
    client.create_task = AsyncMock()
    client.get_tasks_by_status = AsyncMock()
    return client


@pytest.fixture
def task_manager(mock_tracker_client):
    """TaskManager fixture"""
    return TaskManager(mock_tracker_client)


@pytest.mark.asyncio
async def test_create_feature_tasks(task_manager, mock_tracker_client):
    """Test creating all MVP feature tasks"""
    from src.tracker.tracker_client import TrackerTask

    # Mock responses for task creation
    mock_tracker_client.create_task.return_value = TrackerTask(
        key="VOICEBOT-1",
        id="1",
        summary="Test Task",
        status="open"
    )

    tasks = await task_manager.create_feature_tasks()

    # Should create 19 tasks according to development plan
    assert mock_tracker_client.create_task.call_count == 19
    assert len(tasks) == 19


@pytest.mark.asyncio
async def test_get_testing_tasks(task_manager, mock_tracker_client):
    """Test getting tasks in testing status"""
    from src.tracker.tracker_client import TrackerTask

    mock_tracker_client.get_tasks_by_status.return_value = [
        TrackerTask(key="VOICEBOT-5", id="5", summary="Voice STT", status="testing"),
        TrackerTask(key="VOICEBOT-6", id="6", summary="Voice TTS", status="testing")
    ]

    tasks = await task_manager.get_testing_tasks()

    assert len(tasks) == 2
    assert tasks[0].key == "VOICEBOT-5"
    mock_tracker_client.get_tasks_by_status.assert_called_once_with("testing")


@pytest.mark.asyncio
async def test_extract_module_from_task(task_manager):
    """Test extracting module name from task summary"""
    from src.tracker.tracker_client import TrackerTask

    task = TrackerTask(
        key="VOICEBOT-5",
        id="5",
        summary="Voice STT Service",
        status="testing"
    )

    module = task_manager.extract_module_from_task(task)

    # Should extract relevant module path
    assert "voice" in module.lower() or "stt" in module.lower()


def test_feature_task_dataclass():
    """Test FeatureTask dataclass"""
    task = FeatureTask(
        key="VOICEBOT-1",
        title="Project Setup",
        description="Initialize project structure",
        priority="critical",
        estimate="5 min"
    )

    assert task.key == "VOICEBOT-1"
    assert task.priority == "critical"
    assert task.estimate == "5 min"
