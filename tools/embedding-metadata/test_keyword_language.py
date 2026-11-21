from unittest import TestCase
from unittest.mock import Mock

from lareferencia_embedding_metadata.keyword_language import annotate_keywords


class KeywordLanguageTest(TestCase):
    def test_short_keywords_match_only_one_languages_whole_phrase(self):
        row = {"titles": [{"value": "Las heridas y el ADN", "detectedLanguage": "es"},
                          {"value": "Wounds and ADN", "detectedLanguage": "en"}],
               "descriptions": [{"value": "Análisis de los casos", "role": "abstract", "decision": "abstract",
                                 "detectedLanguage": "es"},
                                {"value": "traumatisms", "role": "abstract", "decision": "uncertain",
                                 "detectedLanguage": "en"}]}
        detect = Mock(return_value=("und", None))
        items = [{"value": v} for v in ("heridas", "WOUNDS", "ADN", "herida", "Ana\u0301lisis de", "traumatisms")]
        result = list(annotate_keywords(items, row, detect))
        self.assertEqual([v["language"] for v in result], ["es","en","und","und","es","und"])
        self.assertEqual([v["value"] for v in result], [v["value"] for v in items])
        self.assertNotIn(("adn",), [c.args for c in detect.call_args_list])

    def test_source_tags_model_language_and_ambiguous_qualifiers(self):
        row = {"titles": [{"value": "children and health", "detectedLanguage": "en"}], "descriptions": []}
        items = [{"value":"children", "language":"pt_BR", "qualifier":"es"},
                 {"value":"children", "qualifier":"es"}, {"value":"la santé publique", "language":"ZZ"},
                 {"value":"  ", "language":"es"}, {"value":"123"}, {"value":"otra", "language":"spa"}]
        result = list(annotate_keywords(items, row, lambda _: ("other","fr")))
        self.assertEqual([(v["language"],v["languageSource"]) for v in result],
                         [("pt","declared"),("en","record_text"),("fr","model"),("und","undetermined"),
                          ("und","undetermined"),("es","declared")])
        self.assertEqual(result[0]["declaredLanguage"],"pt_BR")
        self.assertEqual(result[1]["qualifier"],"es")
        self.assertEqual(result[2]["declaredLanguage"],"ZZ")
