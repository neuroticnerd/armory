#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from __future__ import division, print_function

import simplejson as json

from collections import OrderedDict


def _complex_encode(obj):
    return '{0}'.format(obj)


def jsonify(data, pretty=False, **kwargs):
    """Serialize Python objects to JSON with optional 'pretty' formatting

    Raises:
        TypeError: from :mod:`json` lib
        ValueError: from :mod:`json` lib
        JSONDecodeError: from :mod:`json` lib
    """
    isod = isinstance(data, OrderedDict)
    params = {
        'for_json': True,
        'default': _complex_encode,
    }
    if pretty:
        params['indent'] = 2
        params['sort_keys'] = False if isod else True
    params.update(kwargs)
    try:
        return json.dumps(data, ensure_ascii=False, **params)
    except UnicodeDecodeError:
        return json.dumps(data, **params)


def jsonexpand(data, ordered=True):
    if ordered:
        return json.loads(data, object_pairs_hook=OrderedDict)
    return json.loads(data)
