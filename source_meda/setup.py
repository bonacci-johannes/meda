from setuptools import find_packages, setup

"""
Script to build python package. 
Use "python setup.py bdist_wheel" to create the meda package.
"""

#  BUILD THE ADPKD LIBRARY PACKAGE #

requirements = [
    "sqlalchemy==1.4.40",
    "testing.postgresql==1.3.0",
    "numpy==1.23.2",
    "psycopg2-binary==2.9.1",
]

setup(
    name="meda",
    description='A tool to transform flat csv data into a structured database',
    python_requires='>=3.8.*',
    packages=find_packages(include=('meda*',)),
    package_data={'meda': ['utils/unit_conversion/*.yaml']},
    setup_requires=['setuptools_scm'],
    version='0.0.0',
    install_requires=requirements
)
