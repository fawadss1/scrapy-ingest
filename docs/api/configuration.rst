Configuration API Reference
============================

Minimal, auto-generated docs for configuration.

.. currentmodule:: scrapy_item_ingest.config.settings

Settings
--------

.. autoclass:: Settings
   :members:
   :show-inheritance:

Utilities
---------

.. autofunction:: validate_settings

Notes
-----
- Configure DB via `DB_URL` or discrete fields (`DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).
- `DB_TYPE` defaults to `postgres` (aliases: `postgresql`).
- Default tables: `jobs`, `job_items`, `job_requests`, `job_logs`.
- See `configuration` and `quickstart` for practical examples.

      :type: dict
      :default: {'size': 100, 'timeout': 30}

      **Configuration:**

      .. code-block:: python

         BATCH_SETTINGS = {
             'size': 1000,         # Items per batch
             'timeout': 60,        # Batch timeout in seconds
             'max_memory': 512,    # Max memory per batch (MB)
         }

   **Methods:**

   .. method:: validate()

      Validate all configuration settings.

      :returns: List of validation errors
      :rtype: list[str]
      :raises: ConfigurationError if critical settings are invalid

      **Example:**

      .. code-block:: python

         settings = Settings()
         errors = settings.validate()
         if errors:
             raise ConfigurationError(f"Configuration errors: {errors}")

   .. method:: from_crawler_settings(crawler_settings)

      Create Settings instance from Scrapy crawler settings.

      :param crawler_settings: Scrapy settings object
      :type crawler_settings: scrapy.settings.Settings
      :returns: Configured Settings instance
      :rtype: Settings

   .. method:: get_database_url()

      Get database URL with environment variable substitution.

      :returns: Processed database URL
      :rtype: str
      :raises: ConfigurationError if URL is invalid

   .. method:: get_table_name(table_type)

      Get table name for specified table type.

      :param table_type: Type of table ('items', 'requests', 'logs')
      :type table_type: str
      :returns: Table name
      :rtype: str

Validation Functions
-------------------

Settings Validation
~~~~~~~~~~~~~~~~~~

.. autofunction:: validate_settings

   Comprehensive validation of pipeline settings.

   :param settings: Settings object or Scrapy settings
   :type settings: Settings or scrapy.settings.Settings
   :returns: List of validation errors
   :rtype: list[str]

   **Validation Checks:**

   * Database URL format and connectivity
   * Required settings presence
   * Type validation for all settings
   * Range validation for numeric settings
   * Table name validity

   **Example Usage:**

   .. code-block:: python

      from scrapy_item_ingest.config import validate_settings

      def check_configuration(settings):
          errors = validate_settings(settings)
          if errors:
              print("Configuration errors found:")
              for error in errors:
                  print(f"  - {error}")
              return False
          return True

.. autofunction:: validate_database_url

   Validate PostgreSQL database URL format.

   :param db_url: Database connection string
   :type db_url: str
   :returns: True if valid, False otherwise
   :rtype: bool

   **Validation Rules:**

   * Must start with 'postgresql://' or 'postgres://'
   * Must include username and password
   * Host and port must be valid
   * Database name must be specified

.. autofunction:: validate_table_names

   Validate custom table names.

   :param table_names: Dictionary of table names
   :type table_names: dict
   :returns: List of validation errors
   :rtype: list[str]

   **Validation Rules:**

   * Table names must be valid SQL identifiers
   * No SQL keywords allowed
   * Maximum length restrictions
   * Character restrictions (alphanumeric and underscore only)

Configuration Loaders
---------------------

Environment Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: EnvironmentConfigLoader
   :members:
   :undoc-members:

   Load configuration from environment variables with type conversion.

   **Supported Environment Variables:**

   .. code-block:: bash

      # Database configuration
      SCRAPY_DB_URL=postgresql://user:pass@host:5432/db
      SCRAPY_CREATE_TABLES=true
      SCRAPY_JOB_ID=production_job_001

      # Advanced settings
      SCRAPY_POOL_SIZE=20
      SCRAPY_BATCH_SIZE=1000
      SCRAPY_LOG_LEVEL=INFO

   **Methods:**

   .. method:: load()

      Load configuration from environment variables.

      :returns: Configuration dictionary
      :rtype: dict

   .. method:: get_with_type(key, default=None, value_type=str)

      Get environment variable with type conversion.

      :param key: Environment variable name
      :type key: str
      :param default: Default value if not found
      :param value_type: Type to convert to
      :type value_type: type
      :returns: Converted value
      :raises: ValueError if conversion fails

File Configuration
~~~~~~~~~~~~~~~~

.. autoclass:: FileConfigLoader
   :members:
   :undoc-members:

   Load configuration from YAML or JSON files.

   **Supported Formats:**

   .. code-block:: yaml

      # config.yaml
      database:
        url: postgresql://user:pass@localhost:5432/scrapy
        create_tables: true
        pool_size: 20

      job:
        id: yaml_config_job
        batch_size: 500

      tables:
        items: custom_items_table
        requests: custom_requests_table
        logs: custom_logs_table

   .. code-block:: json

      {
        "database": {
          "url": "postgresql://user:pass@localhost:5432/scrapy",
          "create_tables": true,
          "pool_size": 20
        },
        "job": {
          "id": "json_config_job",
          "batch_size": 500
        }
      }

   **Methods:**

   .. method:: load_yaml(file_path)

      Load configuration from YAML file.

      :param file_path: Path to YAML file
      :type file_path: str or Path
      :returns: Configuration dictionary
      :rtype: dict
      :raises: FileNotFoundError, yaml.YAMLError

   .. method:: load_json(file_path)

      Load configuration from JSON file.

      :param file_path: Path to JSON file
      :type file_path: str or Path
      :returns: Configuration dictionary
      :rtype: dict
      :raises: FileNotFoundError, json.JSONDecodeError

Configuration Examples
---------------------

Basic Configuration
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings.py - Basic configuration
   from scrapy_item_ingest.config import Settings

   # Create settings instance
   config = Settings()
   config.DB_URL = 'postgresql://scrapy:password@localhost:5432/scrapy_data'
   config.CREATE_TABLES = True
   config.JOB_ID = 'basic_job_001'

   # Validate configuration
   errors = config.validate()
   if errors:
       raise ValueError(f"Configuration errors: {errors}")

   # Apply to Scrapy settings
   DB_URL = config.DB_URL
   CREATE_TABLES = config.CREATE_TABLES
   JOB_ID = config.JOB_ID

Environment-Based Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings.py - Environment-based configuration
   import os
   from scrapy_item_ingest.config import EnvironmentConfigLoader

   # Load from environment
   env_loader = EnvironmentConfigLoader()
   env_config = env_loader.load()

   # Apply environment configuration
   DB_URL = env_config.get('db_url', 'postgresql://localhost:5432/scrapy')
   CREATE_TABLES = env_config.get('create_tables', True)
   JOB_ID = env_config.get('job_id', f'job_{int(time.time())}')

   # Advanced settings from environment
   if 'db_pool_size' in env_config:
       DB_SETTINGS = {
           'pool_size': env_config['db_pool_size'],
           'max_overflow': env_config.get('db_max_overflow', 30),
       }

Multi-Environment Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings.py - Multi-environment setup
   import os
   from scrapy_item_ingest.config import Settings, FileConfigLoader

   class ConfigurationManager:
       def __init__(self):
           self.environment = os.getenv('SCRAPY_ENV', 'development')
           self.base_config = self._load_base_config()
           self.env_config = self._load_environment_config()

       def _load_base_config(self):
           loader = FileConfigLoader()
           return loader.load_yaml('config/base.yaml')

       def _load_environment_config(self):
           loader = FileConfigLoader()
           config_file = f'config/{self.environment}.yaml'
           if os.path.exists(config_file):
               return loader.load_yaml(config_file)
           return {}

       def get_merged_config(self):
           # Merge base and environment configs
           config = {**self.base_config, **self.env_config}

           # Override with environment variables
           env_loader = EnvironmentConfigLoader()
           env_overrides = env_loader.load()
           config.update(env_overrides)

           return config

   # Initialize configuration
   config_manager = ConfigurationManager()
   merged_config = config_manager.get_merged_config()

   # Apply to Scrapy settings
   DB_URL = merged_config['database']['url']
   CREATE_TABLES = merged_config['database']['create_tables']
   JOB_ID = merged_config['job']['id']

Dynamic Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings.py - Dynamic configuration
   from datetime import datetime
   import socket

   class DynamicConfiguration:
       @staticmethod
       def generate_job_id(spider_name, environment='dev'):
           timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
           hostname = socket.gethostname()
           return f'{environment}_{spider_name}_{hostname}_{timestamp}'

       @staticmethod
       def get_database_url(environment='development'):
           db_configs = {
               'development': 'postgresql://dev:dev@localhost:5432/scrapy_dev',
               'staging': os.getenv('STAGING_DB_URL'),
               'production': os.getenv('PRODUCTION_DB_URL'),
           }
           return db_configs.get(environment)

       @staticmethod
       def get_performance_settings(environment='development'):
           settings_map = {
               'development': {
                   'concurrent_requests': 8,
                   'download_delay': 1,
                   'batch_size': 100,
               },
               'staging': {
                   'concurrent_requests': 16,
                   'download_delay': 0.5,
                   'batch_size': 500,
               },
               'production': {
                   'concurrent_requests': 32,
                   'download_delay': 0.1,
                   'batch_size': 1000,
               }
           }
           return settings_map.get(environment, settings_map['development'])

   # Apply dynamic configuration
   env = os.getenv('SCRAPY_ENV', 'development')
   dynamic_config = DynamicConfiguration()

   DB_URL = dynamic_config.get_database_url(env)
   JOB_ID = dynamic_config.generate_job_id('products', env)

   perf_settings = dynamic_config.get_performance_settings(env)
   CONCURRENT_REQUESTS = perf_settings['concurrent_requests']
   DOWNLOAD_DELAY = perf_settings['download_delay']

Configuration Testing
--------------------

Unit Testing Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import unittest
   from scrapy_item_ingest.config import Settings, validate_settings

   class TestConfiguration(unittest.TestCase):
       def test_valid_configuration(self):
           settings = Settings()
           settings.DB_URL = 'postgresql://test:test@localhost:5432/test_db'
           settings.CREATE_TABLES = True
           settings.JOB_ID = 'test_job'

           errors = settings.validate()
           self.assertEqual(len(errors), 0)

       def test_invalid_database_url(self):
           settings = Settings()
           settings.DB_URL = 'invalid://url'

           errors = settings.validate()
           self.assertGreater(len(errors), 0)
           self.assertTrue(any('database' in error.lower() for error in errors))

       def test_missing_required_settings(self):
           settings = Settings()
           # Don't set DB_URL

           errors = settings.validate()
           self.assertGreater(len(errors), 0)
           self.assertTrue(any('DB_URL' in error for error in errors))

Integration Testing
~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_configuration_integration():
       # Test with actual Scrapy settings
       from scrapy.settings import Settings as ScrapySettings

       scrapy_settings = ScrapySettings()
       scrapy_settings.set('DB_URL', 'postgresql://test:test@localhost:5432/test')
       scrapy_settings.set('CREATE_TABLES', True)

       # Validate with our validator
       errors = validate_settings(scrapy_settings)
       assert len(errors) == 0, f"Configuration errors: {errors}"

See Also
--------

* :doc:`../configuration` - Configuration user guide
* :doc:`../examples/advanced-configurations` - Advanced configuration examples
* :doc:`pipelines` - Pipeline API reference
