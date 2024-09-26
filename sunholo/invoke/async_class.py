import asyncio
from ..custom_logging import log
import traceback
from typing import Callable, Any, AsyncGenerator, Dict
from tenacity import AsyncRetrying, retry_if_exception_type, wait_random_exponential, stop_after_attempt

class AsyncTaskRunner:
    def __init__(self, retry_enabled=False, retry_kwargs=None):
        self.tasks = []
        self.retry_enabled = retry_enabled
        self.retry_kwargs = retry_kwargs or {}

    def add_task(self, func: Callable[..., Any], *args: Any):
        """Adds a task to the list of tasks to be executed."""
        log.info(f"Adding task: {func.__name__} with args: {args}")
        self.tasks.append((func.__name__, func, args))

    async def run_async_as_completed(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs all tasks concurrently and yields results and heartbeats as they are produced.
        """
        log.info("Running tasks asynchronously and yielding results and heartbeats as they occur")
        queue = asyncio.Queue()
        tasks = {}
        completed_tasks = set()

        for name, func, args in self.tasks:
            coro = self._task_wrapper(name, func, args, queue)
            task = asyncio.create_task(coro)
            tasks[task] = name

        while tasks or not queue.empty():
            if not queue.empty():
                message = await queue.get()
                log.info(f"Found queue message: {message}")
                # Ignore heartbeats from completed tasks
                if message['type'] == 'heartbeat' and message['func_name'] in completed_tasks:
                    continue
                yield message
            else:
                done, _ = await asyncio.wait(
                    list(tasks.keys()),
                    timeout=0.1,
                    return_when=asyncio.FIRST_COMPLETED
                )
                for task in done:
                    name = tasks.pop(task)
                    completed_tasks.add(name)
                    try:
                        result = await task
                        await queue.put({'type': 'task_complete', 'func_name': name, 'result': result})
                    except Exception as e:
                        log.error(f"Task {name} resulted in an error: {e}\n{traceback.format_exc()}")
                        await queue.put({'type': 'task_error', 'func_name': name, 'error': e})

        # Process any remaining messages in the queue
        while not queue.empty():
            message = await queue.get()
            log.info(f"Found queue message: {message}")
            if message['type'] == 'heartbeat' and message['func_name'] in completed_tasks:
                continue
            yield message

    async def _task_wrapper(self, name: str, func: Callable[..., Any], args: Any, queue: asyncio.Queue) -> Any:
        """Wraps the task function to process its output and handle retries, while managing heartbeat updates."""
        async def run_func():
            if asyncio.iscoroutinefunction(func):
                return await func(*args)
            else:
                return await asyncio.to_thread(func, *args)

        # Start the heartbeat task
        heartbeat_task = asyncio.create_task(self._send_heartbeat(queue, name))

        try:
            if self.retry_enabled:
                retry_kwargs = {
                    'wait': wait_random_exponential(multiplier=1, max=60),
                    'stop': stop_after_attempt(5),
                    'retry': retry_if_exception_type(Exception),
                    **self.retry_kwargs
                }
                async for attempt in AsyncRetrying(**retry_kwargs):
                    with attempt:
                        return await run_func()
            else:
                try:
                    return await run_func()
                except Exception as e:
                    log.error(f"Error in task {name}: {e}\n{traceback.format_exc()}")
                    raise
        finally:
            # Stop the heartbeat task
            heartbeat_task.cancel()
            # Wait for the heartbeat task to finish
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _send_heartbeat(self, queue: asyncio.Queue, func_name: str, interval=2):
        """
        Sends a periodic heartbeat to keep the task alive and update the spinner with elapsed time.
        """
        # Send the initial spinner HTML
        spinner_html = (
            f'<div id="{func_name}-spinner" class="spinner-container">'
            f'  <div class="spinner"></div>'
            f'  <span class="elapsed-time">Task {func_name} is still running... 0s elapsed</span>'
            f'</div>'
        )
        log.info(f"Heartbeat started for task {func_name}")

        await queue.put({'type': 'heartbeat', 'func_name': func_name, 'token': spinner_html})

        # Keep track of elapsed time
        elapsed_time = 0

        try:
            while True:
                await asyncio.sleep(interval)  # Sleep for the interval
                elapsed_time += interval  # Increment elapsed time
                log.info(f"Sending heartbeat for {func_name}: {elapsed_time}s elapsed")
                # Update spinner with the elapsed time
                update_html = (
                    f'<div style="display: none;" data-update-id="{func_name}-spinner">'
                    f'<span class="elapsed-time">Task {func_name} is still running... {elapsed_time}s elapsed</span>'
                    f'</div>'
                )
                await queue.put({'type': 'heartbeat', 'func_name': func_name, 'token': update_html})
        except asyncio.CancelledError:
            log.info(f"Heartbeat task for {func_name} has been cancelled.")
        finally:
            # Send a message indicating task completion to update the spinner's state
            completion_html = (
                f'<div style="display: none;" data-complete-id="{func_name}-spinner"></div>'
            )
            await queue.put({'type': 'heartbeat', 'func_name': func_name, 'token': completion_html})