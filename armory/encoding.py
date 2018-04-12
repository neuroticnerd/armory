# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import logging
import re
import sys
import unicodedata

log = logging.getLogger(__name__)


def get_controlchars_re(sanity_check=False):
    """Returns regex for unicode control characters."""
    condensed = r'[\x00-\x1f\x7f-\x9f]'

    if sanity_check:
        cc_re = re.compile(condensed)
        all_chars = [chr(i) for i in range(sys.maxunicode)]
        control_chars = ''.join(
            c for c in all_chars if unicodedata.category(c) == 'Cc'
        )
        condensed_chars = ''.join(
            c for c in all_chars if cc_re.match(c)
        )
        if control_chars == condensed_chars:
            result = condensed
        else:  # pragma: no cover
            log.warning('control chars need updating!')
            result = r'{0}'.format(repr(control_chars))
    else:
        result = condensed

    return result


class UnicodeTransformChar(object):
    def __init__(self, char_regex, replacement):
        """Initialized with the regex pattern and replacement substitution.

        !important: regex encoding must match the replacement and ``text``
        parameter encoding when calling the :func:`transform` method!
        """
        self.regex = re.compile(char_regex)
        self.repl = replacement

    def transform(self, text, count=0):
        """Replaces characters in string ``text`` based in regex sub."""
        return re.sub(self.regex, self.repl, text)
