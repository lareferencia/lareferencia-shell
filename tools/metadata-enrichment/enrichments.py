#!/usr/bin/env python3
"""Ingest v2 enrichment returns, query an item or publish a stable edition."""
import argparse
import gzip
import json
from pathlib import Path
import sqlite3

from enrichment_package import lookup, publish, upsert_batch


def read_returns(path, run):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        for number, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
                required = {'exportId', 'network', 'catalogId', 'identifier', 'metadataHash', 'enrichment'}
                if not isinstance(row, dict) or set(row) != required:
                    raise ValueError('Invalid v2 envelope')
                entry = row['enrichment']
                if not isinstance(entry, dict) or set(entry) != {'id','type','schemaVersion','runId','generatedAt','values'}:
                    raise ValueError('Invalid v2 enrichment')
                if any(row[k] != run[k] for k in ('exportId', 'network')) or entry['id'] != run['producer']:
                    raise ValueError('Source or producer mismatch')
                if any(entry[k] != run[k] for k in ('type', 'schemaVersion', 'runId')):
                    raise ValueError('Run mismatch')
                yield {**row, 'fields': entry['values']['fields'], 'generatedAt': entry['generatedAt'],
                       'sourceRef': f'{path.name}:{number}'}
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError(f'{path}:{number}: {error}') from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    ingest = commands.add_parser('ingest')
    ingest.add_argument('database', type=Path)
    ingest.add_argument('jsonl', type=Path)
    ingest.add_argument('--run', type=Path, required=True)
    query = commands.add_parser('lookup')
    query.add_argument('database', type=Path)
    keys = query.add_mutually_exclusive_group(required=True)
    keys.add_argument('--catalog-id')
    keys.add_argument('--identifier')
    edition = commands.add_parser('publish')
    edition.add_argument('database', type=Path)
    edition.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'ingest':
            run = json.loads(args.run.read_text())
            result = {'evaluated': upsert_batch(args.database, run, read_returns(args.jsonl, run))}
        elif args.command == 'lookup':
            result = lookup(args.database, catalog_id=args.catalog_id, identifier=args.identifier)
        else:
            result = publish(args.database, args.destination)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, LookupError, TypeError, sqlite3.Error) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
