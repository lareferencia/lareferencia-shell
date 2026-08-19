# Original vs Complementary Entity Loads

This document explains the difference between an original entity load and a
complementary entity load in `lareferencia-shell`.

Both flows use the same data loading command. The difference is not the command
itself, but the provenance and the amount of data sent in the XML.

## Core Concepts

An entity load uses three important pieces of information:

- `source`: the provider or process that generated the XML data.
- `record`: the record identifier inside that source.
- `semanticIdentifier`: the stable identifier used to match an incoming source
  entity with an existing final entity.

The pair `source + record` identifies the provenance of a loaded source record.
Two loads have the same provenance only when both values are exactly the same.
If either `source` or `record` changes, the provenance is different.

The `semanticIdentifier` is what allows different source records to contribute
to the same final entity.

## Original Load

An original load is the first complete load for a given source record.

It should include all entity fields and relations that are known for that record
at that moment.

Example:

```xml
<entity-relation-data
    source="repo1"
    record="rec123"
    lastUpdate="2026-08-19T10:00:00">

    <entities>
        <entity type="Person" ref="person-1">
            <semanticIdentifier>orcid::0000-0001</semanticIdentifier>
            <field name="name">Jane Doe</field>
            <field name="identifier.orcid">0000-0001</field>
        </entity>
    </entities>
</entity-relation-data>
```

Command:

```bash
load_data --path /path/to/original-data.xml
merge_dirty_entities
```

## Updating the Same Original Record

If the same `source + record` is loaded again with a newer `lastUpdate`, the
system treats it as a replacement for the previous contribution from that same
provenance.

In that case, the XML should be complete again.

Recommended:

```xml
<entity-relation-data
    source="repo1"
    record="rec123"
    lastUpdate="2026-08-20T10:00:00">

    <entities>
        <entity type="Person" ref="person-1">
            <semanticIdentifier>orcid::0000-0001</semanticIdentifier>
            <field name="name">Jane Doe</field>
            <field name="identifier.orcid">0000-0001</field>
            <field name="identifier.scopus">123456789</field>
        </entity>
    </entities>
</entity-relation-data>
```

Avoid sending only the new field for the same `source + record`, because the
previous source entities for that provenance may be logically deleted and
replaced by the new source entities.

## Complementary Load

A complementary load adds extra data from a different provenance to an entity
that already exists. In this context, different provenance means that at least
one part of the `source + record` pair is different.

For example, all of these are different provenances:

| Original provenance | Complementary provenance | Why it is different |
|---|---|---|
| `repo1::rec123` | `repo1::rec123-scopus` | Same `source`, different `record`. |
| `repo1::rec123` | `scopus-enrichment::rec123` | Different `source`, same `record`. |
| `repo1::rec123` | `scopus-enrichment::rec123-scopus` | Different `source` and different `record`. |

It can contain only the `semanticIdentifier` and the new field, as long as the
new field already exists in the entity metamodel.

Example:

```xml
<entity-relation-data
    source="scopus-enrichment"
    record="rec123-scopus"
    lastUpdate="2026-08-20T10:00:00">

    <entities>
        <entity type="Person" ref="person-1">
            <semanticIdentifier>orcid::0000-0001</semanticIdentifier>
            <field name="identifier.scopus">123456789</field>
        </entity>
    </entities>
</entity-relation-data>
```

Command:

```bash
load_data --path /path/to/complementary-data.xml
merge_dirty_entities
```

Because the `semanticIdentifier` matches an existing final entity, the new
source entity is linked to the same final entity during the loading and merge
flow.

## What merge_dirty_entities Does

The `load_data` command stores incoming XML data as source entities and source
relations. These records keep the provenance-specific contribution, but they are
not yet the final consolidated entity view.

The `merge_dirty_entities` command consolidates all dirty source data into the
final `entity` and `relation` tables.

In practical terms, it:

- gathers the active `SourceEntity` records linked to the same final entity;
- copies their field occurrences into the final entity;
- rebuilds final relations from active source relations;
- keeps entities and relations ready for search/indexing;
- marks processed final entities as no longer dirty.

After a normal `load_data`, run `merge_dirty_entities` before indexing or before
expecting the final entity tables to reflect the newly loaded information.

## Model Requirement

Entity data loading does not create new field definitions in the metamodel.

Before loading data that uses a new field, make sure that field already exists
in the entity metamodel. Then load the data:

```bash
load_data --path /path/to/data-with-new-fields.xml
merge_dirty_entities
```

## Decision Table

| Scenario | Recommended action |
|---|---|
| First load of a source record | Send the complete original data. |
| Reloading the same `source + record` with newer data | Send the complete record again. |
| Adding a new field value from another enrichment process | Use a complementary load where `source`, `record`, or both are different. |
| Complementary data uses a field not present in the model | Update the metamodel first, then load the complementary data. |
| Complementary data has the same `semanticIdentifier` as an existing entity | It can be merged into the same final entity. |
| Complementary data has no valid `semanticIdentifier` | The load fails because every source entity needs at least one valid semantic identifier. |
| Same `source + record`, only new field sent | Avoid this; it can replace the previous contribution from that provenance. |

## Recommended Flow

For a new model and original data:

```bash
load_model /path/to/model.xml
load_data --path /path/to/original-data
merge_dirty_entities
```

For adding a new field later:

```bash
load_data --path /path/to/complementary-data
merge_dirty_entities
```

If the later load updates the same original source record, use:

```bash
load_data --path /path/to/complete-updated-original-data.xml
merge_dirty_entities
```

## Short Rule

Use an original load when the XML represents the authoritative data for a
specific `source + record`.

Use a complementary load when the XML represents an additional contribution from
a different provenance, linked to the same final entity through a shared
`semanticIdentifier`. A provenance is different when `source`, `record`, or both
are different.
