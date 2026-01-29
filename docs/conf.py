# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'gredos2x'
copyright = '2026, Gregor Skrt'
author = 'Gregor Skrt'
release = '2.0.3'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',  # Automatically document Python code
    'sphinx.ext.napoleon', # Support for Google and NumPy style docstrings
    'sphinx.ext.viewcode', # Add links to highlighted source code
    'sphinx.ext.todo',
    'sphinx.ext.githubpages',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'sl'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html

todo_include_todos = True

# -- Autodoc configuration ---------------------------------------------------
# Add your project's root directory to the Python path for autodoc to find modules
import os
import sys

sys.path.insert(0, os.path.abspath('../')) # Add the project root to the path (one level up from docs)
sys.path.insert(0, os.path.abspath('../gredos2x')) # Add gredos2x to the path (one level up, then into gredos2x)

