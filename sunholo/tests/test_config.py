import pytest
from unittest.mock import patch, mock_open
from utils import config

@patch('google.cloud.storage.Client')
def test_fetch_config(mock_client):
    # Create a mock bucket and blob
    mock_bucket = Mock()
    mock_blob = Mock()
    mock_client.get_bucket.return_value = mock_bucket
    mock_bucket.get_blob.return_value = mock_blob

    # Test that the function correctly fetches the blob and returns the updated time
    mock_blob.updated = '2022-01-01T00:00:00Z'
    result = config.fetch_config('bucket_name', 'blob_name')
    assert result == '2022-01-01T00:00:00Z'

    # Test the case where the blob does not exist and the function should return None
    mock_bucket.get_blob.return_value = None
    result = config.fetch_config('bucket_name', 'blob_name')
    assert result == None

@patch('os.path.isfile')
def test_get_module_filepath(mock_isfile):
    # Test that the function correctly returns the full file path of the mock file
    mock_isfile.return_value = True
    result = config.get_module_filepath('mock_file')
    assert result == '/path/to/mock_file'

    # Test the case where the file does not exist and the function should raise an error
    mock_isfile.return_value = False
    with pytest.raises(FileNotFoundError):
        config.get_module_filepath('non_existent_file')

@patch('os.path.isfile')
@patch('os.environ')
@patch('builtins.open', new_callable=mock_open, read_data='mock_file_content')
def test_load_config(mock_open, mock_environ, mock_isfile):
    # Test that the function correctly loads the mock configuration file
    mock_isfile.return_value = True
    mock_environ.get.return_value = 'mock_file_path'
    result = config.load_config('mock_file_path')
    assert result == 'mock_file_content'

    # Test the case where the file does not exist and the function should raise an error
    mock_isfile.return_value = False
    with pytest.raises(FileNotFoundError):
        config.load_config('non_existent_file')

    # Test the case where the environment variable is not set and the function should raise an error
    mock_environ.get.return_value = None
    with pytest.raises(EnvironmentError):
        config.load_config('mock_file_path')

@patch('os.path.isfile')
@patch('os.environ')
@patch('builtins.open', new_callable=mock_open, read_data='mock_file_content')
def test_load_config_key(mock_open, mock_environ, mock_isfile):
    # Test that the function correctly loads a specific key from the mock configuration file
    mock_isfile.return_value = True
    mock_environ.get.return_value = 'mock_file_path'
    result = config.load_config_key('mock_file_path', 'mock_key')
    assert result == 'mock_key_value'

    # Test the case where the key does not exist in the configuration file and the function should raise an error
    with pytest.raises(KeyError):
        config.load_config_key('mock_file_path', 'non_existent_key')

