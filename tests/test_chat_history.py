import pytest
from sunholo.agents.chat_history import extract_chat_history, embeds_to_json, create_message_element, is_human, is_bot, is_ai

# Test cases for extract_chat_history function
@pytest.mark.parametrize("chat_history,expected", [
    ([], []),
    ([{"name": "Human", "text": "Hello, AI!"}, {"name": "AI", "text": "Hello, Human! How can I help you today?"}], [("Hello, AI!", "Hello, Human! How can I help you today?")])
])
def test_extract_chat_history(chat_history, expected):
    assert extract_chat_history(chat_history) == expected

# Test cases for embeds_to_json function
@pytest.mark.parametrize("message,expected", [
    ({"embeds": []}, ""),
    ({"embeds": [{"type": "image", "url": "https://example.com/image.png"}]}, '[{"type": "image", "url": "https://example.com/image.png"}]')
])
def test_embeds_to_json(message, expected):
    assert embeds_to_json(message) == expected

# Test cases for create_message_element function
@pytest.mark.parametrize("message,expected", [
    ({"text": "Hello, AI!"}, "Hello, AI!"),
    ({"content": "Hello, AI!"}, "Hello, AI!")
])
def test_create_message_element(message, expected):
    assert create_message_element(message) == expected

# Test cases for is_human function
@pytest.mark.parametrize("message,expected", [
    ({"name": "Human"}, True),
    ({"name": "AI"}, False)
])
def test_is_human(message, expected):
    assert is_human(message) == expected

# Test cases for is_bot function
@pytest.mark.parametrize("message,expected", [
    ({"name": "AI"}, True),
    ({"name": "Human"}, False)
])
def test_is_bot(message, expected):
    assert is_bot(message) == expected

# Test cases for is_ai function
@pytest.mark.parametrize("message,expected", [
    ({"name": "AI"}, True),
    ({"name": "Human"}, False)
])
def test_is_ai(message, expected):
    assert is_ai(message) == expected
