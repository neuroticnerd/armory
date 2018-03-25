from __future__ import absolute_import, unicode_literals

import socket
import struct


def ipv4_to_int(ip_addr):
    """
    Convert an IPv4 address represented as a str to an int scalar.

    Network byte order is big-endian so we use '>' for the conversion.
    """
    return struct.unpack('>L', socket.inet_aton(ip_addr))[0]


def ipv6_to_int(ip_addr, separate=False):
    """
    Convert an IPv6 address represented as a str to an int scalar or int tuple.

    Network byte order is big-endian so we use '>' for the conversion.
    """
    hi, lo = struct.unpack('>QQ', socket.inet_pton(socket.AF_INET6, ip_addr))
    if separate:
        result = (hi, lo)
    else:
        result = (hi << 64) | lo
    return result


def ip_to_int(ip_addr, separate=False):
    try:
        if separate:
            return (0, ipv4_to_int(ip_addr))
        else:
            return ipv4_to_int(ip_addr)
    except OSError:
        return ipv6_to_int(ip_addr, separate)


def ip_int_str(ip_addr):
    """ Returns the string representation of the IP address integer. """
    return '{0}'.format(ip_to_int(ip_addr))
