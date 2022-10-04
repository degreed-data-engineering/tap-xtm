#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name="tap-datadog",
      version="1.0.0",
      description="Singer.io tap for extracting data from different 3rd party sources for Degreed ",
      author="Degreed",
      url="http://singer.io",
      classifiers=["Programming Language :: Python :: 3 :: Only"],
      py_modules=["tap_datadog"],
      install_requires=[
          "singer-python==5.12.1",
          "requests==2.20.0",
          "dateparser"
      ],
      extras_require={
          'dev': [
              'pylint',
              'nose',
              'ipdb'
          ]
      },
      entry_points="""
          [console_scripts]
          tap-datadog=tap_datadog:main
      """,
      packages=["tap_datadog"],
      package_data = {
          "schemas": ["tap_datadog/schemas/*.json"]
      },
      include_package_data=True,
)
