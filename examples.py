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
        'SOME_RANDOM_THING': {'default': 3, 'coerce': int},
        'STRING_TO_INT': {'default': '6256', 'coerce': int},
    })

    # print the values of a couple env vars
    print(env('HOME'))
    print(env('SOME_RANDOM_THING'))

    # if an environment variable is not set, it will raise an exception
    try:
        print(env('ANSIBLE_ROLES_PATH'))
    except Exception as e:
        print(e)

    # environment variables are treated as strings by default
    print(env('STRING_TO_INT'))
    print(type(env('STRING_TO_INT')))
