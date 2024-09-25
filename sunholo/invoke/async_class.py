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
    
    async def run_async_as_completed(self, callback=None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs all tasks concurrently and yields results as they complete, while periodically sending heartbeat messages.

        Args:
            callback: The callback object that will receive heartbeat messages.
        """
        log.info("Running tasks asynchronously and yielding results as they complete")
        tasks = {}
        for name, func, args in self.tasks:
            # Pass the callback down to _task_wrapper
            coro = self._task_wrapper(name, func, args, callback)
            task = asyncio.create_task(coro)
            tasks[task] = name
        
        log.info(f"Start async run with {len(self.tasks)} runners")
        while tasks:
            done, _ = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                name = tasks.pop(task)
                try:
                    result = await task
                    yield {name: result}
                except Exception as e:
                    log.error(f"Task {name} resulted in an error: {e}\n{traceback.format_exc()}")
                    yield {name: e}

    async def _task_wrapper(self, name: str, func: Callable[..., Any], args: Any, callback=None) -> Any:
        """Wraps the task function to process its output and handle retries, while managing heartbeat updates."""
        async def run_func():
            if asyncio.iscoroutinefunction(func):
                # If the function is async, await it
                return await func(*args)
            else:
                # If the function is sync, run it in a thread to prevent blocking
                return await asyncio.to_thread(func, *args)

        # Start the heartbeat task if a callback is provided
        heartbeat_task = None
        if callback:
            heartbeat_task = asyncio.create_task(self._send_heartbeat(callback, name))

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
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task  # Ensure the heartbeat task is properly canceled
                except asyncio.CancelledError:
                    pass

            # Send a message indicating task completion and remove spinner
            if callback:
                completion_html = (
                    f"<script>"
                    f"document.getElementById('{name}-spinner').innerHTML = '✔️ Task {name} completed!';"
                    f"</script>"
                )
                await callback.async_on_llm_new_token(token=completion_html)

    async def _send_heartbeat(self, callback, func_name, interval=2):
        """
        Sends periodic heartbeat updates to indicate the task is still in progress.

        Args:
            callback: The callback to notify that the task is still working.
            func_name: The name of the task function.
            interval: How frequently to send heartbeat messages (in seconds).
        """
        # Send the initial spinner HTML
        spinner_html = (
            f'<div id="{func_name}-spinner" style="display:inline-block; margin: 5px;">'
            f'<div class="spinner" style="width:16px; height:16px; border: 2px solid #f3f3f3; '
            f'border-radius: 50%; border-top: 2px solid #3498db; animation: spin 1s linear infinite;"></div>'
            f'<style>@keyframes spin {{0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }}}}</style>'
            f' <span>Task {func_name} is in progress...</span></div>'
        )
        await callback.async_on_llm_new_token(token=spinner_html)

        # Keep sending heartbeats until task completes
        while True:
            await asyncio.sleep(interval)  # Sleep for the interval but do not send multiple messages