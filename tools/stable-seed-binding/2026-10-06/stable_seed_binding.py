"""Portable S1 seed binding. No augmentation, model, or notebook integration."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

DOMAIN_BYTES = b"arc2-rescore-seed-v1\0"
SEED_BITS = 20
SEED_MODULUS = 1 << SEED_BITS
MAX_BK_UTF8_BYTES = 256
MAX_IMPLEMENTATION_BYTES = 65536
RULE_ID = "arc2-rescore-seed-v1/sha256-big-endian-mod-2pow20"


class SeedBindingError(ValueError):
    """An input or on-disk source identity cannot satisfy the tool contract."""


@dataclass(frozen=True)
class SeedBinding:
    original_bk: str
    original_bk_utf8_bytes: int
    original_bk_utf8_sha256: str
    payload_sha256: str
    seed: int


def bind_seed(original_bk: str) -> SeedBinding:
    """Bind exact UTF-8 bytes to S1; do not trim, normalize, or call hash()."""
    if type(original_bk) is not str:
        raise SeedBindingError("original_bk must be an exact str, not a subclass")
    # Every valid UTF-8 code point needs at least one byte. Check before encoding.
    if not 1 <= len(original_bk) <= MAX_BK_UTF8_BYTES:
        raise SeedBindingError("original_bk must contain 1..256 UTF-8 bytes")
    try:
        bk_bytes = original_bk.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise SeedBindingError("original_bk must be strictly UTF-8 encodable") from exc
    if len(bk_bytes) > MAX_BK_UTF8_BYTES:
        raise SeedBindingError("original_bk exceeds 256 UTF-8 bytes")
    digest = hashlib.sha256(DOMAIN_BYTES + bk_bytes).digest()
    return SeedBinding(
        original_bk=original_bk,
        original_bk_utf8_bytes=len(bk_bytes),
        original_bk_utf8_sha256=hashlib.sha256(bk_bytes).hexdigest(),
        payload_sha256=digest.hex(),
        seed=int.from_bytes(digest, "big") % SEED_MODULUS,
    )


def source_identity() -> Dict[str, Any]:
    """Fingerprint this on-disk implementation, not an executing model or graph."""
    path = Path(__file__)
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_IMPLEMENTATION_BYTES + 1)
    except OSError as exc:
        raise SeedBindingError("cannot read this implementation's source") from exc
    if not raw or len(raw) > MAX_IMPLEMENTATION_BYTES:
        raise SeedBindingError("implementation source is empty or exceeds 64 KiB")
    return {
        "role": "on_disk_implementation",
        "file_name": path.name,
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "loaded_code_attestation": False,
    }


def binding_receipt(original_bk: str) -> Dict[str, Any]:
    """Return detached JSON-compatible evidence; no output file is written."""
    binding = bind_seed(original_bk)
    return {
        "schema": "stable-seed-binding.receipt.v1",
        "rule_id": RULE_ID,
        "domain_utf8": DOMAIN_BYTES.decode("utf-8"),
        "domain_hex": DOMAIN_BYTES.hex(),
        "domain_sha256": hashlib.sha256(DOMAIN_BYTES).hexdigest(),
        "original_bk": binding.original_bk,
        "original_bk_utf8_bytes": binding.original_bk_utf8_bytes,
        "original_bk_utf8_sha256": binding.original_bk_utf8_sha256,
        "payload_bytes": len(DOMAIN_BYTES) + binding.original_bk_utf8_bytes,
        "payload_sha256": binding.payload_sha256,
        "seed": binding.seed,
        "seed_bits": SEED_BITS,
        "seed_modulus": SEED_MODULUS,
        "reduced_seed_is_unique_identity": False,
        "payload_digest_is_model_or_task_data_identity": False,
        "source_identity": source_identity(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_bk", help="exact query key; 1..256 UTF-8 bytes")
    args = parser.parse_args()
    try:
        receipt = binding_receipt(args.original_bk)
    except SeedBindingError as exc:
        parser.error(str(exc))
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
