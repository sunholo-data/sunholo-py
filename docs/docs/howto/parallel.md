# Parallel Execution

In many cases in GenAI its useful to call GenAI models or functions in parallel, to speed up user experience of the response.

A basic `asyncio` powered class is available via `AsyncTaskRunner` to help facilitate this, primarily intended for API calls to VACs and agents.

It will wait for the first function to return and get the full result, before waiting for the next etc.   This is useful when constructing lots of context from different agents to feed into an orchestrator agent.

```python
import asyncio
from sunholo.invoke import AsyncTaskRunner
from sunholo.vertex import init_vertex, vertex_safety
from vertexai.preview.generative_models import GenerativeModel

async def do_async(question):
    # Initialize Vertex AI
    init_vertex(location="europe-west1")
    runner = AsyncTaskRunner(retry_enabled=True)

    # Define async functions for runner
    async def english(question):
        print(f"This is English: question='{question}'")
        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=vertex_safety(),
            system_instruction="Answer in English"
        )
        result = await model.generate_content_async(question)
        return result.text  # Assuming result has a 'text' attribute

    async def danish(question):
        print(f"This is Danish: question='{question}'")
        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=vertex_safety(),
            system_instruction="Answer in Danish"
        )
        result = await model.generate_content_async(question)
        return result.text

    async def french(question):
        print(f"This is French: question='{question}'")
        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=vertex_safety(),
            system_instruction="Answer in French"
        )
        result = await model.generate_content_async(question)
        return result.text

    async def italian(question):
        print(f"This is Italian: question='{question}'")
        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            safety_settings=vertex_safety(),
            system_instruction="Answer in Italian"
        )
        result = await model.generate_content_async(question)
        return result.text

    # Add tasks to the runner
    runner.add_task(english, question)
    runner.add_task(french, question)
    runner.add_task(danish, question)
    runner.add_task(italian, question)

    # Run tasks and process results as they complete
    answers = {}
    print(f"Start async run with {len(runner.tasks)} runners")
    async for result_dict in runner.run_async_as_completed():
        for func_name, result in result_dict.items():
            if isinstance(result, Exception):
                print(f"ERROR in {func_name}: {str(result)}")
            else:
                # Output the result
                print(f"{func_name.capitalize()} answer:")
                print(result)
                answers[func_name] = result

    # Return a dict of the results {"english": ..., "french": ..., "danish": ..., "italian": ...}
    return answers

# Run the asynchronous function
if __name__ == "__main__":
    question = "What is MLOps?"

    # Run the do_async function using asyncio.run
    answers = asyncio.run(do_async(question))

    print("\nFinal answers:")
    for language, answer in answers.items():
        print(f"{language.capitalize()}:\n{answer}\n")
```
