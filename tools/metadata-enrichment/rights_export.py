"""Read one network from a complete, verified original metadata export."""
from contextlib import closing
import gzip
import json
import logging
from pathlib import Path
import sqlite3

from enrichment_package.store import digest, readonly


class RightsExport:
    """Keep the export catalog open read-only while streaming its record parts."""

    def __init__(self, root, network):
        self.root = Path(root).resolve()
        self.network = network
        self.manifest = json.loads((self.root / 'manifest.json').read_text())
        manifest = self.manifest
        if (manifest['status'] != 'COMPLETE' or manifest['options']['variant'] != 'original'
                or manifest['options']['format'] != 'jsonl'):
            raise ValueError('Expected a COMPLETE original JSONL export')
        self.source, = [s for s in manifest['sources'] if s['network'] == network]
        self.files = {}
        for entry in manifest['files']:
            name = Path(entry['path'])
            if name.is_absolute() or '..' in name.parts:
                raise ValueError(f'Unsafe export path: {name}')
            self.files[entry['path']] = entry
        for name in ('mapping.json', 'records.sqlite'):
            self.verify(name)
        mapping = json.loads((self.root / 'mapping.json').read_text())
        if (mapping.get('name') != 'licenses' or mapping.get('version') != '1.1'
                or mapping['fields']['licenses']['select'] != 'dc.rights.*'):
            raise ValueError('Expected the licenses 1.1 extraction profile')
        self.parts = sorted(name for name in self.files
                            if Path(name).parent.as_posix() == network
                            and name.endswith(('.jsonl', '.jsonl.gz')))

    def verify(self, name):
        entry = self.files[name]
        path = self.root / name
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError(f'Checksum or size mismatch: {name}')

    def rows(self):
        """Reconcile every exported identity with its catalog entry, including empty exports."""
        with closing(readonly(self.root / 'records.sqlite')) as catalog:
            expected, = catalog.execute(
                "SELECT count(*) FROM records WHERE network=? AND status='EXPORTED'", (self.network,)).fetchone()
            seen = 0
            for name in self.parts:
                logging.getLogger(__name__).info("Reading verified part %s", name)
                self.verify(name)
                opener = gzip.open if name.endswith('.gz') else open
                with opener(self.root / name, 'rt', encoding='utf-8') as stream:
                    for line_number, line in enumerate(stream, 1):
                        row = json.loads(line)
                        identity = catalog.execute('''SELECT identifier,metadata_hash,file,position FROM records
                            WHERE network=? AND catalog_id=? AND status='EXPORTED' ''',
                                                   (self.network, row['catalogId'])).fetchone()
                        if (row['network'] != self.network or identity !=
                                (row['identifier'], row['metadataHash'], name, line_number)):
                            raise ValueError(f'Export identity or locator mismatch: {name}:{line_number}')
                        values = row['data']['licenses']
                        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                            raise ValueError(f'Expected string licenses: {name}:{line_number}')
                        seen += 1
                        yield row, f'{name}:{line_number}'
            if seen != expected:
                raise ValueError(f'Export count mismatch: read {seen}, expected {expected}')
