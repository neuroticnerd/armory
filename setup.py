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

initfile = '{0}/__init__.py'.format(PROJECT_MODULE)
with open(initfile, 'r', encoding='utf-8') as modinit:
    findver = re.compile(r'^\s*__version__\s*=\s*[\"\'](.*)[\"\']', re.M)
    try:
        VERSION = findver.search(modinit.read()).group(1)
    except AttributeError:
        VERSION = '0.1.0'

with open('LICENSE', 'r', encoding='utf-8') as f:
    LICENSE = r.read()

setup(
    name = PROJECT,
    version = VERSION,
    packages = find_packages(include=[PROJECT_MODULE]),
    author = AUTHOR,
    author_email = EMAIL,
    url = URL,
    description = DESC,
    long_description = LONG_DESC,
    license=LICENSE,
    install_requires=REQUIRES,
    )
