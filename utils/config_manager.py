import logging
import threading
import utils.database as db

class ConfigManager:
    _instance = None
    _lock = threading.Lock()
    _config = {}
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
                    # cls._instance.load_config()
        return cls._instance

    def initialize_config(self):
        """
        在数据库表创建完成后，被显式调用以初始化配置。
        确保只加载一次。
        """
        if not self._is_initialized:
            with self._lock: # 再次加锁确保多线程安全
                if not self._is_initialized:
                    print("Initializing configuration after tables created...")
                    self.load_config()
                    self._is_initialized = True
        else:
            print("ConfigManager already initialized.")

    def load_config(self):
        """Loads configuration from the database."""
        print("Loading configuration from database...")
        self._config = db.get_all_settings()
        print(f"Configuration loaded. Current config: {self._config}")

    def get(self, key: str, default=None):
        """Gets a configuration value by key."""
        return self._config.get(key, default)

    def get_all(self):
        """Gets the entire configuration dictionary."""
        return self._config

    def is_configured(self) -> bool:
        """
        Checks if essential settings are present.
        Essential for now: LLM, Embedding, Rerank models.
        """
        print(f"Checking if configured. Current config: {self._config}")
        retrieval_mode = self.get('retrieval_version', 'v1') # Default to v1 if not set
        print(f"DEBUG: retrieval_mode after get: '{retrieval_mode}', type: {type(retrieval_mode)}")

        required_keys = [
            'llm_model_name', 'llm_base_url', 'llm_api_key',
            'embedding_model_name', 'embedding_base_url', 'embedding_api_key',
        ]
        if retrieval_mode == 'v1':
            required_keys.extend(['rerank_model_name', 'rerank_base_url', 'rerank_api_key'])

        all_present = True
        for key in required_keys:
            value = self.get(key)
            if not value:
                print(f"Required key '{key}' is missing or empty. Value: '{value}'")
                all_present = False
            else:
                print(f"Required key '{key}' found with value: '{value}'")
        google_search_enabled_val = self.get('google_search_enabled', 'false')
        google_search_enabled = str(google_search_enabled_val).lower() == 'true'
        if google_search_enabled:
            google_keys = ['google_api_key', 'google_cse_id']
            for key in google_keys:
                value = self.get(key)
                if not value:
                    print(f"Google search enabled, but required key '{key}' is missing or empty. Value: '{value}'")
                    logging.error(f"Google search enabled, but required key '{key}' is missing or empty. Value: '{value}'")
                    all_present = False
                else:
                    print(f"Google search enabled, required key '{key}' found with value: '{value}'")
                    logging.info(f"Google search enabled, required key '{key}' found with value: '{value}'")
        else:
            logging.info("Google search disabled")
        print(f"Final configured status: {all_present}")
        logging.info(f"Final configured status: {all_present}")
        return all_present
config = ConfigManager()

if __name__ == '__main__':
    db.create_tables()
    mock_settings = {
        'llm_model_name': 'qwen-turbo',
        'llm_base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'llm_api_key': 'sk-test-key-llm',
        'embedding_model_name': 'text-embedding-v4',
        'embedding_base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings',
        'embedding_api_key': 'sk-test-key-embedding',
        'rerank_model_name': 'BAAI/bge-reranker-v2-m3',
        'rerank_base_url': 'https://api.siliconflow.cn/v1/rerank',
        'rerank_api_key': 'sk-test-key-rerank',
        'google_search_enabled': 'false',
        'google_api_key': '',
        'google_cse_id': ''
    }
    
    db.save_settings(mock_settings)
    print("Mock settings saved.")
    config_manager = ConfigManager()
    
    print("\n--- Testing ConfigManager ---")
    print(f"Is configured? {config_manager.is_configured()}")
    print(f"LLM Model: {config_manager.get('llm_model_name')}")
    print(f"Google Enabled: {config_manager.get('google_search_enabled', 'false')}")
    print(f"Non-existent key: {config_manager.get('non_existent_key', 'default_value')}")
    print("---------------------------\n")
    db.save_settings({'llm_model_name': 'new-model'})
    config_manager.load_config()
    print("Reloaded config.")
    print(f"New LLM Model: {config_manager.get('llm_model_name')}") 