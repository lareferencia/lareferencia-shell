# Metadata enrichment packages

A package contains results for one network, snapshot and input variant. Independent producers can update a working SQLite database in successive transactions. Publishing creates a standalone edition containing `enrichments.sqlite` and `manifest.json`. Python 3.9 or newer and the standard library are sufficient. Run commands from the shell checkout root.

## Run the rights pipeline on the harvester server

The command exports the current LGK, builds a dictionary for that cut using taxonomy v7, generates item fields, verifies the results and publishes an edition.

```sh
python3 tools/metadata-enrichment/run_rights_pipeline.py --network PY
```

The default shell directory is the root of this shell checkout. Override it with `--shell-dir /path/to/lareferencia-shell`. Java runs with that directory as its working directory to use the installation's configuration. Each fresh export uses a private copy of the executable JAR and extraction profile. Keep the source checkout stable throughout a run.

The default output root is `/srv/metadata-enrichments`. The operator must have write access. Override it with `--output /path/to/output`. Every invocation creates a new `<network>/run-<uuid>/` directory containing:

| Artifact | Purpose |
| --- | --- |
| `run.log` | Timestamped progress and errors |
| `inputs/`, `export.log`, `exports/exp-*/` | Copied JAR and mapping, Java output and original export for fresh LGK runs |
| `dictionary-v7.jsonl` | Distinct eligible source values, item frequencies and normalization results |
| `work.sqlite` | Working database |
| `edition/enrichments.sqlite`, `edition/manifest.json` | Published results and provenance |

A completed export can be processed again without another LGK export:

```sh
python3 tools/metadata-enrichment/run_rights_pipeline.py --network PY \
  --export-dir /srv/metadata-enrichments/PY/run-UUID/exports/exp-UUID
```

The input must be a COMPLETE original JSONL export with the licenses 1.1 profile and its original `records.sqlite`. Checksums, sizes, identities, metadata hashes and line locators are checked. A multi-network package is restricted to the selected network. A valid empty export publishes zero evaluated items.

The dictionary retains the inventory filters: omit empty strings, COAR and info:eu-repo prefixes, and text longer than 120 Unicode code points. Complete HTTP(S) URLs without whitespace are exempt from that inventory length limit. The export profile already imposes its own 300-code-point limit. Normalization runs once per distinct eligible literal, including previously unseen values. The second pass associates confirmed dictionary results with individual exported items.

Run disconnected from SSH using the server's existing process tools. For example:

```sh
nohup python3 tools/metadata-enrichment/run_rights_pipeline.py --network PY \
  > /srv/metadata-enrichments/py-launch.log 2>&1 < /dev/null &
tail -f /srv/metadata-enrichments/py-launch.log
```

A failure exits nonzero and leaves diagnostics in the run directory. A successful export can be reused with `--export-dir` after a later-stage failure. Published editions use new directories. The manifest records the source export, snapshot, checksums, source-code hashes, dictionary and producer execution. Retain the referenced export and dictionary for evidence reconstruction.

## Rights fields

The producer uses confirmed declarations from the v7 dictionary. Facet schema 4 emits:

| Field | Value construction | Examples |
| --- | --- | --- |
| `dc.rights.license_l1` | Family and instrument, grouping institutional terms | `CC_BY_NC`, `RE_INC`, `INSTITUTIONAL` |
| `dc.rights.license_l2` | L1 plus institution when applicable, known version, jurisdiction or declared country, variant and modifier | `CC_BY_NC_4.0_BR`, `INSTITUTIONAL_IPEA`, `RE_INC_1.0` |
| `dc.rights.copyright` | Confirmed notice subtype | `NOTICE`, `ALL-RIGHTS-RESERVED`, `SOME-RIGHTS-RESERVED`, `RIGHTS-RESERVED` |

Each value occurs once per item and field. L2 preserves canonical declaration attributes, including scope. Differences between declarations sharing a facet value are retained in `details`. Count distinct items per field and value. A network's country never supplies missing jurisdiction. L2 repeats L1 when details are absent. An item containing a license and copyright receives both license fields and the copyright field. An item with only copyright receives that field alone.

The lower-level `build_rights_enrichment.py` command remains available for explicit dictionary inputs and historical recovered samples. See its `--help` for `--part`, `--closures` and `--checksums`.

## Add other producers

The Python API is `upsert_batch(database, run, items)` from `enrichment_package`, with `tools/metadata-enrichment/` on the module path. Each item supplies `catalogId`, `identifier`, `metadataHash`, `generatedAt` and `fields`, optionally `sourceRef`. Each occurrence has a textual `value` and optional JSON attributes.

External producers can use the [v2 enrichment return](https://github.com/lareferencia/lareferencia-platform/blob/main/docs/METADATA_EXCHANGE_FORMAT.md#8-contrato-para-devolver-enriquecimientos). A run descriptor might contain:

```json
{"network":"BR","snapshot":"4193","variant":"original","exportId":"exp-example","producer":"ods","runId":"ods-001","type":"classification","schemaVersion":"1","model":"ods-example-1"}
```

A matching return line could contain:

```json
{"exportId":"exp-example","network":"BR","catalogId":"item-001","identifier":"oai:example:1","metadataHash":"ABC123","enrichment":{"id":"ods","type":"classification","schemaVersion":"1","runId":"ods-001","generatedAt":"2026-11-22T09:00:00Z","values":{"fields":{"dc.subject.ods":[{"value":"ODS-03"},{"value":"ODS-10"}]}}}}
```

```sh
python3 tools/metadata-enrichment/enrichments.py ingest work.sqlite ods.jsonl --run ods-run.json
python3 tools/metadata-enrichment/enrichments.py publish work.sqlite edition-001
python3 tools/metadata-enrichment/enrichments.py lookup edition-001/enrichments.sqlite --catalog-id item-001
python3 tools/metadata-enrichment/enrichments.py lookup edition-001/enrichments.sqlite --identifier oai:example:1
```

Ingestion accepts JSONL and JSONL.GZ. A call commits its iterable atomically. A failed or interrupted batch rolls back. Separate files can serve as batches within an immutable run descriptor. Publish after all intended batches complete. Each result replaces the producer's entire contribution to that item. Empty `fields` records an evaluated empty result. Omitted items retain their previous results. A new run ID permits new provenance. Identity or input-hash conflicts reject the batch. The most recently committed result for each item and producer is current.

## Query and verify an edition

`lookup` uses indexes on catalog ID or OAI identifier and returns the input identity, hash and fields grouped by producer. Unknown or ambiguous identifiers fail explicitly. A consumer must compare identity, variant and metadata hash before applying results.

The [SQLite schema](../tools/metadata-enrichment/enrichment_package/schema.sql) defines items, runs, producer results and shared occurrences. Read clients should open with `mode=ro`. Publishing uses SQLite backup, integrity checks and a sealed database, with its size and SHA-256 recorded in the manifest. Manifest occurrence counts represent item-result links.

For facet counts using SQLite JSON functions:

```sql
SELECT o.target, json_extract(o.content, '$.value') AS facet,
       count(DISTINCT r.item) AS items
FROM results r
JOIN result_occurrences l ON l.result = r.id
JOIN occurrences o ON o.id = l.occurrence
WHERE r.producer = 'rights'
GROUP BY o.target, facet
ORDER BY o.target, items DESC;
```
