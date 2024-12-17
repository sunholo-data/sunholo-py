from sunholo.genai import GoogleAI, GoogleAIConfig
import os
import asyncio

async def main():
    config = GoogleAIConfig(
        api_key=os.getenv("GOOGLE_API_KEY"),
    )
    ai = GoogleAI(config)
    
    prompts = [
        "Tell me a short story",
        "What's the weather like?",
        "How do computers work?"
    ]
    
    for prompt in prompts:
        print(f"\nTesting prompt: {prompt}")
        try:
            await ai.live_async(prompt)
        except Exception as e:
            print(f"Error: {e}")
    
    #print("## Speak NOW for 5 seconds...")
    #response = await ai.live_async(
    #    input_type="audio",
    #    duration=5.0  # Record for 5 seconds
    #)
    #print(response)

    #print("## Video NOW for 3 seconds...")
    #response = await ai.live_async(
    #    input_type="video",
    #    duration=3.0  # Record for 3 seconds
    #)
    #print(response)

if __name__ == "__main__":
    asyncio.run(main())