#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import json
from ..logging import setup_logging

logging = setup_logging()

def extract_chat_history(chat_history=None):

    if chat_history is None:
        logging.info("No chat history found")
        return []

    logging.info(f"Extracting chat history: {chat_history}")
    paired_messages = []

    first_message = chat_history[0]
    logging.info(f"Extracting first_message: {first_message}")
    if is_bot(first_message):
        blank_human_message = {"name": "Human", "content": "", "embeds": []}
        paired_messages.append((create_message_element(blank_human_message), 
                                create_message_element(first_message)))
        chat_history = chat_history[1:]

    last_human_message = ""
    for message in chat_history:
        logging.info(f"Extracing message: {message}")
        if is_human(message):
            last_human_message = create_message_element(message)
            logging.info(f"Extracted human message: {last_human_message}")
        elif is_bot(message):
            ai_message = create_message_element(message)
            logging.info(f"Extracted AI message: {ai_message}")
            paired_messages.append((last_human_message, ai_message))
            last_human_message = ""

    logging.info(f"Paired messages: {paired_messages}")

    return paired_messages

def embeds_to_json(message):
    if len(message['embeds'] > 0):
        return json.dumps(message.get("embeds"))
    else:
        return ""

def create_message_element(message):
    if 'text' in message:  # This is a Slack or Google Chat message
        logging.info(f"Found text element - {message['text']}")
        return message['text']
    elif 'content' in message: # Discord message
        logging.info(f"Found content element - {message['content']}")
        return message['content']
    else:  
        raise KeyError(f"Could not extract 'content' or 'text' element from message: {message}, {type(message)}")

def is_human(message):
    if 'name' in message:
        return message["name"] == "Human"
    elif 'sender' in message:  # Google Chat
        return message['sender']['type'] == 'HUMAN'
    else:
        # Slack: Check for the 'user' field and absence of 'bot_id' field
        return 'user' in message and 'bot_id' not in message

def is_bot(message):
    return not is_human(message)

def is_ai(message):
    if 'name' in message:
        return message["name"] == "AI"
    elif 'sender' in message:  # Google Chat
        return message['sender']['type'] == 'BOT'
    else:
        return 'bot_id' in message  # Slack


