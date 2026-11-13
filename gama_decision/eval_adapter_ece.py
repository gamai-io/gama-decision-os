#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluacija LoRA adaptera: ECE + Brier + ASCII reliability diagram.

Ucitava base model i (opciono) LoRA adapter, racuna log-probability chosen
i rejected odgovora iz DPO dataseta, pretvara marginu u vjerovatnocu i
mjeri kalibraciju preko `calibration_evaluator.py`.

`--dry-run` radi bez GPU/modela: koristi sinteticke, deterministicke
predikcije (overconfident na near-miss kategorijama) da se cijeli pipeline
moze testirati odmah.

Primjer:
    python3 eval_adapter_ece.py --dry-run --dataset dpo_near_miss.jsonl
    GAMA_LORA_ADAPTER=/path/adapter python3 eval_adapter_ece.py \
        --base-model /path/base --dataset dpo_near_miss.jsonl

Napomena: u realnom rezimu `local_files_only=True` je default; za download
postavi GAMA_EVAL_ALLOW_DOWNLOAD=1.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import random
import sys
import time
from contextlib import redirect_stdout

try:  # package import
    from .calibration_evaluator import (
        calculate_brier_score,
        calculate_ece,
        print_ascii_reliability_diagram,
    )
except ImportError:  # pragma: no cover - direct script execution
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from calibration_evaluator import (
        calculate_brier_score,
        calculate_ece,
        print_ascii_reliability_diagram,
    )

DEFAULT_DATASET = os.environ.get("GAMA_DPO_DATASET", "dpo_near_miss.jsonl")
DEFAULT_OUTPUT = os.environ.get("GAMA_ECE_OUTPUT", "eval_adapter_ece.json")
DEFAULT_CALIB_DIR = os.environ.get("GAMA_CALIB_DIR", "models/calibration")
DEFAULT_BINS = 10
DEFAULT_TEMP_MIN = 0.05
DEFAULT_TEMP_MAX = 5.0
DEFAULT_TEMP_GRID = 2000
DEFAULT_CALIB_FRAC = 0.8

_FALLBACK_CASES = [
    {"category": "status_flip", "tool": "sql"},
    {"category": "status_flip", "tool": "fs_read"},
    {"category": "sql_wrong_table", "tool": "sql"},
    {"category": "sql_wrong_column", "tool": "sql"},
    {"category": "path_lookalike", "tool": "fs_read"},
    {"category": "numeric_hallucination", "tool": "sql"},
    {"category": "false_success_ack", "tool": "run"},
] * 3


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
def load_pairs(path: str | None, limit: int | None = None) -> list[dict]:
    """Ucitaj JSONL DPO parove; vrati [] ako fajl ne postoji."""
    if not path or not os.path.exists(path):
        return []
    pairs = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                pairs.append(json.loads(line))
            except ValueError:
                continue
            if limit and len(pairs) >= limit:
                break
    return pairs


def _fallback_pairs() -> list[dict]:
    return [
        {
            "prompt": f"fallback prompt {idx}",
            "chosen": "chosen",
            "rejected": "rejected",
            "synthetic": True,
            "metadata": dict(case),
        }
        for idx, case in enumerate(_FALLBACK_CASES)
    ]


# ---------------------------------------------------------------------------
# Confidence from logits
# ---------------------------------------------------------------------------
def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def pair_logprobs_to_confidence(
    logprob_chosen: float, logprob_rejected: float
) -> tuple[float, float]:
    """Softmax nad dva length-normalized log-probability-ja.

    Vraca (p_chosen, p_rejected); p_chosen + p_rejected = 1.
    """
    finite_c = math.isfinite(logprob_chosen)
    finite_r = math.isfinite(logprob_rejected)
    if not finite_c and not finite_r:
        return 0.5, 0.5
    if not finite_c:
        return 0.0, 1.0
    if not finite_r:
        return 1.0, 0.0
    p_chosen = _sigmoid(logprob_chosen - logprob_rejected)
    return p_chosen, 1.0 - p_chosen


def _sequence_logprob(model, tokenizer, prompt: str, response: str, max_length: int = 2048):
    """Length-normalized log-probability response continuationa."""
    import torch

    prompt_ids = tokenizer(prompt, return_tensors="pt").input_ids
    encoded = tokenizer(
        prompt + response,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )
    input_ids = encoded.input_ids
    labels = input_ids.clone()
    prompt_len = min(prompt_ids.shape[1], labels.shape[1])
    labels[:, :prompt_len] = -100

    device = getattr(model, "device", None)
    if device is None:
        device = next(model.parameters()).device
    input_ids = input_ids.to(device)
    attention_mask = encoded.attention_mask.to(device)
    labels = labels.to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)

    logits = outputs.logits[:, :-1, :].float()
    targets = labels[:, 1:]
    mask = targets != -100
    if int(mask.sum().item()) == 0:
        return float("-inf")
    log_probs = torch.log_softmax(logits, dim=-1)
    gathered = log_probs.gather(-1, targets.clamp(min=0).unsqueeze(-1)).squeeze(-1)
    return float((gathered * mask).sum().item() / mask.sum().item())


def load_model_bundle(base_model: str | None, adapter: str | None):
    """Vrati (bundle, error). Ne importuje torch dok se stvarno ne pozove."""
    if not base_model:
        return None, "base model nije zadat (--base-model ili GAMA_BASE_MODEL)"
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:  # pragma: no cover - zavisi od okruzenja
        return None, f"training dependencies nisu instalirane: {exc}"

    allow_download = os.environ.get("GAMA_EVAL_ALLOW_DOWNLOAD") == "1"
    load_kwargs = {"local_files_only": not allow_download}
    try:
        tokenizer = AutoTokenizer.from_pretrained(base_model, **load_kwargs)
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            device_map="auto",
            torch_dtype="auto",
            **load_kwargs,
        )
    except Exception as exc:  # pragma: no cover - teski model
        return None, f"base model load nije uspio: {exc}"

    if adapter:
        if not os.path.exists(adapter):
            return None, f"adapter nije nadjen: {adapter}"
        try:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, adapter)
        except Exception as exc:  # pragma: no cover - teski model
            return None, f"adapter load nije uspio: {exc}"

    model.eval()
    return {
        "torch": torch,
        "tokenizer": tokenizer,
        "model": model,
        "base_model": base_model,
        "adapter": adapter,
    }, None


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------
def _clamp_prob(value: float) -> float:
    return max(0.02, min(0.98, value))


def _jitter(seed: int, label: str, scale: float = 0.06) -> float:
    digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()[:8]
    unit = int(digest, 16) / 0xFFFFFFFF
    return (unit - 0.5) * 2.0 * scale


def _dry_run_predictions(pairs: list[dict], seed: int = 7) -> list[dict]:
    """Deterministicke sinteticke predikcije: model je preuvjeren na rejected."""
    predictions = []
    for idx, pair in enumerate(pairs):
        meta = pair.get("metadata") or {}
        category = meta.get("category", "unknown")
        if category == "status_flip":
            chosen_conf, rejected_conf = 0.95, 0.08
        elif category in ("sql_wrong_table", "sql_wrong_column"):
            chosen_conf, rejected_conf = 0.78, 0.86
        elif category == "path_lookalike":
            chosen_conf, rejected_conf = 0.74, 0.88
        elif category == "numeric_hallucination":
            chosen_conf, rejected_conf = 0.70, 0.91
        elif category == "false_success_ack":
            chosen_conf, rejected_conf = 0.62, 0.94
        else:
            chosen_conf, rejected_conf = 0.75, 0.80

        chosen_conf = _clamp_prob(chosen_conf + _jitter(seed, f"{idx}:chosen"))
        rejected_conf = _clamp_prob(rejected_conf + _jitter(seed, f"{idx}:rejected"))
        predictions.append(
            {
                "prob": round(chosen_conf, 6),
                "label": 1,
                "side": "chosen",
                "pair_index": idx,
                "tool": meta.get("tool", "unknown"),
                "category": category,
            }
        )
        predictions.append(
            {
                "prob": round(rejected_conf, 6),
                "label": 0,
                "side": "rejected",
                "pair_index": idx,
                "tool": meta.get("tool", "unknown"),
                "category": category,
            }
        )
    return predictions


def _real_predictions(
    pairs: list[dict],
    bundle: dict,
    max_length: int = 2048,
) -> tuple[list[dict], int]:
    tokenizer = bundle["tokenizer"]
    model = bundle["model"]
    predictions = []
    skipped = 0
    for idx, pair in enumerate(pairs):
        meta = pair.get("metadata") or {}
        prompt = pair.get("prompt", "")
        chosen = pair.get("chosen", "")
        rejected = pair.get("rejected", "")
        lp_chosen = _sequence_logprob(model, tokenizer, prompt, chosen, max_length)
        lp_rejected = _sequence_logprob(model, tokenizer, prompt, rejected, max_length)
        if not math.isfinite(lp_chosen) or not math.isfinite(lp_rejected):
            skipped += 1
            continue
        p_chosen, p_rejected = pair_logprobs_to_confidence(lp_chosen, lp_rejected)
        predictions.append(
            {
                "prob": round(p_chosen, 6),
                "label": 1,
                "side": "chosen",
                "pair_index": idx,
                "tool": meta.get("tool", "unknown"),
                "category": meta.get("category", "unknown"),
                "logprob": round(lp_chosen, 6),
            }
        )
        predictions.append(
            {
                "prob": round(p_rejected, 6),
                "label": 0,
                "side": "rejected",
                "pair_index": idx,
                "tool": meta.get("tool", "unknown"),
                "category": meta.get("category", "unknown"),
                "logprob": round(lp_rejected, 6),
            }
        )
    return predictions, skipped


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def _metrics(predictions: list[dict], bins: int) -> dict:
    probabilities = [float(p["prob"]) for p in predictions]
    labels = [int(p["label"]) for p in predictions]
    ece, bin_details = calculate_ece(probabilities, labels, bins)
    brier = calculate_brier_score(probabilities, labels)
    total = len(predictions)
    accuracy = (
        sum(
            1
            for prob, label in zip(probabilities, labels, strict=True)
            if (prob >= 0.5) == bool(label)
        )
        / total
        if total
        else 0.0
    )
    mean_confidence = sum(probabilities) / total if total else 0.0
    return {
        "n_predictions": total,
        "bins": bins,
        "ece": round(ece, 6),
        "brier": round(brier, 6),
        "accuracy": round(accuracy, 6),
        "mean_confidence": round(mean_confidence, 6),
        "bin_details": {str(key): value for key, value in bin_details.items()},
    }


def _reliability_diagram(bin_details: dict, bins: int) -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_ascii_reliability_diagram(
            {int(key): value for key, value in bin_details.items()}, bins
        )
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Temperature scaling (calibration)
# ---------------------------------------------------------------------------
def _logit(prob: float) -> float:
    """logit(p) = log(p / (1 - p)); valjano za binarni chosen/rejected slucaj."""
    p = min(max(float(prob), 1e-6), 1.0 - 1e-6)
    return math.log(p / (1.0 - p))


def apply_temperature(prob: float, temperature: float) -> float:
    """p' = sigmoid(logit(p) / T); monotono, pa rangiranje ostaje nepromijenjeno."""
    t = max(1e-3, float(temperature))
    return _sigmoid(_logit(prob) / t)


def _nll(probabilities: list[float], labels: list[int], temperature: float) -> float:
    if not probabilities:
        return float("inf")
    total = 0.0
    for prob, label in zip(probabilities, labels, strict=True):
        q = min(max(apply_temperature(prob, temperature), 1e-12), 1.0 - 1e-12)
        total += -math.log(q) if label else -math.log(1.0 - q)
    return total / len(probabilities)


def fit_temperature_scaling(
    probabilities: list[float],
    labels: list[int],
    t_min: float = DEFAULT_TEMP_MIN,
    t_max: float = DEFAULT_TEMP_MAX,
    n_grid: int = DEFAULT_TEMP_GRID,
) -> tuple[float, dict]:
    """Fit T* > 0 minimizacijom NLL na calibration splitu (scipy, fallback grid)."""
    if not probabilities:
        return 1.0, {"method": "empty", "evaluated": 0}
    lo = max(1e-3, float(t_min))
    hi = max(lo + 1e-6, float(t_max))
    try:  # pragma: no cover - zavisi od okruzenja
        from scipy.optimize import minimize_scalar

        result = minimize_scalar(
            lambda t: _nll(probabilities, labels, t),
            bounds=(lo, hi),
            method="bounded",
            options={"xatol": 1e-8},
        )
        return float(result.x), {
            "method": "scipy.bounded",
            "nfev": int(getattr(result, "nfev", 0)),
            "nll": round(float(result.fun), 6),
            "at_boundary": bool(min(abs(result.x - lo), abs(result.x - hi)) < 1e-6),
        }
    except Exception:
        best_t, best_v = 1.0, float("inf")
        steps = max(2, int(n_grid))
        for idx in range(steps):
            t = lo + (hi - lo) * idx / (steps - 1)
            value = _nll(probabilities, labels, t)
            if value < best_v:
                best_t, best_v = t, value
        return best_t, {
            "method": "grid",
            "n": steps,
            "nll": round(best_v, 6),
            "at_boundary": bool(min(abs(best_t - lo), abs(best_t - hi)) < 1e-9),
        }


def _split_indices(
    n: int, calib_frac: float = DEFAULT_CALIB_FRAC, seed: int = 7
) -> tuple[list[int], list[int]]:
    """Deterministicki 80/20 split (seed)."""
    indices = list(range(n))
    random.Random(seed).shuffle(indices)
    if n <= 1:
        return indices, []
    cut = round(n * float(calib_frac))
    cut = min(max(cut, 1), n - 1)
    return indices[:cut], indices[cut:]


def _accuracy(probabilities: list[float], labels: list[int]) -> float:
    if not probabilities:
        return 0.0
    correct = sum(
        1
        for prob, label in zip(probabilities, labels, strict=True)
        if (prob >= 0.5) == bool(label)
    )
    return correct / len(probabilities)


def fit_calibration(
    probabilities: list[float],
    labels: list[int],
    *,
    calib_frac: float = DEFAULT_CALIB_FRAC,
    seed: int = 7,
    bins: int = DEFAULT_BINS,
    do_fit: bool = True,
    temperature: float | None = None,
    t_min: float = DEFAULT_TEMP_MIN,
    t_max: float = DEFAULT_TEMP_MAX,
    n_grid: int = DEFAULT_TEMP_GRID,
) -> dict:
    """80/20 split, fit T* na calib, izvijesti ECE/Brier na test PRIJE i POSLIJE."""
    calib_idx, test_idx = _split_indices(len(probabilities), calib_frac, seed)
    calib_probs = [probabilities[i] for i in calib_idx]
    calib_labels = [labels[i] for i in calib_idx]
    test_probs = [probabilities[i] for i in test_idx]
    test_labels = [labels[i] for i in test_idx]

    ece_before, _ = calculate_ece(test_probs, test_labels, bins)
    brier_before = calculate_brier_score(test_probs, test_labels)

    if do_fit:
        fitted, fit_info = fit_temperature_scaling(
            calib_probs, calib_labels, t_min, t_max, n_grid
        )
    elif temperature is not None:
        fitted, fit_info = float(temperature), {"method": "fixed"}
    else:
        fitted, fit_info = 1.0, {"method": "identity"}

    test_scaled = [apply_temperature(prob, fitted) for prob in test_probs]
    ece_after, _ = calculate_ece(test_scaled, test_labels, bins)
    brier_after = calculate_brier_score(test_scaled, test_labels)

    return {
        "temperature": round(float(fitted), 6),
        "ece_before": round(ece_before, 6),
        "ece_after": round(ece_after, 6),
        "brier_before": round(brier_before, 6),
        "brier_after": round(brier_after, 6),
        "n_calib": len(calib_idx),
        "n_test": len(test_idx),
        "fit_ts": round(time.time(), 3),
        "accuracy_before": round(_accuracy(test_probs, test_labels), 6),
        "accuracy_after": round(_accuracy(test_scaled, test_labels), 6),
        "ranking_unchanged": all(
            (before >= 0.5) == (after >= 0.5)
            for before, after in zip(test_probs, test_scaled, strict=True)
        ),
        "calib_seed": seed,
        "calib_frac": calib_frac,
        "bins": bins,
        "fit_method": fit_info.get("method"),
        "fit_info": fit_info,
    }


def _prediction_records(predictions: list[dict]) -> list[dict]:
    """Po-uzorku zapis: confidence, label, correct (za naknadni fit)."""
    return [
        {
            "confidence": round(float(pred["prob"]), 6),
            "label": int(pred["label"]),
            "correct": bool((float(pred["prob"]) >= 0.5) == bool(pred["label"])),
        }
        for pred in predictions
    ]


def _reconstruct_from_eval_json(data: dict) -> tuple[list[float], list[int]]:
    """Vrati (probs, labels) iz eval JSON-a; preferiraj po-uzorku, inace binove."""
    records = data.get("predictions")
    if isinstance(records, list) and records:
        probs, labels = [], []
        for rec in records:
            prob = rec.get("confidence", rec.get("prob"))
            label = rec.get("label")
            if prob is None or label is None:
                continue
            probs.append(float(prob))
            labels.append(int(label))
        if probs:
            return probs, labels

    bin_details = (data.get("metrics") or {}).get("bin_details") or data.get("bin_details") or {}
    probs, labels = [], []
    for key in sorted(bin_details, key=lambda k: int(k)):
        info = bin_details[key]
        size = int(info.get("size", 0))
        if size <= 0:
            continue
        conf = float(info.get("conf", 0.0))
        positives = round(float(info.get("acc", 0.0)) * size)
        positives = min(max(positives, 0), size)
        probs.extend([conf] * size)
        labels.extend([1] * positives + [0] * (size - positives))
    return probs, labels


def _write_calibration(calib_dir: str | None, payload: dict) -> str:
    directory = calib_dir or DEFAULT_CALIB_DIR
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "calibration.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def evaluate(
    *,
    dry_run: bool = False,
    dataset: str | None = DEFAULT_DATASET,
    output: str | None = DEFAULT_OUTPUT,
    bins: int = DEFAULT_BINS,
    limit: int | None = None,
    adapter: str | None = None,
    base_model: str | None = None,
    seed: int = 7,
    max_length: int = 2048,
    do_fit: bool = False,
    temperature: float | None = None,
    calib_dir: str | None = None,
    calib_frac: float = DEFAULT_CALIB_FRAC,
    temp_min: float = DEFAULT_TEMP_MIN,
    temp_max: float = DEFAULT_TEMP_MAX,
    temp_grid: int = DEFAULT_TEMP_GRID,
) -> dict:
    """Pokreni evaluaciju; vrati dict koji se pise kao JSON."""
    bins = max(1, int(bins))
    pairs = load_pairs(dataset, limit=limit)
    dataset_used = dataset
    if not pairs:
        if not dry_run:
            return {
                "ok": False,
                "error": f"nema DPO parova za evaluaciju: {dataset}",
                "dataset": dataset,
            }
        pairs = _fallback_pairs()
        dataset_used = None

    if dry_run:
        predictions = _dry_run_predictions(pairs, seed=seed)
        skipped = 0
        mode = "dry-run"
        adapter_used = None
        base_used = base_model or os.environ.get("GAMA_BASE_MODEL")
    else:
        adapter = adapter or os.environ.get("GAMA_LORA_ADAPTER")
        base_model = base_model or os.environ.get("GAMA_BASE_MODEL")
        bundle, error = load_model_bundle(base_model, adapter)
        if error:
            return {
                "ok": False,
                "error": error,
                "dataset": dataset_used,
                "base_model": base_model,
                "adapter": adapter,
            }
        predictions, skipped = _real_predictions(
            pairs, bundle, max_length=max_length
        )
        if not predictions:
            return {
                "ok": False,
                "error": "nijedan par nije dao validan logprob (provjeri max_length)",
                "dataset": dataset_used,
            }
        mode = "adapter" if adapter else "base-only"
        adapter_used = adapter
        base_used = base_model

    metrics = _metrics(predictions, bins)
    diagram = _reliability_diagram(metrics["bin_details"], bins)

    result = {
        "ok": True,
        "mode": mode,
        "dataset": dataset_used,
        "base_model": base_used,
        "adapter": adapter_used,
        "seed": seed,
        "skipped_pairs": skipped,
        "metrics": metrics,
        "diagram": diagram,
        "predictions": _prediction_records(predictions),
        "predictions_sample": predictions[:20],
    }

    if do_fit or temperature is not None:
        probs = [float(pred["prob"]) for pred in predictions]
        labels = [int(pred["label"]) for pred in predictions]
        calib = fit_calibration(
            probs,
            labels,
            calib_frac=calib_frac,
            seed=seed,
            bins=bins,
            do_fit=do_fit,
            temperature=temperature,
            t_min=temp_min,
            t_max=temp_max,
            n_grid=temp_grid,
        )
        target_dir = calib_dir or adapter_used or DEFAULT_CALIB_DIR
        calib_path = _write_calibration(target_dir, calib)
        result["calibration"] = calib
        result["calibration_file"] = calib_path

    if output:
        output_dir = os.path.dirname(os.path.abspath(output))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="ECE/Brier evaluacija LoRA adaptera na DPO parovima."
    )
    parser.add_argument("--dry-run", action="store_true", help="bez GPU/modela")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="DPO JSONL")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="izlazni JSON")
    parser.add_argument("--bins", type=int, default=DEFAULT_BINS)
    parser.add_argument("--limit", type=int, default=None, help="max DPO parova")
    parser.add_argument(
        "--adapter",
        default=None,
        help="LoRA adapter path (default: GAMA_LORA_ADAPTER)",
    )
    parser.add_argument(
        "--base-model",
        default=None,
        help="base model path (default: GAMA_BASE_MODEL)",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument(
        "--fit-temperature",
        action="store_true",
        help="fit T* (NLL) na 80%% calibration splitu i snimi calibration.json",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="primijeni zadati T na logite prije softmaxa (bez fita)",
    )
    parser.add_argument(
        "--calib-dir",
        default=None,
        help=f"folder za calibration.json (default: adapter ili {DEFAULT_CALIB_DIR})",
    )
    parser.add_argument(
        "--calib-frac", type=float, default=DEFAULT_CALIB_FRAC, help="udio calibration splita"
    )
    parser.add_argument("--temp-min", type=float, default=DEFAULT_TEMP_MIN)
    parser.add_argument("--temp-max", type=float, default=DEFAULT_TEMP_MAX)
    parser.add_argument("--temp-grid", type=int, default=DEFAULT_TEMP_GRID)
    parser.add_argument(
        "--fit-from-json",
        default=None,
        help="fit T iz postojeceg eval JSON-a (po-uzorku ili bin_details rekonstrukcija)",
    )
    parser.add_argument("--json", action="store_true", help="samo JSON rezultat")
    return parser.parse_args(argv)


def fit_from_json(args) -> int:
    """Fit temperature iz vec postojeceg eval JSON-a; pise calibration.json."""
    with open(args.fit_from_json, encoding="utf-8") as handle:
        data = json.load(handle)
    probs, labels = _reconstruct_from_eval_json(data)
    if not probs:
        print(
            f"GRESKA: nema po-uzorku ni bin_details u {args.fit_from_json}",
            file=sys.stderr,
        )
        return 2
    calib = fit_calibration(
        probs,
        labels,
        calib_frac=args.calib_frac,
        seed=args.seed,
        bins=args.bins,
        do_fit=not (args.temperature is not None),
        temperature=args.temperature,
        t_min=args.temp_min,
        t_max=args.temp_max,
        n_grid=args.temp_grid,
    )
    calib["source"] = os.path.abspath(args.fit_from_json)
    calib["n_samples"] = len(probs)
    calib["reconstruction"] = (
        "per_sample" if data.get("predictions") else "bin_details"
    )
    calib["ece_target_met"] = bool(calib["ece_after"] < 0.05)
    if calib.get("fit_info", {}).get("at_boundary") and calib["ece_target_met"]:
        calib["note"] = (
            "NLL monotono opada jer je accuracy=1.0 (svaki chosen > rejected); "
            "T* je na donjoj granici pretrage, ECE cilj <0.05 je postignut."
        )
    calib_dir = args.calib_dir or (data.get("adapter") or DEFAULT_CALIB_DIR)
    path = _write_calibration(calib_dir, calib)
    if args.json:
        print(json.dumps({**calib, "calibration_file": path}, ensure_ascii=False, indent=2))
    else:
        print(f"Source: {calib['source']}  ({calib['reconstruction']}, n={len(probs)})")
        print(
            f"T*={calib['temperature']:.6f}  "
            f"ECE {calib['ece_before']:.6f} -> {calib['ece_after']:.6f}  "
            f"Brier {calib['brier_before']:.6f} -> {calib['brier_after']:.6f}"
        )
        print(
            f"acc {calib['accuracy_before']:.4f} -> {calib['accuracy_after']:.4f}  "
            f"ranking_unchanged={calib['ranking_unchanged']}  "
            f"n_calib={calib['n_calib']} n_test={calib['n_test']}"
        )
        print(f"calibration.json: {path}")
    return 0


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.fit_from_json:
        return fit_from_json(args)
    result = evaluate(
        dry_run=args.dry_run,
        dataset=args.dataset,
        output=args.output,
        bins=args.bins,
        limit=args.limit,
        adapter=args.adapter,
        base_model=args.base_model,
        seed=args.seed,
        max_length=args.max_length,
        do_fit=args.fit_temperature,
        temperature=args.temperature,
        calib_dir=args.calib_dir,
        calib_frac=args.calib_frac,
        temp_min=args.temp_min,
        temp_max=args.temp_max,
        temp_grid=args.temp_grid,
    )

    if not result.get("ok"):
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"GRESKA: {result.get('error')}", file=sys.stderr)
        return 2

    metrics = result["metrics"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"Mode: {result['mode']}  dataset={result['dataset']}")
    if result.get("adapter"):
        print(f"Adapter: {result['adapter']}  base={result['base_model']}")
    print(f"Predictions: {metrics['n_predictions']}  skipped_pairs={result['skipped_pairs']}")
    print(f"ECE: {metrics['ece']:.5f}  Brier: {metrics['brier']:.5f}  "
          f"accuracy: {metrics['accuracy']:.3f}")
    print(result["diagram"])
    if result.get("calibration"):
        calib = result["calibration"]
        print(
            f"T*={calib['temperature']:.6f}  "
            f"ECE_test {calib['ece_before']:.6f} -> {calib['ece_after']:.6f}  "
            f"Brier_test {calib['brier_before']:.6f} -> {calib['brier_after']:.6f}  "
            f"(n_calib={calib['n_calib']} n_test={calib['n_test']})"
        )
        print(f"calibration.json: {result.get('calibration_file')}")
    if args.output:
        print(f"JSON: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
