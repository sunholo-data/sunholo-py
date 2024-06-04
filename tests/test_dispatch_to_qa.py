import pytest
from unittest.mock import patch, MagicMock
from sunholo.agents import dispatch_to_qa
import aiohttp


def setup():
    user_input = 'mock_user_input'
    chat_history = 'mock_chat_history'
    vector_name = 'mock_vector_name'
    stream = 'mock_stream'
    return user_input, chat_history, vector_name, stream


def test_prep_request_payload():
    user_input, chat_history, vector_name, stream = setup()
    # Call 'prep_request_payload' with the mock data
    qna_endpoint, qna_data = dispatch_to_qa.prep_request_payload(user_input, chat_history, vector_name, stream)
    # Check the returned 'qna_endpoint' and 'qna_data'
    assert qna_endpoint == 'expected_qna_endpoint'
    assert qna_data == 'expected_qna_data'


@patch('sunholo.agents.dispatch_to_qa.requests.post')
def test_send_to_qa(mock_post):
    user_input, chat_history, vector_name, stream = setup()
    mock_qna_endpoint = 'http://mock.qna.endpoint'
    mock_response = {'status': 'success'}

    # Scenario where 'stream' is False
    mock_post.return_value.json.return_value = mock_response
    response = dispatch_to_qa.send_to_qa(user_input, chat_history, vector_name, stream)
    assert response == mock_response

    # Scenario where 'stream' is True and the response is a generator that yields response content chunks
    mock_response_chunk = 'mock_response_chunk'
    mock_post.return_value.iter_content.return_value = iter([mock_response_chunk.encode()])
    response = dispatch_to_qa.send_to_qa(user_input, chat_history, vector_name, True)
    assert next(response) == mock_response_chunk.encode()

    # Scenario where an HTTP error occurs
    mock_post.side_effect = Exception('HTTP Error')
    response = dispatch_to_qa.send_to_qa(user_input, chat_history, vector_name, stream)
    assert 'Error' in response

    # Scenario where any other error occurs
    mock_post.side_effect = Exception('ReadTimeout')
    response = dispatch_to_qa.send_to_qa(user_input, chat_history, vector_name, stream)
    assert 'Error' in response


@pytest.mark.asyncio
@patch('sunholo.agents.dispatch_to_qa.aiohttp.ClientSession.post')
async def test_send_to_qa_async(mock_post):
    user_input, chat_history, vector_name, stream = setup()
    mock_qna_endpoint = 'http://mock.qna.endpoint'
    mock_response = {'status': 'success'}

    async def mock_coro(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.json = MagicMock(return_value=mock_response)
        return mock_resp

    mock_post.side_effect = mock_coro

    async with aiohttp.ClientSession() as session:
        async with session.post(mock_qna_endpoint, json=mock_response) as resp:
            response = await dispatch_to_qa.send_to_qa_async(user_input, chat_history, vector_name, stream)
            assert response == mock_response

    # Scenario where an HTTP error occurs
    mock_post.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=MagicMock(), status=500, message="Internal Server Error"
    )
    response = await dispatch_to_qa.send_to_qa_async(user_input, chat_history, vector_name, stream)
    assert 'Error' in response

    # Scenario where any other error occurs
    mock_post.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=MagicMock(), status=400, message="Bad Request"
    )
    response = await dispatch_to_qa.send_to_qa_async(user_input, chat_history, vector_name, stream)
    assert 'Error' in response