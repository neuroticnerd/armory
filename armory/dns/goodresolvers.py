#! /usr/bin/env python3
from __future__ import absolute_import, print_function, unicode_literals

import argparse
import hashlib
import io
import itertools
import json
import logging
import os
import random
import sys
import time
from collections import OrderedDict
from datetime import datetime

import dns.resolver
import dns.reversename

import requests

log = logging.getLogger(__name__)

PUBLIC_RESOLVER_LIST = (
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
DEFAULT_DNS_TIMEOUT = 3.0


def public_dns_resolver(cache=None, nameservers=None, shuffle=True, rand_one=False):
    resolver_list = nameservers or PUBLIC_RESOLVER_LIST
    if rand_one:
        resolv_conf = io.StringIO('nameserver {0}'.format(random.choice(resolver_list)))
    elif shuffle:
        ns_list = list(resolver_list)
        random.shuffle(ns_list)
        resolv_conf = io.StringIO('\n'.join([
            'nameserver {0}'.format(ip) for ip in ns_list
        ]))
    else:
        resolv_conf = io.StringIO('\n'.join([
            'nameserver {0}'.format(ip) for ip in resolver_list
        ]))
    resolver = dns.resolver.Resolver(filename=resolv_conf, configure=True)
    resolver.timeout = DEFAULT_DNS_TIMEOUT
    resolver.lifetime = DEFAULT_DNS_TIMEOUT

    if cache is True:
        global G_LOCAL_DNS_CACHE
        if not G_LOCAL_DNS_CACHE:
            G_LOCAL_DNS_CACHE = dns.resolver.Cache()
        resolver.cache = G_LOCAL_DNS_CACHE
    elif cache:
        resolver.cache = cache

    # print('new resolver: {0}'.format(resolver.nameservers))
    return resolver


class FindGoodResolvers(object):

    def __init__(self, **kwargs):
        self.arg_parser = argparse.ArgumentParser(description='Good DNS Resolvers Parser')
        self.arg_parser.add_argument(
            '--version',
            action='version',
            version='{0} {1}'.format('Good DNS Resolvers Parser', '1.0.0'),
        )
        self.arg_parser.add_argument(
            '--debug',
            dest='debug',
            action='store_true',
            default=False,
            help='enable DEBUG mode',
        )
        self.arg_parser.add_argument(
            '-v', '--verbose',
            dest='verbosity',
            action='count',
            help='increase output verbosity',
        )
        self.arg_parser.add_argument(
            '--publicdns-info-url',
            dest='publicdns_info_url',
            default='https://public-dns.info/nameserver/us.json',
            help='public-dns.info NS download url',
        )
        self.arg_parser.add_argument(
            '--massdns-ns-url',
            dest='massdns_ns_url',
            default=(
                'https://raw.githubusercontent.com/blechschmidt/massdns/master/lists/resolvers.txt'
            ),
            help='MassDNS git repo raw NS download url',
        )
        self.arg_parser.add_argument(
            '--massdns',
            dest='massdns_enabled',
            action='store_true',
            default=False,
            help='include MassDNS resolvers in the output',
        )
        self.arg_parser.add_argument(
            '--reliability-threshold',
            dest='reliability_threshold',
            default=90.0,
            help='integer in range [0, 100] to filter nameservers by',
        )
        self.arg_parser.add_argument(
            '--names',
            dest='lookup_missing_names',
            action='store_true',
            default=False,
            help='perform reverse lookup for NS IPs missing hostnames',
        )
        self.arg_parser.add_argument(
            '--output-json',
            dest='output_json_path',
            default='goodresolvers.json',
            help='path to the output file',
        )
        self.arg_parser.add_argument(
            '--output',
            dest='output_path',
            default='goodresolvers.txt',
            help='path to the output file of line separated list of resolver IPs',
        )
        self.dns_cache = dns.resolver.Cache()
        self.md5_blocksize = 128

    def _get_resolver(self, **kwargs):
        return public_dns_resolver(cache=self.dns_cache, shuffle=True, **kwargs)

    def _configure_logging(self, debug_enabled, verbosity):
        formatters = {
            0: {
                'fmt': '%(message)s',
            },
            1: {
                'fmt': '[ %(levelname)8s ]  %(message)s',
            },
            2: {
                'fmt': (
                    '%(asctime)s [ %(levelname)8s ]  %(message)s'
                ),
                'datefmt': '%Y-%m-%dT%H:%M:%S+00:00',
            },
            3: {
                'fmt': (
                    '%(asctime)s [ %(levelname)8s ] '
                    '%(name)s:%(funcName)s:%(lineno)d  %(message)s'
                ),
                'datefmt': '%Y-%m-%dT%H:%M:%S+00:00',
            },
        }
        console = logging.StreamHandler()
        if debug_enabled:
            console.setLevel(logging.DEBUG)
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            console.setLevel(logging.INFO)
            logging.getLogger().setLevel(logging.INFO)
        formatter_opts = formatters.get(verbosity, formatters[0])
        if 'datefmt' in formatter_opts:
            logging.Formatter.converter = time.gmtime
        formatter = logging.Formatter(**formatter_opts)
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

    def run(self, raw_args=None):
        raw_args = raw_args if raw_args else sys.argv[1:]
        args = self.arg_parser.parse_args(raw_args)
        self._configure_logging(args.debug, args.verbosity)

        output_json_path = args.output_json_path
        existing_data = None
        if os.path.exists(output_json_path):
            with io.open(output_json_path, mode='r', encoding='utf-8') as existing_file:
                existing_raw = existing_file.read()
                existing_data = json.loads(existing_raw, object_pairs_hook=OrderedDict)
            metadata = self.get_current_metadata(existing_data.get('meta', dict()))
        else:
            metadata = self.get_current_metadata(dict())
        log.debug('current metadata:')
        log.debug(json.dumps(metadata, indent=2))
        previous_nameservers = list()
        if existing_data:
            previous_nameservers = existing_data.get('nameservers', list())

        url = args.publicdns_info_url
        metadata['publicdns_info']['url'] = url
        publicdns_info_data = self.download_publicdns_info_list(url)
        ns_publicdns_info = publicdns_info_data['nameservers']
        previous_md5 = metadata['publicdns_info']['md5']
        previous_sha512 = metadata['publicdns_info']['sha512']
        current_md5 = publicdns_info_data['md5']
        current_sha512 = publicdns_info_data['sha512']
        metadata['publicdns_info']['md5'] = current_md5
        metadata['publicdns_info']['sha512'] = current_sha512
        metadata['publicdns_info']['count'] = len(ns_publicdns_info)
        process_publicdns = (
            (previous_md5 is None or previous_md5 != current_md5)
            and (previous_sha512 is None or previous_sha512 != current_sha512)
        )
        log.debug(publicdns_info_data['md5'])
        log.debug(publicdns_info_data['sha512'])
        log.debug('{0} nameservers obtained from {1}'.format(len(ns_publicdns_info), url))
        log.info('public-dns.info data {0} processing'.format((
            'requires' if process_publicdns else 'doesn\'t require'
        )))

        url = args.massdns_ns_url
        metadata['massdns']['url'] = url
        massdns_data = self.download_massdns_list(url)
        ns_massdns = massdns_data['nameservers']
        previous_md5 = metadata['massdns']['md5']
        previous_sha512 = metadata['massdns']['sha512']
        current_md5 = massdns_data['md5']
        current_sha512 = massdns_data['sha512']
        metadata['massdns']['md5'] = current_md5
        metadata['massdns']['sha512'] = current_sha512
        metadata['massdns']['count'] = len(ns_massdns)
        process_massdns = (
            (previous_md5 is None or previous_md5 != current_md5)
            and (previous_sha512 is None or previous_sha512 != current_sha512)
        )
        log.debug(massdns_data['md5'])
        log.debug(massdns_data['sha512'])
        log.debug('{0} nameservers obtained from {1}'.format(len(ns_massdns), url))
        log.info('massdns data {0} processing'.format((
            'requires' if process_massdns else 'doesn\'t require'
        )))

        self.reliability_threshold = max(0.0, min(1.0, float(args.reliability_threshold / 100)))
        self.reliability_counts = dict()
        self.min_reliability = 1.0
        self.ns_reliable = OrderedDict()
        self.ns_unreliable = OrderedDict()
        self.processed_ips = set()
        self.unreliable_ips = set()

        sources_processed = 0
        if process_publicdns:
            self.process_publicdns_nameservers(ns_publicdns_info)
            sources_processed += 1
        else:
            for ns in previous_nameservers:
                if 'public-dns.info' in ns['sources']:
                    self.ns_reliable.setdefault(ns['ip'], ns)
        if args.massdns_enabled and process_massdns:
            self.process_massdns_nameservers(ns_massdns, args.lookup_missing_names)
            sources_processed += 1
        elif args.massdns_enabled:
            for ns in previous_nameservers:
                if 'massdns' in ns['sources']:
                    self.ns_reliable.setdefault(ns['ip'], ns)

        self.reliability_counts = OrderedDict(
            sorted(self.reliability_counts.items(), key=lambda i: i[0], reverse=True)
        )
        if self.reliability_counts or sources_processed > 0:
            log.debug(json.dumps(self.reliability_counts, indent=2))
            log.debug('{0} is the lowest reliability score'.format(self.min_reliability))
            log.debug('{0} resolvers do not have DNSSEC'.format(
                len([n for n in self.ns_reliable.values() if not n['dnssec']])
            ))
        log.info('{0} nameservers pass reliability threshold from {1}'.format(
            len(self.ns_reliable), args.publicdns_info_url
        ))

        if sources_processed > 0:
            log.info('writing JSON results to {0} ...'.format(output_json_path))
            output = OrderedDict()
            output['meta'] = metadata
            output['nameservers'] = list(self.ns_reliable.values())
            with io.open(output_json_path, mode='w', encoding='utf-8') as outputfile:
                outputfile.write(json.dumps(output, indent=2))
                outputfile.write('\n')
        else:
            log.info('no changes to write to disk')

        output_path = args.output_path
        if sources_processed > 0 or not os.path.exists(output_path):
            log.info('writing flat IP file ({0}) to disk...'.format(output_path))
            with io.open(output_path, mode='w', encoding='utf-8') as outputfile:
                for ns in self.ns_reliable.values():
                    outputfile.write(ns['ip'])
                    outputfile.write('\n')
        else:
            log.info('skipped writing flat IP file to disk')

        log.info('done.')

    def get_current_metadata(self, meta_old):
        metadata = OrderedDict()
        metadata['publicdns_info'] = OrderedDict()
        meta_old_publicdns = meta_old.get('publicdns_info', dict())
        metadata['publicdns_info']['url'] = meta_old_publicdns.get('url', None)
        metadata['publicdns_info']['count'] = meta_old_publicdns.get('count', None)
        metadata['publicdns_info']['sha512'] = meta_old_publicdns.get('sha512', None)
        metadata['publicdns_info']['md5'] = meta_old_publicdns.get('md5', None)
        metadata['massdns'] = OrderedDict()
        meta_old_massdns = meta_old.get('massdns', dict())
        metadata['massdns']['url'] = meta_old_massdns.get('url', None)
        metadata['massdns']['count'] = meta_old_massdns.get('count', None)
        metadata['massdns']['sha512'] = meta_old_massdns.get('sha512', None)
        metadata['massdns']['md5'] = meta_old_massdns.get('md5', None)
        metadata['errors'] = list()

        return metadata

    def download_publicdns_info_list(self, url):
        result = OrderedDict()
        result['md5'] = None
        result['sha512'] = None
        result['nameservers'] = list()

        response = requests.get(url)

        md5_hash = hashlib.md5()
        block_generator = itertools.islice(response.content, None, None, self.md5_blocksize)
        for content_chunk in block_generator:
            md5_hash.update(bytes(content_chunk))
        result['md5'] = md5_hash.hexdigest()
        result['sha512'] = hashlib.sha512(response.content).hexdigest()
        result['nameservers'] = response.json(object_pairs_hook=OrderedDict)
        for ns in result['nameservers']:
            ns['sources'] = ['public-dns.info']

        return result

    def download_massdns_list(self, url):
        result = OrderedDict()
        result['md5'] = None
        result['sha512'] = None
        result['nameservers'] = list()

        response = requests.get(url)

        md5_hash = hashlib.md5()
        block_generator = itertools.islice(response.content, None, None, self.md5_blocksize)
        for content_chunk in block_generator:
            md5_hash.update(bytes(content_chunk))
        result['md5'] = md5_hash.hexdigest()
        result['sha512'] = hashlib.sha512(response.content).hexdigest()
        result['nameservers'] = [
            OrderedDict([
                ('ip', line.strip()),
                ('name', None),
                ('country_id', ''),
                ('city', ''),
                ('version', ''),
                ('error', None),
                ('dnssec', None),
                ('reliability', None),
                ('checked_at', None),
                ('created_at', None),
                ('sources', ['massdns']),
            ]) for line in response.text.split('\n') if line.strip()
        ]

        return result

    def process_publicdns_nameservers(self, nameservers):
        for ns in nameservers:
            ns_ip = ns['ip']
            if ns_ip in self.processed_ips:
                continue
            self.processed_ips.add(ns_ip)

            if ns_ip in self.ns_reliable:
                for source in ns['sources']:
                    if source not in self.ns_reliable[ns_ip]['sources']:
                        self.ns_reliable[ns_ip]['sources'].append(source)
                log.warning('duplicate IP in record: {0}'.format(ns))
                continue

            reliability = ns['reliability']
            self.reliability_counts.setdefault(reliability, 0)
            self.reliability_counts[reliability] += 1
            if reliability < self.min_reliability:
                self.min_reliability = reliability
            if reliability < self.reliability_threshold:
                self.ns_unreliable[ns_ip] = ns
                self.unreliable_ips.add(ns_ip)
                continue

            if ns.get('error', None):
                log.warning('{0}'.format(json.dumps(ns, indent=2)))

            self.ns_reliable[ns_ip] = ns

    def process_massdns_nameservers(self, nameservers, lookup_missing=False):
        newly_found = 0
        require_name_lookups = list()
        for ns in nameservers:
            ns_ip = ns['ip']
            if ns_ip in self.processed_ips:
                continue
            self.processed_ips.add(ns_ip)

            if ns_ip in self.ns_reliable:
                for source in ns['sources']:
                    if source not in self.ns_reliable[ns_ip]['sources']:
                        self.ns_reliable[ns_ip]['sources'].append(source)
                continue

            newly_found += 1
            if not ns['name']:
                require_name_lookups.append(ns_ip)

            ns['created_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

            if lookup_missing:
                rname = None
                ns_host = None
                try:
                    rname = dns.reversename.from_address(ns_ip)
                    resolver = self._get_resolver()
                    try:
                        ns_host = str(resolver.query(rname, 'PTR')[0])
                        ns[ns_ip]['name'] = ns_host
                    except (dns.resolver.NoNameservers, dns.resolver.Timeout):
                        resolver = self._get_resolver()
                        ns_host = str(resolver.query(rname, 'PTR')[0])
                        ns[ns_ip]['name'] = ns_host
                except dns.resolver.NXDOMAIN:
                    pass
                except Exception as exc:
                    errmsg = '{0}: {1}'.format(exc.__class__.__name__, exc)
                    ns[ns_ip]['error'] = errmsg
                log.debug('{0} --> {1} --> {2}'.format(ns_ip, rname, ns_host))
            # TODO: check that the IP is from a country we want to use

            # TODO: implement the checks outlined here
            # https://public-dns.info/testing

            ns['checked_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            self.ns_reliable[ns_ip] = ns

        log.debug('{0} new nameservers found from massdns'.format(newly_found))


def find_good_resolvers():
    executor = FindGoodResolvers()
    executor.run()


if __name__ == '__main__':
    find_good_resolvers()
