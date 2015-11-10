#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from __future__ import division, print_function

import re

from setuptools import setup, find_packages
from io import open

PROJECT_MODULE = 'armory'
PROJECT = 'armory'
AUTHOR = 'Bryce Eggleton'
EMAIL = 'eggleton.bryce@gmail.com'
DESC = 'Python utilities and tools'
URL = "https://github.com/neuroticnerd/armory"
REQUIRES = []
LONG_DESC = ''
LICENSE = ''
VERSION = ''

version_file = '{0}/__version__.py'.format(PROJECT_MODULE)
with open(version_file, 'r', encoding='utf-8') as fver:
    re_ver = r'^\s*__version__\s*=\s*[\"\'](.*)[\"\']$'
    VERSION = re.search(re_ver, fver.read(), re.MULTILINE).group(1)

with open('LICENSE', 'r', encoding='utf-8') as f:
    LICENSE = f.read()

setup(
    name=PROJECT,
    version=VERSION,
    packages=find_packages(include=[PROJECT_MODULE]),
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    description=DESC,
    long_description=LONG_DESC,
    license=LICENSE,
    install_requires=REQUIRES,
)
