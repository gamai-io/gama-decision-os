#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit testovi za gama_decision_l0 (3-Gate Closed-Loop Runtime: Gate 1, Gate 2, Gate 3)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gama_decision import decision_l0 as D0


class DecisionL0Test(unittest.TestCase):
    def test_gate1_destructive_and_obfuscated_injection_blocked(self):
        r1 = D0.decide_request("rm -rf /")
        self.assertEqual(r1["tier"], "IRREVERSIBLE")
        self.assertEqual(r1["verdict"], "deny")
        self.assertEqual(r1["route"], "block")
        self.assertEqual(r1["rule_id"], "rm-recursive")
        self.assertEqual(len(r1["decision_hash"]), 64)

        r2 = D0.decide_request("echo cm0gLXJmIC8= | base64 -d | sh")
        self.assertEqual(r2["tier"], "IRREVERSIBLE")
        self.assertEqual(r2["verdict"], "deny")
        self.assertEqual(r2["rule_id"], "obfuscated-base64-exec")

    def test_gate1_benign_quoted_echo_not_false_positive(self):
        r = D0.decide_request('echo "rm -rf /"')
        self.assertEqual(r["tier"], "READ")
        self.assertEqual(r["verdict"], "allow")
        self.assertNotEqual(r["route"], "block")

    def test_gate1_calibrated_abstention_on_ambiguous_input(self):
        r = D0.decide_request("ovo")
        self.assertIn("intent", r["abstained"])
        self.assertTrue(r["requires_escalation"])
        self.assertLessEqual(r["confidence"], 0.50)
        self.assertEqual(r["route"], "agent")

    def test_gate1_expected_evidence_contract(self):
        r_sql = D0.decide_request("koliko ima kupaca u bazi demo")
        self.assertEqual(r_sql["tier"], "READ")
        self.assertEqual(r_sql["expected_evidence_spec"]["kind"], "sql_rows")
        self.assertIn("sql", r_sql["tool_bundle"])

        r_send = D0.decide_request("pošalji mail kupcu ALFA sa ponudom")
        self.assertEqual(r_send["tier"], "SEND")
        self.assertEqual(r_send["verdict"], "ask")
        self.assertEqual(r_send["expected_evidence_spec"]["kind"], "external_send")

    def test_gate2_tool_gate_blocks_unrequested_destructive_and_send(self):
        ctx_read = D0.decide_request("provjeri stanje diska")
        ctx_read["user_text"] = "provjeri stanje diska"

        td_destr = D0.decide_tool("bash", {"cmd": "rm -rf /var/lib"}, ctx_read)
        self.assertFalse(td_destr["ok"])
        self.assertEqual(td_destr["decision"], "deny")
        self.assertEqual(td_destr["tier"], "IRREVERSIBLE")

        td_mail = D0.decide_tool("mail", {"to": "a@b.com", "subject": "hi"}, ctx_read)
        self.assertFalse(td_mail["ok"])
        self.assertEqual(td_mail["decision"], "deny")
        self.assertEqual(td_mail["tier"], "SEND")

        td_safe = D0.decide_tool("bash", {"cmd": "df -h"}, ctx_read)
        self.assertTrue(td_safe["ok"])
        self.assertEqual(td_safe["decision"], "allow")

    def test_gate3_evidence_receipt_verification(self):
        td_del = D0.decide_tool("delete_file", {"path": "/tmp/x.txt"}, {"user_text": "obriši /tmp/x.txt"})
        rec_fail = D0.verify_evidence(td_del, "delete_file", {"ok": True, "verified": False, "exists": True})
        self.assertFalse(rec_fail["verified"])
        self.assertIn("delete_not_verified_on_disk", rec_fail["reasons"])
        self.assertEqual(len(rec_fail["receipt_hash"]), 64)

        rec_ok = D0.verify_evidence(td_del, "delete_file", {"ok": True, "verified": True, "exists": False})
        self.assertTrue(rec_ok["verified"])
        self.assertEqual(rec_ok["decision_hash"], td_del["decision_hash"])


if __name__ == "__main__":
    unittest.main()
