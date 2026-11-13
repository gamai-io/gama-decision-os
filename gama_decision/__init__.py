# -*- coding: utf-8 -*-
"""GAMA Decision OS — Apache-2.0 core.

Three-gate decision runtime:
  Gate 1  decide_request()  pre-action decision envelope (tier, verdict, route)
  Gate 2  decide_tool()     in-action tool gate (allow / sandbox / ask / deny)
  Gate 3  verify_evidence() post-action evidence receipt (proof of success)
"""
from .decision_l0 import (
    apply_prefix_stable_v1,
    decide_request,
    decide_tool,
    enabled,
    extract_dsf_slots,
    speculative_evaluate,
    status,
    verify_evidence,
)
from .decision_context import extract_compressed_context

__version__ = "1.2.2"

__all__ = [
    "decide_request",
    "decide_tool",
    "verify_evidence",
    "extract_dsf_slots",
    "speculative_evaluate",
    "apply_prefix_stable_v1",
    "extract_compressed_context",
    "enabled",
    "status",
    "__version__",
]
