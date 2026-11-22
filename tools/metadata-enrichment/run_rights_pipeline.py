#!/usr/bin/env python3
"""Export and normalize one network's rights, then publish an enrichment edition."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import uuid

from build_rights_enrichment import rights_fields, reference
from count_export_licenses import EXCLUDED_VOCABULARIES, is_web_url
from enrichment_package import publish, upsert_batch
from enrichment_package.store import digest
from normalize_rights import normalize_rights
from rights_export import RightsExport

LOG = logging.getLogger(__name__)


def code_provenance():
    """Include source hashes so an uncommitted checkout remains reproducible."""
    tools = Path(__file__).resolve().parent
    paths = list(tools.glob('*.py')) + list((tools / 'enrichment_package').glob('*'))
    return {str(p.relative_to(tools)): digest(p) for p in sorted(paths)
            if p.is_file() and p.suffix in ('.py', '.sql')}


def export_lgk(args, directory):
    shell = args.shell_dir.resolve()
    inputs = directory / 'inputs'
    inputs.mkdir()
    jar = inputs / 'lareferencia-shell.jar'
    mapping = inputs / 'licenses-v1.json'
    shutil.copyfile(shell / 'lareferencia-shell.jar', jar)
    shutil.copyfile(shell / 'config/exports/licenses-v1.json', mapping)
    exports = directory / 'exports'
    command = ['java', '-jar', str(jar), 'export-metadata', '--network', args.network,
               '--variant', 'original', '--format', 'jsonl', '--mapping', str(mapping),
               '--partition-by', 'network', '--compression', 'gzip', '--output', str(exports)]
    LOG.info('Exporting the current LGK for %s', args.network)
    # The working directory supplies the installation's existing configuration.
    with (directory / 'export.log').open('w') as log:
        subprocess.run(command, cwd=shell, stdout=log, stderr=subprocess.STDOUT, check=True)
    manifests = list(exports.glob('exp-*/manifest.json'))
    if len(manifests) != 1:
        raise ValueError('Expected exactly one newly generated export manifest')
    return manifests[0].parent, {'shellJar': reference(jar)}


def build_dictionary(source, destination):
    counts = Counter()
    for row, _ in source.rows():
        counts.update({v.strip() for v in row['data']['licenses']
                       if v.strip() and not EXCLUDED_VOCABULARIES.match(v.strip())
                       and (len(v.strip()) <= 120 or is_web_url(v.strip()))})
    recognized = {}
    with destination.open('w', encoding='utf-8') as output:
        for value, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
            result = normalize_rights(value)
            if result is not None:
                output.write(json.dumps(dict(result, recordCount=count), ensure_ascii=False) + '\n')
                if result['licenses']:
                    recognized[value] = result['licenses']
    LOG.info('Normalized %d distinct eligible values', len(counts))
    return recognized


def run_pipeline(args, directory):
    inputs = {}
    root = args.export_dir
    if root is None:
        root, inputs = export_lgk(args, directory)
    LOG.info('Verifying export %s', root)
    source = RightsExport(root, args.network)
    dictionary_path = directory / 'dictionary-v7.jsonl'
    dictionary = build_dictionary(source, dictionary_path)
    run = dict(network=args.network, snapshot=str(source.source['internalSnapshotId']), variant='original',
               producer='rights', type='rights-facets', schemaVersion='4', taxonomyVersion=7,
               exportId=source.manifest['exportId'], runId=directory.name, scope='network',
               inputs=dict(inputs, manifest=reference(source.root / 'manifest.json'),
                           mapping=reference(source.root / 'mapping.json'),
                           dictionary=reference(dictionary_path)),
               sourceRoot=str(source.root), code=code_provenance(),
               parts={name: source.files[name]['sha256'] for name in source.parts})
    stamp = datetime.now(timezone.utc).isoformat()

    def results():
        for row, ref in source.rows():
            yield dict(catalogId=row['catalogId'], identifier=row['identifier'],
                       metadataHash=row['metadataHash'], generatedAt=stamp, sourceRef=ref,
                       fields=rights_fields(row['data']['licenses'], dictionary))

    LOG.info('Writing item enrichments')
    count = upsert_batch(directory / 'work.sqlite', run, results())
    LOG.info('Publishing %d evaluated items', count)
    manifest = publish(directory / 'work.sqlite', directory / 'edition')
    if manifest['counts']['items'] != count:
        raise ValueError('Published item count differs from the verified export')
    return dict(network=args.network, snapshot=run['snapshot'], items=count,
                edition=str(directory / 'edition'), exportDir=str(source.root))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network', required=True)
    parser.add_argument('--output', type=Path, default=Path('/srv/metadata-enrichments'))
    parser.add_argument('--export-dir', type=Path)
    parser.add_argument('--shell-dir', type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.network):
        parser.error('Invalid network acronym')
    directory = args.output.resolve() / args.network / ('run-' + str(uuid.uuid4()))
    try:
        directory.mkdir(parents=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                            handlers=[logging.StreamHandler(), logging.FileHandler(directory / 'run.log')])
        result = run_pipeline(args, directory)
        LOG.info('COMPLETE %s', json.dumps(result))
        print(json.dumps(result))
    except (OSError, ValueError, LookupError, TypeError, sqlite3.Error, subprocess.SubprocessError):
        LOG.exception('FAILED; retain the run directory for diagnosis')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
