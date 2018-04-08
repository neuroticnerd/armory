from __future__ import absolute_import, unicode_literals

import logging

log = logging.getLogger(__name__)


class ExceptionGuard(object):
    """
    Context manager which captures, logs, and/or propagates exceptions.

    This can be used via 'with' to capture and log exceptions, while
    optionally allowing the exceptions to continue to propagate (default
    behavior is to prevent propagation, suppressing the error after logging
    it). Additional parameters allow the caller to specify specific exception
    types to either capture or ignore.

    Passing types to the trap parameter allows the caller to define a specific
    set of exceptions which they want to perform logging on while skipping
    others. Defaults to logging on any Exception subclass.

    Passing types to the ignore parameter allows the caller to define a
    specific set of exception which they want to skip any logging on while
    performing logging for others. Defaults to ignoring only SystemExit
    (pass empty tuple or list to ignore parameter if you wish to capture
    SystemExit as well).

    log + suppress
    log + propagate
    ignore + suppress
    ignore + propagate
    """

    def __init__(self, suppress=False, trap=None, ignore=None, propagate=None):
        """
        :param suppress: Specifies whether to allow propagation
        :type suppress: bool
        :param trap: Exception types which should be intercepted
        :type trap: tuple or list of exception types, Exception subclass
        :param ignore: Exception types which logging should be skipped on
        :type ignore: tuple or list of exception types, Exception subclass
        :param propagate: exceptions to propagate whether logged or not
        :type propagate: tuple or list of exception types, Exception subclass
        """
        self.reraise_nontrapped = False
        self.suppress = suppress

        if trap is None or trap is True:
            trap = (Exception,)
        elif trap is False:
            trap = tuple()
        elif trap and issubclass(trap, Exception):
            trap = (trap,)
        self.trap = tuple(set(trap))

        if ignore is None:
            ignore = (SystemExit, KeyboardInterrupt)
        elif ignore and issubclass(ignore, Exception):
            ignore = (ignore,)
        self.ignore = tuple(set(ignore))

        if propagate is True:
            self.reraise_nontrapped = True
            propagate = tuple()
        elif propagate is None:
            propagate = (SystemExit, KeyboardInterrupt)
        elif not propagate:
            propagate = tuple()
        elif propagate and issubclass(propagate, Exception):
            propagate = (propagate,)
        self.propagate = tuple(set(propagate))

        self.error = False
        self.logged = False
        self.exc_info = None
        self.err_msg = None

    def __enter__(self):
        return self

    def __exit__(self, etype, value, tb):
        """
        TODO: add option to log full stack trace
        TODO: and logging without newline chars for logfiles
        http://stackoverflow.com/questions/13210436/get-full-traceback
        http://blog.dscpl.com.au/2015/03/generating-full-stack-traces-for.html
        """
        self.error = (value is not None)
        if self.error:
            self.exc_info = (etype, value, tb)
            self.err_msg = '{0}'.format(value)
        if etype is None and value is None:
            return

        if issubclass(etype, self.ignore):
            if issubclass(etype, self.propagate):
                return
            return self.suppress
        elif not issubclass(etype, self.trap):
            if self.reraise_nontrapped:
                return
            if issubclass(etype, self.propagate):
                return
            return self.suppress

        log.error('Unexpected Error!  ', exc_info=(etype, value, tb))
        self.logged = True
        return self.suppress
