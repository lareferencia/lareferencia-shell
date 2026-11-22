"""SQLite storage shared by all enrichment producers."""
import hashlib
import json
import os
from contextlib import closing
from datetime import datetime
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return 'sha256:' + h.hexdigest()


def string(obj, key):
    value = obj[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Expected nonempty string for {key}')
    return value


def timestamp(value):
    match = re.fullmatch(r'(\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2})(?:\.\d+)?([Zz]|[+-]\d{2}:\d{2})', value)
    if not match:
        raise ValueError('Expected an RFC 3339 timestamp with timezone')
    # Validate the calendar date without losing the producer's subsecond precision.
    zone = match[2] if match[2].upper() != 'Z' else '+00:00'
    datetime.fromisoformat(match[1] + zone)
    return value


def readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def scope(db):
    row = db.execute('SELECT version, network, snapshot, variant FROM package').fetchone()
    if not row or row[0] != 1:
        raise ValueError('Unsupported or uninitialized enrichment package')
    return dict(zip(('formatVersion', 'network', 'snapshot', 'variant'), row))


def iter_occurrences(fields):
    if not isinstance(fields, dict):
        raise ValueError('Expected a fields object')
    for target, entries in fields.items():
        if not re.fullmatch(r'[\w-]+(?:\.[\w-]+)+', target) or not isinstance(entries, list):
            raise ValueError(f'Invalid metadata field: {target}')
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get('value'), str):
                raise ValueError(f'{target} requires occurrences with textual value')
            content = canonical(entry)
            if content not in seen:
                seen.add(content)
                yield target, content


def write_item(db, run_id, run, item):
    for key in ('network', 'exportId', 'variant', 'snapshot'):
        if key in item and item[key] != run[key]:
            raise ValueError(f'Input {key} differs from run provenance')
    catalog, identifier, metadata_hash = (string(item, k) for k in ('catalogId', 'identifier', 'metadataHash'))
    row = db.execute('SELECT id, identifier, metadata_hash FROM items WHERE catalog_id=?', (catalog,)).fetchone()
    if row is None:
        item_id = db.execute('INSERT INTO items(catalog_id,identifier,metadata_hash) VALUES(?,?,?)',
                             (catalog, identifier, metadata_hash)).lastrowid
    elif row[1:] == (identifier, metadata_hash):
        item_id = row[0]
    else:
        raise ValueError(f'Identity or metadata hash conflict for {catalog}')

    # Keep empty results: absence of a producer and a completed empty evaluation differ.
    db.execute('''INSERT INTO results(item,producer,run,generated_at,source_ref) VALUES(?,?,?,?,?)
                  ON CONFLICT(item,producer) DO UPDATE SET run=excluded.run,
                  generated_at=excluded.generated_at, source_ref=excluded.source_ref''',
               (item_id, run['producer'], run_id, timestamp(string(item, 'generatedAt')), item.get('sourceRef')))
    result, = db.execute('SELECT id FROM results WHERE item=? AND producer=?', (item_id, run['producer'])).fetchone()
    db.execute('DELETE FROM result_occurrences WHERE result=?', (result,))
    for position, pair in enumerate(iter_occurrences(item['fields'])):
        db.execute('INSERT OR IGNORE INTO occurrences(target,content) VALUES(?,?)', pair)
        db.execute('''INSERT INTO result_occurrences SELECT ?,?,id FROM occurrences
                      WHERE target=? AND content=?''', (result, position, *pair))


def upsert_batch(path, run, items):
    """Commit an iterable atomically, including validation at the end of its stream."""
    network, snapshot, variant, producer, run_key = (
        string(run, k) for k in ('network', 'snapshot', 'variant', 'producer', 'runId'))
    if variant not in ('original', 'processed') or not string(run, 'exportId').startswith('exp-'):
        raise ValueError('Invalid input variant or export ID')
    for key in ('type', 'schemaVersion'):
        string(run, key)
    metadata = canonical(run)
    with closing(sqlite3.connect(path, timeout=30)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        if db.execute('PRAGMA user_version').fetchone()[0] == 1:
            raise ValueError('Published editions are read-only')
        db.executescript(Path(__file__).with_name('schema.sql').read_text())
        with db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT OR IGNORE INTO package VALUES(1,1,?,?,?)', (network, snapshot, variant))
            identity = scope(db)
            if any(run[k] != identity[k] for k in ('network', 'snapshot', 'variant')):
                raise ValueError('Package scope mismatch')
            db.execute('INSERT OR IGNORE INTO runs(producer,run_key,metadata) VALUES(?,?,?)',
                       (producer, run_key, metadata))
            run_id, existing = db.execute('SELECT id,metadata FROM runs WHERE producer=? AND run_key=?',
                                          (producer, run_key)).fetchone()
            if existing != metadata:
                raise ValueError('Run provenance changed; assign a new runId')
            count = 0
            for item in items:
                write_item(db, run_id, run, item)
                count += 1
            return count


def lookup(path, *, catalog_id=None, identifier=None):
    if (catalog_id is None) == (identifier is None):
        raise ValueError('Specify exactly one item identifier')
    column, key = ('catalog_id', catalog_id) if catalog_id is not None else ('identifier', identifier)
    with closing(readonly(path)) as db:
        db.execute('BEGIN')
        info = scope(db)
        rows = db.execute(f'SELECT id,catalog_id,identifier,metadata_hash FROM items WHERE {column}=? LIMIT 2',
                          (key,)).fetchall()
        if not rows:
            raise LookupError(f'Unknown {column}: {key}')
        if len(rows) > 1:
            raise ValueError(f'Ambiguous {column}: {key}')
        item_id, catalog, oai, metadata_hash = rows[0]
        producers = {}
        for name, run_key, stamp, ref, target, content in db.execute('''
            SELECT r.producer,u.run_key,r.generated_at,r.source_ref,o.target,o.content FROM results r
            JOIN runs u ON u.id=r.run LEFT JOIN result_occurrences l ON l.result=r.id
            LEFT JOIN occurrences o ON o.id=l.occurrence WHERE r.item=? ORDER BY r.producer,l.position''', (item_id,)):
            if name not in producers:
                producers[name] = dict(runId=run_key, generatedAt=stamp, fields={})
                if ref is not None:
                    producers[name]['sourceRef'] = ref
            if target:
                producers[name]['fields'].setdefault(target, []).append(json.loads(content))
        return dict(**info, catalogId=catalog, identifier=oai, metadataHash=metadata_hash, enrichments=producers)


def publish(path, destination):
    """Verify a consistent, standalone snapshot before making its directory visible."""
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(dir=destination.parent))
    try:
        output = temp / 'enrichments.sqlite'
        with closing(readonly(path)) as source, closing(sqlite3.connect(output)) as db:
            source.backup(db)
            # Seal the edition, including when a caller accidentally opens it as a working database.
            db.execute('PRAGMA user_version=1')
            if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)] or db.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('SQLite integrity check failed')
            counts = {k: db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for k, table in
                      [('items', 'items'), ('results', 'results'), ('occurrences', 'result_occurrences')]}
            represented = db.execute('SELECT count(DISTINCT item) FROM results').fetchone()[0]
            if counts['items'] != represented:
                raise ValueError('Some indexed items have no producer result')
            runs = [json.loads(r[0]) for r in db.execute('SELECT metadata FROM runs ORDER BY producer,run_key')]
            manifest = dict(**scope(db), counts=counts, runs=runs)
        manifest['files'] = [dict(path=output.name, bytes=output.stat().st_size, sha256=digest(output))]
        (temp / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.rename(temp, destination)
        return manifest
    finally:
        if temp.exists():
            shutil.rmtree(temp)
