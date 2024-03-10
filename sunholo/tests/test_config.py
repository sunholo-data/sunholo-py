import unittest
import mock
from utils import config

class TestConfig(unittest.TestCase):
    
    def test_fetch_config_blob_exists(self):
        mock_blob = mock.Mock()
        mock_blob.download_as_text.return_value = '{"key": "value"}'
        result = config.fetch_config(mock_blob)
        self.assertEqual(result, {"key": "value"})

    def test_fetch_config_blob_not_exists(self):
        mock_blob = mock.Mock()
        mock_blob.download_as_text.side_effect = google.cloud.exceptions.NotFound
        with self.assertRaises(config.ConfigNotFoundError):
            config.fetch_config(mock_blob)

    def test_fetch_config_logging(self):
        mock_logger = mock.Mock()
        config.logger = mock_logger
        mock_blob = mock.Mock()
        config.fetch_config(mock_blob)
        mock_logger.info.assert_called_with('Fetching config from blob.')
        mock_logger.error.assert_called_with('Config not found.')
    def test_get_module_filepath(self):
        mock_module = mock.Mock()
        mock_module.__file__ = '/path/to/module.py'
        result = config.get_module_filepath(mock_module)
        self.assertEqual(result, '/path/to/module.py')
    def test_get_module_filepath_logging(self):
        mock_logger = mock.Mock()
        config.logger = mock_logger
        mock_module = mock.Mock()
        config.get_module_filepath(mock_module)
        mock_logger.info.assert_called_with('Getting module filepath.')

    def test_load_config_json(self):
        mock_file = mock.Mock()
        mock_file.read.return_value = '{"key": "value"}'
        mock_logger = mock.Mock()
        config.logger = mock_logger
        result = config.load_config(mock_file)
        self.assertEqual(result, {"key": "value"})
        mock_logger.info.assert_called_with('Loading config from file.')

    def test_load_config_yaml(self):
        mock_file = mock.Mock()
        mock_file.read.return_value = 'key: value'
        mock_logger = mock.Mock()
        config.logger = mock_logger
        result = config.load_config(mock_file)
        self.assertEqual(result, {'key': 'value'})
        mock_logger.info.assert_called_with('Loading config from file.')

    def test_load_config_cache(self):
        mock_file = mock.Mock()
        mock_file.read.return_value = '{"key": "value"}'
        mock_logger = mock.Mock()
        config.logger = mock_logger
        result1 = config.load_config(mock_file)
        result2 = config.load_config(mock_file)
        self.assertEqual(result1, {"key": "value"})
        self.assertEqual(result2, {"key": "value"})
        mock_logger.info.assert_called_with('Loading config from file.')
        mock_logger.info.assert_called_with('Returning cached config.')

    def test_load_config_file_not_exists(self):
        mock_logger = mock.Mock()
        config.logger = mock_logger
        with self.assertRaises(config.ConfigNotFoundError):
            config.load_config('nonexistent_file')
        mock_logger.error.assert_called_with('Config file not found.')

    def test_load_config_invalid_format(self):
        mock_file = mock.Mock()
        mock_file.read.return_value = 'invalid_format'
        mock_logger = mock.Mock()
        config.logger = mock_logger
        with self.assertRaises(config.ConfigFormatError):
            config.load_config(mock_file)
        mock_logger.error.assert_called_with('Invalid config format.')

    def test_load_config_key(self):
        mock_file = mock.Mock()
        mock_file.read.return_value = '{"key": "value"}'
        result = config.load_config_key(mock_file, 'key')
        self.assertEqual(result, 'value')

    def test_load_config_key_not_exists(self):
        mock_file = mock.Mock()
        mock_file.read.return_value = '{"key": "value"}'
        with self.assertRaises(config.ConfigKeyNotFoundError):
            config.load_config_key(mock_file, 'nonexistent_key')

    def test_load_config_key_logging(self):
        mock_logger = mock.Mock()
        config.logger = mock_logger
        mock_file = mock.Mock()
        config.load_config_key(mock_file, 'key')
        mock_logger.info.assert_called_with('Loading config key from file.')
