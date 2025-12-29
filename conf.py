# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'gredos2x'
copyright = '2023, Gregor' # Adjust the year and author as needed
author = 'Gregor' # Your name or organization
release = '0.1.0' # Your project's version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',  # Automatically document Python code
    'sphinx.ext.napoleon', # Support for Google and NumPy style docstrings
    'sphinx.ext.viewcode', # Add links to highlighted source code
    'sphinx.ext.todo',     # Support for todo notes
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster' # Or 'sphinx_rtd_theme', 'furo', etc.
html_static_path = ['_static']

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html

todo_include_todos = True

# -- Autodoc configuration ---------------------------------------------------
# Add your project's root directory to the Python path for autodoc to find modules
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
