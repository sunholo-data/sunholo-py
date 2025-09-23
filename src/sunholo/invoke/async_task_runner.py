import asyncio
from typing import Callable, Any, AsyncGenerator, Dict, Optional, Union
from dataclasses import dataclass, field
import time
import traceback
import logging
from ..custom_logging import setup_logging
from tenacity import AsyncRetrying, retry_if_exception_type, wait_random_exponential, stop_after_attempt

log = setup_logging("sunholo_AsyncTaskRunner")

@dataclass
class CallbackContext:
    """Context passed to callbacks with task information and shared state."""
    task_name: str
    elapsed_time: float = 0
    task_metadata: Dict[str, Any] = field(default_factory=dict)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Exception = None
    retry_attempt: int = 0
    message_type: str = ""

@dataclass
class TaskConfig:
    """Per-task configuration for timeout, retry, and callbacks."""
    timeout: Optional[int] = None
    retry_enabled: Optional[bool] = None
    retry_kwargs: Optional[dict] = None
    heartbeat_extends_timeout: Optional[bool] = None
    hard_timeout: Optional[int] = None
    callbacks: Optional[Dict[str, Callable]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AsyncTaskRunner:
    def __init__(self, 
                 retry_enabled: bool = False, 
                 retry_kwargs: dict = None, 
                 timeout: int = 120, 
                 max_concurrency: int = 20,
                 heartbeat_extends_timeout: bool = False,
                 hard_timeout: int = None,
                 callbacks: Optional[Dict[str, Callable]] = None,
                 shared_state: Optional[Dict[str, Any]] = None,
                 use_default_callbacks: bool = True,
                 verbose: bool = True):
        """
        Initialize AsyncTaskRunner with configurable timeout behavior and callbacks.
        
        By default, AsyncTaskRunner uses built-in callbacks that automatically manage task state,
        making it easy to use without any configuration. Just create, add tasks, and get results!
        
        Args:
            retry_enabled: Whether to enable retries globally
            retry_kwargs: Global retry configuration for tenacity
            timeout: Base timeout for tasks in seconds (default: 120)
            max_concurrency: Maximum concurrent tasks (default: 20)
            heartbeat_extends_timeout: If True, heartbeats reset the timeout timer
            hard_timeout: Maximum absolute timeout regardless of heartbeats (seconds).
                         If None, defaults to timeout * 5 when heartbeat_extends_timeout=True
            callbacks: Dict of custom callbacks to override defaults:
                - on_heartbeat: async (context: CallbackContext) -> None
                - on_task_start: async (context: CallbackContext) -> None
                - on_task_complete: async (context: CallbackContext) -> None
                - on_task_error: async (context: CallbackContext) -> None
                - on_retry: async (context: CallbackContext) -> None
                - on_timeout: async (context: CallbackContext) -> None
            shared_state: Custom shared state dict. If None, creates default structure with:
                - results: Dict[str, Any] - Task results by task name
                - errors: Dict[str, str] - Error messages by task name
                - completed: List[str] - Completed task names
                - started: List[str] - Started task names
                - retries: List[str] - Retry attempt records
                - timed_out: List[str] - Timed out task names
            use_default_callbacks: If True (default), use built-in callbacks that:
                - Automatically populate shared_state with results and errors
                - Log task progress with emojis (🚀 start, ✅ complete, ❌ error, etc.)
                - Track task lifecycle (started, completed, retried, timed out)
                Set to False for full manual control
            verbose: If True (default), default callbacks print status messages.
                     If False, default callbacks work silently (still populate state)
        
        Default Callbacks Behavior:
            When use_default_callbacks=True (default), the following happens automatically:
            - on_task_start: Adds task to 'started' list, logs "🚀 Starting task: {name}"
            - on_task_complete: Stores result in 'results', adds to 'completed', logs "✅ {name} completed: {result}"
            - on_task_error: Stores error in 'errors' (truncated to 500 chars), logs "❌ {name} failed: {error}"
            - on_retry: Tracks retry attempts in 'retries', logs "🔄 Retry #{n} for {name}"
            - on_timeout: Adds to 'timed_out', stores timeout error, logs "⏱️ {name} timed out"
            - on_heartbeat: Silent by default (only logs in DEBUG mode)
        
        Examples:
            # Simplest usage - everything automatic
            >>> runner = AsyncTaskRunner()
            >>> runner.add_task(fetch_data, "api_endpoint")
            >>> results = await runner.get_aggregated_results()
            >>> print(results['results'])  # {'fetch_data': 'data from api'}
            
            # Custom task names for better clarity
            >>> runner = AsyncTaskRunner()
            >>> runner.add_task(fetch_data, "user_api", task_name="fetch_user_data")
            >>> runner.add_task(fetch_data, "posts_api", task_name="fetch_posts")
            >>> results = await runner.get_aggregated_results()
            >>> print(results['results']['fetch_user_data'])  # User data
            
            # Silent mode - no console output but still collects results
            >>> runner = AsyncTaskRunner(verbose=False)
            
            # Override just one callback, keep rest as defaults
            >>> runner = AsyncTaskRunner(
            ...     callbacks={'on_task_complete': my_custom_complete_handler}
            ... )
            
            # Full manual control - no default callbacks
            >>> runner = AsyncTaskRunner(use_default_callbacks=False)
        """
        self.tasks = []
        self.task_name_counts = {}  # Track task names to ensure uniqueness
        self.retry_enabled = retry_enabled
        self.retry_kwargs = retry_kwargs or {}
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.heartbeat_extends_timeout = heartbeat_extends_timeout
        self.verbose = verbose
        
        # Initialize default shared_state structure if not provided
        if shared_state is None:
            self.shared_state = {
                'results': {},
                'errors': {},
                'completed': [],
                'started': [],
                'retries': [],
                'timed_out': []
            }
        else:
            self.shared_state = shared_state
            # Ensure basic keys exist even in custom shared_state
            self.shared_state.setdefault('results', {})
            self.shared_state.setdefault('errors', {})
            self.shared_state.setdefault('completed', [])
        
        # Set up callbacks
        self.global_callbacks = self._setup_callbacks(callbacks, use_default_callbacks)
        
        # Set hard timeout
        if hard_timeout is not None:
            self.hard_timeout = hard_timeout
        elif heartbeat_extends_timeout:
            self.hard_timeout = timeout * 5  # Default to 5x base timeout
        else:
            self.hard_timeout = timeout  # Same as regular timeout
    
    def _setup_callbacks(self, user_callbacks: Optional[Dict[str, Callable]], use_defaults: bool) -> Dict[str, Callable]:
        """Setup callbacks, using defaults if requested and filling in any missing callbacks."""
        callbacks = {}
        
        if use_defaults:
            # Define default callbacks
            async def default_on_task_start(ctx: CallbackContext):
                """Default callback for task start."""
                ctx.shared_state.setdefault('started', []).append(ctx.task_name)
                if self.verbose:
                    log.info(f"🚀 Starting task: {ctx.task_name}")
            
            async def default_on_task_complete(ctx: CallbackContext):
                """Default callback for task completion."""
                ctx.shared_state.setdefault('results', {})[ctx.task_name] = ctx.result
                ctx.shared_state.setdefault('completed', []).append(ctx.task_name)
                if self.verbose:
                    log.info(f"✅ {ctx.task_name} completed: {ctx.result}")
            
            async def default_on_task_error(ctx: CallbackContext):
                """Default callback for task errors."""
                # Store truncated error to avoid huge state
                error_str = str(ctx.error)[:500] if ctx.error else "Unknown error"
                ctx.shared_state.setdefault('errors', {})[ctx.task_name] = error_str
                if self.verbose:
                    log.warning(f"❌ {ctx.task_name} failed: {error_str[:100]}")
            
            async def default_on_retry(ctx: CallbackContext):
                """Default callback for retry attempts."""
                retry_info = f"{ctx.task_name}_attempt_{ctx.retry_attempt}"
                ctx.shared_state.setdefault('retries', []).append(retry_info)
                if self.verbose:
                    log.info(f"🔄 Retry #{ctx.retry_attempt} for {ctx.task_name}")
            
            async def default_on_timeout(ctx: CallbackContext):
                """Default callback for timeouts."""
                ctx.shared_state.setdefault('timed_out', []).append(ctx.task_name)
                ctx.shared_state.setdefault('errors', {})[ctx.task_name] = f"Timeout after {ctx.elapsed_time}s"
                if self.verbose:
                    log.warning(f"⏱️ {ctx.task_name} timed out after {ctx.elapsed_time}s")
            
            async def default_on_heartbeat(ctx: CallbackContext):
                """Default callback for heartbeats - only log in debug mode."""
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(f"💓 Heartbeat for {ctx.task_name}: {ctx.elapsed_time}s")
            
            # Set default callbacks
            callbacks = {
                'on_task_start': default_on_task_start,
                'on_task_complete': default_on_task_complete,
                'on_task_error': default_on_task_error,
                'on_retry': default_on_retry,
                'on_timeout': default_on_timeout,
                'on_heartbeat': default_on_heartbeat
            }
        
        # Override with user callbacks if provided
        if user_callbacks:
            callbacks.update(user_callbacks)
        
        return callbacks

    def add_task(self, 
                 func: Callable[..., Any], 
                 *args: Any, 
                 task_config: Optional[TaskConfig] = None,
                 task_name: Optional[str] = None,
                 **kwargs: Any):
        """
        Adds a task to the list of tasks to be executed, with optional per-task configuration.
        
        Automatically ensures task names are unique by appending a suffix if needed.

        Args:
            func: The function to be executed.
            *args: Positional arguments for the function.
            task_config: Optional per-task configuration for timeout, retry, and callbacks.
            task_name: Optional custom name for the task. If not provided, uses func.__name__.
            **kwargs: Keyword arguments for the function.
        """
        # Get base name from task_name or function name
        base_name = task_name if task_name is not None else func.__name__
        
        # Ensure uniqueness by adding suffix if needed
        if base_name in self.task_name_counts:
            # Name already exists, increment count and add suffix
            self.task_name_counts[base_name] += 1
            name = f"{base_name}_{self.task_name_counts[base_name]}"
        else:
            # First occurrence of this name
            self.task_name_counts[base_name] = 0
            name = base_name
        
        log.info(f"Adding task: {name} with args: {args}, kwargs: {kwargs}, config: {task_config}")
        self.tasks.append((name, func, args, kwargs, task_config))

    async def run_async_with_callbacks(self) -> AsyncGenerator[CallbackContext, None]:
        """
        Runs all tasks and automatically processes messages through callbacks.
        Yields CallbackContext after each callback invocation for monitoring.
        """
        async for message in self.run_async_as_completed():
            context = await self._process_message_with_callbacks(message)
            if context:
                yield context

    async def _process_message_with_callbacks(self, message: Dict[str, Any]) -> Optional[CallbackContext]:
        """Process a message and invoke appropriate callbacks."""
        message_type = message.get('type')
        func_name = message.get('func_name') or message.get('name', 'unknown')
        
        # Find task config for this function
        task_config = None
        task_metadata = {}
        for name, _, args, kwargs, config in self.tasks:
            if name == func_name:
                task_config = config
                task_metadata = {'args': args, 'kwargs': kwargs}
                if config and config.metadata:
                    task_metadata.update(config.metadata)
                break
        
        # Create callback context
        context = CallbackContext(
            task_name=func_name,
            elapsed_time=message.get('elapsed_time', 0),
            task_metadata=task_metadata,
            shared_state=self.shared_state,
            message_type=message_type
        )
        
        # Determine which callback to use (task-specific overrides global)
        callback = None
        task_callbacks = task_config.callbacks if task_config and task_config.callbacks else {}
        
        if message_type == 'heartbeat':
            callback = task_callbacks.get('on_heartbeat') or self.global_callbacks.get('on_heartbeat')
            context.elapsed_time = message.get('elapsed_time', 0)
            
        elif message_type == 'task_complete':
            callback = task_callbacks.get('on_task_complete') or self.global_callbacks.get('on_task_complete')
            context.result = message.get('result')
            
        elif message_type == 'task_error':
            callback = task_callbacks.get('on_task_error') or self.global_callbacks.get('on_task_error')
            context.error = message.get('error')
            
        elif message_type == 'task_start':
            callback = task_callbacks.get('on_task_start') or self.global_callbacks.get('on_task_start')
            
        elif message_type == 'retry':
            callback = task_callbacks.get('on_retry') or self.global_callbacks.get('on_retry')
            context.retry_attempt = message.get('retry_attempt', 0)
            context.error = message.get('error')
            
        elif message_type == 'timeout':
            callback = task_callbacks.get('on_timeout') or self.global_callbacks.get('on_timeout')
            context.elapsed_time = message.get('elapsed_time', self.timeout)
        
        # Invoke callback if found
        if callback and asyncio.iscoroutinefunction(callback):
            try:
                await callback(context)
                return context
            except Exception as e:
                log.error(f"Error in callback for {message_type}: {e}\n{traceback.format_exc()}")
        
        return context if callback else None

    async def get_aggregated_results(self) -> Dict[str, Any]:
        """
        Run all tasks with callbacks and return the shared_state with aggregated results.
        
        This is a convenience method that runs all tasks and returns the populated shared_state.
        When using default callbacks, the returned dict will contain:
        - results: Dict[str, Any] with task results keyed by task name
        - errors: Dict[str, str] with error messages for failed tasks
        - completed: List[str] of completed task names
        - started: List[str] of started task names
        - retries: List[str] of retry attempt records
        - timed_out: List[str] of timed out task names
        
        Returns:
            Dict containing the shared_state with all task results and metadata
        
        Example:
            >>> runner = AsyncTaskRunner()
            >>> runner.add_task(fetch_data, "api", task_name="api_fetch")
            >>> runner.add_task(process_data, "raw_data", task_name="data_processing")
            >>> results = await runner.get_aggregated_results()
            >>> print(results['results']['api_fetch'])  # Access specific result
            >>> if results['errors']:  # Check for any errors
            ...     print(f"Errors occurred: {results['errors']}")
        """
        async for _ in self.run_async_with_callbacks():
            pass  # Callbacks handle state updates
        
        return self.shared_state

    async def run_async_as_completed(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs all tasks concurrently and yields results as they complete,
        while periodically sending heartbeat messages.
        
        This is the low-level API that yields raw messages.
        For a higher-level API with automatic callback processing, use run_async_with_callbacks().
        """
        log.info("Running tasks asynchronously and yielding results as they complete")
        queue = asyncio.Queue()
        task_infos = []

        for name, func, args, kwargs, config in self.tasks:
            log.info(f"Executing task: {name=}, {func=} with args: {args}, kwargs: {kwargs}, config: {config}")
            completion_event = asyncio.Event()
            last_heartbeat = {'time': time.time()}  # Shared mutable object for heartbeat tracking
            
            # Send task_start message
            await queue.put({'type': 'task_start', 'func_name': name})
            
            task_coro = self._run_with_retries_and_timeout(name, func, args, kwargs, config, queue, completion_event, last_heartbeat)            
            task = asyncio.create_task(task_coro)
            heartbeat_coro = self._send_heartbeat(name, config, completion_event, queue, last_heartbeat)
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
                                            config: Optional[TaskConfig],
                                            queue: asyncio.Queue, 
                                            completion_event: asyncio.Event,
                                            last_heartbeat: dict) -> None:
        # Determine effective configuration (per-task overrides global)
        retry_enabled = config.retry_enabled if config and config.retry_enabled is not None else self.retry_enabled
        retry_kwargs = config.retry_kwargs if config and config.retry_kwargs else self.retry_kwargs
        timeout = config.timeout if config and config.timeout is not None else self.timeout
        heartbeat_extends = config.heartbeat_extends_timeout if config and config.heartbeat_extends_timeout is not None else self.heartbeat_extends_timeout
        
        # Calculate hard_timeout based on effective settings
        if config and config.hard_timeout is not None:
            hard_timeout = config.hard_timeout
        elif heartbeat_extends:
            hard_timeout = timeout * 5  # Default to 5x the effective timeout when heartbeat extends
        else:
            hard_timeout = timeout  # Same as effective timeout when no heartbeat extension
        
        try:
            log.info(f"run_with_retries_and_timeout: {name=}, {func=} with args: {args}, kwargs: {kwargs}")
            log.info(f"Effective config - timeout: {timeout}s, retry: {retry_enabled}, heartbeat_extends: {heartbeat_extends}, hard_timeout: {hard_timeout}s")
            
            if retry_enabled:
                retry_kwargs_final = {
                    'wait': wait_random_exponential(multiplier=1, max=60),
                    'stop': stop_after_attempt(5),
                    'retry': retry_if_exception_type(Exception),
                }
                # Override with custom retry kwargs if provided
                if retry_kwargs:
                    retry_kwargs_final.update(retry_kwargs)
                
                retry_attempt = 0
                last_exception = None
                
                try:
                    async for attempt in AsyncRetrying(**retry_kwargs_final):
                        with attempt:
                            retry_attempt = attempt.retry_state.attempt_number
                            
                            # Send retry message for attempts > 1
                            if retry_attempt > 1:
                                await queue.put({
                                    'type': 'retry', 
                                    'func_name': name, 
                                    'retry_attempt': retry_attempt,
                                    'error': str(last_exception) if last_exception else None
                                })
                            
                            log.info(f"Starting task '{name}' with retry (attempt {retry_attempt})")
                            
                            try:
                                result = await self._execute_task_with_timeout(
                                    func, name, last_heartbeat, timeout, heartbeat_extends, hard_timeout, *args, **kwargs
                                )
                                await queue.put({'type': 'task_complete', 'func_name': name, 'result': result})
                                log.info(f"Sent 'task_complete' message for task '{name}'")
                                return
                            except Exception as e:
                                last_exception = e
                                raise  # Re-raise to trigger retry
                except Exception as final_error:
                    # All retries exhausted
                    log.error(f"All retry attempts failed for task '{name}': {final_error}")
                    raise
            else:
                log.info(f"Starting task '{name}' with no retry")
                result = await self._execute_task_with_timeout(
                    func, name, last_heartbeat, timeout, heartbeat_extends, hard_timeout, *args, **kwargs
                )
                await queue.put({'type': 'task_complete', 'func_name': name, 'result': result})
                log.info(f"Sent 'task_complete' message for task '{name}'")
        except asyncio.TimeoutError as e:
            log.error(f"Task '{name}' timed out: {e}")
            await queue.put({
                'type': 'timeout', 
                'func_name': name, 
                'elapsed_time': timeout,
                'error': str(e)
            })
            await queue.put({'type': 'task_error', 'func_name': name, 'error': str(e)})
        except Exception as e:
            log.error(f"Error in task '{name}': {e}\n{traceback.format_exc()}")
            await queue.put({'type': 'task_error', 'func_name': name, 'error': f'{e}\n{traceback.format_exc()}'})
        finally:
            log.info(f"Task '{name}' completed.")
            completion_event.set()

    async def _execute_task_with_timeout(self, 
                                         func: Callable[..., Any], 
                                         name: str, 
                                         last_heartbeat: dict,
                                         timeout: int,
                                         heartbeat_extends: bool,
                                         hard_timeout: int,
                                         *args: Any, 
                                         **kwargs: Any) -> Any:
        """
        Execute task with either fixed timeout or heartbeat-extendable timeout.
        """
        if not heartbeat_extends:
            # Original behavior - fixed timeout
            return await asyncio.wait_for(self._execute_task(func, *args, **kwargs), timeout=timeout)
        else:
            # New behavior - heartbeat extends timeout
            return await self._execute_task_with_heartbeat_timeout(
                func, name, last_heartbeat, timeout, hard_timeout, *args, **kwargs
            )

    async def _execute_task_with_heartbeat_timeout(self, 
                                                   func: Callable[..., Any], 
                                                   name: str, 
                                                   last_heartbeat: dict,
                                                   timeout: int,
                                                   hard_timeout: int,
                                                   *args: Any, 
                                                   **kwargs: Any) -> Any:
        """
        Execute task with heartbeat-extendable timeout and hard timeout limit.
        """
        start_time = time.time()
        task = asyncio.create_task(self._execute_task(func, *args, **kwargs))
        
        while not task.done():
            current_time = time.time()
            
            # Check hard timeout first (absolute limit)
            if current_time - start_time > hard_timeout:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                raise asyncio.TimeoutError(f"Hard timeout exceeded ({hard_timeout}s)")
            
            # Check soft timeout (extends with heartbeats)
            time_since_heartbeat = current_time - last_heartbeat['time']
            if time_since_heartbeat > timeout:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                raise asyncio.TimeoutError(f"Timeout exceeded - no heartbeat for {timeout}s")
            
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

    async def _send_heartbeat(self, 
                             func_name: str, 
                             config: Optional[TaskConfig],
                             completion_event: asyncio.Event, 
                             queue: asyncio.Queue, 
                             last_heartbeat: dict, 
                             interval: int = 2):
        """
        Sends periodic heartbeat updates to indicate the task is still in progress.
        Updates last_heartbeat time if heartbeat_extends_timeout is enabled.

        Args:
            func_name (str): The name of the task function.
            config (Optional[TaskConfig]): Per-task configuration.
            completion_event (asyncio.Event): Event to signal when the task is completed.
            queue (asyncio.Queue): The queue to send heartbeat messages to.
            last_heartbeat (dict): Mutable dict containing the last heartbeat time.
            interval (int): How frequently to send heartbeat messages (in seconds).
        """
        # Determine if heartbeat extends timeout for this task
        heartbeat_extends = config.heartbeat_extends_timeout if config and config.heartbeat_extends_timeout is not None else self.heartbeat_extends_timeout
        
        start_time = time.time()
        log.info(f"Starting heartbeat for task '{func_name}' with interval {interval} seconds")
        try:
            while not completion_event.is_set():
                await asyncio.sleep(interval)
                current_time = time.time()
                elapsed_time = int(current_time - start_time)
                
                # Update last heartbeat time if heartbeat extends timeout
                if heartbeat_extends:
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