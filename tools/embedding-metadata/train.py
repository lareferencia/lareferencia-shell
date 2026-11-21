#!/usr/bin/env python3
"""Fit a pilot content classifier with weak labels and evaluate on separate OAI repositories."""
import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import islice
import json
from pathlib import Path
import random
import tempfile
from time import perf_counter

import fasttext
if __package__:
    from .postprocess import clean, LABEL, MIN_ABSTRACT_WORDS, ROLE_THRESHOLD, package_parts, read_rows, sha
else:
    from postprocess import clean, LABEL, MIN_ABSTRACT_WORDS, ROLE_THRESHOLD, package_parts, read_rows, sha


def weak_label(item):
    marker = LABEL.match(item["value"])
    qualifier = item.get("qualifier", "").casefold().split(".")[0]
    if marker:
        return "non_abstract" if marker[1].lower() == "fil" else "abstract"
    if qualifier in ("abstract", "abstractenglish", "resumen", "resumo"):
        return "abstract"
    if qualifier in ("provenance", "sponsorship", "tableofcontents", "uri"):
        return "non_abstract"
    return None


def repository(identifier):
    parts = identifier.split(":", 2)
    return parts[1].lower() if len(parts) == 3 and parts[0] == "oai" else None


def split(repository_id):
    return "holdout" if hashlib.sha256(repository_id.encode()).digest()[0] % 5 == 0 else "train"


def train(packages, output):
    start = perf_counter()
    rng = random.Random(27)
    buckets = defaultdict(set)
    exports = []
    for package in packages:
        manifest, parts = package_parts(package)
        exports.append(manifest["exportId"])
        for part in parts:
            for row in islice(read_rows(part), 2000):
                repo = repository(row["identifier"])
                if not repo:
                    continue
                for item in row["data"]["descriptions"]:
                    label = weak_label(item)
                    if label:
                        text = clean(item["value"]).casefold()
                        if text:
                            buckets[repo, label].add(text)
    pools = {"train": {}, "holdout": {}}
    repos = defaultdict(set)
    for (repo, label), values in sorted(buckets.items()):
        group = split(repo)
        repos[group].add(repo)
        pool = pools[group]
        for text in rng.sample(sorted(values), min(2000, len(values))):
            pool[text] = label if text not in pool or pool[text] == label else None
    training = [(t, k) for t, k in pools["train"].items() if k]
    # Do not let frequent affiliation templates determine the class prior.
    by_label = defaultdict(list)
    for text, label in training:
        by_label[label].append(text)
    if set(by_label) != {"abstract", "non_abstract"}:
        raise ValueError("Both classes are required")
    size = min(map(len, by_label.values()))
    training = [(t, k) for k, texts in by_label.items() for t in rng.sample(texts, size)]
    rng.shuffle(training)
    test = [(t,k) for t,k in pools["holdout"].items() if k and t not in pools["train"]]
    if not test:
        raise ValueError("Empty held-out set")
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(dir=output) as temp:
        data = Path(temp) / "training.txt"
        with data.open("w", encoding="utf-8") as f:
            for text, label in training:
                f.write(f"__label__{label} {text}\n")
        model = fasttext.train_supervised(input=str(data), dim=24, wordNgrams=2, bucket=100000,
                                          epoch=15, lr=0.7, minCount=2, thread=1, verbose=0)
        model.save_model(str(output / "role.bin"))
    results = defaultdict(Counter)
    for text, label in test:
        prediction, scores = model.predict(text)
        role = prediction[0].removeprefix("__label__")
        if scores[0] < ROLE_THRESHOLD or (role == "abstract" and len(text.split()) < MIN_ABSTRACT_WORDS):
            role = "uncertain"
        results[label][role] += 1
    summary = dict(exports=exports, trainPerLabel=size, holdout=results, repositories={
        name: sorted(values) for name, values in repos.items()}, seconds=perf_counter()-start, modelHash=sha(output/"role.bin"))
    (output/"training.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    print({k:v for k,v in summary.items() if k!="repositories"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    train(args.packages, args.output)
