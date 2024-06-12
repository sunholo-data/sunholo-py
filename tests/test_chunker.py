import pytest
from unittest.mock import patch, MagicMock
from sunholo.chunker.data_to_embed_pubsub import data_to_embed_pubsub
from sunholo.chunker.doc_handling import send_doc_to_docstore, create_big_doc, summarise_docs
from sunholo.chunker.images import upload_doc_images

# Existing test for data_to_embed_pubsub function
@patch('sunholo.chunker.data_to_embed_pubsub.process_pubsub_message', return_value=({}, {}, 'test_vector'))
@patch('sunholo.chunker.data_to_embed_pubsub.process_chunker_data', return_value='processed_data')
def test_data_to_embed_pubsub(mock_process_chunker_data, mock_process_pubsub_message):
    assert data_to_embed_pubsub({}) == 'processed_data'
    assert data_to_embed_pubsub({'key': 'value'}) == 'processed_data'
    mock_process_pubsub_message.assert_called()
    mock_process_chunker_data.assert_called()

# New tests for send_doc_to_docstore function
@patch('sunholo.chunker.doc_handling.add_document_if_not_exists', return_value='doc_id')
def test_send_doc_to_docstore(mock_add_document_if_not_exists):
    docs = [{'page_content': 'content', 'metadata': {'source': 'test_source'}}]
    vector_name = 'test_vector'
    doc_id, processed_docs = send_doc_to_docstore(docs, vector_name)
    assert doc_id == 'doc_id'
    assert processed_docs == docs
    mock_add_document_if_not_exists.assert_called_once()

# New tests for create_big_doc function
def test_create_big_doc():
    docs = [{'page_content': 'content1', 'metadata': {'source': 'test_source1'}},
            {'page_content': 'content2', 'metadata': {'source': 'test_source2'}}]
    doc_id, big_doc, processed_docs = create_big_doc(docs)
    assert doc_id is not None
    assert big_doc.page_content == 'content1\ncontent2'
    assert len(processed_docs) == 2

# New tests for summarise_docs function
@patch('sunholo.chunker.doc_handling.llm_str_to_llm', return_value=MagicMock())
def test_summarise_docs(mock_llm_str_to_llm):
    docs = [{'page_content': 'content', 'metadata': {'source': 'test_source'}}]
    vector_name = 'test_vector'
    summaries = summarise_docs(docs, vector_name)
    assert len(summaries) == 1
    mock_llm_str_to_llm.assert_called_once()

# New tests for upload_doc_images function
@patch('sunholo.chunker.images.add_file_to_gcs', return_value='gs://bucket/image.jpg')
def test_upload_doc_images(mock_add_file_to_gcs):
    metadata = {'image_base64': 'base64imagestring', 'vector_name': 'test_vector', 'bucket_name': 'bucket'}
    gsurl = upload_doc_images(metadata)
    assert gsurl == 'gs://bucket/image.jpg'
    assert 'image_base64' not in metadata  # Ensure image_base64 is removed
    assert metadata['uploaded_to_bucket'] is True
    mock_add_file_to_gcs.assert_called_once()
