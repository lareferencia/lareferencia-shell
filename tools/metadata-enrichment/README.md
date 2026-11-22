# Metadata enrichment tools

This directory contains the complete rights pipeline and the generic SQLite enrichment
package writer. All runtime modules and tests are maintained in the shell repository.

From the shell checkout root:

```sh
python3 tools/metadata-enrichment/run_rights_pipeline.py --network PY
python3 tools/metadata-enrichment/run_rights_pipeline.py --network PY --export-dir /srv/metadata-exports/exp-UUID
python3 -m unittest discover -s tools/metadata-enrichment -p 'test_*.py'
```

The default Java shell and extraction profile are resolved relative to this repository.
Use `--shell-dir` to target another configured shell installation.

The [package guide](../../docs/METADATA_ENRICHMENT_PACKAGE.md) documents the commands,
fields, transaction behavior, publication and lookup. The
[extraction history](../../docs/LICENSE_METADATA_EXTRACTION.md) records the original
17-country campaign and its inventory methodology.

| Component | Responsibility |
| --- | --- |
| `run_rights_pipeline.py`, `rights_export.py` | Coordinate a server run and verify exported records |
| `normalize_rights.py`, `rights_taxonomy_v7.py`, `rights_catalog.py` | Recognize declarations and project the current taxonomy |
| `cc_license_fragments.py`, `normalize_cc_licenses.py`, `classify_export_licenses.py` | Shared recognition rules used by the normalizer |
| `count_export_licenses.py` | Count distinct source literals by item |
| `build_rights_enrichment.py` | Generate license and copyright occurrences |
| `enrichment_package/`, `enrichments.py` | Write, publish and query generic enrichment packages |
