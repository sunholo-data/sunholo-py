import json
from ..logging import log

def extract_chat_history(chat_history=None):
    """
    Extracts paired chat history between human and AI messages.

    This function takes a chat history and returns a list of pairs of messages,
    where each pair consists of a human message followed by the corresponding AI response.

    Args:
        chat_history (list): List of chat messages.

    Returns:
        list: List of tuples with paired human and AI messages.

    Example:
    ```python
    chat_history = [
        {"name": "Human", "text": "Hello, AI!"},
        {"name": "AI", "text": "Hello, Human! How can I help you today?"}
    ]
    paired_messages = extract_chat_history(chat_history)
    print(paired_messages)
    # Output: [("Hello, AI!", "Hello, Human! How can I help you today?")]
    ```
    """
    if not chat_history:
        log.info("No chat history found")
        return []

    log.info(f"Extracting chat history: {chat_history}")
    paired_messages = []

    first_message = chat_history[0]
    log.info(f"Extracting first_message: {first_message}")
    if is_bot(first_message):
        blank_human_message = {"name": "Human", "content": "", "embeds": []}
        paired_messages.append((create_message_element(blank_human_message), 
                                create_message_element(first_message)))
        chat_history = chat_history[1:]

    last_human_message = ""
    for message in chat_history:
        log.info(f"Extracing message: {message}")
        if is_human(message):
            last_human_message = create_message_element(message)
            log.info(f"Extracted human message: {last_human_message}")
        elif is_bot(message):
            ai_message = create_message_element(message)
            log.info(f"Extracted AI message: {ai_message}")
            paired_messages.append((last_human_message, ai_message))
            last_human_message = ""

    log.info(f"Paired messages: {paired_messages}")

    return paired_messages

def embeds_to_json(message: dict):
    """
    Converts the 'embeds' field in a message to a JSON string.

    Args:
        message (dict): The message containing the 'embeds' field.

    Returns:
        str: JSON string representation of the 'embeds' field or an empty string if no embeds are found.

    Example:
    ```python
    message = {"embeds": [{"type": "image", "url": "https://example.com/image.png"}]}
    json_string = embeds_to_json(message)
    print(json_string)
    # Output: '[{"type": "image", "url": "https://example.com/image.png"}]'
    ```
    """
    if 'embeds' in message and len(message['embeds']) > 0:
        return json.dumps(message.get("embeds"))
    else:
        return ""

def create_message_element(message: dict):
    """
    Extracts the main content of a message.

    Args:
        message (dict): The message to extract content from.

    Returns:
        str: The text or content of the message.

    Raises:
        KeyError: If neither 'content' nor 'text' fields are found.

    Example:
    ```python
    message = {"text": "Hello, AI!"}
    content = create_message_element(message)
    print(content)
    # Output: 'Hello, AI!'
    ```
    """
    if 'text' in message:  # This is a Slack or Google Chat message
        log.info(f"Found text element - {message['text']}")
        return message['text']
    elif 'content' in message: # Discord or OpenAI history message
        log.info(f"Found content element - {message['content']}")
        return message['content']
    else:  
        raise KeyError(f"Could not extract 'content' or 'text' element from message: {message}, {type(message)}")

def is_human(message: dict):
    """
    Checks if a message was sent by a human.

    Args:
        message (dict): The message to check.

    Returns:
        bool: True if the message was sent by a human, otherwise False.

    Example:
    ```python
    message = {"name": "Human"}
    print(is_human(message))
    # Output: True
    ```
    """
    if 'name' in message:
        return message["name"] == "Human"
    elif 'sender' in message:  # Google Chat
        return message['sender']['type'] == 'HUMAN'
    elif 'role' in message:
        return message['role'] == 'user'
    else:
        # Slack: Check for the 'user' field and absence of 'bot_id' field
        return 'user' in message and 'bot_id' not in message

def is_bot(message: dict):
    """
    Checks if a message was sent by a bot.

    Args:
        message (dict): The message to check.

    Returns:
        bool: True if the message was sent by a bot, otherwise False.

    Example:
    ```python
    message = {"name": "AI"}
    print(is_bot(message))
    # Output: True
    ```
    """
    return not is_human(message)

def is_ai(message: dict):
    """
    Checks if a message was specifically sent by an AI.

    Args:
        message (dict): The message to check.

    Returns:
        bool: True if the message was sent by an AI, otherwise False.

    Example:
    ```python
    message = {"name": "AI"}
    print(is_ai(message))
    # Output: True
    ```
    """
    if 'name' in message:
        return message["name"] == "AI"
    elif 'sender' in message:  # Google Chat
        return message['sender']['type'] == 'BOT'
    elif 'role' in message:
        return message['role'] == 'assistant'
    else:
        return 'bot_id' in message  # Slack
