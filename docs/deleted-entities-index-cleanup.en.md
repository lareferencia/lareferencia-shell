# Deleted Entities and Index Cleanup

This guide explains how to mark final entities as deleted in `lareferencia-shell`
and how to remove those entities, plus their nested references, from
Elasticsearch/OpenSearch indexes.

Use this flow when a known list of final entity UUIDs must stop appearing in
search results.

## 1. Run the Shell

From the `lareferencia-shell` directory:

```bash
cd lareferencia-shell
./lareferencia-shell.jar
```

Before marking entities as deleted, make sure the database migration that adds
the `entity.deleted` column has been applied:

```bash
database_migrate
```

## 2. Mark Entities as deleted

Prepare a text file with the UUIDs of the final entities to delete logically.
The file may contain UUIDs separated by newlines, spaces, commas, or semicolons.
Text after `#` on a line is ignored.

Example:

```bash
mark_entities_deleted --path /opt/shared/OrgUnit_a_retirar.txt
```

This sets `deleted=true` on the listed final entities. After that, they are
excluded from new entity indexing runs.

To undo the flag:

```bash
set_entities_deleted --path /opt/shared/OrgUnit_a_retirar.txt --deleted false
```

## 3. Remove Documents from the Main Entity Index

After marking entities as deleted, remove their root documents from the main
index for that entity type.

For example, when removing `OrgUnit` entities:

```bash
remove_deleted_entities_from_index --indexName brc-nov2025-orgunit-v2 --pageSize 10000 --timeoutSeconds 900
```

This deletes documents whose `_id` matches one of the entity UUIDs marked as
deleted.

## 4. Remove References from Related Indexes

If the deleted entity is embedded as a relation inside other indexes, run the
cleanup once for each related index.

Use `--relationFields` to tell the command which relation object field stores
the related entity.

Example: remove deleted `OrgUnit` references from publications where the
relation is stored in `sponsorOrgUnit.id`:

```bash
remove_deleted_entities_from_index --indexName brc-nov2025-publication-v2 --pageSize 1000 --timeoutSeconds 900 --relationFields sponsorOrgUnit
```

Pass the relation object field name, such as `sponsorOrgUnit`, not the `.id`
subfield. The command builds the query against `sponsorOrgUnit.id` internally.

For very large indexes, `--relationFields` is important because it avoids a full
index scan during the `_update_by_query` relation cleanup step.

When more than one relation field must be cleaned in the same index, pass a
comma-separated list:

```bash
remove_deleted_entities_from_index --indexName brc-nov2025-publication-v2 --pageSize 1000 --timeoutSeconds 900 --relationFields sponsorOrgUnit,journal
```

## Options

- `--indexName`: Elasticsearch/OpenSearch index name. Required.
- `--pageSize`: number of deleted UUIDs processed per batch. Default: `1000`.
- `--timeoutSeconds`: timeout for `_delete_by_query` and `_update_by_query`
  requests. Default: `300`.
- `--relationFields`: optional comma-separated relation object fields to clean.

## Operational Notes

- Run the index cleanup once per target index.
- Always clean the main entity index first.
- Then clean every related index where the deleted entity appears as a nested
  relation.
- The cleanup is idempotent and can be safely re-run.
- For large indexes, increase `--timeoutSeconds` and prefer `--relationFields`
  whenever the related field is known.
