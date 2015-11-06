#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from __future__ import division, print_function

from armory.environ import Environment


if __name__ == "__main__":
    env = Environment({
        'HOME': {},
        'PYTHONPATH': {'default': None},
        'PYTHONUNBUFFERED': {},
        'ANSIBLE_ROLES_PATH': {},
        'SOME_RANDOM_THING': {'default': 3, 'coerce': int}
    })

    # print the values of a couple env vars
    print(env('HOME'))
    print(env('SOME_RANDOM_THING'))

    # if an environment variable is not set, it will raise an exception
    try:
        print(env('ANSIBLE_ROLES_PATH'))
    except Exception as e:
        print(e)

    # ## what if you want to select a default value based on a previous value?
    MODE = 'prod'
    env = Environment({
        'SOME_UNSET_VAR': {
            'default': {
                'dev': 'this is a dev var',
                'prod': 'this is a prod var',
            },
        },
    }, default_key=MODE)

    print(env('SOME_UNSET_VAR'))

    # what if MODE had been set to dev?
