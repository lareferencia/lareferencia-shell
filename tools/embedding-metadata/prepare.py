"""Prepare bibliographic annotations or combined embedding inputs from a metadata export."""
import argparse
from collections import Counter, defaultdict
from contextlib import closing, nullcontext
from datetime import datetime, timezone
import gzip
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from uuid import uuid4

from . import combined, postprocess


IDENTITY = ("network", "catalogId", "identifier", "metadataHash")
FAMILIES = ("titles", "abstracts", "keywords", "affiliations", "funders", "documentTypes", "otherDescriptions")
INPUT_FIELDS = ("titles", "descriptions", "keywords", "affiliations", "funders", "types")
PROFILES = {("bibliographic-roles", "1.0"), ("classification-embeddings", "2.0")}
PART = re.compile(r"[^/]+/part-[0-9]+\.jsonl(?:\.gz)?")
INDEX = """CREATE TABLE records (
    network TEXT NOT NULL, catalog_id TEXT NOT NULL,
    status TEXT NOT NULL, file TEXT, position INTEGER, error TEXT,
    PRIMARY KEY(network, catalog_id), UNIQUE(file, position)
)"""
PROVENANCE = "provenance.jsonl.gz"


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def now():
    return datetime.now(timezone.utc).isoformat()


def checked_export(root):
    manifest = json.loads((root / "manifest.json").read_bytes())
    if (manifest["contractVersion"], manifest["status"], manifest["options"]["format"]) != (2, "COMPLETE", "jsonl"):
        raise ValueError("Expected a COMPLETE version 2 JSONL export")
    files = set()
    parts = []
    for entry in manifest["files"]:
        name = entry["path"]
        rel = Path(name)
        path = root / rel
        if (rel.is_absolute() or ".." in rel.parts or str(rel) != name or name in files
                or not path.resolve().is_relative_to(root) or path.stat().st_size != entry["bytes"]
                or postprocess.sha(path) != entry["sha256"]):
            raise ValueError(f"Invalid export inventory entry: {name}")
        files.add(name)
        if PART.fullmatch(name):
            parts.append(name)
    if not {"records.sqlite", "errors.jsonl", "mapping.json"} <= files:
        raise ValueError("Incomplete export inventory")
    mapping = json.loads((root / "mapping.json").read_bytes())
    if (mapping["name"], mapping["version"]) not in PROFILES:
        raise ValueError("Unsupported export mapping")
    canonical = json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if manifest["mappingHash"] != "sha256:" + hashlib.sha256(canonical.encode()).hexdigest():
        raise ValueError("Unexpected mapping hash")
    return manifest, mapping, sorted(parts)


class RecordError(ValueError):
    """Invalid projected metadata in a record with verified identity."""


def validate_data(data, required):
    if not isinstance(data, dict):
        raise RecordError("Expected a data object")
    for field in INPUT_FIELDS:
        items = data.get(field, None if field in required else [])
        if not isinstance(items, list):
            raise RecordError(f"Expected array in data.{field}")
        for i, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("value"), str):
                raise RecordError(f"Expected string in data.{field}[{i}].value")
            for key in ("language", "qualifier"):
                if key in item and not isinstance(item[key], str):
                    raise RecordError(f"Invalid data.{field}[{i}].{key}")


def bibliographic(row, annotated, *, include_provenance):
    data = {k: [] for k in FAMILIES}
    origins = defaultdict(list)

    def add(family, value, field, index):
        data[family].append(value)
        if include_provenance:
            origins[family].append([field, index])

    def text(item):
        return {"value": item["value"], "language": item.get("detectedLanguageCode", item["detectedLanguage"])}

    for i, item in enumerate(annotated["titles"]):
        add("titles", text(item), "titles", i)
    for i, item in enumerate(row["data"]["keywords"]):
        add("keywords", item, "keywords", i)

    represented = set()
    for family, key in (("funders", "name"), ("affiliations", "literal"), ("documentTypes", "type")):
        for ref in annotated[family]:
            field = {"declaredFunders": "funders", "declaredAffiliations": "affiliations"}.get(ref["field"], ref["field"])
            index = ref["index"]
            item = {"value": ref.get(key, row["data"][field][index]["value"])}
            if family == "funders":
                item["evidence"] = ref["evidence"]
            add(family, item, field, index)
            if field == "descriptions":
                represented.add(index)
    for i, item in enumerate(annotated["descriptions"]):
        value = text(item)
        if item["role"] == "abstract":
            value["selection"] = item.get("abstractSelection", "classified")
            add("abstracts", value, "descriptions", i)
        elif item["role"] in ("other", "uncertain") or i not in represented:
            value["role"] = item["role"]
            add("otherDescriptions", value, "descriptions", i)
    return data, origins


def verify_rows(root, parts, db):
    """Check the annotated package's index against its published JSONL lines."""
    verified = 0
    for part in parts:
        cursor = iter(db.execute("SELECT position,network,catalog_id FROM records WHERE file=? ORDER BY position", (part,)))
        for pos, row in enumerate(postprocess.read_rows(root / part), 1):
            if next(cursor, None) != (pos, row["network"], row["catalogId"]):
                raise ValueError(f"Output index mismatch at {part}:{pos}")
            verified += 1
        if next(cursor, None) is not None:
            raise ValueError(f"Missing output rows in {part}")
    return verified


def write_row(stream, value):
    stream.write(compact(value) + "\n")


def convert(root, dest, manifest, mapping, parts, annotator, *, combine, include_provenance):
    required = INPUT_FIELDS if mapping["name"] == "bibliographic-roles" else ("titles", "descriptions", "keywords")
    source_refs = {s["network"]: s["snapshotRef"] for s in manifest["sources"]}
    index = nullcontext() if combine else closing(sqlite3.connect(dest / "records.sqlite"))
    audit = gzip.open(dest / PROVENANCE, "xt", encoding="utf-8", compresslevel=1) if include_provenance else nullcontext()
    success = "emitted" if combine else "annotated"
    totals = Counter(input=0, errors=0, omittedMissingTitle=0, keywordOccurrences=0, **{success: 0})
    networks = defaultdict(Counter)
    output_parts = []
    with (audit as provenance, index as db,
          closing(sqlite3.connect((root / "records.sqlite").as_uri() + "?mode=ro&immutable=1", uri=True)) as source,
          (dest / "errors.jsonl").open("w", encoding="utf-8") as errors):
        if db is not None:
            db.execute(INDEX)
        expected = manifest["counts"]["exported"]
        if source.execute("SELECT count(*) FROM records WHERE status='EXPORTED'").fetchone()[0] != expected:
            raise ValueError("Parent index count differs from manifest")
        seen = set()
        for part in parts:
            out_name = part if part.endswith(".gz") else part + ".gz"
            if out_name in seen:
                raise ValueError(f"Output part collision: {out_name}")
            seen.add(out_name)
            out = dest / out_name
            out.parent.mkdir(exist_ok=True)
            count = 0
            with gzip.open(out, "xt", encoding="utf-8", compresslevel=1) as stream:
                for pos, row in enumerate(postprocess.read_rows(root / part), 1):
                    key = {k: row[k] for k in IDENTITY[:2]}
                    parent = source.execute("SELECT export_id,identifier,metadata_hash,snapshot_ref,file,position "
                                            "FROM records WHERE network=? AND catalog_id=? AND status='EXPORTED'",
                                            tuple(key.values())).fetchone()
                    if parent != (manifest["exportId"], row["identifier"], row["metadataHash"],
                                  source_refs[row["network"]], part, pos):
                        raise ValueError(f"Parent index mismatch at {part}:{pos}")
                    stats = networks[row["network"]]
                    for counter in (totals, stats):
                        counter["input"] += 1
                    try:
                        validate_data(row.get("data"), required)
                    except RecordError as exc:
                        error = str(exc)
                        write_row(errors, {**key, "error": error})
                        if db is not None:
                            db.execute("INSERT INTO records VALUES (?,?, 'ERROR',NULL,NULL,?)", (*key.values(), error))
                        totals["errors"] += 1
                        stats["errors"] += 1
                        continue

                    counts = defaultdict(Counter)
                    annotated = annotator.annotate(row, manifest["exportId"], counts)
                    if combine:
                        text, origins = combined.compose(row["data"], annotated, include_provenance=include_provenance)
                        if text is None:
                            totals["omittedMissingTitle"] += 1
                            stats["omittedMissingTitle"] += 1
                            continue
                        record = {**key, "text": text}
                    else:
                        data, origins = bibliographic(row, annotated, include_provenance=include_provenance)
                        record = {**key, "data": data}
                    write_row(stream, record)
                    count += 1
                    if db is not None:
                        db.execute("INSERT INTO records VALUES (?,?, 'ANNOTATED',?,?,NULL)", (*key.values(), out_name, count))
                    if provenance is not None:
                        write_row(provenance, {**key, "identifier": row["identifier"], "metadataHash": row["metadataHash"],
                                               "snapshotRef": parent[3], "sourceFile": part, "sourceLine": pos,
                                               "origins": origins})
                    for counter in (totals, stats):
                        counter[success] += 1
                        counter["keywordOccurrences"] += len(row["data"]["keywords"])
                        for family in ("title", "abstract"):
                            for label, n in counts["records." + family].items():
                                counter[family + "." + label] += n
            output_parts.append(out_name)
            if db is not None:
                db.commit()
        if db is not None and verify_rows(dest, output_parts, db) != totals[success]:
            raise ValueError("Output index counts do not reconcile")
        if totals["input"] != expected or totals[success] + totals["omittedMissingTitle"] + totals["errors"] != expected:
            raise ValueError("Output counts do not reconcile")
    return totals, networks, output_parts


def prepare(root, output, models, *, combine=False, include_provenance=False):
    root = root.resolve()
    if output.resolve().is_relative_to(root):
        raise ValueError("Choose an output directory outside the input package")
    parent_hash = postprocess.sha(root / "manifest.json")
    parent, mapping, parts = checked_export(root)
    language, role = models / "lid.176.ftz", models / "role.bin"
    annotator = postprocess.Annotator(language, role)
    package_id = ("emb-inputs-" if combine else "ann-") + str(uuid4())
    output.mkdir(parents=True, exist_ok=True)
    final = output / package_id
    started = now()
    with tempfile.TemporaryDirectory(dir=output, prefix=".prepare-") as work:
        dest = Path(work) / package_id
        dest.mkdir()
        totals, networks, data_parts = convert(root, dest, parent, mapping, parts, annotator,
                                                combine=combine, include_provenance=include_provenance)
        if parent_hash != postprocess.sha(root / "manifest.json"):
            raise ValueError("Parent manifest changed during preparation")
        names = [*data_parts, "errors.jsonl"]
        if not combine:
            names.append("records.sqlite")
        if include_provenance:
            names.append(PROVENANCE)
        status = "PARTIAL" if totals["errors"] else "COMPLETE"
        manifest = {
            "contractVersion": 1 if combine else 2,
            "packageType": "embedding-inputs" if combine else "annotated-metadata",
            "packageId": package_id, "status": status, "startedAt": started, "finishedAt": now(),
            "counts": totals, "countsByNetwork": networks, "parts": data_parts,
            "files": [{"path": name, "bytes": (dest / name).stat().st_size, "sha256": postprocess.sha(dest / name)}
                      for name in names],
        }
        if combine:
            manifest["recipe"] = combined.RECIPE
        if include_provenance:
            manifest["parent"] = {
                "exportId": parent["exportId"], "manifestHash": parent_hash, "variant": parent["options"]["variant"],
                "mapping": {k: mapping[k] for k in ("name", "version")}, "mappingHash": parent["mappingHash"],
                "sources": parent["sources"], "skippedSources": parent.get("skippedSources", []),
            }
            manifest["processor"] = {
                "name": "prepare-embedding-metadata", "version": version("lareferencia-embedding-metadata"),
                "fasttext": version("fasttext"), "modelHashes": {"language": postprocess.sha(language), "role": postprocess.sha(role)},
            }
        (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        dest.rename(final)
    return status, final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="COMPLETE export package directory")
    parser.add_argument("--output", type=Path, required=True, help="Parent directory for the new package")
    parser.add_argument("--models-dir", type=Path, default=os.getenv("LR_EMBEDDING_MODELS", "modelos"),
                        help="Directory containing lid.176.ftz and role.bin (default: LR_EMBEDDING_MODELS or ./modelos)")
    parser.add_argument("--combine", action="store_true", help="Prepare one combined embedding input per record with a title")
    parser.add_argument("--include-provenance", action="store_true", help="Include source provenance and occurrence references")
    args = parser.parse_args()
    try:
        status, dest = prepare(args.input, args.output, args.models_dir,
                               combine=args.combine, include_provenance=args.include_provenance)
    except (ValueError, OSError, KeyError, RuntimeError, sqlite3.Error, EOFError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"{status}: {dest.resolve()}")
    return 0 if status == "COMPLETE" else 2
