"""Assign a language to each exported keyword without changing its source literal."""
from functools import lru_cache
import re
import unicodedata

from langcodes import Language, LanguageTagError


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


@lru_cache(maxsize=512)
def declared_code(raw):
    try:
        tag = Language.get(raw.strip().replace("_", "-"))
        code = tag.language
        if tag.is_valid() and code and code not in {"und", "mul", "zxx", "mis"} and not code.startswith("x-"):
            return code
    except LanguageTagError:
        pass
    return None


@lru_cache(maxsize=4096)
def phrase_matcher(term):
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")


def assign(item, passages, detect_language):
    value = normalized(item["value"])
    if not value:
        return "und", "undetermined"
    if item.get("language"):
        code = declared_code(item["language"])
        if code:
            return code, "declared"
    if not any(ch.isalpha() for ch in value):
        return "und", "undetermined"
    matches = {code for code, text in passages if phrase_matcher(value).search(text)}
    if len(matches) == 1:
        return matches.pop(), "record_text"
    if not matches:
        _, code = detect_language(value)
        if code:
            return code, "model"
    return "und", "undetermined"


def annotate_keywords(keywords, annotated, detect_language):
    passages = []
    for field in ("titles", "descriptions"):
        for item in annotated[field]:
            if field == "descriptions" and item.get("decision") != "abstract":
                continue
            code = item.get("detectedLanguageCode", item["detectedLanguage"])
            if code != "und":
                passages.append((code, normalized(item["value"])))
    for item in keywords:
        code, source = assign(item, passages, detect_language)
        result = dict(item, language=code, languageSource=source)
        if "language" in item:
            result["declaredLanguage"] = item["language"]
        yield result
