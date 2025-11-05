"""Unit tests for Yandex Tracker client"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.tracker.tracker_client import TrackerClient, TrackerTask


@pytest.fixture
def tracker_config():
    """Tracker configuration fixture"""
    return {
        "token": "test_token",
        "org_id": "test_org",
        "queue": "VOICEBOT"
    }


@pytest.fixture
def tracker_client(tracker_config):
    """TrackerClient fixture"""
    return TrackerClient(
        token=tracker_config["token"],
        org_id=tracker_config["org_id"],
        queue=tracker_config["queue"]
    )


@pytest.mark.asyncio
async def test_create_task(tracker_client):
    """Test creating a task in Yandex Tracker"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={
            "key": "VOICEBOT-1",
            "id": "12345",
            "summary": "Test Task",
            "status": {"key": "open"}
        })
        mock_post.return_value.__aenter__.return_value = mock_response

        task = await tracker_client.create_task(
            summary="Test Task",
            description="Test Description",
            priority="normal"
        )

        assert task.key == "VOICEBOT-1"
        assert task.summary == "Test Task"
        assert task.status == "open"


@pytest.mark.asyncio
async def test_update_task_status(tracker_client):
    """Test updating task status"""
    with patch('aiohttp.ClientSession.patch') as mock_patch:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "key": "VOICEBOT-1",
            "status": {"key": "testing"}
        })
        mock_patch.return_value.__aenter__.return_value = mock_response

        result = await tracker_client.update_task_status("VOICEBOT-1", "testing")

        assert result is True


@pytest.mark.asyncio
async def test_add_comment(tracker_client):
    """Test adding comment to task"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={
            "id": "comment123",
            "text": "Test comment"
        })
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await tracker_client.add_comment("VOICEBOT-1", "Test comment")

        assert result is True


@pytest.mark.asyncio
async def test_get_tasks_by_status(tracker_client):
    """Test getting tasks by status"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {
                "key": "VOICEBOT-1",
                "id": "1",
                "summary": "Task 1",
                "status": {"key": "testing"}
            },
            {
                "key": "VOICEBOT-2",
                "id": "2",
                "summary": "Task 2",
                "status": {"key": "testing"}
            }
        ])
        mock_get.return_value.__aenter__.return_value = mock_response

        tasks = await tracker_client.get_tasks_by_status("testing")

        assert len(tasks) == 2
        assert tasks[0].key == "VOICEBOT-1"
        assert tasks[1].key == "VOICEBOT-2"


@pytest.mark.asyncio
async def test_handle_api_error(tracker_client):
    """Test handling API errors"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(Exception):
            await tracker_client.create_task("Test", "Desc")


@pytest.mark.asyncio
async def test_link_commit(tracker_client):
    """Test linking commit to task"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await tracker_client.link_commit("VOICEBOT-1", "abc123", "feat: Add feature")

        assert result is True


def test_tracker_task_model():
    """Test TrackerTask dataclass"""
    task = TrackerTask(
        key="VOICEBOT-1",
        id="12345",
        summary="Test",
        status="open",
        description="Desc"
    )

    assert task.key == "VOICEBOT-1"
    assert task.id == "12345"
    assert task.status == "open"
