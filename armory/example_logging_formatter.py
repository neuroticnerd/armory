# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging


class MyFormatterExample(logging.Formatter):

    err_fmt = 'ERROR: %(msg)s'
    dbg_fmt = 'DBG: %(module)s: %(lineno)d: %(msg)s'
    info_fmt = '%(msg)s'

    def __init__(self, fmt='%(levelno)s: %(msg)s'):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = MyFormatterExample.dbg_fmt
        elif record.levelno == logging.INFO:
            self._fmt = MyFormatterExample.info_fmt
        elif record.levelno == logging.ERROR:
            self._fmt = MyFormatterExample.err_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result
