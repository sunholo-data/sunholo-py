import pytest
from unittest.mock import patch, mock_open
from sunholo.utils import config

def test_load_config():
    expected_config = {"key": "value"}
    with pytest.raises(FileNotFoundError):
        config.load_config("non_existent_file")
    with patch("builtins.open", mock_open(read_data='{"key": "value"}'), create=True):
        result, _ = config.load_config("mock_file.json")
        assert result == expected_config
