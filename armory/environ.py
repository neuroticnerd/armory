#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import os

from collections import OrderedDict
from armory.utils import items


_BOOL_MAP = {
    'y': True,
    'yes': True,
    't': True,
    'true': True,
    '1': True,
    'n': False,
    'no': False,
    'f': False,
    'false': False,
    '0': False,
}
_NOT_PROVIDED = object()
_ENV_ERROR_MSG = 'Environment variable "{0}" or a default value is required'


def boolean(value, boolmap=_BOOL_MAP):
    """ Convert string value to <type bool>. """
    return boolmap.get(value.lower(), bool(value))


def env(key, default=_NOT_PROVIDED, cast=str,
        force=False, boolmap=False, sticky=False):
    """
    Retrieve environment variables and specify default and options.

    :param key: (required) environment variable name to retrieve
    :param default: value to use if the environment var doesn't exist
    :param cast: values always come in as strings, cast to this type if needed
    :param force: force casting of value even when it may not be needed
    :param boolmap: if True use default map, otherwise you can pass custom map
    :param sticky: injects default into environment so child processes inherit

    NOTE: None can be passed as the default to avoid raising a ValueError
    """
    if boolmap is True:
        boolmap = _BOOL_MAP

    value = os.environ.get(key, default)
    if value is _NOT_PROVIDED:
        raise ValueError(_ENV_ERROR_MSG.format(key))

    if sticky and value == default:
        try:
            os.environ[key] = value
        except TypeError:
            os.environ[key] = str(value)

    if force or (value != default and type(value) != cast):
        if cast is bool and boolmap:
            value = boolean(value, boolmap=boolmap)
        else:
            value = cast(value)

    return value


'''


def env(key, default=NOT_PROVIDED, cast=str, force=False):
    """utility for getting settings from environment variables"""
    if default is NOT_PROVIDED:
        val = os.environ.get(key)
        if val is None:
            errmsg = "Environment variable {0} is required."
            raise ValueError(errmsg.format(key))
    else:
        val = os.environ.get(key, default)
    if val is not None:
        if val == default and not force:
            return val
        else:
            return cast(val)
    return val
'''
NOT_PROVIDED = object()
NONEOBJ = object()


class VarInfo(object):
    def __init__(self, default, cast, lazy, force):
        self.default = default
        self.cast = cast
        self.lazy = lazy
        self.force = force

    def json_dict(self):
        jd = OrderedDict()
        jd['default'] = '{0}'.format(self.default)
        jd['cast'] = '{0}'.format(self.cast)
        jd['lazy'] = self.lazy
        jd['force'] = self.force
        return jd


class Var(object):
    def __init__(self, name, default=NOT_PROVIDED, cast=None, lazy=None):
        self.name = name
        self.default = default
        self.cast = cast
        self.lazy = lazy

    def _var_info(self):
        return VarInfo(self.default, self.cast, self.lazy)


'''
TODO:
*   make sure there is the option to only coerce values retrieved, but leave
    a provided default at whichever type it currently is
*   provide subclass options to specify env vars and validate that the env var
    actually conforms to a specification (glob/regex/url/path/choice)
'''


class Environment(object):
    """
    Alternative class-based environment config implementation

    Allows you to define information about the environment under which a
    program should be running using a dictionary. The benefit of doing
    this instead of using the function is that you can define all of the things
    that you expect from the environment up front so that it is easier for
    someone looking at the code to understand what variables your code needs.
    """

    def __init__(self, varconf, cast=str, force=False, lazy=True):
        self._varconf = varconf
        self._cast = cast
        self._force = force
        self._lazy = lazy
        self._variables = {}
        self._values = {}
        if isinstance(varconf, list):
            try:
                for conf in varconf:
                    self._variables[conf.name] = conf._var_info()
            except AttributeError:
                raise ValueError('ERROR: expected list of Var objects')
        else:
            for var, conf in items(varconf):
                self._variables[var] = VarInfo(
                    default=conf.get('default', NOT_PROVIDED),
                    cast=conf.get('cast', self._cast),
                    lazy=conf.get('lazy', self._lazy),
                    force=conf.get('force', self._force)
                )
        if lazy is False:
            self._resolve_all()

    def __call__(self, varname):
        return self._resolve(varname)

    def _resolve(self, varname):
        try:
            return self._values[varname]
        except KeyError:
            pass

        varinfo = self._variables.get(varname, NONEOBJ)
        if varinfo is NONEOBJ:
            raise ValueError('ERROR: unknown var "{0}"'.format(varname))

        if varinfo.default is NOT_PROVIDED:
            value = os.environ.get(varname)
            if value is None:
                errmsg = "Environment variable '{0}' is required!"
                raise ValueError(errmsg.format(varname))
        else:
            value = os.environ.get(varname, varinfo.default)

        if value is not None:
            if value != varinfo.default or varinfo.force:
                value = varinfo.cast(value)

        self._values[varname] = value
        return value

    def _resolve_all(self):
        for var in self._variables.keys():
            self._resolve(var)
