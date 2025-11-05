"""Unit tests for Test Agent"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from src.agents.test_agent import TestAgent as AgentClass
from src.tracker.tracker_client import TrackerTask


@pytest.fixture
def mock_tracker():
    """Mock tracker client"""
    tracker = AsyncMock()
    tracker.get_tasks_by_status = AsyncMock(return_value=[])
    tracker.add_comment = AsyncMock(return_value=True)
    tracker.update_task_status = AsyncMock(return_value=True)
    return tracker


@pytest.fixture
def agent_instance(mock_tracker):
    """Test agent fixture"""
    return AgentClass(
        tracker_client=mock_tracker,
        project_root=Path("/fake/project"),
        poll_interval=1,
        coverage_threshold=80
    )


@pytest.fixture
def sample_task():
    """Sample tracker task"""
    return TrackerTask(
        key="EXTEST-11",
        id="12345",
        summary="Test Task",
        status="inProgress"
    )


def test_test_agent_initialization(agent_instance):
    """Test TestAgent initialization"""
    assert agent_instance.poll_interval == 1
    assert agent_instance.coverage_threshold == 80
    assert agent_instance.running == False


@pytest.mark.asyncio
async def test_get_tasks_for_testing(agent_instance, mock_tracker, sample_task):
    """Test getting tasks for testing"""
    mock_tracker.get_tasks_by_status.return_value = [sample_task]

    tasks = await agent_instance._get_tasks_for_testing()

    assert len(tasks) == 1
    assert tasks[0].key == "EXTEST-11"
    mock_tracker.get_tasks_by_status.assert_called_once_with("inProgress")


@pytest.mark.asyncio
async def test_get_tasks_for_testing_filters_unmapped(agent_instance, mock_tracker):
    """Test that tasks without test mappings are filtered out"""
    unmapped_task = TrackerTask(
        key="EXTEST-999",
        id="99999",
        summary="Unmapped Task",
        status="inProgress"
    )

    mock_tracker.get_tasks_by_status.return_value = [unmapped_task]

    tasks = await agent_instance._get_tasks_for_testing()

    assert len(tasks) == 0


def test_extract_coverage(agent_instance):
    """Test coverage extraction from pytest output"""
    output = """
    tests/unit/test_models.py::test_event_creation PASSED [ 50%]
    tests/unit/test_models.py::test_command_creation PASSED [100%]

    ----------- coverage: platform win32, python 3.12.3 -----------
    Name                                     Stmts   Miss  Cover
    ----------------------------------------------------------------
    src/__init__.py                              0      0   100%
    src/models.py                               50      5    90%
    ----------------------------------------------------------------
    TOTAL                                      200     20    81%
    """

    coverage = agent_instance._extract_coverage(output)
    assert coverage == 81


def test_extract_coverage_not_found(agent_instance):
    """Test coverage extraction when not found"""
    output = "No coverage data"

    coverage = agent_instance._extract_coverage(output)
    assert coverage is None


@pytest.mark.asyncio
async def test_handle_test_success(agent_instance, mock_tracker, sample_task):
    """Test handling successful test result"""
    await agent_instance._handle_test_success(sample_task)

    # Should add comment and close task
    mock_tracker.add_comment.assert_called_once()
    comment_call = mock_tracker.add_comment.call_args[0]
    assert "успешно пройдены" in comment_call[1]

    mock_tracker.update_task_status.assert_called_once_with("EXTEST-11", "closed")


@pytest.mark.asyncio
async def test_handle_test_failure(agent_instance, mock_tracker, sample_task):
    """Test handling failed test result"""
    test_result = {
        "success": False,
        "exit_code": 1,
        "output": "Test failed",
        "coverage": 75
    }

    await agent_instance._handle_test_failure(sample_task, test_result)

    # Should add comment and return to open status
    mock_tracker.add_comment.assert_called_once()
    comment_call = mock_tracker.add_comment.call_args[0]
    assert "не прошли" in comment_call[1]
    assert "75%" in comment_call[1]

    mock_tracker.update_task_status.assert_called_once_with("EXTEST-11", "stop_progress")


@pytest.mark.asyncio
async def test_handle_test_error(agent_instance, mock_tracker, sample_task):
    """Test handling test error"""
    error_message = "Unexpected error occurred"

    await agent_instance._handle_test_error(sample_task, error_message)

    # Should add error comment
    mock_tracker.add_comment.assert_called_once()
    comment_call = mock_tracker.add_comment.call_args[0]
    assert "Ошибка при тестировании" in comment_call[1]
    assert error_message in comment_call[1]

    # Should NOT change task status
    mock_tracker.update_task_status.assert_not_called()


@pytest.mark.asyncio
async def test_test_task_no_tests(agent_instance, mock_tracker):
    """Test task with no test mapping"""
    task = TrackerTask(
        key="EXTEST-7",  # Has no tests
        id="12345",
        summary="Project Structure",
        status="inProgress"
    )

    await agent_instance._test_task(task)

    # Should handle as success since no tests to run
    mock_tracker.add_comment.assert_called_once()
    mock_tracker.update_task_status.assert_called_once_with("EXTEST-7", "closed")


@pytest.mark.asyncio
async def test_run_tests_success(agent_instance):
    """Test running tests successfully"""
    with patch('subprocess.run') as mock_run:
        # Mock successful test run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "TOTAL ... 85%"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = await agent_instance._run_tests("tests/unit/test_models.py")

        assert result["success"] == True
        assert result["exit_code"] == 0
        assert result["coverage"] == 85


@pytest.mark.asyncio
async def test_run_tests_failure(agent_instance):
    """Test running tests with failure"""
    with patch('subprocess.run') as mock_run:
        # Mock failed test run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "1 failed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = await agent_instance._run_tests("tests/unit/test_models.py")

        assert result["success"] == False
        assert result["exit_code"] == 1


@pytest.mark.asyncio
async def test_run_tests_low_coverage(agent_instance):
    """Test running tests with low coverage"""
    with patch('subprocess.run') as mock_run:
        # Mock test run with low coverage
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "TOTAL ... 70%"  # Below threshold of 80%
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = await agent_instance._run_tests("tests/unit/test_models.py")

        # Should fail due to low coverage
        assert result["success"] == False
        assert result["coverage"] == 70
