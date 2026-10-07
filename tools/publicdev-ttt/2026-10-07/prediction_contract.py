# SPDX-License-Identifier: Apache-2.0
"""Freeze predictions before evaluation. Never opens challenge or solution data.

Immutability means exclusive file creation, read-only mode and externally pinned
content hashes. It is a procedural contract, not protection against a privileged
actor changing files or independently reading answers.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

from grid_tokens import parse_attempt

TASK_ID = "3dc255db"
CHALLENGE_SHA256 = "e7c62a4bd211867c6b538f66b8013b81f299663c82ca062f49a52bf439d6e4e8"
HELPER_SOURCES = ("grid_tokens.py", "prediction_contract.py", "evaluate_frozen_predictions.py")
ORDER = (("before", 1, "identity"), ("before", 2, "transpose"),
         ("after", 1, "identity"), ("after", 2, "transpose"))
MAX_ARTIFACT_BYTES = 4 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError("HOLD: " + message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def valid_hash(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def safe_name(name):
    require(type(name) is str and re.fullmatch(r"[A-Za-z0-9_.-]+", name) is not None
            and name not in (".", ".."), "unsafe artifact basename")
    return name


def read_bound(path, expected_hash=None, immutable=False):
    path = Path(path)
    require(not path.is_symlink() and path.is_file(), "missing/symlink artifact " + path.name)
    if immutable:
        require(path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0,
                "artifact is not frozen read-only: " + path.name)
    require(path.stat().st_size <= MAX_ARTIFACT_BYTES, "oversized artifact " + path.name)
    raw = path.read_bytes()
    if expected_hash is not None:
        require(valid_hash(expected_hash) and digest(raw) == expected_hash, "artifact hash drift: " + path.name)
    return raw


def write_frozen(path, raw):
    path = Path(path)
    require(type(raw) is bytes and len(raw) <= MAX_ARTIFACT_BYTES, "invalid/oversized frozen bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o444)
    return {"file": path.name, "bytes": len(raw), "sha256": digest(raw)}


def source_pins(source_dir, native_source_name, extra_sources=()):
    source_dir = Path(source_dir)
    native_source_name = safe_name(native_source_name)
    require(native_source_name.endswith(".py") and native_source_name not in HELPER_SOURCES,
            "native driver must be separately pinned")
    require(type(extra_sources) in (list, tuple), "extra source names must be an explicit list/tuple")
    names = [*HELPER_SOURCES, native_source_name, *extra_sources]
    require(len(set(names)) == len(names), "duplicate source names")
    require(all(safe_name(name).endswith('.py') for name in names), "every pinned source must be a .py file")
    return {name: digest(read_bound(source_dir / name)) for name in sorted(names)}


def make_protocol(source_hashes, native_source_name, model_identity_sha256,
                  tokenizer_identity_sha256, train_views_sha256):
    native_source_name = safe_name(native_source_name)
    protocol = {
        "schema": "arc2-publicdev-quality-v1", "task_id": TASK_ID, "test_index": 0,
        "challenge_sha256": CHALLENGE_SHA256, "train_seed": 42, "augment_seed": 1,
        "adaptation_steps": 32, "train_views": 128, "attempts_per_stage": 2,
        "decode_policy": "greedy", "max_new_tokens": 930,
        "attempt_order": [list(row) for row in ORDER],
        "vocabulary": {"digits": list(range(10)), "newline": 10, "eos": 15},
        "native_source_name": native_source_name, "source_sha256": source_hashes,
        "source_names": sorted(source_hashes),
        "model_identity_sha256": model_identity_sha256,
        "tokenizer_identity_sha256": tokenizer_identity_sha256,
        "train_views_sha256": train_views_sha256,
        "train_prompt_selection_uses_test_answers": False,
        "solution_file_access_before_prediction_freeze": False,
        "prior_public_training_pair_exposure": True,
        "scope": "Preregistered public development task/test0 only; not blinded selection, benchmark or hidden evaluation",
        "solution_basename": "arc-agi_evaluation_solutions.json",
    }
    validate_protocol(protocol)
    return protocol


def validate_protocol(protocol):
    require(type(protocol) is dict, "protocol object required")
    fixed = {"schema":"arc2-publicdev-quality-v1", "task_id":TASK_ID, "test_index":0,
             "challenge_sha256":CHALLENGE_SHA256, "train_seed":42, "augment_seed":1,
             "adaptation_steps":32, "train_views":128, "attempts_per_stage":2,
             "decode_policy":"greedy", "max_new_tokens":930,
             "attempt_order":[list(row) for row in ORDER],
             "vocabulary":{"digits":list(range(10)), "newline":10, "eos":15},
             "train_prompt_selection_uses_test_answers":False,
             "solution_file_access_before_prediction_freeze":False,
             "prior_public_training_pair_exposure":True,
             "scope":"Preregistered public development task/test0 only; not blinded selection, benchmark or hidden evaluation",
             "solution_basename":"arc-agi_evaluation_solutions.json"}
    for name, value in fixed.items():
        require(type(protocol.get(name)) is type(value) and canonical_json(protocol.get(name)) == canonical_json(value),
                "preregistered field changed: " + name)
    native = safe_name(protocol.get("native_source_name"))
    require(native.endswith(".py") and native not in HELPER_SOURCES, "invalid native driver name")
    pins = protocol.get("source_sha256")
    require(type(pins) is dict and set(pins) >= {*HELPER_SOURCES, native}
            and all(safe_name(name).endswith('.py') and valid_hash(value) for name,value in pins.items()),
            "source pin set differs")
    require(type(protocol.get('source_names')) is list and protocol['source_names'] == sorted(pins),
            "explicit source name set differs")
    for name in ("model_identity_sha256", "tokenizer_identity_sha256", "train_views_sha256"):
        require(valid_hash(protocol.get(name)), "missing identity digest: " + name)
    require(set(protocol) == {*fixed, "native_source_name", "source_sha256", "source_names", "model_identity_sha256",
                              "tokenizer_identity_sha256", "train_views_sha256"}, "unexpected protocol fields")


def write_protocol(output_dir, protocol):
    validate_protocol(protocol)
    return write_frozen(Path(output_dir) / "quality_protocol.json", canonical_json(protocol))


def verify_sources(protocol, source_dir):
    validate_protocol(protocol)
    for name, expected in protocol["source_sha256"].items():
        read_bound(Path(source_dir) / safe_name(name), expected)
    return True


def freeze_predictions(output_dir, protocol_sha256, attempts, source_dir,
                       actual_adaptation_steps=32):
    """Called once after both decode stages, before invoking the evaluator process.

    attempts: exactly four dicts, with stage, attempt, transform, generated_ids,
    decoded_bytes, decoder_state_sha256, prompt_sha256. Preserve the COMPLETE generated suffix;
    never strip EOS, pads, role tokens or malformed text to make parsing pass.
    """
    output_dir = Path(output_dir)
    protocol_raw = read_bound(output_dir / "quality_protocol.json", protocol_sha256, immutable=True)
    protocol = json.loads(protocol_raw)
    verify_sources(protocol, source_dir)
    require(type(actual_adaptation_steps) is int and actual_adaptation_steps == 32, "optimizer step count differs")
    require(type(attempts) in (list, tuple) and len(attempts) == 4, "complete before/after attempt set required")
    records, stage_states, transform_prompts = [], {}, {}
    for attempt, expected in zip(attempts, ORDER):
        require(type(attempt) is dict and set(attempt) == {"stage", "attempt", "transform", "generated_ids",
                "decoded_bytes", "decoder_state_sha256", "prompt_sha256"}, "attempt field set differs")
        require((attempt["stage"], attempt["attempt"], attempt["transform"]) == expected
                and type(attempt["attempt"]) is int, "attempt order/transform drift")
        require(type(attempt["generated_ids"]) in (list, tuple)
                and all(type(value) is int for value in attempt["generated_ids"]), "generated IDs must be exact integers")
        require(type(attempt["decoded_bytes"]) is bytes, "exact decoded bytes required")
        state = attempt["decoder_state_sha256"]
        require(valid_hash(state), "decoder state digest missing")
        prompt = attempt['prompt_sha256']
        transform = attempt['transform']
        require(valid_hash(prompt) and (transform not in transform_prompts or transform_prompts[transform] == prompt),
                "before/after prompt identity differs")
        transform_prompts[transform] = prompt
        stage = attempt["stage"]
        require(stage not in stage_states or stage_states[stage] == state, "decoder changed within a stage")
        stage_states[stage] = state
        stem = stage + "_attempt_" + str(attempt["attempt"])
        ids = list(attempt["generated_ids"])
        tokens = write_frozen(output_dir / (stem + "_tokens.json"), canonical_json(ids))
        decoded = write_frozen(output_dir / (stem + "_decoded.bin"), attempt["decoded_bytes"])
        records.append({"stage":stage, "attempt":attempt["attempt"], "transform":attempt["transform"],
                        "decoder_state_sha256":state, "prompt_sha256":prompt,
                        "token_artifact":tokens, "decoded_artifact":decoded,
                        "parse":parse_attempt(ids, attempt["transform"])})
    manifest = {"schema":"arc2-frozen-predictions-v1", "protocol_sha256":protocol_sha256,
                "task_id":TASK_ID, "test_index":0, "actual_adaptation_steps":32,
                "model_identity_sha256":protocol["model_identity_sha256"],
                "tokenizer_identity_sha256":protocol["tokenizer_identity_sha256"],
                "train_views_sha256":protocol["train_views_sha256"], "attempts":records,
                "held_solution_access_before_freeze":False,
                "prior_public_training_pair_exposure":True,
                "score_scope":"one public development query; no benchmark/hidden-score claim"}
    return write_frozen(output_dir / "prediction_manifest.json", canonical_json(manifest))


def verify_frozen_predictions(output_dir, protocol_sha256, manifest_sha256, source_dir):
    """Entire gate completes before the evaluator is allowed to open any solutions."""
    output_dir = Path(output_dir)
    protocol_raw = read_bound(output_dir / "quality_protocol.json", protocol_sha256, immutable=True)
    manifest_raw = read_bound(output_dir / "prediction_manifest.json", manifest_sha256, immutable=True)
    protocol, manifest = json.loads(protocol_raw), json.loads(manifest_raw)
    verify_sources(protocol, source_dir)
    require(type(manifest) is dict and set(manifest) == {"schema", "protocol_sha256", "task_id", "test_index",
            "actual_adaptation_steps", "model_identity_sha256", "tokenizer_identity_sha256", "train_views_sha256",
            "attempts", "held_solution_access_before_freeze", "prior_public_training_pair_exposure", "score_scope"},
            "manifest field set differs")
    fixed = {"schema":"arc2-frozen-predictions-v1", "protocol_sha256":protocol_sha256,
             "task_id":TASK_ID, "test_index":0, "actual_adaptation_steps":32,
             "held_solution_access_before_freeze":False, "prior_public_training_pair_exposure":True,
             "score_scope":"one public development query; no benchmark/hidden-score claim"}
    for name, value in fixed.items():
        require(type(manifest.get(name)) is type(value) and manifest.get(name) == value, "manifest field changed: " + name)
    for name in ("model_identity_sha256", "tokenizer_identity_sha256", "train_views_sha256"):
        require(manifest[name] == protocol[name], "prediction identity differs: " + name)
    require(type(manifest["attempts"]) is list and len(manifest["attempts"]) == 4, "missing frozen attempts")
    states, prompts = {}, {}
    for record, expected in zip(manifest["attempts"], ORDER):
        require(type(record) is dict and set(record) == {"stage", "attempt", "transform", "decoder_state_sha256",
                "token_artifact", "decoded_artifact", "parse", "prompt_sha256"}, "prediction record fields differ")
        require((record["stage"], record["attempt"], record["transform"]) == expected and type(record["attempt"]) is int,
                "frozen attempt order differs")
        state = record["decoder_state_sha256"]
        require(valid_hash(state) and (record["stage"] not in states or states[record["stage"]] == state),
                "inconsistent decoder state")
        states[record["stage"]] = state
        prompt = record['prompt_sha256']
        transform = record['transform']
        require(valid_hash(prompt) and (transform not in prompts or prompts[transform] == prompt),
                "frozen before/after prompt identity differs")
        prompts[transform] = prompt
        stem = record["stage"] + "_attempt_" + str(record["attempt"])
        artifacts = {}
        for key, suffix in (("token_artifact", "_tokens.json"), ("decoded_artifact", "_decoded.bin")):
            artifact = record[key]
            require(type(artifact) is dict and set(artifact) == {"file", "bytes", "sha256"}
                    and artifact["file"] == stem + suffix and type(artifact["bytes"]) is int,
                    "frozen artifact descriptor differs")
            raw = read_bound(output_dir / safe_name(artifact["file"]), artifact["sha256"], immutable=True)
            require(len(raw) == artifact["bytes"], "artifact byte count differs")
            artifacts[key] = raw
        ids = json.loads(artifacts["token_artifact"])
        require(type(ids) is list and all(type(value) is int for value in ids), "frozen token IDs invalid")
        require(canonical_json(record["parse"]) == canonical_json(parse_attempt(ids, record["transform"])),
                "frozen parse differs from exact tokens")
    return protocol, manifest
