# SPDX-License-Identifier: Apache-2.0
"""Invented control-flow fixture. No model, learning, real task or data access."""
import json
import prediction_contract as pc


class SyntheticAdapter:
    kind="synthetic"
    def __init__(self):self.steps=0
    def prepare(self,task,*,train_seed,augment_seed):
        pc.require((train_seed,augment_seed)==(42,1),"fixed seed drift")
        return dict(model_identity_sha256=pc.digest(b"invented model; no parameters"),
            tokenizer_identity_sha256=pc.digest(b"invented16-token vocabulary"),
            train_views_sha256=pc.digest(b"invented128-view identity; no real views"),initialization_checks_passed=True)
    def decode(self,*,transform,seed,max_new_tokens):
        pc.require(seed==42 and max_new_tokens==930,"fixed decode drift")
        if self.steps==0:
            ids=[0,0,10,0,0,15] if transform=="identity" else [0,10,0]
        else:
            ids=[7,1,0,10,3,2,4,15] if transform=="identity" else [7,3,10,1,2,10,0,4,15]
        return dict(generated_ids=ids,decoded_bytes=json.dumps(ids).encode(),
            decoder_state_sha256=pc.digest(pc.canonical_json({"synthetic_steps":self.steps})),
            prompt_sha256=pc.digest(pc.canonical_json([11,12] if transform=="identity" else [11,10,12])))
    def adapt(self,*,steps,seed):
        pc.require(self.steps==0 and steps==32 and seed==42,"synthetic control sequence drift")
        self.steps=32
        # Invented values exercise validation only. They are not measured gradients.
        return dict(actual_steps=32,first_loss=1.0,first_head_b_gradient_norm=1.0,
            first_head_b_coordinate_absolute_change=1.0,finite_later=True,exact_step_counts=True,
            unique_actual_head_optimizer_membership=True,loss_phase_flag1=True)


def build_adapter():return SyntheticAdapter()
