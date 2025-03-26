import os.path
import argparse
from typing import List, Optional
import sys
from ..custom_logging import log

try:
    import PIL.Image
    from ollama import generate
except ImportError:
    generate = None

CHAT_MODEL_NAME = os.getenv("MODEL_NAME_LATEST")

def chat_ollama(msg, model_name, the_images=None):
    
    if not generate:
        raise ImportError("Import ollama via `pip install ollama`")
    
    chat_images = []
    if the_images:
        for the_image in the_images:
            chat_image = PIL.Image.open(the_image)
            chat_images.append(chat_image)

    log.info(f"Ollama [{model_name}]: Chatting...{msg=}")
    for response in generate(model_name, msg, images=chat_images, stream=True):
        print(response['response'], end='', flush=True)

def main():
    parser = argparse.ArgumentParser(description='Chat with Ollama models from the command line')
    parser.add_argument('--model', '-m', type=str, default=CHAT_MODEL_NAME,
                        help='Model name to use (defaults to MODEL_NAME_LATEST env var)')
    parser.add_argument('--images', '-i', type=str, nargs='+',
                        help='Image file paths to include in the prompt')
    parser.add_argument('--message', '-p', type=str,
                        help='Message to send')
    
    args = parser.parse_args()
    
    if not args.model:
        print("Error: No model specified. Either set MODEL_NAME_LATEST environment variable or use --model flag.")
        sys.exit(1)
    
    # If no message provided via args, read from stdin
    if not args.message:
        print(f"Enter your message to {args.model} (Ctrl+D to send):")
        user_input = sys.stdin.read().strip()
    else:
        user_input = args.message
    
    if not user_input:
        print("Error: Empty message. Exiting.")
        sys.exit(1)
    
    try:
        chat_ollama(user_input, args.model, args.images)
        print()  # Add a newline after the response
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # uv run src/sunholo/ollama/ollama_images.py --model=gemma3:12b - chat and then CTRL+D
    # uv run src/sunholo/ollama/ollama_images.py --model gemma3:12b --message "Tell me about quantum computing"


    main()