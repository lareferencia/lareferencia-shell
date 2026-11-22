"""Regression tests for the generic store and the rights producer."""
from pathlib import Path
import json
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from build_rights_enrichment import COPYRIGHT, L1, L2, rights_fields, license_facets
from enrichment_package import lookup, publish, upsert_batch
from enrichment_package.store import digest
from enrichments import read_returns


class PackageTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = self.root / 'work.sqlite'
        self.run = dict(producer='rights', network='BR', exportId='exp-test', runId='sample',
                        snapshot='4193', variant='original', type='rights-facets', schemaVersion='1')
        self.item = dict(catalogId='stored', identifier='oai:x', metadataHash='hash',
                         generatedAt='2026-01-01T00:00:00Z', fields={L1: [{'value':'CC_BY'}]})

    def lookup(self):
        return lookup(self.db, identifier='oai:x')['enrichments']

    def test_two_producers_publication_and_empty_update(self):
        upsert_batch(self.db, self.run, [self.item])
        ods = dict(self.run, producer='ods', type='sdg')
        fields = {'dc.subject.ods': [{'value':'ODS-03'}, {'value':'ODS-10'}, {'value':'ODS-03'}]}
        row = {k:self.item[k] for k in ('catalogId', 'identifier', 'metadataHash')}
        row.update(network='BR', exportId='exp-test', enrichment={
            'id':'ods','type':'sdg','schemaVersion':'1','runId':'sample',
            'generatedAt':self.item['generatedAt'], 'values':{'fields':fields}})
        path = self.root / 'input.jsonl'
        path.write_text(json.dumps(row))
        for _ in range(2):
            upsert_batch(self.db, ods, read_returns(path, ods))
        self.assertEqual(self.lookup()['ods']['fields']['dc.subject.ods'], fields['dc.subject.ods'][:2])
        edition = self.root / 'edition'
        manifest = publish(self.db, edition)
        stable = edition / 'enrichments.sqlite'
        self.assertEqual(manifest['files'][0]['sha256'], digest(stable))
        self.assertEqual(manifest['counts'], dict(items=1,results=2,occurrences=3))
        upsert_batch(self.db, ods, [dict(self.item, fields={'dc.subject.ods':[{'value':'ODS-03'}]})])
        upsert_batch(self.db, ods, [dict(self.item, fields={})])
        self.assertEqual(self.lookup()['ods']['fields'], {})
        self.assertEqual(self.lookup()['rights']['fields'], self.item['fields'])
        self.assertEqual(len(lookup(stable, catalog_id='stored')['enrichments']['ods']['fields']['dc.subject.ods']), 2)
        with self.assertRaisesRegex(ValueError, 'read-only'):
            upsert_batch(stable, ods, [self.item])
        self.assertEqual(digest(stable), manifest['files'][0]['sha256'])
        with self.assertRaises(FileExistsError):
            publish(self.db, edition)

    def test_bad_last_line_is_not_partially_published(self):
        row = dict(catalogId='one', identifier='oai:one', metadataHash='hash',
                   network='BR', exportId='exp-test', enrichment={
                       'id':'rights', 'type':'rights-facets', 'schemaVersion':'1', 'runId':'sample',
                       'generatedAt':'2026-11-22T01:02:03.123456789Z', 'values':{'fields':{}}})
        path = self.root / 'broken.jsonl'
        path.write_text(json.dumps(row) + '\n{}')
        upsert_batch(self.db, self.run, [self.item])
        with self.assertRaisesRegex(ValueError, 'broken.jsonl:2'):
            upsert_batch(self.db, self.run, read_returns(path, self.run))
        with self.assertRaises(LookupError):
            lookup(self.db, catalog_id='one')

    def test_conflicts_and_interrupt_roll_back_whole_batch(self):
        upsert_batch(self.db, self.run, [self.item])
        new = dict(self.item, catalogId='new')
        for conflict in [dict(self.item, metadataHash='different'), dict(self.item, identifier='different')]:
            with self.assertRaises(ValueError):
                upsert_batch(self.db, self.run, [new, conflict])
            with self.assertRaises(LookupError):
                lookup(self.db, catalog_id='new')

        def interrupted():
            yield new
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            upsert_batch(self.db, self.run, interrupted())
        with self.assertRaises(LookupError):
            lookup(self.db, catalog_id='new')
        with self.assertRaises(ValueError):
            upsert_batch(self.db, dict(self.run, snapshot='other'), [new])
        with self.assertRaises(ValueError):
            upsert_batch(self.db, dict(self.run, schemaVersion='changed'), [new])
        upsert_batch(self.db, self.run, [new])
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            self.lookup()
        with sqlite3.connect(self.db) as db:
            for column in ('catalog_id', 'identifier'):
                plan = db.execute(f'EXPLAIN QUERY PLAN SELECT id FROM items WHERE {column}=?', ('x',)).fetchone()
                self.assertIn('INDEX', plan[-1])


class RightsTest(unittest.TestCase):
    def test_all_families(self):
        cases = [('CC','BY-NC','CC_BY_NC'), ('SOFTWARE','MIT','SOFTWARE_MIT'), ('DATA','ODbL','DATA_ODBL'),
                 ('EDITORIAL','YouTube','EDITORIAL_YOUTUBE'), ('RE','InC','RE_INC'),
                 ('INSTITUTIONAL','Terms','INSTITUTIONAL'), ('OTHER-LICENSE','X','OTHER_LICENSE_X'),
                 ('PUBLIC-DOMAIN','CC0','PUBLIC_DOMAIN_CC0')]
        for family, instrument, expected in cases:
            self.assertEqual(license_facets(dict(family=family,instrument=instrument))[0], expected)

    def test_copyright_only_emits_distinct_subtypes_in_source_order(self):
        subtypes = ['NOTICE', 'ALL-RIGHTS-RESERVED', 'SOME-RIGHTS-RESERVED', 'RIGHTS-RESERVED']
        dictionary = {s: [dict(family='Copyright', instrument=s)] for s in subtypes}
        self.assertEqual(rights_fields(subtypes * 2, dictionary),
                         {COPYRIGHT: [{'value': s} for s in subtypes]})

    def test_two_institutions_on_one_item_share_one_overview_value(self):
        dictionary = {'terms': [dict(family='INSTITUTIONAL', instrument=i) for i in ('IPEA', 'ENAP')]}
        fields = rights_fields(['terms'], dictionary)
        self.assertEqual(fields[L1], [{'value': 'INSTITUTIONAL'}])
        self.assertEqual([o['value'] for o in fields[L2]], ['INSTITUTIONAL_IPEA', 'INSTITUTIONAL_ENAP'])

    def test_scopes_versions_coexistence_and_facet_counting(self):
        cc = dict(family='CC',instrument='BY-NC',version='4.0')
        dictionary = {'url':[cc], 'text':[dict(cc,scope='images'),dict(cc,version='3.0',country='BR')],
                      'copyright':[dict(family='Copyright',instrument='ALL-RIGHTS-RESERVED')]}
        fields = rights_fields(['url','url','text','copyright','pending'], dictionary)
        self.assertEqual([o['value'] for o in fields[L1]], ['CC_BY_NC'])
        self.assertEqual([o['value'] for o in fields[L2]], [
            'CC_BY_NC_4.0','CC_BY_NC_3.0_BR'])
        self.assertEqual(fields[COPYRIGHT], [{'value': 'ALL-RIGHTS-RESERVED'}])
        self.assertEqual(fields[L2][0]['details'], [{}, {'scope':'images'}])
        self.assertEqual(license_facets(dict(cc, jurisdiction='international', variant='3-clause',modifier='or-later'))[1],
                         'CC_BY_NC_4.0_INTERNATIONAL_3_CLAUSE_OR_LATER')
        self.assertEqual(rights_fields(['pending'], dictionary), {})


if __name__ == '__main__':
    unittest.main()
