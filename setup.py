#!/usr/bin/env python
# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""Setup script for greplin-twisted-utils."""

try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup

setup(name='greplin-twisted-utils',
      version='0.1',
      description='Utilities for Twisted',
      license='Apache',
      author='Greplin, Inc.',
      author_email='opensource@greplin.com',
      url='http://www.github.com/Greplin/greplin-twisted-utilities',
      package_dir = {'':'src'},
      packages = [
        'greplin',
        'greplin.defer',
        'greplin.net',
        'greplin.testing',
      ],
      namespace_packages = [
        'greplin',
        'greplin.defer',
        'greplin.net',
        'greplin.testing',
      ],
      test_suite = 'nose.collector',
      zip_safe = True
)