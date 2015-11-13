#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from __future__ import division, print_function


def items(dict_obj):
    try:
        return dict_obj.iteritems()
    except AttributeError:
        return dict_obj.items()
