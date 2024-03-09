import pytest
import requests_mock
from sunholo.agents import dispatch_to_qa


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


def test_send_to_qa():
    user_input, chat_history, vector_name, stream = setup()
    mock_qna_endpoint = 'http://mock.qna.endpoint'
    mock_response = {'status': 'success'}
    with requests_mock.Mocker() as m:
        m.post(mock_qna_endpoint, json=mock_response)
        response = dispatch_to_qa.send_to_qa(user_input, chat_history, vector_name, stream)
        assert response == mock_response

    # Scenario where 'stream' is True and the response is a generator that yields response content chunks
    mock_response_chunk = 'mock_response_chunk'
    m.post(mock_qna_endpoint, text=mock_response_chunk)
    response = dispatch_to_qa.send_to_qa(user_input, chat_history, vector_name, True)
    assert next(response) == mock_response_chunk

    # Scenario where an HTTP error occurs
    m.post(mock_qna_endpoint, status_code=500)
    response = dispatch_to_qa.send_to_qa(user_input, chat_history, vector_name, stream)
    assert 'Error' in response

    # Scenario where any other error occurs
    m.post(mock_qna_endpoint, exc=requests_mock.exceptions.ReadTimeout)
    response = dispatch_to_qa.send_to_qa(user_input, chat_history, vector_name, stream)
    assert 'Error' in response


def test_send_to_qa_async():
    user_input, chat_history, vector_name, stream = setup()
    mock_qna_endpoint = 'http://mock.qna.endpoint'
    mock_response = {'status': 'success'}
    import aiohttp

    @pytest.mark.asyncio
    async def test_send_to_qa_async():
        user_input, chat_history, vector_name, stream = setup()
        mock_qna_endpoint = 'http://mock.qna.endpoint'
        mock_response = {'status': 'success'}
        async with aiohttp.ClientSession() as session:
            async with session.post(mock_qna_endpoint, json=mock_response) as resp:
                response = await dispatch_to_qa.send_to_qa_async(user_input, chat_history, vector_name, stream)
                assert response == mock_response

        # Scenario where an HTTP error occurs
        async with session.post(mock_qna_endpoint, status=500) as resp:
            response = await dispatch_to_qa.send_to_qa_async(user_input, chat_history, vector_name, stream)
            assert 'Error' in response

        # Scenario where any other error occurs
        async with session.post(mock_qna_endpoint, raise_for_status=False) as resp:
            response = await dispatch_to_qa.send_to_qa_async(user_input, chat_history, vector_name, stream)
            assert 'Error' in response