#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sunholo.utils.config_class import ConfigManager


class TestConfigManagerCaching:
    """Test suite for ConfigManager caching functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing cache
        ConfigManager.clear_instance_cache()
        
        # Create temporary directories for config files
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, "config")
        os.makedirs(self.config_dir)
        
        # Create sample config files
        self.create_sample_configs()
        
    def teardown_method(self):
        """Cleanup after each test method"""
        # Clear instance cache
        ConfigManager.clear_instance_cache()
        
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_sample_configs(self):
        """Create sample configuration files for testing"""
        # vac_config.yaml
        vac_config = {
            "apiVersion": "v1",
            "kind": "vacConfig",
            "vac": {
                "test_vac": {
                    "agent": "test_agent",
                    "llm": "test_llm",
                    "vector_name": "test_vector"
                },
                "empty_vac": {
                    "agent": None,
                    "llm": None
                }
            }
        }
        with open(os.path.join(self.config_dir, "vac_config.yaml"), "w") as f:
            import yaml
            yaml.dump(vac_config, f)
        
        # agent_config.yaml
        agent_config = {
            "apiVersion": "v1", 
            "kind": "agentConfig",
            "agents": {
                "test_agent": "test_endpoint",
                "default": "default_endpoint"
            }
        }
        with open(os.path.join(self.config_dir, "agent_config.yaml"), "w") as f:
            yaml.dump(agent_config, f)
        
        # prompt_config.yaml  
        prompt_config = {
            "apiVersion": "v1",
            "kind": "promptConfig", 
            "prompts": {
                "test_vac": {
                    "system": "test_system_prompt",
                    "user": "test_user_prompt"
                }
            }
        }
        with open(os.path.join(self.config_dir, "prompt_config.yaml"), "w") as f:
            yaml.dump(prompt_config, f)
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_instance_caching_basic(self):
        """Test basic instance caching functionality"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            # Create first instance
            config1 = ConfigManager("test_vac", validate=False)
            
            # Create second instance with same parameters
            config2 = ConfigManager("test_vac", validate=False)
            
            # Should return the same cached instance
            assert config1 is config2
            
            # Create instance with different parameters
            config3 = ConfigManager("test_vac", validate=True)
            
            # Should be a different instance (different cache key)
            assert config1 is not config3
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_instance_cache_expiration(self):
        """Test that instance cache expires correctly"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            # Mock datetime to control cache expiration
            mock_time = datetime.now()
            with patch('sunholo.utils.config_class.datetime') as mock_datetime:
                mock_datetime.now.return_value = mock_time
                
                # Create instance
                config1 = ConfigManager("test_vac", validate=False)
                cache_info = ConfigManager.get_cached_instances()
                assert len(cache_info) == 1
                
                # Advance time beyond cache duration (30 minutes + 1 second)
                expired_time = mock_time + timedelta(minutes=30, seconds=1)
                mock_datetime.now.return_value = expired_time
                
                # Create new instance - should create new one due to expiration
                config2 = ConfigManager("test_vac", validate=False)
                
                # Should be different instances due to cache expiration
                assert config1 is not config2
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_config_reload_expiration(self):
        """Test that config files are reloaded when cache expires"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            config = ConfigManager("test_vac", validate=False)
            
            # Get initial value
            initial_agent = config.vacConfig("agent")
            assert initial_agent == "test_agent"
            
            # Modify config file
            vac_config = {
                "apiVersion": "v1",
                "kind": "vacConfig",
                "vac": {
                    "test_vac": {
                        "agent": "modified_agent",
                        "llm": "test_llm",
                        "vector_name": "test_vector"
                    }
                }
            }
            with open(os.path.join(self.config_dir, "vac_config.yaml"), "w") as f:
                import yaml
                yaml.dump(vac_config, f)
            
            # Mock time to trigger config reload (5 minutes + 1 second)
            future_time = datetime.now() + timedelta(minutes=5, seconds=1)
            with patch('sunholo.utils.config_class.datetime') as mock_datetime:
                mock_datetime.now.return_value = future_time
                
                # Should reload and return new value
                updated_agent = config.vacConfig("agent")
                assert updated_agent == "modified_agent"
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_empty_results_issue(self):
        """Test scenarios that could cause empty results"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            config = ConfigManager("test_vac", validate=False)
            
            # Test normal operation
            agent = config.vacConfig("agent")
            assert agent == "test_agent"
            
            # Test with non-existent vac name
            config_missing = ConfigManager("missing_vac", validate=False)
            missing_agent = config_missing.vacConfig("agent")
            assert missing_agent is None
            
            # Test with vac that has None values
            config_empty = ConfigManager("empty_vac", validate=False)
            empty_agent = config_empty.vacConfig("agent")
            assert empty_agent is None
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_cache_corruption_scenario(self):
        """Test scenario where cache might get corrupted"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            config = ConfigManager("test_vac", validate=False)
            
            # Manually corrupt the config cache
            config.config_cache = {}
            config.configs_by_kind = {}
            
            # Should still work by reloading
            agent = config.vacConfig("agent")
            assert agent == "test_agent"
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_concurrent_access_simulation(self):
        """Test simulated concurrent access to cached instances"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            # Simulate multiple threads accessing the same instance
            instances = []
            for i in range(5):
                instance = ConfigManager("test_vac", validate=False)
                instances.append(instance)
            
            # All should be the same cached instance
            for instance in instances[1:]:
                assert instances[0] is instance
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_cache_clear_functionality(self):
        """Test cache clearing functionality"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            # Create multiple instances
            config1 = ConfigManager("test_vac", validate=False)
            config2 = ConfigManager("test_vac", validate=True)
            config3 = ConfigManager("other_vac", validate=False)
            
            cache_info = ConfigManager.get_cached_instances()
            assert len(cache_info) == 3
            
            # Clear specific instance
            ConfigManager.clear_instance_cache("test_vac", validate=False)
            cache_info = ConfigManager.get_cached_instances()
            assert len(cache_info) == 2
            
            # Clear all instances for vector_name
            ConfigManager.clear_instance_cache("test_vac")
            cache_info = ConfigManager.get_cached_instances()
            assert len(cache_info) == 1
            
            # Clear all cache
            ConfigManager.clear_instance_cache()
            cache_info = ConfigManager.get_cached_instances()
            assert len(cache_info) == 0
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_initialization_flag_issue(self):
        """Test the _initialized flag doesn't cause issues with caching"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            # Create instance
            config1 = ConfigManager("test_vac", validate=False)
            assert hasattr(config1, '_initialized')
            assert config1._initialized is True
            
            # Get cached instance
            config2 = ConfigManager("test_vac", validate=False)
            assert config1 is config2
            assert hasattr(config2, '_initialized')
            assert config2._initialized is True
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    @patch('sunholo.utils.config_class.os.path.exists')
    def test_missing_config_files(self, mock_exists):
        """Test behavior when config files are missing"""
        # Mock file existence to return False for some files
        mock_exists.return_value = False
        
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            with patch('sunholo.utils.config_class.os.listdir') as mock_listdir:
                mock_listdir.return_value = []  # No config files
                
                config = ConfigManager("test_vac", validate=False)
                
                # Should return None when no configs exist
                agent = config.vacConfig("agent")
                assert agent is None
    
    @patch.dict(os.environ, {"VAC_CONFIG_FOLDER": ""})
    def test_file_modification_during_cache(self):
        """Test behavior when files are modified during cache lifetime"""
        with patch.dict(os.environ, {"VAC_CONFIG_FOLDER": self.config_dir}):
            config = ConfigManager("test_vac", validate=False)
            
            # Get initial value
            initial_agent = config.vacConfig("agent")
            assert initial_agent == "test_agent"
            
            # Delete the config file
            os.remove(os.path.join(self.config_dir, "vac_config.yaml"))
            
            # Should still return cached value initially
            cached_agent = config.vacConfig("agent")
            assert cached_agent == "test_agent"
            
            # Clear cache and try again
            config.config_cache.clear()
            config.configs_by_kind.clear()
            
            # Should return None now
            missing_agent = config.vacConfig("agent")
            assert missing_agent is None