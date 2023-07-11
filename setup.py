from setuptools import setup

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gredos2x',
    version='1.0.1',
    author='Gregor Skrt',
    author_email='gregor.skrt@gmail.com',
    description='gredos2x is a format converter for Gredos power system model built by EIMV in 1991. This tool is a set of Python tools, for export to other formats and simulators and supports GIS data conversion from Gredos.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/GSkrt/gredos2x',
    py_modules=['gredos2x'],
    install_requires = ['geopandas', 'fiona', 'sqlalchemy','pyodbc','sqlalchemy-access'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3.10', 
        'Programming Language :: Python :: 3.11'
        
    ],
)


