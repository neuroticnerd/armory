from __future__ import absolute_import, print_function, unicode_literals

import io
import json
import logging
import random
from collections import OrderedDict

import dns
import dns.resolver

log = logging.getLogger(__name__)

DEFAULT_PUBLIC_RESOLVER_LIST = (
    # google public DNS
    '8.8.8.8',
    '8.8.4.4',

    # OpenDNS
    '208.67.222.222',  # (resolver1.opendns.com)
    '208.67.220.220',  # (resolver2.opendns.com)
    '208.67.222.220',  # (resolver3.opendns.com)
    '208.67.220.222',  # (resolver4.opendns.com)

    # level3 - http://www.level3.com/en/
    '209.244.0.3',
    '209.244.0.4',

    # verisign - https://www.verisign.com/en_US/security-services/public-dns/index.xhtml
    '64.6.64.6',
    '64.6.65.6',

    # freedns - https://freedns.zone/en/
    '37.235.1.174',
    '37.235.1.177',

    # hurricane electric - https://dns.he.net/
    '74.82.42.42',

    # neustar - https://www.security.neustar/dns-services/free-recursive-dns-service
    '156.154.70.1',
    '156.154.71.1',
)
RESOLVER_LIST_FILENAME = '/opt/massdns/lists/resolvers.txt'
DEFAULT_DNS_TIMEOUT = 6.0
DEFAULT_DNS_LIFETIME = 6.0
DEFAULT_DNS_RETRIES = 5
MIN_RESOLVER_COUNT = 400

PUBLIC_RESOLVER_LIST = None


class MisconfiguredDNS(dns.exception.DNSException):
    msg = 'Suspected incorrect DNS configuration.'
    fmt = 'Suspected incorrect DNS configuration - {errors}'
    supp_kwargs = set(['errors'])


def public_dns_resolver(cache=None, nameservers=None, ns_all=False, sample=False, sample_size=10):
    global PUBLIC_RESOLVER_LIST
    global RESOLVER_LIST_FILENAME

    low_resolver_count = False
    if PUBLIC_RESOLVER_LIST is not None and len(PUBLIC_RESOLVER_LIST) <= MIN_RESOLVER_COUNT:
        low_resolver_count = True
    if not nameservers and not PUBLIC_RESOLVER_LIST or low_resolver_count:
        PUBLIC_RESOLVER_LIST = list()
        with io.open(RESOLVER_LIST_FILENAME, mode='r', encoding='utf8') as resolver_file:
            for rawline in resolver_file:
                line = rawline.strip()
                if not line:
                    continue
                if ':' in line:
                    continue
                PUBLIC_RESOLVER_LIST.append(line)

    resolver_list = list(nameservers or PUBLIC_RESOLVER_LIST)
    if ns_all:
        resolv_conf = io.StringIO('\n'.join(['nameserver {0}'.format(ip) for ip in resolver_list]))
    elif sample:
        resolv_conf = io.StringIO('\n'.join([
            'nameserver {0}'.format(ip) for ip in random.sample(resolver_list, sample_size)
        ]))
    else:
        resolv_conf = io.StringIO('nameserver {0}'.format(random.choice(resolver_list)))

    resolver = dns.resolver.Resolver(filename=resolv_conf, configure=True)
    resolver.timeout = DEFAULT_DNS_TIMEOUT
    resolver.lifetime = DEFAULT_DNS_LIFETIME
    # resolver.rotate = True

    # NOTE: this is *very* important to force it to remove SERVFAIL from list
    resolver.retry_servfail = False

    if cache is True:
        global G_LOCAL_DNS_CACHE
        if not G_LOCAL_DNS_CACHE:
            G_LOCAL_DNS_CACHE = dns.resolver.Cache()
        resolver.cache = G_LOCAL_DNS_CACHE
    elif cache:
        resolver.cache = cache

    return resolver


def query_dns(
    query_name, query_type='A', retries=None, raises=False, suppress=None,
    answer_attr=None, tcp=False, **kwargs
):
    if retries is None:
        retries = DEFAULT_DNS_RETRIES
    elif not retries:
        retries = 1
    ns_timeout = list()
    ns_nonameservers = list()
    exc_info_list = list()
    suppress = suppress or tuple()
    # nonameservers_threshold = 3

    query_type = query_type.upper()
    rdtype_code = getattr(dns.rdatatype, query_type)
    result = set()

    for i in range(0, retries):
        resolver = public_dns_resolver(**kwargs)
        try:
            answers = resolver.query(query_name, query_type, tcp=tcp)
            for answer in answers.response.answer:
                for answer_data in answer:
                    if answer_data.rdtype == rdtype_code:
                        if answer_attr:
                            answer_value = getattr(answer_data, answer_attr)
                        else:
                            answer_value = answer_data
                        if hasattr(answer_value, 'to_text'):
                            answer_value = answer_value.to_text()
                        result.add(str(answer_value).strip())
            break
        except dns.resolver.NXDOMAIN as exc:
            log.debug('{0}: {1}'.format(exc.__class__.__name__, query_name))
            not_suppress = suppress is not True and dns.resolver.NXDOMAIN not in suppress
            if not_suppress and raises:
                raise exc
            break
        except dns.resolver.NoAnswer as exc:
            log.debug('{0}: {1}'.format(exc.__class__.__name__, query_name))
            not_suppress = suppress is not True and dns.resolver.NoAnswer not in suppress
            if not_suppress and raises:
                raise exc
            break
        except dns.resolver.NoNameservers as exc:
            exc_info = OrderedDict([
                ('type', str(exc.__class__.__name__)),
                ('value', str(exc)),
                ('nameserver', resolver.nameservers[0]),
            ])
            exc_info_list.append(exc_info)
            ns_nonameservers.append(resolver.nameservers[0])

            if ns_timeout and ns_nonameservers:
                # NOTE: a mix of timeouts and SERVFAIL is *almost always*
                # due to DNS config issues of the domain being queried
                raise MisconfiguredDNS(errors=json.dumps(exc_info_list))

            # if i + 1 < retries and len(ns_nonameservers) <= nonameservers_threshold:
            if i + 1 < retries:
                continue

            exc.fmt = exc.fmt + ' {0}'.format(ns_nonameservers)
            exc.msg = exc.msg + ' {0}'.format(ns_nonameservers)
            log.error('{0}: {1}  {2}'.format(
                exc.__class__.__name__, query_name, ns_nonameservers
            ))

            if suppress is not True and dns.resolver.NoNameservers not in suppress:
                raise exc
        except dns.exception.Timeout as exc:
            global PUBLIC_RESOLVER_LIST
            PUBLIC_RESOLVER_LIST.remove(resolver.nameservers[0])

            exc_info = OrderedDict([
                ('type', str(exc.__class__.__name__)),
                ('value', str(exc)),
                ('nameserver', resolver.nameservers[0]),
            ])
            exc_info_list.append(exc_info)
            ns_timeout.append(resolver.nameservers[0])

            if ns_timeout and ns_nonameservers:
                # NOTE: a mix of timeouts and SERVFAIL is *almost always*
                # due to DNS config issues of the domain being queried
                raise MisconfiguredDNS(errors=json.dumps(exc_info_list))

            if i + 1 < retries:
                continue

            exc.fmt = exc.fmt + ' {0}'.format(ns_timeout)
            exc.msg = exc.msg + ' {0}'.format(ns_timeout)
            log.error('{0}: {1} query_name = {2}'.format(exc.__class__.__name__, exc, query_name))

            if suppress is not True and dns.exception.Timeout not in suppress:
                raise exc

    return list(result)


if __name__ == '__main__':
    print(query_dns(sys.argv[1]))
