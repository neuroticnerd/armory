"""
https://github.com/erikrose/more-itertools
"""
from __future__ import absolute_import, unicode_literals

import itertools
import random


def iterchunks(iterable_obj, chunk_size, chunk_type=tuple):
    source_iter = iter(iterable_obj)
    chunk = chunk_type(itertools.islice(source_iter, chunk_size))
    while chunk:
        yield chunk
        chunk = chunk_type(itertools.islice(source_iter, chunk_size))


def rand_iterchunks(iterable_obj, chunk_min, chunk_max, chunk_type=tuple):
    source_iter = iter(iterable_obj)
    chunk = chunk_type(itertools.islice(source_iter, random.randint(chunk_min, chunk_max)))
    while chunk:
        yield chunk
        chunk = chunk_type(itertools.islice(source_iter, random.randint(chunk_min, chunk_max)))
