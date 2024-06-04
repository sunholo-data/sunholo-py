import pytest
from sunholo.agents.chat_history import extract_chat_history, embeds_to_json, create_message_element, is_human, is_bot, is_ai

# Test cases for extract_chat_history function
def test_extract_chat_history_empty():
    assert extract_chat_history([]) == []

def test_extract_chat_history_valid():
    chat_history = [
        {"name": "Human", "text": "Hello, AI!"},
        {"name": "AI", "text": "Hello, Human! How can I help you today?"}
    ]
    expected = [("Hello, AI!", "Hello, Human! How can I help you today?")]
    assert extract_chat_history(chat_history) == expected

# Test cases for embeds_to_json function
def test_embeds_to_json_empty():
    message = {"embeds": []}
    assert embeds_to_json(message) == ""

def test_embeds_to_json_valid():
    message = {"embeds": [{"type": "image", "url": "https://example.com/image.png"}]}
    expected = '[{"type": "image", "url": "https://example.com/image.png"}]'
    assert embeds_to_json(message) == expected

# Test cases for create_message_element function
def test_create_message_element_text():
    message = {"text": "Hello, AI!"}
    assert create_message_element(message) == "Hello, AI!"

def test_create_message_element_content():
    message = {"content": "Hello, AI!"}
    assert create_message_element(message) == "Hello, AI!"

# Test cases for is_human function
def test_is_human_true():
    message = {"name": "Human"}
    assert is_human(message) == True

def test_is_human_false():
    message = {"name": "AI"}
    assert is_human(message) == False

# Test cases for is_bot function
def test_is_bot_true():
    message = {"name": "AI"}
    assert is_bot(message) == True

def test_is_bot_false():
    message = {"name": "Human"}
    assert is_bot(message) == False

# Test cases for is_ai function
def test_is_ai_true():
    message = {"name": "AI"}
    assert is_ai(message) == True

def test_is_ai_false():
    message = {"name": "Human"}
    assert is_ai(message) == False
