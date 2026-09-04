from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

BASE_DIR = Path(__file__).parent
try:
    long_description = (BASE_DIR / "README.md").read_text(encoding="utf-8")
except FileNotFoundError:
    long_description = (
        "A comprehensive Scrapy extension for ingesting scraped items, "
        "requests, logs, and stats into PostgreSQL databases."
    )

PTH = "import scrapy_ingest.extensions.log_handler\n"


def _pth(dirpath):
    if dirpath:
        try:
            Path(dirpath).joinpath("scrapy_ingest_early.pth").write_text(
                PTH, encoding="utf-8"
            )
        except Exception:
            pass


class DevelopCommand(develop):
    def run(self):
        develop.run(self)
        _pth(getattr(self, "install_dir", None) or self.install_lib)


class InstallCommand(install):
    def run(self):
        install.run(self)
        _pth(self.install_lib)


setup(
    name="scrapy-ingest",
    version="1.2.0",
    description="Scrapy extension for database ingestion with job/spider tracking",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Fawad Ali",
    author_email="fawadstar6@gmail.com",
    url="https://github.com/fawadss1/scrapy_item_ingest",
    project_urls={
        "Documentation": "https://scrapy-ingest.readthedocs.io/",
        "Source": "https://github.com/fawadss1/scrapy_item_ingest",
        "Tracker": "https://github.com/fawadss1/scrapy_item_ingest/issues",
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
    cmdclass={"develop": DevelopCommand, "install": InstallCommand},
    entry_points={
        "scrapy.pipelines": [
            "db_ingest = scrapy_ingest.pipelines.main:DbInsertPipeline"
        ],
        "scrapy.extensions": [
            "logging_ext = scrapy_ingest.extensions.logging:LoggingExtension",
            "stats_ext = scrapy_ingest.extensions.stats:StatsExtension",
        ],
    },
    python_requires=">=3.10",
    include_package_data=True,
    zip_safe=False,
)
