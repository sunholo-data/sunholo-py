"""
Simple example demonstrating AsyncTaskRunner with default callbacks.
Shows how easy it is to use without any configuration.

AsyncTaskRunner Overview:
- Manages concurrent execution of async tasks
- Provides built-in callbacks for task lifecycle events
- Maintains shared state across all tasks
- Supports both default and custom callbacks

Key Methods:
- add_task(func, *args, **kwargs): Add an async function to run
- get_aggregated_results(): Run all tasks and return results
- run_tasks(): Run all tasks without returning results

Default Callbacks (automatically provided):
- on_task_start: Logs when task begins
- on_task_complete: Logs completion and stores result in shared_state
- on_task_error: Logs errors and stores in shared_state
- on_all_complete: Logs when all tasks finish

Shared State Structure:
- shared_state['results']: Dict of {task_name: result}
- shared_state['errors']: Dict of {task_name: error}
- shared_state['completed']: List of completed task names

Callback Context (ctx) provides:
- ctx.task_name: Name of the current task
- ctx.result: Result from the task (on_task_complete)
- ctx.error: Exception object (on_task_error)
- ctx.shared_state: Dict shared across all callbacks
"""

import asyncio
from sunholo.invoke.async_task_runner import AsyncTaskRunner

# Example async functions to demonstrate task execution
# These represent typical async operations like API calls or database queries
async def fetch_data(source: str):
    """Simulates fetching data from a remote source."""
    await asyncio.sleep(1)  # Simulate network delay
    return f"Data from {source}"

async def process_data(data: str):
    """Simulates processing/transforming data."""
    await asyncio.sleep(0.5)  # Simulate processing time
    return f"Processed: {data}"

async def main():
    print("AsyncTaskRunner - Simple Example with Default Callbacks")
    print("=" * 60)
    
    # Example 1: Simplest usage - just add tasks and run
    print("\n1. Simplest usage - default callbacks handle everything:")
    
    # Create runner with default configuration:
    # - verbose=True: Shows status messages
    # - use_default_callbacks=True: Provides built-in lifecycle callbacks
    # - callbacks={}: No custom callbacks, uses all defaults
    runner = AsyncTaskRunner()  # All defaults!
    
    # Add tasks to the runner
    # AsyncTaskRunner now automatically ensures unique task names by adding suffixes
    # This prevents results from being overwritten when the same function is called multiple times
    runner.add_task(fetch_data, "API")          # Will be named: fetch_data
    runner.add_task(fetch_data, "Database")     # Will be named: fetch_data_1 (auto-suffixed!)
    runner.add_task(process_data, "Sample data") # Will be named: process_data
    
    # Run all tasks concurrently and wait for completion
    # Returns the shared_state dict containing results, errors, and completed lists
    results = await runner.get_aggregated_results()
    
    # Access the aggregated results from shared_state
    print(f"\nResults: {results['results']}")     # Dict of task_name -> result
    print(f"Completed: {results['completed']}")   # List of completed task names
    
    # Example 2: Using custom task names for clarity
    print("\n2. Custom task names - distinguish between similar tasks:")
    
    runner = AsyncTaskRunner()
    
    # Use custom task names to differentiate multiple calls to the same function
    # This is especially useful when running the same function with different arguments
    runner.add_task(fetch_data, "API", task_name="fetch_api_data")
    runner.add_task(fetch_data, "Database", task_name="fetch_db_data")
    runner.add_task(fetch_data, "Cache", task_name="fetch_cache_data")
    runner.add_task(process_data, "Sample data", task_name="process_sample")
    
    # Now each task has a unique, meaningful name
    results = await runner.get_aggregated_results()
    
    print(f"\nResults with custom names:")
    for task_name, result in results['results'].items():
        print(f"  {task_name}: {result}")
    print(f"Completed: {results['completed']}")
    
    # Example 3: Disable verbose output for quiet operation
    print("\n3. Quiet mode - no status messages:")
    
    # verbose=False disables the default status logging
    # Callbacks still run, but they won't print messages
    runner = AsyncTaskRunner(verbose=False)  # Silent operation
    
    # Add tasks silently (no status messages)
    runner.add_task(fetch_data, "Source1")
    runner.add_task(process_data, "Data1")
    
    # Results still collected, just without verbose output
    results = await runner.get_aggregated_results()
    print(f"Results: {results['results']}")
    
    # Example 4: Mix default callbacks with one custom callback
    # This demonstrates how to override specific callbacks while keeping others
    print("\n4. Override just one callback, keep the rest as defaults:")
    
    async def custom_complete(ctx):
        """Custom callback for task completion.
        
        Args:
            ctx: CallbackContext object with:
                - task_name: str - Name of the completed task
                - result: Any - Return value from the task
                - shared_state: dict - State shared across all callbacks
        """
        print(f"  [CUSTOM] Task {ctx.task_name} done!")
        # Important: Update shared_state to maintain results tracking
        # This mimics what the default callback does
        ctx.shared_state['results'][ctx.task_name] = ctx.result
        ctx.shared_state['completed'].append(ctx.task_name)
    
    runner = AsyncTaskRunner(
        callbacks={'on_task_complete': custom_complete}
        # Only on_task_complete is overridden
        # Other callbacks (on_task_start, on_task_error, on_all_complete) use defaults
    )
    
    # Custom callback will be called when task completes
    runner.add_task(fetch_data, "CustomSource")
    results = await runner.get_aggregated_results()
    print(f"Results: {results['results']}")
    
    # Example 5: Disable all default callbacks for manual control
    # This shows what happens when you don't use any callbacks
    print("\n5. No default callbacks - manual control:")
    
    # use_default_callbacks=False means NO automatic result tracking
    # You would need to provide your own callbacks to track results
    runner = AsyncTaskRunner(use_default_callbacks=False)
    
    # Add task but no callbacks will run
    runner.add_task(fetch_data, "ManualSource")
    results = await runner.get_aggregated_results()
    
    # Without callbacks, shared_state won't be populated automatically
    # Results will be an empty dict because no callbacks stored the data
    print(f"Results (empty without callbacks): {results}")
    
    print("\n" + "=" * 60)
    print("Done! Default callbacks make AsyncTaskRunner easy to use!")
    print("\nKey takeaways:")
    print("- Default callbacks handle result aggregation automatically")
    print("- Use custom task_name to distinguish multiple calls to the same function")
    print("- Override specific callbacks while keeping others")
    print("- Use verbose=False for quiet operation")
    print("- Disable defaults with use_default_callbacks=False for full control")

if __name__ == "__main__":
    asyncio.run(main())