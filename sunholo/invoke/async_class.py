import asyncio
import logging
from typing import Callable, List, Any, Coroutine, Tuple

# Setup basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncTaskRunner:
    """
    # Example async functions for testing
    async def api_call_1(url, params):
        await asyncio.sleep(1)
        if "fail" in params:
            raise ValueError(f"Error in api_call_1 with params: {params}")
        return f"api_call_1 response from {url} with params {params}"

    async def api_call_2(url, params):
        await asyncio.sleep(2)
        if "fail" in params:
            raise ValueError(f"Error in api_call_2 with params: {params}")
        return f"api_call_2 response from {url} with params {params}"

    # Example usage in an existing async function
    async def example_usage():
        runner = AsyncTaskRunner()

        runner.add_task(api_call_1, "http://example.com", {"key": "value"})
        runner.add_task(api_call_2, "http://example.org", {"key": "fail"})

        # Run all tasks within the existing event loop
        results = await runner.run_async()
        for result in results:
            print(result)

    # Example of calling run_sync() in a synchronous context
    if __name__ == "__main__":
        runner = AsyncTaskRunner()

        runner.add_task(api_call_1, "http://example.com", {"key": "value"})
        runner.add_task(api_call_2, "http://example.org", {"key": "fail"})

        # Running in a synchronous context
        results = runner.run_sync()
        for result in results:
            print(result)
    """
    def __init__(self):
        self.tasks = []

    def add_task(self, func: Callable[..., Coroutine], *args: Any):
        """Adds a task (function and its arguments) to the list of tasks to be executed."""
        logger.info(f"Adding task: {func.__name__} with args: {args}")
        self.tasks.append(func(*args))

    def add_group(self, functions: List[Callable[..., Coroutine]], *args: Any):
        """Adds a group of functions that should run in parallel with the same arguments."""
        group_tasks = [func(*args) for func in functions]
        logger.info(f"Adding group of tasks with args: {args}")
        self.tasks.append(asyncio.gather(*group_tasks, return_exceptions=True))

    async def run_async(self) -> List[Any]:
        """Runs all tasks using the current event loop and returns the results."""
        logger.info("Running tasks asynchronously")
        results = await asyncio.gather(*self.tasks, return_exceptions=True)
        self._log_results(results)
        return results

    def run_sync(self) -> List[Any]:
        """Runs all tasks synchronously (blocking) using a new event loop and returns the results."""
        try:
            logger.info("Running tasks synchronously")
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self.run_async())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.run_async())
            loop.close()
            return results

    def _log_results(self, results: List[Any]):
        """Logs the results of the task executions."""
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task resulted in an error: {result}")
            else:
                logger.info(f"Task completed successfully: {result}")

