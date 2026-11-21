"""Conservative, evidence-preserving refinements for short bibliographic statements."""
import re


# Only normalize full declared values. Keep every original literal for wider vocabularies.
TYPE_ALIASES = {
    "article": ("article", "artigo", "artículo", "journal article", "peer-reviewed article"),
    "masterThesis": ("masterthesis", "master thesis", "master's thesis", "dissertação de mestrado",
                     "tesis de maestría", "mémoire de master"),
    "doctoralThesis": ("doctoralthesis", "doctoral thesis", "phd thesis", "tesis doctoral",
                      "tese de doutorado", "thèse de doctorat"),
    "bachelorThesis": ("bachelorthesis", "bachelor thesis", "trabajo de grado - pregrado"),
    "conferenceObject": ("conferenceobject", "conference paper", "artigo em anais e proceedings"),
    "book": ("book", "libro", "livro", "livre"),
    "bookPart": ("bookpart", "book chapter", "capítulo de libro", "capítulo de livro", "chapitre de livre"),
    "report": ("report", "informe", "relatório", "rapport"),
    "dataset": ("dataset",), "other": ("other",),
}
DECLARED_TYPES = {alias: kind for kind, aliases in TYPE_ALIASES.items() for alias in aliases}
DEGREE_NOTES = [
    ("masterThesis", re.compile(r"^(?:dissertação\s*\(\s*mestrado\b|tesis\s*\(\s*maestría\b|master['’]s thesis\s*[-:(]|mémoire de master\s*[-:(])", re.I)),
    ("doctoralThesis", re.compile(r"^(?:tese\s*\(\s*doutorado\b|tesis\s*\(\s*doctorado\b|doctoral thesis\s*[-:(]|thèse de doctorat\s*[-:(])", re.I)),
    ("bachelorThesis", re.compile(r"^(?:trabalho de conclusão de curso|monografia)\s*\(\s*graduação\b", re.I)),
]
AFFILIATION = re.compile(r"^(?:universidad[e]?|universit[éy]|faculté|faculty|facultad|faculdade|department|département|departamento|instituto|laborat[oó]rio|laboratoire)\b", re.I)
EXPLICIT_AFFILIATION = re.compile(r"^\s*(?:fil|afiliaci[óo]n|afiliaç[ãa]o|affiliation)\s*:\s*", re.I)
# Funding cues describe a relationship. A standalone agency name supplies weaker evidence.
SUPPORT = re.compile(r"\b(?:financiad[oa]s?\s+(?:por|pel[ao])|financiamento\s+(?:da|do|de)|"
                     r"(?:com|con) (?:o |el )?(?:apoio|apoyo)(?: financier[oa]| financeiro)? (?:de|da|do|del|pela|pelo)|"
                     r"(?:funded|(?:financially )?supported) by|financ[ée]e? par|avec le soutien de)\s+", re.I)
AGENCY = re.compile(r"\b(?:CAPES|CNPq|FAPESP|FAPEMIG|FAPERJ|ANII|ANPCyT|CONICET)\b", re.I)
AGENCY_NAME = re.compile(r"^(?:Coordenação de Aperfeiçoamento de Pessoal de Nível Superior|"
                         r"Conselho Nacional de Desenvolvimento Científico e Tecnológico|"
                         r"Fundação de Amparo à Pesquisa do Estado de São Paulo)\b", re.I)
NEGATION = re.compile(r"\b(?:n[aã]o|no|not|never|aucun|sans|pas|sem|ning[uú]n)\b", re.I)
FUNDING_START = re.compile(r"^(?:(?:o presente |a presente |este |esta |el presente |la presente |ce |cet |cette |this )?(?:trabalho|estudo|pesquisa|trabajo|estudio|investigación|recherche|travail|projet|research|project|work|study)(?: (?:foi|fue|was|is|a été|est))?(?: (?:realizad[oa]|réalisé|conduzido|conducted))?)?$", re.I)
ORG_START = re.compile(r"^(?:secretar[ií]a|ministerio|ministério|ministry|ministère|fundación|fundação|fondation|"
                       r"foundation|ag[eê]ncia|agence|conse(?:jo|lho|il)|universi|institut|empresa |financiadora |international |national |european )", re.I)


def normalize_type(text):
    literal = " ".join(text.lower().split()).removeprefix("info:eu-repo/semantics/")
    return DECLARED_TYPES.get(literal)


def named_funders(fragment):
    # Return literal candidates rather than assigning an organization identifier.
    names = [m[0] for m in AGENCY.finditer(fragment)]
    if not names:
        name = re.split(r"(?:\s[-–—]\s|[;.!?]|\s+(?:através|por meio|under grant)\b)", fragment, maxsplit=1, flags=re.I)[0].strip(" :,")
        name = re.sub(r"^(?:la|el|las|los|le|les|the|a|o)\s+", "", name, flags=re.I)
        if name and len(name.split()) <= 24 and (ORG_START.match(name) or AGENCY_NAME.match(name)):
            names.append(name)
    return list(dict.fromkeys(names))


def affiliation_literal(text):
    """Keep the institutional phrase if a recognizable boundary follows an author name."""
    marker = EXPLICIT_AFFILIATION.match(text)
    if not marker:
        return text.strip()
    content = text[marker.end():].strip()
    for start in [0] + [m.end() for m in re.finditer(r"[.;]\s+", content)]:
        phrase = content[start:]
        if AFFILIATION.match(phrase) or ORG_START.match(phrase) or AGENCY.match(phrase):
            return phrase
    return None


def describe(item, baseline):
    """Return role, inferred document type and (literal, evidence) funder mentions."""
    text = " ".join(item["value"].split())
    qualifier = item.get("qualifier", "").lower().split(".")[0]
    fallback = "other" if baseline == "non_abstract" else baseline
    if not text:
        return "uncertain", None, []
    if EXPLICIT_AFFILIATION.match(text) or qualifier in {"affiliation", "affilliation", "affiliationunesp", "affiliationunifesp", "filiation"}:
        return "affiliation", None, []
    if len(text) <= 900:
        for kind, pattern in DEGREE_NOTES:
            if pattern.match(text):
                return "document_type", kind, []
    support = SUPPORT.search(text)
    mentions = []
    if support and not NEGATION.search(text[max(0, support.start()-45):support.start()]):
        mentions = [(name, "funding_statement") for name in named_funders(text[support.end():])]
        # Keep abstracts that also acknowledge support as eligible for embeddings.
        unambiguous = support[0].strip().lower() != "supported by" or bool(mentions)
        if unambiguous and len(text.split()) <= 55 and (support.start() == 0 or FUNDING_START.fullmatch(text[:support.start()].strip())):
            return "funding", None, mentions
    if qualifier in {"sponsorship", "funding", "funder"} and len(text.split()) <= 55:
        if text.casefold().strip(" .") in {"nenhum", "nenhuma", "none", "outro", "other", "n/a"}:
            return "other", None, []
        if NEGATION.search(text):
            return "uncertain", None, []
        if not mentions and not support:
            mentions = [(name, "sponsorship_field") for name in named_funders(text)]
        return "funding", None, mentions
    standalone = re.fullmatch(r"(CAPES|CNPq|FAPESP|FAPEMIG|FAPERJ|ANII|ANPCyT|CONICET)(?:\s*:\s*\d+)?", text, re.I)
    if standalone or (len(text.split()) <= 18 and AGENCY_NAME.match(text)):
        names = [standalone[1]] if standalone else named_funders(text)
        return "uncertain", None, [(name, "agency_mention") for name in names]
    if baseline == "non_abstract" and len(text.split()) <= 70 and AFFILIATION.match(text):
        return "affiliation", None, mentions
    return fallback, None, mentions
