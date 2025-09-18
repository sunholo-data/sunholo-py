"""
Simple example demonstrating AsyncTaskRunner with default callbacks.
Shows how easy it is to use without any configuration.
"""

import asyncio
from sunholo.invoke.async_task_runner import AsyncTaskRunner

# Simple async functions
async def fetch_data(source: str):
    await asyncio.sleep(1)
    return f"Data from {source}"

async def process_data(data: str):
    await asyncio.sleep(0.5)
    return f"Processed: {data}"

async def main():
    print("AsyncTaskRunner - Simple Example with Default Callbacks")
    print("=" * 60)
    
    # Example 1: Simplest usage - just add tasks and run
    print("\n1. Simplest usage - default callbacks handle everything:")
    
    runner = AsyncTaskRunner()  # All defaults!
    
    runner.add_task(fetch_data, "API")
    runner.add_task(fetch_data, "Database")
    runner.add_task(process_data, "Sample data")
    
    results = await runner.get_aggregated_results()
    
    print(f"\nResults: {results['results']}")
    print(f"Completed: {results['completed']}")
    
    # Example 2: Disable verbose output for quiet operation
    print("\n2. Quiet mode - no status messages:")
    
    runner = AsyncTaskRunner(verbose=False)  # Silent operation
    
    runner.add_task(fetch_data, "Source1")
    runner.add_task(process_data, "Data1")
    
    results = await runner.get_aggregated_results()
    print(f"Results: {results['results']}")
    
    # Example 3: Mix default callbacks with one custom callback
    print("\n3. Override just one callback, keep the rest as defaults:")
    
    async def custom_complete(ctx):
        print(f"  [CUSTOM] Task {ctx.task_name} done!")
        # Still update shared_state like default would
        ctx.shared_state['results'][ctx.task_name] = ctx.result
        ctx.shared_state['completed'].append(ctx.task_name)
    
    runner = AsyncTaskRunner(
        callbacks={'on_task_complete': custom_complete}
        # All other callbacks remain as defaults
    )
    
    runner.add_task(fetch_data, "CustomSource")
    results = await runner.get_aggregated_results()
    print(f"Results: {results['results']}")
    
    # Example 4: Disable all default callbacks for manual control
    print("\n4. No default callbacks - manual control:")
    
    runner = AsyncTaskRunner(use_default_callbacks=False)
    
    runner.add_task(fetch_data, "ManualSource")
    results = await runner.get_aggregated_results()
    
    # Without callbacks, shared_state won't be populated automatically
    print(f"Results (empty without callbacks): {results}")
    
    print("\n" + "=" * 60)
    print("Done! Default callbacks make AsyncTaskRunner easy to use!")

if __name__ == "__main__":
    asyncio.run(main())