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

# Test cases for load_config_key function
@patch("sunholo.utils.config.load_all_configs")
def test_load_config_key(mock_load_all_configs):
    mock_load_all_configs.return_value = {
        "vacConfig": {
            "vac": {
                "test_vector": {
                    "key1": "value1",
                    "key2": "value2"
                }
            }
        }
    }
    # Test existing key
    assert config.load_config_key("key1", "test_vector", "vacConfig") == "value1"
    # Test non-existing key
    result = config.load_config_key("non_existing_key", "test_vector", "vacConfig")
    assert result is None

    # Test invalid configuration
    with pytest.raises(KeyError):
        config.load_config_key("key1", "test_vector", "invalidConfig")
