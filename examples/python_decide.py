#!/usr/bin/env python3
"""Call the three gates directly from Python."""
from gama_decision import decide_request, decide_tool, verify_evidence

envelope = decide_request("delete /tmp/report.txt")
print("Gate 1:", envelope["tier"], envelope["verdict"], envelope["expected_evidence_spec"])

decision = decide_tool("delete_file", {"path": "/tmp/report.txt"}, envelope)
print("Gate 2:", decision["decision"], decision["reason"])

receipt = verify_evidence(
    decision,
    "delete_file",
    {"ok": True, "verified": True, "exists": False},
)
print("Gate 3:", receipt["verified"], receipt["receipt_hash"])
