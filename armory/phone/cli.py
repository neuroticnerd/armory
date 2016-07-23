#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

try:
    input = raw_input
except:
    pass

import click
import os
import logging
import json

from collections import OrderedDict

from armory.serialize import jsonify
from armory.phone.phone import PhoneNumber, EmailSMS

CONFIG_FILE = '.phonecache'

helptxt = {}
helptxt['config_file'] = 'specify the config file location'
helptxt['list_lookups'] = 'list the currently stored lookups'

#@click.argument('import_path', click.Path(exists=True), required=False)
@click.group(invoke_without_command=True)
@click.option(
    '-c', '--config', 'config',
    help=helptxt.get('config_file'))
@click.option(
    '-l', '--list', 'list_lookups',
    is_flag=True, default=False, #is_eager=True,
    help=helptxt.get('list_lookups'))
@click.version_option(message='%(prog)s %(version)s')
@click.pass_context
def CLI(ctx, config, list_lookups):
    """Lookup basic phone number information or send SMS messages"""
    loglevel = 'info'
    verbosity = getattr(logging, loglevel.upper(), 'INFO')
    #verbosity = logging.DEBUG
    ctx.obj = {
        'verbosity': verbosity,
        'logfile': None,
        'config': {'lookups': {}},
    }
    #logfmt = '%(levelname)-8s | %(message)s'
    logfmt = '%(message)s'
    logging.basicConfig(format=logfmt, level=verbosity)
    debug('CLI >  CWD="{0}"'.format(os.getcwd()))
    with open(CONFIG_FILE, 'ab+') as phonedb:
        phonedb.seek(0)
        rawdata = phonedb.read()
        if rawdata:
            data = json.loads(rawdata, object_pairs_hook=OrderedDict)
            debug(data)
            ctx.obj['config'] = data
            if 'lookups' not in ctx.obj['config']:
                ctx.obj['config']['lookups'] = {}

    if 'sms_gateways' not in ctx.obj['config']:
        """
        gwsorted = sorted(ctx.obj['config']['sms_gateways'].items())
        gwordered = OrderedDict()
        for (k, v) in gwsorted:
            gwordered[k] = v
        ctx.obj['config']['sms_gateways'] = gwordered
        """
        info('loading SMS gateways...')
        sms_gateways = {}
        with open('carrier-gateways', 'rb') as gateways:
            gwdata = gateways.read()
            import re
            re_carrier = r'(?P<carrier>\w+[\w\&\(\)\-\'\s]*[\w\)\(]+)\s+'
            re_gateway = r'10digitphonenumber(?P<gateway>\@\w[\w\.]*\w)\s+'
            gwre = re.compile(re_carrier + re_gateway)
            gws = gwre.findall(gwdata)
            for gw in gwre.finditer(gwdata):
                gwinfo = gw.groupdict()
                debug(gw.groupdict())
                sms_gateways[gwinfo['carrier']] = gwinfo['gateway']
            num_lines = len([l for l in gwdata.split('\n') if len(l)])
            debug('lines={0} ({1} / 2)'.format(num_lines/2, num_lines))
            debug('matches={0}'.format(len(data)))
        ctx.obj['config']['sms_gateways'] = sms_gateways
        with open(CONFIG_FILE, 'wb') as cfg:
            cfg.write(json.dumps(ctx.obj['config'], indent=2))
        info('SMS gateways written to config')

    if list_lookups:
        sms_updated = False
        from fuzzywuzzy import fuzz
        from fuzzywuzzy import process
        lookups = ctx.obj['config']['lookups']
        info('cached lookups:')
        for number, pinfo in lookups.iteritems():
            owner = pinfo['comment']
            common = pinfo['body']['national_format']
            carrier = pinfo['body']['carrier']['name']
            pntype = pinfo['body']['carrier']['type']
            info('  {0}: {1}'.format(owner, common))
            info('    - carrier: {0}'.format(carrier))
            info('    - type: {0}'.format(pntype))
            debug('    - unformatted: {0}'.format(number))
            if 'sms' not in lookups[number]:
                carriers = ctx.obj['config']['sms_gateways'].keys()
                fuzzy = process.extract(carrier, carriers)
                fuzz_max = 0
                result = []
                gateway_key = None
                for f in fuzzy:
                    if f[1] >= fuzz_max:
                        fuzz_max = f[1]
                        result.append(f[0])
                debug(result)
                if len(result) > 1:
                    if len(sorted(result)[0]) <= len(carrier):
                        gateway_key = sorted(result)[0]
                    else:
                        gateway_key = result[0]
                else:
                    gateway_key = result[0]
                gw_suffix = ctx.obj['config']['sms_gateways'][gateway_key]
                ctx.obj['config']['lookups'][number]['sms'] = '{0}{1}'.format(
                    number, gw_suffix)
                sms_updated = True
            info('    - SMS gateway: {0}'.format(
                ctx.obj['config']['lookups'][number]['sms']))
        if sms_updated:
            with open(CONFIG_FILE, 'wb') as cfg:
                cfg.write(json.dumps(ctx.obj['config'], indent=2))
        ctx.exit()


helptxt['comment'] = 'add a comment to the phone number record (recommended)'
helptxt['nocache'] = 'do not cache the results into the config file'


@click.command()
@click.option(
    '-c', '--comment', 'comment',
    help=helptxt.get('comment'))
@click.option(
    '--no-cache', 'cache',
    is_flag=True, default=True,
    help=helptxt.get('nocache'))
@click.argument('number')
@click.pass_context
def lookup(ctx, number, comment, cache):
    """Get the carrier and country code for a phone number"""
    phone = PhoneNumber(number, comment=comment)
    info('{0} | {1}'.format(phone.number, ctx.obj['config']['lookups'].keys()))
    if phone.number in ctx.obj['config']['lookups']:
        info('{0} is already cached:'.format(phone.number))
        info(jsonify(ctx.obj['config']['lookups'][phone.number]))
        return
    data = phone.lookup()
    info('carrier = {0}'.format(phone.carrier))
    info('type = {0}'.format(phone.type))
    info('cache = {0}'.format(cache))
    if cache:
        ctx.obj['config']['lookups'][phone.number] = phone.raw
        with open(CONFIG_FILE, 'wb') as cfg:
            cfg.write(json.dumps(ctx.obj['config'], indent=2))

CLI.add_command(lookup)


helptxt['phone_number'] = '10 digit US/CA phone number'
helptxt['send_all'] = 'message is sent to all cached numbers (-n is ignored)'
helptxt['sms_message'] = 'SMS message to be sent to recipients (required)'


@click.command()
@click.option(
    '-n', '--number', 'numbers',
    multiple=True,
    help=helptxt.get('phone_number'))
@click.option(
    '--all', 'send_all',
    is_flag=True, default=False,
    help=helptxt.get('send_all'))
@click.option(
    '-m', '--message', 'message',
    required=True,
    help=helptxt.get('sms_message'))
@click.pass_context
def sms(ctx, numbers, send_all, message):
    smtp_login = ctx.obj['config'].get('smtp_login', None)
    if smtp_login is None:
        error('cannot send SMS messages until SMTP has been configured')
        return
    debug(numbers)
    debug('message="{0}"'.format(message))
    debug(jsonify(smtp_login))
    if len(message) > 160:
        info('converting to multipart message...')
        return
    lookups = ctx.obj['config'].get('lookups')
    if send_all:
        info('sending to all stored phone numbers...')
        with EmailSMS(**smtp_login) as smsgw:
            for num, data in lookups.iteritems():
                info('sending to {0}[{1}]'.format(
                    data['comment'], data['sms']))
                smsgw.send(data['sms'], message)
    elif len(numbers):
        info('sending to numbers: {0}'.format(numbers))
        with EmailSMS(**smtp_login) as smsgw:
            for num in numbers:
                data = lookups.get(num, None)
                if not data:
                    info('WARNING | unknown number: {0}'.format(num))
                    continue
                info('sending to {0}[{1}]'.format(
                    data['comment'], data['sms']))
                smsgw.send(data['sms'], message)
    else:
        info('no numbers have been selected!')

CLI.add_command(sms)


helptxt['config_server'] = 'SMTP server which should be used to proxy SMS'
helptxt['config_uname'] = 'SMTP server login username'
helptxt['config_pass'] = 'SMTP server login passcode'


@click.command()
@click.option(
    '-s', '--server', 'server',
    help=helptxt.get('config_server'))
@click.option(
    '-u', '--user', 'username',
    help=helptxt.get('config_uname'))
@click.option(
    '-p', '--pass', 'passcode',
    help=helptxt.get('config_pass'))
@click.pass_context
def config(ctx, server, username, passcode):
    smtp_login = ctx.obj['config'].get('smtp_login', None)
    if smtp_login is None:
        ctx.obj['config']['smtp_login'] = OrderedDict()
        smtp_login['server'] = None
        smtp_login['username'] = None
        smtp_login['passcode'] = None
        smtp_login = ctx.obj['config']['smtp_login']
    debug(jsonify(ctx.obj['config']['smtp_login']))

    update_config = False
    if server is not None and server != smtp_login['server']:
        smtp_login['server'] = server
        info('SMTP server set to: {0}'.format(server))
        update_config = True
    elif server is not None:
        info('SMTP server is already set to: {0}'.format(server))
    if username is not None and username != smtp_login['username']:
        smtp_login['username'] = username
        info('SMTP username set to: {0}'.format(username))
        update_config = True
    elif username is not None:
        info('SMTP username is already set to: {0}'.format(username))
    if passcode is not None and passcode != smtp_login['passcode']:
        smtp_login['passcode'] = passcode
        info('SMTP passcode set to: {0}'.format(passcode))
        update_config = True
    elif passcode is not None:
        info('SMTP passcode is already set to: {0}'.format(passcode))

    if not update_config:
        info('no config changes to write')
        return
    with open(CONFIG_FILE, 'wb') as config:
        config.write(jsonify(ctx.obj['config']))
    info('\nSMTP settings:')
    info('  - server = {0}'.format(ctx.obj['config']['smtp_login']['server']))
    info('  - user = {0}'.format(ctx.obj['config']['smtp_login']['username']))
    info('  - pass = {0}'.format(ctx.obj['config']['smtp_login']['passcode']))

CLI.add_command(config)
