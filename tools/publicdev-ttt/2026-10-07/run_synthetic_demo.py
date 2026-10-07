# SPDX-License-Identifier: Apache-2.0
"""Runnable standard-library POSIX toy demo; all output files are NEW/preserved."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import prediction_contract as pc

HERE=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    science=args.output/"science"
    child_flags=["-B"]+(["-O"] if not __debug__ else [])
    worker=subprocess.run([sys.executable,*child_flags,str(HERE/"run_experiment.py"),"--output",str(science),
        "--adapter-file","synthetic_adapter.py","--synthetic"],capture_output=True,text=True,timeout=60)
    pc.require(worker.returncode==0,"synthetic scientific worker failed")
    metadata=json.loads(pc.read_bound(science/"run-metadata.json",immutable=True))
    protocol_sha,manifest_sha=metadata["protocol_sha256"],metadata["manifest_sha256"]
    pc.verify_frozen_predictions(science,protocol_sha,manifest_sha,HERE)
    # The invented truth file is created only after the scientific process exits
    # and all outputs verify. No real solution file is bundled or read.
    truthdir=args.output/"invented-truth";truthdir.mkdir(exist_ok=False)
    truthfile=truthdir/"arc-agi_evaluation_solutions.json"
    pc.write_frozen(truthfile,pc.canonical_json({pc.TASK_ID:[[[7,1,0],[3,2,4]]]}))
    report=args.output/"synthetic-comparison.json"
    evaluator=subprocess.run([sys.executable,*child_flags,str(HERE/"evaluate_frozen_predictions.py"),"--output-dir",str(science),
        "--source-dir",str(HERE),"--protocol-sha256",protocol_sha,"--manifest-sha256",manifest_sha,
        "--public-solutions",str(truthfile),"--receipt",str(report)],capture_output=True,text=True,timeout=60)
    pc.require(evaluator.returncode==0,"separate synthetic evaluator failed")
    result=json.loads(pc.read_bound(report,immutable=True))
    pc.require(result["before_any_exact"] is False and result["after_any_exact"] is True,"invented comparison changed")
    print(json.dumps(dict(scope="SYNTHETIC_CONTROL_FLOW_ONLY",before_any_exact=False,after_any_exact=True,
        worker_exited_before_truth_creation=True,separate_evaluator=True,native_training=False,
        scientific_worker_optimized=metadata["optimized_interpreter"],evaluator_requested_optimized=not __debug__,
        real_challenges_or_solutions_read=False,quality_or_official_score_claim=False,output=str(args.output))))
if __name__=="__main__":main()
