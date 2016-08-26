#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import io
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


PROJECT_MODULE = 'armory'
PROJECT = 'armory'
AUTHOR = 'Bryce Eggleton'
EMAIL = 'eggleton.bryce@gmail.com'
DESC = 'Python utilities and tools'
LONG_DESC = ''
URL = "https://github.com/neuroticnerd/armory"
REQUIRES = []
SCRIPTS = {
    "console_scripts": [
        'phone = armory.phone.cli:CLI',
    ]}
LICENSE = 'BSD'
VERSION = ''

version_file = os.path.join(here, '{0}/__version__.py'.format(PROJECT_MODULE))
ver_find = r'^\s*__version__\s*=\s*[\"\'](.*)[\"\']$'
with io.open(version_file, 'r', encoding='utf-8') as ver_file:
    VERSION = re.search(ver_find, ver_file.read(), re.MULTILINE).group(1)

readme_file = os.path.join(here, 'README.rst')
with io.open(readme_file, 'r', encoding='utf-8') as f:
    LONG_DESC = f.read()

if __name__ == '__main__':
    setup(
        name=PROJECT,
        version=VERSION,
        packages=find_packages(include=[PROJECT_MODULE + '*']),
        author=AUTHOR,
        author_email=EMAIL,
        url=URL,
        description=DESC,
        long_description=LONG_DESC,
        license=LICENSE,
        install_requires=REQUIRES,
        # entry_points = SCRIPTS,
    )
