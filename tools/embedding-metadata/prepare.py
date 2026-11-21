"""Build a self-contained annotated-metadata v1 package from an export v2 package."""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
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

from . import keyword_language, metadata_roles, postprocess


IDENTITY = ("network", "catalogId", "identifier", "metadataHash")
FAMILIES = ("titles", "abstracts", "keywords", "affiliations", "funders", "documentTypes", "otherDescriptions")
INPUT_FIELDS = ("titles", "descriptions", "keywords", "affiliations", "funders", "types")
PROFILES = {("bibliographic-roles", "1.0"), ("classification-embeddings", "2.0")}
PART = re.compile(r"[^/]+/part-[0-9]+\.jsonl(?:\.gz)?")
INDEX = """CREATE TABLE records (
    network TEXT NOT NULL, catalog_id TEXT NOT NULL, identifier TEXT NOT NULL, metadata_hash TEXT NOT NULL,
    snapshot_ref TEXT NOT NULL, parent_file TEXT NOT NULL, parent_position INTEGER NOT NULL,
    status TEXT NOT NULL, file TEXT, position INTEGER, origins TEXT, error TEXT,
    PRIMARY KEY(network, catalog_id), UNIQUE(file, position), UNIQUE(parent_file, parent_position)
)"""


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


def bibliographic(row, annotated, detect_language):
    data = {k: [] for k in FAMILIES}
    origins = defaultdict(list)

    def add(family, value, field, index):
        data[family].append(value)
        origins[family].append([field, index])

    def text(item):
        return {"value": item["value"], "language": item.get("detectedLanguageCode", item["detectedLanguage"])}

    for i, item in enumerate(annotated["titles"]):
        add("titles", text(item), "titles", i)
    for i, item in enumerate(keyword_language.annotate_keywords(row["data"]["keywords"], annotated, detect_language)):
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
    return {**{k: row[k] for k in IDENTITY}, "data": data}, origins


def verify_rows(root, parts, db):
    """Check each published locator against its actual JSONL line and identity."""
    verified = 0
    for part in parts:
        cursor = iter(db.execute("SELECT position,network,catalog_id,identifier,metadata_hash FROM records "
                                 "WHERE file=? ORDER BY position", (part,)))
        for pos, row in enumerate(postprocess.read_rows(root / part), 1):
            if next(cursor, None) != (pos, *(row[k] for k in IDENTITY)):
                raise ValueError(f"Output index mismatch at {part}:{pos}")
            verified += 1
        if next(cursor, None) is not None:
            raise ValueError(f"Missing output rows in {part}")
    return verified


def convert(root, dest, manifest, mapping, parts, annotator):
    required = INPUT_FIELDS if mapping["name"] == "bibliographic-roles" else ("titles", "descriptions", "keywords")
    source_refs = {s["network"]: s["snapshotRef"] for s in manifest["sources"]}
    totals = Counter(input=0, annotated=0, errors=0, keywordOccurrences=0, keywordsUndetermined=0)
    networks = defaultdict(Counter)
    output_parts = []
    with (closing(sqlite3.connect((root / "records.sqlite").as_uri() + "?mode=ro&immutable=1", uri=True)) as source,
          closing(sqlite3.connect(dest / "records.sqlite")) as db,
          (dest / "errors.jsonl").open("w", encoding="utf-8") as errors):
        db.execute(INDEX)
        expected = manifest["counts"]["exported"]
        if source.execute("SELECT count(*) FROM records WHERE status='EXPORTED'").fetchone()[0] != expected:
            raise ValueError("Parent index count differs from manifest")
        for part in parts:
            out_name = part if part.endswith(".gz") else part + ".gz"
            out = dest / out_name
            out.parent.mkdir(exist_ok=True)
            count = 0
            with gzip.open(out, "xt", encoding="utf-8", compresslevel=1) as f:
                for pos, row in enumerate(postprocess.read_rows(root / part), 1):
                    identity = tuple(row[k] for k in IDENTITY)
                    parent = source.execute("SELECT export_id,identifier,metadata_hash,snapshot_ref,file,position "
                                            "FROM records WHERE network=? AND catalog_id=? AND status='EXPORTED'",
                                            identity[:2]).fetchone()
                    if parent != (manifest["exportId"], *identity[2:], source_refs[row["network"]], part, pos):
                        raise ValueError(f"Parent index mismatch at {part}:{pos}")
                    totals["input"] += 1
                    stats = networks[row["network"]]
                    stats["input"] += 1
                    try:
                        validate_data(row.get("data"), required)
                        counts = defaultdict(Counter)
                        ann = annotator.annotate(row, manifest["exportId"], counts)
                        record, origins = bibliographic(row, ann, annotator.detect_language)
                    except RecordError as exc:
                        error = str(exc)
                        errors.write(compact({**dict(zip(IDENTITY, identity)), "error": error}) + "\n")
                        result = ("ERROR", None, None, None, error)
                        totals["errors"] += 1
                        stats["errors"] += 1
                    else:
                        f.write(compact(record) + "\n")
                        count += 1
                        totals["annotated"] += 1
                        stats["annotated"] += 1
                        for family in ("title", "abstract"):
                            for label, n in counts["records." + family].items():
                                stats[family + "." + label] += n
                        for keyword in record["data"]["keywords"]:
                            stats["keyword.language." + keyword["language"]] += 1
                            stats["keyword.evidence." + keyword["languageSource"]] += 1
                            totals["keywordOccurrences"] += 1
                            totals["keywordsUndetermined"] += keyword["language"] == "und"
                        result = ("ANNOTATED", out_name, count, compact(origins), None)
                    db.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                               (*identity, parent[3], part, pos, *result))
            output_parts.append(out_name)
            db.commit()
        verified = verify_rows(dest, output_parts, db)
        if totals["input"] != expected or verified != totals["annotated"] or verified + totals["errors"] != expected:
            raise ValueError("Output counts do not reconcile")
    return totals, networks, output_parts


def prepare(root, output, models):
    root = root.resolve()
    if output.resolve().is_relative_to(root):
        raise ValueError("Choose an output directory outside the input package")
    parent_hash = postprocess.sha(root / "manifest.json")
    parent, mapping, parts = checked_export(root)
    language, role = models / "lid.176.ftz", models / "role.bin"
    processor = {
        "name": "prepare-embedding-metadata", "version": version("lareferencia-embedding-metadata"),
        "keywordLanguage": "declared-record-text-model-v1", "langcodes": version("langcodes"),
        "fasttext": version("fasttext"), "modelHashes": {"language": postprocess.sha(language), "role": postprocess.sha(role)},
        "codeHashes": {p.name: postprocess.sha(p) for p in map(Path, (__file__, postprocess.__file__, metadata_roles.__file__, keyword_language.__file__))},
        "thresholds": {"language": postprocess.LANG_THRESHOLD, "languageMargin": postprocess.LANG_MARGIN,
                       "role": postprocess.ROLE_THRESHOLD, "minAbstractWords": postprocess.MIN_ABSTRACT_WORDS},
        "abstractFallback": "longest-nonblank-uncertain-first-on-tie"
    }
    annotator = postprocess.Annotator(language, role)
    package_id = "ann-" + str(uuid4())
    output.mkdir(parents=True, exist_ok=True)
    final = output / package_id
    with tempfile.TemporaryDirectory(dir=output, prefix=".prepare-") as work:
        dest = Path(work) / package_id
        dest.mkdir()
        started = now()
        totals, networks, data_parts = convert(root, dest, parent, mapping, parts, annotator)
        if parent_hash != postprocess.sha(root / "manifest.json"):
            raise ValueError("Parent manifest changed during annotation")
        files = [{"path": name, "bytes": (dest / name).stat().st_size, "sha256": postprocess.sha(dest / name)}
                 for name in [*data_parts, "records.sqlite", "errors.jsonl"]]
        status = "PARTIAL" if totals["errors"] else "COMPLETE"
        manifest = {
            "contractVersion": 1, "packageType": "annotated-metadata", "packageId": package_id,
            "status": status, "startedAt": started, "finishedAt": now(),
            "parent": {"exportId": parent["exportId"], "manifestHash": parent_hash,
                       "contractVersion": parent["contractVersion"], "options": parent["options"],
                       "mapping": {k: mapping[k] for k in ("name", "version")}, "mappingHash": parent["mappingHash"]},
            "sources": parent["sources"], "skippedSources": parent.get("skippedSources", []),
            "processor": processor, "counts": totals, "countsByNetwork": networks,
            "parts": data_parts, "files": files,
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
    args = parser.parse_args()
    try:
        status, dest = prepare(args.input, args.output, args.models_dir)
    except (ValueError, OSError, KeyError, RuntimeError, sqlite3.Error, EOFError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"{status}: {dest.resolve()}")
    return 0 if status == "COMPLETE" else 2
