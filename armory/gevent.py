# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from __future__ import division, print_function

"""
The Hub object in gevent processes exceptions raised by Greenlets, however,
under certain circumstances the system exception would be printed to console
even though it is simply supposed to be thrown upwards to let the external
code deal with it. This was due to how the control structure in the error
handling function was implemented; the function below patches the Hub object
to resolve this undesirable behavior.
"""


def patch_gevent_hub():
    """ this fixes the error handler in the gevent Hub object """
    from gevent.hub import Hub

    def fixed_handle_error(self, context, etype, value, tb):
        """ previously it did not properly handle certain system errors """
        if isinstance(value, str):
            value = etype(value)
        valid_error = (not issubclass(etype, self.NOT_ERROR))
        system_error = issubclass(etype, self.SYSTEM_ERROR)
        if valid_error and not system_error:
            self.print_exception(context, etype, value, tb)
        if context is None or system_error:
            self.handle_system_error(etype, value)

    Hub._original_handle_error = Hub.handle_error
    Hub.handle_error = fixed_handle_error
