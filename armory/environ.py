# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

from .boolean import boolean

_NOT_PROVIDED = object()
_ENV_ERROR_MSG = 'Environment variable "{0}" or a default value is required'


def env(key, default=_NOT_PROVIDED, cast=str, force=False, **kwargs):
    """
    Retrieve environment variables and specify default and options.

    :param key: (required) environment variable name to retrieve
    :param default: value to use if the environment var doesn't exist
    :param cast: values always come in as strings, cast to this type if needed
    :param force: force casting of value even when it may not be needed
    :param boolmap: if True use default map, otherwise you can pass custom map
    :param sticky: injects default into environment so child processes inherit

    NOTE: None can be passed as the default to avoid raising a KeyError
    """
    boolmap = kwargs.get('boolmap', None)
    sticky = kwargs.get('sticky', False)

    value = os.environ.get(key, default)
    if value is _NOT_PROVIDED:
        raise KeyError(_ENV_ERROR_MSG.format(key))

    if sticky and value == default:
        try:
            os.environ[key] = value
        except TypeError:
            os.environ[key] = str(value)

    if force or (value != default and type(value) != cast):
        if cast is bool and boolmap is not None:
            value = boolean(value, boolmap=boolmap)
        elif cast is bool:
            value = boolean(value)
        else:
            value = cast(value)

    return value
