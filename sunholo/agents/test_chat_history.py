import pytest
from .chat_history import *


def test_extract_chat_history_null_input():
    assert extract_chat_history(None) == [], 'Expected empty list for null input'


def test_extract_chat_history_no_chat():
    assert extract_chat_history([]) == [], 'Expected empty list for no chat history'


def test_extract_chat_history_with_chat():
    chat_history = [('User', 'Hello'), ('Bot', 'Hi'), ('User', 'How are you?'), ('Bot', 'I am fine.')]
    expected_output = [('User', 'Hello'), ('Bot', 'Hi'), ('User', 'How are you?'), ('Bot', 'I am fine.')]
    assert extract_chat_history(chat_history) == expected_output, 'Expected list of paired messages for chat history'


# Test cases for embeds_to_json function

def test_embeds_to_json_no_embeds():
    message = 'Hello, world!'
    assert embeds_to_json(message) == '', 'Expected empty string for message with no embeds'


def test_embeds_to_json_one_embed():
    message = 'Hello, world! [embed]'
    expected_output = '{"embeds": ["embed"]}'
    assert embeds_to_json(message) == expected_output, 'Expected JSON string with one embed for message with one embed'


def test_embeds_to_json_multiple_embeds():
    message = 'Hello, world! [embed1] [embed2]'
    expected_output = '{"embeds": ["embed1", "embed2"]}'
    assert embeds_to_json(message) == expected_output, 'Expected JSON string with multiple embeds for message with multiple embeds'


# Test cases for create_message_element function

def test_create_message_element_text():
    message = {'text': 'Hello, world!'}
    assert create_message_element(message) == 'Hello, world!', 'Expected text element for message with text'


def test_create_message_element_content():
    message = {'content': 'Hello, world!'}
    assert create_message_element(message) == 'Hello, world!', 'Expected content element for message with content'


def test_create_message_element_no_text_or_content():
    message = {}
    with pytest.raises(KeyError):
        create_message_element(message)


# Test cases for is_human function

def test_is_human_name_human():
    message = {'name': 'Human'}
    assert is_human(message) == True, 'Expected True for message with name Human'


def test_is_human_sender_type_human():
    message = {'sender': {'type': 'HUMAN'}}
    assert is_human(message) == True, 'Expected True for message with sender type HUMAN'


def test_is_human_user_no_bot_id():
    message = {'user': 'User1', 'bot_id': None}
    assert is_human(message) == True, 'Expected True for message with user field and no bot_id field'


def test_is_human_not_human():
    message = {'name': 'Bot'}
    assert is_human(message) == False, 'Expected False for message not from a human'


# Test cases for is_bot function

def test_is_bot_name_bot():
    message = {'name': 'Bot'}
    assert is_bot(message) == True, 'Expected True for message with name Bot'


def test_is_bot_sender_type_bot():
    message = {'sender': {'type': 'BOT'}}
    assert is_bot(message) == True, 'Expected True for message with sender type BOT'


def test_is_bot_with_bot_id():
    message = {'bot_id': 'bot1'}
    assert is_bot(message) == True, 'Expected True for message with bot_id field'


def test_is_bot_not_bot():
    message = {'name': 'Human'}
    assert is_bot(message) == False, 'Expected False for message not from a bot'


# Test cases for is_ai function

def test_is_ai_name_ai():
    message = {'name': 'AI'}
    assert is_ai(message) == True, 'Expected True for message with name AI'


def test_is_ai_sender_type_bot():
    message = {'sender': {'type': 'BOT'}}
    assert is_ai(message) == True, 'Expected True for message with sender type BOT'


def test_is_ai_with_bot_id():
    message = {'bot_id': 'bot1'}
    assert is_ai(message) == True, 'Expected True for message with bot_id field'


def test_is_ai_not_ai():
    message = {'name': 'Human'}
    assert is_ai(message) == False, 'Expected False for message not from an AI'
