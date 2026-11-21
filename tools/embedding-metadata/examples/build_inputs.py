"""Example consumer: emit model input texts using only a delivered package and Python 3.11+."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path


def build_inputs(package, classified_only=False):
    manifest = json.loads((package / "manifest.json").read_bytes())
    if (manifest["status"], manifest["packageType"], manifest["contractVersion"]) != ("COMPLETE", "annotated-metadata", 1):
        raise ValueError("Expected a COMPLETE annotated-metadata v1 package")
    files = {entry["path"]: entry for entry in manifest["files"]}
    for name in manifest["parts"]:
        part = (package / name).resolve()
        if not part.is_relative_to(package.resolve()):
            raise ValueError(f"Part outside package: {name}")
        with part.open("rb") as raw:
            if "sha256:" + hashlib.file_digest(raw, "sha256").hexdigest() != files[name]["sha256"]:
                raise ValueError(f"Invalid checksum: {name}")
        with gzip.open(part, "rt", encoding="utf-8") as lines:
            for line in lines:
                row = json.loads(line)
                data = row["data"]
                if not any(title["value"].strip() for title in data["titles"]):
                    continue
                groups = defaultdict(list)
                for field in ("titles", "abstracts"):
                    for index, item in enumerate(data[field]):
                        if not item["value"].strip():
                            continue
                        if classified_only and item.get("selection") == "uncertain_fallback":
                            continue
                        language = item["language"]
                        # Each undetermined occurrence remains usable on its own.
                        key = (language, field, index) if language == "und" else (language,)
                        groups[key].append((field, index))
                by_language = defaultdict(list)
                for index, keyword in enumerate(data["keywords"]):
                    language = keyword.get("language")
                    if keyword.get("languageSource") and language and language != "und" and keyword["value"].strip():
                        by_language[language].append(("keywords", index))
                for key, refs in groups.items():
                    paragraphs = [data[field][i]["value"] for field, i in refs]
                    keywords = by_language.get(key[0], [])
                    if keywords:
                        paragraphs.append(", ".join(data[field][i]["value"] for field, i in keywords))
                    yield {"packageId": manifest["packageId"], "network": row["network"], "catalogId": row["catalogId"],
                           "language": key[0], "fields": refs + keywords,
                           "text": "\n\n".join(paragraphs)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--classified-only", action="store_true")
    args = parser.parse_args()
    for result in build_inputs(args.package, args.classified_only):
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
