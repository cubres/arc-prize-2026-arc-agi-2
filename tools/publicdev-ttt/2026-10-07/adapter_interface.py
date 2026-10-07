# SPDX-License-Identifier: Apache-2.0
"""Original engine interface for the specialized public-development comparison.

The engine owns real initialization/backward/optimizer evidence. The harness
validates reported aggregates and freezes outputs; it cannot attest compiled
framework execution or stop an independently privileged reader of answers.
"""
from typing import Protocol


class Adapter(Protocol):
    kind: str  # "external_neural" or explicitly "synthetic"

    def prepare(self, task: dict, *, train_seed: int, augment_seed: int) -> dict:
        """Return model_identity_sha256, tokenizer_identity_sha256,
        train_views_sha256, and initialization_checks_passed.

        Complete same-model/checkpoint/tokenizer, zero-B, head storage/binding
        and actual-optimizer membership checks before any decode. A real backend
        must construct exactly128 fixed augmented rows from public train pairs.
        task contains train demonstrations and test INPUT only, never solutions.
        """

    def decode(self, *, transform: str, seed: int, max_new_tokens: int) -> dict:
        """Return generated_ids, decoded_bytes, decoder_state_sha256 and
        prompt_sha256. Keep the entire generated suffix including EOS15.
        prompt_sha256 hashes canonical JSON of actual prompt token IDs. Equal
        transform prompts must match before/after; state is shared within stage.
        """

    def adapt(self, *, steps: int, seed: int) -> dict:
        """Return actual_steps and finite first_loss, first_head_b_gradient_norm,
        first_head_b_coordinate_absolute_change. Return True for finite_later,
        exact_step_counts, unique_actual_head_optimizer_membership and
        loss_phase_flag1. Step1 requires nonzero gradient/positive real update;
        legitimate later zero gradients/deltas are permitted and recorded.
        These are backend-reported summaries, not independent native proof.
        """
