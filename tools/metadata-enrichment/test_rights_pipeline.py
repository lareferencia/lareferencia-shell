"""Exercise the complete Python pipeline with real SQLite export fixtures."""
from argparse import Namespace
import gzip
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from enrichment_package import lookup
from enrichment_package.store import digest
from run_rights_pipeline import main, run_pipeline


class PipelineTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.export = self.root / 'export'
        (self.export / 'PY').mkdir(parents=True)
        profile = Path(__file__).resolve().parents[2] / 'config/exports/licenses-v1.json'
        (self.export / 'mapping.json').write_bytes(profile.read_bytes())
        self.rows = [
            dict(network='PY',catalogId='one',identifier='oai:one',metadataHash='abc',data={
                'licenses':['https://creativecommons.org/licenses/by/4.0/',
                            'http://creativecommons.org/licenses/by/4.0/',
                            'Copyright (c) 2026 Example']}),
            dict(network='PY',catalogId='empty',identifier='oai:empty',metadataHash='def',data={'licenses':[]})]
        self.write_export(self.rows)

    def write_export(self, rows):
        name = 'PY/part-000001.jsonl.gz'
        with gzip.open(self.export / name, 'wt') as stream:
            for row in rows:
                stream.write(json.dumps(row) + '\n')
        db = sqlite3.connect(self.export / 'records.sqlite')
        db.execute('DROP TABLE IF EXISTS records')
        db.execute('CREATE TABLE records(network,catalog_id,identifier,metadata_hash,file,position,status)')
        for number, row in enumerate(rows, 1):
            db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?)',
                       ('PY',row['catalogId'],row['identifier'],row['metadataHash'],name,number,'EXPORTED'))
        db.commit()
        db.close()
        files = [dict(path=n,bytes=(self.export/n).stat().st_size,sha256=digest(self.export/n))
                 for n in (name,'records.sqlite','mapping.json')]
        self.manifest = dict(status='COMPLETE',exportId='exp-test',options=dict(variant='original',format='jsonl'),
                             sources=[dict(network='PY',internalSnapshotId=4195)], files=files)
        self.save_manifest()

    def save_manifest(self):
        (self.export/'manifest.json').write_text(json.dumps(self.manifest))

    def execute(self, name):
        directory = self.root / name
        directory.mkdir()
        return run_pipeline(Namespace(network='PY',export_dir=self.export),directory)

    def test_cli_default_shell_is_its_own_checkout(self):
        arguments = ['run_rights_pipeline.py', '--network', 'PY', '--output', str(self.root / 'output')]
        with patch('sys.argv', arguments), patch('run_rights_pipeline.run_pipeline', return_value={}) as run:
            with patch('run_rights_pipeline.logging.basicConfig'), patch('builtins.print'):
                main()
        args, _ = run.call_args.args
        self.assertEqual(args.shell_dir, Path(__file__).resolve().parents[2])

    def test_complete_and_repeated_export(self):
        for name in ('a','b'):
            result = self.execute(name)
            db = Path(result['edition'])/'enrichments.sqlite'
            item = lookup(db,catalog_id='one')
            fields = item['enrichments']['rights']['fields']
            self.assertEqual(fields['dc.rights.license_l1'],[{'value':'CC_BY'}])
            self.assertEqual(len(fields['dc.rights.license_l2']),1)
            self.assertEqual(fields['dc.rights.copyright'],[{'value':'NOTICE'}])
            self.assertEqual(lookup(db,identifier='oai:empty')['enrichments']['rights']['fields'],{})
            self.assertEqual(result['items'],2)

    def test_empty_export(self):
        self.write_export([])
        self.assertEqual(self.execute('empty')['items'],0)

    def test_identity_mismatch_rolls_back(self):
        db = sqlite3.connect(self.export / 'records.sqlite')
        db.execute("UPDATE records SET metadata_hash='wrong' WHERE catalog_id='one'")
        db.commit()
        db.close()
        for entry in self.manifest['files']:
            if entry['path'] == 'records.sqlite':
                entry['sha256'] = digest(self.export / 'records.sqlite')
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.execute('mismatch')
        self.assertFalse((self.root / 'mismatch/edition').exists())

    def test_failed_export_or_corrupt_file_never_publishes(self):
        self.manifest['status']='PARTIAL'
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.execute('partial')
        self.manifest['status']='COMPLETE'
        self.save_manifest()
        (self.export/'PY/part-000001.jsonl.gz').write_bytes(b'broken')
        with self.assertRaises(ValueError):
            self.execute('corrupt')
        self.assertFalse((self.root/'corrupt/edition').exists())


if __name__ == '__main__':
    unittest.main()
