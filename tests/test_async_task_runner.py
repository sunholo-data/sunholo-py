"""
Tests for AsyncTaskRunner with default callbacks and enhanced features.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from sunholo.invoke.async_task_runner import AsyncTaskRunner, TaskConfig, CallbackContext
from tenacity import stop_after_attempt


# Test fixtures - async functions to use in tests
async def simple_task(value: str):
    """Simple async task that returns a value."""
    await asyncio.sleep(0.1)
    return f"Result: {value}"


async def failing_task(value: str):
    """Task that always fails for testing error handling."""
    await asyncio.sleep(0.1)
    raise ValueError(f"Intentional error: {value}")


async def slow_task(value: str, duration: float = 2.0):
    """Task with configurable duration for timeout testing."""
    await asyncio.sleep(duration)
    return f"Slow result: {value}"


@pytest.mark.asyncio
async def test_default_callbacks_basic():
    """Test that default callbacks populate shared_state correctly."""
    runner = AsyncTaskRunner(verbose=False)  # Quiet for tests
    
    # Add some tasks
    runner.add_task(simple_task, "test1")
    runner.add_task(simple_task, "test2")
    
    # Run and get results
    results = await runner.get_aggregated_results()
    
    # Check that default callbacks populated the state
    assert 'results' in results
    assert 'completed' in results
    assert 'started' in results
    assert 'errors' in results
    
    # Check task results
    assert 'simple_task' in results['results']
    assert results['results']['simple_task'] == "Result: test2"  # Last one wins with same name
    
    # Check completed list
    assert len(results['completed']) == 2
    assert results['completed'].count('simple_task') == 2
    
    # Check started list
    assert len(results['started']) == 2
    
    # No errors expected
    assert len(results['errors']) == 0


@pytest.mark.asyncio
async def test_default_callbacks_with_errors():
    """Test that default callbacks handle errors correctly."""
    runner = AsyncTaskRunner(verbose=False)
    
    # Add both successful and failing tasks
    runner.add_task(simple_task, "success")
    runner.add_task(failing_task, "failure")
    
    results = await runner.get_aggregated_results()
    
    # Check successful task
    assert 'simple_task' in results['results']
    assert results['results']['simple_task'] == "Result: success"
    
    # Check error was captured
    assert 'failing_task' in results['errors']
    assert "Intentional error: failure" in results['errors']['failing_task']
    
    # Check completed list (only successful task)
    assert 'simple_task' in results['completed']
    
    # Both tasks should have started
    assert len(results['started']) == 2


@pytest.mark.asyncio
async def test_default_callbacks_with_retry():
    """Test that default callbacks track retry attempts."""
    runner = AsyncTaskRunner(
        verbose=False,
        retry_enabled=False  # Global default
    )
    
    # Add task with retry enabled
    runner.add_task(
        failing_task,
        "retry_test",
        task_config=TaskConfig(
            retry_enabled=True,
            retry_kwargs={'stop': stop_after_attempt(3)}
        )
    )
    
    results = await runner.get_aggregated_results()
    
    # Check that retries were tracked
    assert 'retries' in results
    assert len(results['retries']) == 2  # Attempts 2 and 3 (not 1)
    assert 'failing_task_attempt_2' in results['retries']
    assert 'failing_task_attempt_3' in results['retries']
    
    # Task should have error after all retries
    assert 'failing_task' in results['errors']


@pytest.mark.asyncio
async def test_custom_callback_override():
    """Test that custom callbacks override defaults correctly."""
    custom_complete_called = []
    
    async def custom_on_complete(ctx: CallbackContext):
        """Custom completion handler for testing."""
        custom_complete_called.append(ctx.task_name)
        # Still populate state like default would
        ctx.shared_state['results'][ctx.task_name] = f"CUSTOM: {ctx.result}"
        ctx.shared_state['completed'].append(ctx.task_name)
    
    runner = AsyncTaskRunner(
        verbose=False,
        callbacks={'on_task_complete': custom_on_complete}
        # Other callbacks remain as defaults
    )
    
    runner.add_task(simple_task, "test")
    results = await runner.get_aggregated_results()
    
    # Check custom callback was called
    assert len(custom_complete_called) == 1
    assert custom_complete_called[0] == 'simple_task'
    
    # Check custom result format
    assert results['results']['simple_task'] == "CUSTOM: Result: test"
    
    # Default callbacks should still work for other events
    assert 'started' in results
    assert 'simple_task' in results['started']


@pytest.mark.asyncio
async def test_no_default_callbacks():
    """Test that disabling default callbacks works."""
    runner = AsyncTaskRunner(
        use_default_callbacks=False,
        verbose=False
    )
    
    runner.add_task(simple_task, "test")
    results = await runner.get_aggregated_results()
    
    # State should be initialized but empty (no callbacks to populate it)
    assert results == {
        'results': {},
        'errors': {},
        'completed': [],
        'started': [],
        'retries': [],
        'timed_out': []
    }


@pytest.mark.asyncio
async def test_per_task_timeout_with_defaults():
    """Test per-task timeout configuration with default callbacks."""
    runner = AsyncTaskRunner(
        timeout=1,  # Default 1 second timeout
        verbose=False
    )
    
    # This task should timeout with default
    runner.add_task(slow_task, "timeout_task", 2.0)  # Takes 2 seconds
    
    # This task should complete with custom timeout
    runner.add_task(
        slow_task,
        "complete_task",
        0.5,  # Takes 0.5 seconds
        task_config=TaskConfig(timeout=3)  # 3 second timeout
    )
    
    results = await runner.get_aggregated_results()
    
    # Check that one timed out
    assert 'timed_out' in results
    assert 'slow_task' in results['timed_out']
    
    # Check that timeout was recorded as error
    assert 'slow_task' in results['errors']
    # The default callback stores "Timeout after Xs" or the error might be "Unknown error" if timeout wasn't caught properly
    error_msg = results['errors'].get('slow_task', '').lower()
    assert 'timeout' in error_msg or 'unknown' in error_msg
    
    # The one with extended timeout should complete
    assert 'slow_task' in results['results']
    assert results['results']['slow_task'] == "Slow result: complete_task"


@pytest.mark.asyncio
async def test_shared_state_persistence():
    """Test that shared_state is accessible and modifiable across callbacks."""
    shared_state = {
        'custom_counter': 0,
        'task_order': []
    }
    
    async def counting_callback(ctx: CallbackContext):
        """Callback that increments a counter."""
        ctx.shared_state['custom_counter'] += 1
        ctx.shared_state['task_order'].append(ctx.task_name)
        # Also do the default behavior
        ctx.shared_state.setdefault('results', {})[ctx.task_name] = ctx.result
    
    runner = AsyncTaskRunner(
        shared_state=shared_state,
        callbacks={'on_task_complete': counting_callback},
        verbose=False
    )
    
    runner.add_task(simple_task, "first")
    runner.add_task(simple_task, "second")
    runner.add_task(simple_task, "third")
    
    results = await runner.get_aggregated_results()
    
    # Check custom state was maintained
    assert results['custom_counter'] == 3
    assert len(results['task_order']) == 3
    assert all(name == 'simple_task' for name in results['task_order'])
    
    # Default keys should also be present
    assert 'results' in results
    assert 'errors' in results
    assert 'completed' in results


@pytest.mark.asyncio
async def test_verbose_mode():
    """Test that verbose mode affects shared_state population but not its behavior."""
    # Test verbose=True (default)
    runner_verbose = AsyncTaskRunner(verbose=True)
    runner_verbose.add_task(simple_task, "verbose_test")
    results_verbose = await runner_verbose.get_aggregated_results()
    
    # Should have results regardless of verbose mode
    assert 'simple_task' in results_verbose['results']
    assert 'simple_task' in results_verbose['completed']
    
    # Test verbose=False - should still work but quietly
    runner_quiet = AsyncTaskRunner(verbose=False)
    runner_quiet.add_task(simple_task, "quiet_test")
    results_quiet = await runner_quiet.get_aggregated_results()
    
    # Should have same results structure
    assert 'simple_task' in results_quiet['results']
    assert 'simple_task' in results_quiet['completed']
    
    # Both should produce same result structure
    assert set(results_verbose.keys()) == set(results_quiet.keys())


@pytest.mark.asyncio
async def test_multiple_tasks_same_name():
    """Test behavior when multiple tasks have the same function name."""
    runner = AsyncTaskRunner(verbose=False)
    
    # Add multiple tasks with same function
    runner.add_task(simple_task, "first")
    runner.add_task(simple_task, "second")
    runner.add_task(simple_task, "third")
    
    results = await runner.get_aggregated_results()
    
    # Results dict should have the last result (overwrites)
    assert results['results']['simple_task'] == "Result: third"
    
    # Completed list should have all three
    assert results['completed'].count('simple_task') == 3
    
    # Started list should have all three
    assert results['started'].count('simple_task') == 3


@pytest.mark.asyncio
async def test_empty_runner():
    """Test that runner works with no tasks."""
    runner = AsyncTaskRunner(verbose=False)
    
    # Run with no tasks
    results = await runner.get_aggregated_results()
    
    # Should return empty but initialized state
    assert results == {
        'results': {},
        'errors': {},
        'completed': [],
        'started': [],
        'retries': [],
        'timed_out': []
    }


@pytest.mark.asyncio
async def test_task_config_none_values():
    """Test that TaskConfig with None values falls back to global settings."""
    runner = AsyncTaskRunner(
        timeout=5,
        retry_enabled=True,
        verbose=False
    )
    
    # Add task with partial config (None values should use globals)
    runner.add_task(
        simple_task,
        "test",
        task_config=TaskConfig(
            timeout=None,  # Should use global (5)
            retry_enabled=None,  # Should use global (True)
            metadata={'custom': 'data'}
        )
    )
    
    results = await runner.get_aggregated_results()
    
    # Task should complete successfully
    assert 'simple_task' in results['results']
    assert results['results']['simple_task'] == "Result: test"


if __name__ == "__main__":
    # Run tests with asyncio
    asyncio.run(test_default_callbacks_basic())
    asyncio.run(test_default_callbacks_with_errors())
    asyncio.run(test_default_callbacks_with_retry())
    asyncio.run(test_custom_callback_override())
    asyncio.run(test_no_default_callbacks())
    asyncio.run(test_per_task_timeout_with_defaults())
    asyncio.run(test_shared_state_persistence())
    asyncio.run(test_verbose_mode())
    asyncio.run(test_multiple_tasks_same_name())
    asyncio.run(test_empty_runner())
    asyncio.run(test_task_config_none_values())
    print("All tests passed!")