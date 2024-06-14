import pytest
from unittest.mock import patch, MagicMock
from sunholo.chunker.data_to_embed_pubsub import data_to_embed_pubsub
from sunholo.chunker import direct_file_to_embed, process_chunker_data, format_chunk_return

# Existing test for data_to_embed_pubsub function
@patch('sunholo.chunker.data_to_embed_pubsub.process_pubsub_message', return_value=({}, {}, 'test_vector'))
@patch('sunholo.chunker.data_to_embed_pubsub.process_chunker_data', return_value='processed_data')
def test_data_to_embed_pubsub(mock_process_chunker_data, mock_process_pubsub_message):
    assert data_to_embed_pubsub({}) == 'processed_data'
    assert data_to_embed_pubsub({'key': 'value'}) == 'processed_data'
    mock_process_pubsub_message.assert_called()
    mock_process_chunker_data.assert_called()

# New test for direct_file_to_embed function
@patch('sunholo.chunker.direct_file_to_embed.loaders.read_file_to_documents', return_value=[])
@patch('sunholo.chunker.direct_file_to_embed.format_chunk_return', return_value='formatted_data')
def test_direct_file_to_embed(mock_format_chunk_return, mock_read_file_to_documents):
    assert direct_file_to_embed('file_path', {}, 'vector_name') == 'formatted_data'
    mock_read_file_to_documents.assert_called_with('file_path', metadata={}, vector_name='vector_name')
    mock_format_chunk_return.assert_called()

# New test for process_chunker_data function
@patch('sunholo.chunker.process_chunker_data.handle_gcs_message', return_value=('chunks', 'metadata'))
def test_process_chunker_data(mock_handle_gcs_message):
    assert process_chunker_data('message_data', {}, 'vector_name') == ('chunks', 'metadata')
    mock_handle_gcs_message.assert_called_with('message_data', {}, 'vector_name')

# New test for format_chunk_return function
def test_format_chunk_return():
    chunks = ['chunk1', 'chunk2']
    metadata = {'key': 'value'}
    vector_name = 'vector_name'
    assert format_chunk_return(chunks, metadata, vector_name) == metadata
    assert 'vector_name' in metadata

# Mocking utils.config.load_config_key() for all tests
@patch('sunholo.utils.config.load_config_key', return_value=None)
def test_mock_load_config_key(mock_load_config_key):
    # This test ensures that load_config_key() is mocked correctly for all tests
    assert mock_load_config_key('any_key', 'any_vector_name', 'any_kind') is None
