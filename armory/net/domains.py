from __future__ import absolute_import, unicode_literals

import logging

from sortedcontainers import SortedDict

# We use this to retrieve the list of top level domains we want
# http://stackoverflow.com/questions/14406300/python-urlparse-extract-domain-name-without-subdomain#answer-22228140
import tld

from .exceptions import ArmoryError

log = logging.getLogger(__name__)


DEFAULT_ENCODING_LIST = (
    'ISO-8859-2',
    'ISO-8859-1',
    'utf-8',
    'windows-1250',
    'windows-1252',
    'utf-16',
)
DEFAULT_ENCODING = 'utf-8'
DEFAULT_DELIMITER = ','
TLD_LOOKUP_MAPPING = None


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

    # TODO: is the SortedDict actually faster at all?
    def get_dict():
        if use_sorted:
            result = SortedDict()
        else:
            result = dict()
        return result

    TLD_LOOKUP_MAPPING = get_dict()

    for domain in tld.get_tld_names():
        current = TLD_LOOKUP_MAPPING
        for part in reversed(domain.split('.')):
            current.setdefault(part, get_dict())
            current = current[part]

    log.debug('done.')


def get_root_domain(domain):
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
    root = []
    lookup = TLD_LOOKUP_MAPPING
    base_check = True
    domain_parts = reversed(domain.split('.'))
    for part in domain_parts:
        lookup = lookup.get(part, None)
        if base_check:
            if lookup is None:
                raise InvalidDomainError('TLD not found: "{0}"'.format(part))
            base_check = False
        root.insert(0, part)
        if lookup is None:
            break

    result = '.'.join(root)
    return result


get_second_level_domain = get_root_domain
