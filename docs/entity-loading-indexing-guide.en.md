# Entity Loading and Indexing Guide

This guide describes a simple end-to-end flow to build the platform, configure
`lareferencia-shell`, load an entity model and entity data, merge duplicated or
dirty entities, and index the final entities.

## 1. Build the Platform

Run the build from the parent repository root, `lareferencia-platform`.

Choose the profile for the target deployment:

```bash
./build.sh ibict
```

Other common profiles:

```bash
./build.sh lareferencia
./build.sh rcaap
./build.sh lite
```

Profiles `ibict`, `lareferencia`, and `rcaap` include
`lareferencia-shell-entity-plugin`, which provides the entity loading and
indexing commands.

## 2. Configure lareferencia-shell

Edit:

```text
lareferencia-platform/lareferencia-shell/config/application.properties
```

Point the shell to the PostgreSQL database that will receive the loaded data:

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/database_name
```

Replace `database_name` with the actual database name.

Make sure the rest of the shell configuration also matches the environment:

- `spring.datasource.username`
- `spring.datasource.password`
- Elasticsearch/OpenSearch properties, when indexing to Elasticsearch
- Any metadata, entity, or custom context properties required by the selected
  profile

## 3. Download or Prepare the Entity Model

For example, to use the BrCris/Ibict model from GitHub:

```bash
git clone https://github.com/brcris-ibict/brcris-model.git
```

Identify the model XML file inside the cloned repository, for example:

```text
/path/to/brcris-model/modelo_brcris.xml
```

Also prepare the entity data directory or XML file to load:

```text
/path/to/entity-data
```

`load_data` can receive either one XML file or a directory. When a directory is
provided, all `.xml` files inside it are loaded recursively.

## 4. Start the Shell

From the `lareferencia-shell` directory:

```bash
cd lareferencia-shell
./lareferencia-shell.jar
```

If you need to point to another configuration directory:

```bash
JAVA_OPTS="-Dapp.config.dir=/path/to/config" ./lareferencia-shell.jar
```

## 5. Prepare the Database

Inside the shell, run:

```bash
database_migrate
```

If you intentionally need to recreate an empty database, clean it first:

```bash
database_clean --confirm true
database_migrate
```

Warning: `database_clean --confirm true` deletes the Flyway-managed database
objects and data. Use it only when you really want to reset the database.

## 6. Load the Entity Model

Load the entity metamodel XML:

```bash
load_model /path/to/modelo.xml
```

## 7. Load Entity Data

Recommended first pass: run a dry run to validate the path and XML files
without persisting data.

```bash
load_data --path /path/to/entity-data --dryRun true
```

Then run the real load:

```bash
load_data --path /path/to/entity-data
```

After `load_data` finishes, the data is loaded into source or dirty entity
structures. It still must be merged before indexing.

## 8. Merge Dirty Entities

Run the merge process:

```bash
merge_dirty_entities
```

This consolidates the loaded source entity data into the final entity and
relation tables used by indexing.

## 9. Index Entities

List the indexers available in the current shell configuration:

```bash
list-indexers
```

Run indexing with the desired indexing config, entity type, page size, and
indexer bean.

Example:

```bash
index-entities \
  --configFileFullPath /path/to/entity-indexing-config.xml \
  --indexerName entityIndexerElastic \
  --entityTypeName Person \
  --pageSize 1000
```

Useful optional filters:

```bash
index-entities \
  --configFileFullPath /path/to/entity-indexing-config.xml \
  --indexerName entityIndexerElastic \
  --entityTypeName Person \
  --lastUpdate 2026-08-01T00:00:00 \
  --pageSize 1000
```

```bash
index-entities \
  --configFileFullPath /path/to/entity-indexing-config.xml \
  --indexerName entityIndexerElastic \
  --entityTypeName Person \
  --provenance brc \
  --pageSize 1000
```

When `provenance` is provided, `lastUpdate` is ignored.

## 10. Quick Checklist

- Platform built with a profile that includes the entity plugin.
- `spring.datasource.url` points to the correct PostgreSQL database.
- Database migrations were executed.
- Entity model was loaded with `load_model`.
- Entity data was loaded with `load_data --path`.
- `merge_dirty_entities` completed successfully.
- `list-indexers` shows the expected indexer bean.
- `index-entities` completed and generated an indexing report.
