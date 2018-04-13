# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import io
import logging
import re
import sys
import unicodedata

log = logging.getLogger(__name__)

DEFAULT_ENCODING_LIST = (
    'utf8',
    'ISO-8859-2',
    'ISO-8859-1',
    'windows-1250',
    'utf16',
    'windows-1252',
)
DEFAULT_ENCODING = 'utf8'


def iter_decoded_lines(self, filename, encoding=None, offset=0, try_encodings=None):
    """
    Yield lines in the input file, decode if needed.

    This also tries decoding the file lines manually since its
    nearly impossible to guess the file encoding beforehand unless it has
    been passed as an option, in which case we assume the given value to
    be correct.
    """
    try_encodings = try_encodings or DEFAULT_ENCODING_LIST
    encoding_known = bool(encoding)
    encoding = encoding or DEFAULT_ENCODING
    file_opts = dict()
    if encoding_known:
        file_opts['encoding'] = encoding
    file_opts['mode'] = 'r' if encoding_known else 'rb'

    with io.open(filename, **file_opts) as infile:
        if offset > 0:
            log.info('attempting to advance to offset...')
            infile.seek(0, io.SEEK_END)
            file_end = infile.tell()
            if file_end > offset:
                new_positioin = infile.seek(offset)
                if new_positioin != offset:
                    raise ValueError('unable to seek to offset: {0}'.format(offset))
                log.info('reached offset: {0}'.format(offset))
            else:
                infile.seek(0)
                log.error('invalid offset: {0}'.format(offset))

        if encoding_known:
            for line in infile:
                yield line
        else:
            for line in infile:
                is_decoded = False
                for encoding in try_encodings:
                    try:
                        yield line.decode(encoding)
                        is_decoded = True
                        break
                    except UnicodeDecodeError:
                        pass
                if not is_decoded:  # pragma: no cover
                    log.error('unable to decode line {0}'.format(repr(line)))


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
