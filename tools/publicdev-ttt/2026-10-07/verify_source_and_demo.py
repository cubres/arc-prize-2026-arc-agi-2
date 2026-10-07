# SPDX-License-Identifier: Apache-2.0
"""Focused source+synthetic checks, preserving all generated output directories."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import grid_tokens
from run_experiment import validate_adaptation
import prediction_contract as pc

HERE=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    checks=[]
    def check(ok,label):
        if not ok:raise RuntimeError(label)
        checks.append(label)
    manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
    for entry in manifest["files"]:
        name=pc.safe_name(entry["path"]);raw=pc.read_bound(HERE/name)
        check(len(raw)==entry["bytes"] and pc.digest(raw)==entry["sha256"],"source pin:"+name)
    for ids in ([0,1,10,2,3],[0,1,10,2,15],[0,15,0],[11,0,15],[0,10,15]):
        check(grid_tokens.parse_attempt(ids,"identity")["valid"] is False,"malformed suffix retained:"+repr(ids))
    before=dict(actual_steps=32,first_loss=1.,first_head_b_gradient_norm=1.,first_head_b_coordinate_absolute_change=1.,
        finite_later=True,exact_step_counts=True,unique_actual_head_optimizer_membership=True,loss_phase_flag1=True)
    check(validate_adaptation(before)["actual_steps"]==32,"explicit backend32 report accepted")
    for key,value in (("actual_steps",31),("first_head_b_gradient_norm",0.),("first_head_b_coordinate_absolute_change",0.),("finite_later",False)):
        changed={**before,key:value}
        try:validate_adaptation(changed)
        except ValueError:check(True,"invalid backend report refused:"+key)
        else:raise RuntimeError("invalid backend report accepted:"+key)
    demo=args.output/"demo"
    result=subprocess.run([sys.executable,"-B",*(["-O"] if not __debug__ else []),str(HERE/"run_synthetic_demo.py"),"--output",str(demo)],
        capture_output=True,text=True,timeout=120)
    check(result.returncode==0,"separate toy scientific/evaluator processes complete")
    summary=json.loads(result.stdout)
    check(summary["scientific_worker_optimized"]==(not __debug__) and summary["evaluator_requested_optimized"]==(not __debug__),"actual child optimization flags match verifier")
    check(summary["scope"]=="SYNTHETIC_CONTROL_FLOW_ONLY" and summary["native_training"] is False,"toy scope never claimed native")
    check(summary["worker_exited_before_truth_creation"] is True and summary["separate_evaluator"] is True,"toy truth ordering")
    check(summary["real_challenges_or_solutions_read"] is False and summary["quality_or_official_score_claim"] is False,"no official data or score claim")
    metadata=json.loads(pc.read_bound(demo/"science/run-metadata.json",immutable=True))
    check(metadata["driver_solution_reads"]==0 and metadata["backend_solution_access_attested"] is False,"driver-only nonaccess scope explicit")
    check(metadata["synthetic_data"] is True and metadata["official_challenge_read"] is False and
        metadata["independently_attested_native_execution"] is False,"synthetic metadata explicit")
    protocol,frozen=pc.verify_frozen_predictions(demo/"science",metadata["protocol_sha256"],metadata["manifest_sha256"],HERE)
    check(len(frozen["attempts"])==4,"all four attempts frozen")
    check(frozen["attempts"][1]["parse"]["valid"] is False,"incomplete toy attempt not repaired")
    check(set(protocol["source_names"])=={*pc.HELPER_SOURCES,"run_experiment.py","adapter_interface.py","synthetic_adapter.py"},"exact scientific source closure")
    report=dict(status="PASS_SOURCE_AND_SYNTHETIC_DEMO",optimized=not __debug__,checks=checks,
        check_count=len(checks),source_manifest_sha256=hashlib.sha256((HERE/"SOURCE_MANIFEST.json").read_bytes()).hexdigest(),
        real_data_read=False,native_training_or_quality_evidence=False,generated_outputs_preserved=True)
    with (args.output/"VERIFICATION.json").open("x") as stream:json.dump(report,stream,indent=2,sort_keys=True)
    print(json.dumps({"status":report["status"],"check_count":len(checks),"optimized":not __debug__}))
if __name__=="__main__":main()
