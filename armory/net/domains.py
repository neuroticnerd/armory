from __future__ import absolute_import, unicode_literals

import logging
from collections import OrderedDict

# We use this to retrieve the list of top level domains we want
# http://stackoverflow.com/questions/14406300/python-urlparse-extract-domain-name-without-subdomain#answer-22228140
import tld

from .exceptions import ArmoryError

log = logging.getLogger(__name__)


TLD_LOOKUP_MAPPING = None
IDN_CCTLD_PREFIX = 'xn--'


class InvalidDomainError(ArmoryError):
    """Used to signify malformed or unrecognized domains."""
    pass


def init_tld_mapping(update=True, use_sorted=False):
    """This creates a TLD lookup mapping tree in reverse."""
    global TLD_LOOKUP_MAPPING
    if TLD_LOOKUP_MAPPING is not None:
        return

    log.debug('configuring TLD lookups...')

    if update:
        tld.utils.update_tld_names()

    TLD_LOOKUP_MAPPING = OrderedDict()

    for domain in tld.get_tld_names():
        current = TLD_LOOKUP_MAPPING
        for part in reversed(domain.split('.')):
            current.setdefault(part, OrderedDict())
            current = current[part]

    log.debug('done.')


def get_root_domain(domain, raises=False):
    """
    Extract the second level domain + TLD from a given domain string.

    Using an existing implementation for extracting the root domain was
    just too damn slow for large volumes of data, so this is faster.

    NOTE: this expects just the raw domain, you must use urlparse prior to
    calling this function if there is a protocol, querystring, or fragment.

    https://raventools.com/marketing-glossary/root-domain/
    https://moz.com/blog/understanding-root-domains-subdomains-vs-subfolders-microsites
    https://en.wikipedia.org/wiki/Second-level_domain
    """
    global IDN_CCTLD_PREFIX
    global TLD_LOOKUP_MAPPING
    lookup = TLD_LOOKUP_MAPPING
    length = len

    do_base_check = True
    domain_len = length(domain)
    sld_index = 0
    for part in reversed(domain.split('.')):
        # lookup = lookup.get(part, None) is slower than this way
        if part in lookup:
            lookup = lookup[part]
        else:
            lookup = None

        if do_base_check:
            if lookup is None:
                if part.startswith(IDN_CCTLD_PREFIX):
                    # this is a hacky way to deal with them being commented
                    # out in the publicsuffix.org source file
                    TLD_LOOKUP_MAPPING.setdefault(part, OrderedDict())
                    lookup = TLD_LOOKUP_MAPPING[part]
                elif raises:
                    error_msg = 'TLD \'{0}\' not found from {1}'
                    raise InvalidDomainError(error_msg.format(part, repr(domain)))
                else:
                    return None
            do_base_check = False

        sld_index += (length(part) + 1)
        if lookup is None:
            break

    sld_index = (domain_len - sld_index + 1)
    if sld_index < 0:
        sld_index = None

    return domain[sld_index:]


get_second_level_domain = get_root_domain
