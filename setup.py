#!/usr/bin/env python
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name='target-jsonl',
    version='0.1.2',
    description='Singer.io target for writing JSON Line files into S3',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Forked from Andy Huynh',
    author_email="bogdan.cojocar@gmail.com",
    url="https://github.com/BogdanCojocar/target-jsonl",
    keywords=["singer", "singer.io", "target", "etl"],
    classifiers=['Programming Language :: Python :: 3 :: Only'],
    py_modules=['target_jsonl'],
    install_requires=['jsonschema==2.6.0', 'singer-python==2.1.4', 'boto3'],
    entry_points='''
          [console_scripts]
          target-jsonl=target_jsonl:main
      ''',
)
