# -*- coding: utf-8 -*-
"""Unit and integration tests for Pravac A (Zero-Latency Speculative Execution and DSF)"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gama_decision import decision_l0 as D0


class SpeculativeL0Test(unittest.TestCase):
    def setUp(self):
        # Očistimo istoriju sesija prije svakog testa
        with D0._HISTORY_LOCK:
            D0._SESSION_HISTORY.clear()

    def test_dsf_explicit_file_path_extraction(self):
        """Testira izdvajanje eksplicitnih putanja fajlova."""
        res1 = D0.extract_dsf_slots("Molim te pročitaj datoteku /tmp/test_fajl.py")
        self.assertEqual(res1["filePath"], "/tmp/test_fajl.py")

        res2 = D0.extract_dsf_slots("Pogledaj 'src/components/button.ts'")
        self.assertEqual(res2["filePath"], "src/components/button.ts")

        res3 = D0.extract_dsf_slots("Otvori fajl config.json i provjeri postavke")
        self.assertEqual(res3["filePath"], "config.json")

    def test_dsf_explicit_sql_extraction(self):
        """Testira izdvajanje eksplicitnih SQL upita."""
        sql_query = "SELECT sifra, naziv, zaliha FROM customers WHERE zaliha > 0;"
        res = D0.extract_dsf_slots(f"Izvrši upit: {sql_query}")
        self.assertEqual(res["sql"], sql_query)

        # Markdown block
        res_md = D0.extract_dsf_slots("Pokreni ovo:\n```sql\nSELECT * FROM demo2;\n```")
        self.assertEqual(res_md["sql"], "SELECT * FROM demo2;")

    def test_dsf_anaphoric_file_path_resolution(self):
        """Testira anaforsko izdvajanje filePath parametara iz istorije sesije."""
        sid = "sess-12345"
        
        # 1. Prva poruka postavlja filePath
        D0.extract_dsf_slots("Otvori datoteku '/tmp/example.py'", sid=sid)
        
        # 2. Druga poruka se odnosi na nju anaforski ("u njemu")
        res2 = D0.extract_dsf_slots("Pronađi funkciju decide_request u njemu", sid=sid)
        self.assertEqual(res2["filePath"], "/tmp/example.py")

        # 3. Treća poruka se odnosi anaforski ("taj fajl")
        res3 = D0.extract_dsf_slots("Izmijeni taj fajl i dodaj komentar", sid=sid)
        self.assertEqual(res3["filePath"], "/tmp/example.py")

    def test_dsf_anaphoric_sql_resolution(self):
        """Testira anaforsko izdvajanje SQL upita iz istorije sesije."""
        sid = "sess-999"
        sql_query = "SELECT COUNT(*) FROM customers;"

        # 1. Prva poruka sadrži SQL upit
        D0.extract_dsf_slots(f"Izvrši: {sql_query}", sid=sid)

        # 2. Druga poruka se odnosi anaforski ("taj upit")
        res2 = D0.extract_dsf_slots("Objasni mi taj upit detaljno", sid=sid)
        self.assertEqual(res2["sql"], sql_query)

        # 3. Treća poruka se odnosi anaforski ("pokreni ga")
        res3 = D0.extract_dsf_slots("Sada ga pokreni ponovo", sid=sid)
        self.assertEqual(res3["sql"], sql_query)

    @unittest.skipUnless(
        os.environ.get("GAMA_SPECULATIVE_URL"),
        "set GAMA_SPECULATIVE_URL to run the live speculative-network test",
    )
    def test_live_speculative_evaluate_benign(self):
        """Optional live check against a configured speculative endpoint."""
        res_char = D0.speculative_evaluate(
            "Samo pročitaj podatke iz baze", timeout_s=1.0
        )
        if res_char is not None:
            self.assertIn(res_char, ("R", "D", "S", "I"))

    @patch("gama_decision.decision_l0.speculative_evaluate")
    def test_speculative_override_applied(self, mock_spec_eval):
        """Speculative safety override raises the tier when the classifier is riskier."""
        # Postavimo da spekulativni model prepozna "IRREVERSIBLE" ('I'),
        # dok bi naša lokalna heuristika za običan tekst rekla "READ"
        mock_spec_eval.return_value = "I"

        envelope = D0.decide_request("Neki običan tekst koji bi inače bio READ")
        
        # Provjeravamo da li je tier uspješno override-ovan na IRREVERSIBLE
        self.assertEqual(envelope["tier"], "IRREVERSIBLE")
        self.assertEqual(envelope["verdict"], "deny")
        self.assertEqual(envelope["speculative_execution"]["speculative_tier"], "IRREVERSIBLE")
        self.assertEqual(envelope["speculative_execution"]["speculative_match"], True)

    @patch("gama_decision.decision_l0.speculative_evaluate")
    def test_speculative_override_with_send(self, mock_spec_eval):
        """Testira override na SEND tier."""
        mock_spec_eval.return_value = "S"

        envelope = D0.decide_request("Neki upit za slanje")
        self.assertEqual(envelope["tier"], "SEND")
        self.assertEqual(envelope["verdict"], "ask")
        self.assertEqual(envelope["speculative_execution"]["speculative_tier"], "SEND")


if __name__ == "__main__":
    unittest.main()
