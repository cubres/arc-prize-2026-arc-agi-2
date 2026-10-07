# SPDX-License-Identifier: Apache-2.0
"""Strict parser for canonical ARC completion token IDs; no framework or file I/O."""
from __future__ import annotations

EOS = 15
NEWLINE = 10
MAX_SIDE = 30
MAX_VALID_TOKENS = 30 * 30 + 29 + 1


class GridTokenError(ValueError):
    def __init__(self, code, index=None):
        self.code, self.index = code, index
        super().__init__(code + (" at token " + str(index) if index is not None else ""))


def validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= MAX_SIDE:
        raise GridTokenError("height_out_of_range")
    width = None
    result = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or not 1 <= len(row) <= MAX_SIDE:
            raise GridTokenError("width_out_of_range")
        if width is not None and len(row) != width:
            raise GridTokenError("ragged_grid")
        width = len(row)
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise GridTokenError("invalid_colour")
        result.append(list(row))
    return result


def parse_token_ids(token_ids):
    """Require digits, internal nonempty row separators and exactly one final EOS.

    Prompt prefixes, role IDs 11/12, padding/endoftext 13, im_start 14 and all
    unknown IDs are errors. A final newline before EOS is an empty final row.
    Never repair, strip, trim, infer dimensions or select a suffix.
    """
    if not isinstance(token_ids, (list, tuple)):
        raise GridTokenError("token_sequence_required")
    if not 2 <= len(token_ids) <= MAX_VALID_TOKENS:
        raise GridTokenError("token_count_out_of_range")
    if any(type(value) is not int for value in token_ids):
        raise GridTokenError("integer_token_ids_required")
    if token_ids[-1] != EOS:
        raise GridTokenError("missing_terminal_eos")
    rows, row = [], []
    for index, token_id in enumerate(token_ids[:-1]):
        if 0 <= token_id <= 9:
            row.append(token_id)
            if len(row) > MAX_SIDE:
                raise GridTokenError("width_out_of_range", index)
        elif token_id == NEWLINE:
            if not row:
                raise GridTokenError("empty_row", index)
            rows.append(row)
            row = []
            if len(rows) >= MAX_SIDE:
                raise GridTokenError("height_out_of_range", index)
        elif token_id == EOS:
            raise GridTokenError("early_eos_or_trailing_tokens", index)
        else:
            raise GridTokenError("role_special_or_unknown_token", index)
    if not row:
        raise GridTokenError("empty_final_row")
    rows.append(row)
    return validate_grid(rows)


def transpose_grid(grid):
    parsed = validate_grid(grid)
    return [list(column) for column in zip(*parsed)]


def canonical_grid_bytes(grid):
    parsed = validate_grid(grid)
    return "\n".join("".join(str(value) for value in row) for row in parsed).encode("ascii")


def parse_attempt(token_ids, transform):
    """Return the base-coordinate prediction for a preregistered input transform."""
    if transform not in ("identity", "transpose"):
        raise GridTokenError("unsupported_transform")
    try:
        decoded = parse_token_ids(token_ids)
    except GridTokenError as error:
        return {"valid": False, "error_code": error.code, "error_index": error.index,
                "decoded_grid": None, "base_grid": None}
    return {"valid": True, "error_code": None, "error_index": None,
            "decoded_grid": decoded,
            "base_grid": transpose_grid(decoded) if transform == "transpose" else decoded}
