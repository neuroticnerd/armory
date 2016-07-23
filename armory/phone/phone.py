# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import logging
import smtplib

from armory.phone.lookup import carrier_lookup
from armory.serialize import jsonify


class PhoneNumber(object):
    """lookup country code and carrier for a phone number"""
    def __init__(self, phonenumber=None, data=None, logger=None, comment=None):
        self._logger = logger if logger else ''
        self.log = logging.getLogger(self._logger)
        self._raw = None
        self._carrier = None
        self._type = None
        self._comment = None
        self.number = ''
        if data is not None:
            self._raw = data
            self._unpack()
        if phonenumber is not None:
            num = phonenumber.strip()
            num = num.replace('(', '')
            num = num.replace(')', '')
            num = num.replace('-', '')
            num = num.replace(' ', '')
            if len(num) != 10:
                raise ValueError('phone number is not 10 digits')
            self.number = num
        if comment is not None:
            self._comment = comment

    @property
    def raw(self):
        if not self._raw:
            self.lookup()
        return self._raw

    @property
    def carrier(self):
        if not self._carrier:
            self.lookup()
        return self._carrier

    @property
    def type(self):
        if not self._type:
            self.lookup()
        return self._type

    def _unpack(self):
        if not self._raw:
            return
        raw = self._raw
        success = raw.get('success')
        if not success:
            raise ValueError('raw data could not be unpacked')
        data = raw.get('body')
        carrier = data.get('carrier')
        self._carrier = carrier.get('name')
        self._type = carrier.get('type')

    def lookup(self):
        log = self.log
        try:
            info = carrier_lookup(self.number, self._logger)
        except ValueError:
            raise SystemExit()
        log.debug(jsonify(info))
        self._raw = info
        self._unpack()
        self._raw['comment'] = self._comment
        return info


# http://stackoverflow.com/questions/9763455/how-to-send-a-mail-directly-to-smtp-server-without-authentication
class EmailSMS(object):
    def __init__(self, server, username, passcode, sender=None, logger=None):
        logger = logger if logger else __name__
        self.log = logging.getLogger(logger)
        self._smtp = None
        self._smtp_tls = True
        self._smtp_login = True
        self._server = server
        self._smtp_user = username
        self._passcode = passcode
        self._sender = sender if sender else self._smtp_user

    def __enter__(self):
        self._initialize_smtp()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._smtp:
            self._smtp.quit()
        self._smtp = None

    def _initialize_smtp(self):
        self._smtp = smtplib.SMTP(self._server)
        self._smtp.starttls()
        self._smtp.login(self._smtp_user, self._passcode)

    @property
    def smtp(self):
        if not self._smtp:
            self._initialize_smtp()
        return self._smtp

    def send(self, recipient, message):
        self.smtp.sendmail(self._sender, recipient, message)
        self.log.info('sender: {0}'.format(self._sender))
        self.log.info('recipient: {0}'.format(recipient))
        self.log.info('message: "{0}"'.format(message))
        self.log.info('')
