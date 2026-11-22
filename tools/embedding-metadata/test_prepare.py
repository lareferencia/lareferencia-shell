import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from lareferencia_embedding_metadata import prepare as p


class PackageTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root, self.output, self.models = base/'exp-test', base/'result', base/'models'
        self.root.mkdir()
        self.models.mkdir()
        for name in ('lid.176.ftz', 'role.bin'):
            (self.models/name).write_bytes(b'test')
        self.profile = json.loads((Path(__file__).resolve().parents[2] / 'config/exports/bibliographic-roles-v1.json').read_bytes())
        (self.root/'mapping.json').write_text(p.compact(self.profile))
        (self.root/'errors.jsonl').touch()
        self.part = 'data/part-000001.jsonl'
        (self.root/'data').mkdir()
        self.rows = []
        for cc in ('AR', 'UY'):
            data = {key: [] for key in p.INPUT_FIELDS}
            data.update(titles=[{'value': 'Sol'}], descriptions=[{'value': 'Breve.'}],
                        keywords=[{'value':'Cielo'}])
            self.rows.append(dict(network=cc, catalogId='A', identifier='id', metadataHash='hash', data=data))
        with sqlite3.connect(self.root/'records.sqlite') as con:
            con.execute('CREATE TABLE records (export_id, identifier, metadata_hash, snapshot_ref, file, position, network, catalog_id, status)')
            for i, row in enumerate(self.rows, 1):
                con.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?)',
                            ('exp-test','id','hash',row['network'],self.part,i,row['network'],'A','EXPORTED'))
        self.dump()
        self.fake = p.postprocess.Annotator.__new__(p.postprocess.Annotator)
        self.fake.detect_role = lambda _: 'uncertain'
        self.fake.detect_language = lambda _: ('und', None)

    def dump(self):
        (self.root/self.part).write_text(''.join(p.compact(row)+'\n' for row in self.rows))
        path = self.root/'manifest.json'
        canonical = json.dumps(self.profile, sort_keys=True, separators=(',',':'), ensure_ascii=False)
        fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
        manifest = dict(contractVersion=2, exportId='exp-test', status='COMPLETE', options={'format':'jsonl','variant':'original'},
                        counts={'exported':len(self.rows)}, mappingHash='sha256:'+fingerprint,
                        sources=[{'network':cc, 'snapshotRef':cc} for cc in ('AR','UY')])
        manifest['files'] = [dict(path=str(f.relative_to(self.root)),bytes=f.stat().st_size,sha256=p.postprocess.sha(f))
                             for f in self.root.rglob('*') if f.is_file() and f!=path]
        path.write_text(p.compact(manifest))

    def execute(self, **options):
        with patch.object(p.postprocess, 'Annotator', return_value=self.fake):
            return p.prepare(self.root,self.output,self.models, **options)

    def test_partial_then_retry_and_locators(self):
        self.rows[0]['data']['titles'] = None
        self.dump()
        status, dest = self.execute()
        self.assertEqual(status,'PARTIAL')
        with sqlite3.connect(dest/'records.sqlite') as con:
            rows = list(con.execute('SELECT network,position,status FROM records ORDER BY network'))
            self.assertEqual(rows,[('AR',None,'ERROR'),('UY',1,'ANNOTATED')])
        with gzip.open(dest/(self.part+'.gz'),'rt') as f:
            data = json.loads(f.readline())['data']
        self.assertEqual(data['abstracts'],[dict(value='Breve.',language='und',selection='uncertain_fallback')])
        self.assertEqual(data['keywords'],[{'value':'Cielo'}])
        self.assertEqual(json.loads((dest/'errors.jsonl').read_text())['network'],'AR')
        self.rows[0]['data']['titles'] = []
        self.dump()
        status, second = self.execute()
        self.assertEqual(status,'COMPLETE')
        self.assertNotEqual(dest,second)
        self.assertEqual(json.loads((second/'manifest.json').read_text())['countsByNetwork']['AR']['title.missing'],1)

    def test_new_annotated_keywords_are_kept_out_of_consumer_texts(self):
        from examples.build_inputs import build_inputs

        self.rows = self.rows[:1]
        with sqlite3.connect(self.root/'records.sqlite') as con:
            con.execute("DELETE FROM records WHERE network='UY'")
        self.rows[0]['data'].update(titles=[{'value':'Heridas de mano'}, {'value':'Wounds of hand'}],
                                    keywords=[{'value':s} for s in ('mano','hand','heridas','traumatisms')])
        self.fake.detect_language = lambda s: {'Heridas de mano':('es','es'),
                                               'Wounds of hand':('en','en')}.get(s,('und',None))
        self.dump()
        _, dest = self.execute()
        inputs = list(build_inputs(dest, classified_only=True))
        self.assertEqual([(r['language'],r['text']) for r in inputs],
                         [('es','Heridas de mano'),('en','Wounds of hand')])
        self.assertEqual(inputs[0]['fields'], [('titles',0)])
        totals = json.loads((dest/'manifest.json').read_bytes())['counts']
        self.assertEqual(totals['keywordOccurrences'], 4)
        self.assertNotIn('keywordsUndetermined', totals)

    def test_corrupt_input_or_index_never_publishes(self):
        (self.root/self.part).write_text('')
        with self.assertRaisesRegex(ValueError,'inventory'):
            self.execute()
        self.rows[0]['metadataHash'] = 'wrong'
        self.dump()
        with self.assertRaisesRegex(ValueError,'Parent index mismatch'):
            self.execute()
        self.assertEqual(list(self.output.glob('*')),[])

    def test_empty_export_and_partial_parent(self):
        self.rows.clear()
        with sqlite3.connect(self.root/'records.sqlite') as con:
            con.execute('DELETE FROM records')
        self.dump()
        status,dest = self.execute()
        self.assertEqual(status,'COMPLETE')
        self.assertEqual(json.loads((dest/'manifest.json').read_text())['counts']['annotated'],0)
        path = self.root/'manifest.json'
        m = json.loads(path.read_text())
        m['status']='PARTIAL'
        path.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'COMPLETE'):
            self.execute()

    def test_combined_order_and_opt_in_provenance(self):
        first, second = self.rows
        first['data'].update(
            titles=[{'value': 'Un título'}, {'value': 'An English title'}, {'value': 'Another English title'}],
            descriptions=[{'value': 'Un resumen. Financiado por alguien.'},
                          {'value': 'A summary. A tradução. CC BY.'},
                          {'value': 'Otro resumen.'}, {'value': 'A doubtful note.'}],
            keywords=[{'value': 'tema', 'language': 'es'}, {'value': ' '}, {'value': 'policy'}],
        )
        second['data'].update(descriptions=[{'value': 'Pequeño.'}, {'value': 'Longer uncertain description.'}])
        self.dump()

        def language(value):
            self.assertNotIn(value, {'tema', 'policy'})
            return ('en', 'en') if value.startswith(('An', 'A summary')) else ('es', 'es')

        self.fake.detect_language = language
        self.fake.detect_role = lambda s: 'abstract' if 'resumen' in s or 'summary' in s else 'uncertain'
        status, minimal = self.execute(combine=True)
        self.assertEqual(status, 'COMPLETE')
        _, audited = self.execute(combine=True, include_provenance=True)
        part = self.part + '.gz'
        rows = list(p.postprocess.read_rows(minimal / part))
        self.assertEqual(rows, list(p.postprocess.read_rows(audited / part)))
        self.assertEqual(rows[0], {
            'network': 'AR', 'catalogId': 'A',
            'text': 'title: An English title\n\nAnother English title\n\nUn título | text: '
                    'A summary. A tradução. CC BY.\n\nUn resumen. Financiado por alguien.\n\n'
                    'Otro resumen.\n\ntema, policy',
        })
        self.assertEqual(rows[1]['text'], 'title: Sol | text: Longer uncertain description.\n\nCielo')
        audit = list(p.postprocess.read_rows(audited / p.PROVENANCE))
        self.assertEqual(audit[0]['origins'], {
            'titles': [1, 2, 0], 'keywords': [0, 2],
            'descriptions': [{'index': index, 'selection': 'classified'} for index in [1, 0, 2]],
        })
        self.assertEqual(audit[1]['origins']['descriptions'], [{'index': 1, 'selection': 'uncertain_fallback'}])
        self.assertEqual(audit[1]['sourceLine'], 2)
        manifest = json.loads((minimal / 'manifest.json').read_bytes())
        self.assertNotIn('parent', manifest)
        self.assertNotIn('processor', manifest)
        self.assertFalse((minimal / p.PROVENANCE).exists())
        self.assertEqual(manifest['counts']['emitted'], 2)

    def test_combined_title_fallback_and_missing_title(self):
        self.fake.detect_role = lambda _: 'non_abstract'
        self.rows[1]['data']['titles'] = [{'value': '  '}]
        self.dump()
        status, dest = self.execute(combine=True)
        self.assertEqual(status, 'COMPLETE')
        rows = list(p.postprocess.read_rows(dest / (self.part + '.gz')))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['text'], 'title: Sol | text: Sol\n\nCielo')
        manifest = json.loads((dest / 'manifest.json').read_bytes())
        self.assertEqual(manifest['counts']['omittedMissingTitle'], 1)
