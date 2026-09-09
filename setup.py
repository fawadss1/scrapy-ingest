from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).parent
try:
    long_description = (BASE_DIR / "README.md").read_text(encoding="utf-8")
except FileNotFoundError:
    long_description = (
        "A comprehensive Scrapy extension for ingesting scraped items, "
        "requests, logs, and stats into PostgreSQL databases."
    )

setup(
    name="scrapy-ingest",
    version="1.3.0",
    description="Scrapy extension for database ingestion with job/spider tracking",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Fawad Ali",
    author_email="fawadstar6@gmail.com",
    url="https://github.com/fawadss1/scrapy-ingest",
    project_urls={
        "Documentation": "https://scrapy-ingest.readthedocs.io/",
        "Source": "https://github.com/fawadss1/scrapy-ingest",
        "Tracker": "https://github.com/fawadss1/scrapy-ingest/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Framework :: Scrapy",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Database",
    ],
    keywords="scrapy, database, postgresql, mysql, web-scraping, data-pipeline",
    install_requires=[
        "scrapy>=2.18.0",
        "psycopg2-binary>=2.9.12",
        "itemadapter>=0.13.1",
        "pytz>=2026.3",
        "w3lib>=2.4.1",
        "PyMySQL>=1.2.0",
        "opensearch-py>=3.2.0",
    ],
    extras_require={
        "docs": [
            "sphinx>=5.0.0",
            "sphinx_rtd_theme>=1.2.0",
            "myst-parser>=0.18.0",
            "sphinx-autodoc-typehints>=1.19.0",
            "sphinx-copybutton>=0.5.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scrapy-ingest=scrapy_ingest.cli:main",
        ],
        "scrapy.pipelines": [
            "db_ingest = scrapy_ingest.pipelines.main:DbInsertPipeline"
        ],
        "scrapy.extensions": [
            "logging_ext = scrapy_ingest.extensions.logging:LoggingExtension",
            "stats_ext = scrapy_ingest.extensions.stats:StatsExtension",
        ],
    },
    python_requires=">=3.10",
    zip_safe=False,
)
