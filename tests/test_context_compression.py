# -*- coding: utf-8 -*-
"""
test_context_compression.py — Unit testovi za Dynamic Schema/Context Compression i KV-cache stabilnost
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gama_decision import decision_l0 as D0
from gama_decision import decision_context as DC


class ContextCompressionTest(unittest.TestCase):
    def setUp(self):
        # Definišemo dummy test root direktorij
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_extract_compressed_context_basic(self):
        # Kreiramo test envelope
        envelope = {
            "intent": "trazi_kod",
            "domain": "code",
            "tool_bundle": ["fs_read", "fs_grep"]
        }
        res = DC.extract_compressed_context(
            envelope=envelope,
            root_dir=self.root_dir,
            budget_tokens=2000,
            user_text="kako se startuje server"
        )
        self.assertTrue(res["ok"])
        self.assertIn("=== COMPRESSED REPO SCHEMA ===", res["formatted_context"])
        self.assertIn("kako se startuje server", res["formatted_context"])
        self.assertGreater(res["tokens_used"], 0)
        self.assertGreater(res["files_count"], 0)

    def test_apply_prefix_stable_v1_sorting_and_shifting(self):
        # 1. Testiranje sortiranja šema
        schemas = [
            {"function": {"name": "write_file"}},
            {"function": {"name": "fs_read"}},
            {"function": {"name": "apply_patch"}},
        ]
        system_prompt = (
            "You are a GAMA agent.\n"
            "Today's date: Friday, Nov 13, 2026\n"
            "Current time: 14:30\n"
            "Session ID: test-sid-123\n"
            "Do your job carefully."
        )

        sorted_schemas, cleaned_prompt = D0.apply_prefix_stable_v1(
            schemas=schemas,
            system_prompt=system_prompt,
            dynamic_vars={"workflow_step": "verification"}
        )

        # Provjera da li su šeme sortirane abecedno po imenu
        names = [s["function"]["name"] for s in sorted_schemas]
        self.assertEqual(names, ["apply_patch", "fs_read", "write_file"])

        # Provjera da li su dinamičke varijable uklonjene iz glavnog prompta i prebačene na kraj
        self.assertNotIn("Today's date:", cleaned_prompt.split("=== DYNAMIC CONTEXT")[0])
        self.assertNotIn("Current time:", cleaned_prompt.split("=== DYNAMIC CONTEXT")[0])
        self.assertNotIn("Session ID:", cleaned_prompt.split("=== DYNAMIC CONTEXT")[0])

        self.assertIn("=== DYNAMIC CONTEXT (KV-CACHE STABLE) ===", cleaned_prompt)
        self.assertIn("Today's date: Friday, Nov 13, 2026", cleaned_prompt)
        self.assertIn("Current time: 14:30", cleaned_prompt)
        self.assertIn("Session ID: test-sid-123", cleaned_prompt)
        self.assertIn("workflow_step: verification", cleaned_prompt)

    def test_read_tier_blocks_mutating_tools(self):
        # Kreiramo req_ctx sa tier=READ
        req_ctx = {
            "tier": "READ",
            "decision_hash": "dummyhash123",
            "user_text": "pročitaj log fajl"
        }

        # Pokušaj poziva mutating alata "write_file" treba biti blokiran
        td_write = D0.decide_tool("write_file", {"filePath": "test.txt", "content": "hi"}, req_ctx)
        self.assertFalse(td_write["ok"])
        self.assertEqual(td_write["decision"], "deny")
        self.assertEqual(td_write["tier"], "READ")
        self.assertIn("vrši mutaciju što je zabranjeno u READ tieru", td_write["reason"])

        # READ_ONLY_SHELL_V1: read-only shell komanda (ls, df, cat) je dozvoljena u READ tieru
        td_bash_ro = D0.decide_tool("bash", {"command": "ls -la"}, req_ctx)
        self.assertTrue(td_bash_ro["ok"])
        self.assertEqual(td_bash_ro["decision"], "allow")

        # Mutirajuća shell komanda (touch) ostaje blokirana u READ tieru
        td_bash_mut = D0.decide_tool("bash", {"command": "touch /tmp/x"}, req_ctx)
        self.assertFalse(td_bash_mut["ok"])
        self.assertEqual(td_bash_mut["decision"], "deny")
        self.assertEqual(td_bash_mut["tier"], "READ")

        # Poziv read-only alata "gama_sql" treba biti dozvoljen
        td_sql = D0.decide_tool("gama_sql", {"query": "SELECT 1"}, req_ctx)
        self.assertTrue(td_sql["ok"])
        self.assertEqual(td_sql["decision"], "allow")


if __name__ == "__main__":
    unittest.main()
