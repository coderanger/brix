#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name = 'balanced-infra',
    version = '1.0-dev',
    packages = find_packages(),
    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Balanced infrastructure stuff.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    license = 'Apache 2.0',
    url = 'https://github.com/balanaced/balanced-infra',
    classifiers = [
        #'Development Status :: 1 - Planning',
        #'Development Status :: 2 - Pre-Alpha',
        #'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    zip_safe = False,
    install_requires = ['stratosphere', 'boto'],
    tests_require = ['pytest', 'pretend', 'flake8'],
    cmdclass = {'test': PyTest},
    entry_points = {
        'console_scripts': [
            'balanced-stacks = stacks:main',
        ],
    }
)
