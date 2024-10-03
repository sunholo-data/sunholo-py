import asyncio
from sunholo.invoke import AsyncTaskRunner
# Mock logger for demonstration
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# Dummy task functions for testing
async def google_search(query, config_manager):
    await asyncio.sleep(5)  # Simulate a long-running task
    return f"Results for '{query}'"

async def use_pdfs(query, arg2, arg3):
    await asyncio.sleep(2)  # Simulate a medium-running task
    return "No image_uri specified\n"

async def process_urls(url):
    await asyncio.sleep(1)  # Simulate a short-running task
    return "No URLs were found"

# Mock callback for demonstration
class MockCallback:
    async def async_on_llm_new_token(self, token):
        log.info(f"Callback received token: {token}")

# Mock functions for demonstration
def format_token_output(func_name, tokens, result=None, error=None):
    if error:
        return f"Error in {func_name}: {error}"
    return f"{func_name} completed with {tokens} tokens. Result: {result}"

async def count_tokens(result):
    return len(result.split())

async def kwargs_function(required_arg, **kwargs):
    await asyncio.sleep(3)  # Simulate a medium-running task
    return f"Required arg: {required_arg}, Optional args: {kwargs}"

# Example usage
async def main():
    runner = AsyncTaskRunner(retry_enabled=True)
    
    # Add your tasks
    runner.add_task(google_search, "<original user question>...", "<config>")
    runner.add_task(use_pdfs, "<original user question>...", None, None)
    runner.add_task(process_urls, "please give me a forecast of ppas for spain using wind energy")
    runner.add_task(kwargs_function, "required_value", optional_arg1="test", optional_arg2=42)
    
    callback = MockCallback()
    answers = {}
    total_context_tokens = 0
    
    async for message in runner.run_async_as_completed():
        log.info(f"Runner message={message}")
        if message['type'] == 'heartbeat':
            func_name = message['name']
            elapsed_time = message['elapsed_time']
            log.info(f"Runner Heartbeat for {func_name}, elapsed_time={elapsed_time}")
            # Send heartbeat to callback
            update_html = (
                f'<div style="display: none;" data-update-id="{func_name}-spinner">'
                f'<span class="elapsed-time">{elapsed_time} seconds elapsed</span>'
                f'</div>'
            )
            await callback.async_on_llm_new_token(token=f"[[HEARTBEAT]]{update_html}[[/HEARTBEAT]]")
        elif message['type'] == 'task_complete':
            func_name = message['func_name']
            result = message['result']
            log.info(f"Runner completed task: {func_name}")
            # Process result
            if isinstance(result, Exception):
                log.info(f"Error Exception for {func_name}: {str(result)}")
                formatted_output = format_token_output(func_name, 0, error="No results")
                await callback.async_on_llm_new_token(token=formatted_output)
            else:
                # Stream the result to the callback
                tokens = await count_tokens(result)
                total_context_tokens += tokens
                log.info(f"Got task {func_name} to stream result length [{len(result)}] [{tokens} tokens]")
                formatted_output = format_token_output(func_name, tokens, result=result)
                await callback.async_on_llm_new_token(token=formatted_output)
                answers[func_name] = result
        elif message['type'] == 'task_error':
            func_name = message['func_name']
            error = message['error']
            log.info(f"Error Exception for {func_name}: {str(error)}")
            formatted_output = format_token_output(func_name, 0, error="No results")
            await callback.async_on_llm_new_token(token=formatted_output)

    await callback.async_on_llm_new_token(
        token=f'<div style="margin-top: 20px; color: #333;"><strong>-- Using [{total_context_tokens}] tokens in context for final answer --</strong></div>'
    )
    log.info("All tasks have been processed.")

# Run the main coroutine
if __name__ == "__main__":
    asyncio.run(main())