# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

from builtins import str

from .boolean import boolean

_NOT_PROVIDED = object()
_ENV_ERROR_MSG = 'Environment variable "{0}" or a default value is required'


def getenv(key, default=_NOT_PROVIDED, cast=str, force=False, boolmap=True, sticky=False):
    """
    Retrieve environment variables and specify default and options.

    :param key: (required) environment variable name to retrieve
    :type key: str
    :param default: value to use if the environment variable does not exist
    :type default: <any>
    :param cast: values always come in as strings, cast to this type if needed
    :type cast: type
    :param force: force casting of value even when it may not be needed
    :type force: bool
    :param boolmap: if True use default map, otherwise you can pass custom map
    :type boolmap: dict (or dict-like object)
    :param sticky: injects default into environment so child processes inherit
    :type sticky: bool
    :returns: environment var value or default if provided
    :rtype: dynamic; depends on provided default value and cast parameter
    :raises: KeyError, TypeError

    NOTE: None can be passed as the default to avoid raising a KeyError
    """
    value = os.environ.get(key, default)
    if value is _NOT_PROVIDED:
        raise KeyError(_ENV_ERROR_MSG.format(key))

    if sticky and value == default:
        # This can raise TypeError when inserting value into environment
        env_val = value if isinstance(value, str) else '{0}'.format(value)
        os.environ[key] = env_val

    if force or (value != default and type(value) != cast):
        if cast is bool and boolmap is True:
            value = boolean(value)
        elif cast is bool and boolmap:
            value = boolean(value, boolmap=boolmap)
        else:
            value = cast(value)

    return value
