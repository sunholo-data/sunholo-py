import os
import json
import yaml
from datetime import datetime, timedelta
from collections import defaultdict
from yaml.constructor import SafeConstructor, ConstructorError

from .timedelta import format_timedelta

class ConfigManager:
    def __init__(self, vector_name: str, validate:bool=True):
        """
        Initialize the ConfigManager with a vector name.
        Requires a local config/ folder holding your configuration files or the env var VAC_CONFIG_FOLDER to be set.

        Read more at: https://dev.sunholo.com/docs/config

        Args:
            vector_name (str): The name of the vector in the configuration files.
            validate (bool): Whether to validate the configurations
        
        Example:
        ```python
        # Usage example:
        config = ConfigManager("my_vac")
        agent = config.vacConfig("agent")
        ```
        """
        if os.getenv("VAC_CONFIG_FOLDER") is None:
            print("WARNING: No VAC_CONFIG_FOLDER environment variable was specified")
        local_config_folder = os.path.join(os.getcwd(), "config")
        if not os.path.isdir(local_config_folder):
            local_config_folder = None
            
        if os.getenv("VAC_CONFIG_FOLDER") is None and local_config_folder is None:
            raise ValueError(f"Must have either a local config/ folder in this dir ({os.getcwd()}/config/) or a folder specified via the VAC_CONFIG_FOLDER environment variable, or both.")

        self.vector_name = vector_name
        self.config_cache = {}
        self.config_folder = os.getenv("VAC_CONFIG_FOLDER", os.getcwd())
        self.local_config_folder = local_config_folder
        self.configs_by_kind = self.load_all_configs()
        self.validate = validate

        test_agent = self.vacConfig("agent")
        if not test_agent and self.vector_name != "global" and self.validate:
            print(f"WARNING: No vacConfig.agent found for {self.vector_name} - are you in right folder? {local_config_folder=} {self.config_folder=}")

    def load_all_configs(self):
        """
        Load all configuration files from the specified directories into a dictionary.
        Caching is used to avoid reloading files within a 5-minute window.

        Returns:
            dict: A dictionary of configurations grouped by their 'kind' key.
        """
        from ..custom_logging import log

        log.debug(f"Loading all configs from folder: {self.config_folder} and local folder: {self.local_config_folder}")
        global_configs_by_kind = self._load_configs_from_folder(self.config_folder)

        if self.local_config_folder:
            local_configs_by_kind = self._load_configs_from_folder(self.local_config_folder)
            # Merge local configs into global configs
            for kind, local_config in local_configs_by_kind.items():
                if kind in global_configs_by_kind:
                    global_configs_by_kind[kind] = self._merge_dicts(global_configs_by_kind[kind], local_config)
                else:
                    global_configs_by_kind[kind] = local_config

        return global_configs_by_kind

    def _load_configs_from_folder(self, folder):
        """
        Load all configuration files from a specific folder into a dictionary.

        Args:
            folder (str): The path of the folder to load configurations from.

        Returns:
            dict: A dictionary of configurations grouped by their 'kind' key.
        """
        from ..custom_logging import log

        configs_by_kind = defaultdict(dict)
        current_time = datetime.now()
        
        for filename in os.listdir(folder):
            if filename in ["cloudbuild.yaml", "cloud_run_urls.json"]:
                continue
            if filename.endswith(('.yaml', '.yml', '.json')):
                config_file = os.path.join(folder, filename)
               
                if filename in self.config_cache:
                    cached_config, cache_time = self.config_cache[filename]
                    time_to_recache = (current_time - cache_time)
                    if time_to_recache < timedelta(minutes=5):
                        config = cached_config
                    else:
                        config = self._reload_config_file(config_file, filename, folder == self.local_config_folder)
                else:
                    config = self._reload_config_file(config_file, filename, folder == self.local_config_folder)
                if config is None:
                    log.error(f"No config found within {filename}")
                    continue
                kind = config.get('kind')
                if kind:
                    configs_by_kind[kind] = config
                else:
                    log.warning(f"No 'kind' found in {filename}")
        return configs_by_kind

    def _reload_config_file(self, config_file, filename, is_local=False):
        """
        Helper function to load a config file and update the cache.

        Args:
            config_file (str): The path to the configuration file.
            filename (str): The name of the configuration file.
            is_local (bool): Indicates if the config file is from the local folder.

        Returns:
            dict: The loaded configuration.
        """
        from ..custom_logging import log

        class NoDuplicateKeyConstructor(SafeConstructor):
            def construct_mapping(self, node, deep=False):
                mapping = {}
                for key_node, value_node in node.value:
                    key = self.construct_object(key_node, deep=deep)
                    if key in mapping:
                        raise ConstructorError(f"Duplicate key found: {key_node.start_mark}")
                    value = self.construct_object(value_node, deep=deep)
                    mapping[key] = value
                return mapping

        NoDuplicateKeyLoader = yaml.Loader
        NoDuplicateKeyLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            NoDuplicateKeyConstructor.construct_mapping
        )

        with open(config_file, 'r') as file:
            if filename.endswith('.json'):
                config = json.load(file)
            else:
                config = yaml.load(file, Loader=NoDuplicateKeyLoader)

        self.config_cache[filename] = (config, datetime.now())
        if is_local:
            log.info(f"Local configuration override for {filename} via {self.local_config_folder}")
        return config

    def _check_and_reload_configs(self):
        """
        Check if configurations are older than 5 minutes and reload if necessary.
        """
        current_time = datetime.now()
        for filename, (config, cache_time) in list(self.config_cache.items()):
            if (current_time - cache_time) >= timedelta(minutes=5):
                config_file_main = os.path.join(self.config_folder, filename)
                config_file_local = os.path.join(self.local_config_folder, filename)
                if os.path.exists(config_file_local):
                    self._reload_config_file(config_file_local, filename, is_local=True)
                if os.path.exists(config_file_main):
                    self._reload_config_file(config_file_main, filename, is_local=False)
        self.configs_by_kind = self.load_all_configs()

    def _merge_dicts(self, dict1, dict2):
        """
        Recursively merge two dictionaries. Local values in dict2 will overwrite global values in dict1.

        Args:
            dict1 (dict): The global dictionary.
            dict2 (dict): The local dictionary.

        Returns:
            dict: The merged dictionary.
        """
        for key, value in dict2.items():
            if isinstance(value, dict) and key in dict1 and isinstance(dict1[key], dict):
                dict1[key] = self._merge_dicts(dict1[key], value)
            else:
                dict1[key] = value
        return dict1

    def vacConfig(self, key: str):
        """
        Fetch a key from 'vacConfig' kind configuration.

        Args:
            key (str): The key to fetch from the configuration.

        Returns:
            str: The value associated with the specified key.
        """
        self._check_and_reload_configs()
        config = self.configs_by_kind.get('vacConfig')
        if not config:
            return None
        if self.vector_name == 'global':
            return config.get(key)
        vac = config['vac']

        vac_config = vac.get(self.vector_name)
        if not vac_config:
            return None
        return vac_config.get(key)

    def promptConfig(self, key: str):
        """
        Fetch a key from 'promptConfig' kind configuration.

        Args:
            key (str): The key to fetch from the configuration.

        Returns:
            str: The value associated with the specified key.
        """
        self._check_and_reload_configs()
        config = self.configs_by_kind.get('promptConfig')
        if not config:
            return None
        prompts = config['prompts']
        prompt_for_vector_name = prompts.get(self.vector_name)
        if not prompt_for_vector_name:
            return None
        return prompt_for_vector_name.get(key)

    def agentConfig(self, key: str):
        """
        Fetch a key from 'agentConfig' kind configuration.

        Args:
            key (str): The key to fetch from the configuration.

        Returns:
            str: The value associated with the specified key.
        """
        self._check_and_reload_configs()
        config = self.configs_by_kind.get('agentConfig')
        if not config:
            return None
        agents = config.get('agents')
        if key in agents:
            return agents[key]
        else:
            return agents.get("default")

