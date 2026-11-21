import unittest
from collections import Counter, defaultdict
from unittest.mock import Mock

from postprocess import Annotator, select_record_abstract


class AnnotatorTest(unittest.TestCase):
    def setUp(self):
        self.annotator = Annotator.__new__(Annotator)
        self.annotator.language = Mock()
        self.annotator.role = Mock()

    def test_missing_runner_up_or_empty_prediction_is_undetermined(self):
        for labels, scores in [([], []), (["__label__pt"], [0.99])]:
            self.annotator.detect_language.cache_clear()
            self.annotator.language.predict.return_value = (labels, scores)
            self.assertEqual(self.annotator.detect_language("dois ou três"), ("und", None))

    def test_original_occurrences_keep_indices_and_language(self):
        self.annotator.language.predict.return_value = (["__label__pt", "__label__es"], [.94, .05])
        self.annotator.role.predict.return_value = (["__label__abstract"], [.99])
        text = "Resumo: " + "Um texto muito interessante sobre a história das cidades ao longo do tempo."
        row = dict(catalogId="A", identifier="id", network="UY", metadataHash="hash", data={
            "titles": [{"value": "Um"}], "descriptions": [{"value": ""}, {"value": text, "language": "por"}]})
        result = self.annotator.annotate(row, "exp-test", defaultdict(Counter))
        self.assertEqual(result["embeddingGroups"], {"pt": {"titles": [], "descriptions": [1]}})
        self.assertEqual(result["descriptions"][0]["decision"], "uncertain")
        self.assertEqual(result["descriptions"][1]["value"], text)
        self.assertEqual(result["descriptions"][1]["language"], "por")
        self.assertEqual(result["descriptions"][1]["detectedLanguage"], "pt")
        self.assertNotIn("resumo:", self.annotator.role.predict.call_args.args[0])

    def test_metadata_roles_keep_evidence_and_group_only_abstracts(self):
        self.annotator.language.predict.return_value = (["__label__fr", "__label__es"], [.95, .03])
        self.annotator.role.predict.return_value = (["__label__abstract"], [.99])
        text = "Ce travail analyse les résultats de la recherche sur les pratiques de lecture en français."
        values = [text, "O presente trabalho foi realizado com apoio de Secretaria de Saúde do Distrito Federal (SES-DF) - Código 001.",
                  "Fil: Pardo, Ana M. Universidad de Buenos Aires; Argentina", "Dissertação (mestrado) - Universidade Federal", "CAPES"]
        row = dict(network="BR", catalogId="01", identifier="oai:test", metadataHash="hash", data={
            "titles":[{"value": text}], "descriptions":[{"value": v} for v in values],
            "types":[{"value":"info:eu-repo/semantics/publishedVersion"}, {"value":"info:eu-repo/semantics/article"}],
            "funders":[{"value":"Agence nationale de la recherche"}]})
        result = self.annotator.annotate(row, "exp", defaultdict(Counter))
        self.assertEqual(result["titles"][0]["detectedLanguage"], "fr")
        self.assertEqual(result["embeddingGroups"]["fr"], {"titles":[0], "descriptions":[0]})
        self.assertEqual([d["role"] for d in result["descriptions"]], ["abstract","funding","affiliation","document_type","uncertain"])
        self.assertEqual(result["affiliations"][0], {"field":"descriptions","index":2,"literal":"Universidad de Buenos Aires; Argentina"})
        self.assertEqual(result["documentTypes"], [{"type":"article","field":"types","index":1}])
        self.assertEqual([f["evidence"] for f in result["funders"]], ["declared","funding_statement","agency_mention"])
        self.assertEqual(result["funders"][1]["name"], "Secretaria de Saúde do Distrito Federal (SES-DF)")
        del row["data"]["types"]
        self.assertEqual(self.annotator.annotate(row, "exp", defaultdict(Counter))["documentTypes"][0]["type"], "masterThesis")

    def test_mixed_prose_and_negation(self):
        from metadata_roles import describe
        mixed = "This study investigates crop growth using three field trials. This work was funded by CAPES."
        self.assertEqual(describe({"value": mixed}, "abstract"), ("abstract", None, [("CAPES","funding_statement")]))
        self.assertFalse(describe({"value":"This work was not funded by CAPES."}, "uncertain")[2])
        self.assertEqual(describe({"value":"Esta dissertação apresenta uma análise econômica do comércio."}, "abstract")[0], "abstract")

    def test_selects_one_longest_uncertain_description_and_keeps_original_decision(self):
        self.annotator.language.predict.return_value = (["__label__it", "__label__es"], [.94, .05])
        self.annotator.role.predict.return_value = (["__label__abstract"], [.55])
        values = ["Tre parole diverse", "  La ricerca sulle biblioteche.  ", "La ricerca sulle biblioteche.",
                  "Fil: Julia Santos. Universidad de Buenos Aires, Argentina"]
        row = dict(network="AR", catalogId="1", identifier="test", metadataHash="h", data={
            "titles": [{"value": "Le biblioteche italiane"}], "descriptions": [{"value": v} for v in values]})
        counts = defaultdict(Counter)
        result = self.annotator.annotate(row, "exp", counts)
        self.assertEqual([d["role"] for d in result["descriptions"]], ["uncertain", "abstract", "uncertain", "affiliation"])
        chosen = result["descriptions"][1]
        self.assertEqual((chosen["value"], chosen["decision"], chosen["abstractSelection"]),
                         (values[1], "uncertain", "uncertain_fallback"))
        self.assertEqual(select_record_abstract(result), "uncertain_fallback")
        self.assertEqual(result["embeddingGroups"], {"it": {"titles": [0], "descriptions": [1]}})
        self.assertEqual(counts["records.abstract"], {"uncertain_fallback": 1})
        self.assertEqual(counts["descriptions.decision"], {"uncertain": 3, "non_abstract": 1})
        self.assertEqual(counts["descriptions.role"], {"uncertain": 2, "abstract": 1, "affiliation": 1})

    def test_existing_abstract_in_any_language_prevents_fallback(self):
        result = {"descriptions": [{"role": "uncertain", "value": "A possible English abstract", "detectedLanguage": "en"},
                                   {"role": "abstract", "value": "Resumen", "detectedLanguage": "und"}],
                  "embeddingGroups": {}}
        self.assertEqual(select_record_abstract(result), "classified")
        self.assertEqual(result["descriptions"][0]["role"], "uncertain")
        self.assertEqual(result["embeddingGroups"], {})

    def test_one_undetermined_candidate_and_empty_or_unrelated_descriptions(self):
        row = dict(network="AR", catalogId="1", identifier="test", metadataHash="h")
        counts = defaultdict(Counter)
        for values in [[], [" \t", "Resumen: "], ["Fil: A. Universidad de Buenos Aires"], ["Breve"]]:
            self.annotator.role.predict.return_value = ([], [])
            self.annotator.language.predict.return_value = ([], [])
            result = self.annotator.annotate(dict(row, data={"descriptions": [{"value": v} for v in values]}),
                                             "exp", counts)
            self.assertEqual(result["embeddingGroups"], {})
        self.assertEqual(result["descriptions"][0]["role"], "abstract")
        self.assertEqual(result["descriptions"][0]["detectedLanguage"], "und")
        self.assertEqual(counts["records.abstract"], {"missing": 3, "uncertain_fallback": 1})

    def test_only_nonblank_title_is_required_for_coverage(self):
        counts = defaultdict(Counter)
        row = dict(network="MX", catalogId="id", identifier="oai:test", metadataHash="hash")
        for data in ({}, {"titles": [{"value": " \t"}]}, {"titles": [{"value": ""}, {"value": "Sol"}]}):
            result = self.annotator.annotate(dict(row, data=data), "exp", counts)
            self.assertEqual(result["descriptions"], [])
        self.assertEqual(result["titles"][1]["detectedLanguage"], "und")
        self.assertEqual(counts["records.title"], {"present": 1, "missing": 2})
