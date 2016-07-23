#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from __future__ import division, print_function

from .boolean import boolean
from .builtins import items
from .encoding import UnicodeTransformChar

__all__ = (
    'boolean',
    'items',
    'UnicodeTransformChar',
)


def pretty_print_req(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.
    """
    return ('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join(
            '{}: {}'.format(k, v) for k, v in req.headers.items()
        ),
        req.body,
    ))
