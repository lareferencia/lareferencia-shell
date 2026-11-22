# Prepare metadata for embeddings

The pipeline has two preparation steps. The Java shell exports metadata from a snapshot. The Python command in this repository selects descriptions and builds the text for the batch embedding calculator. Use `--combine` for one vector per record with a title.

## Export and prepare

From the LA Referencia shell, export the original metadata for the required network. Add `--valid-only` when the campaign is limited to validated records.

```text
export-metadata --network UY --variant original --format jsonl --mapping config/exports/bibliographic-roles-v1.json --compression gzip --output /srv/metadata-exports
```

Install the Python command from the shell repository and provision the approved `lid.176.ftz` and `role.bin` files in the same models directory. The [pilot guide](../tools/embedding-metadata/README.md) documents how to obtain the language model and train the role model. The preparer also accepts the `classification-embeddings` 2.0 profile.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install ./tools/embedding-metadata

.venv/bin/prepare-embedding-metadata \
  --input "$EXPORT_DIR" --models-dir "$MODELS_DIR" \
  --output /srv/metadata-exports/prepared --combine
```

Use the exact `exp-…` directory reported by Java as `EXPORT_DIR`. You can set `LR_EMBEDDING_MODELS` in place of `--models-dir`. The Python command validates the export inventory, checks each input against its index and writes a new package directory. It publishes by renaming a temporary directory. Exit code 0 means `COMPLETE`, 2 means `PARTIAL` with row errors in `errors.jsonl`, and 1 signals a fatal failure. Automated consumers must require `COMPLETE`.

## Combined text

fastText and the role rules evaluate every description. The preparer retains all accepted descriptions. When none is accepted, it picks the longest nonblank uncertain description after cleaning, breaking ties by source order. Each selected occurrence keeps its original literal, including any languages, rights statements or acknowledgments it contains.

The title and abstract blocks each put detected English occurrences first and preserve source order within the English and remaining groups. Two newlines separate occurrences. The body uses the title block when no description was selected. The preparer appends all nonblank keywords as the last paragraph of the body, in source order and separated by commas. It performs language detection only on titles and descriptions. The template is `title: {titles} | text: {body}`.

The `embedding-inputs` v1 manifest lists the recipe, completion status, ordered GZIP JSONL parts, file sizes, SHA-256 checksums and counts. The main data rows contain only `network`, `catalogId` and `text`. Counts reconcile input rows with emitted rows, omissions for missing titles and errors. The abstract counts describe the emitted records and distinguish direct classification, uncertain fallback and missing descriptions.

Add `--include-provenance` to produce `provenance.jsonl.gz`. The sidecar uses `(network, catalogId)` to join to the data rows. It includes the OAI identifier, metadata hash, snapshot reference, export part and 1-based line, and the 0-based occurrence indexes in text order. Description references record `classified` or `uncertain_fallback`. The manifest resolves snapshot references and identifies the parent export, profile and fastText model hashes. Keep the parent export to inspect original projected occurrences and the snapshot store to access historical XML.

## Calculate vectors

Use the batch calculator from the embedding-service repository. Pass the prepared package directory reported by Python. Pin a model revision available in the GPU environment.

```sh
python scripts/python/compute_metadata_embeddings.py \
  "$PREPARED_DIR" "$VECTOR_DIR" --revision "$MODEL_REVISION"
```

The calculator verifies the data checksums and encodes the supplied text. It emits one row containing `network`, `catalogId` and `vector` per input row. The default overflow policy for this format truncates the encoder input and records the part, line and token counts in the vector manifest. Use `--on-overflow error` to reject oversize inputs. The prepared text stays complete on disk.

## Annotated metadata and per-language texts

Omit `--combine` to produce an `annotated-metadata` v2 package. It includes a local SQLite index and arrays for titles, abstracts, raw keywords, affiliations, funders, document types and other descriptions. Titles and abstracts include their detected languages. Abstracts record their selection. Records without a title remain available for inspection. Add `--include-provenance` for the export locators and occurrence indexes.

```sh
python3.12 tools/embedding-metadata/examples/build_inputs.py "$ANNOTATED_DIR" > entries.jsonl
```

This example creates texts per language for records with a title. Unknown-language occurrences get individual entries. New annotated packages keep the keywords in metadata and omit them from these texts. The example also reads historical v1 packages and respects their recorded keyword assignments. Use `--classified-only` to exclude uncertain fallbacks from this per-language view.

## Verification with Uruguay

The reference export for UY snapshot 4186 contains 30,752 records with usable titles. The combined recipe produces 30,752 inputs and preserves the 2,040 uncertain description selections from the historical annotation. The historical per-language pilot produced 53,737 inputs.

Run the preparer tests from the shell repository after installing the package.

```sh
.venv/bin/python -m unittest discover -s tools/embedding-metadata
```
