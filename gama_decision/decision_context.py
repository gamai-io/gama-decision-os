# -*- coding: utf-8 -*-
"""
decision_context.py — Dynamic repository/context compression for GAMA Decision OS.

The public core ships a small, dependency-free ranker: it scans text files under
``root_dir`` and ranks them against the decision envelope (intent, domain, tool
bundle) and the caller's query. If the optional ``gama_repomap3`` module is
installed, it is used instead for a richer PageRank-based map.

The return value is a stable dict with the keys ``ok``, ``formatted_context``,
``tokens_used``, ``files_count`` and (optionally) ``raw_response``.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

try:  # optional richer backend
    import gama_repomap3  # type: ignore
except Exception:  # pragma: no cover - expected in the public core
    gama_repomap3 = None

_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}
_TEXT_EXT = {
    ".py",
    ".md",
    ".txt",
    ".rst",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".yml",
    ".yaml",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".sh",
}


def _query_from_envelope(
    envelope: Dict[str, Any], user_text: Optional[str]
) -> str:
    parts: List[str] = []
    if user_text:
        parts.append(user_text)
    for key in ("intent", "domain"):
        value = envelope.get(key)
        if value:
            parts.append(str(value))
    bundle = envelope.get("tool_bundle")
    if bundle:
        if isinstance(bundle, (list, tuple, set)):
            parts.extend(str(item) for item in bundle)
        else:
            parts.append(str(bundle))
    return " ".join(parts)


def _fallback_rank(
    root_dir: str, query: str, budget_tokens: int
) -> Dict[str, Any]:
    terms = [t.lower() for t in query.split() if len(t) > 1]
    scored: List[Tuple[float, str, int]] = []
    root_dir = os.path.abspath(root_dir)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            if os.path.splitext(name)[1].lower() not in _TEXT_EXT:
                continue
            path = os.path.join(dirpath, name)
            try:
                if os.path.getsize(path) > 512 * 1024:
                    continue
                with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                    text = handle.read()
            except (OSError, UnicodeError):
                continue
            rel = os.path.relpath(path, root_dir)
            haystack = (rel + "\n" + text).lower()
            score = 0.0
            for term in terms:
                score += haystack.count(term)
            if score <= 0:
                continue
            # Prefer smaller, focused files when scores tie.
            score += 1.0 / (1.0 + len(text) / 4000.0)
            scored.append((score, rel, len(text)))

    scored.sort(key=lambda item: (-item[0], item[1]))
    max_score = scored[0][0] if scored else 1.0

    lines = [
        "=== COMPRESSED REPO SCHEMA ===",
        f"Query-intent context: {query}",
        f"Budget limit: {budget_tokens} tokens",
        "",
    ]
    used_tokens = 0
    files_count = 0
    for score, rel, size in scored:
        block = [f"File: {rel} (rank={score / max_score:.4f})", ""]
        block_tokens = max(1, sum(len(line) for line in block) // 4)
        if used_tokens + block_tokens > budget_tokens and files_count > 0:
            break
        lines.extend(block)
        used_tokens += block_tokens
        files_count += 1

    return {
        "ok": True,
        "formatted_context": "\n".join(lines),
        "tokens_used": used_tokens,
        "files_count": files_count,
        "backend": "fallback",
    }


def extract_compressed_context(
    envelope: Dict[str, Any],
    root_dir: str = ".",
    budget_tokens: int = 4000,
    user_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    For a DecisionEnvelope and optional user text, find the most relevant files
    under ``root_dir`` and compress them into a prompt-friendly block.
    """
    query = _query_from_envelope(envelope, user_text)

    if gama_repomap3 is not None:
        try:
            res = gama_repomap3.build_map(
                root=root_dir,
                query=query,
                budget=budget_tokens,
            )
        except Exception:
            res = None
        if res and res.get("ok"):
            lines = [
                "=== COMPRESSED REPO SCHEMA ===",
                f"Query-intent context: {query}",
                f"Budget limit: {budget_tokens} tokens",
                "",
            ]
            for entry in res.get("files", []):
                lines.append(f"File: {entry['path']} (rank={entry['rank']:.4f})")
                for symbol in entry.get("symbols", []):
                    lines.append(
                        f"  {symbol['kind']} {symbol['name']} L{symbol['line']}"
                    )
                lines.append("")
            return {
                "ok": True,
                "formatted_context": "\n".join(lines),
                "tokens_used": res.get("total_tokens", 0),
                "files_count": len(res.get("files", [])),
                "raw_response": res,
                "backend": "repomap3",
            }

    return _fallback_rank(root_dir, query, budget_tokens)
