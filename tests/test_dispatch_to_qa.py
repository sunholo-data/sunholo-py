import pytest
from unittest.mock import patch
from sunholo.agents.dispatch_to_qa import prep_request_payload

@pytest.mark.parametrize("user_input, chat_history, vector_name, stream, expected_endpoint, expected_payload", [
    ("What is AI?", [], "my_vector", False, "http://example.com/invoke", {"user_input": "What is AI?", "chat_history": [], "vector_name": "my_vector"}),
    ("Tell me about ML", ["Previous chat message"], "another_vector", True, "http://example.com/stream", {"user_input": "Tell me about ML", "chat_history": ["Previous chat message"], "vector_name": "another_vector"}),
    # Additional test cases to cover all logic paths
    ("", [], "empty_input_vector", False, "http://example.com/invoke", {"user_input": "", "chat_history": [], "vector_name": "empty_input_vector"}),
    ("Valid input", ["Chat history present"], "history_vector", False, "http://example.com/invoke", {"user_input": "Valid input", "chat_history": ["Chat history present"], "vector_name": "history_vector"}),
    ("Stream request", [], "stream_vector", True, "http://example.com/stream", {"user_input": "Stream request", "chat_history": [], "vector_name": "stream_vector"})
])
@patch('sunholo.agents.dispatch_to_qa.load_config_key')
@patch('sunholo.agents.dispatch_to_qa.route_endpoint')
def test_prep_request_payload(mock_route_endpoint, mock_load_config_key, user_input, chat_history, vector_name, stream, expected_endpoint, expected_payload):
    mock_route_endpoint.return_value = {"invoke": "http://example.com/invoke", "stream": "http://example.com/stream"}
    mock_load_config_key.side_effect = lambda key, vector_name=None, kind=None: "my_vector" if key == "vector_name" else None

    endpoint, payload = prep_request_payload(user_input, chat_history, vector_name, stream)

    assert endpoint == expected_endpoint
    assert payload == expected_payload
