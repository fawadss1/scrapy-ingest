Contributing
============

Thank you for your interest in contributing to Scrapy Ingest! This guide will help you get started with contributing to the project.

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~

1. **Fork and clone the repository:**

   .. code-block:: bash

      git clone https://github.com/fawadss1/scrapy_item_ingest.git
      cd scrapy_ingest

2. **Create a virtual environment:**

   .. code-block:: bash

      python -m venv venv
      # On Windows:
      venv\Scripts\activate
      # On macOS/Linux:
      source venv/bin/activate

3. **Install development dependencies:**

   .. code-block:: bash

      pip install -e .
      pip install -r requirements-dev.txt

4. **Set up pre-commit hooks:**

   .. code-block:: bash

      pre-commit install

5. **Set up test database:**

   .. code-block:: bash

      # Create test database
      createdb scrapy_test

      # Run initial tests
      pytest tests/

Development Environment
~~~~~~~~~~~~~~~~~~~~~~

**Required Tools:**

* Python 3.10+
* PostgreSQL 12+
* Git
* Code editor (VS Code, PyCharm, etc.)

**Recommended Tools:**

* Docker (for testing different environments)
* Redis (for advanced features testing)
* pgAdmin or similar (for database inspection)

**Environment Variables:**

.. code-block:: bash

   # .env.development
   TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/scrapy_test
   DEBUG=true
   LOG_LEVEL=DEBUG

Project Structure
----------------

Understanding the Codebase
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   scrapy_ingest/
   ├── __init__.py              # Package initialization and exports
   ├── config/                  # Configuration management
   │   ├── __init__.py
   │   └── settings.py         # Settings validation and defaults
   ├── database/               # Database operations
   │   ├── __init__.py
   │   ├── connection.py       # Connection management
   │   └── schema.py          # Table creation and management
   ├── extensions/             # Scrapy extensions
   │   ├── __init__.py
   │   ├── base.py            # Base extension class
   │   └── logging.py         # Logging extension
   ├── pipelines/              # Scrapy pipelines
   │   ├── __init__.py
   │   ├── base.py            # Base pipeline class
   │   ├── items.py           # Items pipeline
   │   ├── main.py            # Combined pipeline
   │   └── requests.py        # Requests pipeline
   └── utils/                  # Utility functions
       ├── __init__.py
       ├── fingerprint.py      # Request fingerprinting
       └── serialization.py    # Data serialization

**Key Components:**

* **Pipelines**: Core functionality for processing items and requests
* **Extensions**: Additional features like logging and monitoring
* **Database**: Connection management and schema operations
* **Config**: Settings validation and configuration management
* **Utils**: Helper functions and utilities

Code Style and Standards
-----------------------

Coding Standards
~~~~~~~~~~~~~~~

We follow PEP 8 with some additional guidelines:

* **Line length**: Maximum 88 characters (Black formatter)
* **Imports**: Use absolute imports, group by standard/third-party/local
* **Docstrings**: Use Google-style docstrings
* **Type hints**: Use type hints where appropriate
* **Variable names**: Use descriptive names, avoid abbreviations

**Example Code Style:**

.. code-block:: python

   from typing import Dict, List, Optional
   import logging
   from scrapy import Spider
   from scrapy.item import Item

   logger = logging.getLogger(__name__)


   class ItemsPipeline:
       """Pipeline for storing scraped items in database.

       This pipeline handles the storage of scraped items into PostgreSQL
       database with automatic serialization and error handling.

       Args:
           settings: Scrapy settings object containing configuration

       Attributes:
           db_url: Database connection string
           job_id: Unique identifier for the crawl job
       """

       def __init__(self, settings: Dict[str, Any]) -> None:
           self.db_url: str = settings.get('DB_URL')
           self.job_id: Optional[str] = settings.get('JOB_ID')
           self._connection: Optional[Connection] = None

       def process_item(self, item: Item, spider: Spider) -> Item:
           """Process and store item in database.

           Args:
               item: The scraped item to process
               spider: The spider that scraped the item

           Returns:
               The processed item

           Raises:
               DatabaseError: If database operation fails
           """
           try:
               serialized_item = self._serialize_item(item)
               self._store_item(serialized_item, spider)
               return item
           except Exception as e:
               logger.error(f"Failed to process item: {e}")
               raise

Documentation Standards
~~~~~~~~~~~~~~~~~~~~~~

* **Code Comments**: Explain why, not what
* **Docstrings**: Document all public functions, classes, and methods
* **Type Hints**: Use type hints for function signatures
* **Examples**: Include usage examples in docstrings

**Docstring Example:**

.. code-block:: python

   def serialize_item(item: Union[Item, Dict]) -> Dict[str, Any]:
       """Serialize Scrapy item to JSON-compatible format.

       Converts Scrapy Item objects and dictionaries to a format that can
       be safely serialized to JSON. Handles datetime objects, Decimal
       numbers, and other non-JSON-serializable types.

       Args:
           item: The item to serialize. Can be a Scrapy Item or dictionary.

       Returns:
           A dictionary with all values converted to JSON-serializable types.

       Raises:
           SerializationError: If the item contains objects that cannot be
               serialized or converted to a compatible format.

       Example:
           >>> from datetime import datetime
           >>> item = {'name': 'Product', 'created': datetime.now()}
           >>> serialized = serialize_item(item)
           >>> isinstance(serialized['created'], str)
           True
       """

Testing Guidelines
-----------------

Test Structure
~~~~~~~~~~~~~

We use pytest for testing with the following structure:

.. code-block:: text

   tests/
   ├── conftest.py              # Pytest configuration and fixtures
   ├── unit/                    # Unit tests
   │   ├── test_pipelines.py
   │   ├── test_extensions.py
   │   ├── test_serialization.py
   │   └── test_config.py
   ├── integration/             # Integration tests
   │   ├── test_database.py
   │   └── test_scrapy_integration.py
   └── fixtures/                # Test data and fixtures
       ├── sample_items.json
       └── test_responses.html

Writing Tests
~~~~~~~~~~~~

**Unit Test Example:**

.. code-block:: python

   import pytest
   from unittest.mock import Mock, patch
   from scrapy_ingest.pipelines.items import ItemsPipeline


   class TestItemsPipeline:
       @pytest.fixture
       def pipeline(self, mock_settings):
           return ItemsPipeline(mock_settings)

       @pytest.fixture
       def mock_settings(self):
           return {
               'DB_URL': 'postgresql://test:test@localhost:5432/test_db',
               'CREATE_TABLES': True,
               'JOB_ID': 'test_job'
           }

       @pytest.fixture
       def sample_item(self):
           return {
               'title': 'Test Product',
               'price': 29.99,
               'url': 'https://example.com/product/123'
           }

       def test_process_item_success(self, pipeline, sample_item):
           spider = Mock()
           spider.name = 'test_spider'

           with patch.object(pipeline, '_store_item') as mock_store:
               result = pipeline.process_item(sample_item, spider)

               assert result == sample_item
               mock_store.assert_called_once()

       def test_process_item_database_error(self, pipeline, sample_item):
           spider = Mock()

           with patch.object(pipeline, '_store_item', side_effect=Exception("DB Error")):
               with pytest.raises(Exception):
                   pipeline.process_item(sample_item, spider)

**Integration Test Example:**

.. code-block:: python

   import pytest
   import psycopg2
   from scrapy_ingest.pipelines.main import DbInsertPipeline


   @pytest.mark.integration
   class TestDatabaseIntegration:
       @pytest.fixture(scope='class')
       def test_database(self):
           # Setup test database
           db_url = 'postgresql://test:test@localhost:5432/test_scrapy'
           conn = psycopg2.connect(db_url)

           yield db_url

           # Cleanup
           conn.close()

       def test_end_to_end_pipeline(self, test_database):
           settings = {
               'DB_URL': test_database,
               'CREATE_TABLES': True,
               'JOB_ID': 'integration_test'
           }

           pipeline = DbInsertPipeline(settings)
           spider = Mock()
           spider.name = 'test_spider'

           # Test pipeline functionality
           pipeline.open_spider(spider)

           item = {'title': 'Test Item', 'url': 'https://example.com'}
           result = pipeline.process_item(item, spider)

           assert result == item

           pipeline.close_spider(spider)

Running Tests
~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest

   # Run specific test file
   pytest tests/unit/test_pipelines.py

   # Run with coverage
   pytest --cov=scrapy_ingest --cov-report=html

   # Run only integration tests
   pytest -m integration

   # Run tests in parallel
   pytest -n auto

Test Coverage
~~~~~~~~~~~~

We aim for 90%+ test coverage. Check coverage with:

.. code-block:: bash

   pytest --cov=scrapy_ingest --cov-report=term-missing

Contribution Workflow
--------------------

Making Changes
~~~~~~~~~~~~~

1. **Create a feature branch:**

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make your changes:**
   - Write code following our style guidelines
   - Add or update tests
   - Update documentation if needed

3. **Run tests and linting:**

   .. code-block:: bash

      # Run tests
      pytest

      # Run linting
      flake8 scrapy_ingest/
      black --check scrapy_ingest/
      mypy scrapy_ingest/

4. **Commit your changes:**

   .. code-block:: bash

      git add .
      git commit -m "feat: add new feature description"

5. **Push and create pull request:**

   .. code-block:: bash

      git push origin feature/your-feature-name

Commit Message Format
~~~~~~~~~~~~~~~~~~~

We use conventional commits format:

.. code-block:: text

   type(scope): description

   [optional body]

   [optional footer]

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

.. code-block:: text

   feat(pipelines): add batch processing support
   fix(database): handle connection timeout errors
   docs(api): update pipeline documentation
   test(integration): add database integration tests

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~

**Before submitting:**

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for significant changes)
- [ ] Commit messages follow conventional format

**Pull Request Template:**

.. code-block:: markdown

   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests pass

Release Process
--------------

Versioning
~~~~~~~~~

We use Semantic Versioning (SemVer):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Release Checklist
~~~~~~~~~~~~~~~~

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create release tag
4. Build and publish to PyPI
5. Update documentation

.. code-block:: bash

   # Create release
   git tag v1.2.0
   git push origin v1.2.0

   # Build package
   python setup.py sdist bdist_wheel

   # Upload to PyPI
   twine upload dist/*

Getting Help
-----------

**Development Questions:**
- GitHub Discussions
- Open an issue with `question` label

**Bug Reports:**
- Use GitHub Issues
- Include minimal reproduction case
- Provide environment details

**Feature Requests:**
- Open GitHub Issue with `enhancement` label
- Describe use case and expected behavior

Code of Conduct
---------------

We are committed to providing a welcoming and inclusive environment for all contributors. Please read and follow our Code of Conduct.

**Our Standards:**

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

**Unacceptable Behavior:**

- Harassment or discrimination
- Personal attacks or trolling
- Publishing private information
- Inappropriate sexual content

**Reporting:**

Report unacceptable behavior to the maintainers at admin@yourproject.com.

Recognition
----------

Contributors are recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- Project documentation

Thank you for contributing to Scrapy Ingest! 🎉
