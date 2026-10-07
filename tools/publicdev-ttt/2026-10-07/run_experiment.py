# SPDX-License-Identifier: Apache-2.0
"""Source-pinned one-case TTT orchestration; never opens a solution file.

This is an original engine adapter harness, not the private neural engine.
The real backend must supply independently reviewed initialization/training
evidence. Its reported counters alone do not establish native optimizer proof.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path

import prediction_contract as pc

HERE=Path(__file__).resolve().parent


def validate_adaptation(row):
    pc.require(type(row) is dict and type(row.get("actual_steps")) is int and row["actual_steps"]==32,
               "backend did not report exactly32 steps")
    for key in ("first_loss","first_head_b_gradient_norm","first_head_b_coordinate_absolute_change"):
        pc.require(type(row.get(key)) in (int,float) and math.isfinite(row[key]), "invalid aggregate "+key)
    pc.require(row["first_head_b_gradient_norm"]>0 and row["first_head_b_coordinate_absolute_change"]>0,
               "first head-B gradient/update reports must be positive")
    for key in ("finite_later","exact_step_counts","unique_actual_head_optimizer_membership","loss_phase_flag1"):
        pc.require(row.get(key) is True,"missing reported adaptation gate "+key)
    return {key:row[key] for key in ("actual_steps","first_loss","first_head_b_gradient_norm",
        "first_head_b_coordinate_absolute_change","finite_later","exact_step_counts",
        "unique_actual_head_optimizer_membership","loss_phase_flag1")}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--adapter-file",required=True)
    parser.add_argument("--challenge-file",type=Path)
    parser.add_argument("--synthetic",action="store_true")
    args=parser.parse_args()
    pc.require(args.output!=HERE and not args.output.exists(),"output must be a NEW directory")
    name=pc.safe_name(args.adapter_file)
    pc.require(name.endswith(".py") and name not in (*pc.HELPER_SOURCES,"run_experiment.py","adapter_interface.py"),"invalid adapter source")
    # Pin the driver and exact sibling backend before import. Dependency/container
    # closure remains the backend author's responsibility and should be recorded.
    pins=pc.source_pins(HERE,"run_experiment.py",extra_sources=("adapter_interface.py",name))
    if args.synthetic:
        pc.require(args.challenge_file is None and name=="synthetic_adapter.py","synthetic demo cannot read real challenges")
        task={"train":[{"input":[[0]],"output":[[0]]}],"test":[{"input":[[0]]}]}
    else:
        pc.require(args.challenge_file is not None,"real experiment requires official public challenges")
        raw=pc.read_bound(args.challenge_file,expected_hash=pc.CHALLENGE_SHA256)
        challenges=json.loads(raw)
        pc.require(all("output" not in item for task in challenges.values() for item in task["test"]),"challenge contains test outputs")
        task=challenges[pc.TASK_ID]
        pc.require(len(task["train"])==3 and len(task["test"])==1,"fixed public task shape drift")
    args.output.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location("public_ttt_backend",HERE/name)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    adapter=module.build_adapter()
    pc.require(adapter.kind==("synthetic" if args.synthetic else "external_neural"),"backend kind disagrees with run scope")
    setup=adapter.prepare(task,train_seed=42,augment_seed=1)
    pc.require(setup.get("initialization_checks_passed") is True,"initialization checks must precede decoding")
    protocol=pc.make_protocol(pins,"run_experiment.py",setup["model_identity_sha256"],
        setup["tokenizer_identity_sha256"],setup["train_views_sha256"])
    seal=pc.write_protocol(args.output,protocol)
    attempts=[]
    for stage in ("before","after"):
        if stage=="after":adaptation=validate_adaptation(adapter.adapt(steps=32,seed=42))
        for attempt,transform in ((1,"identity"),(2,"transpose")):
            decoded=adapter.decode(transform=transform,seed=42,max_new_tokens=930)
            attempts.append({"stage":stage,"attempt":attempt,"transform":transform,
                **{key:decoded[key] for key in ("generated_ids","decoded_bytes","decoder_state_sha256","prompt_sha256")}})
    manifest=pc.freeze_predictions(args.output,seal["sha256"],attempts,HERE,actual_adaptation_steps=32)
    metadata=dict(scope="SYNTHETIC_CONTROL_FLOW_ONLY" if args.synthetic else "BACKEND_REPORTED_PUBLICDEV_STUDY",
        synthetic_data=args.synthetic,official_challenge_read=not args.synthetic,
        protocol_sha256=seal["sha256"],manifest_sha256=manifest["sha256"],backend_reported_adaptation=adaptation,
        independently_attested_native_execution=False,driver_solution_reads=0,backend_solution_access_attested=False,
        optimized_interpreter=not __debug__,competition_submission=False,
        limitations="Backend source hashes and summaries do not attest live compiled execution, dataset origin or OS isolation")
    pc.write_frozen(args.output/"run-metadata.json",pc.canonical_json(metadata))
    print(json.dumps({key:metadata[key] for key in ("scope","protocol_sha256","manifest_sha256","driver_solution_reads","backend_solution_access_attested")}))


if __name__=="__main__":main()
