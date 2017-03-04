# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from builtins import str

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


def boolean(value, boolmap=_BOOL_MAP):
    """
    Convert value to <type bool>.

    Uses the boolean mapping dict to attempt to determine the conversion
    of the given value. If the value is not found in the mapping, it falls
    back to the built-in Python bool conversion. Optionally, a custom
    mapping dict can be passed to use for the value lookups.

    The default mapping dict allows quick and easy conversion of some
    common string values that have logical meaning as being true or false.

    This alternative allows one to consider a separate mapping when
    converting values to a boolean that are not what Python would
    inherently consider the value as. This is particularly useful for
    environment variables which are almost always retrieved as strings
    instead of whatever their inherent data type actually is.

    Because of how Python treats strings, this means that an environment
    variable which has been given the value of ``"False"`` ends up
    evaluating to ``True`` even though that was probably not the intention.
    """
    if boolmap == _BOOL_MAP and isinstance(value, str):
        result = boolmap.get(value.lower())
    else:
        result = boolmap.get(value)

    if result is None:
        result = bool(value)
    return result
