#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import os

NOT_PROVIDED = object()


def env(key, default=NOT_PROVIDED, coerce=str):
    """utility for getting settings from environment variables"""
    if default is NOT_PROVIDED:
        val = os.environ.get(key)
        if val is None:
            raise ValueError("Environment variable %s is required." % key)
    else:
        val = os.environ.get(key, default)
    return coerce(val) if val is not None else val


class Environment(object):
    """
    Alternative class-based environment config implementation

    Allows you to define information about the environment under which a
    program should be running using a dictionary. The benefit of doing
    this instead of using the function is that you can define all of the things
    that you expect from the environment up front so that it is easier for
    someone looking at the code to understand what variables your code needs.
    """
    NOT_PROVIDED = object()

    def __init__(self, varconf, coerce=str):
        self._varconf = varconf
        self._coerce = coerce

    def __call__(self, getvar):
        try:
            varinfo = self._varconf[getvar]
        except AttributeError:
            varinfo = {}
        coerce = varinfo.get('coerce', self._coerce)
        default = varinfo.get('default', self.NOT_PROVIDED)
        if default is self.NOT_PROVIDED:
            value = os.environ.get(getvar)
            if value is None:
                errmsg = "Environment variable '{0}' is required!"
                raise ValueError(errmsg.format(getvar))
        else:
            value = os.environ.get(getvar, default)
        return coerce(value) if value is not None else value
