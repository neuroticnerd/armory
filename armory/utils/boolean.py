#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from __future__ import division, print_function

TRUTHS = ['yes', 'y', 'true', 't', '1']
FALSEHOODS = ['no', 'n', 'false', 'f', '0']


def boolean(value):
    """
    This function returns a boolean result based on the given value

    Unlike the 'bool' python builtin, this supports string values as well,
    which semantically indicate a value of truth or falehoods; these are
    'yes', 'y', 'true', 't', '1', 'no', 'n', 'false', 'f', '0'. If you do
    not need string support, then use the python builtin as usual.
    """
    try:
        val = str(value).lower()
        if val in TRUTHS:
            return True
        if val in FALSEHOODS:
            return False
    except (UnicodeDecodeError, TypeError):
        pass
    return bool(value)
