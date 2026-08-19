# LA Referencia Shell

Spring Shell command-line application for LA Referencia platform administration,
maintenance, data loading, indexing, and operational diagnostics.

The base module provides database, repository, workflow, dump, and maintenance
commands. Entity commands are contributed by `lareferencia-shell-entity-plugin`
when `lareferencia-shell` is built with a profile that includes that plugin
(`lareferencia`, `rcaap`, or `ibict`).

## Build

Build from the parent repository root (`lareferencia-platform`) with the
project build script:

```bash
./build.sh <profile>
```

Common profiles:

```bash
./build.sh lareferencia
./build.sh ibict
./build.sh rcaap
./build.sh lite
```

Profiles `lareferencia`, `ibict`, and `rcaap` include
`lareferencia-shell-entity-plugin`, so the entity loading and indexing commands
are available in the shell. The `lite` profile builds the base shell without
those entity plugin commands.

The package phase copies the executable shell jar to:

```text
lareferencia-shell/lareferencia-shell.jar
```

## Configuration

By default, the shell reads configuration from `./config` relative to the
current working directory. Use `app.config.dir` to point the shell at another
configuration directory:

```bash
JAVA_OPTS="-Dapp.config.dir=/etc/lrharvester/config" ./lareferencia-shell.jar
```

The main configuration variables are stored in:

```text
lareferencia-shell/config/application.properties
```

Use this file to configure the shell environment, including database
connection, Elasticsearch/OpenSearch, metadata store, indexing, Flowable, and
optional entity settings. The application expects these values to match the
platform services that the shell will operate on.

## Running Commands

Start an interactive shell:

```bash
./lareferencia-shell.jar
```

With a custom configuration directory:

```bash
JAVA_OPTS="-Dapp.config.dir=/etc/lrharvester/config" ./lareferencia-shell.jar list-networks
```

Inside the interactive shell, use `help` to list available commands and
`help <command>` to inspect command syntax for the built distribution.

## Common Workflows

### Initialize or Upgrade the Database

```bash
database_info
database_migrate
database_info
```

For existing databases, `database_migrate` defaults to
`baselineOnMigrate=true`.

```bash
database_migrate --out-of-order true --baseline-on-migrate true
```

### Load Entity Data from XML

Entity commands require a shell build that includes
`lareferencia-shell-entity-plugin`.

1. Load or update the entity metamodel if needed:

```bash
load_model /data/entities/metamodel.xml
```

2. Dry-run one XML file:

```bash
load_data --path /data/entities/batch_19792.xml --dryRun true
```

3. Load every `.xml` file under a directory:

```bash
load_data --path /data/entities/incoming --dryRun false
```

4. Merge dirty/source entities into final entity tables:

```bash
merge_dirty_entities
```

`load_data` accepts either one XML file or a directory. Directories are scanned
recursively and non-XML files are skipped. After a real load, run
`merge_dirty_entities` before indexing.

### Index Entities

List available indexer beans:

```bash
list-indexers
```

Export the OpenSearch/Elasticsearch mapping generated from an indexing
configuration:

```bash
index-entities-mapping /etc/lrharvester/entity-indexing.xml /tmp/person-mapping.json Person
```

Index all entity types with an indexer bean:

```bash
index-entities /etc/lrharvester/entity-indexing.xml entityIndexerElastic
```

Index only one entity type:

```bash
index-entities /etc/lrharvester/entity-indexing.xml entityIndexerElastic Person
```

Index entities updated since an ISO local date-time:

```bash
index-entities /etc/lrharvester/entity-indexing.xml entityIndexerElastic null null 2026-08-01T00:00:00
```

Index entities from one provenance source. When `provenance` is provided,
`lastUpdate` is ignored:

```bash
index-entities /etc/lrharvester/entity-indexing.xml entityIndexerElastic null brc
```

Tune pagination and worker count:

```bash
index-entities /etc/lrharvester/entity-indexing.xml entityIndexerElastic Person null null 2000 1 4
```

The full argument order is:

```text
index-entities <configFileFullPath> <indexerName> [entityTypeName] [provenance] [lastUpdate] [pageSize] [fromPage] [threadsToRun]
```

Use the literal value `null` to skip optional positional arguments before later
arguments.

### Mark and Remove Deleted Entities

Run migrations first so the `entity.deleted` column exists:

```bash
database_migrate
```

Mark UUIDs as deleted:

```bash
mark_entities_deleted --path /data/entities/deleted-uuids.txt
```

The UUID file may contain UUIDs separated by newlines, spaces, commas, or
semicolons. Text after `#` on a line is ignored.

Undo the deleted flag:

```bash
set_entities_deleted --path /data/entities/deleted-uuids.txt --deleted false
```

Remove deleted root documents and nested references from one index:

```bash
remove_deleted_entities_from_index --indexName brc-person --pageSize 1000
```

Run index cleanup once per target index.

### Run Network Workflows

Flowable workflow commands are available only when
`workflow.engine=flowable`.

```bash
list-workflows
list-networks
run-process networkProcessing 42 false
list-running
process-status 9a52b84c-7d7e-11f0-91d6-acde48001122
stop-process 9a52b84c-7d7e-11f0-91d6-acde48001122 "Manual stop"
```

### Export LGK Data

Export a SQLite mapping of `ACRONYM_recordId` to OAI identifiers for all
networks:

```bash
export-all-lgk-identifiers-mapping /exports/lgk-identifiers.sqlite --overwrite true
```

Export gzipped original metadata XML for all networks:

```bash
export-all-lgk-metadata /exports/lgk-metadata --overwrite true
```

Export only one network:

```bash
export-all-lgk-metadata /exports/lgk-metadata 42 true
```

## Command Reference

### Database

| Command | Arguments and options | Description |
| --- | --- | --- |
| `database_info` | none | Show Flyway migration state. |
| `database_migrate` | `[--out-of-order <true\|false>] [--baseline-on-migrate <true\|false>]` | Apply pending database migrations. Defaults: `outOfOrder=false`, `baselineOnMigrate=true`. |
| `database_repair` | none | Repair Flyway schema history metadata. |
| `database_clean` | `[--confirm <true\|false>]` | Delete all database objects managed by Flyway only when `confirm=true`; otherwise logs a warning. |

### Repository and Snapshot Operations

| Command | Arguments and options | Description |
| --- | --- | --- |
| `list-networks` | none | List networks/repositories with ID, acronym, name, and publication flag. |
| `list-snapshots` | `<networkId> [includeDeleted]` | List snapshots for a network. Default `includeDeleted=false`. |
| `networks-table-dump` | `<excelFileFullPath>` | Export network table properties and attributes to an Excel file. |
| `networks-table-update` | `<excelFileFullPath>` | Backup current network table data to `backup.<excelFileFullPath>` and update DB values from Excel. |

### Validators and Transformers

| Command | Arguments and options | Description |
| --- | --- | --- |
| `list-validators` | none | Print validator IDs and names. |
| `list-transformers` | none | Print transformer IDs and names. |
| `migrate-validators` | `[--dry-run <true\|false>]` | Replace legacy v4 validator package references with v5 package references. |
| `migrate-transformers` | `[--dry-run <true\|false>]` | Replace legacy v4 transformer package references with v5 package references. |
| `export-validator` | `--id <validatorId> --filename <path>` | Export one validator as JSON. |
| `import-validator` | `--filename <path> [--migrate <true\|false>]` | Import a validator JSON file. `--migrate true` rewrites legacy package references before import. |
| `export-transformer` | `--id <transformerId> --filename <path>` | Export one transformer as JSON. |
| `import-transformer` | `--filename <path> [--migrate <true\|false>]` | Import a transformer JSON file. `--migrate true` rewrites legacy package references before import. |

### Workflow Commands

Available when `workflow.engine=flowable`.

| Command | Arguments and options | Description |
| --- | --- | --- |
| `list-workflows` | none | List deployed workflow definitions. |
| `run-process` | `<processKey> <networkId> [incremental]` | Submit a workflow for a network. Default `incremental=false`. |
| `process-status` | `<processInstanceId>` | Show process instance details and selected variables. |
| `list-running` | none | List running process instances. |
| `list-queued` | none | Show queue size, running count, and busy lanes. |
| `stop-process` | `<processInstanceId> [reason]` | Terminate a running process. Default reason is `Manual termination`. |

### Dumps and Exports

| Command | Arguments and options | Description |
| --- | --- | --- |
| `export-all-lgk-identifiers-mapping` | `<sqliteFilePath> [overwrite]` | Export LGK identifier mapping for all networks into one SQLite file. Default `overwrite=false`. |
| `export-all-lgk-metadata` | `<outputDirectory> [networkId] [overwrite]` | Export LGK original metadata to `.xml.gz` files. If `networkId` is omitted, all networks are exported. Default `overwrite=false`. |

### Maintenance

| Command | Arguments and options | Description |
| --- | --- | --- |
| `clean-orphan-metadata` | `[snapshotId] [networkId] [dryRun]` | Clean metadata store entries not referenced by a snapshot. Provide either `snapshotId` or `networkId`; `snapshotId` takes priority. Default `dryRun=false`. |
| `migrate-catalog-parquet-to-sqlite` | `<snapshotId> [dryRun]` | Migrate one snapshot catalog from Parquet to SQLite. Default `dryRun=false`. |

### OpenAIRE Broker

| Command | Arguments and options | Description |
| --- | --- | --- |
| `download_broker_events` | `<networkId> <opendoarId>` | Experimental command that downloads OpenAIRE Broker events and stores them for the network. Existing events for that network are deleted first. |

### Entity Metamodel

Provided by `lareferencia-shell-entity-plugin`.

| Command | Arguments and options | Description |
| --- | --- | --- |
| `load_model` | `<filename>` | Load and persist the entity-relation metamodel from XML. |
| `save_model` | `<filename>` | Export the current DB metamodel to XML. |

### Entity Data

Provided by `lareferencia-shell-entity-plugin`.

| Command | Arguments and options | Description |
| --- | --- | --- |
| `load_data` | `--path <file-or-directory> [--dryRun <true\|false>] [--doProfile <true\|false>] [--threadsToRun <n>]` | Load entity-relation XML data. Directories are scanned recursively. Default `dryRun=false`. `threadsToRun` is deprecated and ignored. |
| `merge_dirty_entities` | none | Consolidate loaded source/dirty entity data into final entity and relation tables. |
| `mark_entities_deleted` | `--path <uuid-file>` | Mark listed final entities as deleted. |
| `set_entities_deleted` | `--path <uuid-file> [--deleted <true\|false>]` | Set the deleted flag for listed final entities. Default `deleted=true`. |
| `remove_deleted_entities_from_index` | `--indexName <index> [--pageSize <n>]` | Delete root documents for deleted entities and remove nested deleted-entity references from one OpenSearch/Elasticsearch index. Default `pageSize=1000`. |

### Entity Indexing

Provided by `lareferencia-shell-entity-plugin`.

| Command | Arguments and options | Description |
| --- | --- | --- |
| `list-indexers` | none | List available `IEntityIndexer` bean names. |
| `list-indexing-filters` | none | List available indexing filter bean names. |
| `index-entities-mapping` | `<configFileFullPath> [outputFileFullPath] [entityTypeName]` | Export OpenSearch/Elasticsearch JSON mappings from an entity indexing config. Use `null` to omit optional arguments. |
| `transform-jena-tdb-to-xml` | `--path <tdb-path>` | Export the default graph from a Jena TDB2 dataset to `<path>.xml`. |
| `index-entities` | `<configFileFullPath> <indexerName> [entityTypeName] [provenance] [lastUpdate] [pageSize] [fromPage] [threadsToRun]` | Index entities using an indexer bean. Defaults: `entityTypeName=null`, `provenance=null`, `lastUpdate=null`, `pageSize=1000`, `fromPage=1`, `threadsToRun=0`. `lastUpdate` format is `yyyy-MM-ddTHH:mm:ss`. |
| `index-entities-solr` | `<configFileFullPath> <entityTypeName> [provenance] [pageSize]` | Convenience wrapper that indexes with `entityIndexerSolr`. Defaults: `provenance=none`, `pageSize=1000`. |

## lareferencia-shell guides

Entity loading and indexing guides:

- [English](docs/entity-loading-indexing-guide.en.md)
- [Espanol](docs/guia-carga-indexacion.es.md)
- [Portugues](docs/guia-carga-indexacao.pt.md)

- [Original vs Complementary Entity Loads](original-vs-complementary-entity-load.en.md)

## Notes and Safety

- Prefer `database_info` before and after migrations.
- Run `load_data --dryRun true` before large entity loads.
- Run `merge_dirty_entities` after successful entity loads and before indexing.
- Run `list-indexers` in the target environment before choosing an indexer bean.
- Use `database_clean --confirm true` only on disposable environments; it deletes
  Flyway-managed database objects.
- Use `help <command>` in the built shell to verify exact generated option names
  for your Spring Shell version.

## License

Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
See [LICENSE.txt](../LICENSE.txt) for complete terms.

## Support

Email: soporte@lareferencia.redclara.net

---

LA Referencia - Red Latinoamericana y de Espana de Ciencia Abierta
Part of the LA Referencia Platform v4.2.6 / v5.0
