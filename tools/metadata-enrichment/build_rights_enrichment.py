#!/usr/bin/env python3
"""Build rights facets from a verified original export and a v7 rights inventory."""
import argparse
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import re
import sqlite3
import uuid

from enrichment_package import upsert_batch
from enrichment_package.store import digest

L1 = 'dc.rights.license_l1'
L2 = 'dc.rights.license_l2'
COPYRIGHT = 'dc.rights.copyright'


def token(value):
    return re.sub(r'[^\w.]+', '_', value.upper()).strip('_')


def instrument_key(declaration):
    return token(declaration['family']) + '_' + token(declaration['instrument'])


def license_facets(declaration):
    family = declaration['family']
    instrument = instrument_key(declaration)
    group = token(family) if family == 'INSTITUTIONAL' else instrument
    details = (declaration.get('version'), declaration.get('jurisdiction') or declaration.get('country'),
               declaration.get('variant'), declaration.get('modifier'))
    return group, '_'.join([instrument] + [token(value) for value in details if value])


def load_dictionary(path):
    lookup = {}
    instruments = {}
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['taxonomyVersion'] != 7:
                raise ValueError('Expected v7 dictionary')
            for declaration in row['licenses']:
                key = instrument_key(declaration)
                pair = (declaration['family'], declaration['instrument'])
                if instruments.setdefault(key, pair) != pair:
                    raise ValueError(f'Instrument collision: {key}')
            if row['licenses']:
                lookup[row['value']] = row['licenses']
    return lookup


def merged_occurrence(value, declarations):
    """Keep one facet value while preserving differences between its source declarations."""
    first = declarations[0]
    common = {k: v for k, v in first.items() if all(d.get(k) == v for d in declarations)}
    occurrence = {'value': value, **common}
    if len(declarations) > 1:
        occurrence['details'] = [{k: v for k, v in d.items() if k not in common} for d in declarations]
    return occurrence


def rights_fields(values, dictionary):
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ValueError('Expected data.licenses to contain strings')
    groups, specific, notices = {}, {}, {}
    for value in values:
        for declaration in dictionary.get(value.strip(), ()):
            if declaration['family'] == 'Copyright':
                subtype = declaration['instrument']
                notices[subtype] = {'value': subtype}
                continue
            group, detail = license_facets(declaration)
            groups[group] = {'value': group}
            occurrence = {k: v for k, v in declaration.items() if v is not None}
            variants = specific.setdefault(detail, [])
            if occurrence not in variants:
                variants.append(occurrence)
    fields = {}
    if groups:
        fields[L1] = list(groups.values())
        fields[L2] = [merged_occurrence(key, variants) for key, variants in specific.items()]
    if notices:
        fields[COPYRIGHT] = list(notices.values())
    return fields


def records(root, parts, run, dictionary, stamp):
    for name, checksum in parts.items():
        path = root / name
        if digest(path) != checksum:
            raise ValueError(f'Checksum mismatch for {name}')
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            for number, line in enumerate(stream, 1):
                row = json.loads(line)
                if row['network'] != run['network']:
                    raise ValueError(f'Network mismatch in {name}:{number}')
                yield dict(catalogId=row['catalogId'], identifier=row['identifier'], metadataHash=row['metadataHash'],
                           generatedAt=stamp, sourceRef=f'{name}:{number}',
                           fields=rights_fields(row['data']['licenses'], dictionary))


def prepare(args):
    manifest = json.loads(args.manifest.read_text())
    network = args.network
    source, = [s for s in manifest['sources'] if s['network'] == network]
    if manifest['options']['variant'] != 'original' or manifest['options']['format'] != 'jsonl':
        raise ValueError('Expected an original JSONL export')
    refs = {'manifest': reference(args.manifest), 'dictionary': reference(args.dictionary)}
    if manifest['status'] == 'COMPLETE':
        checks = {entry['path']: entry['sha256'] for entry in manifest['files']}
    else:
        # The consolidated campaign retained source closure logs from a suspended export.
        if manifest['status'] != 'RUNNING' or not args.closures or not args.checksums:
            raise ValueError('Recovered parts require a source closure and trusted checksums')
        pattern = (re.escape(f"Export {manifest['exportId']}: source {source['snapshotRef']} ({network}): finished: ")
                   + r'attempted (\d+), exported \d+, filtered \d+, errors 0$')
        if not re.search(pattern, args.closures.read_text(), re.MULTILINE):
            raise ValueError('Missing successful source closure for this export')
        refs.update(closure=reference(args.closures), checksums=reference(args.checksums))
        checks = {}
        for line in args.checksums.read_text().splitlines():
            checksum, name = line.split(maxsplit=1)
            checks[name] = 'sha256:' + checksum
    mapping = args.root / 'mapping.json'
    if checks.get('mapping.json') != digest(mapping) or 'licenses' not in json.loads(mapping.read_text())['fields']:
        raise ValueError('Export mapping mismatch')
    refs['mapping'] = reference(mapping)
    if not re.fullmatch(r'[\w-]+', network):
        raise ValueError('Invalid network directory')
    names = sorted(name for name in checks if re.fullmatch(re.escape(network) + r'/part-\d+\.jsonl\.gz', name))
    if args.part:
        names = [f'{network}/{args.part}'] if f'{network}/{args.part}' in names else []
    elif manifest['status'] != 'COMPLETE':
        raise ValueError('Select a verified part explicitly for a recovered sample')
    if not names:
        raise ValueError('No verified input parts selected')
    parts = {name: checks[name] for name in names}
    return dict(network=network, snapshot=str(source['internalSnapshotId']), variant='original',
                producer='rights', type='rights-facets', schemaVersion='4', taxonomyVersion=7,
                runId=str(uuid.uuid4()), exportId=manifest['exportId'], inputs=refs, parts=parts,
                scope='sample' if args.part else 'network', sourceRoot=str(args.root.resolve()))


def reference(path):
    return dict(path=str(path.resolve()), sha256=digest(path))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('database', 'root', 'manifest', 'dictionary'):
        p.add_argument(name, type=Path)
    p.add_argument('--network', required=True)
    p.add_argument('--part', help='Load only this named part as a sample')
    p.add_argument('--closures', type=Path)
    p.add_argument('--checksums', type=Path)
    args = p.parse_args()
    try:
        run = prepare(args)
        dictionary = load_dictionary(args.dictionary)
        stamp = datetime.now(timezone.utc).isoformat()
        rows = records(args.root, run['parts'], run, dictionary, stamp)
        count = upsert_batch(args.database, run, rows)
        print(json.dumps(dict(runId=run['runId'], items=count, scope=run['scope'])))
    except (ValueError, LookupError, TypeError, OSError, sqlite3.Error) as error:
        p.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
