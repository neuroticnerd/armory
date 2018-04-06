# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import socket
import struct

from intervaltree import IntervalTree


RESERVED_IP_RANGES = None


def init_reserved_ip_ranges():
    global RESERVED_IP_RANGES
    if RESERVED_IP_RANGES is not None:
        return RESERVED_IP_RANGES

    # TODO: try to find a better way to construct this or keep it
    #     updated rather than hard-coding the IP ranges
    _reserved_ip_blocks = (
        # 'this'
        (ip_to_int('0.0.0.0'), ip_to_int('0.255.255.255')),
        # localhost
        (ip_to_int('127.0.0.0'), ip_to_int('127.255.255.255')),
        # local private network
        (ip_to_int('10.0.0.0'), ip_to_int('10.255.255.255')),
        # local private network
        (ip_to_int('172.16.0.0'), ip_to_int('172.31.255.255')),
        # for the IANA IPv4 Special Purpose Address Registry
        (ip_to_int('192.168.0.0'), ip_to_int('192.168.255.255')),
        # link-local addresses
        (ip_to_int('169.254.0.0'), ip_to_int('169.254.255.255')),
        # multicast
        (ip_to_int('224.0.0.1'), ip_to_int('239.255.255.255')),
    )
    RESERVED_IP_RANGES = IntervalTree()
    for start_ip, stop_ip in _reserved_ip_blocks:
        # TODO: should the data value just be True to conserve memory?
        # or should the value be what the range is actually reserved for?
        RESERVED_IP_RANGES[start_ip:(stop_ip + 1)] = 'reserved'

    return RESERVED_IP_RANGES


def get_reserved_ip_ranges():
    global RESERVED_IP_RANGES
    init_reserved_ip_ranges()
    return RESERVED_IP_RANGES


class IPAddrInfo(object):

    def __init__(self, ip_addr=None, ip_int=None, version=None, reserved=None):
        self.ip = ip_addr
        self.ip_int = ip_int
        self.version = version
        if version == 4:
            self.ipv4 = True
            self.ipv6 = False
        elif version == 6:
            self.ipv4 = False
            self.ipv6 = True
        else:
            self.ipv4 = None
            self.ipv6 = None
        self.iana_reserved = reserved
        self._gathered = False
        self._inflate()

    def __int__(self):
        """NOTE: because of the ip_int property, this could return None!"""
        return self.ip_int

    def __float__(self):
        return float(self.ip_int) if self.ip_int is not None else None

    def __and__(self, other):
        return (self.ip_int or 0) & other

    def __or__(self, other):
        return (self.ip_int or 0) | other

    def _inflate(self):
        if self._gathered:
            return

        if self.ip:
            try:
                self.ip_int = ipv4_to_int(self.ip)
                self.version = 4
            except OSError:
                self.ip_int = ipv6_to_int(self.ip)
                self.version = 6
        elif self.ip_int:
            try:
                self.ip = socket.inet_ntop(socket.AF_INET, struct.pack('>L', self.ip_int))
                self.version = 4
            except (struct.error, ValueError):
                hi_bits = (self.ip_int >> 64)
                lo_bits = (self.ip_int & ((1 << 64) - 1))
                self.ip = socket.inet_ntop(socket.AF_INET6, struct.pack('>QQ', hi_bits, lo_bits))
                self.version = 6

        if self.ip_int is not None:
            global RESERVED_IP_RANGES
            self.iana_reserved = bool(RESERVED_IP_RANGES[self.ip_int])

        self._gathered = True

    @property
    def ip_int_censored(self):
        if self.iana_reserved:
            return None
        return self.ip_int

    def hi_lo(self):
        hi = (self.ip_int >> 64)
        lo = (self.ip_int & ((1 << 64) - 1))
        return (hi, lo)


def ipv4_to_int(ip_addr, hi_lo=False):
    """
    Convert an IPv4 address to an integer value.

    Network byte order is big-endian so we use '>' for the conversion.
    """
    result = struct.unpack('>L', socket.inet_pton(socket.AF_INET, ip_addr))[0]
    if hi_lo:
        result = (0, result)
    return result


def ipv6_to_int(ip_addr, hi_lo=False):
    """
    Convert an IPv6 address to an integer value or tuple.

    Network byte order is big-endian so we use '>' for the conversion.
    """
    hi, lo = struct.unpack('>QQ', socket.inet_pton(socket.AF_INET6, ip_addr))
    if hi_lo:
        result = (hi, lo)
    else:
        result = (hi << 64) | lo
    return result


def ip_to_int(ip_addr, **kwargs):
    """Returns an integer or tuple of two integers representing the IP."""
    try:
        return ipv4_to_int(ip_addr, **kwargs)
    except OSError:
        return ipv6_to_int(ip_addr, **kwargs)


def ip_int_str(ip_addr):
    """Returns the string representation of the IP address integer."""
    return '{0}'.format(ip_to_int(ip_addr))


def int_to_ip(ip_int):
    try:
        return socket.inet_ntop(socket.AF_INET, struct.pack('>L', ip_int))
    except (struct.error, ValueError):
        hi = (ip_int >> 64)
        lo = (ip_int & ((1 << 64) - 1))
        return socket.inet_ntop(socket.AF_INET6, struct.pack('>QQ', hi, lo))


def get_ip_info(ip_addr=None, ip_int=None):
    if ip_addr:
        try:
            return IPAddrInfo(ip_addr=ip_addr, ip_int=ipv4_to_int(ip_addr), version=4)
        except OSError:
            return IPAddrInfo(ip_addr=ip_addr, ip_int=ipv6_to_int(ip_addr), version=6)
    elif ip_int:
        try:
            ip_addr = socket.inet_ntop(socket.AF_INET, struct.pack('>L', ip_int))
            return IPAddrInfo(ip_addr=ip_addr, ip_int=ip_int, version=4)
        except (struct.error, ValueError):
            hi = (ip_int >> 64)
            lo = (ip_int & ((1 << 64) - 1))
            ip_addr = socket.inet_ntop(socket.AF_INET6, struct.pack('>QQ', hi, lo))
            return IPAddrInfo(ip_addr=ip_addr, ip_int=ip_int, version=6)
    return None
