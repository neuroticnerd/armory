# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import requests
import json
import logging

from bs4 import BeautifulSoup as htmldoc


def carrier_lookup():
    return None


class CarrierLookup(object):
    def __init__(self, number, logname=None):
        self.number = number
        self._logname = logname if logname else ''
        self.log = logging.getLogger(self._logname)

    def lookup(self):
        log = self.log

        domain = 'www.twilio.com'
        host = 'https://{0}'.format(domain)
        lookup = '{0}/lookup'.format(host)

        # masquerade as OS-X Firefox
        s = requests.Session()
        s.headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:37.0) Gecko/20100101 Firefox/37.0'
        s.headers['x-requested-with'] = 'XMLHttpRequest'
        s.headers['accept-language'] = 'en-US,en;q=0.5'
        s.headers['cache-control'] = 'no-cache'
        s.headers['content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        s.headers['host'] = domain
        s.headers['DNT'] = '1'
        s.headers['connection'] = 'close'

        # fetch the base page to set the cookies and get csrf and sid values
        r = s.get(lookup)
        hdrs = {k: v for k, v in s.headers.iteritems()}
        cookies = [{c.name: c.value} for c in s.cookies]
        log.debug('\nsession headers: {0}\n'.format(jsonify(hdrs)))
        log.debug('\nsession cookies: {0}\n'.format(jsonify(cookies)))
        if not cookies:
            log.error('unknown error accessing base page: {0}'.format(lookup))
            log.error('ERROR: {0}'.format(r.status_code))
            log.error(r.text)
            raise ValueError()

        # extract the csrf and sid
        page = htmldoc(r.text)
        token = page.find('meta', attrs={'name': 'csrfToken'})
        if token is None:
            log.debug(r.text)
        csrf = token['content']
        log.debug('NAME={0} CONTENT={1}'.format(token['name'], csrf))
        sid_attrs = {'type': 'hidden', 'role': 'visitorSid'}
        role = page.find('input', attrs=sid_attrs)
        sid = role['value']
        log.debug('ROLE={0} VALUE={1}'.format(role['role'], sid))

        # retrieve the phone number information
        s.headers['referer'] = lookup
        params = {
            'Type': 'lookup',
            'PhoneNumber': "{0}".format(self.number),
            'VisitorSid': sid,
            'CSRF': csrf,
        }
        log.debug('\nparams: {0}\n'.format(jsonify(params)))
        url = '{0}/functional-demos'.format(host)
        r = s.post(url, params=params)
        info = json.loads(r.content)
        return info
