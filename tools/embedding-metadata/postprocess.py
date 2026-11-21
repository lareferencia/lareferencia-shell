#!/usr/bin/env python3
"""Annotate titles and descriptions from a COMPLETE classification-embeddings 2.0 JSONL export."""
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import gzip
import hashlib
from importlib.metadata import version
import json
from itertools import islice
from pathlib import Path
import re
import tempfile
from time import perf_counter

import fasttext
if __package__:
    from . import metadata_roles
else:
    import metadata_roles


LABEL = re.compile(r"^\s*(fil|resumen|abstract|resumo)\s*:\s*", re.I)
WORDS = re.compile(r"[^\W\d_]+")
LANG_THRESHOLD = 0.75
LANG_MARGIN = 0.20
ROLE_THRESHOLD = 0.90
MIN_ABSTRACT_WORDS = 12


def clean(value):
    # Remove explicit labels before either model sees the text. One line per occurrence.
    return " ".join(LABEL.sub("", value).split()).replace("\x00", "").replace("__label__", "")


def sha(path):
    with path.open("rb") as f:
        return "sha256:" + hashlib.file_digest(f, "sha256").hexdigest()


def package_parts(package):
    manifest = json.loads((package / "manifest.json").read_text())
    mapping = json.loads((package / "mapping.json").read_text())
    profiles = {("classification-embeddings", "2.0"), ("bibliographic-roles", "1.0")}
    if (manifest["status"] != "COMPLETE" or manifest["options"]["format"] != "jsonl"
            or (mapping["name"], mapping["version"]) not in profiles):
        raise ValueError(f"Incompatible export: {package}")
    parts = []
    for entry in manifest["files"]:
        rel = Path(entry["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Invalid path: {rel}")
        if rel.name.startswith("part-") and rel.name.endswith((".jsonl", ".jsonl.gz")):
            path = package / rel
            if sha(path) != entry["sha256"]:
                raise ValueError(f"Checksum mismatch: {path}")
            parts.append(path)
    return manifest, parts


def read_rows(part):
    opener = gzip.open if part.suffix == ".gz" else open
    with opener(part, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def select_record_abstract(record):
    """Select one uncertain description only when the whole record lacks a classified abstract."""
    descriptions = record["descriptions"]
    candidate = None
    longest = 0
    for index, item in enumerate(descriptions):
        if item["role"] == "abstract":
            return item.get("abstractSelection", "classified")
        if item["role"] == "uncertain":
            length = len(clean(item["value"]).strip())
            if length > longest:
                candidate, longest = index, length

    if candidate is None:
        return "missing"

    chosen = descriptions[candidate]
    chosen["role"] = "abstract"
    chosen["abstractSelection"] = "uncertain_fallback"
    language = chosen.get("detectedLanguageCode") or chosen["detectedLanguage"]
    if language != "und":
        groups = record["embeddingGroups"]
        group = groups.setdefault(language, {"titles": [], "descriptions": []})
        group["descriptions"].append(candidate)
    return "uncertain_fallback"


class Annotator:
    def __init__(self, language, role):
        self.language = fasttext.load_model(str(language))
        self.role = fasttext.load_model(str(role))
        if set(self.role.labels) != {"__label__abstract", "__label__non_abstract"}:
            raise ValueError("Unexpected role model labels")

    @lru_cache(maxsize=4096)
    def detect_language(self, text):
        if next(islice(WORDS.finditer(text), 2, 3), None) is None:
            return "und", None
        labels, scores = self.language.predict(text, k=2)
        if len(scores) < 2 or scores[0] < LANG_THRESHOLD or scores[0] - scores[1] < LANG_MARGIN:
            return "und", None
        first = labels[0].removeprefix("__label__")
        return (first if first in ("es", "en", "pt", "fr") else "other"), first

    @lru_cache(maxsize=4096)
    def detect_role(self, text):
        if not text:
            return "uncertain"
        labels, scores = self.role.predict(text.casefold())
        if not labels or scores[0] < ROLE_THRESHOLD:
            return "uncertain"
        role = labels[0].removeprefix("__label__")
        if role == "abstract" and len(text.split(None, MIN_ABSTRACT_WORDS)) < MIN_ABSTRACT_WORDS:
            return "uncertain"
        return role

    def annotate(self, row, export_id, counts):
        out = {k: row[k] for k in ("network", "catalogId", "identifier", "metadataHash")}
        out["exportId"] = export_id
        out["types"] = row["data"].get("types", [])
        out["declaredFunders"] = row["data"].get("funders", [])
        out["declaredAffiliations"] = row["data"].get("affiliations", [])
        types = []
        for i, item in enumerate(out["types"]):
            kind = metadata_roles.normalize_type(item["value"])
            if kind:
                types.append({"type": kind, "field": "types", "index": i})
        inferred_types = []
        funders = [{"name": item["value"], "evidence": "declared", "field": "declaredFunders", "index": i}
                   for i, item in enumerate(out["declaredFunders"]) if item["value"].strip()]
        affiliations = [{"literal": item["value"], "field": "declaredAffiliations", "index": i}
                        for i, item in enumerate(out["declaredAffiliations"]) if item["value"].strip()]
        groups = defaultdict(lambda: {"titles": [], "descriptions": []})
        for field in ("titles", "descriptions"):
            values = []
            for i, item in enumerate(row["data"].get(field, [])):
                text = clean(item["value"])
                lang, code = self.detect_language(text)
                result = dict(item, detectedLanguage=lang)
                if lang == "other":
                    result["detectedLanguageCode"] = code
                counts[field + ".language"][lang] += 1
                eligible = True
                if field == "descriptions":
                    role, kind, mentions = metadata_roles.describe(item, self.detect_role(text))
                    result["role"] = role
                    decision = role if role in ("abstract", "uncertain") else "non_abstract"
                    result["decision"] = decision
                    counts["descriptions.decision"][decision] += 1
                    if role == "affiliation":
                        ref = {"field": "descriptions", "index": i}
                        literal = metadata_roles.affiliation_literal(item["value"])
                        if literal:
                            ref["literal"] = literal
                        affiliations.append(ref)
                    if kind:
                        inferred_types.append({"type": kind, "field": "descriptions", "index": i})
                    funders.extend({"name": name, "evidence": evidence, "field": "descriptions", "index": i}
                                   for name, evidence in mentions)
                    eligible = role == "abstract"
                if eligible and code:
                    groups[code][field].append(i)
                values.append(result)
            out[field] = values
        has_title = any(title["value"].strip() for title in out["titles"])
        counts["records.title"]["present" if has_title else "missing"] += 1
        out["documentTypes"] = types if types else inferred_types
        out["funders"] = funders
        out["affiliations"] = affiliations
        out["embeddingGroups"] = dict(groups)
        selection = select_record_abstract(out)
        counts["records.abstract"][selection] += 1
        counts["descriptions.role"].update(item["role"] for item in out["descriptions"])
        return out


def process(package, output, language_model, role_model):
    start = perf_counter()
    manifest, parts = package_parts(package)
    models = {"language": sha(language_model), "role": sha(role_model)}
    annotator = Annotator(language_model, role_model)
    setup = perf_counter() - start
    output.mkdir(parents=True, exist_ok=True)
    stem = manifest["exportId"]
    final = output / (stem + ".jsonl.gz")
    report = output / (stem + ".summary.json")
    if final.exists() or report.exists():
        raise FileExistsError(f"Output already exists for {stem}")
    counts = defaultdict(Counter)
    n = 0
    read = classify = write = 0.0
    with tempfile.TemporaryDirectory(dir=output) as tmp:
        dest = Path(tmp) / final.name
        with gzip.open(dest, "wt", encoding="utf-8", compresslevel=1) as stream:
            for part in parts:
                tick = perf_counter()
                for row in read_rows(part):
                    now = perf_counter()
                    read += now - tick
                    annotated = annotator.annotate(row, stem, counts)
                    done = perf_counter()
                    classify += done - now
                    stream.write(json.dumps(annotated, ensure_ascii=False, separators=(",", ":")) + "\n")
                    tick = perf_counter()
                    write += tick - done
                    n += 1
        if n != manifest["counts"]["exported"]:
            raise ValueError(f"Read {n} rows, expected {manifest['counts']['exported']}")
        summary = dict(exportId=stem, records=n, counts=counts, sources=[
            {k:s[k] for k in ("network","internalSnapshotId")} for s in manifest["sources"]],
            inputMappingHash=manifest["mappingHash"], modelHashes=models, fasttext=version("fasttext"),
            thresholds={"language": LANG_THRESHOLD, "languageMargin": LANG_MARGIN, "role": ROLE_THRESHOLD,
                        "minAbstractWords": MIN_ABSTRACT_WORDS}, codeHash=sha(Path(__file__)), roleRulesHash=sha(Path(metadata_roles.__file__)),
            outputHash=sha(dest), seconds={"setupAndChecks": setup, "read": read, "annotate": classify,
                                           "serializeAndWrite": write, "total": perf_counter() - start})
        desc = Path(tmp) / report.name
        desc.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        # Link only to new names; avoid overwriting a concurrent run.
        final.hardlink_to(dest)
        try:
            report.hardlink_to(desc)
        except OSError:
            final.unlink()
            raise
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", nargs="+", type=Path)
    parser.add_argument("--language-model", required=True, type=Path)
    parser.add_argument("--role-model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    for package in args.packages:
        process(package, args.output, args.language_model, args.role_model)
