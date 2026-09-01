# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# Mock imports for modules that might not be available during doc build
autodoc_mock_imports = [
    'scrapy',
    'psycopg2',
    'SQLAlchemy',
    'itemadapter',
    'twisted',
]

project = 'Scrapy Ingest'
copyright = '2025, Fawad Ali'
author = 'Fawad Ali'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Source file parsers
source_suffix = {
    '.rst': None,
    '.md': 'myst_parser',
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Theme options
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,  # Enable external link styling
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#333333',  # Dark header background
    # Toc options
    'collapse_navigation': False,  # Keep navigation expanded
    'sticky_navigation': True,
    'navigation_depth': 4,  # Depth of navigation tree
    'includehidden': True,
    'titles_only': False,  # Show full titles in navigation
}

# Add custom CSS for dark theme
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',  # Custom CSS for dark theme
]

# Ensure _static directory exists
import os
os.makedirs('_static', exist_ok=True)

# Create custom.css file for dark theme
custom_css_path = os.path.join('_static', 'css')
os.makedirs(custom_css_path, exist_ok=True)
with open(os.path.join(custom_css_path, 'custom.css'), 'w') as f:
    f.write("""
    body {
        background-color: #121212;
        color: #ffffff;
    }
    a {
        color: #1e90ff;
    }
    """)

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Don't fail on import errors
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'scrapy': ('https://docs.scrapy.org/en/latest/', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/20/', None),
}

# MyST parser settings
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "html_admonition",
    "html_image",
    "colon_fence",
    "smartquotes",
    "replacements",
]

# Todo extension
todo_include_todos = True
