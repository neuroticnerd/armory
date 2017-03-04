# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import re


class UnicodeTransformChar(object):
    def __init__(self, char_regex, replacement):
        """Initializes with the regex and replacement substitution

        !important: regex encoding must match the replacement and ``text``
        parameter encoding when calling the :func:`transform` method!
        """
        self.regex = re.compile(char_regex)
        self.repl = replacement

    def transform(self, text):
        """Replaces characters in string ``text`` based in regex sub"""
        return re.sub(self.regex, self.repl, text)
