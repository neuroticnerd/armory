# -*- encoding: utf8 -*-
from __future__ import absolute_import, unicode_literals

import gevent
from gevent.hub import Hub
from gevent.pool import Group


class AliveGroup(Group):
    """gevent Group with extra method to determine greenlet status."""
    def alive(self):
        for greenlet in self.greenlets:
            if not greenlet.ready():
                return True
        return False


def patch_gevent_hub():
    """
    This patches the error handler in the gevent Hub object.

    The Hub object in gevent processes exceptions raised by Greenlets,
    however, under certain circumstances the system exception would be printed
    to console even though it is simply supposed to be thrown upwards to let
    the external code deal with it. This was due to how the control structure
    in the error handling function was implemented; the function below patches
    the Hub object to resolve this undesirable behavior.
    """
    def patched_handle_error(self, context, etype, value, tb):
        """ Patched to not print KeyboardInterrupt exceptions. """
        if isinstance(value, str):
            value = etype(value)
        not_error = issubclass(etype, self.NOT_ERROR)
        system_error = issubclass(etype, self.SYSTEM_ERROR)
        if not not_error and not issubclass(etype, KeyboardInterrupt):
            self.print_exception(context, etype, value, tb)
        if context is None or system_error:
            self.handle_system_error(etype, value)

    Hub._original_handle_error = Hub.handle_error
    Hub.handle_error = patched_handle_error


def monkey_patch_all():
    patch_gevent_hub()
    gevent.monkey.patch_all()
    return True
