"""Compose a single embedding input while preserving whole source occurrences."""


RECIPE = "title-abstract-keywords-combined-v1"


def english_first(items):
    present = ((index, item) for index, item in enumerate(items) if item["value"].strip())
    # A stable sort keeps source order within each language group.
    return sorted(present, key=lambda pair: pair[1]["detectedLanguage"] != "en")


def compose(data, annotated, *, include_provenance):
    titles = english_first(annotated["titles"])
    if not titles:
        return None, None

    # Sort using the original description indexes for the audit file.
    abstracts = [(i, item) for i, item in english_first(annotated["descriptions"])
                 if item["role"] == "abstract"]
    title = "\n\n".join(item["value"] for _, item in titles)
    body = "\n\n".join(item["value"] for _, item in abstracts) if abstracts else title
    keywords = [(i, item["value"]) for i, item in enumerate(data["keywords"]) if item["value"].strip()]
    if keywords:
        body += "\n\n" + ", ".join(value for _, value in keywords)

    origins = None
    if include_provenance:
        origins = {
            "titles": [i for i, _ in titles],
            "descriptions": [{"index": i, "selection": item.get("abstractSelection", "classified")}
                             for i, item in abstracts],
            "keywords": [i for i, _ in keywords],
        }
    return f"title: {title} | text: {body}", origins
