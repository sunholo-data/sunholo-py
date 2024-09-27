import asyncio
from typing import Callable, Any, AsyncGenerator, Dict
import time
import traceback
from ..custom_logging import setup_logging
from tenacity import AsyncRetrying, retry_if_exception_type, wait_random_exponential, stop_after_attempt

log = setup_logging("sunholo_AsyncTaskRunner")

class AsyncTaskRunner:
    def __init__(self, retry_enabled=False, retry_kwargs=None):
        self.tasks = []
        self.retry_enabled = retry_enabled
        self.retry_kwargs = retry_kwargs or {}

    def add_task(self, func: Callable[..., Any], *args: Any):
        """
        Adds a task to the list of tasks to be executed.
        """
        log.info(f"Adding task: {func.__name__} with args: {args}")
        self.tasks.append((func.__name__, func, args))

    async def run_async_as_completed(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs all tasks concurrently and yields results as they complete,
        while periodically sending heartbeat messages.
        """
        log.info("Running tasks asynchronously and yielding results as they complete")

        # Create a queue for inter-coroutine communication
        queue = asyncio.Queue()

        # List to keep track of all running tasks and their heartbeats
        task_infos = []

        # Start all tasks and their corresponding heartbeats
        for name, func, args in self.tasks:
            # Create an event to signal task completion to the heartbeat
            completion_event = asyncio.Event()

            # Start the main task with retries
            task_coro = self._run_with_retries(name, func, *args, queue=queue, completion_event=completion_event)
            task = asyncio.create_task(task_coro)

            # Start the heartbeat coroutine
            heartbeat_coro = self._send_heartbeat(name, completion_event, queue)
            heartbeat_task = asyncio.create_task(heartbeat_coro)

            # Store task information for management
            task_infos.append({
                'name': name,
                'task': task,
                'heartbeat_task': heartbeat_task,
                'completion_event': completion_event
            })

            log.info(f"Started task '{name}' and its heartbeat")

        log.info(f"Started async run with {len(self.tasks)} tasks and heartbeats")

        # Create a monitor task to detect when all tasks and heartbeats are done
        monitor = asyncio.create_task(self._monitor_tasks(task_infos, queue))

        # Continuously yield messages from the queue until sentinel is received
        while True:
            message = await queue.get()
            if message is None:
                log.info("Received sentinel. Exiting message loop.")
                break  # Sentinel received, all tasks and heartbeats are done
            log.info(f"Received message from queue: {message}")
            yield message

        # Wait for the monitor to finish
        await monitor

        log.info("All tasks and heartbeats have completed")

    async def _monitor_tasks(self, task_infos, queue):
        """
        Monitors the tasks and heartbeats, and sends a sentinel to the queue when done.
        """
        # Wait for all main tasks to complete
        main_tasks = [info['task'] for info in task_infos]
        log.info("Monitor: Waiting for all main tasks to complete")
        await asyncio.gather(*main_tasks, return_exceptions=True)
        log.info("Monitor: All main tasks have completed")

        # Cancel all heartbeat tasks
        for info in task_infos:
            info['heartbeat_task'].cancel()
            try:
                await info['heartbeat_task']
            except asyncio.CancelledError:
                pass
            log.info(f"Monitor: Heartbeat for task '{info['name']}' has been canceled")

        # Send a sentinel to indicate completion
        await queue.put(None)
        log.info("Monitor: Sent sentinel to queue")

    async def _run_with_retries(self, name: str, func: Callable[..., Any], *args: Any, queue: asyncio.Queue, completion_event: asyncio.Event) -> None:
        """
        Executes a task with optional retries and sends completion or error messages to the queue.
        """
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
                        log.info(f"Starting task '{name}' with retry")
                        result = await self._execute_task(func, *args)
                        await queue.put({'type': 'task_complete', 'func_name': name, 'result': result})
                        log.info(f"Sent 'task_complete' message for task '{name}'")
                        return
            else:
                log.info(f"Starting task '{name}' with no retry")
                result = await self._execute_task(func, *args)
                await queue.put({'type': 'task_complete', 'func_name': name, 'result': result})
                log.info(f"Sent 'task_complete' message for task '{name}'")
        except Exception as e:
            log.error(f"Error in task '{name}': {e}\n{traceback.format_exc()}")
            await queue.put({'type': 'task_error', 'func_name': name, 'error': f'{e}\n{traceback.format_exc()}'})
            log.info(f"Sent 'task_error' message for task '{name}'")
        finally:
            log.info(f"Task '{name}' completed.")
            # Set the completion event after sending the message
            completion_event.set()

    async def _execute_task(self, func: Callable[..., Any], *args: Any) -> Any:
        """
        Executes the given task function and returns its result.

        Args:
            func (Callable): The callable to execute.
            *args: Arguments to pass to the callable.

        Returns:
            Any: The result of the task.
        """
        if asyncio.iscoroutinefunction(func):
            return await func(*args)
        else:
            return await asyncio.to_thread(func, *args)

    async def _send_heartbeat(self, func_name: str, completion_event: asyncio.Event, queue: asyncio.Queue, interval: int = 2):
        """
        Sends periodic heartbeat updates to indicate the task is still in progress.

        Args:
            func_name (str): The name of the task function.
            completion_event (asyncio.Event): Event to signal when the task is completed.
            queue (asyncio.Queue): The queue to send heartbeat messages to.
            interval (int): How frequently to send heartbeat messages (in seconds).
        """
        start_time = time.time()
        log.info(f"Starting heartbeat for task '{func_name}' with interval {interval} seconds")
        try:
            while not completion_event.is_set():
                await asyncio.sleep(interval)
                elapsed_time = int(time.time() - start_time)
                heartbeat_message = {
                    'type': 'heartbeat',
                    'name': func_name,
                    'interval': interval,
                    'elapsed_time': elapsed_time
                }
                log.info(f"Sending heartbeat for task '{func_name}', running for {elapsed_time} seconds")
                await queue.put(heartbeat_message)
        except asyncio.CancelledError:
            log.info(f"Heartbeat for task '{func_name}' has been canceled")
        finally:
            log.info(f"Heartbeat for task '{func_name}' stopped")

