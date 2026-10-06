"""Verify the portable S1 contract; preserve receipts in a fresh output directory."""

from __future__ import annotations

import argparse
from dataclasses import FrozenInstanceError
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unicodedata

sys.dont_write_bytecode = True
import stable_seed_binding as subject

VECTORS = (
    ("00d62c1b_0", "f7562fb3c6616287887e464e5fa39d529def296da513fb02343ac14983cca8df", 829663),
    ("00d62c1b_1", "2f7e6419da586aa941b9e2575a5689ebdc14b4a93d0a5b1403d861c02cd1e940", 125248),
    ("任务_α", "7f2fd76ca5ede5292fd632c62a5596b6d7ae7837b05f18edd0e4c40a25eacfdf", 708575),
    ("00d62c1b_0 ", "9c1b17f0c7bfbeee30aba347fc950763a1bb22835491792a6f6b7f354151dc70", 121968),
)
COLLISION_KEYS = ("collision-probe-681_0", "collision-probe-1298_0")


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def probe_child(key: str, hash_seed: str, optimized: bool = False) -> dict:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable] + (["-O"] if optimized else [])
    command += [str(Path(subject.__file__).resolve()), key]
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
    require(result.returncode == 0, "standalone child binding failed")
    require(not result.stderr, "standalone child emitted unexpected stderr")
    require(len(result.stdout.encode()) <= 32768, "unexpected child output size")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new receipt directory; must not exist")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "stable-seed-binding.verification.v1",
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python": sys.version,
        "optimized_interpreter": not __debug__,
        "checks": [],
        "claim_limits": {
            "augmentation_implemented": False,
            "native_arc2_executed": False,
            "model_or_candidates_used": False,
            "native_speed_claim": None,
            "quality_or_generalization_claim": None,
        },
    }
    checks = report["checks"]
    try:
        packet = Path(__file__).resolve().parent
        manifest_path = packet / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        require(manifest["schema"] == "stable-seed-binding.source-manifest.v1", "manifest schema drift")
        require(manifest["generated_evidence_excluded"] is True, "manifest scope drift")
        for entry in manifest["files"]:
            relative = Path(entry["path"])
            require(not relative.is_absolute() and len(relative.parts) == 1, "manifest path must name a sibling")
            raw = (packet / relative).read_bytes()
            require(len(raw) == entry["size_bytes"], "source size drift: " + str(relative))
            require(hashlib.sha256(raw).hexdigest() == entry["sha256"], "source hash drift: " + str(relative))
        report["source_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        checks.append({"name": "source_manifest", "files": len(manifest["files"]), "status": "PASS"})
        require(subject.DOMAIN_BYTES == b"arc2-rescore-seed-v1\0", "domain drift")
        require(subject.SEED_MODULUS == 2**20, "modulus drift")
        for key, digest, seed in VECTORS:
            result = subject.bind_seed(key)
            require(result.payload_sha256 == digest and result.seed == seed, "fixed vector mismatch")
            require(0 <= result.seed < 2**20, "seed outside range")
            receipt = subject.binding_receipt(key)
            require(receipt["domain_hex"] == b"arc2-rescore-seed-v1\0".hex(), "receipt domain mismatch")
            require(receipt["payload_bytes"] == len(b"arc2-rescore-seed-v1\0") + len(key.encode("utf-8")), "payload length mismatch")
            own_bytes = (packet / "stable_seed_binding.py").read_bytes()
            require(receipt["source_identity"]["sha256"] == hashlib.sha256(own_bytes).hexdigest(), "source receipt mismatch")
            require(receipt["source_identity"]["loaded_code_attestation"] is False, "unsupported loaded-code attestation")
        checks.append({"name": "fixed_vectors_and_receipts", "count": len(VECTORS), "status": "PASS"})

        class StrSubclass(str):
            pass

        invalid = (None, False, 1, 1.0, b"key", [], {}, object(), StrSubclass("key"), "", "a"*257, "😀"*65, "\ud800", "\udfff")
        for value in invalid:
            try:
                subject.bind_seed(value)
            except subject.SeedBindingError:
                pass
            else:
                raise VerificationError("invalid input accepted: " + type(value).__name__)
        for key in ("a", "a"*256, "😀"*64, "\0", " ", "\n"):
            binding = subject.bind_seed(key)
            require(binding.original_bk == key, "input bytes were normalized")
            require(binding.original_bk_utf8_bytes == len(key.encode("utf-8")), "UTF-8 boundary mismatch")
        nfc, nfd = "é_0", unicodedata.normalize("NFD", "é_0")
        for left, right in ((nfc, nfd), ("Case_0", "case_0"), ("key", "key ")):
            require(subject.bind_seed(left).payload_sha256 != subject.bind_seed(right).payload_sha256, "distinct exact content lost")
        require(subject.bind_seed("key").payload_sha256 != hashlib.sha256(b"arc2-rescore-seed-v2\0key").hexdigest(), "domain separation lost")
        try:
            subject.bind_seed("key").seed = 0
        except FrozenInstanceError:
            pass
        else:
            raise VerificationError("binding record is mutable")
        checks.append({"name": "input_boundaries_exact_content_and_domain", "invalid_count": len(invalid), "status": "PASS"})

        left, right = [subject.bind_seed(key) for key in COLLISION_KEYS]
        require(left.seed == right.seed == 477269, "declared reduced collision changed")
        require(left.payload_sha256 != right.payload_sha256 and left.original_bk != right.original_bk, "full bindings collapsed")
        for key in COLLISION_KEYS:
            receipt = subject.binding_receipt(key)
            require(receipt["reduced_seed_is_unique_identity"] is False, "reduced seed incorrectly claims uniqueness")
            require(receipt["payload_digest_is_model_or_task_data_identity"] is False, "payload digest overclaims scope")
        report["collision_witness"] = {"left": left.original_bk, "right": right.original_bk, "seed": left.seed, "left_payload_sha256": left.payload_sha256, "right_payload_sha256": right.payload_sha256}
        checks.append({"name": "collision_is_not_identity", "status": "PASS"})

        child_records = []
        for key, _, _ in VECTORS:
            expected = subject.binding_receipt(key)
            for hash_seed in ("0", "42", "random"):
                receipt = probe_child(key, hash_seed)
                require(receipt == expected, "receipt changed across startup hash seeds")
                child_records.append({"key": key, "startup_hash_seed": hash_seed, "payload_sha256": receipt["payload_sha256"], "seed": receipt["seed"]})
            require(probe_child(key, "42", optimized=True) == expected, "optimized interpreter changed binding")
        report["cross_process_bindings"] = child_records
        checks.append({"name": "cross_process_and_optimized_mode", "normal_children": len(child_records), "optimized_children": len(VECTORS), "status": "PASS"})

        invalid_cli_count = 0
        for optimized in (False, True):
            for invalid_key in ("", "a"*257):
                command = [sys.executable] + (["-O"] if optimized else []) + [str(packet / "stable_seed_binding.py"), invalid_key]
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
                process = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
                require(process.returncode == 2 and not process.stdout, "invalid CLI did not refuse")
                invalid_cli_count += 1
        checks.append({"name": "invalid_cli_refusals", "count": invalid_cli_count, "status": "PASS"})
        report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        report["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (output / "VERIFICATION.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=True, sort_keys=True, indent=2)
            stream.write("\n")
    print(json.dumps({"status": report["status"], "checks": len(checks), "receipt": str((output / "VERIFICATION.json").resolve())}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
