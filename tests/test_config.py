import pytest
from unittest.mock import patch, mock_open
from sunholo.utils import config

def test_load_config():
    expected_config = {"key": "value"}
    with pytest.raises(FileNotFoundError):
        config.load_config("non_existent_file")
    with patch("builtins.open", mock_open(read_data="key: value"), create=True):
        result = config.load_config("mock_file")
        assert result == expected_config

def test_load_config_key():
    expected_value = "value"
    with pytest.raises(KeyError):
        config.load_config_key("non_existent_key", "mock_vector_name")

def test_get_module_filepath():
    expected_path = "/absolute/path/to/module/file"
    with patch("os.path.dirname", return_value="/absolute/path/to"):
        result = config.get_module_filepath("module_name")
        assert result == expected_path

def test_fetch_config():
    expected_update_time = "2022-01-01T00:00:00Z"
    with patch("google.cloud.storage.Client") as mock_client:
        mock_bucket = mock_client.return_value.bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        mock_blob.download_as_text.return_value = "key: value"
        result = config.fetch_config("bucket_name", "blob_name")
        assert result == {"key": "value"}