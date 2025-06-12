import asyncio
from typing import Callable, Any, AsyncGenerator, Dict
import time
import traceback
from ..custom_logging import setup_logging
from tenacity import AsyncRetrying, retry_if_exception_type, wait_random_exponential, stop_after_attempt

log = setup_logging("sunholo_AsyncTaskRunner")

class AsyncTaskRunner:
    def __init__(self, 
                 retry_enabled: bool = False, 
                 retry_kwargs: dict = None, 
                 timeout: int = 120, 
                 max_concurrency: int = 20,
                 heartbeat_extends_timeout: bool = False,
                 hard_timeout: int = None):
        """
        Initialize AsyncTaskRunner with configurable timeout behavior.
        
        Args:
            retry_enabled: Whether to enable retries
            retry_kwargs: Retry configuration
            timeout: Base timeout for tasks (seconds)
            max_concurrency: Maximum concurrent tasks
            heartbeat_extends_timeout: If True, heartbeats reset the timeout timer
            hard_timeout: Maximum absolute timeout regardless of heartbeats (seconds).
                         If None, defaults to timeout * 5 when heartbeat_extends_timeout=True
        """
        self.tasks = []
        self.retry_enabled = retry_enabled
        self.retry_kwargs = retry_kwargs or {}
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.heartbeat_extends_timeout = heartbeat_extends_timeout
        
        # Set hard timeout
        if hard_timeout is not None:
            self.hard_timeout = hard_timeout
        elif heartbeat_extends_timeout:
            self.hard_timeout = timeout * 5  # Default to 5x base timeout
        else:
            self.hard_timeout = timeout  # Same as regular timeout

    def add_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any):
        """
        Adds a task to the list of tasks to be executed, supporting both positional and keyword arguments.

        Args:
            func: The function to be executed.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
        """
        log.info(f"Adding task: {func.__name__} with args: {args}, kwargs: {kwargs}")
        self.tasks.append((func.__name__, func, args, kwargs))

    async def run_async_as_completed(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs all tasks concurrently and yields results as they complete,
        while periodically sending heartbeat messages.
        """
        log.info("Running tasks asynchronously and yielding results as they complete")
        queue = asyncio.Queue()
        task_infos = []

        for name, func, args, kwargs in self.tasks:
            log.info(f"Executing task: {name=}, {func=} with args: {args}, kwargs: {kwargs}")
            completion_event = asyncio.Event()
            last_heartbeat = {'time': time.time()}  # Shared mutable object for heartbeat tracking
            
            task_coro = self._run_with_retries_and_timeout(name, func, args, kwargs, queue, completion_event, last_heartbeat)            
            task = asyncio.create_task(task_coro)
            heartbeat_coro = self._send_heartbeat(name, completion_event, queue, last_heartbeat)
            heartbeat_task = asyncio.create_task(heartbeat_coro)
            task_infos.append({
                'name': name,
                'task': task,
                'heartbeat_task': heartbeat_task,
                'completion_event': completion_event
            })
            log.info(f"Started task '{name}' and its heartbeat")

        log.info(f"Started async run with {len(self.tasks)} tasks and heartbeats")
        monitor = asyncio.create_task(self._monitor_tasks(task_infos, queue))

        while True:
            message = await queue.get()
            if message is None:
                log.info("Received sentinel. Exiting message loop.")
                break
            log.info(f"Received message from queue: {message}")
            yield message

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

        await queue.put(None)
        log.info("Monitor: Sent sentinel to queue")

    async def _run_with_retries_and_timeout(self, 
                                            name: str,
                                            func: Callable[..., Any], 
                                            args: tuple,
                                            kwargs: dict,
                                            queue: asyncio.Queue, 
                                            completion_event: asyncio.Event,
                                            last_heartbeat: dict) -> None:
        try:
            log.info(f"run_with_retries_and_timeout: {name=}, {func=} with args: {args}, kwargs: {kwargs}")
            log.info(f"Timeout mode: heartbeat_extends_timeout={self.heartbeat_extends_timeout}, timeout={self.timeout}s, hard_timeout={self.hard_timeout}s")
            
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
                        result = await self._execute_task_with_timeout(func, name, last_heartbeat, *args, **kwargs)
                        await queue.put({'type': 'task_complete', 'func_name': name, 'result': result})
                        log.info(f"Sent 'task_complete' message for task '{name}'")
                        return
            else:
                log.info(f"Starting task '{name}' with no retry")
                result = await self._execute_task_with_timeout(func, name, last_heartbeat, *args, **kwargs)
                await queue.put({'type': 'task_complete', 'func_name': name, 'result': result})
                log.info(f"Sent 'task_complete' message for task '{name}'")
        except asyncio.TimeoutError:
            log.error(f"Task '{name}' timed out after {self.timeout} seconds")
            await queue.put({'type': 'task_error', 'func_name': name, 'error': f'Task timed out after {self.timeout} seconds'})
        except Exception as e:
            log.error(f"Error in task '{name}': {e}\n{traceback.format_exc()}")
            await queue.put({'type': 'task_error', 'func_name': name, 'error': f'{e}\n{traceback.format_exc()}'})
        finally:
            log.info(f"Task '{name}' completed.")
            completion_event.set()

    async def _execute_task_with_timeout(self, func: Callable[..., Any], name: str, last_heartbeat: dict, *args: Any, **kwargs: Any) -> Any:
        """
        Execute task with either fixed timeout or heartbeat-extendable timeout.
        """
        if not self.heartbeat_extends_timeout:
            # Original behavior - fixed timeout
            return await asyncio.wait_for(self._execute_task(func, *args, **kwargs), timeout=self.timeout)
        else:
            # New behavior - heartbeat extends timeout
            return await self._execute_task_with_heartbeat_timeout(func, name, last_heartbeat, *args, **kwargs)

    async def _execute_task_with_heartbeat_timeout(self, func: Callable[..., Any], name: str, last_heartbeat: dict, *args: Any, **kwargs: Any) -> Any:
        """
        Execute task with heartbeat-extendable timeout and hard timeout limit.
        """
        start_time = time.time()
        task = asyncio.create_task(self._execute_task(func, *args, **kwargs))
        
        while not task.done():
            current_time = time.time()
            
            # Check hard timeout first (absolute limit)
            if current_time - start_time > self.hard_timeout:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                raise asyncio.TimeoutError(f"Hard timeout exceeded ({self.hard_timeout}s)")
            
            # Check soft timeout (extends with heartbeats)
            time_since_heartbeat = current_time - last_heartbeat['time']
            if time_since_heartbeat > self.timeout:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                raise asyncio.TimeoutError(f"Timeout exceeded - no heartbeat for {self.timeout}s")
            
            # Wait a bit before checking again
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=1.0)
                break  # Task completed
            except asyncio.TimeoutError:
                continue  # Check timeouts again
        
        return await task

    async def _execute_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Executes the given task function and returns its result.

        Args:
            func (Callable): The callable to execute.
            *args: Positional arguments to pass to the callable.
            **kwargs: Keyword arguments to pass to the callable.

        Returns:
            Any: The result of the task.
        """
        async with self.semaphore:  # Use semaphore to limit concurrent executions
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return await asyncio.to_thread(func, *args, **kwargs)

    async def _send_heartbeat(self, func_name: str, completion_event: asyncio.Event, queue: asyncio.Queue, last_heartbeat: dict, interval: int = 2):
        """
        Sends periodic heartbeat updates to indicate the task is still in progress.
        Updates last_heartbeat time if heartbeat_extends_timeout is enabled.

        Args:
            func_name (str): The name of the task function.
            completion_event (asyncio.Event): Event to signal when the task is completed.
            queue (asyncio.Queue): The queue to send heartbeat messages to.
            last_heartbeat (dict): Mutable dict containing the last heartbeat time.
            interval (int): How frequently to send heartbeat messages (in seconds).
        """
        start_time = time.time()
        log.info(f"Starting heartbeat for task '{func_name}' with interval {interval} seconds")
        try:
            while not completion_event.is_set():
                await asyncio.sleep(interval)
                current_time = time.time()
                elapsed_time = int(current_time - start_time)
                
                # Update last heartbeat time if heartbeat extends timeout
                if self.heartbeat_extends_timeout:
                    last_heartbeat['time'] = current_time
                    log.debug(f"Updated heartbeat time for task '{func_name}' at {current_time}")
                
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