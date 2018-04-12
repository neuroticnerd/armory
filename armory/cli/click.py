from __future__ import absolute_import, unicode_literals

import logging
import re

from collections import OrderedDict
from datetime import datetime
from datetime import timedelta

import click

from dateutil.parser import parse as parse_date
from dateutil.tz import tzutc

log = logging.getLogger(__name__)


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class DeltaDateParamType(click.ParamType):
    name = 'datedelta'
    re_delta = re.compile(r'^(?P<delta>(?:\d+[wWdDhHmMsS]){1,}?)$')
    re_values = re.compile((
        r'(?:(?P<weeks>\d+)[wW])|'
        r'(?:(?P<days>\d+)[dD])|'
        r'(?:(?P<hours>\d+)[hH])|'
        r'(?:(?P<minutes>\d+)[mM])|'
        r'(?:(?P<seconds>\d+)[sS])'
    ))

    def convert(self, value, param, ctx):
        now = datetime.now(tzutc())
        try:
            match = self.re_delta.match(value)
            if match is not None:
                values = {}
                for m in self.re_values.finditer(match.group('delta')):
                    for key, delta in m.groupdict().items():
                        if delta is not None:
                            values.setdefault(key, int(delta))
                result = now - timedelta(**values)
                has_time = (
                    'hours' in values or
                    'minutes' in values or
                    'seconds' in values
                )
                if not has_time:
                    result = result.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
            else:
                result = parse_date(value)
                result.replace(tzinfo=tzutc())
            return result
        except ValueError:
            fail_msg = '{0} is not a valid date delta'
            self.fail(fail_msg.format(value), param, ctx)


DELTA_DATE = DeltaDateParamType()


class InvocationContext(object):
    def __init__(self):
        self._settings = OrderedDict()

    def add_param(self, name, value):
        self._settings[name] = value

    def __getitem__(self, key):
        return self._settings[key]

    def get(self, key, default=None):
        return self._settings.get(key, default)


pass_invocation_context = click.make_pass_decorator(
    InvocationContext, ensure=True
)


def add_to_context(ctx, param, value):
    context = ctx.ensure_object(InvocationContext)
    context.add_param(param.name, value)
    return value


def option_verbosity(func):
    return click.option(
        '-v', '--verbose', 'verbosity',
        count=True,
        help='Determines verbosity of log messages (not level)',
        expose_value=False,
        callback=add_to_context,
    )(func)


def option_debug(func):
    return click.option(
        '--debug', 'debug',
        is_flag=True,
        default=False,
        help='Enable debug logging messages',
        expose_value=False,
        callback=add_to_context,
    )(func)


def option_sqldebug(func):
    return click.option(
        '--sqldebug', 'sqldebug',
        is_flag=True,
        default=False,
        help='Enable debug logging for sqlalchemy',
        expose_value=False,
        callback=add_to_context,
    )(func)


def option_showconf(func):
    return click.option(
        '--show-config', 'showconf',
        is_flag=True,
        default=False,
        help='Displays configuration in INFO log messages',
        expose_value=False,
        callback=add_to_context,
    )(func)


def option_config(func):
    # TODO: determine if this should be an eager option that autoloads.
    return click.option(
        '--config', 'config_file',
        type=click.Path(readable=True, dir_okay=False, exists=True),
        default=None,
        help='Path to configuration properties file',
        # expose_value=False,
        callback=add_to_context,
    )(func)
